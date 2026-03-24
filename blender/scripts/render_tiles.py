import bpy
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.validation import (
    ValidationError,
    load_and_validate_config,
    validate_object_name,
    validate_rotation_mode,
)


def get_cli_argument(argument_name: str) -> str:
    if "--" not in sys.argv:
        return ""

    custom_arguments = sys.argv[sys.argv.index("--") + 1 :]
    prefix = f"--{argument_name}="

    for argument_value in custom_arguments:
        if argument_value.startswith(prefix):
            return argument_value[len(prefix) :]

    return ""


def load_config() -> dict:
    config_path = get_cli_argument("config")
    if not config_path:
        raise RuntimeError("Missing --config=/absolute/or/relative/path.json")

    resolved_path = Path(config_path).expanduser().resolve()
    config_data, warnings = load_and_validate_config(resolved_path)
    for warning in warnings:
        print(f"WARNING: {warning}")
    return config_data


def ensure_directory(directory_path: Path) -> None:
    directory_path.mkdir(parents=True, exist_ok=True)


def get_rotation_degrees(rotation_mode: str) -> list[int]:
    if rotation_mode == "rotate_360":
        return [0, 90, 180, 270]
    if rotation_mode == "rotate_90":
        return [0, 90]
    return [0]


def normalize_tags(raw_tags: object) -> list[str]:
    if raw_tags is None:
        return []
    if isinstance(raw_tags, str):
        return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    if isinstance(raw_tags, (list, tuple)):
        normalized_tags = []
        for tag in raw_tags:
            tag_text = str(tag).strip()
            if tag_text:
                normalized_tags.append(tag_text)
        return normalized_tags
    return [str(raw_tags).strip()] if str(raw_tags).strip() else []


def default_anchor_type(category: str) -> str:
    if category == "floor":
        return "tile_center"
    if category == "wall":
        return "wall_base"
    if category == "prop":
        return "floor_contact"
    return "tile_center"


def default_height_class(category: str) -> str:
    if category == "floor":
        return "flat"
    if category == "wall":
        return "tall"
    if category == "stair":
        return "medium"
    return "medium"


def default_tile_shape(projection_mode: str) -> str:
    if projection_mode == "square":
        return "square"
    return "isometric"


def build_entry_metadata(export_object: bpy.types.Object, source_collection: str, projection_mode: str) -> dict:
    category = infer_category_from_name(export_object.name)
    return {
        "source_object": export_object.name,
        "category": category,
        "projection_mode": projection_mode,
        "tile_shape": default_tile_shape(projection_mode),
        "render_profile": str(export_object.get("render_profile", "default")),
        "anchor_type": str(export_object.get("anchor_type", default_anchor_type(category))),
        "footprint_width": int(export_object.get("footprint_width", 1)),
        "footprint_height": int(export_object.get("footprint_height", 1)),
        "height_class": str(export_object.get("height_class", default_height_class(category))),
        "tags": normalize_tags(export_object.get("tags", [])),
        "source_collection": source_collection,
        "material_variant": str(export_object.get("material_variant", "default")),
        "render_preset": str(export_object.get("render_preset", "default")),
    }


def get_sorted_export_objects(collection_names: list[str]) -> list[dict]:
    export_objects: list[dict] = []
    seen_object_names: set[str] = set()

    for collection_name in collection_names:
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            raise ValidationError(f'Export collection "{collection_name}" was not found.')

        for collection_object in collection.objects:
            if collection_object.type != "MESH":
                continue
            if collection_object.hide_render:
                continue
            if collection_object.name in seen_object_names:
                raise ValidationError(f'Duplicate export object name "{collection_object.name}".')
            validate_object_name(collection_object.name)
            export_objects.append(
                {
                    "object": collection_object,
                    "source_collection": collection_name,
                }
            )
            seen_object_names.add(collection_object.name)

    export_objects.sort(key=lambda item: item["object"].name)
    if not export_objects:
        raise ValidationError("No eligible export objects were found in the configured export collections.")
    return export_objects


def find_camera(camera_name: str) -> bpy.types.Object:
    camera_object = bpy.data.objects.get(camera_name)
    if camera_object is None or camera_object.type != "CAMERA":
        raise RuntimeError(f'Camera "{camera_name}" was not found.')
    return camera_object


def configure_render(scene: bpy.types.Scene, width: int, height: int) -> None:
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100


def render_object_variants(config: dict) -> dict:
    scene = bpy.context.scene
    projection_mode = str(config.get("projection_mode", "isometric")).strip().lower()
    render_profile = str(config.get("render_profile", "default")).strip() or "default"
    output_root = Path(config["output_root"]).expanduser().resolve()
    png_output_directory = output_root / "png"
    metadata_output_directory = output_root / "metadata"

    ensure_directory(png_output_directory)
    ensure_directory(metadata_output_directory)

    render_resolution = config.get("render_resolution", {})
    configure_render(
        scene,
        int(render_resolution.get("width", 256)),
        int(render_resolution.get("height", 256)),
    )

    scene.camera = find_camera(config["camera_name"])
    export_object_records = get_sorted_export_objects(config.get("export_collections", []))

    original_rotations: dict[str, tuple[float, float, float]] = {}
    for export_record in export_object_records:
        export_object = export_record["object"]
        original_rotations[export_object.name] = tuple(export_object.rotation_euler)

    manifest_entries: list[dict] = []

    for export_record in export_object_records:
        export_object = export_record["object"]
        source_collection = export_record["source_collection"]
        rotation_mode = export_object.get("rotation_mode", config.get("default_rotation_mode", "none"))
        rotation_mode = str(rotation_mode)
        validate_rotation_mode(rotation_mode, export_object.name)
        rotation_degrees_list = get_rotation_degrees(rotation_mode)
        entry_metadata = build_entry_metadata(export_object, source_collection, projection_mode)
        entry_metadata["render_profile"] = render_profile

        for rotation_degrees in rotation_degrees_list:
            export_object.rotation_euler[2] = math.radians(rotation_degrees)

            output_name = f"{export_object.name}_rot{rotation_degrees}.png"
            output_path = png_output_directory / output_name
            scene.render.filepath = str(output_path)
            bpy.ops.render.render(write_still=True)

            manifest_entries.append(
                {
                    "id": f"{export_object.name}_rot{rotation_degrees}",
                    "name": export_object.name,
                    **entry_metadata,
                    "rotation": rotation_degrees,
                    "file": str(output_path),
                    "file_name": output_name,
                    "width": scene.render.resolution_x,
                    "height": scene.render.resolution_y,
                }
            )

    for export_record in export_object_records:
        export_object = export_record["object"]
        original_rotation = original_rotations[export_object.name]
        export_object.rotation_euler = original_rotation

    manifest_data = {
        "tileset_name": config.get("tileset_name", "tileset"),
        "projection_mode": projection_mode,
        "render_profile": render_profile,
        "output_mode": str(config.get("output_mode", "png")),
        "entries": manifest_entries,
    }

    manifest_path = metadata_output_directory / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as manifest_file:
        json.dump(manifest_data, manifest_file, indent=2)

    return {
        "manifest_path": str(manifest_path),
        "entry_count": len(manifest_entries),
    }


def infer_category_from_name(object_name: str) -> str:
    lowered_name = object_name.lower()

    if "_floor_" in lowered_name or lowered_name.startswith("floor_"):
        return "floor"
    if "_wall_" in lowered_name or lowered_name.startswith("wall_"):
        return "wall"
    if "_stair_" in lowered_name or lowered_name.startswith("stair_"):
        return "stair"
    if "_prop_" in lowered_name or lowered_name.startswith("prop_"):
        return "prop"

    split_name = lowered_name.split("_")
    if len(split_name) >= 2:
        return split_name[1]

    return "unknown"


def main() -> None:
    config = load_config()
    result = render_object_variants(config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
