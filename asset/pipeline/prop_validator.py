from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw

ALPHA_OBJECT_THRESHOLD = 32

DEFAULT_PROP_VALIDATION = {
    "canvas_width": 128,
    "canvas_height": 256,
    "min_side_margin_px": 3,
    "min_top_margin_px": 3,
    "min_bbox_width_px": 16,
    "min_bbox_height_px": 16,
    "max_bbox_width_px": 124,
    "max_bbox_height_px": 252,
    "bottom_anchor_tolerance_px": 8,
    "center_x_tolerance_px": 12,
    "max_background_low_alpha_pixels": 256,
    "max_corner_alpha_mean": 8,
    "min_opaque_pixel_ratio": 0.01,
    "max_opaque_pixel_ratio": 0.70,
    "max_corner_opaque_pixels": 16,
    "max_floor_side_opaque_pixels": 1200,
    "max_floor_span_width_px": 124,
    "max_pair_width_delta_ratio": 0.28,
    "max_pair_height_delta_ratio": 0.35,
    "max_pair_center_delta_px": 12,
    "max_pair_bottom_delta_px": 8,
}


class PropValidationError(RuntimeError):
    pass


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def alpha_mask(image: Image.Image, *, threshold: int = ALPHA_OBJECT_THRESHOLD) -> Image.Image:
    return image.convert("RGBA").getchannel("A").point(lambda value: 255 if value >= threshold else 0, mode="L")


def mask_area(mask: Image.Image) -> int:
    histogram = mask.histogram()
    return int(histogram[255]) if len(histogram) > 255 else 0


def _bbox_payload(bbox: tuple[int, int, int, int] | None) -> dict[str, Any] | None:
    if bbox is None:
        return None
    left, top, right, bottom = bbox
    return {
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "right_inclusive": right - 1,
        "bottom_inclusive": bottom - 1,
        "width": right - left,
        "height": bottom - top,
        "center_x": (left + right - 1) / 2.0,
        "center_y": (top + bottom - 1) / 2.0,
    }


def _alpha_centroid(mask: Image.Image) -> tuple[float, float] | None:
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
    return sum_x / count, sum_y / count


def _low_alpha_background_pixels(image: Image.Image, bbox: tuple[int, int, int, int] | None) -> int:
    if bbox is None:
        return 0
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    pixels = alpha.load()
    left, top, right, bottom = bbox
    count = 0
    for y in range(rgba.height):
        for x in range(rgba.width):
            inside_bbox = left <= x < right and top <= y < bottom
            value = pixels[x, y]
            if not inside_bbox and 0 < value < ALPHA_OBJECT_THRESHOLD:
                count += 1
    return count


def _corner_opaque_pixels(mask: Image.Image, *, corner_size: int = 32) -> dict[str, int]:
    pixels = mask.load()
    corners = {
        "top_left": (0, 0, corner_size, corner_size),
        "top_right": (mask.width - corner_size, 0, mask.width, corner_size),
        "bottom_left": (0, mask.height - corner_size, corner_size, mask.height),
        "bottom_right": (mask.width - corner_size, mask.height - corner_size, mask.width, mask.height),
    }
    counts: dict[str, int] = {}
    for name, (x0, y0, x1, y1) in corners.items():
        count = 0
        for y in range(max(0, y0), min(mask.height, y1)):
            for x in range(max(0, x0), min(mask.width, x1)):
                if pixels[x, y] >= 128:
                    count += 1
        counts[name] = count
    return counts


def _corner_alpha_means(image: Image.Image, *, corner_size: int = 32) -> dict[str, float]:
    alpha = image.convert("RGBA").getchannel("A")
    pixels = alpha.load()
    corners = {
        "top_left": (0, 0, corner_size, corner_size),
        "top_right": (alpha.width - corner_size, 0, alpha.width, corner_size),
        "bottom_left": (0, alpha.height - corner_size, corner_size, alpha.height),
        "bottom_right": (alpha.width - corner_size, alpha.height - corner_size, alpha.width, alpha.height),
    }
    means: dict[str, float] = {}
    for name, (x0, y0, x1, y1) in corners.items():
        total = 0
        count = 0
        for y in range(max(0, y0), min(alpha.height, y1)):
            for x in range(max(0, x0), min(alpha.width, x1)):
                total += int(pixels[x, y])
                count += 1
        means[name] = total / max(1, count)
    return means


def _floor_tile_heuristic(mask: Image.Image, *, anchor_x: int, anchor_y: int, thresholds: dict[str, Any]) -> dict[str, Any]:
    """Detect a likely baked-in 1x1 floor diamond under a prop.

    This is intentionally conservative and engineering-oriented.  It only flags
    large side-floor occupancy near the bottom anchor, not normal prop bases.
    """
    floor_mask = Image.new("L", mask.size, 0)
    draw = ImageDraw.Draw(floor_mask)
    top_y = max(0, anchor_y - 64)
    mid_y = max(0, anchor_y - 32)
    draw.polygon(
        [
            (anchor_x, top_y),
            (mask.width - 1, mid_y),
            (anchor_x, min(mask.height - 1, anchor_y)),
            (0, mid_y),
        ],
        fill=255,
    )
    central_clear = Image.new("L", mask.size, 0)
    clear_draw = ImageDraw.Draw(central_clear)
    clear_draw.rectangle((anchor_x - 28, top_y, anchor_x + 28, min(mask.height - 1, anchor_y)), fill=255)
    side_floor_zone = ImageChops.subtract(floor_mask, central_clear)
    opaque_in_side_floor = ImageChops.multiply(mask, side_floor_zone)
    side_floor_pixels = mask_area(opaque_in_side_floor)

    pixels = mask.load()
    max_span_width = 0
    bottom_scan_top = max(0, anchor_y - 72)
    for y in range(bottom_scan_top, min(mask.height, anchor_y + 1)):
        xs = [x for x in range(mask.width) if pixels[x, y] >= 128]
        if xs:
            max_span_width = max(max_span_width, max(xs) - min(xs) + 1)

    fail = (
        side_floor_pixels > int(thresholds["max_floor_side_opaque_pixels"])
        or max_span_width > int(thresholds["max_floor_span_width_px"])
    )
    return {
        "fail": fail,
        "side_floor_opaque_pixels": side_floor_pixels,
        "max_span_width_near_anchor": max_span_width,
        "thresholds": {
            "max_floor_side_opaque_pixels": int(thresholds["max_floor_side_opaque_pixels"]),
            "max_floor_span_width_px": int(thresholds["max_floor_span_width_px"]),
        },
    }


def _make_checker(size: tuple[int, int], *, cell: int = 8) -> Image.Image:
    image = Image.new("RGBA", size, (220, 220, 220, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if ((x // cell) + (y // cell)) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(180, 180, 180, 255))
    return image


def write_debug_overlay(
    image: Image.Image,
    *,
    output_path: Path,
    bbox: tuple[int, int, int, int] | None,
    anchor_x: int,
    anchor_y: int,
    center_x: float | None,
    status: str,
) -> str:
    canvas = _make_checker(image.size)
    canvas.alpha_composite(image.convert("RGBA"))
    draw = ImageDraw.Draw(canvas)
    if bbox is not None:
        left, top, right, bottom = bbox
        color = (80, 255, 120, 255) if status == "pass" else (255, 80, 80, 255)
        draw.rectangle((left, top, right - 1, bottom - 1), outline=color, width=2)
    draw.line((anchor_x - 8, anchor_y, anchor_x + 8, anchor_y), fill=(80, 160, 255, 255), width=2)
    draw.line((anchor_x, anchor_y - 8, anchor_x, anchor_y), fill=(80, 160, 255, 255), width=2)
    draw.line((anchor_x, 0, anchor_x, image.height - 1), fill=(80, 160, 255, 140), width=1)
    if center_x is not None:
        draw.line((center_x, 0, center_x, image.height - 1), fill=(255, 220, 80, 200), width=1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return str(output_path)


def _normalized_thresholds(validation_spec: dict[str, Any] | None, canvas: dict[str, Any]) -> dict[str, Any]:
    thresholds = dict(DEFAULT_PROP_VALIDATION)
    if validation_spec:
        thresholds.update({key: value for key, value in validation_spec.items() if key in thresholds})
    thresholds["canvas_width"] = int(canvas.get("width", thresholds["canvas_width"]))
    thresholds["canvas_height"] = int(canvas.get("height", thresholds["canvas_height"]))
    return thresholds


def validate_single_prop_asset(
    *,
    image_path: Path,
    asset_id: str,
    role: str,
    spec: dict[str, Any],
    thresholds: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    opened = Image.open(image_path)
    original_mode = opened.mode
    image = opened.convert("RGBA")
    mask = alpha_mask(image)
    bbox = mask.getbbox()
    bbox_info = _bbox_payload(bbox)
    centroid = _alpha_centroid(mask)
    anchor = spec.get("anchor", {}) if isinstance(spec.get("anchor"), dict) else {}
    anchor_x = int(anchor.get("x", image.width // 2))
    anchor_y = int(anchor.get("y", image.height - 1))

    failures: list[str] = []
    diagnostics: dict[str, Any] = {}

    has_alpha_channel = "A" in opened.getbands()
    diagnostics["has_alpha_channel"] = has_alpha_channel
    if not has_alpha_channel:
        failures.append(f"png_missing_alpha_channel:{original_mode}")
    elif original_mode != "RGBA":
        failures.append(f"png_mode_not_rgba:{original_mode}")
    expected_size = (int(thresholds["canvas_width"]), int(thresholds["canvas_height"]))
    if image.size != expected_size:
        failures.append(f"canvas_size_mismatch:{image.width}x{image.height}:expected_{expected_size[0]}x{expected_size[1]}")
    total_pixels = max(1, image.width * image.height)
    opaque_ratio = mask_area(mask) / total_pixels
    diagnostics["opaque_pixel_ratio"] = opaque_ratio
    if opaque_ratio < float(thresholds["min_opaque_pixel_ratio"]):
        failures.append(f"opaque_pixel_ratio_too_small:{opaque_ratio:.4f}")
    if opaque_ratio > float(thresholds["max_opaque_pixel_ratio"]):
        failures.append(f"opaque_pixel_ratio_too_large:{opaque_ratio:.4f}")
    if bbox is None:
        failures.append("missing_opaque_bbox")
    else:
        left, top, right, bottom = bbox
        bbox_width = right - left
        bbox_height = bottom - top
        diagnostics["bbox_padding"] = {
            "left": left,
            "right": image.width - right,
            "top": top,
            "bottom": image.height - bottom,
        }
        if bbox_width < int(thresholds["min_bbox_width_px"]):
            failures.append(f"bbox_width_too_small:{bbox_width}px")
        if bbox_height < int(thresholds["min_bbox_height_px"]):
            failures.append(f"bbox_height_too_small:{bbox_height}px")
        if bbox_width > int(thresholds["max_bbox_width_px"]):
            failures.append(f"bbox_width_too_large:{bbox_width}px")
        if bbox_height > int(thresholds["max_bbox_height_px"]):
            failures.append(f"bbox_height_too_large:{bbox_height}px")
        side_margin = int(thresholds["min_side_margin_px"])
        top_margin = int(thresholds["min_top_margin_px"])
        if left < side_margin:
            failures.append("opaque_bbox_touches_left_edge")
        if right > image.width - side_margin:
            failures.append("opaque_bbox_touches_right_edge")
        if top < top_margin:
            failures.append("opaque_bbox_touches_top_edge")
        bottom_y = bottom - 1
        bottom_gap = abs(anchor_y - bottom_y)
        diagnostics["bottom_anchor_gap_px"] = bottom_gap
        if bottom_gap > int(thresholds["bottom_anchor_tolerance_px"]):
            failures.append(f"bottom_not_close_to_anchor:{bottom_gap}px")
        bbox_center_x = (left + right - 1) / 2.0
        centroid_x = centroid[0] if centroid is not None else bbox_center_x
        center_error = min(abs(bbox_center_x - anchor_x), abs(centroid_x - anchor_x))
        diagnostics["bbox_center_x_error_px"] = abs(bbox_center_x - anchor_x)
        diagnostics["centroid_x_error_px"] = abs(centroid_x - anchor_x)
        if center_error > float(thresholds["center_x_tolerance_px"]):
            failures.append(f"object_center_x_too_far:{center_error:.2f}px")

    low_alpha_count = _low_alpha_background_pixels(image, bbox)
    diagnostics["background_low_alpha_pixels"] = low_alpha_count
    if low_alpha_count > int(thresholds["max_background_low_alpha_pixels"]):
        failures.append("background_alpha_not_clean")

    corner_counts = _corner_opaque_pixels(mask)
    diagnostics["corner_opaque_pixels"] = corner_counts
    corner_alpha_means = _corner_alpha_means(image)
    diagnostics["corner_alpha_mean"] = corner_alpha_means
    # Bottom-corner alpha can be valid for bottom-anchored props with legs/bases
    # near the contact anchor.  Top corners remain the background-cleanliness guard.
    top_corner_alpha_means = {key: value for key, value in corner_alpha_means.items() if key.startswith("top_")}
    if any(mean > float(thresholds["max_corner_alpha_mean"]) for mean in top_corner_alpha_means.values()):
        failures.append("corner_alpha_not_transparent")
    top_corner_counts = {key: value for key, value in corner_counts.items() if key.startswith("top_")}
    if any(count > int(thresholds["max_corner_opaque_pixels"]) for count in top_corner_counts.values()):
        failures.append("possible_text_or_watermark_in_canvas_corner")

    floor_check = _floor_tile_heuristic(mask, anchor_x=anchor_x, anchor_y=anchor_y, thresholds=thresholds)
    diagnostics["baked_floor_tile_check"] = floor_check
    if floor_check["fail"]:
        failures.append("possible_baked_floor_tile")

    status = "pass" if not failures else "hard_fail"
    overlay_path = write_debug_overlay(
        image,
        output_path=output_dir / f"debug_overlay_{asset_id}.png",
        bbox=bbox,
        anchor_x=anchor_x,
        anchor_y=min(anchor_y, image.height - 1),
        center_x=centroid[0] if centroid is not None else None,
        status=status,
    )
    return {
        "asset_id": asset_id,
        "role": role,
        "status": status,
        "failures": failures,
        "image_path": str(image_path),
        "mode": original_mode,
        "size": [image.width, image.height],
        "bbox": bbox_info,
        "area_pixels": mask_area(mask),
        "centroid": list(centroid) if centroid is not None else None,
        "anchor": {"type": anchor.get("type", "bottom_center"), "x": anchor_x, "y": anchor_y},
        "diagnostics": diagnostics,
        "debug_overlay": overlay_path,
    }


def validate_prop_asset_set(
    *,
    spec: dict[str, Any],
    asset_paths: dict[str, Path],
    output_dir: Path,
) -> dict[str, Any]:
    canvas = spec.get("canvas", {}) if isinstance(spec.get("canvas"), dict) else {}
    validation_spec = spec.get("validation", {}) if isinstance(spec.get("validation"), dict) else {}
    thresholds = _normalized_thresholds(validation_spec, canvas)
    states = spec.get("states", [])
    if not isinstance(states, list) or not states:
        raise PropValidationError("prop asset spec must contain non-empty states array")

    per_asset: dict[str, Any] = {}
    for state in states:
        if not isinstance(state, dict):
            raise PropValidationError("each prop asset state must be an object")
        asset_id = str(state.get("asset_id", "")).strip()
        role = str(state.get("role", "")).strip()
        if not asset_id:
            raise PropValidationError("state.asset_id must be non-empty")
        image_path = asset_paths.get(asset_id)
        if image_path is None:
            raise PropValidationError(f"missing image path for asset_id '{asset_id}'")
        if not image_path.exists():
            raise PropValidationError(f"missing image file for asset_id '{asset_id}': {image_path}")
        per_asset[asset_id] = validate_single_prop_asset(
            image_path=image_path,
            asset_id=asset_id,
            role=role,
            spec=spec,
            thresholds=thresholds,
            output_dir=output_dir,
        )

    pair_consistency = _validate_pair_consistency(per_asset, thresholds)
    statuses = [item["status"] for item in per_asset.values()]
    if pair_consistency["status"] != "pass":
        statuses.append(pair_consistency["status"])
    final_status = "hard_fail" if "hard_fail" in statuses else "pass"
    result = {
        "ok": final_status == "pass",
        "status": final_status,
        "schema_version": "prop_asset_validation_v1",
        "asset_family": spec.get("asset_family"),
        "thresholds": thresholds,
        "assets": per_asset,
        "pair_consistency": pair_consistency,
    }
    write_json(output_dir / "validation_summary.json", result)
    return result


def _validate_pair_consistency(per_asset: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    if len(per_asset) < 2:
        return {"status": "skipped", "failures": ["pair consistency skipped because fewer than two assets were supplied"]}
    asset_items = list(per_asset.values())
    usable = [item for item in asset_items if item.get("bbox")]
    if len(usable) < 2:
        return {"status": "hard_fail", "failures": ["pair consistency could not compare opaque bboxes"]}
    base = usable[0]
    failures: list[str] = []
    comparisons: list[dict[str, Any]] = []
    for other in usable[1:]:
        base_bbox = base["bbox"]
        other_bbox = other["bbox"]
        width_delta = abs(float(other_bbox["width"]) - float(base_bbox["width"]))
        height_delta = abs(float(other_bbox["height"]) - float(base_bbox["height"]))
        width_ratio = width_delta / max(1.0, float(base_bbox["width"]))
        height_ratio = height_delta / max(1.0, float(base_bbox["height"]))
        center_delta = abs(float(other_bbox["center_x"]) - float(base_bbox["center_x"]))
        bottom_delta = abs(float(other_bbox["bottom_inclusive"]) - float(base_bbox["bottom_inclusive"]))
        comparison = {
            "base_asset_id": base["asset_id"],
            "other_asset_id": other["asset_id"],
            "width_delta_ratio": width_ratio,
            "height_delta_ratio": height_ratio,
            "center_x_delta_px": center_delta,
            "bottom_delta_px": bottom_delta,
        }
        comparisons.append(comparison)
        if width_ratio > float(thresholds["max_pair_width_delta_ratio"]):
            failures.append(f"pair_bbox_width_delta_too_large:{other['asset_id']}")
        if height_ratio > float(thresholds["max_pair_height_delta_ratio"]):
            failures.append(f"pair_bbox_height_delta_too_large:{other['asset_id']}")
        if center_delta > float(thresholds["max_pair_center_delta_px"]):
            failures.append(f"pair_center_x_delta_too_large:{other['asset_id']}")
        if bottom_delta > float(thresholds["max_pair_bottom_delta_px"]):
            failures.append(f"pair_bottom_delta_too_large:{other['asset_id']}")
    return {
        "status": "pass" if not failures else "hard_fail",
        "failures": failures,
        "comparisons": comparisons,
    }
