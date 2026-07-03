from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image

from pipeline.variant_selector import (
    alpha_mask,
    canonical_target_for_variant,
    effective_bbox,
    render_final_output,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _floor_target(variant: str) -> dict:
    return canonical_target_for_variant(
        variant=variant,
        selector_profile="",
        variant_profile={},
    )


def _coverage(mask: Image.Image, point: tuple[int, int], radius: int = 1) -> float:
    pixels = mask.load()
    x0 = max(0, point[0] - radius)
    x1 = min(mask.width - 1, point[0] + radius)
    y0 = max(0, point[1] - radius)
    y1 = min(mask.height - 1, point[1] + radius)
    total = 0
    solid = 0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            total += 1
            if pixels[x, y] >= 128:
                solid += 1
    return solid / total if total else 0.0


class FloorPlaneDistortTests(unittest.TestCase):
    def test_reference_full_floor_maps_to_canonical_full_geometry(self) -> None:
        reference_path = REPO_ROOT / "output" / "png" / "001_floor_plain_rot0.png"
        canonical_target = _floor_target("full")
        mapped = render_final_output(
            Image.open(reference_path).convert("RGBA"),
            reference_path=reference_path,
            canonical_target=canonical_target,
        )
        self.assertEqual(mapped.size, (128, 128))
        mask = alpha_mask(mapped)
        bbox = effective_bbox(mask)
        self.assertLessEqual(abs(bbox.left - 0), 0)
        self.assertLessEqual(abs(bbox.top - 0), 1)
        self.assertLessEqual(abs(bbox.right - 127), 0)
        self.assertLessEqual(abs(bbox.bottom - 127), 1)
        for point in ((64, 16), (64, 64), (64, 96)):
            with self.subTest(point=point):
                self.assertGreaterEqual(_coverage(mask, point), 0.34)

    def test_reference_half_floor_maps_to_canonical_half_geometry(self) -> None:
        reference_path = REPO_ROOT / "output" / "png" / "002_floor_half_rot0.png"
        canonical_target = _floor_target("half")
        mapped = render_final_output(
            Image.open(reference_path).convert("RGBA"),
            reference_path=reference_path,
            canonical_target=canonical_target,
        )
        self.assertEqual(mapped.size, (128, 128))
        mask = alpha_mask(mapped)
        bbox = effective_bbox(mask)
        self.assertLessEqual(abs(bbox.left - 0), 0)
        self.assertLessEqual(abs(bbox.top - 32), 1)
        self.assertLessEqual(abs(bbox.right - 127), 0)
        self.assertLessEqual(abs(bbox.bottom - 127), 1)
        for point in ((16, 88), (64, 48), (112, 88), (64, 96)):
            with self.subTest(point=point):
                self.assertGreaterEqual(_coverage(mask, point), 0.34)


if __name__ == "__main__":
    unittest.main()
