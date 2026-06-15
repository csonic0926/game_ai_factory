from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any, Iterable

from PIL import Image


def _parse_hex_color(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError(f"Invalid RGB hex color: {value}")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def _rgb_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def _is_near_any_key(rgb: tuple[int, int, int], key_colors: list[tuple[int, int, int]], tolerance: int) -> bool:
    return any(_rgb_distance(rgb, key) <= tolerance for key in key_colors)


def _connected_background_mask(raw: Image.Image, *, key_colors: list[tuple[int, int, int]], tolerance: int) -> bytearray:
    image = raw.convert("RGBA")
    width, height = image.size
    pixels = image.load()
    mask = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def try_seed(x: int, y: int) -> None:
        idx = y * width + x
        if mask[idx]:
            return
        r, g, b, a = pixels[x, y]
        if a >= 16 and _is_near_any_key((r, g, b), key_colors, tolerance):
            mask[idx] = 1
            queue.append((x, y))

    for x in range(width):
        try_seed(x, 0)
        try_seed(x, height - 1)
    for y in range(height):
        try_seed(0, y)
        try_seed(width - 1, y)

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            idx = ny * width + nx
            if mask[idx]:
                continue
            r, g, b, a = pixels[nx, ny]
            if a >= 16 and _is_near_any_key((r, g, b), key_colors, tolerance):
                mask[idx] = 1
                queue.append((nx, ny))
    return mask




def _all_key_mask(raw: Image.Image, *, key_colors: list[tuple[int, int, int]], tolerance: int) -> bytearray:
    image = raw.convert("RGBA")
    width, height = image.size
    pixels = image.load()
    mask = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a >= 16 and _is_near_any_key((r, g, b), key_colors, tolerance):
                mask[y * width + x] = 1
    return mask

def _alpha_bbox(image: Image.Image, *, threshold: int = 32) -> tuple[int, int, int, int] | None:
    alpha = image.convert("RGBA").getchannel("A").point(lambda value: 255 if value >= threshold else 0, mode="L")
    return alpha.getbbox()


def _bbox_score(bbox: tuple[int, int, int, int] | None, size: tuple[int, int]) -> tuple[float, list[str]]:
    if bbox is None:
        return 0.0, ["missing_candidate_bbox"]
    width, height = size
    left, top, right, bottom = bbox
    bbox_w = right - left
    bbox_h = bottom - top
    issues: list[str] = []
    if left <= 0 or top <= 0 or right >= width or bottom >= height:
        issues.append("candidate_bbox_touches_canvas_edge")
    area_ratio = (bbox_w * bbox_h) / float(width * height)
    if area_ratio > 0.92:
        issues.append("candidate_bbox_nearly_full_canvas")
    if area_ratio < 0.002:
        issues.append("candidate_bbox_too_small")
    score = 1.0
    if issues:
        score -= 0.35 * len(issues)
    return max(0.0, min(1.0, score)), issues


def score_cleanup_candidates(
    *,
    raw_path: Path,
    candidates: Iterable[dict[str, Any]],
    key_colors: Iterable[str],
    tolerance: int,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Score prop cleanup candidates by comparing raw RGB pixels with candidate alpha/RGB.

    The scorer is deliberately not an art critic. It rewards candidates that remove
    reserved color-key background, including enclosed key-color holes, while preserving
    non-background raw pixels.
    """
    raw = Image.open(raw_path).convert("RGBA")
    width, height = raw.size
    parsed_key_colors = [_parse_hex_color(color) for color in key_colors]
    if not parsed_key_colors:
        parsed_key_colors = [(255, 0, 255)]
    connected_background_mask = _connected_background_mask(raw, key_colors=parsed_key_colors, tolerance=tolerance)
    all_key_mask = _all_key_mask(raw, key_colors=parsed_key_colors, tolerance=tolerance)
    raw_pixels = list(raw.getdata())
    # Prop color-key prompts reserve the key colors exclusively for background.
    # Score enclosed key-color holes as background too; otherwise a correctly
    # transparent brazier ring/opening is penalized as deleted object pixels.
    background_mask = bytearray(1 if connected_background_mask[index] or all_key_mask[index] else 0 for index in range(width * height))
    background_indices = [index for index, flag in enumerate(background_mask) if flag]
    object_indices = [index for index, flag in enumerate(background_mask) if not flag and raw_pixels[index][3] >= 16]
    bg_count = max(1, len(background_indices))
    obj_count = max(1, len(object_indices))

    scored: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_path_raw = candidate.get("path")
        if not candidate_path_raw:
            continue
        candidate_path = Path(str(candidate_path_raw))
        if not candidate_path.exists():
            scored.append({**candidate, "score": 0.0, "issues": ["missing_candidate_file"]})
            continue
        image = Image.open(candidate_path).convert("RGBA")
        if image.size != raw.size:
            image = image.resize(raw.size, Image.Resampling.NEAREST)
        pixels = list(image.getdata())
        bg_alpha_sum = sum(pixels[index][3] for index in background_indices)
        bg_removal_score = 1.0 - min(1.0, bg_alpha_sum / (255.0 * bg_count))
        object_opaque_count = sum(1 for index in object_indices if pixels[index][3] >= 64)
        object_preservation_score = object_opaque_count / float(obj_count)

        color_delta_sum = 0.0
        color_delta_count = 0
        fringe_count = 0
        retained_count = 0
        for index in object_indices:
            r, g, b, a = pixels[index]
            if a < 64:
                continue
            retained_count += 1
            raw_r, raw_g, raw_b, _ = raw_pixels[index]
            color_delta_sum += _rgb_distance((r, g, b), (raw_r, raw_g, raw_b)) / 441.67295593
            color_delta_count += 1
            if _is_near_any_key((r, g, b), parsed_key_colors, tolerance + 24):
                fringe_count += 1
        color_preservation_score = 1.0 - min(1.0, color_delta_sum / max(1, color_delta_count))
        fringe_ratio = fringe_count / float(max(1, retained_count))
        fringe_score = 1.0 - min(1.0, fringe_ratio * 8.0)
        hole_penalty = 1.0 - object_preservation_score
        bbox, bbox_issues = _alpha_bbox(image), []
        bbox_score, bbox_issues = _bbox_score(bbox, image.size)
        score = (
            0.35 * bg_removal_score
            + 0.35 * object_preservation_score
            + 0.14 * color_preservation_score
            + 0.08 * fringe_score
            + 0.08 * bbox_score
        )
        issues = list(bbox_issues)
        if bg_removal_score < 0.96:
            issues.append("background_residue")
        if object_preservation_score < 0.90:
            issues.append("object_pixels_removed")
        if fringe_score < 0.80:
            issues.append("key_color_fringe_retained")
        scored.append(
            {
                **candidate,
                "score": round(float(score), 6),
                "components": {
                    "background_removal_score": round(float(bg_removal_score), 6),
                    "object_preservation_score": round(float(object_preservation_score), 6),
                    "color_preservation_score": round(float(color_preservation_score), 6),
                    "fringe_score": round(float(fringe_score), 6),
                    "bbox_score": round(float(bbox_score), 6),
                    "hole_penalty": round(float(hole_penalty), 6),
                },
                "bbox": list(bbox) if bbox else None,
                "issues": issues,
            }
        )

    scored.sort(key=lambda item: (float(item.get("score", 0.0)), str(item.get("cleanup_id", ""))), reverse=True)
    selected = scored[0] if scored else None
    payload = {
        "schema_version": "prop_cleanup_score_v1",
        "raw_path": str(raw_path),
        "image_size": {"width": width, "height": height},
        "key_colors": ["#{:02X}{:02X}{:02X}".format(*color) for color in parsed_key_colors],
        "tolerance": tolerance,
        "raw_classification": {
            "background_like_pixels": len(background_indices),
            "connected_background_like_pixels": sum(1 for flag in connected_background_mask if flag),
            "internal_key_like_pixels": max(0, len(background_indices) - sum(1 for flag in connected_background_mask if flag)),
            "object_like_pixels": len(object_indices),
            "background_like_ratio": round(len(background_indices) / float(width * height), 6),
            "object_like_ratio": round(len(object_indices) / float(width * height), 6),
        },
        "selected_cleanup_id": selected.get("cleanup_id") if selected else None,
        "selected_path": selected.get("path") if selected else None,
        "candidates": scored,
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
