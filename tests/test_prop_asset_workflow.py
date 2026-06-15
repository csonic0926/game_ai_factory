from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

from itf import command_generate_prop_assets
from pipeline.prop_asset_workflow import _build_prop_provider_adapter, _normalize_generation_canvas, generate_prop_assets
from pipeline.prop_cleanup_scorer import score_cleanup_candidates
from pipeline.reference_pair_workflow import apply_color_key_to_image
from pipeline.prop_validator import validate_prop_asset_set


def _base_spec(temp_path: Path) -> dict:
    return {
        "schema_version": "prop_asset_workflow_v1",
        "asset_family": "flame_relay_brazier",
        "run_id": "brazier_test",
        "output_root": str(temp_path / "runs"),
        "provider": {"name": "mock"},
        "model": {"name": "mock"},
        "background": {"mode": "color_key", "prompt_color": "#FF00FF", "fallback_colors": ["#00FF00"], "tolerance": 24},
        "canvas": {"width": 128, "height": 256},
        "projection_mode": "isometric",
        "anchor": {"type": "bottom_center", "x": 64, "y": 255},
        "footprint": {"tile_width": 1, "tile_height": 1},
        "states": [
            {"asset_id": "imt_flame_target_brazier_unlit", "role": "target_unlit", "generation": {"mode": "base"}},
            {
                "asset_id": "imt_flame_source_brazier_active",
                "role": "source_active",
                "generation": {
                    "mode": "edit_from",
                    "source_asset_id": "imt_flame_target_brazier_unlit",
                    "prompt_delta": "add compact active flame",
                },
            },
        ],
        "constraints": {
            "transparent_background": True,
            "no_text": True,
            "no_watermark": True,
            "no_floor_tile_baked_in": True,
            "no_large_cast_shadow": True,
        },
        "validation": {"profile": "prop_engineering_v1"},
        "atlas": {"enabled": True},
    }


def _transparent_spec(temp_path: Path) -> dict:
    spec = _base_spec(temp_path)
    spec["provider"] = {"name": "mock"}
    spec["model"] = {"name": "mock"}
    spec["background"] = {"mode": "transparent_native"}
    spec["validation"] = {**spec["validation"], "native_transparency_required": True}
    return spec


def _make_valid_brazier_image(
    *,
    active: bool,
    size: tuple[int, int] = (128, 256),
    background_rgba: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> Image.Image:
    image = Image.new("RGBA", (128, 256), background_rgba)
    draw = ImageDraw.Draw(image)
    draw.ellipse((34, 164, 94, 204), fill=(130, 80, 40, 255), outline=(60, 40, 25, 255), width=3)
    draw.rectangle((58, 202, 70, 239), fill=(60, 40, 25, 255))
    draw.polygon([(49, 239), (79, 239), (89, 255), (39, 255)], fill=(60, 40, 25, 255))
    draw.line((48, 205, 35, 252), fill=(60, 40, 25, 255), width=5)
    draw.line((80, 205, 93, 252), fill=(60, 40, 25, 255), width=5)
    if active:
        draw.polygon([(64, 128), (49, 166), (79, 166)], fill=(255, 118, 26, 255))
        draw.polygon([(64, 140), (54, 167), (73, 167)], fill=(255, 214, 72, 255))
    else:
        draw.ellipse((48, 157, 80, 179), fill=(45, 40, 36, 255))
    if size != image.size:
        image = image.resize(size, Image.Resampling.NEAREST)
    return image


def _draw_valid_brazier(path: Path, *, active: bool, size: tuple[int, int] = (128, 256), background_rgba: tuple[int, int, int, int] = (0, 0, 0, 0)) -> None:
    _make_valid_brazier_image(active=active, size=size, background_rgba=background_rgba).save(path)


def _make_brazier_source_canvas(
    *,
    active: bool,
    canvas_size: tuple[int, int],
    background_rgba: tuple[int, int, int, int],
) -> Image.Image:
    canvas = Image.new("RGBA", canvas_size, background_rgba)
    prop = _make_valid_brazier_image(active=active, size=(128, 256), background_rgba=(0, 0, 0, 0))
    paste_x = (canvas_size[0] - prop.width) // 2
    paste_y = canvas_size[1] - prop.height
    canvas.alpha_composite(prop, (paste_x, paste_y))
    return canvas


def _draw_brazier_with_floor(path: Path) -> None:
    image = Image.new("RGBA", (128, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.polygon([(64, 191), (127, 223), (64, 255), (0, 223)], fill=(90, 80, 70, 255))
    draw.ellipse((42, 156, 86, 196), fill=(130, 80, 40, 255))
    draw.rectangle((58, 194, 70, 248), fill=(60, 40, 25, 255))
    image.save(path)


def _draw_opaque_corner_background(path: Path) -> None:
    image = Image.new("RGBA", (128, 256), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.ellipse((44, 168, 84, 205), fill=(130, 80, 40, 255))
    draw.rectangle((58, 202, 70, 239), fill=(60, 40, 25, 255))
    draw.polygon([(49, 239), (79, 239), (89, 255), (39, 255)], fill=(60, 40, 25, 255))
    image.save(path)


def _draw_bottom_corner_prop(path: Path) -> None:
    image = Image.new("RGBA", (128, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 165, 124, 255), fill=(130, 80, 40, 255))
    image.save(path)


def _draw_touching_edge(path: Path) -> None:
    image = Image.new("RGBA", (128, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 150, 65, 255), fill=(130, 80, 40, 255))
    image.save(path)


def _draw_raw_color_key_fixture(path: Path, *, size: tuple[int, int] = (64, 64)) -> None:
    image = Image.new("RGBA", size, (255, 0, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((22, 18, 42, 50), fill=(120, 80, 40, 255))
    draw.ellipse((25, 10, 39, 24), fill=(255, 120, 20, 255))
    image.save(path)


def _draw_cleanup_candidate(path: Path, *, kind: str, size: tuple[int, int] = (64, 64)) -> None:
    if kind == "background_retained":
        image = Image.new("RGBA", size, (255, 0, 255, 255))
    else:
        image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if kind != "object_deleted":
        draw.rectangle((22, 18, 42, 50), fill=(120, 80, 40, 255))
        draw.ellipse((25, 10, 39, 24), fill=(255, 120, 20, 255))
    if kind == "fringe":
        draw.rectangle((19, 15, 45, 53), outline=(255, 0, 255, 255), width=3)
    image.save(path)


class PropAssetWorkflowTests(unittest.TestCase):
    def test_generation_canvas_derives_tall_source_from_final_canvas(self) -> None:
        generation_canvas = _normalize_generation_canvas({}, final_canvas={"width": 128, "height": 256})
        self.assertEqual(generation_canvas["derived_aspect_ratio"], "1:2")
        self.assertEqual(generation_canvas["derived_size"], {"width": 512, "height": 1024})

    def test_generation_canvas_derives_square_source_from_final_canvas(self) -> None:
        generation_canvas = _normalize_generation_canvas({}, final_canvas={"width": 128, "height": 128})
        self.assertEqual(generation_canvas["derived_aspect_ratio"], "1:1")
        self.assertEqual(generation_canvas["derived_size"], {"width": 1024, "height": 1024})

    def test_gpt_adapter_falls_back_to_supported_portrait_size(self) -> None:
        generation_canvas = _normalize_generation_canvas({}, final_canvas={"width": 128, "height": 256})
        adapter = _build_prop_provider_adapter(
            provider_name="cliproxyapi",
            provider_mode="direct",
            model_name="gpt-image-2",
            generation_canvas=generation_canvas,
        )
        self.assertEqual(adapter["adapter"], "gpt_image")
        self.assertEqual(adapter["provider_generation_args"]["size"], "1024x1536")
        self.assertTrue(adapter["adapter_decision"]["fallback_used"])
        self.assertEqual(adapter["adapter_decision"]["reason"], "closest_supported_size")

    def test_gemini_adapter_falls_back_to_closest_supported_tall_ratio(self) -> None:
        generation_canvas = _normalize_generation_canvas({}, final_canvas={"width": 128, "height": 256})
        adapter = _build_prop_provider_adapter(
            provider_name="gemini_cli",
            provider_mode="direct",
            model_name="nano-banana-pro",
            generation_canvas=generation_canvas,
        )
        self.assertEqual(adapter["adapter"], "gemini_cli")
        self.assertEqual(adapter["provider_generation_args"]["aspect_ratio"], "9:16")
        self.assertEqual(adapter["provider_generation_args"]["image_size"], "1K")
        self.assertTrue(adapter["adapter_decision"]["fallback_used"])
        self.assertEqual(adapter["adapter_decision"]["reason"], "closest_supported_ratio")

    def test_prop_validator_accepts_engineering_valid_brazier_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            target_path = temp_path / "target.png"
            source_path = temp_path / "source.png"
            _draw_valid_brazier(target_path, active=False)
            _draw_valid_brazier(source_path, active=True)

            result = validate_prop_asset_set(
                spec=spec,
                asset_paths={
                    "imt_flame_target_brazier_unlit": target_path,
                    "imt_flame_source_brazier_active": source_path,
                },
                output_dir=temp_path / "validation",
            )

            self.assertTrue(result["ok"], result)
            self.assertTrue((temp_path / "validation" / "debug_overlay_imt_flame_source_brazier_active.png").exists())

    def test_transparent_png_with_alpha_channel_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _transparent_spec(temp_path)
            target_path = temp_path / "target.png"
            source_path = temp_path / "source.png"
            _draw_valid_brazier(target_path, active=False)
            _draw_valid_brazier(source_path, active=True)

            result = validate_prop_asset_set(
                spec=spec,
                asset_paths={
                    "imt_flame_target_brazier_unlit": target_path,
                    "imt_flame_source_brazier_active": source_path,
                },
                output_dir=temp_path / "validation",
            )

            self.assertTrue(result["ok"], result)
            self.assertTrue(result["assets"]["imt_flame_target_brazier_unlit"]["diagnostics"]["has_alpha_channel"])

    def test_png_without_alpha_channel_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _transparent_spec(temp_path)
            target_path = temp_path / "target_rgb.png"
            source_path = temp_path / "source_rgb.png"
            Image.new("RGB", (128, 256), (255, 255, 255)).save(target_path)
            Image.new("RGB", (128, 256), (255, 255, 255)).save(source_path)

            result = validate_prop_asset_set(
                spec=spec,
                asset_paths={
                    "imt_flame_target_brazier_unlit": target_path,
                    "imt_flame_source_brazier_active": source_path,
                },
                output_dir=temp_path / "validation",
            )

            self.assertFalse(result["ok"], result)
            failures = result["assets"]["imt_flame_target_brazier_unlit"]["failures"]
            self.assertTrue(any(item.startswith("png_missing_alpha_channel") for item in failures), failures)

    def test_opaque_corners_fail_transparency_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _transparent_spec(temp_path)
            target_path = temp_path / "target.png"
            source_path = temp_path / "source.png"
            _draw_opaque_corner_background(target_path)
            _draw_opaque_corner_background(source_path)

            result = validate_prop_asset_set(
                spec=spec,
                asset_paths={
                    "imt_flame_target_brazier_unlit": target_path,
                    "imt_flame_source_brazier_active": source_path,
                },
                output_dir=temp_path / "validation",
            )

            self.assertFalse(result["ok"], result)
            failures = result["assets"]["imt_flame_target_brazier_unlit"]["failures"]
            self.assertIn("corner_alpha_not_transparent", failures)

    def test_bottom_corner_contact_is_allowed_for_bottom_anchored_props(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _transparent_spec(temp_path)
            target_path = temp_path / "target.png"
            source_path = temp_path / "source.png"
            _draw_bottom_corner_prop(target_path)
            _draw_bottom_corner_prop(source_path)

            result = validate_prop_asset_set(
                spec=spec,
                asset_paths={
                    "imt_flame_target_brazier_unlit": target_path,
                    "imt_flame_source_brazier_active": source_path,
                },
                output_dir=temp_path / "validation",
            )

            failures = result["assets"]["imt_flame_target_brazier_unlit"]["failures"]
            self.assertNotIn("corner_alpha_not_transparent", failures, result)

    def test_object_touching_edge_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _transparent_spec(temp_path)
            target_path = temp_path / "target.png"
            source_path = temp_path / "source.png"
            _draw_touching_edge(target_path)
            _draw_touching_edge(source_path)

            result = validate_prop_asset_set(
                spec=spec,
                asset_paths={
                    "imt_flame_target_brazier_unlit": target_path,
                    "imt_flame_source_brazier_active": source_path,
                },
                output_dir=temp_path / "validation",
            )

            self.assertFalse(result["ok"], result)
            failures = result["assets"]["imt_flame_target_brazier_unlit"]["failures"]
            self.assertIn("opaque_bbox_touches_left_edge", failures)

    def test_prop_validator_rejects_baked_floor_tile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            target_path = temp_path / "target.png"
            source_path = temp_path / "source.png"
            _draw_brazier_with_floor(target_path)
            _draw_brazier_with_floor(source_path)

            result = validate_prop_asset_set(
                spec=spec,
                asset_paths={
                    "imt_flame_target_brazier_unlit": target_path,
                    "imt_flame_source_brazier_active": source_path,
                },
                output_dir=temp_path / "validation",
            )

            self.assertFalse(result["ok"], result)
            failures = result["assets"]["imt_flame_target_brazier_unlit"]["failures"]
            self.assertIn("possible_baked_floor_tile", failures)

    def test_mock_generation_writes_required_prop_deliverables(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            spec["target_project_folder"] = "img/generated/flame_relay_brazier/"
            spec_path = temp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")

            result = generate_prop_assets(spec_path)

            self.assertTrue(result["ok"], result)
            deliverables = Path(result["deliverables"]["deliverables_dir"])
            self.assertTrue((deliverables / "imt_flame_target_brazier_unlit.png").exists())
            self.assertTrue((deliverables / "imt_flame_source_brazier_active.png").exists())
            self.assertTrue((deliverables / "prop_asset_manifest.json").exists())
            self.assertTrue((deliverables / "imt_prop_handoff.json").exists())
            self.assertTrue((deliverables / "validation_summary.json").exists())
            self.assertTrue((deliverables / "preview_sheet.png").exists())
            manifest = json.loads((deliverables / "prop_asset_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], "prop_asset_manifest_v1")
            self.assertEqual(len(manifest["assets"]), 2)
            self.assertTrue((deliverables / "prop_asset_atlas_metadata.json").exists())
            atlas_metadata = json.loads((deliverables / "prop_asset_atlas_metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(atlas_metadata["entries"][0]["atlas_rect"], {"x": 0, "y": 0, "w": 128, "h": 256})
            self.assertEqual(atlas_metadata["entries"][1]["atlas_rect"], {"x": 128, "y": 0, "w": 128, "h": 256})
            handoff = json.loads((deliverables / "imt_prop_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(handoff["schema_version"], "imt_prop_handoff_v1")
            self.assertEqual(handoff["target_project_folder"], "img/generated/flame_relay_brazier/")
            self.assertEqual(handoff["atlas"]["path"], "prop_asset_atlas.png")
            self.assertEqual(handoff["assets"][0]["atlas_rect"], {"x": 0, "y": 0, "w": 128, "h": 256})
            self.assertEqual(handoff["assets"][1]["atlas_rect"], {"x": 128, "y": 0, "w": 128, "h": 256})

    def test_final_deliverable_stays_on_final_canvas_even_when_raw_source_is_high_res(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            spec_path = temp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")

            result = generate_prop_assets(spec_path)

            self.assertTrue(result["ok"], result)
            run_root = Path(result["run_root"])
            with Image.open(run_root / "step_1_raw" / "s1_raw.imt_flame_target_brazier_unlit.png") as raw_image:
                self.assertEqual(raw_image.size, (512, 1024))
            with Image.open(Path(result["outputs"]["imt_flame_target_brazier_unlit"])) as final_image:
                self.assertEqual(final_image.size, (128, 256))

    def test_prop_color_key_cleanup_removes_enclosed_key_holes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            raw_path = temp_path / "raw_with_internal_key_hole.png"
            output_path = temp_path / "keyed.png"
            image = Image.new("RGBA", (64, 64), (255, 0, 255, 255))
            draw = ImageDraw.Draw(image)
            draw.ellipse((14, 10, 50, 54), fill=(120, 80, 40, 255))
            draw.ellipse((27, 27, 37, 37), fill=(255, 0, 255, 255))
            image.save(raw_path)

            payload = apply_color_key_to_image(
                raw_path,
                output_path,
                prompt_color="#FF00FF",
                fallback_colors=["#00FF00"],
                tolerance=24,
                remove_all_key_pixels=True,
            )

            self.assertGreater(payload["removed_internal_key_pixels"], 0, payload)
            with Image.open(output_path) as opened:
                keyed = opened.convert("RGBA")
            self.assertEqual(keyed.getpixel((32, 32))[3], 0)
            self.assertGreater(keyed.getpixel((20, 32))[3], 0)

    def test_cleanup_scorer_prefers_clean_preserved_object(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            raw_path = temp_path / "raw.png"
            _draw_raw_color_key_fixture(raw_path)
            clean_path = temp_path / "clean.png"
            retained_path = temp_path / "retained.png"
            deleted_path = temp_path / "deleted.png"
            fringe_path = temp_path / "fringe.png"
            _draw_cleanup_candidate(clean_path, kind="clean")
            _draw_cleanup_candidate(retained_path, kind="background_retained")
            _draw_cleanup_candidate(deleted_path, kind="object_deleted")
            _draw_cleanup_candidate(fringe_path, kind="fringe")

            result = score_cleanup_candidates(
                raw_path=raw_path,
                candidates=[
                    {"cleanup_id": "clean", "path": str(clean_path)},
                    {"cleanup_id": "background_retained", "path": str(retained_path)},
                    {"cleanup_id": "object_deleted", "path": str(deleted_path)},
                    {"cleanup_id": "fringe", "path": str(fringe_path)},
                ],
                key_colors=["#FF00FF"],
                tolerance=24,
                output_path=temp_path / "score.json",
            )

            self.assertEqual(result["selected_cleanup_id"], "clean", result)
            scores = {item["cleanup_id"]: item for item in result["candidates"]}
            self.assertGreater(scores["clean"]["score"], scores["background_retained"]["score"])
            self.assertGreater(scores["clean"]["score"], scores["object_deleted"]["score"])
            self.assertGreater(scores["clean"]["score"], scores["fringe"]["score"])

    def test_workflow_uses_scorer_selected_cleanup_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            spec["states"] = [spec["states"][0]]
            spec_path = temp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")

            def fake_apply_color_key_to_image(image_path, output_path, *, prompt_color, fallback_colors, tolerance, emit_variant_pool=False, remove_all_key_pixels=False):
                good = output_path.with_name(f"{output_path.stem}.01_conservative{output_path.suffix}")
                bad = output_path.with_name(f"{output_path.stem}.03_balanced{output_path.suffix}")
                _draw_valid_brazier(good, active=False)
                Image.new("RGBA", (128, 256), (0, 0, 0, 0)).save(bad)
                return {
                    "input": str(image_path),
                    "active_key_color": "#FF00FF",
                    "removed_background_pixels": 1,
                    "variants": {
                        "01_conservative": {"label": "Conservative", "output": str(good)},
                        "03_balanced": {"label": "Balanced", "output": str(bad)},
                    },
                }

            with patch("pipeline.prop_asset_workflow.apply_color_key_to_image", side_effect=fake_apply_color_key_to_image):
                result = generate_prop_assets(spec_path)

            self.assertTrue(result["ok"], result)
            run_root = Path(result["run_root"])
            score = json.loads((run_root / "step_3_cleanup_pool" / "prop_cleanup_score.imt_flame_target_brazier_unlit.json").read_text(encoding="utf-8"))
            self.assertEqual(score["selected_cleanup_id"], "v01_conservative", score)
            with Image.open(run_root / "processed" / "imt_flame_target_brazier_unlit.normalized.png") as selected_opened:
                selected_image = selected_opened.convert("RGBA")
            with Image.open(
                run_root / "step_3_cleanup_pool" / "s3_cleanup.imt_flame_target_brazier_unlit.v01_conservative.png"
            ) as expected_opened:
                expected_image = expected_opened.convert("RGBA")
            self.assertEqual(selected_image.size, expected_image.size)
            self.assertEqual(list(selected_image.getdata()), list(expected_image.getdata()))

    def test_transparent_mock_generation_writes_imt_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _transparent_spec(temp_path)
            spec["provider"] = {"name": "gpt_image", "mode": "gpt_image_transparent_prop"}
            spec["model"] = {"name": "gpt-image-2"}
            # Use mock provider name through CLI-independent fixture by patching the spec back to mock
            # while retaining the transparent-native background contract.
            spec["provider"] = {"name": "mock"}
            spec["model"] = {"name": "mock"}
            spec_path = temp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")

            result = generate_prop_assets(spec_path)

            self.assertTrue(result["ok"], result)
            deliverables = Path(result["deliverables"]["deliverables_dir"])
            handoff = json.loads((deliverables / "imt_prop_handoff.json").read_text(encoding="utf-8"))
            self.assertTrue(handoff["alpha_validated"])
            self.assertEqual(handoff["background_mode"], "transparent_native")

    def test_edit_from_routes_clean_target_as_reference_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            spec_path = temp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")

            result = generate_prop_assets(spec_path)

            self.assertTrue(result["ok"], result)
            run_root = Path(result["run_root"])
            requests = json.loads((run_root / "request" / "provider_requests.json").read_text(encoding="utf-8"))
            source_refs = requests["imt_flame_source_brazier_active"]["reference_images"]
            self.assertEqual(len(source_refs), 1)
            self.assertTrue(source_refs[0].endswith("imt_flame_target_brazier_unlit.normalized.png"), source_refs)

    def test_direct_provider_request_payload_is_testable_without_external_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            spec["provider"] = {"name": "cliproxyapi", "mode": "direct"}
            spec["model"] = {"name": "gpt-image-2"}
            spec["background"] = {"mode": "transparent"}
            spec_path = temp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")

            def fake_generate_with_provider(
                *,
                provider_name,
                model_name,
                prompt_text,
                reference_images,
                output_path,
                transparent_background=False,
                size_override=None,
                aspect_ratio_override=None,
                image_size_override=None,
            ):
                active = "source_active" in prompt_text
                self.assertEqual(size_override, "1024x1536")
                self.assertIsNone(aspect_ratio_override)
                self.assertIsNone(image_size_override)
                _make_brazier_source_canvas(active=active, canvas_size=(1024, 1536), background_rgba=(0, 0, 0, 0)).save(output_path)
                return {
                    "provider": provider_name,
                    "model": model_name,
                    "request_mode": "edit" if reference_images else "generate",
                    "reference_images": [str(path) for path in reference_images],
                }

            with patch("pipeline.prop_asset_workflow.generate_with_provider", side_effect=fake_generate_with_provider):
                result = generate_prop_assets(spec_path)

            self.assertTrue(result["ok"], result)
            run_root = Path(result["run_root"])
            requests = json.loads((run_root / "request" / "provider_requests.json").read_text(encoding="utf-8"))
            self.assertEqual(requests["imt_flame_target_brazier_unlit"]["provider"], "cliproxyapi")
            self.assertEqual(requests["imt_flame_target_brazier_unlit"]["reference_images"], [])
            self.assertEqual(requests["imt_flame_target_brazier_unlit"]["generation_canvas"]["derived_size"], {"width": 512, "height": 1024})
            self.assertEqual(requests["imt_flame_target_brazier_unlit"]["adapter_decision"]["provider_size"], "1024x1536")
            source_refs = requests["imt_flame_source_brazier_active"]["reference_images"]
            self.assertEqual(len(source_refs), 1)
            self.assertTrue(source_refs[0].endswith("imt_flame_target_brazier_unlit.normalized.png"), source_refs)

    def test_gemini_provider_request_snapshot_records_aspect_ratio_adapter_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            spec["provider"] = {"name": "gemini_cli", "mode": "direct"}
            spec["model"] = {"name": "nano-banana-pro"}
            spec_path = temp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")

            def fake_generate_with_provider(
                *,
                provider_name,
                model_name,
                prompt_text,
                reference_images,
                output_path,
                transparent_background=False,
                size_override=None,
                aspect_ratio_override=None,
                image_size_override=None,
            ):
                self.assertEqual(provider_name, "gemini_cli")
                self.assertIsNone(size_override)
                self.assertEqual(aspect_ratio_override, "9:16")
                self.assertEqual(image_size_override, "1K")
                self.assertIn("matching 9:16", prompt_text)
                self.assertIn("final 1:2 128x256 sprite", prompt_text)
                active = "source_active" in prompt_text
                _make_brazier_source_canvas(active=active, canvas_size=(576, 1024), background_rgba=(255, 0, 255, 255)).save(output_path)
                return {
                    "provider": provider_name,
                    "model": model_name,
                    "aspect_ratio": aspect_ratio_override,
                    "image_size": image_size_override,
                }

            with patch("pipeline.prop_asset_workflow.generate_with_provider", side_effect=fake_generate_with_provider):
                result = generate_prop_assets(spec_path)

            self.assertTrue(result["ok"], result)
            run_root = Path(result["run_root"])
            requests = json.loads((run_root / "request" / "provider_requests.json").read_text(encoding="utf-8"))
            self.assertEqual(requests["imt_flame_target_brazier_unlit"]["provider_generation_args"]["aspect_ratio"], "9:16")
            self.assertEqual(requests["imt_flame_target_brazier_unlit"]["provider_generation_args"]["image_size"], "1K")
            self.assertEqual(requests["imt_flame_target_brazier_unlit"]["adapter_decision"]["reason"], "closest_supported_ratio")

    def test_gpt_image_provider_uses_color_key_prompt_and_cliproxy_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            spec["provider"] = {"name": "gpt_image", "mode": "gpt_image_prop_color_key"}
            spec["model"] = {"name": "gpt-image-2"}
            spec_path = temp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            seen_provider_names = []

            def fake_generate_with_provider(
                *,
                provider_name,
                model_name,
                prompt_text,
                reference_images,
                output_path,
                transparent_background=False,
                size_override=None,
                aspect_ratio_override=None,
                image_size_override=None,
            ):
                seen_provider_names.append(provider_name)
                self.assertIn("#FF00FF", prompt_text)
                self.assertIn("solid chroma-key background", prompt_text)
                self.assertIn("Generate a high-resolution source image", prompt_text)
                self.assertIn("matching 2:3 at about 1024x1536", prompt_text)
                self.assertIn("final 1:2 128x256 sprite", prompt_text)
                self.assertNotIn("Use a 1:2 composition (source target about 512x1024)", prompt_text)
                self.assertIn("The factory will crop, clean, and normalize", prompt_text)
                self.assertEqual(size_override, "1024x1536")
                self.assertIsNone(aspect_ratio_override)
                self.assertIsNone(image_size_override)
                active = "source_active" in prompt_text
                _make_brazier_source_canvas(active=active, canvas_size=(1024, 1536), background_rgba=(255, 0, 255, 255)).save(output_path)
                return {"provider": provider_name, "model": model_name}

            with patch("pipeline.prop_asset_workflow.generate_with_provider", side_effect=fake_generate_with_provider):
                result = generate_prop_assets(spec_path)

            self.assertTrue(result["ok"], result)
            self.assertEqual(seen_provider_names, ["cliproxyapi", "cliproxyapi"])
            run_root = Path(result["run_root"])
            requests = json.loads((run_root / "request" / "provider_requests.json").read_text(encoding="utf-8"))
            self.assertEqual(requests["imt_flame_target_brazier_unlit"]["adapter_decision"]["provider_size"], "1024x1536")
            self.assertEqual(requests["imt_flame_target_brazier_unlit"]["generation_canvas"]["provider_aspect_ratio"], "2:3")

    def test_cli_provider_override_replaces_mock_model_with_provider_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            spec_path = temp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            captured_specs: list[dict] = []

            def fake_generate_prop_assets(spec_path: Path) -> dict:
                captured_specs.append(json.loads(Path(spec_path).read_text(encoding="utf-8")))
                return {"ok": True, "run_root": str(temp_path / "run")}

            with patch("itf.generate_prop_assets", side_effect=fake_generate_prop_assets):
                exit_code = command_generate_prop_assets(
                    Namespace(
                        spec=str(spec_path),
                        provider="cliproxyapi",
                        model=None,
                        transparent_background=None,
                        out=str(temp_path / "cliproxy_run"),
                    )
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(captured_specs[0]["provider"], {"name": "cliproxyapi", "mode": "direct"})
            self.assertEqual(captured_specs[0]["model"], {"name": "gpt-image-2"})

    def test_cli_provider_override_accepts_explicit_gemini_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            spec = _base_spec(temp_path)
            spec_path = temp_path / "spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            captured_specs: list[dict] = []

            def fake_generate_prop_assets(spec_path: Path) -> dict:
                captured_specs.append(json.loads(Path(spec_path).read_text(encoding="utf-8")))
                return {"ok": True, "run_root": str(temp_path / "run")}

            with patch("itf.generate_prop_assets", side_effect=fake_generate_prop_assets):
                exit_code = command_generate_prop_assets(
                    Namespace(
                        spec=str(spec_path),
                        provider="gemini_cli",
                        model="nano-banana-pro",
                        transparent_background=None,
                        out=None,
                    )
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(captured_specs[0]["provider"], {"name": "gemini_cli", "mode": "direct"})
            self.assertEqual(captured_specs[0]["model"], {"name": "nano-banana-pro"})


if __name__ == "__main__":
    unittest.main()
