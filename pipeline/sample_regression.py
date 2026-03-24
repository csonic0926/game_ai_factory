#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError as import_error:
    raise SystemExit("Pillow is required. Install with: python3 -m pip install pillow") from import_error


def parse_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(description="Snapshot or verify the sample output baseline.")
    argument_parser.add_argument(
        "--output-root",
        default="output",
        help="Generated output root to snapshot or verify",
    )
    argument_parser.add_argument(
        "--baseline-root",
        default="examples/golden/sample_factory",
        help="Committed baseline directory",
    )
    argument_parser.add_argument(
        "--update",
        action="store_true",
        help="Write/update the baseline from current outputs instead of verifying",
    )
    return argument_parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_image_pixels(path: Path) -> str:
    digest = hashlib.sha256()
    with Image.open(path) as image:
        rgba_image = image.convert("RGBA")
        digest.update(f"{rgba_image.width}x{rgba_image.height}".encode("utf-8"))
        digest.update(rgba_image.tobytes())
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as input_file:
        return json.load(input_file)


def normalize_manifest(manifest_data: dict) -> dict:
    normalized_entries = []
    for entry in manifest_data["entries"]:
        normalized_entry = dict(entry)
        normalized_entry["file"] = Path(normalized_entry["file"]).name
        normalized_entries.append(normalized_entry)
    return {
        "tileset_name": manifest_data["tileset_name"],
        "entries": normalized_entries,
    }


def normalize_tileset(tileset_data: dict) -> dict:
    normalized_entries = []
    for entry in tileset_data["entries"]:
        normalized_entry = dict(entry)
        normalized_entry["file"] = Path(normalized_entry["file"]).name
        normalized_entries.append(normalized_entry)

    normalized_tileset = dict(tileset_data)
    normalized_tileset["atlas_path"] = Path(normalized_tileset["atlas_path"]).name
    normalized_tileset["entries"] = normalized_entries
    return normalized_tileset


def collect_current_artifacts(output_root: Path) -> dict[str, Path]:
    artifacts = {
        "atlas_png": output_root / "atlas" / "tileset.png",
        "manifest_json": output_root / "metadata" / "manifest.json",
        "tileset_json": output_root / "metadata" / "tileset.json",
    }

    png_directory = output_root / "png"
    for png_path in sorted(png_directory.glob("*.png")):
        artifacts[f"png/{png_path.name}"] = png_path

    missing = [label for label, path in artifacts.items() if not path.exists()]
    if missing:
        raise RuntimeError(f"Missing output artifact(s): {', '.join(missing)}")

    return artifacts


def snapshot_baseline(output_root: Path, baseline_root: Path) -> dict:
    artifacts = collect_current_artifacts(output_root)
    images_dir = baseline_root / "images"
    metadata_dir = baseline_root / "metadata"
    images_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(artifacts["atlas_png"], images_dir / "tileset.png")

    for label, path in artifacts.items():
        if label.startswith("png/"):
            shutil.copy2(path, images_dir / path.name)

    manifest_data = normalize_manifest(load_json(artifacts["manifest_json"]))
    tileset_data = normalize_tileset(load_json(artifacts["tileset_json"]))

    (metadata_dir / "manifest.normalized.json").write_text(
        json.dumps(manifest_data, indent=2) + "\n",
        encoding="utf-8",
    )
    (metadata_dir / "tileset.normalized.json").write_text(
        json.dumps(tileset_data, indent=2) + "\n",
        encoding="utf-8",
    )

    summary = {
        "atlas_png_sha256": sha256_image_pixels(images_dir / "tileset.png"),
        "png_sha256": {
            path.name: sha256_image_pixels(path)
            for label, path in artifacts.items()
            if label.startswith("png/")
        },
        "manifest_entry_count": len(manifest_data["entries"]),
        "tileset_entry_count": len(tileset_data["entries"]),
    }
    (baseline_root / "baseline_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def verify_baseline(output_root: Path, baseline_root: Path) -> dict:
    artifacts = collect_current_artifacts(output_root)
    images_dir = baseline_root / "images"
    metadata_dir = baseline_root / "metadata"
    summary_path = baseline_root / "baseline_summary.json"

    expected_paths = [
        images_dir / "tileset.png",
        metadata_dir / "manifest.normalized.json",
        metadata_dir / "tileset.normalized.json",
        summary_path,
    ]
    if any(not path.exists() for path in expected_paths):
        missing = [str(path) for path in expected_paths if not path.exists()]
        raise RuntimeError(f"Missing baseline artifact(s): {', '.join(missing)}")

    failures: list[str] = []

    expected_summary = load_json(summary_path)
    actual_manifest = normalize_manifest(load_json(artifacts["manifest_json"]))
    actual_tileset = normalize_tileset(load_json(artifacts["tileset_json"]))
    expected_manifest = load_json(metadata_dir / "manifest.normalized.json")
    expected_tileset = load_json(metadata_dir / "tileset.normalized.json")

    if actual_manifest != expected_manifest:
        failures.append("Normalized manifest does not match baseline.")
    if actual_tileset != expected_tileset:
        failures.append("Normalized tileset metadata does not match baseline.")

    actual_atlas_hash = sha256_image_pixels(artifacts["atlas_png"])
    if actual_atlas_hash != expected_summary["atlas_png_sha256"]:
        failures.append("Atlas image hash does not match baseline.")

    actual_png_hashes = {
        path.name: sha256_image_pixels(path)
        for label, path in artifacts.items()
        if label.startswith("png/")
    }
    if actual_png_hashes != expected_summary["png_sha256"]:
        failures.append("Rendered PNG hashes do not match baseline.")

    return {
        "ok": not failures,
        "failures": failures,
        "actual": {
            "atlas_png_sha256": actual_atlas_hash,
            "png_sha256": actual_png_hashes,
            "manifest_entry_count": len(actual_manifest["entries"]),
            "tileset_entry_count": len(actual_tileset["entries"]),
        },
    }


def main() -> None:
    arguments = parse_arguments()
    output_root = Path(arguments.output_root).expanduser().resolve()
    baseline_root = Path(arguments.baseline_root).expanduser().resolve()

    if arguments.update:
        result = snapshot_baseline(output_root, baseline_root)
        print(json.dumps({"ok": True, "mode": "update", "baseline_root": str(baseline_root), "summary": result}, indent=2))
        return

    result = verify_baseline(output_root, baseline_root)
    if not result["ok"]:
        print(json.dumps(result, indent=2))
        raise SystemExit(1)

    print(json.dumps({"ok": True, "mode": "verify", "baseline_root": str(baseline_root), **result}, indent=2))


if __name__ == "__main__":
    main()
