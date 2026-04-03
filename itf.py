#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from pipeline.build_atlas import build_atlas
from pipeline.inspect_manifest import build_summary
from pipeline.reference_pair_workflow import (
    ReferencePairWorkflowError,
    generate_reference_pair,
    prepare_reference_pair_run,
    validate_reference_pair_run,
)
from pipeline.sample_regression import snapshot_baseline, verify_baseline
from pipeline.validation import (
    ValidationError,
    load_and_validate_config,
    load_and_validate_manifest,
)

REPO_ROOT = Path(__file__).resolve().parent
RENDER_SCRIPT = REPO_ROOT / "blender" / "scripts" / "render_tiles.py"
SCENE_VALIDATE_SCRIPT = REPO_ROOT / "blender" / "scripts" / "validate_scene.py"
CREATE_SAMPLE_SCRIPT = REPO_ROOT / "blender" / "scripts" / "create_sample_factory.py"


def parse_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(description="isometric_tile_factory repo CLI")
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
        help="Prepare, generate, and validate requested variant(s) from the reference-pair workflow",
    )
    ref_generate_parser.add_argument("--spec", required=True, help="Path to reference-pair spec JSON")

    ref_validate_parser = subparsers.add_parser(
        "validate-reference-pair",
        help="Validate generated tile PNGs against the prepared reference-pair run",
    )
    ref_validate_parser.add_argument("--run-root", required=True, help="Prepared reference-pair run root")
    ref_validate_parser.add_argument("--full-image", help="Override generated full image path")
    ref_validate_parser.add_argument("--half-image", help="Override generated half image path")

    return argument_parser.parse_args()


def run_subprocess(command: list[str]) -> int:
    completed_process = subprocess.run(command, cwd=REPO_ROOT)
    return completed_process.returncode


def run_step(step_name: str, command: list[str]) -> None:
    print(json.dumps({"step": step_name, "command": command}, indent=2))
    exit_code = run_subprocess(command)
    if exit_code != 0:
        raise SystemExit(exit_code)


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
        result = generate_reference_pair(Path(arguments.spec).expanduser().resolve())
        print(json.dumps({"ok": True, "mode": "generate-reference-pair", "result": result}, indent=2))
        return 0
    except ReferencePairWorkflowError as error:
        print(json.dumps({"ok": False, "mode": "generate-reference-pair", "error": str(error)}, indent=2))
        return 1


def command_validate_reference_pair(arguments: argparse.Namespace) -> int:
    try:
        result = validate_reference_pair_run(
            Path(arguments.run_root).expanduser().resolve(),
            full_image=Path(arguments.full_image).expanduser().resolve() if arguments.full_image else None,
            half_image=Path(arguments.half_image).expanduser().resolve() if arguments.half_image else None,
        )
        print(json.dumps({"ok": result["ok"], "mode": "validate-reference-pair", "result": result}, indent=2))
        return 0 if result["ok"] else 1
    except ReferencePairWorkflowError as error:
        print(json.dumps({"ok": False, "mode": "validate-reference-pair", "error": str(error)}, indent=2))
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
    if arguments.command == "validate-reference-pair":
        raise SystemExit(command_validate_reference_pair(arguments))

    raise SystemExit(f"Unknown command: {arguments.command}")


if __name__ == "__main__":
    main()
