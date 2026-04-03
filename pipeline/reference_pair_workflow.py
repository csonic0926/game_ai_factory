from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from pipeline.credentials import CredentialError, build_gemini_provider_env

REPO_ROOT = Path(__file__).resolve().parents[1]
NANO_BANANA_ROOT = (REPO_ROOT.parent / "nano_banana").resolve()
NANO_BANANA_SCRIPT = NANO_BANANA_ROOT / "scripts" / "generate_image.js"
SCHEMA_VERSION = "reference_pair_workflow_v1"
SUPPORTED_PROVIDERS = {"mock", "nano_banana", "nano_banana_pro"}
SUPPORTED_VARIANTS = {"full", "half"}
PROVIDER_MODELS = {
    "nano_banana": "nano-banana-2",
    "nano_banana_pro": "nano-banana-pro",
}
ALPHA_THRESHOLD = 32


class ReferencePairWorkflowError(RuntimeError):
    pass


@dataclass
class PairMetrics:
    image_path: str
    size: tuple[int, int]
    bbox: tuple[int, int, int, int] | None
    area_pixels: int
    center: tuple[float, float] | None


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    lowered = "_".join(value.strip().lower().split())
    cleaned = "".join(character if character.isalnum() or character == "_" else "_" for character in lowered)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "run"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReferencePairWorkflowError(f"{label} must be a non-empty string.")
    return value.strip()


def resolve_input_path(path_value: str, *, base_path: Path) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = (base_path / path).resolve()
    else:
        path = path.resolve()
    return path


def load_and_validate_spec(spec_path: Path) -> tuple[dict[str, Any], list[str]]:
    raw = load_json(spec_path)
    if not isinstance(raw, dict):
        raise ReferencePairWorkflowError("Spec must be a JSON object.")

    schema_version = require_non_empty_string(raw.get("schema_version"), "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise ReferencePairWorkflowError(
            f"Unsupported schema_version '{schema_version}'. Expected '{SCHEMA_VERSION}'."
        )

    provider_data = raw.get("provider", {})
    if not isinstance(provider_data, dict):
        raise ReferencePairWorkflowError("provider must be an object.")
    provider_name = require_non_empty_string(provider_data.get("name", "mock"), "provider.name").lower()
    if provider_name not in SUPPORTED_PROVIDERS:
        raise ReferencePairWorkflowError(
            f"Unsupported provider.name '{provider_name}'. Expected one of: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )

    reference_pair = raw.get("reference_pair")
    if not isinstance(reference_pair, dict):
        raise ReferencePairWorkflowError("reference_pair must be an object.")
    full_reference = resolve_input_path(
        require_non_empty_string(reference_pair.get("full"), "reference_pair.full"),
        base_path=spec_path.parent,
    )
    half_reference = resolve_input_path(
        require_non_empty_string(reference_pair.get("half"), "reference_pair.half"),
        base_path=spec_path.parent,
    )
    for label, image_path in (("reference_pair.full", full_reference), ("reference_pair.half", half_reference)):
        if not image_path.exists():
            raise ReferencePairWorkflowError(f"{label} was not found: {image_path}")

    validation_data = raw.get("validation", {})
    if validation_data is not None and not isinstance(validation_data, dict):
        raise ReferencePairWorkflowError("validation must be an object when provided.")

    variants_raw = raw.get("variants", ["full", "half"])
    if not isinstance(variants_raw, list) or not variants_raw:
        raise ReferencePairWorkflowError("variants must be a non-empty array when provided.")
    variants: list[str] = []
    for variant in variants_raw:
        variant_name = require_non_empty_string(variant, "variants[]").lower()
        if variant_name not in SUPPORTED_VARIANTS:
            raise ReferencePairWorkflowError(
                f"Unsupported variant '{variant_name}'. Expected one of: {', '.join(sorted(SUPPORTED_VARIANTS))}"
            )
        if variant_name not in variants:
            variants.append(variant_name)

    output_root = resolve_input_path(require_non_empty_string(raw.get("output_root"), "output_root"), base_path=spec_path.parent)
    theme = require_non_empty_string(raw.get("theme"), "theme")
    run_id = str(raw.get("run_id", "")).strip() or slugify(theme)

    normalized = {
        "schema_version": SCHEMA_VERSION,
        "theme": theme,
        "run_id": run_id,
        "output_root": str(output_root),
        "variants": variants,
        "provider": {"name": provider_name},
        "reference_pair": {"full": str(full_reference), "half": str(half_reference)},
        "prompt": require_non_empty_string(raw.get("prompt"), "prompt"),
        "negative_prompt": str(raw.get("negative_prompt", "")).strip(),
        "reference_intent": str(raw.get("reference_intent", "")).strip()
        or (
            "Use the references to preserve camera angle, silhouette, proportions, face visibility, "
            "height relationship, and transparent-background single-tile framing."
        ),
        "generator_notes": str(raw.get("generator_notes", "")).strip(),
        "validation": {
            "iou_soft_fail": float(validation_data.get("iou_soft_fail", 0.92)),
            "iou_hard_fail": float(validation_data.get("iou_hard_fail", 0.80)),
            "bbox_delta_soft_fail": int(validation_data.get("bbox_delta_soft_fail", 6)),
            "bbox_delta_hard_fail": int(validation_data.get("bbox_delta_hard_fail", 16)),
            "pair_height_ratio_soft_fail": float(validation_data.get("pair_height_ratio_soft_fail", 0.08)),
            "pair_height_ratio_hard_fail": float(validation_data.get("pair_height_ratio_hard_fail", 0.16)),
        },
    }

    warnings: list[str] = []
    if provider_name != "mock":
        warnings.append("Provider execution requires GEMINI_API_KEY in process env or repo .env.")
    return normalized, warnings


def run_root_for_spec(spec: dict[str, Any]) -> Path:
    return Path(spec["output_root"]).expanduser().resolve() / spec["run_id"]


def build_run_directories(run_root: Path) -> dict[str, Path]:
    directories = {
        "run_root": run_root,
        "refs": run_root / "refs",
        "request": run_root / "request",
        "generated": run_root / "generated",
        "validation": run_root / "validation",
        "logs": run_root / "logs",
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)
    return directories


def compose_reference_sheet(full_image_path: Path, half_image_path: Path, output_path: Path) -> Path:
    full_image = Image.open(full_image_path).convert("RGBA")
    half_image = Image.open(half_image_path).convert("RGBA")
    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    full_resized = full_image.resize((384, 384), Image.LANCZOS)
    half_resized = half_image.resize((384, 384), Image.LANCZOS)
    canvas.alpha_composite(full_resized, ((1024 - 384) // 2, 96))
    canvas.alpha_composite(half_resized, ((1024 - 384) // 2, 544))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((300, 72, 724, 504), radius=24, outline=(255, 255, 255, 96), width=3)
    draw.rounded_rectangle((300, 520, 724, 952), radius=24, outline=(255, 255, 255, 96), width=3)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return output_path


def build_generation_prompt(spec: dict[str, Any], *, height: str, use_reference_sheet: bool) -> str:
    role_text = "full-height cube tile" if height == "full" else "half-height cube tile"
    reference_rule = (
        "Use the supplied reference sheet for structure only (upper reference = full-height; lower reference = half-height). "
        if use_reference_sheet
        else f"Use the supplied {role_text} reference image for structure only. "
    )
    negative_prompt = spec.get("negative_prompt", "")
    extra_negative = f" Negative constraints: {negative_prompt}" if negative_prompt else ""
    generator_notes = spec.get("generator_notes", "")
    generator_sentence = f" Extra notes: {generator_notes}" if generator_notes else ""
    return (
        f"Create one transparent-background isometric game tile PNG as a {role_text}. "
        f"{reference_rule}"
        f"For this output, match the {role_text} geometry exactly: keep camera angle, silhouette, perspective, "
        f"face visibility, footprint width, and overall proportions aligned to the corresponding reference. "
        "Do not add a scene, ground shadow, border, glow, extra objects, text, or watermark. "
        "Keep the tile centered in frame with transparent background. "
        f"Reference intent: {spec['reference_intent']} "
        f"Art direction: {spec['prompt']}."
        f"{extra_negative}{generator_sentence}"
    )


def prepare_reference_pair_run(spec_path: Path) -> dict[str, Any]:
    spec, warnings = load_and_validate_spec(spec_path)
    run_root = run_root_for_spec(spec)
    directories = build_run_directories(run_root)
    variants = spec["variants"]

    full_reference_src = Path(spec["reference_pair"]["full"])
    half_reference_src = Path(spec["reference_pair"]["half"])
    full_reference_dst = directories["refs"] / "floor_full.png"
    half_reference_dst = directories["refs"] / "floor_half.png"
    shutil.copy2(full_reference_src, full_reference_dst)
    shutil.copy2(half_reference_src, half_reference_dst)
    reference_sheet_path = compose_reference_sheet(
        full_reference_dst,
        half_reference_dst,
        directories["refs"] / "reference_pair_sheet.png",
    )

    prompts: dict[str, str] = {}
    prompt_paths: dict[str, str] = {}
    expected_outputs: dict[str, str] = {}
    generation_inputs: dict[str, str] = {}
    use_reference_sheet = len(variants) == 2
    for variant in variants:
        prompt_text = build_generation_prompt(spec, height=variant, use_reference_sheet=use_reference_sheet)
        prompt_path = directories["request"] / f"prompt_{variant}.txt"
        prompt_path.write_text(prompt_text + "\n", encoding="utf-8")
        prompts[variant] = prompt_text
        prompt_paths[variant] = str(prompt_path)
        expected_outputs[variant] = str(directories["generated"] / f"generated_{variant}.png")
        generation_inputs[variant] = (
            str(reference_sheet_path) if len(variants) == 2 else str(directories["refs"] / f"floor_{variant}.png")
        )

    request_payload = {
        "schema_version": SCHEMA_VERSION,
        "prepared_at": now_iso(),
        "spec_path": str(spec_path.resolve()),
        "theme": spec["theme"],
        "variants": variants,
        "provider": spec["provider"],
        "references": {
            "full": str(full_reference_dst),
            "half": str(half_reference_dst),
            "pair_sheet": str(reference_sheet_path),
        },
        "generation_inputs": generation_inputs,
        "expected_outputs": expected_outputs,
        "prompts": prompts,
        "validation": spec["validation"],
        "warnings": warnings,
    }
    write_json(directories["request"] / "request.json", request_payload)
    write_json(directories["logs"] / "prepare.json", {"ok": True, "prepared_at": now_iso(), "warnings": warnings})
    return {
        "run_root": str(run_root),
        "variants": variants,
        "request_path": str(directories["request"] / "request.json"),
        "reference_sheet": str(reference_sheet_path),
        "prompt_paths": prompt_paths,
        "warnings": warnings,
    }


def provider_env_for_generation(provider_name: str) -> dict[str, str]:
    if provider_name == "mock":
        return dict(os.environ)
    try:
        return build_gemini_provider_env()
    except CredentialError as error:
        raise ReferencePairWorkflowError(str(error)) from error


def generate_with_provider(*, provider_name: str, prompt_text: str, reference_image: Path, output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if provider_name == "mock":
        return {"provider": "mock", "model": "mock", "stdout": "mock mode skips external generation"}
    if not NANO_BANANA_SCRIPT.exists():
        raise ReferencePairWorkflowError(f"Nano Banana CLI not found: {NANO_BANANA_SCRIPT}")

    command = [
        "node",
        str(NANO_BANANA_SCRIPT),
        f"--prompt={prompt_text}",
        f"--image={reference_image}",
        f"--out={output_path}",
        "--key=company",
        f"--model={PROVIDER_MODELS[provider_name]}",
        "--aspect-ratio=1:1",
        "--image-size=1K",
    ]
    completed = subprocess.run(
        command,
        cwd=NANO_BANANA_ROOT,
        env=provider_env_for_generation(provider_name),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        raise ReferencePairWorkflowError(completed.stderr.strip() or completed.stdout.strip() or "Gemini provider failed")
    return {
        "provider": provider_name,
        "model": PROVIDER_MODELS[provider_name],
        "stdout": completed.stdout.strip(),
    }


def generate_reference_pair(spec_path: Path) -> dict[str, Any]:
    prepare_result = prepare_reference_pair_run(spec_path)
    run_root = Path(prepare_result["run_root"])
    request_payload = load_json(run_root / "request" / "request.json")
    provider_name = request_payload["provider"]["name"]
    variants: list[str] = request_payload.get("variants", ["full", "half"])

    generation_logs: dict[str, Any] = {}
    generated_paths: dict[str, str] = {}
    for variant in variants:
        output_path = run_root / "generated" / f"generated_{variant}.png"
        reference_image = Path(request_payload["references"][variant])
        generated_paths[variant] = str(output_path)
        if provider_name == "mock":
            shutil.copy2(reference_image, output_path)
            generation_logs[variant] = {"provider": "mock", "copied_from": str(reference_image)}
        else:
            generation_logs[variant] = generate_with_provider(
                provider_name=provider_name,
                prompt_text=request_payload["prompts"][variant],
                reference_image=Path(request_payload["generation_inputs"][variant]),
                output_path=output_path,
            )

    write_json(run_root / "logs" / "generate.json", {"ok": True, "generated_at": now_iso(), "results": generation_logs})
    validation_result = validate_reference_pair_run(run_root)
    return {
        "run_root": str(run_root),
        "variants": variants,
        "generated": generated_paths,
        "validation": validation_result,
    }


def alpha_mask(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    return alpha.point(lambda value: 255 if value >= ALPHA_THRESHOLD else 0, mode="L")


def mask_area(mask: Image.Image) -> int:
    histogram = mask.histogram()
    return int(histogram[255]) if len(histogram) > 255 else 0


def mask_center(mask: Image.Image) -> tuple[float, float] | None:
    bbox = mask.getbbox()
    if bbox is None:
        return None
    pixels = mask.load()
    sum_x = 0.0
    sum_y = 0.0
    count = 0
    for y in range(mask.height):
        for x in range(mask.width):
            if pixels[x, y] >= 128:
                sum_x += x
                sum_y += y
                count += 1
    if count == 0:
        return None
    return (sum_x / count, sum_y / count)


def pair_metrics(image_path: Path) -> PairMetrics:
    image = Image.open(image_path).convert("RGBA")
    mask = alpha_mask(image)
    return PairMetrics(
        image_path=str(image_path),
        size=image.size,
        bbox=mask.getbbox(),
        area_pixels=mask_area(mask),
        center=mask_center(mask),
    )


def intersection_over_union(mask_a: Image.Image, mask_b: Image.Image) -> float:
    intersection = ImageChops.multiply(mask_a, mask_b)
    union = ImageChops.lighter(mask_a, mask_b)
    intersection_area = mask_area(intersection)
    union_area = mask_area(union)
    if union_area == 0:
        return 0.0
    return intersection_area / union_area


def bbox_deltas(bbox_a: tuple[int, int, int, int] | None, bbox_b: tuple[int, int, int, int] | None) -> dict[str, int] | None:
    if bbox_a is None or bbox_b is None:
        return None
    return {
        "left": bbox_b[0] - bbox_a[0],
        "top": bbox_b[1] - bbox_a[1],
        "right": bbox_b[2] - bbox_a[2],
        "bottom": bbox_b[3] - bbox_a[3],
        "width": (bbox_b[2] - bbox_b[0]) - (bbox_a[2] - bbox_a[0]),
        "height": (bbox_b[3] - bbox_b[1]) - (bbox_a[3] - bbox_a[1]),
    }


def mask_visual(mask: Image.Image, color: tuple[int, int, int, int]) -> Image.Image:
    rgba = Image.new("RGBA", mask.size, color)
    transparent = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    return Image.composite(rgba, transparent, mask)


def create_overlay(reference_path: Path, generated_path: Path, output_path: Path) -> None:
    reference = Image.open(reference_path).convert("RGBA")
    generated = Image.open(generated_path).convert("RGBA")
    ref_mask = alpha_mask(reference)
    gen_mask = alpha_mask(generated)
    ref_outline = ImageChops.subtract(ref_mask.filter(ImageFilter.MaxFilter(3)), ref_mask)
    gen_outline = ImageChops.subtract(gen_mask.filter(ImageFilter.MaxFilter(3)), gen_mask)
    canvas = Image.new("RGBA", reference.size, (0, 0, 0, 0))
    canvas.alpha_composite(reference)
    canvas.alpha_composite(mask_visual(ref_outline, (80, 255, 120, 220)))
    canvas.alpha_composite(mask_visual(gen_outline, (255, 64, 220, 220)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def create_diff_mask(reference_path: Path, generated_path: Path, output_path: Path) -> None:
    reference = Image.open(reference_path).convert("RGBA")
    generated = Image.open(generated_path).convert("RGBA")
    ref_mask = alpha_mask(reference)
    gen_mask = alpha_mask(generated)
    added = ImageChops.subtract(gen_mask, ref_mask)
    removed = ImageChops.subtract(ref_mask, gen_mask)
    canvas = Image.new("RGBA", reference.size, (0, 0, 0, 0))
    canvas.alpha_composite(mask_visual(removed, (255, 80, 80, 220)))
    canvas.alpha_composite(mask_visual(added, (80, 180, 255, 220)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def validate_single_pair(reference_path: Path, generated_path: Path, thresholds: dict[str, Any]) -> dict[str, Any]:
    reference_image = Image.open(reference_path).convert("RGBA")
    generated_image = Image.open(generated_path).convert("RGBA")
    if reference_image.size != generated_image.size:
        return {
            "status": "hard_fail",
            "reason": f"Canvas size mismatch: reference={reference_image.size}, generated={generated_image.size}",
        }

    reference_mask = alpha_mask(reference_image)
    generated_mask = alpha_mask(generated_image)
    reference_metrics = pair_metrics(reference_path)
    generated_metrics = pair_metrics(generated_path)
    iou = intersection_over_union(reference_mask, generated_mask)
    deltas = bbox_deltas(reference_metrics.bbox, generated_metrics.bbox)
    non_transparent_canvas = generated_metrics.bbox == (0, 0, generated_image.width, generated_image.height)

    failures: list[str] = []
    severity = "pass"
    if generated_metrics.bbox is None:
        failures.append("generated image has no opaque tile silhouette")
        severity = "hard_fail"
    if non_transparent_canvas:
        failures.append("generated image appears to fill the whole canvas; background may not be transparent")
        severity = "hard_fail"
    if iou < thresholds["iou_hard_fail"]:
        failures.append(f"silhouette IOU too low: {iou:.4f}")
        severity = "hard_fail"
    elif iou < thresholds["iou_soft_fail"] and severity != "hard_fail":
        failures.append(f"silhouette IOU drift: {iou:.4f}")
        severity = "soft_fail"
    if deltas is not None:
        max_bbox_delta = max(abs(value) for value in deltas.values())
        if max_bbox_delta > thresholds["bbox_delta_hard_fail"]:
            failures.append(f"bbox delta too large: {deltas}")
            severity = "hard_fail"
        elif max_bbox_delta > thresholds["bbox_delta_soft_fail"] and severity == "pass":
            failures.append(f"bbox delta drift: {deltas}")
            severity = "soft_fail"

    return {
        "status": severity,
        "failures": failures,
        "reference": reference_metrics.__dict__,
        "generated": generated_metrics.__dict__,
        "iou": iou,
        "bbox_deltas": deltas,
    }


def validate_reference_pair_run(run_root: Path, *, full_image: Path | None = None, half_image: Path | None = None) -> dict[str, Any]:
    request_payload = load_json(run_root / "request" / "request.json")
    thresholds = request_payload["validation"]
    variants: list[str] = request_payload.get("variants", ["full", "half"])
    full_reference = Path(request_payload["references"]["full"])
    half_reference = Path(request_payload["references"]["half"])
    full_generated = full_image or run_root / "generated" / "generated_full.png"
    half_generated = half_image or run_root / "generated" / "generated_half.png"
    if "full" in variants and not full_generated.exists():
        raise ReferencePairWorkflowError(f"Missing generated full image: {full_generated}")
    if "half" in variants and not half_generated.exists():
        raise ReferencePairWorkflowError(f"Missing generated half image: {half_generated}")

    full_result = validate_single_pair(full_reference, full_generated, thresholds) if "full" in variants else None
    half_result = validate_single_pair(half_reference, half_generated, thresholds) if "half" in variants else None

    full_ref_metrics = pair_metrics(full_reference)
    half_ref_metrics = pair_metrics(half_reference)
    full_gen_metrics = pair_metrics(full_generated) if "full" in variants else None
    half_gen_metrics = pair_metrics(half_generated) if "half" in variants else None

    def bbox_height(metrics: PairMetrics) -> int | None:
        if metrics.bbox is None:
            return None
        return metrics.bbox[3] - metrics.bbox[1]

    ref_ratio = None
    gen_ratio = None
    pair_status = "skipped"
    pair_failures: list[str] = []
    if "full" in variants and "half" in variants:
        pair_status = "pass"
        if bbox_height(full_ref_metrics) and bbox_height(half_ref_metrics):
            ref_ratio = bbox_height(half_ref_metrics) / bbox_height(full_ref_metrics)
        if full_gen_metrics is not None and half_gen_metrics is not None:
            if bbox_height(full_gen_metrics) and bbox_height(half_gen_metrics):
                gen_ratio = bbox_height(half_gen_metrics) / bbox_height(full_gen_metrics)

        if ref_ratio is not None and gen_ratio is not None:
            ratio_delta = abs(gen_ratio - ref_ratio)
            if ratio_delta > thresholds["pair_height_ratio_hard_fail"]:
                pair_status = "hard_fail"
                pair_failures.append(
                    f"full/half height ratio drift too large: reference={ref_ratio:.4f}, generated={gen_ratio:.4f}"
                )
            elif ratio_delta > thresholds["pair_height_ratio_soft_fail"]:
                pair_status = "soft_fail"
                pair_failures.append(
                    f"full/half height ratio drift: reference={ref_ratio:.4f}, generated={gen_ratio:.4f}"
                )
        else:
            pair_status = "hard_fail"
            pair_failures.append("could not compute full/half bbox heights")
    else:
        pair_failures.append("pair relationship validation skipped because only one variant was requested")

    validation_dir = run_root / "validation"
    artifacts: dict[str, str] = {"validation_json": str(validation_dir / "validation.json")}
    if "full" in variants:
        create_overlay(full_reference, full_generated, validation_dir / "overlay_full.png")
        create_diff_mask(full_reference, full_generated, validation_dir / "diff_full.png")
        artifacts["overlay_full"] = str(validation_dir / "overlay_full.png")
        artifacts["diff_full"] = str(validation_dir / "diff_full.png")
    if "half" in variants:
        create_overlay(half_reference, half_generated, validation_dir / "overlay_half.png")
        create_diff_mask(half_reference, half_generated, validation_dir / "diff_half.png")
        artifacts["overlay_half"] = str(validation_dir / "overlay_half.png")
        artifacts["diff_half"] = str(validation_dir / "diff_half.png")

    statuses = [result["status"] for result in (full_result, half_result) if result is not None]
    if pair_status != "skipped":
        statuses.append(pair_status)
    if "hard_fail" in statuses:
        final_status = "hard_fail"
    elif "soft_fail" in statuses:
        final_status = "soft_fail"
    else:
        final_status = "pass"

    result = {
        "ok": final_status == "pass",
        "status": final_status,
        "validated_at": now_iso(),
        "run_root": str(run_root),
        "variants": variants,
        "pair_relationship": {
            "status": pair_status,
            "failures": pair_failures,
            "reference_height_ratio_half_to_full": ref_ratio,
            "generated_height_ratio_half_to_full": gen_ratio,
        },
        "artifacts": artifacts,
    }
    if full_result is not None:
        result["full"] = full_result
    if half_result is not None:
        result["half"] = half_result
    write_json(validation_dir / "validation.json", result)
    write_json(run_root / "logs" / "validate.json", {"ok": True, "validated_at": now_iso(), "status": final_status})
    return result
