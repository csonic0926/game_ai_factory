#!/usr/bin/env python3

import argparse
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from PIL import Image
except ImportError as import_error:
    raise SystemExit("Pillow is required. Install with: python3 -m pip install pillow") from import_error

from pipeline.validation import load_and_validate_manifest


def parse_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(description="Build an atlas from a render manifest.")
    argument_parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    argument_parser.add_argument("--out", required=True, help="Path to atlas png output")
    argument_parser.add_argument("--columns", type=int, default=8, help="Atlas column count")
    argument_parser.add_argument("--padding", type=int, default=0, help="Padding in pixels between cells")
    return argument_parser.parse_args()


def build_atlas(manifest_data: dict, output_path: Path, columns: int, padding: int) -> Path:
    entries = manifest_data.get("entries", [])
    if not entries:
        raise RuntimeError("Manifest has no entries.")

    first_entry = entries[0]
    tile_width = int(first_entry["width"])
    tile_height = int(first_entry["height"])
    rows = int(math.ceil(len(entries) / float(columns)))

    atlas_width = columns * tile_width + max(columns - 1, 0) * padding
    atlas_height = rows * tile_height + max(rows - 1, 0) * padding
    atlas_image = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))

    atlas_entries: list[dict] = []

    for entry_index, entry in enumerate(entries):
        column_index = entry_index % columns
        row_index = entry_index // columns
        destination_x = column_index * (tile_width + padding)
        destination_y = row_index * (tile_height + padding)

        source_image = Image.open(entry["file"]).convert("RGBA")
        atlas_image.paste(source_image, (destination_x, destination_y))

        atlas_entries.append(
            {
                **entry,
                "atlas_index": entry_index,
                "atlas_column": column_index,
                "atlas_row": row_index,
                "atlas_x": destination_x,
                "atlas_y": destination_y,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    atlas_image.save(output_path)

    tileset_metadata = {
        "tileset_name": manifest_data.get("tileset_name", "tileset"),
        "atlas_path": str(output_path),
        "tile_width": tile_width,
        "tile_height": tile_height,
        "columns": columns,
        "rows": rows,
        "padding": padding,
        "entries": atlas_entries,
    }

    metadata_path = output_path.parent.parent / "metadata" / "tileset.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(tileset_metadata, metadata_file, indent=2)

    return metadata_path


def main() -> None:
    arguments = parse_arguments()
    manifest_path = Path(arguments.manifest).expanduser().resolve()
    output_path = Path(arguments.out).expanduser().resolve()

    if arguments.columns <= 0:
        raise SystemExit("--columns must be a positive integer")
    if arguments.padding < 0:
        raise SystemExit("--padding must be zero or greater")

    manifest_data, warnings = load_and_validate_manifest(manifest_path, require_files=True)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    metadata_path = build_atlas(manifest_data, output_path, arguments.columns, arguments.padding)

    print(
        json.dumps(
            {
                "atlas_path": str(output_path),
                "metadata_path": str(metadata_path),
                "entry_count": len(manifest_data.get("entries", [])),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
