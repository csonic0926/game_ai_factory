from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops
from pipeline.reference_pair_workflow import color_key_similarity, parse_hex_color


TARGET_SIZE = 128
KNOWN_VARIANTS = (
    "01_conservative",
    "02_conservative_plus",
    "03_balanced",
    "04_balanced_plus",
    "05_aggressive",
    "06_aggressive_plus",
)
MIN_NORMALIZED_IOU = 0.94
MAX_ANCHOR_ERROR = 3.0
MAX_SHOULDER_INSET = 2
MAX_MID_INSET = 2
MAX_BOTTOM_TIP_DRIFT = 3
MIN_EFFECTIVE_SCALE_RATIO = 0.88
TOP_BOUNDARY_SCAN_RATIO = 0.35
TOP_BOUNDARY_KEY_SIMILARITY_FAIL = 0.55
TOP_BOUNDARY_KEY_PIXEL_RATIO_FAIL = 0.03
TOP_BOUNDARY_KEY_PIXEL_COUNT_FAIL = 8
TOP_BOUNDARY_KEY_RUN_FAIL = 3


class VariantSelectorError(RuntimeError):
    pass


@dataclass
class EffectiveBBox:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left + 1

    @property
    def height(self) -> int:
        return self.bottom - self.top + 1


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def alpha_mask(image: Image.Image) -> Image.Image:
    alpha = image.convert("RGBA").getchannel("A")
    return alpha.point(lambda value: 255 if value >= 32 else 0, mode="L")


def row_span(mask: Image.Image, y: int) -> tuple[int, int] | None:
    pixels = mask.load()
    xs = [x for x in range(mask.width) if pixels[x, y] >= 128]
    if not xs:
        return None
    return min(xs), max(xs)


def effective_bbox(mask: Image.Image) -> EffectiveBBox:
    bbox = mask.getbbox()
    if bbox is None:
        raise VariantSelectorError("Mask has no opaque pixels.")
    left0, top0, right0, bottom0 = bbox
    bottom = bottom0 - 1
    right = right0 - 1

    spans: list[tuple[int, int, int]] = []
    for y in range(top0, bottom + 1):
        span = row_span(mask, y)
        if span is None:
            continue
        spans.append((y, span[0], span[1]))
    if not spans:
        raise VariantSelectorError("Could not compute row spans for mask.")

    max_width = max((span_right - span_left + 1) for _y, span_left, span_right in spans)
    width_gate = max(3, int(round(max_width * 0.60)))
    top_candidates = [y for y, span_left, span_right in spans if (span_right - span_left + 1) >= width_gate]
    top = min(top_candidates) if top_candidates else top0

    relevant_spans = [(y, span_left, span_right) for y, span_left, span_right in spans if y >= top]
    left = min(span_left for _y, span_left, _span_right in relevant_spans)
    right = max(span_right for _y, _span_left, span_right in relevant_spans)
    return EffectiveBBox(left=left, top=top, right=right, bottom=bottom)


def normalize_mask(mask: Image.Image, *, target_size: int = TARGET_SIZE) -> tuple[Image.Image, EffectiveBBox]:
    bbox = effective_bbox(mask)
    cropped = mask.crop((bbox.left, bbox.top, bbox.right + 1, bbox.bottom + 1))
    normalized = cropped.resize((target_size, target_size), Image.NEAREST)
    return normalized, bbox


def mask_area(mask: Image.Image) -> int:
    histogram = mask.histogram()
    return int(histogram[255]) if len(histogram) > 255 else 0


def iou(mask_a: Image.Image, mask_b: Image.Image) -> float:
    intersection = ImageChops.multiply(mask_a, mask_b)
    union = ImageChops.lighter(mask_a, mask_b)
    union_area = mask_area(union)
    if union_area == 0:
        return 0.0
    return mask_area(intersection) / union_area


def find_anchor(mask: Image.Image, target_y: int, side: str) -> tuple[int, int] | None:
    search_order = [0]
    for delta in range(1, mask.height):
        search_order.extend((delta, -delta))
    pixels = mask.load()
    for delta in search_order:
        y = target_y + delta
        if y < 0 or y >= mask.height:
            continue
        xs = [x for x in range(mask.width) if pixels[x, y] >= 128]
        if not xs:
            continue
        if side == "left":
            return min(xs), y
        if side == "right":
            return max(xs), y
    return None


def mask_anchors(mask: Image.Image) -> dict[str, tuple[int, int] | None]:
    bbox = mask.getbbox()
    if bbox is None:
        return {"left_shoulder": None, "right_shoulder": None, "left_mid": None, "right_mid": None, "bottom_tip": None}
    left, top, right, bottom = bbox
    height = bottom - top
    shoulder_y = top + max(1, int(round(height * 0.18)))
    mid_y = top + max(1, int(round(height * 0.56)))
    pixels = mask.load()
    bottom_points = [(x, bottom - 1) for x in range(mask.width) if pixels[x, bottom - 1] >= 128]
    bottom_tip = None
    if bottom_points:
        median_index = len(bottom_points) // 2
        bottom_tip = bottom_points[median_index]
    return {
        "left_shoulder": find_anchor(mask, shoulder_y, "left"),
        "right_shoulder": find_anchor(mask, shoulder_y, "right"),
        "left_mid": find_anchor(mask, mid_y, "left"),
        "right_mid": find_anchor(mask, mid_y, "right"),
        "bottom_tip": bottom_tip,
    }


def anchor_error(candidate: dict[str, tuple[int, int] | None], reference: dict[str, tuple[int, int] | None]) -> float:
    total = 0.0
    count = 0
    for key, ref_value in reference.items():
        cand_value = candidate.get(key)
        if ref_value is None or cand_value is None:
            total += 128.0
            count += 1
            continue
        total += abs(cand_value[0] - ref_value[0]) + abs(cand_value[1] - ref_value[1])
        count += 1
    return total / count if count else 999.0


def overlay_preview(reference_mask: Image.Image, candidate_mask: Image.Image, output_path: Path) -> None:
    canvas = Image.new("RGBA", reference_mask.size, (245, 245, 245, 255))
    ref_rgba = Image.new("RGBA", reference_mask.size, (100, 210, 120, 180))
    cand_rgba = Image.new("RGBA", candidate_mask.size, (255, 80, 120, 140))
    canvas.alpha_composite(Image.composite(ref_rgba, Image.new("RGBA", reference_mask.size, (0, 0, 0, 0)), reference_mask))
    canvas.alpha_composite(Image.composite(cand_rgba, Image.new("RGBA", candidate_mask.size, (0, 0, 0, 0)), candidate_mask))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def top_boundary_key_contamination(candidate_path: Path, *, active_key_color: str) -> dict[str, Any]:
    image = Image.open(candidate_path).convert("RGBA")
    mask = alpha_mask(image)
    bbox = effective_bbox(mask)
    key_color = parse_hex_color(active_key_color)
    scan_limit = bbox.top + max(1, int(round(bbox.height * TOP_BOUNDARY_SCAN_RATIO)))
    contaminated_pixels = 0
    scanned_pixels = 0
    max_contiguous_run = 0
    current_run = 0
    strongest_samples: list[dict[str, Any]] = []

    for x in range(bbox.left, bbox.right + 1):
        first_hit = None
        for y in range(bbox.top, min(bbox.bottom + 1, scan_limit + 1)):
            r, g, b, a = image.getpixel((x, y))
            if a > 0:
                similarity = color_key_similarity((r, g, b), key_color)
                first_hit = {"x": x, "y": y, "rgb": [r, g, b], "similarity": similarity}
                break
        if first_hit is None:
            current_run = 0
            continue
        scanned_pixels += 1
        if first_hit["similarity"] >= TOP_BOUNDARY_KEY_SIMILARITY_FAIL:
            contaminated_pixels += 1
            current_run += 1
            max_contiguous_run = max(max_contiguous_run, current_run)
            strongest_samples.append(first_hit)
        else:
            current_run = 0

    strongest_samples.sort(key=lambda item: item["similarity"], reverse=True)
    contamination_ratio = contaminated_pixels / scanned_pixels if scanned_pixels else 0.0
    fail = (
        contaminated_pixels >= TOP_BOUNDARY_KEY_PIXEL_COUNT_FAIL
        or contamination_ratio >= TOP_BOUNDARY_KEY_PIXEL_RATIO_FAIL
        or max_contiguous_run >= TOP_BOUNDARY_KEY_RUN_FAIL
    )
    return {
        "active_key_color": active_key_color,
        "scanned_pixels": scanned_pixels,
        "contaminated_pixels": contaminated_pixels,
        "contamination_ratio": contamination_ratio,
        "max_contiguous_run": max_contiguous_run,
        "similarity_threshold": TOP_BOUNDARY_KEY_SIMILARITY_FAIL,
        "fail": fail,
        "strongest_samples": strongest_samples[:12],
    }


def score_candidate(candidate_path: Path, reference_mask_normalized: Image.Image, reference_anchors: dict[str, tuple[int, int] | None], output_dir: Path) -> dict[str, Any]:
    image = Image.open(candidate_path).convert("RGBA")
    candidate_mask_normalized, bbox = normalize_mask(alpha_mask(image))
    candidate_anchors = mask_anchors(candidate_mask_normalized)
    candidate_iou = iou(reference_mask_normalized, candidate_mask_normalized)
    candidate_anchor_error = anchor_error(candidate_anchors, reference_anchors)
    score = (candidate_iou * 1000.0) - (candidate_anchor_error * 4.0)
    overlay_path = output_dir / f"{candidate_path.stem}.overlay.png"
    normalized_path = output_dir / f"{candidate_path.stem}.normalized.png"
    overlay_preview(reference_mask_normalized, candidate_mask_normalized, overlay_path)
    candidate_mask_normalized.save(normalized_path)
    return {
        "path": str(candidate_path),
        "normalized_path": str(normalized_path),
        "overlay_path": str(overlay_path),
        "effective_bbox": {
            "left": bbox.left,
            "top": bbox.top,
            "right": bbox.right,
            "bottom": bbox.bottom,
            "width": bbox.width,
            "height": bbox.height,
        },
        "normalized_iou": candidate_iou,
        "anchor_error": candidate_anchor_error,
        "score": score,
        "anchors": {key: list(value) if value is not None else None for key, value in candidate_anchors.items()},
    }


def evaluate_fail_rules(
    candidate: dict[str, Any],
    *,
    reference_effective_bbox: EffectiveBBox,
    reference_anchors: dict[str, tuple[int, int] | None],
    active_key_color: str,
) -> list[str]:
    fail_reasons: list[str] = []
    if candidate["normalized_iou"] < MIN_NORMALIZED_IOU:
        fail_reasons.append("normalized_iou_too_low")
    if candidate["anchor_error"] > MAX_ANCHOR_ERROR:
        fail_reasons.append("anchor_error_too_high")

    bbox = candidate["effective_bbox"]
    width_ratio = bbox["width"] / reference_effective_bbox.width
    height_ratio = bbox["height"] / reference_effective_bbox.height
    if width_ratio < MIN_EFFECTIVE_SCALE_RATIO:
        fail_reasons.append("effective_width_too_small")
    if height_ratio < MIN_EFFECTIVE_SCALE_RATIO:
        fail_reasons.append("effective_height_too_small")

    anchors = candidate["anchors"]
    for anchor_name in ("left_shoulder", "right_shoulder", "left_mid", "right_mid", "bottom_tip"):
        if anchors.get(anchor_name) is None:
            fail_reasons.append(f"missing_{anchor_name}")

    def anchor_tuple(name: str) -> tuple[int, int] | None:
        value = anchors.get(name)
        return (int(value[0]), int(value[1])) if value is not None else None

    left_shoulder = anchor_tuple("left_shoulder")
    right_shoulder = anchor_tuple("right_shoulder")
    left_mid = anchor_tuple("left_mid")
    right_mid = anchor_tuple("right_mid")
    bottom_tip = anchor_tuple("bottom_tip")

    ref_left_shoulder = reference_anchors["left_shoulder"]
    ref_right_shoulder = reference_anchors["right_shoulder"]
    ref_left_mid = reference_anchors["left_mid"]
    ref_right_mid = reference_anchors["right_mid"]
    ref_bottom_tip = reference_anchors["bottom_tip"]

    if left_shoulder is not None and ref_left_shoulder is not None and left_shoulder[0] - ref_left_shoulder[0] > MAX_SHOULDER_INSET:
        fail_reasons.append("left_shoulder_inset_too_large")
    if right_shoulder is not None and ref_right_shoulder is not None and ref_right_shoulder[0] - right_shoulder[0] > MAX_SHOULDER_INSET:
        fail_reasons.append("right_shoulder_inset_too_large")
    if left_mid is not None and ref_left_mid is not None and left_mid[0] - ref_left_mid[0] > MAX_MID_INSET:
        fail_reasons.append("left_mid_inset_too_large")
    if right_mid is not None and ref_right_mid is not None and ref_right_mid[0] - right_mid[0] > MAX_MID_INSET:
        fail_reasons.append("right_mid_inset_too_large")
    if bottom_tip is not None and ref_bottom_tip is not None and abs(bottom_tip[1] - ref_bottom_tip[1]) > MAX_BOTTOM_TIP_DRIFT:
        fail_reasons.append("bottom_tip_drift_too_large")

    contamination = top_boundary_key_contamination(Path(candidate["path"]), active_key_color=active_key_color)
    candidate["top_boundary_contamination"] = contamination
    if contamination["fail"]:
        fail_reasons.append("top_boundary_key_contamination")

    return fail_reasons


def fail_reason_cutoff_direction(fail_reasons: list[str]) -> str | None:
    if "top_boundary_key_contamination" in fail_reasons:
        return "more_conservative"
    geometry_fail_reasons = {
        "normalized_iou_too_low",
        "anchor_error_too_high",
        "effective_width_too_small",
        "effective_height_too_small",
        "missing_left_shoulder",
        "missing_right_shoulder",
        "missing_left_mid",
        "missing_right_mid",
        "missing_bottom_tip",
        "left_shoulder_inset_too_large",
        "right_shoulder_inset_too_large",
        "left_mid_inset_too_large",
        "right_mid_inset_too_large",
        "bottom_tip_drift_too_large",
    }
    if any(reason in geometry_fail_reasons for reason in fail_reasons):
        return "more_aggressive"
    return None


def select_variant_pool(run_root: Path, *, variant: str = "full") -> dict[str, Any]:
    request = load_json(run_root / "request" / "request.json")
    validation_path = run_root / "validation" / "validation.json"
    validation_payload = load_json(validation_path) if validation_path.exists() else {}
    preprocessing_payload = validation_payload.get("preprocessing", {}).get(variant, {})
    active_key_color = str(preprocessing_payload.get("active_key_color", request.get("background", {}).get("prompt_color", "#FF00FF")))
    reference_path = Path(request["references"][variant])
    reference_mask_normalized, reference_bbox = normalize_mask(alpha_mask(Image.open(reference_path).convert("RGBA")))
    reference_anchors = mask_anchors(reference_mask_normalized)

    generated_dir = run_root / "generated"
    candidates = [generated_dir / f"generated_{variant}.{name}.png" for name in KNOWN_VARIANTS]
    missing = [str(path) for path in candidates if not path.exists()]
    if missing:
        raise VariantSelectorError(f"Missing variant candidate(s): {', '.join(missing)}")

    output_dir = run_root / "selection" / variant
    output_dir.mkdir(parents=True, exist_ok=True)
    reference_mask_normalized.save(output_dir / "reference.normalized.png")

    scored = [score_candidate(candidate, reference_mask_normalized, reference_anchors, output_dir) for candidate in candidates]
    candidate_by_name = {Path(candidate["path"]).stem.replace(f"generated_{variant}.", ""): candidate for candidate in scored}
    ordered_names = [name for name in KNOWN_VARIANTS if name in candidate_by_name]
    ordered_candidates = [candidate_by_name[name] for name in ordered_names]

    pass_candidates: list[dict[str, Any]] = []
    failed_candidates: list[dict[str, Any]] = []
    base_fail_reasons_by_name: dict[str, list[str]] = {}
    base_cutoff_by_name: dict[str, str | None] = {}
    for candidate in ordered_candidates:
        fail_reasons = evaluate_fail_rules(
            candidate,
            reference_effective_bbox=reference_bbox,
            reference_anchors=reference_anchors,
            active_key_color=active_key_color,
        )
        candidate_name = Path(candidate["path"]).stem.replace(f"generated_{variant}.", "")
        base_fail_reasons_by_name[candidate_name] = fail_reasons
        base_cutoff_by_name[candidate_name] = fail_reason_cutoff_direction(fail_reasons)

    blocked_names: dict[str, str] = {}
    for index, name in enumerate(ordered_names):
        fail_reasons = base_fail_reasons_by_name[name]
        cutoff_direction = base_cutoff_by_name[name]
        if not fail_reasons or cutoff_direction is None:
            continue
        if cutoff_direction == "more_aggressive":
            affected = ordered_names[index + 1 :]
        elif cutoff_direction == "more_conservative":
            affected = ordered_names[:index]
        else:
            affected = []
        for affected_name in affected:
            if affected_name not in blocked_names:
                blocked_names[affected_name] = f"blocked_by_{cutoff_direction}_after_fail"

    for candidate in ordered_candidates:
        candidate_name = Path(candidate["path"]).stem.replace(f"generated_{variant}.", "")
        fail_reasons = list(base_fail_reasons_by_name[candidate_name])
        if candidate_name in blocked_names:
            fail_reasons = fail_reasons + [blocked_names[candidate_name]]
        candidate["fail_reasons"] = fail_reasons
        candidate["passed"] = len(fail_reasons) == 0
        if candidate["passed"]:
            pass_candidates.append(candidate)
        else:
            failed_candidates.append(candidate)
    pass_candidates.sort(key=lambda item: item["score"], reverse=True)

    result = {
        "ok": True,
        "run_root": str(run_root),
        "variant": variant,
        "reference": {
            "path": str(reference_path),
            "normalized_path": str(output_dir / "reference.normalized.png"),
            "effective_bbox": {
                "left": reference_bbox.left,
                "top": reference_bbox.top,
                "right": reference_bbox.right,
                "bottom": reference_bbox.bottom,
                "width": reference_bbox.width,
                "height": reference_bbox.height,
            },
            "anchors": {key: list(value) if value is not None else None for key, value in reference_anchors.items()},
        },
        "active_key_color": active_key_color,
        "fail_rule_thresholds": {
            "min_normalized_iou": MIN_NORMALIZED_IOU,
            "max_anchor_error": MAX_ANCHOR_ERROR,
            "max_shoulder_inset": MAX_SHOULDER_INSET,
            "max_mid_inset": MAX_MID_INSET,
            "max_bottom_tip_drift": MAX_BOTTOM_TIP_DRIFT,
            "min_effective_scale_ratio": MIN_EFFECTIVE_SCALE_RATIO,
            "top_boundary_scan_ratio": TOP_BOUNDARY_SCAN_RATIO,
            "top_boundary_key_similarity_fail": TOP_BOUNDARY_KEY_SIMILARITY_FAIL,
            "top_boundary_key_pixel_ratio_fail": TOP_BOUNDARY_KEY_PIXEL_RATIO_FAIL,
            "top_boundary_key_pixel_count_fail": TOP_BOUNDARY_KEY_PIXEL_COUNT_FAIL,
            "top_boundary_key_run_fail": TOP_BOUNDARY_KEY_RUN_FAIL,
        },
        "pass_candidates": pass_candidates,
        "failed_candidates": failed_candidates,
        "selected": pass_candidates[0] if pass_candidates else None,
    }
    write_json(run_root / "selection" / f"{variant}.selection.json", result)
    return result
