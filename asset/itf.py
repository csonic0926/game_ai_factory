#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from pipeline.build_atlas import build_atlas
from pipeline.inspect_manifest import build_summary
from pipeline.reference_pair_workflow import (
    ReferencePairWorkflowError,
    generate_reference_pair,
    load_and_validate_spec,
    prepare_reference_pair_run,
    validate_reference_pair_run,
)
from pipeline.prop_asset_workflow import (
    PropAssetWorkflowError,
    generate_prop_assets,
    prepare_prop_asset_run,
    validate_prop_asset_run,
)
from pipeline.tile_reskin_workflow import (
    TileReskinWorkflowError,
    generate_tile_reskin,
    prepare_tile_reskin_run,
)
from pipeline.sample_regression import snapshot_baseline, verify_baseline
from pipeline.variant_selector import VariantSelectorError, select_variant_pool
from pipeline.validation import (
    ValidationError,
    load_and_validate_config,
    load_and_validate_manifest,
)

REPO_ROOT = Path(__file__).resolve().parent
RENDER_SCRIPT = REPO_ROOT / "blender" / "scripts" / "render_tiles.py"
SCENE_VALIDATE_SCRIPT = REPO_ROOT / "blender" / "scripts" / "validate_scene.py"
CREATE_SAMPLE_SCRIPT = REPO_ROOT / "blender" / "scripts" / "create_sample_factory.py"
REFERENCE_PAIR_EXAMPLES_ROOT = REPO_ROOT / "examples" / "reference_pair_workflow"


def parse_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(description="game_ai_factory asset-factory CLI")
    subparsers = argument_parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate config, manifest, or Blender scene")
    validate_parser.add_argument("--config", help="Path to config JSON")
    validate_parser.add_argument("--manifest", help="Path to manifest JSON")
    validate_parser.add_argument("--scene", help="Path to Blender scene (.blend) for scene validation")
    validate_parser.add_argument(
        "--sample-scene",
        action="store_true",
        help="Enable strict sample fixture checks for Blender scene validation",
    )
    validate_parser.add_argument(
        "--skip-file-checks",
        action="store_true",
        help="Skip manifest file existence checks",
    )
    validate_parser.add_argument("--blender-bin", default="blender", help="Blender executable to use")

    render_parser = subparsers.add_parser("render", help="Render PNG variants and manifest from a Blender scene")
    render_parser.add_argument("--scene", required=True, help="Path to Blender scene (.blend)")
    render_parser.add_argument("--config", required=True, help="Path to config JSON")
    render_parser.add_argument("--blender-bin", default="blender", help="Blender executable to use")

    atlas_parser = subparsers.add_parser("build-atlas", help="Build atlas and tileset metadata from a manifest")
    atlas_parser.add_argument("--manifest", required=True, help="Path to manifest JSON")
    atlas_parser.add_argument("--out", required=True, help="Path to atlas PNG output")
    atlas_parser.add_argument("--columns", type=int, help="Override atlas column count")
    atlas_parser.add_argument("--padding", type=int, help="Override atlas padding")

    inspect_parser = subparsers.add_parser("inspect-manifest", help="Inspect manifest summary")
    inspect_parser.add_argument("--manifest", required=True, help="Path to manifest JSON")

    sample_parser = subparsers.add_parser("create-sample-scene", help="Generate examples/sample_factory.blend")
    sample_parser.add_argument("--blender-bin", default="blender", help="Blender executable to use")

    regression_parser = subparsers.add_parser(
        "sample-regression",
        help="Update or verify the committed sample output baseline",
    )
    regression_parser.add_argument("--output-root", default="output", help="Generated output root")
    regression_parser.add_argument(
        "--baseline-root",
        default="examples/golden/sample_factory",
        help="Baseline directory",
    )
    regression_parser.add_argument("--update", action="store_true", help="Write/update the baseline from current output")

    smoke_parser = subparsers.add_parser(
        "smoke-sample",
        help="Run the full sample fixture pipeline: create, validate, render, atlas, regression",
    )
    smoke_parser.add_argument("--config", default="examples/config.json", help="Path to config JSON")
    smoke_parser.add_argument(
        "--scene",
        default="examples/sample_factory.blend",
        help="Path to sample Blender scene (.blend)",
    )
    smoke_parser.add_argument(
        "--manifest",
        default="output/metadata/manifest.json",
        help="Path to manifest JSON output",
    )
    smoke_parser.add_argument(
        "--output-root",
        default="output",
        help="Generated output root for regression verification",
    )
    smoke_parser.add_argument(
        "--atlas-out",
        default="output/atlas/tileset.png",
        help="Path to atlas PNG output",
    )
    smoke_parser.add_argument("--blender-bin", default="blender", help="Blender executable to use")
    smoke_parser.add_argument(
        "--baseline-root",
        default="examples/golden/sample_factory",
        help="Baseline directory",
    )
    smoke_parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update the committed baseline at the end of the smoke run",
    )

    ref_prepare_parser = subparsers.add_parser(
        "prepare-reference-pair",
        help="Prepare a reference-pair workflow run with prompts and references for requested variant(s)",
    )
    ref_prepare_parser.add_argument("--spec", required=True, help="Path to reference-pair spec JSON")

    ref_generate_parser = subparsers.add_parser(
        "generate-reference-pair",
        help="Prepare, generate/ingest Step 1 output, and validate requested variant(s) from the reference-pair workflow",
    )
    ref_generate_parser.add_argument("--spec", required=True, help="Path to reference-pair spec JSON")
    ref_generate_parser.add_argument(
        "--ensure-proxy",
        action="store_true",
        help="For cliproxyapi/GPT Image runs, start the local cli-proxy if the /v1/models health check is unreachable.",
    )

    wall_generate_parser = subparsers.add_parser(
        "generate-wall-reference-pair",
        help="Generate wall reference-pair variants with configurable height and side selection",
    )
    wall_generate_parser.add_argument("--height", choices=["1", "2"], default="1", help="Wall height in tile units")
    wall_generate_parser.add_argument(
        "--variant",
        action="append",
        choices=["left", "right"],
        default=[],
        help="Wall side to generate. Repeatable. Defaults to both left and right.",
    )
    wall_generate_parser.add_argument(
        "--provider",
        default="mock",
        help="Provider/backend name to place in the generated spec (canonical: mock, gemini_cli, cliproxyapi, agent_handoff; legacy aliases remain accepted)",
    )
    wall_generate_parser.add_argument(
        "--model",
        default="",
        help="Optional model name for the chosen provider/backend (for example: nano-banana-2, nano-banana-pro, gpt-image-2)",
    )
    wall_generate_parser.add_argument(
        "--run-id",
        help="Optional run id override. Defaults to wall_<height>u_<variants>.",
    )
    wall_generate_parser.add_argument(
        "--output-root",
        default="output/reference_pair_runs",
        help="Reference-pair run output root",
    )
    wall_generate_parser.add_argument(
        "--spec-out",
        help="Optional path to write the generated wall spec JSON for inspection/reuse",
    )
    wall_generate_parser.add_argument(
        "--ensure-proxy",
        action="store_true",
        help="For cliproxyapi/GPT Image runs, start the local cli-proxy if the /v1/models health check is unreachable.",
    )

    ref_validate_parser = subparsers.add_parser(
        "validate-reference-pair",
        help="Validate generated tile PNGs against the prepared reference-pair run",
    )
    ref_validate_parser.add_argument("--run-root", required=True, help="Prepared reference-pair run root")
    ref_validate_parser.add_argument("--full-image", help="Override generated full image path")
    ref_validate_parser.add_argument("--half-image", help="Override generated half image path")
    ref_validate_parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Override generated image path for an arbitrary variant using variant=/absolute/path.png",
    )

    select_variant_parser = subparsers.add_parser(
        "select-reference-pair-variant",
        help="Score generated cleanup variants against normalized reference geometry",
    )
    select_variant_parser.add_argument("--run-root", required=True, help="Prepared reference-pair run root")
    select_variant_parser.add_argument("--variant", default="full", help="Variant to score")

    prop_prepare_parser = subparsers.add_parser(
        "prepare-prop-assets",
        help="Prepare a prop/object asset workflow run with prompts for requested states",
    )
    prop_prepare_parser.add_argument("--spec", required=True, help="Path to prop asset workflow spec JSON")

    prop_generate_parser = subparsers.add_parser(
        "generate-prop-assets",
        help="Generate, validate, and emit deliverables for a prop/object asset workflow spec",
    )
    prop_generate_parser.add_argument("--spec", required=True, help="Path to prop asset workflow spec JSON")
    prop_generate_parser.add_argument("--provider", help="Override prop provider, e.g. gpt_image")
    prop_generate_parser.add_argument(
        "--transparent-background",
        choices=["true", "false"],
        help="Deprecated for gpt-image-2 prop runs; use false/color-key because native transparent background is not supported by that model.",
    )
    prop_generate_parser.add_argument(
        "--model",
        help="Override prop model for the chosen provider, e.g. gpt-image-2, nano-banana-2, or nano-banana-pro",
    )
    prop_generate_parser.add_argument("--out", help="Override run root for this prop run")

    tile_reskin_prepare_parser = subparsers.add_parser(
        "prepare-tile-reskin",
        help="Prepare a tile re-skin run (re-texture an existing geometrically-correct tile set)",
    )
    tile_reskin_prepare_parser.add_argument("--spec", required=True, help="Path to tile_reskin_workflow_v1 spec JSON")

    tile_reskin_generate_parser = subparsers.add_parser(
        "generate-tile-reskin",
        help="Generate materials, re-skin every source tile variant, and emit deliverables",
    )
    tile_reskin_generate_parser.add_argument("--spec", required=True, help="Path to tile_reskin_workflow_v1 spec JSON")
    tile_reskin_generate_parser.add_argument("--provider", help="Override provider, e.g. mock / gpt_image / gemini_cli")
    tile_reskin_generate_parser.add_argument("--out", help="Override run root for this tile re-skin run")

    prop_validate_parser = subparsers.add_parser(
        "validate-prop-assets",
        help="Validate generated prop/object asset PNGs against the prepared prop workflow run",
    )
    prop_validate_parser.add_argument("--run-root", help="Prepared prop asset run root")
    prop_validate_parser.add_argument("--run", help="Alias for --run-root")
    prop_validate_parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Override image path for an asset using asset_id=/absolute/path.png",
    )

    return argument_parser.parse_args()


def run_subprocess(command: list[str]) -> int:
    completed_process = subprocess.run(command, cwd=REPO_ROOT)
    return completed_process.returncode


def run_step(step_name: str, command: list[str]) -> None:
    print(json.dumps({"step": step_name, "command": command}, indent=2))
    exit_code = run_subprocess(command)
    if exit_code != 0:
        raise SystemExit(exit_code)


def build_wall_reference_pair_spec(
    *,
    height_units: int,
    variants: list[str],
    provider_name: str,
    model_name: str,
    output_root: Path,
    run_id: str,
) -> dict:
    wall_object_name = "101_wall_straight" if height_units == 1 else "102_wall_straight_2u"
    height_label = "1u" if height_units == 1 else "2u"
    theme = f"pixel stone wall {height_label}"
    provider_payload = {"name": provider_name}
    if provider_name in {"imagegen_handoff", "agent_handoff"}:
        provider_payload["mode"] = "agent_handoff"
        provider_payload["agent_tool"] = "imagegen"
    return {
        "schema_version": "reference_pair_workflow_v1",
        "theme": theme,
        "run_id": run_id,
        "output_root": str(output_root),
        "variants": variants,
        "provider": provider_payload,
        "model": {"name": model_name},
        "background": {
            "mode": "color_key",
            "prompt_color": "#FF00FF",
            "fallback_colors": ["#00FF00"],
            "tolerance": 24,
        },
        "reference_pair": {
            "left": f"../golden/sample_factory/images/{wall_object_name}_rot90.png",
            "right": f"../golden/sample_factory/images/{wall_object_name}_rot0.png",
        },
        "variant_profiles": {
            "left": {
                "role_text": "left-facing isometric wall segment",
                "geometry_guidance": "The visible wall face should favor the left side of the isometric view and keep the base anchored exactly to the reference silhouette",
                "sheet_label": f"left wall {height_label}",
                "selector_profile": "wall",
                "wall_side": "left",
                "height_units": height_units,
                "reference_rotation": 90,
            },
            "right": {
                "role_text": "right-facing isometric wall segment",
                "geometry_guidance": "The visible wall face should favor the right side of the isometric view and keep the base anchored exactly to the reference silhouette",
                "sheet_label": f"right wall {height_label}",
                "selector_profile": "wall",
                "wall_side": "right",
                "height_units": height_units,
                "reference_rotation": 0,
            },
        },
        "prompt": "pixel art style dungeon stone wall with readable block seams, restrained shading, and no extra props",
        "negative_prompt": "no scene background, no cast shadow, no floor tile attached, no extra props, no border, no text, no watermark, no shape deformation",
        "generator_notes": f"preserve the same {height_label} wall family between left and right variants",
        "validation": {
            "iou_soft_fail": 0.92,
            "iou_hard_fail": 0.80,
            "bbox_delta_soft_fail": 6,
            "bbox_delta_hard_fail": 16,
        },
    }


def command_validate(arguments: argparse.Namespace) -> int:
    if not arguments.config and not arguments.manifest and not arguments.scene:
        raise SystemExit("validate requires at least one of: --config, --manifest, --scene")

    results: dict[str, dict] = {}

    try:
        if arguments.config:
            config_path = Path(arguments.config).expanduser().resolve()
            config_data, config_warnings = load_and_validate_config(config_path)
            results["config"] = {
                "path": str(config_path),
                "warnings": config_warnings,
                "normalized": config_data,
            }

        if arguments.manifest:
            manifest_path = Path(arguments.manifest).expanduser().resolve()
            manifest_data, manifest_warnings = load_and_validate_manifest(
                manifest_path,
                require_files=not arguments.skip_file_checks,
            )
            results["manifest"] = {
                "path": str(manifest_path),
                "warnings": manifest_warnings,
                "entry_count": len(manifest_data["entries"]),
            }
    except ValidationError as validation_error:
        print(json.dumps({"ok": False, "error": str(validation_error)}, indent=2))
        return 1

    if results:
        print(json.dumps({"ok": True, "results": results}, indent=2))

    if arguments.scene:
        if not arguments.config:
            raise SystemExit("scene validation requires --config")

        command = [
            arguments.blender_bin,
            "-b",
            "--factory-startup",
            str(Path(arguments.scene).expanduser().resolve()),
            "-P",
            str(SCENE_VALIDATE_SCRIPT),
            "--",
            f"--config={Path(arguments.config).expanduser().resolve()}",
        ]
        if arguments.sample_scene:
            command.append("--sample-scene=true")
        return run_subprocess(command)

    return 0


def command_select_reference_pair_variant(arguments: argparse.Namespace) -> int:
    try:
        result = select_variant_pool(Path(arguments.run_root).expanduser().resolve(), variant=arguments.variant)
    except VariantSelectorError as error:
        print(json.dumps({"ok": False, "mode": "select-reference-pair-variant", "error": str(error)}, indent=2))
        return 1
    print(json.dumps({"ok": True, "mode": "select-reference-pair-variant", "result": result}, indent=2))
    return 0


def command_render(arguments: argparse.Namespace) -> int:
    config_path = Path(arguments.config).expanduser().resolve()
    try:
        config_data, warnings = load_and_validate_config(config_path)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    except ValidationError as validation_error:
        print(json.dumps({"ok": False, "error": str(validation_error)}, indent=2))
        return 1

    command = [
        arguments.blender_bin,
        "-b",
        "--factory-startup",
        str(Path(arguments.scene).expanduser().resolve()),
        "-P",
        str(RENDER_SCRIPT),
        "--",
        f"--config={config_path}",
    ]
    render_exit_code = run_subprocess(command)
    if render_exit_code != 0:
        return render_exit_code

    output_mode = str(config_data.get("output_mode", "png")).strip().lower()
    if output_mode not in {"atlas", "both"}:
        return 0

    try:
        output_root = Path(config_data["output_root"]).expanduser().resolve()
        manifest_path = output_root / "metadata" / "manifest.json"
        atlas_output_path = output_root / "atlas" / "tileset.png"
        manifest_data, manifest_warnings = load_and_validate_manifest(manifest_path, require_files=True)
        for warning in manifest_warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

        atlas_config = config_data.get("atlas", {})
        metadata_path = build_atlas(
            manifest_data,
            atlas_output_path,
            int(atlas_config.get("columns", 8)),
            int(atlas_config.get("padding", 0)),
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "render-post-atlas",
                    "output_mode": output_mode,
                    "atlas_path": str(atlas_output_path),
                    "metadata_path": str(metadata_path),
                },
                indent=2,
            )
        )
        return 0
    except ValidationError as validation_error:
        print(json.dumps({"ok": False, "error": str(validation_error)}, indent=2))
        return 1


def command_build_atlas(arguments: argparse.Namespace) -> int:
    try:
        manifest_path = Path(arguments.manifest).expanduser().resolve()
        output_path = Path(arguments.out).expanduser().resolve()
        manifest_data, warnings = load_and_validate_manifest(manifest_path, require_files=True)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

        columns = arguments.columns if arguments.columns is not None else 8
        padding = arguments.padding if arguments.padding is not None else 0
        if columns <= 0:
            raise ValidationError("Atlas columns must be a positive integer.")
        if padding < 0:
            raise ValidationError("Atlas padding must be zero or greater.")

        metadata_path = build_atlas(manifest_data, output_path, columns, padding)
        print(
            json.dumps(
                {
                    "ok": True,
                    "atlas_path": str(output_path),
                    "metadata_path": str(metadata_path),
                    "entry_count": len(manifest_data["entries"]),
                },
                indent=2,
            )
        )
        return 0
    except ValidationError as validation_error:
        print(json.dumps({"ok": False, "error": str(validation_error)}, indent=2))
        return 1


def command_inspect_manifest(arguments: argparse.Namespace) -> int:
    try:
        manifest_path = Path(arguments.manifest).expanduser().resolve()
        manifest_data, warnings = load_and_validate_manifest(manifest_path, require_files=True)
        print(
            json.dumps(
                {
                    "ok": True,
                    "path": str(manifest_path),
                    "warnings": warnings,
                    "summary": build_summary(manifest_data),
                },
                indent=2,
            )
        )
        return 0
    except ValidationError as validation_error:
        print(json.dumps({"ok": False, "error": str(validation_error)}, indent=2))
        return 1


def command_create_sample_scene(arguments: argparse.Namespace) -> int:
    command = [
        arguments.blender_bin,
        "-b",
        "--factory-startup",
        "-P",
        str(CREATE_SAMPLE_SCRIPT),
    ]
    return run_subprocess(command)


def command_sample_regression(arguments: argparse.Namespace) -> int:
    output_root = Path(arguments.output_root).expanduser().resolve()
    baseline_root = Path(arguments.baseline_root).expanduser().resolve()

    if arguments.update:
        summary = snapshot_baseline(output_root, baseline_root)
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "update",
                    "baseline_root": str(baseline_root),
                    "summary": summary,
                },
                indent=2,
            )
        )
        return 0

    result = verify_baseline(output_root, baseline_root)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


def command_smoke_sample(arguments: argparse.Namespace) -> int:
    config_path = Path(arguments.config).expanduser().resolve()
    scene_path = Path(arguments.scene).expanduser().resolve()
    manifest_path = Path(arguments.manifest).expanduser().resolve()
    atlas_output_path = Path(arguments.atlas_out).expanduser().resolve()
    baseline_root = Path(arguments.baseline_root).expanduser().resolve()

    run_step(
        "create_sample_scene",
        ["python3", str(REPO_ROOT / "itf.py"), "create-sample-scene", "--blender-bin", arguments.blender_bin],
    )
    run_step(
        "validate_sample_scene",
        [
            "python3",
            str(REPO_ROOT / "itf.py"),
            "validate",
            "--scene",
            str(scene_path),
            "--config",
            str(config_path),
            "--sample-scene",
            "--blender-bin",
            arguments.blender_bin,
        ],
    )
    run_step(
        "render_sample_scene",
        [
            "python3",
            str(REPO_ROOT / "itf.py"),
            "render",
            "--scene",
            str(scene_path),
            "--config",
            str(config_path),
            "--blender-bin",
            arguments.blender_bin,
        ],
    )
    run_step(
        "build_sample_atlas",
        [
            "python3",
            str(REPO_ROOT / "itf.py"),
            "build-atlas",
            "--manifest",
            str(manifest_path),
            "--out",
            str(atlas_output_path),
        ],
    )
    run_step(
        "verify_sample_regression" if not arguments.update_baseline else "update_sample_regression",
        [
            "python3",
            str(REPO_ROOT / "itf.py"),
            "sample-regression",
            "--output-root",
            str(Path(arguments.output_root).expanduser().resolve()),
            "--baseline-root",
            str(baseline_root),
            *(["--update"] if arguments.update_baseline else []),
        ],
    )

    print(
        json.dumps(
            {
                "ok": True,
                "smoke_sample": {
                    "config": str(config_path),
                    "scene": str(scene_path),
                    "manifest": str(manifest_path),
                    "atlas_out": str(atlas_output_path),
                    "baseline_root": str(baseline_root),
                    "baseline_mode": "update" if arguments.update_baseline else "verify",
                },
            },
            indent=2,
        )
    )
    return 0


def command_prepare_reference_pair(arguments: argparse.Namespace) -> int:
    try:
        result = prepare_reference_pair_run(Path(arguments.spec).expanduser().resolve())
        print(json.dumps({"ok": True, "mode": "prepare-reference-pair", "result": result}, indent=2))
        return 0
    except ReferencePairWorkflowError as error:
        print(json.dumps({"ok": False, "mode": "prepare-reference-pair", "error": str(error)}, indent=2))
        return 1


def command_generate_reference_pair(arguments: argparse.Namespace) -> int:
    try:
        result = generate_reference_pair(
            Path(arguments.spec).expanduser().resolve(),
            ensure_proxy=bool(getattr(arguments, "ensure_proxy", False)),
        )
        print(json.dumps({"ok": True, "mode": "generate-reference-pair", "result": result}, indent=2))
        return 0
    except ReferencePairWorkflowError as error:
        print(json.dumps({"ok": False, "mode": "generate-reference-pair", "error": str(error)}, indent=2))
        return 1


def command_generate_wall_reference_pair(arguments: argparse.Namespace) -> int:
    try:
        height_units = int(arguments.height)
        variants = arguments.variant or ["left", "right"]
        normalized_variants: list[str] = []
        for variant in variants:
            if variant not in normalized_variants:
                normalized_variants.append(variant)
        variants = normalized_variants
        variant_label = "_".join(variants)
        run_id = arguments.run_id or f"wall_{height_units}u_{variant_label}"
        spec = build_wall_reference_pair_spec(
            height_units=height_units,
            variants=variants,
            provider_name=str(arguments.provider).strip() or "mock",
            model_name=str(arguments.model).strip() or "",
            output_root=Path(arguments.output_root).expanduser().resolve(),
            run_id=run_id,
        )
        spec_out = (
            Path(arguments.spec_out).expanduser().resolve()
            if arguments.spec_out
            else REFERENCE_PAIR_EXAMPLES_ROOT / f"{run_id}.generated.spec.json"
        )
        spec_out.parent.mkdir(parents=True, exist_ok=True)
        spec_out.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        normalized_spec, _ = load_and_validate_spec(spec_out)
        provider_mode = str(normalized_spec.get("provider", {}).get("mode", "direct")).strip().lower() or "direct"
        if provider_mode == "agent_handoff":
            result = prepare_reference_pair_run(spec_out)
            mode = "generate-wall-reference-pair.prepare-agent-handoff"
        else:
            result = generate_reference_pair(spec_out, ensure_proxy=bool(getattr(arguments, "ensure_proxy", False)))
            mode = "generate-wall-reference-pair"
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": mode,
                    "spec_path": str(spec_out),
                    "height": height_units,
                    "variants": variants,
                    "result": result,
                },
                indent=2,
            )
        )
        return 0
    except ReferencePairWorkflowError as error:
        print(json.dumps({"ok": False, "mode": "generate-wall-reference-pair", "error": str(error)}, indent=2))
        return 1


def command_validate_reference_pair(arguments: argparse.Namespace) -> int:
    try:
        variant_images: dict[str, Path] = {}
        for raw_item in arguments.image:
            if "=" not in raw_item:
                raise ReferencePairWorkflowError(f"Invalid --image value '{raw_item}'. Expected variant=/path/to/image.png")
            variant_name, path_value = raw_item.split("=", 1)
            normalized_variant = variant_name.strip().lower()
            if not normalized_variant or not path_value.strip():
                raise ReferencePairWorkflowError(f"Invalid --image value '{raw_item}'. Expected variant=/path/to/image.png")
            variant_images[normalized_variant] = Path(path_value).expanduser().resolve()
        result = validate_reference_pair_run(
            Path(arguments.run_root).expanduser().resolve(),
            full_image=Path(arguments.full_image).expanduser().resolve() if arguments.full_image else None,
            half_image=Path(arguments.half_image).expanduser().resolve() if arguments.half_image else None,
            variant_images=variant_images,
        )
        print(json.dumps({"ok": result["ok"], "mode": "validate-reference-pair", "result": result}, indent=2))
        return 0 if result["ok"] else 1
    except ReferencePairWorkflowError as error:
        print(json.dumps({"ok": False, "mode": "validate-reference-pair", "error": str(error)}, indent=2))
        return 1


def command_prepare_prop_assets(arguments: argparse.Namespace) -> int:
    try:
        result = prepare_prop_asset_run(Path(arguments.spec).expanduser().resolve())
        print(json.dumps({"ok": True, "mode": "prepare-prop-assets", "result": result}, indent=2))
        return 0
    except PropAssetWorkflowError as error:
        print(json.dumps({"ok": False, "mode": "prepare-prop-assets", "error": str(error)}, indent=2))
        return 1


def command_generate_prop_assets(arguments: argparse.Namespace) -> int:
    try:
        spec_path = Path(arguments.spec).expanduser().resolve()
        if arguments.provider or arguments.transparent_background or arguments.model or arguments.out:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            model_override = str(arguments.model or "").strip().lower()
            if arguments.provider:
                provider_name = str(arguments.provider).strip().lower()
                default_model = ""
                if provider_name in {"gpt_image", "gpt_image_transparent_prop"}:
                    spec["provider"] = {"name": "gpt_image", "mode": "gpt_image_prop_color_key"}
                    default_model = "gpt-image-2"
                    spec["background"] = {"mode": "color_key", "prompt_color": "#FF00FF", "fallback_colors": ["#00FF00"], "tolerance": 24}
                else:
                    if provider_name == "agent_handoff":
                        spec["provider"] = {"name": provider_name, "mode": "agent_handoff", "agent_tool": "imagegen"}
                        default_model = "gpt-image-2"
                    else:
                        spec["provider"] = {"name": provider_name, "mode": "direct"}
                        if provider_name in {"cliproxyapi", "gpt_image_2", "imagegen"}:
                            default_model = "gpt-image-2"
                        elif provider_name in {"gemini_cli", "nano_banana"}:
                            default_model = "nano-banana-2"
                        elif provider_name == "nano_banana_pro":
                            default_model = "nano-banana-pro"
                        elif provider_name == "mock":
                            default_model = "mock"
                existing_model = ""
                if isinstance(spec.get("model"), dict):
                    existing_model = str(spec["model"].get("name", "")).strip().lower()
                model_name = model_override or default_model or existing_model
                if default_model and existing_model == "mock" and not model_override:
                    model_name = default_model
                if model_name:
                    spec["model"] = {"name": model_name}
            elif model_override:
                spec["model"] = {"name": model_override}
            if arguments.transparent_background == "true":
                raise PropAssetWorkflowError(
                    "--transparent-background true is not supported for gpt-image-2 prop runs; use color-key background and cleanup scoring."
                )
            elif arguments.transparent_background == "false":
                spec["background"] = {"mode": "color_key", "prompt_color": "#FF00FF", "fallback_colors": ["#00FF00"], "tolerance": 24}
            if arguments.out:
                run_root = Path(arguments.out).expanduser().resolve()
                spec["output_root"] = str(run_root.parent)
                spec["run_id"] = run_root.name
            with tempfile.NamedTemporaryFile("w", suffix=".prop.spec.json", delete=False, encoding="utf-8") as temp_file:
                json.dump(spec, temp_file, indent=2)
                temp_file.write("\n")
                spec_path = Path(temp_file.name)
        result = generate_prop_assets(spec_path)
        print(json.dumps({"ok": result["ok"], "mode": "generate-prop-assets", "result": result}, indent=2))
        return 0 if result["ok"] else 1
    except (PropAssetWorkflowError, ReferencePairWorkflowError) as error:
        print(json.dumps({"ok": False, "mode": "generate-prop-assets", "error": str(error)}, indent=2))
        return 1


def command_prepare_tile_reskin(arguments: argparse.Namespace) -> int:
    try:
        result = prepare_tile_reskin_run(Path(arguments.spec).expanduser().resolve())
        print(json.dumps({"ok": True, "mode": "prepare-tile-reskin", "result": result}, indent=2))
        return 0
    except TileReskinWorkflowError as error:
        print(json.dumps({"ok": False, "mode": "prepare-tile-reskin", "error": str(error)}, indent=2))
        return 1


def command_generate_tile_reskin(arguments: argparse.Namespace) -> int:
    try:
        spec_path = Path(arguments.spec).expanduser().resolve()
        if arguments.provider or arguments.out:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            if arguments.provider:
                provider_name = str(arguments.provider).strip().lower()
                mode = "mock" if provider_name == "mock" else "direct"
                spec["provider"] = {"name": provider_name, "mode": mode}
            if arguments.out:
                run_root = Path(arguments.out).expanduser().resolve()
                spec["output_root"] = str(run_root.parent)
                spec["run_id"] = run_root.name
            with tempfile.NamedTemporaryFile("w", suffix=".tile_reskin.spec.json", delete=False, encoding="utf-8") as temp_file:
                json.dump(spec, temp_file, indent=2)
                temp_file.write("\n")
                spec_path = Path(temp_file.name)
        result = generate_tile_reskin(spec_path)
        print(json.dumps({"ok": result["ok"], "mode": "generate-tile-reskin", "result": result}, indent=2))
        return 0 if result["ok"] else 1
    except TileReskinWorkflowError as error:
        print(json.dumps({"ok": False, "mode": "generate-tile-reskin", "error": str(error)}, indent=2))
        return 1


def command_validate_prop_assets(arguments: argparse.Namespace) -> int:
    try:
        run_root_value = arguments.run_root or arguments.run
        if not run_root_value:
            raise PropAssetWorkflowError("validate-prop-assets requires --run-root or --run")
        asset_paths: dict[str, Path] = {}
        for raw_item in arguments.image:
            if "=" not in raw_item:
                raise PropAssetWorkflowError(f"Invalid --image value '{raw_item}'. Expected asset_id=/path/to/image.png")
            asset_id, path_value = raw_item.split("=", 1)
            normalized_asset_id = asset_id.strip()
            if not normalized_asset_id or not path_value.strip():
                raise PropAssetWorkflowError(f"Invalid --image value '{raw_item}'. Expected asset_id=/path/to/image.png")
            asset_paths[normalized_asset_id] = Path(path_value).expanduser().resolve()
        result = validate_prop_asset_run(
            Path(run_root_value).expanduser().resolve(),
            asset_paths=asset_paths or None,
        )
        print(json.dumps({"ok": result["ok"], "mode": "validate-prop-assets", "result": result}, indent=2))
        return 0 if result["ok"] else 1
    except PropAssetWorkflowError as error:
        print(json.dumps({"ok": False, "mode": "validate-prop-assets", "error": str(error)}, indent=2))
        return 1


def main() -> None:
    arguments = parse_arguments()

    if arguments.command == "validate":
        raise SystemExit(command_validate(arguments))
    if arguments.command == "render":
        raise SystemExit(command_render(arguments))
    if arguments.command == "build-atlas":
        raise SystemExit(command_build_atlas(arguments))
    if arguments.command == "inspect-manifest":
        raise SystemExit(command_inspect_manifest(arguments))
    if arguments.command == "create-sample-scene":
        raise SystemExit(command_create_sample_scene(arguments))
    if arguments.command == "sample-regression":
        raise SystemExit(command_sample_regression(arguments))
    if arguments.command == "smoke-sample":
        raise SystemExit(command_smoke_sample(arguments))
    if arguments.command == "prepare-reference-pair":
        raise SystemExit(command_prepare_reference_pair(arguments))
    if arguments.command == "generate-reference-pair":
        raise SystemExit(command_generate_reference_pair(arguments))
    if arguments.command == "generate-wall-reference-pair":
        raise SystemExit(command_generate_wall_reference_pair(arguments))
    if arguments.command == "validate-reference-pair":
        raise SystemExit(command_validate_reference_pair(arguments))
    if arguments.command == "select-reference-pair-variant":
        raise SystemExit(command_select_reference_pair_variant(arguments))
    if arguments.command == "prepare-prop-assets":
        raise SystemExit(command_prepare_prop_assets(arguments))
    if arguments.command == "generate-prop-assets":
        raise SystemExit(command_generate_prop_assets(arguments))
    if arguments.command == "validate-prop-assets":
        raise SystemExit(command_validate_prop_assets(arguments))
    if arguments.command == "prepare-tile-reskin":
        raise SystemExit(command_prepare_tile_reskin(arguments))
    if arguments.command == "generate-tile-reskin":
        raise SystemExit(command_generate_tile_reskin(arguments))

    raise SystemExit(f"Unknown command: {arguments.command}")


if __name__ == "__main__":
    main()
