#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from pipeline.validation import load_and_validate_manifest


def parse_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(description="Inspect a validated render manifest.")
    argument_parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    return argument_parser.parse_args()


def build_summary(manifest_data: dict) -> dict:
    entries = manifest_data["entries"]
    category_counts = Counter(entry["category"] for entry in entries)
    rotation_counts = Counter(str(entry["rotation"]) for entry in entries)
    source_collection_counts = Counter(entry["source_collection"] for entry in entries)
    height_class_counts = Counter(entry["height_class"] for entry in entries)
    source_objects = sorted({entry["source_object"] for entry in entries})

    return {
        "tileset_name": manifest_data["tileset_name"],
        "entry_count": len(entries),
        "source_object_count": len(source_objects),
        "image_size": {
            "width": entries[0]["width"],
            "height": entries[0]["height"],
        },
        "categories": dict(sorted(category_counts.items())),
        "source_collections": dict(sorted(source_collection_counts.items())),
        "height_classes": dict(sorted(height_class_counts.items())),
        "rotations": dict(sorted(rotation_counts.items(), key=lambda item: int(item[0]))),
        "source_objects": source_objects,
        "first_entry_id": entries[0]["id"],
        "last_entry_id": entries[-1]["id"],
    }


def main() -> None:
    arguments = parse_arguments()
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


if __name__ == "__main__":
    main()
