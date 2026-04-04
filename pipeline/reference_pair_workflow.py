from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections import deque
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

    background_data = raw.get("background", {})
    if background_data is not None and not isinstance(background_data, dict):
        raise ReferencePairWorkflowError("background must be an object when provided.")
    background_mode = str(background_data.get("mode", "transparent")).strip().lower() or "transparent"
    if background_mode not in {"transparent", "color_key"}:
        raise ReferencePairWorkflowError("background.mode must be one of: transparent, color_key")
    prompt_color = str(background_data.get("prompt_color", "#FF00FF")).strip().upper() or "#FF00FF"
    fallback_colors_raw = background_data.get("fallback_colors", ["#00FF00"])
    if isinstance(fallback_colors_raw, str):
        fallback_colors_raw = [fallback_colors_raw]
    if not isinstance(fallback_colors_raw, list):
        raise ReferencePairWorkflowError("background.fallback_colors must be an array when provided.")
    fallback_colors = [require_non_empty_string(color, "background.fallback_colors[]").upper() for color in fallback_colors_raw]
    parse_hex_color(prompt_color)
    for fallback_color in fallback_colors:
        parse_hex_color(fallback_color)
    color_key_tolerance = int(background_data.get("tolerance", 24))
    if color_key_tolerance < 0 or color_key_tolerance > 255:
        raise ReferencePairWorkflowError("background.tolerance must be between 0 and 255.")

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
            "height relationship, and single-tile framing."
        ),
        "generator_notes": str(raw.get("generator_notes", "")).strip(),
        "background": {
            "mode": background_mode,
            "prompt_color": prompt_color,
            "fallback_colors": fallback_colors,
            "tolerance": color_key_tolerance,
        },
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
        "processed": run_root / "processed",
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
    height_sentence = (
        "Full-height means a normal tall cube tile with the expected full vertical side depth. "
        "Do not compress the side faces or turn it into a shallow slab. "
        if height == "full"
        else "Half-height means a shallow half-block slab: the visible side faces must be short, and the total visible tile height "
        "should be clearly about half of a full-height cube with the same footprint. Do not generate a full-height cube, "
        "do not use tall vertical side faces, and do not fake half-height by only changing texture."
    )
    reference_rule = (
        "Use the supplied reference sheet for structure only (upper reference = full-height; lower reference = half-height). "
        if use_reference_sheet
        else f"Use the supplied {role_text} reference image for structure only. "
    )
    negative_prompt = spec.get("negative_prompt", "")
    extra_negative = f" Negative constraints: {negative_prompt}" if negative_prompt else ""
    generator_notes = spec.get("generator_notes", "")
    generator_sentence = f" Extra notes: {generator_notes}" if generator_notes else ""
    background = spec.get("background", {})
    if background.get("mode") == "color_key":
        allowed_colors = [background["prompt_color"], *background.get("fallback_colors", [])]
        allowed_colors_text = ", ".join(allowed_colors)
        background_sentence = (
            f" Use a single flat solid background color chosen from this allowed set: {allowed_colors_text}. "
            "Estimate the RGB colors that will appear on the visible outer boundary of the generated tile silhouette, "
            "but prioritize the top surface, top rim, upper silhouette, and ground material colors over the lower side walls. "
            "Choose the allowed chroma-key color with the largest color-distance from those top-surface and upper-edge RGB values. "
            "Treat the lower dirt or side-wall materials as secondary when choosing the chroma-key color. "
            "If the tile's top surface is grass, foliage, moss, or otherwise green-dominant, prefer #FF00FF and avoid #00FF00. "
            "Prefer the chroma key that is maximally separated from the top-surface colors and least likely to contaminate the tile edges. "
            "After choosing one of the allowed colors, use that one single chosen color consistently behind the tile "
            "for the entire canvas. This background is a temporary chroma-key mask only: no transparency, no gradient, "
            "no lighting variation, no shadow, no vignette, and no extra colored backdrop elements. "
            "The background must stay one exact uniform color across the whole non-tile area, with crisp edges and no contamination from the tile colors. "
        )
    else:
        background_sentence = " Keep the tile centered in frame with transparent background. "
    outline_sentence = (
        " Do not add any outline, border stroke, rim line, sticker edge, comic contour, or icon-style contour around the tile silhouette. "
        "Do not add a dark perimeter line between the tile and the background. "
        "Edge pixels must read as the tile material itself, not as a separating frame."
    )
    return (
        f"Create one isometric game tile PNG as a {role_text}. "
        f"{reference_rule}"
        f"{height_sentence}"
        f"For this output, match the {role_text} geometry exactly: keep camera angle, silhouette, perspective, "
        f"face visibility, footprint width, and overall proportions aligned to the corresponding reference. "
        "Do not add a scene, ground shadow, border, glow, extra objects, text, or watermark. "
        f"{background_sentence}"
        f"{outline_sentence}"
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
        "background": spec["background"],
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
    background = request_payload.get("background", {"mode": "transparent"})

    generation_logs: dict[str, Any] = {}
    generated_paths: dict[str, str] = {}
    for variant in variants:
        output_path = run_root / "generated" / f"generated_{variant}.png"
        raw_output_path = run_root / "generated" / f"generated_{variant}.raw.png"
        reference_image = Path(request_payload["references"][variant])
        generated_paths[variant] = str(output_path)
        if provider_name == "mock":
            shutil.copy2(reference_image, raw_output_path if background.get("mode") == "color_key" else output_path)
            generation_logs[variant] = {"provider": "mock", "copied_from": str(reference_image)}
        else:
            generation_logs[variant] = generate_with_provider(
                provider_name=provider_name,
                prompt_text=request_payload["prompts"][variant],
                reference_image=Path(request_payload["generation_inputs"][variant]),
                output_path=raw_output_path if background.get("mode") == "color_key" else output_path,
            )
        if background.get("mode") == "color_key":
            generation_logs[variant]["color_key"] = apply_color_key_to_image(
                raw_output_path,
                output_path,
                prompt_color=str(background.get("prompt_color", "#FF00FF")),
                fallback_colors=list(background.get("fallback_colors", ["#00FF00"])),
                tolerance=int(background.get("tolerance", 24)),
                emit_variant_pool=False,
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


def parse_hex_color(value: str) -> tuple[int, int, int]:
    normalized = value.strip().lstrip("#")
    if len(normalized) != 6:
        raise ReferencePairWorkflowError(f"Invalid hex color '{value}'. Expected #RRGGBB.")
    try:
        return tuple(int(normalized[index : index + 2], 16) for index in range(0, 6, 2))  # type: ignore[return-value]
    except ValueError as error:
        raise ReferencePairWorkflowError(f"Invalid hex color '{value}'. Expected #RRGGBB.") from error


def pixel_matches_any_key(pixel: tuple[int, int, int, int], key_colors: list[tuple[int, int, int]], tolerance: int) -> bool:
    red, green, blue, _alpha = pixel
    for key_red, key_green, key_blue in key_colors:
        if (
            abs(red - key_red) <= tolerance
            and abs(green - key_green) <= tolerance
            and abs(blue - key_blue) <= tolerance
        ):
            return True
    return False


def color_key_connected_background_mask(
    image: Image.Image,
    *,
    key_colors: list[tuple[int, int, int]],
    tolerance: int,
) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    mask = Image.new("L", rgba.size, 0)
    mask_pixels = mask.load()
    queue: deque[tuple[int, int]] = deque()

    def enqueue_if_background(x: int, y: int) -> None:
        if mask_pixels[x, y] != 0:
            return
        if not pixel_matches_any_key(pixels[x, y], key_colors, tolerance):
            return
        mask_pixels[x, y] = 255
        queue.append((x, y))

    for x in range(width):
        enqueue_if_background(x, 0)
        enqueue_if_background(x, height - 1)
    for y in range(height):
        enqueue_if_background(0, y)
        enqueue_if_background(width - 1, y)

    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            next_x = x + dx
            next_y = y + dy
            if 0 <= next_x < width and 0 <= next_y < height:
                enqueue_if_background(next_x, next_y)
    return mask


def color_distance(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int]) -> float:
    return (
        (rgb_a[0] - rgb_b[0]) ** 2
        + (rgb_a[1] - rgb_b[1]) ** 2
        + (rgb_a[2] - rgb_b[2]) ** 2
    ) ** 0.5


def color_key_similarity(rgb: tuple[int, int, int], key_color: tuple[int, int, int]) -> float:
    max_distance = (3 * (255**2)) ** 0.5
    return max(0.0, 1.0 - (color_distance(rgb, key_color) / max_distance))


def best_key_color_match(
    rgb: tuple[int, int, int],
    key_colors: list[tuple[int, int, int]],
) -> tuple[tuple[int, int, int], float]:
    best_color = key_colors[0]
    best_similarity = color_key_similarity(rgb, best_color)
    for key_color in key_colors[1:]:
        similarity = color_key_similarity(rgb, key_color)
        if similarity > best_similarity:
            best_color = key_color
            best_similarity = similarity
    return best_color, best_similarity


def detect_active_key_color(
    image: Image.Image,
    *,
    key_colors: list[tuple[int, int, int]],
) -> tuple[tuple[int, int, int], dict[str, Any]]:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    scores = {key_color: 0.0 for key_color in key_colors}
    sample_count = 0

    def sample_pixel(x: int, y: int) -> None:
        nonlocal sample_count
        red, green, blue, _alpha = pixels[x, y]
        rgb = (red, green, blue)
        for key_color in key_colors:
            scores[key_color] += color_key_similarity(rgb, key_color)
        sample_count += 1

    for x in range(width):
        sample_pixel(x, 0)
        sample_pixel(x, height - 1)
    for y in range(1, height - 1):
        sample_pixel(0, y)
        sample_pixel(width - 1, y)

    best_color = max(scores, key=scores.get)
    normalized_scores = {
        "#{:02X}{:02X}{:02X}".format(*key_color): (scores[key_color] / sample_count if sample_count else 0.0)
        for key_color in key_colors
    }
    return best_color, {
        "detected_active_key_color": "#{:02X}{:02X}{:02X}".format(*best_color),
        "border_similarity_scores": normalized_scores,
        "border_sample_count": sample_count,
    }


def opaque_edge_distance(alpha: Image.Image, *, max_distance: int) -> list[list[int | None]]:
    width, height = alpha.size
    alpha_pixels = alpha.load()
    distances: list[list[int | None]] = [[None for _ in range(width)] for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()

    for y in range(height):
        for x in range(width):
            if alpha_pixels[x, y] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = x + dx
                ny = y + dy
                if nx < 0 or nx >= width or ny < 0 or ny >= height or alpha_pixels[nx, ny] == 0:
                    distances[y][x] = 1
                    queue.append((x, y))
                    break

    while queue:
        x, y = queue.popleft()
        current_distance = distances[y][x]
        if current_distance is None or current_distance >= max_distance:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x + dx
            ny = y + dy
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue
            if alpha_pixels[nx, ny] == 0 or distances[ny][nx] is not None:
                continue
            distances[ny][nx] = current_distance + 1
            queue.append((nx, ny))
    return distances


def average_neighbor_color(
    pixels: Any,
    alpha_pixels: Any,
    edge_distances: list[list[int | None]],
    *,
    center_x: int,
    center_y: int,
    min_edge_distance: int,
    search_radius: int,
    key_colors: list[tuple[int, int, int]],
) -> tuple[int, int, int] | None:
    width = len(edge_distances[0]) if edge_distances else 0
    height = len(edge_distances)
    total_red = 0
    total_green = 0
    total_blue = 0
    count = 0
    for dy in range(-search_radius, search_radius + 1):
        y = center_y + dy
        if y < 0 or y >= height:
            continue
        for dx in range(-search_radius, search_radius + 1):
            x = center_x + dx
            if x < 0 or x >= width:
                continue
            if dx == 0 and dy == 0:
                continue
            if alpha_pixels[x, y] == 0:
                continue
            neighbor_distance = edge_distances[y][x]
            if neighbor_distance is None or neighbor_distance < min_edge_distance:
                continue
            red, green, blue, _alpha = pixels[x, y]
            _matched_key, similarity = best_key_color_match((red, green, blue), key_colors)
            if similarity > 0.55:
                continue
            total_red += red
            total_green += green
            total_blue += blue
            count += 1
    if count == 0:
        return None
    return (round(total_red / count), round(total_green / count), round(total_blue / count))


def despill_key_fringe(
    image: Image.Image,
    *,
    key_colors: list[tuple[int, int, int]],
    max_edge_distance: int = 7,
    delete_similarity_threshold: float = 0.48,
    recolor_similarity_threshold: float = 0.18,
    neighbor_search_radius: int = 5,
    passes: int = 3,
) -> tuple[Image.Image, dict[str, Any]]:
    result = image.convert("RGBA").copy()
    pixels = result.load()
    alpha = result.getchannel("A")
    alpha_pixels = alpha.load()
    edge_distances = opaque_edge_distance(alpha, max_distance=max_edge_distance + neighbor_search_radius)
    changed_pixels = 0
    deleted_pixels = 0
    recolored_pixels = 0

    for _pass_index in range(passes):
        for y in range(result.height):
            for x in range(result.width):
                if alpha_pixels[x, y] == 0:
                    continue
                edge_distance = edge_distances[y][x]
                if edge_distance is None or edge_distance > max_edge_distance:
                    continue
                red, green, blue, alpha_value = pixels[x, y]
                matched_key, similarity = best_key_color_match((red, green, blue), key_colors)
                if similarity < recolor_similarity_threshold:
                    continue
                if similarity >= delete_similarity_threshold:
                    pixels[x, y] = (red, green, blue, 0)
                    alpha_pixels[x, y] = 0
                    changed_pixels += 1
                    deleted_pixels += 1
                    continue
                neighbor_color = average_neighbor_color(
                    pixels,
                    alpha_pixels,
                    edge_distances,
                    center_x=x,
                    center_y=y,
                    min_edge_distance=edge_distance + 1,
                    search_radius=neighbor_search_radius,
                    key_colors=key_colors,
                )
                if neighbor_color is None:
                    continue
                if neighbor_color != (red, green, blue):
                    pixels[x, y] = (neighbor_color[0], neighbor_color[1], neighbor_color[2], alpha_value)
                    changed_pixels += 1
                    recolored_pixels += 1
        alpha = result.getchannel("A")
        alpha_pixels = alpha.load()
        edge_distances = opaque_edge_distance(alpha, max_distance=max_edge_distance + neighbor_search_radius)

    return result, {
        "despill_enabled": True,
        "key_colors": ["#{:02X}{:02X}{:02X}".format(*key_color) for key_color in key_colors],
        "max_edge_distance": max_edge_distance,
        "delete_similarity_threshold": delete_similarity_threshold,
        "recolor_similarity_threshold": recolor_similarity_threshold,
        "neighbor_search_radius": neighbor_search_radius,
        "passes": passes,
        "changed_pixels": changed_pixels,
        "deleted_pixels": deleted_pixels,
        "recolored_pixels": recolored_pixels,
        "mode": "delete_near_purple_else_recolor_to_edge",
    }


COLOR_KEY_VARIANT_SPECS = [
    {
        "name": "01_conservative",
        "label": "Conservative",
        "max_edge_distance": 4,
        "delete_similarity_threshold": 0.60,
        "recolor_similarity_threshold": 0.26,
        "neighbor_search_radius": 4,
        "passes": 2,
        "is_default": False,
    },
    {
        "name": "02_conservative_plus",
        "label": "Conservative+",
        "max_edge_distance": 5,
        "delete_similarity_threshold": 0.56,
        "recolor_similarity_threshold": 0.24,
        "neighbor_search_radius": 4,
        "passes": 2,
        "is_default": False,
    },
    {
        "name": "03_balanced",
        "label": "Balanced",
        "max_edge_distance": 7,
        "delete_similarity_threshold": 0.48,
        "recolor_similarity_threshold": 0.18,
        "neighbor_search_radius": 5,
        "passes": 3,
        "is_default": True,
    },
    {
        "name": "04_balanced_plus",
        "label": "Balanced+",
        "max_edge_distance": 8,
        "delete_similarity_threshold": 0.46,
        "recolor_similarity_threshold": 0.16,
        "neighbor_search_radius": 5,
        "passes": 3,
        "is_default": False,
    },
    {
        "name": "05_aggressive",
        "label": "Aggressive",
        "max_edge_distance": 9,
        "delete_similarity_threshold": 0.42,
        "recolor_similarity_threshold": 0.14,
        "neighbor_search_radius": 6,
        "passes": 4,
        "is_default": False,
    },
    {
        "name": "06_aggressive_plus",
        "label": "Aggressive+",
        "max_edge_distance": 10,
        "delete_similarity_threshold": 0.39,
        "recolor_similarity_threshold": 0.12,
        "neighbor_search_radius": 6,
        "passes": 4,
        "is_default": False,
    },
]


def write_preview_variants(image: Image.Image, output_path: Path, variant_name: str) -> dict[str, str]:
    preview_paths: dict[str, str] = {}
    for background_rgba, suffix in (((240, 240, 240, 255), "light"), ((32, 32, 32, 255), "dark")):
        canvas = Image.new("RGBA", image.size, background_rgba)
        canvas.alpha_composite(image)
        preview_path = output_path.with_name(f"{output_path.stem}.{variant_name}.preview_{suffix}{output_path.suffix}")
        canvas.save(preview_path)
        preview_paths[suffix] = str(preview_path)
    return preview_paths


def mirror_variant_pool_to_generated(run_root: Path, *, variant: str, preprocessing_payload: dict[str, Any]) -> None:
    generated_dir = run_root / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    variants_payload = preprocessing_payload.get("variants", {})
    if not isinstance(variants_payload, dict):
        return
    for variant_name, variant_info in variants_payload.items():
        if not isinstance(variant_info, dict):
            continue
        output_value = variant_info.get("output")
        if not output_value:
            continue
        source_path = Path(str(output_value))
        if not source_path.exists():
            continue
        destination_path = generated_dir / f"generated_{variant}.{variant_name}{source_path.suffix}"
        shutil.copy2(source_path, destination_path)


def apply_color_key_to_image(
    image_path: Path,
    output_path: Path,
    *,
    prompt_color: str,
    fallback_colors: list[str],
    tolerance: int,
    emit_variant_pool: bool = False,
) -> dict[str, Any]:
    image = Image.open(image_path).convert("RGBA")
    colors = [parse_hex_color(prompt_color), *(parse_hex_color(color) for color in fallback_colors)]
    background_mask = color_key_connected_background_mask(image, key_colors=colors, tolerance=tolerance)
    active_key_color, detection_stats = detect_active_key_color(image, key_colors=colors)
    masked_result = image.copy()
    masked_result.putalpha(ImageChops.subtract(masked_result.getchannel("A"), background_mask))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not emit_variant_pool:
        result, despill_stats = despill_key_fringe(masked_result, key_colors=[active_key_color])
        result.save(output_path)
        variants_payload = {}
        selected_variant_name = "03_balanced"
    else:
        variants_payload = {}
        selected_variant_name = "03_balanced"
        for variant_spec in COLOR_KEY_VARIANT_SPECS:
            variant_image, variant_stats = despill_key_fringe(
                masked_result.copy(),
                key_colors=[active_key_color],
                max_edge_distance=int(variant_spec["max_edge_distance"]),
                delete_similarity_threshold=float(variant_spec["delete_similarity_threshold"]),
                recolor_similarity_threshold=float(variant_spec["recolor_similarity_threshold"]),
                neighbor_search_radius=int(variant_spec["neighbor_search_radius"]),
                passes=int(variant_spec["passes"]),
            )
            variant_output_path = output_path.with_name(f"{output_path.stem}.{variant_spec['name']}{output_path.suffix}")
            variant_image.save(variant_output_path)
            preview_paths = write_preview_variants(variant_image, output_path, str(variant_spec["name"]))
            variants_payload[str(variant_spec["name"])] = {
                "label": variant_spec["label"],
                "output": str(variant_output_path),
                "previews": preview_paths,
                "despill": variant_stats,
            }
            if bool(variant_spec.get("is_default")):
                selected_variant_name = str(variant_spec["name"])
                variant_image.save(output_path)
                despill_stats = variant_stats
        if selected_variant_name not in variants_payload:
            raise ReferencePairWorkflowError("No default color-key variant was configured.")

    return {
        "input": str(image_path),
        "output": str(output_path),
        "prompt_color": prompt_color,
        "fallback_colors": fallback_colors,
        "tolerance": tolerance,
        "removed_background_pixels": mask_area(background_mask),
        "active_key_color": detection_stats["detected_active_key_color"],
        "key_color_detection": detection_stats,
        "selected_variant": selected_variant_name,
        "variants": variants_payload,
        "despill": despill_stats,
    }


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
    background = request_payload.get("background", {"mode": "transparent"})
    full_reference = Path(request_payload["references"]["full"])
    half_reference = Path(request_payload["references"]["half"])
    full_raw_default = run_root / "generated" / "generated_full.raw.png"
    half_raw_default = run_root / "generated" / "generated_half.raw.png"
    full_generated_input = full_image or (
        full_raw_default if background.get("mode") == "color_key" and full_raw_default.exists() else run_root / "generated" / "generated_full.png"
    )
    half_generated_input = half_image or (
        half_raw_default if background.get("mode") == "color_key" and half_raw_default.exists() else run_root / "generated" / "generated_half.png"
    )
    full_generated = full_generated_input
    half_generated = half_generated_input
    preprocessing: dict[str, Any] = {}
    if background.get("mode") == "color_key":
        if "full" in variants:
            full_generated = run_root / "processed" / "generated_full.keyed.png"
            preprocessing["full"] = apply_color_key_to_image(
                full_generated_input,
                full_generated,
                prompt_color=str(background.get("prompt_color", "#FF00FF")),
                fallback_colors=list(background.get("fallback_colors", ["#00FF00"])),
                tolerance=int(background.get("tolerance", 24)),
                emit_variant_pool=True,
            )
            mirror_variant_pool_to_generated(run_root, variant="full", preprocessing_payload=preprocessing["full"])
        if "half" in variants:
            half_generated = run_root / "processed" / "generated_half.keyed.png"
            preprocessing["half"] = apply_color_key_to_image(
                half_generated_input,
                half_generated,
                prompt_color=str(background.get("prompt_color", "#FF00FF")),
                fallback_colors=list(background.get("fallback_colors", ["#00FF00"])),
                tolerance=int(background.get("tolerance", 24)),
                emit_variant_pool=True,
            )
            mirror_variant_pool_to_generated(run_root, variant="half", preprocessing_payload=preprocessing["half"])
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
        "background": background,
        "preprocessing": preprocessing,
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
