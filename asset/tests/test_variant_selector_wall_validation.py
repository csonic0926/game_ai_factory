from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from pipeline.variant_selector import (
    FAIL_RULES_BY_VARIANT,
    _validate_wall_edge_alignment,
    canonical_target_for_variant,
    render_final_output,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _wall_target(variant: str, *, height_units: int) -> dict:
    return canonical_target_for_variant(
        variant=variant,
        selector_profile="wall",
        variant_profile={"wall_profile": {"height_units": height_units}},
    )


def _polygon_image(points: list[tuple[int, int]], size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.polygon(points, fill=(180, 180, 180, 255))
    return image


class WallEdgeValidationTests(unittest.TestCase):
    def _validate(self, image: Image.Image, canonical_target: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "wall.png"
            image.save(path)
            return _validate_wall_edge_alignment(
                path,
                canonical_target=canonical_target,
                fail_rules=FAIL_RULES_BY_VARIANT["wall"],
            )

    def test_left_2u_accepts_thicker_wall_when_edge_angles_match(self) -> None:
        target = _wall_target("left", height_units=2)
        image = _polygon_image(
            [(0, 224), (0, 40), (56, 12), (104, 36), (104, 172)],
            (128, 256),
        )
        result = self._validate(image, target)
        self.assertTrue(result["passed"], result)

    def test_left_2u_rejects_mirrored_wall(self) -> None:
        target = _wall_target("left", height_units=2)
        image = _polygon_image(
            [(128, 224), (128, 40), (72, 12), (24, 36), (24, 226), (72, 198)],
            (128, 256),
        )
        result = self._validate(image, target)
        self.assertFalse(result["passed"], result)
        self.assertTrue(any("angle_mismatch" in reason for reason in result["fail_reasons"]), result)

    def test_left_2u_rejects_slumped_top_edge(self) -> None:
        target = _wall_target("left", height_units=2)
        image = _polygon_image(
            [(0, 224), (0, 60), (56, 55), (104, 60), (104, 226), (48, 198)],
            (128, 256),
        )
        result = self._validate(image, target)
        self.assertFalse(result["passed"], result)
        self.assertIn("wall_top_edge_angle_mismatch", result["fail_reasons"], result)

    def test_reference_wall_mapping_outputs_pass_edge_validation(self) -> None:
        cases = [
            ("left", 1, REPO_ROOT / "output" / "png" / "101_wall_straight_rot90.png"),
            ("right", 1, REPO_ROOT / "output" / "png" / "101_wall_straight_rot0.png"),
            ("left", 2, REPO_ROOT / "output" / "png" / "102_wall_straight_2u_rot90.png"),
            ("right", 2, REPO_ROOT / "output" / "png" / "102_wall_straight_2u_rot0.png"),
        ]
        for variant, height_units, reference_path in cases:
            with self.subTest(variant=variant, height_units=height_units):
                canonical_target = _wall_target(variant, height_units=height_units)
                mapped = render_final_output(
                    Image.open(reference_path).convert("RGBA"),
                    reference_path=reference_path,
                    canonical_target=canonical_target,
                )
                self.assertEqual(mapped.size, (canonical_target["canvas_width"], canonical_target["canvas_height"]))
                result = self._validate(mapped, canonical_target)
                self.assertTrue(result["passed"], result)


if __name__ == "__main__":
    unittest.main()
