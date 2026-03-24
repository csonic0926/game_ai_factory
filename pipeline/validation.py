#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from pathlib import Path

VALID_ROTATION_MODES = {"none", "rotate_90", "rotate_360"}
VALID_PROJECTION_MODES = {"isometric", "square"}
VALID_OUTPUT_MODES = {"png", "atlas", "both"}
OBJECT_NAME_PATTERN = re.compile(r"^\d{3}_[a-z0-9]+_[a-z0-9_]+$")
CONFIG_REQUIRED_KEYS = {
    "tileset_name",
    "output_root",
    "export_collections",
    "camera_name",
}
CONFIG_OPTIONAL_KEYS = {
    "projection_mode",
    "output_mode",
    "render_profile",
    "render_profiles",
    "default_rotation_mode",
    "render_resolution",
    "atlas",
}
CONFIG_ALLOWED_KEYS = CONFIG_REQUIRED_KEYS | CONFIG_OPTIONAL_KEYS
MANIFEST_ENTRY_REQUIRED_KEYS = {
    "id",
    "name",
    "source_object",
    "category",
    "projection_mode",
    "tile_shape",
    "render_profile",
    "anchor_type",
    "footprint_width",
    "footprint_height",
    "height_class",
    "tags",
    "source_collection",
    "material_variant",
    "render_preset",
    "rotation",
    "file",
    "file_name",
    "width",
    "height",
}


class ValidationError(RuntimeError):
    pass


def load_json_file(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as input_file:
        return json.load(input_file)


def validate_config_data(config_data: dict) -> tuple[dict, list[str]]:
    if not isinstance(config_data, dict):
        raise ValidationError("Config must be a JSON object.")

    warnings: list[str] = []

    missing_keys = sorted(CONFIG_REQUIRED_KEYS - set(config_data.keys()))
    if missing_keys:
        raise ValidationError(f"Config is missing required key(s): {', '.join(missing_keys)}")

    unknown_keys = sorted(set(config_data.keys()) - CONFIG_ALLOWED_KEYS)
    for unknown_key in unknown_keys:
        warnings.append(f'Unknown top-level config key: "{unknown_key}"')

    export_collections = config_data["export_collections"]
    if not isinstance(export_collections, list) or not export_collections:
        raise ValidationError("Config 'export_collections' must be a non-empty array of strings.")
    if any(not isinstance(item, str) or not item.strip() for item in export_collections):
        raise ValidationError("Every 'export_collections' entry must be a non-empty string.")

    if not isinstance(config_data["tileset_name"], str) or not config_data["tileset_name"].strip():
        raise ValidationError("Config 'tileset_name' must be a non-empty string.")

    if not isinstance(config_data["output_root"], str) or not config_data["output_root"].strip():
        raise ValidationError("Config 'output_root' must be a non-empty string.")

    if not isinstance(config_data["camera_name"], str) or not config_data["camera_name"].strip():
        raise ValidationError("Config 'camera_name' must be a non-empty string.")

    projection_mode = str(config_data.get("projection_mode", "isometric")).strip().lower()
    if projection_mode not in VALID_PROJECTION_MODES:
        raise ValidationError(
            f"Unsupported projection_mode '{projection_mode}'. "
            f"Expected one of: {', '.join(sorted(VALID_PROJECTION_MODES))}"
        )

    output_mode = str(config_data.get("output_mode", "png")).strip().lower()
    if output_mode not in VALID_OUTPUT_MODES:
        raise ValidationError(
            f"Unsupported output_mode '{output_mode}'. "
            f"Expected one of: {', '.join(sorted(VALID_OUTPUT_MODES))}"
        )

    default_rotation_mode = str(config_data.get("default_rotation_mode", "none"))
    if default_rotation_mode not in VALID_ROTATION_MODES:
        raise ValidationError(
            f"Unsupported default_rotation_mode '{default_rotation_mode}'. "
            f"Expected one of: {', '.join(sorted(VALID_ROTATION_MODES))}"
        )

    render_resolution = config_data.get("render_resolution", {})
    if not isinstance(render_resolution, dict):
        raise ValidationError("Config 'render_resolution' must be an object.")
    render_width = int(render_resolution.get("width", 256))
    render_height = int(render_resolution.get("height", 256))
    if render_width <= 0 or render_height <= 0:
        raise ValidationError("Render resolution width and height must be positive integers.")

    atlas = config_data.get("atlas", {})
    if not isinstance(atlas, dict):
        raise ValidationError("Config 'atlas' must be an object.")
    atlas_columns = int(atlas.get("columns", 8))
    atlas_padding = int(atlas.get("padding", 0))
    if atlas_columns <= 0:
        raise ValidationError("Atlas columns must be a positive integer.")
    if atlas_padding < 0:
        raise ValidationError("Atlas padding must be zero or greater.")

    render_profiles = config_data.get("render_profiles", {})
    if not isinstance(render_profiles, dict):
        raise ValidationError("Config 'render_profiles' must be an object.")

    selected_render_profile = str(config_data.get("render_profile", "default")).strip()
    if not selected_render_profile:
        raise ValidationError("Config 'render_profile' must be a non-empty string when provided.")

    normalized_render_profiles: dict[str, dict] = {}
    for profile_name, profile_data in render_profiles.items():
        normalized_name = str(profile_name).strip()
        if not normalized_name:
            raise ValidationError("Config 'render_profiles' cannot contain an empty profile name.")
        if not isinstance(profile_data, dict):
            raise ValidationError(f'Render profile "{normalized_name}" must be an object.')

        profile_camera_name = str(profile_data.get("camera_name", config_data["camera_name"])).strip()
        if not profile_camera_name:
            raise ValidationError(f'Render profile "{normalized_name}" has an empty camera_name.')

        profile_projection_mode = str(profile_data.get("projection_mode", projection_mode)).strip().lower()
        if profile_projection_mode not in VALID_PROJECTION_MODES:
            raise ValidationError(
                f'Render profile "{normalized_name}" has unsupported projection_mode "{profile_projection_mode}".'
            )

        profile_render_resolution = profile_data.get("render_resolution", render_resolution)
        if not isinstance(profile_render_resolution, dict):
            raise ValidationError(f'Render profile "{normalized_name}" render_resolution must be an object.')
        profile_render_width = int(profile_render_resolution.get("width", render_width))
        profile_render_height = int(profile_render_resolution.get("height", render_height))
        if profile_render_width <= 0 or profile_render_height <= 0:
            raise ValidationError(
                f'Render profile "{normalized_name}" width/height must be positive integers.'
            )

        normalized_render_profiles[normalized_name] = {
            "camera_name": profile_camera_name,
            "projection_mode": profile_projection_mode,
            "render_resolution": {
                "width": profile_render_width,
                "height": profile_render_height,
            },
        }

    if selected_render_profile != "default" and selected_render_profile not in normalized_render_profiles:
        raise ValidationError(
            f'Config render_profile "{selected_render_profile}" was not found in render_profiles.'
        )

    active_render_profile = normalized_render_profiles.get(
        selected_render_profile,
        {
            "camera_name": config_data["camera_name"].strip(),
            "projection_mode": projection_mode,
            "render_resolution": {
                "width": render_width,
                "height": render_height,
            },
        },
    )

    normalized_config = {
        "tileset_name": config_data["tileset_name"].strip(),
        "output_root": config_data["output_root"].strip(),
        "export_collections": [item.strip() for item in export_collections],
        "camera_name": active_render_profile["camera_name"],
        "projection_mode": active_render_profile["projection_mode"],
        "output_mode": output_mode,
        "render_profile": selected_render_profile,
        "render_profiles": normalized_render_profiles,
        "default_rotation_mode": default_rotation_mode,
        "render_resolution": active_render_profile["render_resolution"],
        "atlas": {
            "columns": atlas_columns,
            "padding": atlas_padding,
        },
    }

    return normalized_config, warnings


def load_and_validate_config(config_path: Path) -> tuple[dict, list[str]]:
    return validate_config_data(load_json_file(config_path))


def validate_object_name(object_name: str) -> None:
    if not OBJECT_NAME_PATTERN.match(object_name):
        raise ValidationError(
            f'Invalid export object name "{object_name}". '
            'Expected format "<order>_<category>_<name>" with a zero-padded 3-digit prefix.'
        )


def validate_rotation_mode(rotation_mode: str, object_name: str | None = None) -> None:
    if rotation_mode not in VALID_ROTATION_MODES:
        label = f' on "{object_name}"' if object_name else ""
        raise ValidationError(
            f"Unsupported rotation_mode '{rotation_mode}'{label}. "
            f"Expected one of: {', '.join(sorted(VALID_ROTATION_MODES))}"
        )


def validate_manifest_data(manifest_data: dict, *, require_files: bool = True) -> tuple[dict, list[str]]:
    if not isinstance(manifest_data, dict):
        raise ValidationError("Manifest must be a JSON object.")

    warnings: list[str] = []
    tileset_name = manifest_data.get("tileset_name")
    if not isinstance(tileset_name, str) or not tileset_name.strip():
        raise ValidationError("Manifest 'tileset_name' must be a non-empty string.")

    entries = manifest_data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValidationError("Manifest must contain a non-empty 'entries' array.")

    normalized_entries: list[dict] = []
    seen_ids: set[str] = set()
    expected_size: tuple[int, int] | None = None

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValidationError(f"Manifest entry at index {index} must be an object.")

        missing_keys = sorted(MANIFEST_ENTRY_REQUIRED_KEYS - set(entry.keys()))
        if missing_keys:
            raise ValidationError(
                f"Manifest entry at index {index} is missing required key(s): {', '.join(missing_keys)}"
            )

        entry_id = str(entry["id"])
        if entry_id in seen_ids:
            raise ValidationError(f'Duplicate manifest entry id "{entry_id}".')
        seen_ids.add(entry_id)

        object_name = str(entry["name"])
        validate_object_name(object_name)

        width = int(entry["width"])
        height = int(entry["height"])
        if width <= 0 or height <= 0:
            raise ValidationError(f'Manifest entry "{entry_id}" has non-positive width/height.')

        if expected_size is None:
            expected_size = (width, height)
        elif expected_size != (width, height):
            raise ValidationError(
                f'Manifest entry "{entry_id}" size {width}x{height} does not match '
                f"the first entry size {expected_size[0]}x{expected_size[1]}."
            )

        rotation = int(entry["rotation"])
        if rotation not in {0, 90, 180, 270}:
            raise ValidationError(f'Manifest entry "{entry_id}" has unsupported rotation {rotation}.')

        anchor_type = str(entry["anchor_type"]).strip()
        if not anchor_type:
            raise ValidationError(f'Manifest entry "{entry_id}" has an empty anchor_type.')

        projection_mode = str(entry["projection_mode"]).strip().lower()
        if projection_mode not in VALID_PROJECTION_MODES:
            raise ValidationError(
                f'Manifest entry "{entry_id}" has unsupported projection_mode "{projection_mode}".'
            )

        tile_shape = str(entry["tile_shape"]).strip().lower()
        if tile_shape not in VALID_PROJECTION_MODES:
            raise ValidationError(f'Manifest entry "{entry_id}" has unsupported tile_shape "{tile_shape}".')

        render_profile = str(entry["render_profile"]).strip()
        if not render_profile:
            raise ValidationError(f'Manifest entry "{entry_id}" has an empty render_profile.')

        footprint_width = int(entry["footprint_width"])
        footprint_height = int(entry["footprint_height"])
        if footprint_width <= 0 or footprint_height <= 0:
            raise ValidationError(
                f'Manifest entry "{entry_id}" has non-positive footprint dimensions '
                f"{footprint_width}x{footprint_height}."
            )

        height_class = str(entry["height_class"]).strip()
        if not height_class:
            raise ValidationError(f'Manifest entry "{entry_id}" has an empty height_class.')

        tags = entry["tags"]
        if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
            raise ValidationError(f'Manifest entry "{entry_id}" must provide tags as an array of non-empty strings.')

        source_collection = str(entry["source_collection"]).strip()
        if not source_collection:
            raise ValidationError(f'Manifest entry "{entry_id}" has an empty source_collection.')

        material_variant = str(entry["material_variant"]).strip()
        if not material_variant:
            raise ValidationError(f'Manifest entry "{entry_id}" has an empty material_variant.')

        render_preset = str(entry["render_preset"]).strip()
        if not render_preset:
            raise ValidationError(f'Manifest entry "{entry_id}" has an empty render_preset.')

        file_path = Path(str(entry["file"])).expanduser()
        if require_files and not file_path.exists():
            raise ValidationError(f'Manifest entry "{entry_id}" file does not exist: {file_path}')

        normalized_entries.append(
            {
                "id": entry_id,
                "name": object_name,
                "source_object": str(entry["source_object"]),
                "category": str(entry["category"]),
                "projection_mode": projection_mode,
                "tile_shape": tile_shape,
                "render_profile": render_profile,
                "anchor_type": anchor_type,
                "footprint_width": footprint_width,
                "footprint_height": footprint_height,
                "height_class": height_class,
                "tags": [tag.strip() for tag in tags],
                "source_collection": source_collection,
                "material_variant": material_variant,
                "render_preset": render_preset,
                "rotation": rotation,
                "file": str(file_path),
                "file_name": str(entry["file_name"]),
                "width": width,
                "height": height,
            }
        )

    normalized_manifest = {
        "tileset_name": tileset_name.strip(),
        "entries": normalized_entries,
    }
    for optional_key in ("projection_mode", "render_profile", "output_mode"):
        if optional_key in manifest_data:
            normalized_manifest[optional_key] = manifest_data[optional_key]

    return normalized_manifest, warnings


def load_and_validate_manifest(manifest_path: Path, *, require_files: bool = True) -> tuple[dict, list[str]]:
    return validate_manifest_data(load_json_file(manifest_path), require_files=require_files)
