import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.validation import (
    ValidationError,
    load_and_validate_config,
    validate_object_name,
    validate_rotation_mode,
)

REQUIRED_COLLECTIONS = {
    "Factory_Rig",
    "Factory_Reference",
    "Export_Floor",
    "Export_Walls",
    "Export_Stairs",
    "Export_Props",
    "Disabled_Archive",
}
REQUIRED_RIG_OBJECTS = {
    "IsoCamera": "CAMERA",
    "SquareCamera": "CAMERA",
    "KeyLight": "LIGHT",
    "FillLight": "LIGHT",
}
OPTIONAL_RIG_OBJECTS = {
    "RimLight": "LIGHT",
}
REQUIRED_REFERENCE_OBJECTS = {
    "Guide_Tile_1x1",
    "Guide_Tile_2x1",
    "Guide_Height_1",
    "OriginMarker",
}
SAMPLE_EXPORT_OBJECTS = {
    "Export_Floor": {"001_floor_plain": "none"},
    "Export_Walls": {"101_wall_straight": "rotate_90"},
    "Export_Stairs": {"201_stair_up": "rotate_90"},
    "Export_Props": {"301_prop_switch": "rotate_360"},
}
GROUND_EPSILON = 1e-4
ORIGIN_EPSILON = 1e-4


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
        raise ValidationError("Missing --config=/absolute/or/relative/path.json")

    resolved_path = Path(config_path).expanduser().resolve()
    config_data, warnings = load_and_validate_config(resolved_path)
    for warning in warnings:
        print(f"WARNING: {warning}")
    return config_data


def find_collection(collection_name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        raise ValidationError(f'Required collection "{collection_name}" was not found.')
    return collection


def find_object(object_name: str, expected_type: str | None = None) -> bpy.types.Object:
    scene_object = bpy.data.objects.get(object_name)
    if scene_object is None:
        raise ValidationError(f'Required object "{object_name}" was not found.')
    if expected_type and scene_object.type != expected_type:
        raise ValidationError(
            f'Required object "{object_name}" must be type {expected_type}, found {scene_object.type}.'
        )
    return scene_object


def object_min_world_z(scene_object: bpy.types.Object) -> float:
    world_corners = [scene_object.matrix_world @ Vector(corner) for corner in scene_object.bound_box]
    return min(corner.z for corner in world_corners)


def validate_required_collections() -> None:
    for collection_name in sorted(REQUIRED_COLLECTIONS):
        find_collection(collection_name)


def validate_camera(camera_name: str) -> None:
    camera_object = find_object(camera_name, "CAMERA")
    if camera_object.data.type != "ORTHO":
        raise ValidationError(f'Camera "{camera_name}" must use Orthographic projection.')


def validate_rig_objects() -> None:
    for object_name, expected_type in REQUIRED_RIG_OBJECTS.items():
        find_object(object_name, expected_type)

    for object_name, expected_type in OPTIONAL_RIG_OBJECTS.items():
        scene_object = bpy.data.objects.get(object_name)
        if scene_object is not None and scene_object.type != expected_type:
            raise ValidationError(
                f'Optional rig object "{object_name}" must be type {expected_type}, found {scene_object.type}.'
            )


def validate_reference_objects() -> None:
    reference_collection = find_collection("Factory_Reference")
    collection_object_names = {scene_object.name for scene_object in reference_collection.objects}

    for object_name in sorted(REQUIRED_REFERENCE_OBJECTS):
        if object_name not in collection_object_names:
            raise ValidationError(f'Reference object "{object_name}" is missing from Factory_Reference.')

    for scene_object in reference_collection.objects:
        if not scene_object.hide_render:
            raise ValidationError(
                f'Reference object "{scene_object.name}" must have hide_render enabled.'
            )


def validate_export_object(scene_object: bpy.types.Object, default_rotation_mode: str) -> dict:
    if scene_object.type != "MESH":
        raise ValidationError(
            f'Export object "{scene_object.name}" must be type MESH, found {scene_object.type}.'
        )
    if scene_object.hide_render:
        raise ValidationError(f'Export object "{scene_object.name}" must not have hide_render enabled.')

    validate_object_name(scene_object.name)

    origin = scene_object.matrix_world.translation
    if (
        math.fabs(origin.x) > ORIGIN_EPSILON
        or math.fabs(origin.y) > ORIGIN_EPSILON
        or math.fabs(origin.z) > ORIGIN_EPSILON
    ):
        raise ValidationError(
            f'Export object "{scene_object.name}" origin must be at world origin; '
            f"found ({origin.x:.6f}, {origin.y:.6f}, {origin.z:.6f})."
        )

    minimum_z = object_min_world_z(scene_object)
    if math.fabs(minimum_z) > GROUND_EPSILON:
        raise ValidationError(
            f'Export object "{scene_object.name}" must sit on Z=0; minimum bound z is {minimum_z:.6f}.'
        )

    rotation_mode = str(scene_object.get("rotation_mode", default_rotation_mode))
    validate_rotation_mode(rotation_mode, scene_object.name)

    return {
        "name": scene_object.name,
        "rotation_mode": rotation_mode,
    }


def validate_export_collections(config: dict) -> dict:
    export_summary: dict[str, list[dict]] = {}
    seen_object_names: set[str] = set()

    for collection_name in config["export_collections"]:
        collection = find_collection(collection_name)
        export_summary[collection_name] = []

        for scene_object in sorted(collection.objects, key=lambda item: item.name):
            if scene_object.name in seen_object_names:
                raise ValidationError(f'Duplicate export object name "{scene_object.name}".')
            export_summary[collection_name].append(
                validate_export_object(scene_object, config["default_rotation_mode"])
            )
            seen_object_names.add(scene_object.name)

        if not export_summary[collection_name]:
            raise ValidationError(f'Export collection "{collection_name}" has no export objects.')

    return export_summary


def validate_sample_scene_contract(export_summary: dict[str, list[dict]]) -> None:
    for collection_name, expected_objects in SAMPLE_EXPORT_OBJECTS.items():
        actual_objects = {item["name"]: item["rotation_mode"] for item in export_summary.get(collection_name, [])}
        if set(actual_objects.keys()) != set(expected_objects.keys()):
            raise ValidationError(
                f'Sample scene collection "{collection_name}" must contain exactly: '
                f'{", ".join(sorted(expected_objects.keys()))}.'
            )

        for object_name, expected_rotation_mode in expected_objects.items():
            actual_rotation_mode = actual_objects[object_name]
            if actual_rotation_mode != expected_rotation_mode:
                raise ValidationError(
                    f'Sample scene object "{object_name}" must use rotation_mode='
                    f'"{expected_rotation_mode}", found "{actual_rotation_mode}".'
                )


def validate_scene(config: dict, sample_scene: bool) -> dict:
    validate_required_collections()
    validate_camera(config["camera_name"])
    validate_rig_objects()
    validate_reference_objects()
    export_summary = validate_export_collections(config)

    if sample_scene:
        validate_sample_scene_contract(export_summary)

    return {
        "camera_name": config["camera_name"],
        "export_collections": export_summary,
        "sample_scene_checked": sample_scene,
    }


def main() -> None:
    config = load_config()
    sample_scene = get_cli_argument("sample-scene").lower() in {"1", "true", "yes"}
    result = validate_scene(config, sample_scene=sample_scene)
    print(json.dumps({"ok": True, "result": result}, indent=2))


if __name__ == "__main__":
    main()
