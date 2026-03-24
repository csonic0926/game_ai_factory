#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.validation import (
    ValidationError,
    load_and_validate_config,
    load_and_validate_manifest,
)


def parse_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(description="Validate isometric_tile_factory config or manifest files.")
    argument_parser.add_argument("--config", help="Path to config JSON")
    argument_parser.add_argument("--manifest", help="Path to manifest JSON")
    argument_parser.add_argument(
        "--skip-file-checks",
        action="store_true",
        help="Skip manifest file existence checks",
    )
    return argument_parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if not arguments.config and not arguments.manifest:
        raise SystemExit("Provide at least one of: --config, --manifest")

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
                "normalized": manifest_data,
            }
    except ValidationError as validation_error:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(validation_error),
                },
                indent=2,
            )
        )
        raise SystemExit(1) from validation_error

    print(json.dumps({"ok": True, "results": results}, indent=2))


if __name__ == "__main__":
    main()
