from __future__ import annotations

import json
import math
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw
from pipeline.reference_pair_workflow import (
    _cleanup_artifact_token,
    _copy_artifact,
    _update_deliverable_manifest,
    color_key_similarity,
    parse_hex_color,
    update_step_status_summary,
    write_json,
)


TARGET_SIZE = 128
REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_TILE_SPEC_PATH = REPO_ROOT / "examples" / "workflow_references" / "canonical_tile_spec.json"

KNOWN_VARIANTS = (
    "01_conservative",
    "02_conservative_plus",
    "03_balanced",
    "04_balanced_plus",
    "05_aggressive",
    "06_aggressive_plus",
)
FAIL_RULES_BY_VARIANT = {
    "full": {
        "min_normalized_iou": 0.94,
        "max_anchor_error": 3.0,
        "max_shoulder_inset": 2,
        "max_mid_inset": 2,
        "max_bottom_tip_drift": 3,
        "min_effective_scale_ratio": 0.88,
        "top_boundary_scan_ratio": 0.35,
        "top_boundary_key_similarity_fail": 0.55,
        "top_boundary_key_pixel_ratio_fail": 0.03,
        "top_boundary_key_pixel_count_fail": 8,
        "top_boundary_key_run_fail": 3,
    },
    "half": {
        "min_normalized_iou": 0.91,
        "max_anchor_error": 3.0,
        "max_shoulder_inset": 4,
        "max_mid_inset": 2,
        "max_bottom_tip_drift": 3,
        "min_effective_scale_ratio": 0.88,
        "top_boundary_scan_ratio": 0.35,
        "top_boundary_key_similarity_fail": 0.55,
        "top_boundary_key_pixel_ratio_fail": 0.03,
        "top_boundary_key_pixel_count_fail": 8,
        "top_boundary_key_run_fail": 3,
    },
    "wall": {
        "min_normalized_iou": 0.90,
        "max_anchor_error": 10.0,
        "max_shoulder_inset": 24,
        "max_mid_inset": 2,
        "max_bottom_tip_drift": 12,
        "min_effective_scale_ratio": 0.88,
        "top_boundary_scan_ratio": 0.35,
        "top_boundary_key_similarity_fail": 0.55,
        "top_boundary_key_pixel_ratio_fail": 0.03,
        "top_boundary_key_pixel_count_fail": 8,
        "top_boundary_key_run_fail": 3,
    },
}


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


def _premultiply_rgba(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    premultiplied = []
    for r, g, b, a in rgba.getdata():
        premultiplied.append((
            (r * a + 127) // 255,
            (g * a + 127) // 255,
            (b * a + 127) // 255,
            a,
        ))
    result = Image.new("RGBA", rgba.size)
    result.putdata(premultiplied)
    return result


def _unpremultiply_rgba(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    restored = []
    for r, g, b, a in rgba.getdata():
        if a <= 0:
            restored.append((0, 0, 0, 0))
            continue
        restored.append((
            min(255, (r * 255 + a // 2) // a),
            min(255, (g * 255 + a // 2) // a),
            min(255, (b * 255 + a // 2) // a),
            a,
        ))
    result = Image.new("RGBA", rgba.size)
    result.putdata(restored)
    return result


def polygon_bbox(points: list[list[int]]) -> EffectiveBBox:
    xs = [int(point[0]) for point in points]
    ys = [int(point[1]) for point in points]
    return EffectiveBBox(left=min(xs), top=min(ys), right=max(xs), bottom=max(ys))


def canonical_tile_spec() -> dict[str, Any]:
    return load_json(CANONICAL_TILE_SPEC_PATH)


def infer_canonical_tile_key(*, variant: str, selector_profile: str, variant_profile: dict[str, Any]) -> str | None:
    if selector_profile == "wall":
        wall_profile = variant_profile.get("wall_profile", {}) if isinstance(variant_profile, dict) else {}
        height_units_raw = wall_profile.get("height_units") if isinstance(wall_profile, dict) else None
        height_units: int | None = None
        if height_units_raw is not None and str(height_units_raw).strip():
            try:
                height_units = int(height_units_raw)
            except (TypeError, ValueError):
                height_units = None
        if height_units not in {1, 2}:
            role_text = str(variant_profile.get("role_text", "")).strip().lower()
            height_units = 2 if "two-tile-high" in role_text or "2u" in role_text else 1
        height_suffix = "2u" if height_units == 2 else "1u"
        if variant in {"left", "right"}:
            return f"wall_{variant}_{height_suffix}"
    if variant in {"full", "half"}:
        return f"floor_{variant}"
    return None


def canonical_target_for_variant(*, variant: str, selector_profile: str, variant_profile: dict[str, Any]) -> dict[str, Any] | None:
    tile_key = infer_canonical_tile_key(variant=variant, selector_profile=selector_profile, variant_profile=variant_profile)
    if tile_key is None:
        return None
    spec = canonical_tile_spec()
    tile = spec.get("tiles", {}).get(tile_key)
    if not isinstance(tile, dict):
        return None
    canvas = tile.get("canvas", {})
    if not isinstance(canvas, dict):
        return None
    target_polygon = tile.get("body")
    if not isinstance(target_polygon, list):
        faces = tile.get("faces", {})
        if isinstance(faces, dict):
            target_polygon = []
            for face_name in ("top", "left", "right"):
                face_points = faces.get(face_name)
                if isinstance(face_points, list):
                    target_polygon.extend(face_points)
    if not isinstance(target_polygon, list) or not target_polygon:
        return None
    if str(tile_key).startswith("wall_"):
        target_polygon = _wall_canonical_polygon(
            canvas_width=int(canvas.get("width", TARGET_SIZE)),
            canvas_height=int(canvas.get("height", TARGET_SIZE)),
            wall_side="left" if "_left_" in tile_key else "right",
            target_tile=tile,
        )
    target_bbox = polygon_bbox(target_polygon)
    return {
        "tile_key": tile_key,
        "canvas_width": int(canvas.get("width", TARGET_SIZE)),
        "canvas_height": int(canvas.get("height", TARGET_SIZE)),
        "target_bbox": target_bbox,
        "target_polygon": target_polygon,
        "contact_edge": tile.get("contact_edge"),
        "anchors": tile.get("anchors", {}),
        "placement": tile.get("placement", {}),
    }


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
    left, top, right0, bottom0 = bbox
    return EffectiveBBox(left=left, top=top, right=right0 - 1, bottom=bottom0 - 1)


def normalize_mask(mask: Image.Image, *, target_size: int = TARGET_SIZE) -> tuple[Image.Image, EffectiveBBox]:
    bbox = effective_bbox(mask)
    cropped = mask.crop((bbox.left, bbox.top, bbox.right + 1, bbox.bottom + 1))
    normalized = cropped.resize((target_size, target_size), Image.NEAREST)
    return normalized, bbox


def normalize_rgba_image(image: Image.Image, *, target_size: int = TARGET_SIZE) -> tuple[Image.Image, EffectiveBBox]:
    bbox = effective_bbox(alpha_mask(image))
    cropped = image.crop((bbox.left, bbox.top, bbox.right + 1, bbox.bottom + 1))
    normalized = cropped.resize((target_size, target_size), Image.NEAREST)
    return normalized, bbox


def raw_alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    bbox = alpha_mask(image).getbbox()
    if bbox is None:
        raise VariantSelectorError("Image has no opaque pixels.")
    return bbox


def _needs_left_edge_nudge(canvas: Image.Image) -> bool:
    scale = canvas.height / TARGET_SIZE if TARGET_SIZE else 1.0
    checkpoints = (
        (0, int(round(32 * scale))),
        (0, int(round(33 * scale))),
    )
    for x, y in checkpoints:
        if x >= canvas.width or y >= canvas.height:
            return False
        if canvas.getpixel((x, y))[3] < 32:
            return True
    return False


def _shift_canvas(canvas: Image.Image, *, dx: int = 0, dy: int = 0) -> Image.Image:
    shifted = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shifted.alpha_composite(canvas, (dx, dy))
    return shifted


def _align_canvas_bbox(
    canvas: Image.Image,
    *,
    target_left: int,
    target_top: int,
) -> Image.Image:
    bbox = alpha_mask(canvas).getbbox()
    if bbox is None:
        return canvas
    dx = target_left - bbox[0]
    dy = target_top - bbox[1]
    if dx == 0 and dy == 0:
        return canvas
    return _shift_canvas(canvas, dx=dx, dy=dy)


def _apply_polygon_mask(canvas: Image.Image, polygon: list[list[int]]) -> Image.Image:
    masked = canvas.copy()
    mask = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(int(point[0]), int(point[1])) for point in polygon], fill=255)
    alpha = masked.getchannel("A")
    masked.putalpha(ImageChops.multiply(alpha, mask))
    return masked


def _polygon_mask(size: tuple[int, int], polygon: list[list[int]]) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(int(point[0]), int(point[1])) for point in polygon], fill=255)
    return mask


def _apply_opaque_half_rule(canvas: Image.Image, opaque_half: str) -> Image.Image:
    if opaque_half not in {"left", "right"}:
        return canvas
    masked = canvas.copy()
    mask = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(mask)
    midpoint = canvas.width // 2
    if opaque_half == "left":
        draw.rectangle((0, 0, midpoint, canvas.height), fill=255)
    else:
        draw.rectangle((midpoint, 0, canvas.width, canvas.height), fill=255)
    alpha = masked.getchannel("A")
    masked.putalpha(ImageChops.multiply(alpha, mask))
    return masked


def _opaque_half_mask(size: tuple[int, int], opaque_half: str) -> Image.Image:
    mask = Image.new("L", size, 0)
    if opaque_half not in {"left", "right"}:
        ImageDraw.Draw(mask).rectangle((0, 0, size[0], size[1]), fill=255)
        return mask
    draw = ImageDraw.Draw(mask)
    midpoint = size[0] // 2
    if opaque_half == "left":
        draw.rectangle((0, 0, midpoint, size[1]), fill=255)
    else:
        draw.rectangle((midpoint, 0, size[0], size[1]), fill=255)
    return mask


def _wall_side_from_target(canonical_target: dict[str, Any]) -> str:
    tile_key = str(canonical_target.get("tile_key", "")).lower()
    if "_left_" in tile_key:
        return "left"
    if "_right_" in tile_key:
        return "right"
    placement = canonical_target.get("placement", {})
    attach_edge = str(placement.get("attach_edge", "")).strip().lower() if isinstance(placement, dict) else ""
    if attach_edge == "top_left":
        return "left"
    if attach_edge == "top_right":
        return "right"
    raise VariantSelectorError("Could not infer wall side from canonical target.")


def _clamp_point_to_canvas(point: tuple[float, float], *, width: int, height: int) -> tuple[float, float]:
    x, y = point
    return (
        min(max(float(x), 0.0), float(max(0, width - 1))),
        min(max(float(y), 0.0), float(max(0, height - 1))),
    )


def _wall_canonical_polygon(
    *,
    canvas_width: int,
    canvas_height: int,
    wall_side: str,
    target_tile: dict[str, Any],
) -> list[tuple[float, float]]:
    body = target_tile.get("body")
    if not isinstance(body, list) or len(body) != 4:
        raise VariantSelectorError("Canonical wall tile is missing a 4-point body polygon.")

    body_points = [
        _clamp_point_to_canvas((float(point[0]), float(point[1])), width=canvas_width, height=canvas_height)
        for point in body
    ]

    if wall_side == "left":
        side_bottom = body_points[0]
        side_top_point = body_points[1]
        top_tip_point = body_points[2]
        inner_bottom_point = body_points[3]
    else:
        inner_bottom_point = body_points[0]
        top_tip_point = body_points[1]
        side_top_point = body_points[2]
        side_bottom = body_points[3]

    outer_x = 0.0 if wall_side == "right" else float(max(0, canvas_width - 1))
    outer_top = _clamp_point_to_canvas((outer_x, float(side_top_point[1])), width=canvas_width, height=canvas_height)
    outer_bottom = _clamp_point_to_canvas((outer_x, float(side_bottom[1])), width=canvas_width, height=canvas_height)
    return [side_bottom, side_top_point, top_tip_point, outer_top, outer_bottom, inner_bottom_point]


def _wall_target_face_anchors(canonical_target: dict[str, Any]) -> list[tuple[float, float]]:
    canvas_width = int(canonical_target["canvas_width"])
    canvas_height = int(canonical_target["canvas_height"])
    polygon = canonical_target["target_polygon"]
    side = _wall_side_from_target(canonical_target)
    xs = [int(point[0]) for point in polygon]
    side_x_raw = min(xs) if side == "left" else max(xs)
    side_x = side_x_raw if side == "left" else min(side_x_raw, canvas_width - 1)
    side_points = [(int(point[0]), int(point[1])) for point in polygon if int(point[0]) == side_x_raw]
    if len(side_points) < 2:
        raise VariantSelectorError("Canonical wall polygon is missing the side-face vertical edge.")
    top_y = min(point[1] for point in side_points)
    bottom_y = max(point[1] for point in side_points)
    apex_raw = min(((int(point[0]), int(point[1])) for point in polygon), key=lambda point: (point[1], point[0]))
    apex = _clamp_point_to_canvas(apex_raw, width=canvas_width, height=canvas_height)
    return [
        _clamp_point_to_canvas((side_x, top_y), width=canvas_width, height=canvas_height),
        _clamp_point_to_canvas((side_x, bottom_y), width=canvas_width, height=canvas_height),
        apex,
    ]


def _row_span_or_error(mask: Image.Image, y: int, *, label: str) -> tuple[int, int]:
    span = row_span(mask, y)
    if span is None:
        raise VariantSelectorError(f"Wall source image is missing opaque pixels for {label}.")
    return span


def _wall_source_face_anchors(mask: Image.Image, *, wall_side: str) -> list[tuple[float, float]]:
    bbox = mask.getbbox()
    if bbox is None:
        raise VariantSelectorError("Wall source image has no opaque pixels.")
    pixels = mask.load()
    anchor_x = 0 if wall_side == "left" else mask.width - 1
    ys = [y for y in range(mask.height) if pixels[anchor_x, y] >= 128]
    if not ys:
        raise VariantSelectorError("Wall source edge did not contain opaque pixels for anchor extraction.")
    top_y = min(ys)
    bottom_y = max(ys)
    top_span = row_span(mask, 0)
    if top_span is None:
        raise VariantSelectorError("Wall source top row did not contain opaque pixels for anchor extraction.")
    top_center_x = (top_span[0] + top_span[1]) / 2.0
    return [
        (float(anchor_x), float(top_y)),
        (float(anchor_x), float(bottom_y)),
        (float(top_center_x), 0.0),
    ]



def _wall_source_deform_anchors(mask: Image.Image, *, wall_side: str) -> dict[str, tuple[float, float]]:
    bbox = mask.getbbox()
    if bbox is None:
        raise VariantSelectorError("Wall source image has no opaque pixels.")
    top_y = bbox[1]
    bottom_y = bbox[3] - 1

    apex_row_y = top_y
    apex_span = _row_span_or_error(mask, top_y, label="top row span")
    search_limit = min(bottom_y, top_y + 24)
    face_top_span = apex_span
    for y in range(top_y, search_limit + 1):
        span = row_span(mask, y)
        if span is None:
            continue
        if (span[1] - span[0]) >= 2:
            apex_row_y = y
            apex_span = span
            face_top_span = span
            break

    bottom_span = _row_span_or_error(mask, bottom_y, label="bottom row span")
    apex_x = (apex_span[0] + apex_span[1]) / 2.0
    if wall_side == "left":
        return {
            "face_top": (float(face_top_span[0]), float(apex_row_y)),
            "apex": (float(apex_x), float(top_y)),
            "top_outer": (float(apex_span[1]), float(apex_row_y)),
            "bottom_outer": (float(bottom_span[1]), float(bottom_y)),
            "face_bottom": (float(bottom_span[0]), float(bottom_y)),
        }
    return {
        "face_top": (float(face_top_span[1]), float(apex_row_y)),
        "apex": (float(apex_x), float(top_y)),
        "top_outer": (float(apex_span[0]), float(apex_row_y)),
        "bottom_outer": (float(bottom_span[0]), float(bottom_y)),
        "face_bottom": (float(bottom_span[1]), float(bottom_y)),
    }


# ---------------------------------------------------------------------------
# Wall iso-skew: line fitting, intersection, corner detection, perspective
# ---------------------------------------------------------------------------


def _fit_line(points: list[tuple[float, float]]) -> tuple[float, float, float]:
    """Fit line ``ax + by + c = 0`` to *points* via least squares.

    Automatically chooses the numerically stable parameterisation
    (``x = my + k`` when near-vertical, ``y = mx + k`` otherwise).
    Returns ``(a, b, c)`` normalised so ``a² + b² = 1``.
    """
    n = len(points)
    if n < 2:
        raise VariantSelectorError("Need at least 2 points to fit a line.")
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_range = max(xs) - min(xs)
    y_range = max(ys) - min(ys)

    if y_range >= x_range:
        # Near-vertical: fit x = m·y + k
        sum_t = sum(ys)
        sum_v = sum(xs)
        sum_tt = sum(y * y for y in ys)
        sum_tv = sum(y * x for x, y in points)
        det = float(n) * sum_tt - sum_t * sum_t
        if abs(det) < 1e-12:
            raise VariantSelectorError("Degenerate line fit (all points at same y).")
        m = (float(n) * sum_tv - sum_t * sum_v) / det
        k = (sum_tt * sum_v - sum_t * sum_tv) / det
        a, b, c = 1.0, -m, -k
    else:
        # Fit y = m·x + k
        sum_t = sum(xs)
        sum_v = sum(ys)
        sum_tt = sum(x * x for x in xs)
        sum_tv = sum(x * y for x, y in points)
        det = float(n) * sum_tt - sum_t * sum_t
        if abs(det) < 1e-12:
            raise VariantSelectorError("Degenerate line fit (all points at same x).")
        m = (float(n) * sum_tv - sum_t * sum_v) / det
        k = (sum_tt * sum_v - sum_t * sum_tv) / det
        a, b, c = m, -1.0, k

    norm = math.hypot(a, b)
    return (a / norm, b / norm, c / norm)


def _intersect_lines(
    line1: tuple[float, float, float],
    line2: tuple[float, float, float],
) -> tuple[float, float]:
    """Intersect two lines ``a·x + b·y + c = 0``.  Returns ``(x, y)``."""
    a1, b1, c1 = line1
    a2, b2, c2 = line2
    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-9:
        raise VariantSelectorError("Lines are parallel; cannot intersect.")
    x = (b1 * c2 - b2 * c1) / det
    y = (a2 * c1 - a1 * c2) / det
    return (x, y)


def _detect_wall_edge_pixels(
    mask: Image.Image,
    *,
    wall_side: str,
) -> dict[str, list[tuple[float, float]]]:
    """Scan alpha *mask* and return pixel lists for four wall edges.

    Returns ``{"face": [...], "top": [...], "bottom": [...], "outer": [...]}``.
    Each list contains ``(x, y)`` tuples suitable for :func:`_fit_line`.
    """
    bbox = mask.getbbox()
    if bbox is None:
        raise VariantSelectorError("Wall source mask has no opaque pixels.")
    bx0, by0, bx1, by1 = bbox
    bw = bx1 - bx0
    bh = by1 - by0
    pixels = mask.load()

    # Vertical range for face/outer edge sampling (middle 60 %)
    y_margin = int(bh * 0.20)
    y_lo = by0 + y_margin
    y_hi = by1 - y_margin

    # Column range for top/bottom edge sampling.
    # The top edge can start from the face column (the taper diverges outward).
    # The bottom edge must skip ~25 % near the face to avoid the wall-base
    # taper where face meets bottom edge.
    if wall_side == "left":
        top_col_lo = bx0
        top_col_hi = bx0 + int(bw * 0.55)
        bot_col_lo = bx0 + int(bw * 0.25)
        bot_col_hi = bx0 + int(bw * 0.65)
    else:
        top_col_lo = bx1 - int(bw * 0.55)
        top_col_hi = bx1
        bot_col_lo = bx1 - int(bw * 0.65)
        bot_col_hi = bx1 - int(bw * 0.25)

    face_pixels: list[tuple[float, float]] = []
    outer_pixels: list[tuple[float, float]] = []
    for y in range(y_lo, y_hi + 1):
        xs = [x for x in range(bx0, bx1) if pixels[x, y] >= 128]
        if not xs:
            continue
        if wall_side == "left":
            face_pixels.append((float(min(xs)), float(y)))
            outer_pixels.append((float(max(xs)), float(y)))
        else:
            face_pixels.append((float(max(xs)), float(y)))
            outer_pixels.append((float(min(xs)), float(y)))

    top_pixels: list[tuple[float, float]] = []
    for x in range(top_col_lo, top_col_hi + 1):
        ys_opaque = [y for y in range(by0, by1) if pixels[x, y] >= 128]
        if ys_opaque:
            top_pixels.append((float(x), float(min(ys_opaque))))

    bottom_pixels: list[tuple[float, float]] = []
    for x in range(bot_col_lo, bot_col_hi + 1):
        ys_opaque = [y for y in range(by0, by1) if pixels[x, y] >= 128]
        if ys_opaque:
            bottom_pixels.append((float(x), float(max(ys_opaque))))

    for name, pts in [("face", face_pixels), ("top", top_pixels),
                      ("bottom", bottom_pixels), ("outer", outer_pixels)]:
        if len(pts) < 2:
            raise VariantSelectorError(
                f"Not enough pixels to fit wall {name} edge (got {len(pts)})."
            )

    return {"face": face_pixels, "top": top_pixels,
            "bottom": bottom_pixels, "outer": outer_pixels}


def _detect_wall_corners(
    image: Image.Image,
    *,
    wall_side: str,
) -> list[tuple[float, float]]:
    """Detect four wall-body corners by fitting edge lines and intersecting.

    Returns corners in the same winding order as the canonical body polygon
    (counter-clockwise: bottom-left, top-left, top-right, bottom-right).

    For a **left** wall the face is on the left, so the order is
    ``[face_bottom, face_top, outer_top, outer_bottom]``.

    For a **right** wall the face is on the right, so the order is
    ``[outer_bottom, outer_top, face_top, face_bottom]``.
    """
    mask = alpha_mask(image)
    edge_px = _detect_wall_edge_pixels(mask, wall_side=wall_side)

    face_line = _fit_line(edge_px["face"])
    top_line = _fit_line(edge_px["top"])
    bottom_line = _fit_line(edge_px["bottom"])
    outer_line = _fit_line(edge_px["outer"])

    face_top = _intersect_lines(face_line, top_line)
    face_bottom = _intersect_lines(face_line, bottom_line)
    outer_top = _intersect_lines(outer_line, top_line)
    outer_bottom = _intersect_lines(outer_line, bottom_line)

    if wall_side == "left":
        return [face_bottom, face_top, outer_top, outer_bottom]
    # right wall: face is on the right side of the canvas
    return [outer_bottom, outer_top, face_top, face_bottom]


def _solve_linear_system(
    matrix: list[list[float]],
    vector: list[float],
) -> list[float]:
    """Solve an N×N linear system via Gaussian elimination with partial pivoting."""
    size = len(matrix)
    rows = [row[:] + [v] for row, v in zip(matrix, vector)]
    for col in range(size):
        pivot_row = max(range(col, size), key=lambda r: abs(rows[r][col]))
        if abs(rows[pivot_row][col]) < 1e-12:
            raise VariantSelectorError("Singular matrix in linear system solve.")
        if pivot_row != col:
            rows[col], rows[pivot_row] = rows[pivot_row], rows[col]
        pivot_val = rows[col][col]
        rows[col] = [v / pivot_val for v in rows[col]]
        for r in range(size):
            if r == col:
                continue
            factor = rows[r][col]
            if abs(factor) < 1e-15:
                continue
            rows[r] = [cur - factor * piv for cur, piv in zip(rows[r], rows[col])]
    return [rows[i][size] for i in range(size)]


def _solve_affine_coefficients(
    src_points: list[tuple[float, float]],
    dst_points: list[tuple[float, float]],
) -> list[float]:
    """Solve 2D affine transform coefficients."""
    if len(src_points) != 3 or len(dst_points) != 3:
        raise VariantSelectorError("Affine solve requires exactly 3 point pairs.")
    matrix: list[list[float]] = []
    rhs: list[float] = []
    for (sx, sy), (dx, dy) in zip(src_points, dst_points):
        matrix.append([sx, sy, 1.0, 0.0, 0.0, 0.0])
        rhs.append(dx)
        matrix.append([0.0, 0.0, 0.0, sx, sy, 1.0])
        rhs.append(dy)
    return _solve_linear_system(matrix, rhs)


def _apply_affine_point(coeffs: list[float], point: tuple[float, float]) -> tuple[float, float]:
    if len(coeffs) != 6:
        raise VariantSelectorError("Affine coefficients must have length 6.")
    a, b, c, d, e, f = coeffs
    x, y = point
    return (a * x + b * y + c, d * x + e * y + f)


def _solve_perspective_coefficients(
    src_points: list[tuple[float, float]],
    dst_points: list[tuple[float, float]],
) -> list[float]:
    """Solve 8 perspective-transform coefficients (PIL convention).

    PIL maps each **destination** pixel ``(X, Y)`` to a **source** pixel::

        x = (a·X + b·Y + c) / (g·X + h·Y + 1)
        y = (d·X + e·Y + f) / (g·X + h·Y + 1)

    Given four ``(dst → src)`` point pairs, returns ``[a, b, c, d, e, f, g, h]``.
    """
    if len(src_points) != 4 or len(dst_points) != 4:
        raise VariantSelectorError("Perspective solve requires exactly 4 point pairs.")

    # Build the 8×8 system   A · [a,b,c,d,e,f,g,h]^T = rhs
    mat: list[list[float]] = []
    rhs: list[float] = []
    for (dx, dy), (sx, sy) in zip(dst_points, src_points):
        mat.append([dx, dy, 1.0, 0.0, 0.0, 0.0, -dx * sx, -dy * sx])
        rhs.append(sx)
        mat.append([0.0, 0.0, 0.0, dx, dy, 1.0, -dx * sy, -dy * sy])
        rhs.append(sy)

    return _solve_linear_system(mat, rhs)


def _perspective_warp(
    image: Image.Image,
    *,
    source_corners: list[tuple[float, float]],
    target_corners: list[tuple[float, float]],
    output_size: tuple[int, int],
) -> Image.Image:
    """Perspective-warp *image* so that *source_corners* land on *target_corners*.

    Pads the source image so that off-canvas source coordinates are safe.
    """
    # Pad source so line-extension corners outside the image are handled.
    pad = 128
    padded = Image.new("RGBA", (image.width + 2 * pad, image.height + 2 * pad), (0, 0, 0, 0))
    padded.alpha_composite(_premultiply_rgba(image), (pad, pad))
    padded_src = [(x + pad, y + pad) for x, y in source_corners]

    coeffs = _solve_perspective_coefficients(padded_src, target_corners)
    result = padded.transform(output_size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    return _unpremultiply_rgba(result)


def _canonical_wall_body(canonical_target: dict[str, Any]) -> list[tuple[float, float]]:
    """Extract the 4-point body polygon from *canonical_target*.

    Falls back to reading the canonical tile spec if ``body`` is not inlined.
    """
    tile_key = canonical_target.get("tile_key", "")
    spec = canonical_tile_spec()
    tile = spec.get("tiles", {}).get(tile_key)
    if isinstance(tile, dict):
        body = tile.get("body")
        if isinstance(body, list) and len(body) == 4:
            return [(float(p[0]), float(p[1])) for p in body]
    # Fallback: derive from target_polygon (first 4 unique points)
    polygon = canonical_target.get("target_polygon", [])
    if len(polygon) >= 4:
        return [(float(p[0]), float(p[1])) for p in polygon[:4]]
    raise VariantSelectorError(f"Cannot extract 4-point body for {tile_key}.")



def _wall_source_backbone_points(mask: Image.Image, *, wall_side: str) -> list[tuple[float, float]]:
    bbox = mask.getbbox()
    if bbox is None:
        raise VariantSelectorError("Wall source image has no opaque pixels.")
    top_y = bbox[1]
    bottom_y = bbox[3] - 1

    apex_span = row_span(mask, top_y)
    if apex_span is None:
        raise VariantSelectorError("Wall source top row did not contain opaque pixels for backbone extraction.")
    apex = ((apex_span[0] + apex_span[1]) / 2.0, float(top_y))

    search_limit = min(bottom_y, top_y + max(12, int(round(mask.height * 0.18))))
    face_top: tuple[float, float] | None = None
    for y in range(top_y, search_limit + 1):
        span = row_span(mask, y)
        if span is None:
            continue
        if (span[1] - span[0]) >= 2:
            face_top = (float(span[0] if wall_side == "left" else span[1]), float(y))
            break
    if face_top is None:
        face_top = (float(apex_span[0] if wall_side == "left" else apex_span[1]), float(top_y))

    bottom_span = row_span(mask, bottom_y)
    if bottom_span is None:
        raise VariantSelectorError("Wall source bottom row did not contain opaque pixels for backbone extraction.")
    face_bottom = (
        float(bottom_span[0] if wall_side == "left" else bottom_span[1]),
        float(bottom_y),
    )
    return [face_bottom, face_top, apex]



def _derive_wall_source_polygon(
    image: Image.Image,
    *,
    canonical_target: dict[str, Any],
    wall_side: str,
) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    mask = alpha_mask(image)
    bbox = mask.getbbox()
    if bbox is None:
        raise VariantSelectorError("Wall source image has no opaque pixels.")

    target_polygon = [tuple(float(value) for value in point) for point in canonical_target["target_polygon"]]
    target_backbone = [target_polygon[0], target_polygon[1], target_polygon[2]]

    top_y = bbox[1]
    bottom_y = bbox[3] - 1
    apex_span = _row_span_or_error(mask, top_y, label="top row span")
    bottom_span = _row_span_or_error(mask, bottom_y, label="bottom row span")

    target_face_top_ratio_den = target_polygon[0][1] - target_polygon[2][1]
    if abs(target_face_top_ratio_den) < 1e-6:
        raise VariantSelectorError("Canonical wall backbone is degenerate.")
    target_face_top_ratio = (target_polygon[1][1] - target_polygon[2][1]) / target_face_top_ratio_den
    desired_face_top_y = int(round(top_y + (bottom_y - top_y) * target_face_top_ratio))
    desired_face_top_y = min(max(desired_face_top_y, top_y), bottom_y)

    face_top_y = desired_face_top_y
    face_top_span = row_span(mask, face_top_y)
    if face_top_span is None or (face_top_span[1] - face_top_span[0]) < 2:
        max_radius = max(8, int(round(mask.height * 0.05)))
        face_top_span = None
        for radius in range(1, max_radius + 1):
            for probe_y in (desired_face_top_y - radius, desired_face_top_y + radius):
                if probe_y < top_y or probe_y > bottom_y:
                    continue
                span = row_span(mask, probe_y)
                if span is None or (span[1] - span[0]) < 2:
                    continue
                face_top_y = probe_y
                face_top_span = span
                break
            if face_top_span is not None:
                break
    if face_top_span is None:
        raise VariantSelectorError("Could not find a stable wall shoulder row for 6-point mapping.")

    apex = ((apex_span[0] + apex_span[1]) / 2.0, float(top_y))
    face_bottom = (float(bottom_span[0] if wall_side == "left" else bottom_span[1]), float(bottom_y))
    face_top = (float(face_top_span[0] if wall_side == "left" else face_top_span[1]), float(face_top_y))
    top_outer = (float(face_top_span[1] if wall_side == "left" else face_top_span[0]), float(face_top_y))
    bottom_outer = (float(bottom_span[1] if wall_side == "left" else bottom_span[0]), float(bottom_y))

    source_backbone = [face_bottom, face_top, apex]
    target_to_source = _solve_affine_coefficients(target_backbone, source_backbone)
    source_polygon = [
        face_bottom,
        face_top,
        apex,
        top_outer,
        bottom_outer,
        _apply_affine_point(target_to_source, target_polygon[5]),
    ]
    return source_polygon, target_polygon



def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    count = len(polygon)
    for index in range(count):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % count]
        if (y1 > y) == (y2 > y):
            continue
        x_hit = (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1
        if x < x_hit:
            inside = not inside
    return inside



def _mean_value_coordinates(
    point: tuple[float, float],
    polygon: list[tuple[float, float]],
) -> list[float]:
    eps = 1e-6
    px, py = point
    count = len(polygon)
    if count < 3:
        raise VariantSelectorError("Mean value coordinates require a polygon with at least 3 points.")

    vectors: list[tuple[float, float]] = []
    distances: list[float] = []
    for index, (vx, vy) in enumerate(polygon):
        dx = vx - px
        dy = vy - py
        dist = math.hypot(dx, dy)
        if dist <= eps:
            weights = [0.0] * count
            weights[index] = 1.0
            return weights
        vectors.append((dx, dy))
        distances.append(dist)

    for index in range(count):
        next_index = (index + 1) % count
        x1, y1 = polygon[index]
        x2, y2 = polygon[next_index]
        edge_x = x2 - x1
        edge_y = y2 - y1
        rel_x = px - x1
        rel_y = py - y1
        cross = edge_x * rel_y - edge_y * rel_x
        if abs(cross) > 1e-5:
            continue
        dot = rel_x * (px - x2) + rel_y * (py - y2)
        if dot > eps:
            continue
        edge_len = math.hypot(edge_x, edge_y)
        if edge_len <= eps:
            break
        t = ((px - x1) * edge_x + (py - y1) * edge_y) / (edge_len * edge_len)
        t = min(max(t, 0.0), 1.0)
        weights = [0.0] * count
        weights[index] = 1.0 - t
        weights[next_index] = t
        return weights

    angles: list[float] = []
    for index in range(count):
        vx1, vy1 = vectors[index]
        vx2, vy2 = vectors[(index + 1) % count]
        cross = vx1 * vy2 - vy1 * vx2
        dot = vx1 * vx2 + vy1 * vy2
        angles.append(math.atan2(cross, dot))

    weights = [0.0] * count
    total = 0.0
    for index in range(count):
        prev_angle = angles[(index - 1) % count]
        next_angle = angles[index]
        weight = (math.tan(prev_angle / 2.0) + math.tan(next_angle / 2.0)) / distances[index]
        weights[index] = weight
        total += weight
    if abs(total) <= eps:
        raise VariantSelectorError("Mean value coordinate weights became degenerate.")
    return [weight / total for weight in weights]



def _sample_premultiplied_rgba(image: Image.Image, x: float, y: float) -> tuple[int, int, int, int]:
    width, height = image.size
    if x < 0.0 or y < 0.0 or x > width - 1 or y > height - 1:
        return (0, 0, 0, 0)

    x0 = int(math.floor(x))
    y0 = int(math.floor(y))
    x1 = min(x0 + 1, width - 1)
    y1 = min(y0 + 1, height - 1)
    tx = x - x0
    ty = y - y0

    p00 = image.getpixel((x0, y0))
    p10 = image.getpixel((x1, y0))
    p01 = image.getpixel((x0, y1))
    p11 = image.getpixel((x1, y1))

    def blend(c00: int, c10: int, c01: int, c11: int) -> int:
        top = c00 * (1.0 - tx) + c10 * tx
        bottom = c01 * (1.0 - tx) + c11 * tx
        return int(round(top * (1.0 - ty) + bottom * ty))

    return tuple(blend(p00[index], p10[index], p01[index], p11[index]) for index in range(4))



def _warp_rgba_polygon(
    image: Image.Image,
    *,
    source_polygon: list[tuple[float, float]],
    target_polygon: list[tuple[float, float]],
    output_size: tuple[int, int],
) -> Image.Image:
    if len(source_polygon) != len(target_polygon):
        raise VariantSelectorError("Source/target wall polygons must have the same point count.")
    premultiplied = _premultiply_rgba(image)
    result = Image.new("RGBA", output_size, (0, 0, 0, 0))
    target_mask = _polygon_mask(output_size, [list(point) for point in target_polygon])
    mask_pixels = target_mask.load()

    xs = [point[0] for point in target_polygon]
    ys = [point[1] for point in target_polygon]
    x_min = max(0, int(math.floor(min(xs))))
    x_max = min(output_size[0] - 1, int(math.ceil(max(xs))))
    y_min = max(0, int(math.floor(min(ys))))
    y_max = min(output_size[1] - 1, int(math.ceil(max(ys))))

    for y in range(y_min, y_max + 1):
        for x in range(x_min, x_max + 1):
            if mask_pixels[x, y] < 128 and not _point_in_polygon((x + 0.5, y + 0.5), target_polygon):
                continue
            weights = _mean_value_coordinates((x + 0.5, y + 0.5), target_polygon)
            source_x = sum(weight * point[0] for weight, point in zip(weights, source_polygon))
            source_y = sum(weight * point[1] for weight, point in zip(weights, source_polygon))
            result.putpixel((x, y), _sample_premultiplied_rgba(premultiplied, source_x, source_y))
    return _unpremultiply_rgba(result)



def _render_wall_output(
    image: Image.Image,
    *,
    canonical_target: dict[str, Any],
) -> Image.Image:
    """Fit a wall image to canonical game-iso geometry via backbone-first 6-point warp."""
    canvas_width = int(canonical_target["canvas_width"])
    canvas_height = int(canonical_target["canvas_height"])
    wall_side = _wall_side_from_target(canonical_target)
    source_polygon, target_polygon = _derive_wall_source_polygon(
        image,
        canonical_target=canonical_target,
        wall_side=wall_side,
    )
    warped = _warp_rgba_polygon(
        image,
        source_polygon=source_polygon,
        target_polygon=target_polygon,
        output_size=(canvas_width, canvas_height),
    )
    warped = _apply_polygon_mask(warped, [list(p) for p in _canonical_wall_body(canonical_target)])
    placement = canonical_target.get("placement", {})
    if isinstance(placement, dict):
        warped = _apply_opaque_half_rule(warped, str(placement.get("opaque_half", "")).strip().lower())
    return warped


def render_final_output(
    image: Image.Image,
    *,
    reference_path: Path,
    canonical_target: dict[str, Any] | None = None,
    target_size: int | None = None,
) -> Image.Image:
    reference_image = Image.open(reference_path).convert("RGBA")
    if canonical_target is not None:
        if canonical_target.get("tile_key", "").startswith("wall_"):
            return _render_wall_output(image, canonical_target=canonical_target)
        target_bbox: EffectiveBBox = canonical_target["target_bbox"]
        canvas_width = int(canonical_target["canvas_width"])
        canvas_height = int(canonical_target["canvas_height"])
        target_left = target_bbox.left
        target_top = target_bbox.top
        target_right = target_bbox.right + 1
        target_bottom = target_bbox.bottom + 1
    else:
        ref_effective = effective_bbox(alpha_mask(reference_image))
        canvas_width = reference_image.width if target_size is None else target_size
        canvas_height = reference_image.height if target_size is None else target_size
        if target_size is None:
            target_left = ref_effective.left
            target_top = ref_effective.top
            target_right = ref_effective.right + 1
            target_bottom = ref_effective.bottom + 1
        else:
            target_left = int(round(ref_effective.left * target_size / reference_image.width))
            target_top = int(round(ref_effective.top * target_size / reference_image.height))
            target_right = int(round((ref_effective.right + 1) * target_size / reference_image.width))
            target_bottom = int(round((ref_effective.bottom + 1) * target_size / reference_image.height))
    target_width = max(1, target_right - target_left)
    target_height = max(1, target_bottom - target_top)

    source_effective = effective_bbox(alpha_mask(image))
    source_left = source_effective.left
    source_top = source_effective.top
    source_right_exclusive = source_effective.right + 1
    source_bottom_exclusive = source_effective.bottom + 1

    source_crop = image.crop((source_left, source_top, source_right_exclusive, source_bottom_exclusive))
    scale = max(target_width / source_crop.width, target_height / source_crop.height)

    full_resized_width = max(1, int(round(image.width * scale)))
    full_resized_height = max(1, int(round(image.height * scale)))
    resized_full = image.resize((full_resized_width, full_resized_height), Image.NEAREST)

    scaled_left = int(round(source_left * scale))
    scaled_top = int(round(source_top * scale))
    paste_x = target_left - scaled_left
    paste_y = target_top - scaled_top

    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    canvas.alpha_composite(resized_full, (paste_x, paste_y))
    canvas = _align_canvas_bbox(canvas, target_left=target_left, target_top=target_top)
    if canonical_target is not None:
        canvas = _apply_polygon_mask(canvas, canonical_target["target_polygon"])
        placement = canonical_target.get("placement", {})
        if isinstance(placement, dict):
            canvas = _apply_opaque_half_rule(canvas, str(placement.get("opaque_half", "")).strip().lower())

    if _needs_left_edge_nudge(canvas):
        nudged = _shift_canvas(canvas, dy=-1)
        if not _needs_left_edge_nudge(nudged):
            canvas = nudged

    return canvas


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


def exterior_background_residue_check(candidate_path: Path, *, active_key_color: str, fail_rules: dict[str, float | int]) -> dict[str, Any]:
    image = Image.open(candidate_path).convert("RGBA")
    key_color = parse_hex_color(active_key_color)
    similarity_fail = float(fail_rules["top_boundary_key_similarity_fail"])
    pixel_ratio_fail = float(fail_rules["top_boundary_key_pixel_ratio_fail"])
    pixel_count_fail = int(fail_rules["top_boundary_key_pixel_count_fail"])
    run_fail = int(fail_rules["top_boundary_key_run_fail"])
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    alpha = rgba.getchannel("A")
    alpha_pixels = alpha.load()
    exterior_mask = Image.new("L", rgba.size, 0)
    exterior_pixels = exterior_mask.load()
    queue: deque[tuple[int, int]] = deque()

    def enqueue_if_exterior(x: int, y: int) -> None:
        if x < 0 or x >= width or y < 0 or y >= height:
            return
        if exterior_pixels[x, y] != 0:
            return
        if alpha_pixels[x, y] >= 32:
            return
        exterior_pixels[x, y] = 255
        queue.append((x, y))

    for corner_x, corner_y in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        enqueue_if_exterior(corner_x, corner_y)

    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            enqueue_if_exterior(x + dx, y + dy)

    boundary_samples: dict[tuple[int, int], dict[str, Any]] = {}
    corner_touch_samples: list[dict[str, Any]] = []
    strongest_samples: list[dict[str, Any]] = []
    for y in range(height):
        for x in range(width):
            if exterior_pixels[x, y] < 128:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = x + dx
                ny = y + dy
                if nx < 0 or nx >= width or ny < 0 or ny >= height:
                    continue
                if alpha_pixels[nx, ny] < 32:
                    continue
                r, g, b, _a = pixels[nx, ny]
                similarity = color_key_similarity((r, g, b), key_color)
                sample = {"x": nx, "y": ny, "rgb": [r, g, b], "similarity": similarity}
                boundary_samples[(nx, ny)] = sample

    corner_window = max(1, min(width, height) // 16)
    for x in range(width):
        for y in range(height):
            if alpha_pixels[x, y] < 32:
                continue
            in_corner_window = (
                (x < corner_window and y < corner_window)
                or (x >= width - corner_window and y < corner_window)
                or (x < corner_window and y >= height - corner_window)
                or (x >= width - corner_window and y >= height - corner_window)
            )
            if not in_corner_window:
                continue
            r, g, b, _a = pixels[x, y]
            similarity = color_key_similarity((r, g, b), key_color)
            sample = {"x": x, "y": y, "rgb": [r, g, b], "similarity": similarity}
            boundary_samples[(x, y)] = sample
            corner_touch_samples.append(sample)

    scanned_pixels = len(boundary_samples)
    contaminated_positions = {
        position: sample for position, sample in boundary_samples.items()
        if float(sample["similarity"]) >= similarity_fail
    }
    contaminated_pixels = len(contaminated_positions)
    if contaminated_positions:
        strongest_samples = sorted(contaminated_positions.values(), key=lambda item: item["similarity"], reverse=True)

    max_contiguous_run = 0
    visited: set[tuple[int, int]] = set()
    for position in contaminated_positions:
        if position in visited:
            continue
        component_size = 0
        component_queue: deque[tuple[int, int]] = deque([position])
        visited.add(position)
        while component_queue:
            px, py = component_queue.popleft()
            component_size += 1
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (px + dx, py + dy)
                if neighbor in contaminated_positions and neighbor not in visited:
                    visited.add(neighbor)
                    component_queue.append(neighbor)
        max_contiguous_run = max(max_contiguous_run, component_size)

    contamination_ratio = contaminated_pixels / scanned_pixels if scanned_pixels else 0.0
    fail = (
        contaminated_pixels >= pixel_count_fail
        or contamination_ratio >= pixel_ratio_fail
        or max_contiguous_run >= run_fail
    )
    return {
        "active_key_color": active_key_color,
        "scanned_pixels": scanned_pixels,
        "contaminated_pixels": contaminated_pixels,
        "contamination_ratio": contamination_ratio,
        "max_contiguous_run": max_contiguous_run,
        "similarity_threshold": similarity_fail,
        "fail": fail,
        "mode": "four_corner_exterior_fill",
        "corner_window": corner_window,
        "corner_touch_sample_count": len(corner_touch_samples),
        "exterior_background_pixels": int(exterior_mask.histogram()[255]) if len(exterior_mask.histogram()) > 255 else 0,
        "strongest_samples": strongest_samples[:12],
    }


def score_candidate(
    candidate_path: Path,
    reference_path: Path,
    reference_mask_normalized: Image.Image,
    reference_anchors: dict[str, tuple[int, int] | None],
    output_dir: Path,
    canonical_target: dict[str, Any] | None = None,
) -> dict[str, Any]:
    image = Image.open(candidate_path).convert("RGBA")
    candidate_alpha_mask = alpha_mask(image)
    candidate_rgba_normalized = render_final_output(image, reference_path=reference_path, canonical_target=canonical_target)
    scoring_mask_source = candidate_alpha_mask
    if canonical_target is not None and str(canonical_target.get("tile_key", "")).startswith("wall_"):
        scoring_mask_source = ImageChops.multiply(
            alpha_mask(candidate_rgba_normalized),
            _polygon_mask(candidate_rgba_normalized.size, [list(point) for point in _canonical_wall_body(canonical_target)]),
        )
    candidate_mask_normalized, bbox = normalize_mask(scoring_mask_source)
    candidate_anchors = mask_anchors(candidate_mask_normalized)
    candidate_iou = iou(reference_mask_normalized, candidate_mask_normalized)
    candidate_anchor_error = anchor_error(candidate_anchors, reference_anchors)
    candidate_raw_area = mask_area(candidate_alpha_mask)
    source_bbox = effective_bbox(candidate_alpha_mask)
    source_nontransparent_canvas = (
        source_bbox.left == 0
        and source_bbox.top == 0
        and source_bbox.right == image.width - 1
        and source_bbox.bottom == image.height - 1
    )
    score = (candidate_iou * 1000.0) - (candidate_anchor_error * 4.0)
    overlay_path = output_dir / f"{candidate_path.stem}.overlay.png"
    normalized_path = output_dir / f"{candidate_path.stem}.normalized.png"
    final_path = output_dir / f"{candidate_path.stem}.final.png"
    overlay_preview(reference_mask_normalized, candidate_mask_normalized, overlay_path)
    candidate_mask_normalized.save(normalized_path)
    candidate_rgba_normalized.save(final_path)
    return {
        "path": str(candidate_path),
        "normalized_path": str(normalized_path),
        "final_path": str(final_path),
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
        "raw_mask_area": candidate_raw_area,
        "score": score,
        "anchors": {key: list(value) if value is not None else None for key, value in candidate_anchors.items()},
        "source_effective_bbox": {
            "left": source_bbox.left,
            "top": source_bbox.top,
            "right": source_bbox.right,
            "bottom": source_bbox.bottom,
            "width": source_bbox.width,
            "height": source_bbox.height,
        },
        "source_nontransparent_canvas": source_nontransparent_canvas,
    }


def _candidate_cleanup_id(candidate_path: str, *, variant: str) -> str:
    raw_name = Path(candidate_path).stem.replace(f"generated_{variant}.", "")
    return _cleanup_artifact_token(raw_name)


def _export_selector_stage_artifacts(run_root: Path, *, variant: str, result: dict[str, Any]) -> None:
    step_6_dir = run_root / "step_6_mapping"
    step_7_dir = run_root / "step_7_selection"
    for directory in (step_6_dir, step_7_dir):
        directory.mkdir(parents=True, exist_ok=True)

    reference = result.get("reference", {}) if isinstance(result, dict) else {}
    reference_path_raw = reference.get("normalized_path") if isinstance(reference, dict) else None
    if reference_path_raw:
        _copy_artifact(Path(str(reference_path_raw)), step_7_dir / f"s7_reference_normalized.{variant}.png")

    chosen_candidate = result.get("chosen_candidate") if isinstance(result.get("chosen_candidate"), dict) else None
    verification = result.get("verification", {}) if isinstance(result.get("verification"), dict) else {}
    mapping_candidates: list[dict[str, Any]] = []
    verification_candidates: list[dict[str, Any]] = []

    for candidate in ([chosen_candidate] if chosen_candidate is not None else []):
        candidate_path = str(candidate.get("path", ""))
        cleanup_id = _candidate_cleanup_id(candidate_path, variant=variant)
        mapped_src = Path(str(candidate.get("final_path", ""))) if candidate.get("final_path") else None
        mapped_copy = _copy_artifact(mapped_src, step_6_dir / f"s6_mapped.{variant}.{cleanup_id}.png") if mapped_src else None
        normalized_src = Path(str(candidate.get("normalized_path", ""))) if candidate.get("normalized_path") else None
        normalized_copy = _copy_artifact(normalized_src, step_7_dir / f"s7_normalized.{variant}.{cleanup_id}.png") if normalized_src else None
        overlay_src = Path(str(candidate.get("overlay_path", ""))) if candidate.get("overlay_path") else None
        overlay_copy = _copy_artifact(overlay_src, step_7_dir / f"s7_overlay.{variant}.{cleanup_id}.png") if overlay_src else None

        final_stage = candidate.get("final_stage", {}) if isinstance(candidate.get("final_stage", {}), dict) else {}

        mapping_candidates.append(
            {
                "cleanup_id": cleanup_id,
                "source_input_path": candidate.get("path"),
                "mapped_output_path": mapped_copy or candidate.get("final_path"),
                "canvas_size": result.get("canonical_target", {}),
                "effective_bbox": candidate.get("effective_bbox"),
                "mapping_status": "ok" if mapped_copy or candidate.get("final_path") else "missing_mapped_output",
                "mapping_fail_reasons": final_stage.get("fail_reasons", []) if not final_stage.get("passed", False) else [],
                "mapping_diagnostics": {
                    "normalized_iou": candidate.get("normalized_iou"),
                    "anchor_error": candidate.get("anchor_error"),
                    "anchors": candidate.get("anchors"),
                },
            }
        )

        verification_candidates.append(
            {
            "cleanup_id": cleanup_id,
            "source_path": candidate.get("path"),
            "mapped_path": mapped_copy or candidate.get("final_path"),
            "overlay_path": overlay_copy or candidate.get("overlay_path"),
            "normalized_path": normalized_copy or candidate.get("normalized_path"),
            "mapping_score": candidate.get("score"),
            "final_stage": final_stage,
            "fail_reasons": candidate.get("fail_reasons", []),
            }
        )

    write_json(
        step_6_dir / f"s6_mapping.{variant}.json",
        {
            "variant": variant,
            "mapping_method": "single_chosen_cleanup_candidate",
            "chosen_candidate_id": result.get("chosen_candidate_id"),
            "candidates": mapping_candidates,
        },
    )
    update_step_status_summary(
        run_root,
        variant=variant,
        step_key="step_6_mapping",
        status="pass" if any(item["mapping_status"] == "ok" for item in mapping_candidates) else "fail",
        summary=f"{sum(1 for item in mapping_candidates if item['mapping_status'] == 'ok')}/{len(mapping_candidates)} mapped outputs written",
        primary_artifact=mapping_candidates[0]["mapped_output_path"] if mapping_candidates else None,
        details_path=str(step_6_dir / f"s6_mapping.{variant}.json"),
    )

    selected = result.get("selected") if isinstance(result.get("selected"), dict) else None
    selected_cleanup_id = _candidate_cleanup_id(str(selected.get("path", "")), variant=variant) if selected else None
    selected_output_path = None
    if result.get("selected_final_output"):
        selected_output_path = _copy_artifact(
            Path(str(result["selected_final_output"])),
            step_7_dir / f"s7_selected.{variant}.png",
        )

    write_json(
        step_7_dir / f"s7_selection.{variant}.json",
        {
            "variant": variant,
            "ok": bool(result.get("ok")),
            "verified_candidate_id": selected_cleanup_id,
            "selected_output_path": selected_output_path or result.get("selected_final_output"),
            "verification": verification,
            "candidates": verification_candidates,
        },
    )
    update_step_status_summary(
        run_root,
        variant=variant,
        step_key="step_7_selection",
        status="pass" if selected_output_path else "fail",
        summary="mapped candidate verified" if selected_output_path else "mapped candidate failed verification",
        primary_artifact=selected_output_path,
        details_path=str(step_7_dir / f"s7_selection.{variant}.json"),
    )
    if selected_output_path:
        _update_deliverable_manifest(
            run_root,
            selected_outputs={variant: selected_output_path},
            workflow_status="mapping_verified",
            selected_from_step="step_7_selection",
        )


def evaluate_final_fit(
    candidate: dict[str, Any],
    *,
    reference_effective_bbox: EffectiveBBox,
    reference_anchors: dict[str, tuple[int, int] | None],
    fail_rules: dict[str, float | int],
) -> tuple[list[str], dict[str, Any]]:
    fail_reasons: list[str] = []

    if candidate["normalized_iou"] < float(fail_rules["min_normalized_iou"]):
        fail_reasons.append("final_normalized_iou_too_low")
    if candidate["anchor_error"] > float(fail_rules["max_anchor_error"]):
        fail_reasons.append("final_anchor_error_too_high")

    bbox = candidate["effective_bbox"]
    width_ratio = bbox["width"] / reference_effective_bbox.width
    height_ratio = bbox["height"] / reference_effective_bbox.height
    if width_ratio < float(fail_rules["min_effective_scale_ratio"]):
        fail_reasons.append("final_effective_width_too_small")
    if height_ratio < float(fail_rules["min_effective_scale_ratio"]):
        fail_reasons.append("final_effective_height_too_small")

    anchors = candidate["anchors"]
    for anchor_name in ("left_shoulder", "right_shoulder", "left_mid", "right_mid", "bottom_tip"):
        if anchors.get(anchor_name) is None:
            fail_reasons.append(f"final_missing_{anchor_name}")

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

    if left_shoulder is not None and ref_left_shoulder is not None and left_shoulder[0] - ref_left_shoulder[0] > int(fail_rules["max_shoulder_inset"]):
        fail_reasons.append("final_left_shoulder_inset_too_large")
    if right_shoulder is not None and ref_right_shoulder is not None and ref_right_shoulder[0] - right_shoulder[0] > int(fail_rules["max_shoulder_inset"]):
        fail_reasons.append("final_right_shoulder_inset_too_large")
    if left_mid is not None and ref_left_mid is not None and left_mid[0] - ref_left_mid[0] > int(fail_rules["max_mid_inset"]):
        fail_reasons.append("final_left_mid_inset_too_large")
    if right_mid is not None and ref_right_mid is not None and ref_right_mid[0] - right_mid[0] > int(fail_rules["max_mid_inset"]):
        fail_reasons.append("final_right_mid_inset_too_large")
    if bottom_tip is not None and ref_bottom_tip is not None and abs(bottom_tip[1] - ref_bottom_tip[1]) > int(fail_rules["max_bottom_tip_drift"]):
        fail_reasons.append("final_bottom_tip_drift_too_large")
    return fail_reasons, {
        "passed": len(fail_reasons) == 0,
        "fail_reasons": fail_reasons,
        "normalized_iou": candidate["normalized_iou"],
        "anchor_error": candidate["anchor_error"],
        "effective_bbox": candidate["effective_bbox"],
        "anchors": candidate["anchors"],
    }

def select_variant_pool(run_root: Path, *, variant: str = "full") -> dict[str, Any]:
    request = load_json(run_root / "request" / "request.json")
    variant_profiles = request.get("variant_profiles", {})
    variant_profile = variant_profiles.get(variant, {}) if isinstance(variant_profiles, dict) else {}
    selector_profile = ""
    if isinstance(variant_profiles, dict):
        selector_profile = str(variant_profiles.get(variant, {}).get("selector_profile", "")).strip().lower()
    fail_rules_key = selector_profile or variant
    if fail_rules_key not in FAIL_RULES_BY_VARIANT:
        raise VariantSelectorError(f"Unsupported variant '{variant}'.")
    fail_rules = FAIL_RULES_BY_VARIANT[fail_rules_key]
    validation_path = run_root / "validation" / "validation.json"
    validation_payload = load_json(validation_path) if validation_path.exists() else {}
    preprocessing_payload = validation_payload.get("preprocessing", {}).get(variant, {})
    preprocessing_gate = validation_payload.get(variant, {}).get("preprocessing_gate", {})
    active_key_color = str(preprocessing_payload.get("active_key_color", request.get("background", {}).get("prompt_color", "#FF00FF")))
    reference_path = Path(request["references"][variant])
    canonical_target = canonical_target_for_variant(
        variant=variant,
        selector_profile=selector_profile,
        variant_profile=variant_profile if isinstance(variant_profile, dict) else {},
    )
    reference_image = Image.open(reference_path).convert("RGBA")
    if canonical_target is not None and str(canonical_target.get("tile_key", "")).startswith("wall_"):
        reference_scoring_mask = _polygon_mask(
            (int(canonical_target["canvas_width"]), int(canonical_target["canvas_height"])),
            [list(point) for point in _canonical_wall_body(canonical_target)],
        )
    else:
        reference_scoring_mask = alpha_mask(reference_image)
    reference_mask_normalized, reference_bbox = normalize_mask(reference_scoring_mask)
    reference_anchors = mask_anchors(reference_mask_normalized)

    chosen_candidate_raw = preprocessing_gate.get("chosen_candidate", {}) if isinstance(preprocessing_gate, dict) else {}
    chosen_candidate_path_raw = chosen_candidate_raw.get("path") if isinstance(chosen_candidate_raw, dict) else None
    if not chosen_candidate_path_raw:
        raise VariantSelectorError(f"No chosen cleanup candidate found for variant '{variant}'.")
    chosen_candidate_path = Path(str(chosen_candidate_path_raw))
    if not chosen_candidate_path.exists():
        raise VariantSelectorError(f"Chosen cleanup candidate is missing: {chosen_candidate_path}")

    output_dir = run_root / "selection" / variant
    output_dir.mkdir(parents=True, exist_ok=True)
    reference_mask_normalized.save(output_dir / "reference.normalized.png")

    chosen_candidate = score_candidate(
        chosen_candidate_path,
        reference_path,
        reference_mask_normalized,
        reference_anchors,
        output_dir,
        canonical_target=canonical_target,
    )
    final_fail_reasons, final_stage = evaluate_final_fit(
        chosen_candidate,
        reference_effective_bbox=reference_bbox,
        reference_anchors=reference_anchors,
        fail_rules=fail_rules,
    )
    chosen_candidate["final_stage"] = final_stage
    chosen_candidate["fail_reasons"] = list(final_fail_reasons)
    chosen_candidate["passed"] = len(final_fail_reasons) == 0

    result = {
        "ok": bool(chosen_candidate["passed"]),
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
        "canonical_target": {
            "tile_key": canonical_target.get("tile_key"),
            "canvas_width": canonical_target.get("canvas_width"),
            "canvas_height": canonical_target.get("canvas_height"),
            "target_bbox": {
                "left": canonical_target["target_bbox"].left,
                "top": canonical_target["target_bbox"].top,
                "right": canonical_target["target_bbox"].right,
                "bottom": canonical_target["target_bbox"].bottom,
                "width": canonical_target["target_bbox"].width,
                "height": canonical_target["target_bbox"].height,
            } if canonical_target is not None else None,
            "target_polygon": canonical_target.get("target_polygon") if canonical_target is not None else None,
            "contact_edge": canonical_target.get("contact_edge") if canonical_target is not None else None,
        } if canonical_target is not None else None,
        "active_key_color": active_key_color,
        "verification_workflow": {
            "stages": [
                "chosen_cleanup_candidate",
                "map_to_canonical_game_iso",
                "mapping_verification",
            ]
        },
        "fail_rule_thresholds": {
            "min_normalized_iou": float(fail_rules["min_normalized_iou"]),
            "max_anchor_error": float(fail_rules["max_anchor_error"]),
            "max_shoulder_inset": int(fail_rules["max_shoulder_inset"]),
            "max_mid_inset": int(fail_rules["max_mid_inset"]),
            "max_bottom_tip_drift": int(fail_rules["max_bottom_tip_drift"]),
            "min_effective_scale_ratio": float(fail_rules["min_effective_scale_ratio"]),
            "top_boundary_scan_ratio": float(fail_rules["top_boundary_scan_ratio"]),
            "top_boundary_key_similarity_fail": float(fail_rules["top_boundary_key_similarity_fail"]),
            "top_boundary_key_pixel_ratio_fail": float(fail_rules["top_boundary_key_pixel_ratio_fail"]),
            "top_boundary_key_pixel_count_fail": int(fail_rules["top_boundary_key_pixel_count_fail"]),
            "top_boundary_key_run_fail": int(fail_rules["top_boundary_key_run_fail"]),
        },
        "chosen_candidate_id": _candidate_cleanup_id(str(chosen_candidate["path"]), variant=variant),
        "chosen_candidate": chosen_candidate,
        "verification": final_stage,
        "selected": chosen_candidate if chosen_candidate["passed"] else None,
    }
    if result["selected"] is not None:
        selected_path = Path(str(result["selected"]["final_path"]))
        final_dir = run_root / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        final_output_path = final_dir / f"selected_{variant}.png"
        Image.open(selected_path).save(final_output_path)
        result["selected_final_output"] = str(final_output_path)
        result["selected_candidate_id"] = _candidate_cleanup_id(str(result["selected"]["path"]), variant=variant)
    else:
        result["selected_final_output"] = None
        result["selected_candidate_id"] = None
    write_json(run_root / "selection" / f"{variant}.selection.json", result)
    _export_selector_stage_artifacts(run_root, variant=variant, result=result)
    return result
