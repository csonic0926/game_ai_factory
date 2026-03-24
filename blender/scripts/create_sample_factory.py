import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_BLEND_PATH = REPO_ROOT / "examples" / "sample_factory.blend"


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def ensure_collection(collection_name: str, parent: bpy.types.Collection | None = None) -> bpy.types.Collection:
    collection = bpy.data.collections.new(collection_name)
    if parent is None:
        bpy.context.scene.collection.children.link(collection)
    else:
        parent.children.link(collection)
    return collection


def link_object(scene_object: bpy.types.Object, collection: bpy.types.Collection) -> None:
    if scene_object.name not in collection.objects:
        collection.objects.link(scene_object)


def unlink_from_scene_root(scene_object: bpy.types.Object) -> None:
    root_collection = bpy.context.scene.collection
    if scene_object.name in root_collection.objects:
        root_collection.objects.unlink(scene_object)


def assign_rotation_mode(scene_object: bpy.types.Object, rotation_mode: str) -> None:
    scene_object["rotation_mode"] = rotation_mode


def assign_sample_metadata(
    scene_object: bpy.types.Object,
    *,
    anchor_type: str,
    footprint_width: int,
    footprint_height: int,
    height_class: str,
    tags: list[str],
    material_variant: str = "default",
    render_preset: str = "default",
) -> None:
    scene_object["anchor_type"] = anchor_type
    scene_object["footprint_width"] = footprint_width
    scene_object["footprint_height"] = footprint_height
    scene_object["height_class"] = height_class
    scene_object["tags"] = ",".join(tags)
    scene_object["material_variant"] = material_variant
    scene_object["render_preset"] = render_preset


def bake_location_into_mesh_and_zero_origin(scene_object: bpy.types.Object) -> None:
    if scene_object.type != "MESH":
        return
    translation = scene_object.location.copy()
    scene_object.data.transform(Matrix.Translation(translation))
    scene_object.location = (0.0, 0.0, 0.0)


def create_camera(factory_rig: bpy.types.Collection) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new("IsoCamera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 4.0
    camera_object = bpy.data.objects.new("IsoCamera", camera_data)
    camera_object.location = (8.0, -8.0, 8.0)
    camera_object.rotation_euler = (math.radians(54.7356), 0.0, math.radians(45.0))
    link_object(camera_object, factory_rig)
    bpy.context.scene.camera = camera_object
    return camera_object


def create_square_camera(factory_rig: bpy.types.Collection) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new("SquareCamera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 2.5
    camera_object = bpy.data.objects.new("SquareCamera", camera_data)
    camera_object.location = (0.0, 0.0, 8.0)
    camera_object.rotation_euler = (0.0, 0.0, 0.0)
    link_object(camera_object, factory_rig)
    return camera_object


def create_light(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    energy: float,
) -> bpy.types.Object:
    light_data = bpy.data.lights.new(name=name, type="SUN")
    light_data.energy = energy
    light_object = bpy.data.objects.new(name, light_data)
    light_object.location = location
    link_object(light_object, collection)
    return light_object


def create_reference_plane(
    collection: bpy.types.Collection,
    name: str,
    size_x: float,
    size_y: float,
    z: float = 0.0,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    half_x = size_x / 2.0
    half_y = size_y / 2.0
    vertices = [
        (-half_x, -half_y, z),
        (half_x, -half_y, z),
        (half_x, half_y, z),
        (-half_x, half_y, z),
    ]
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    scene_object = bpy.data.objects.new(name, mesh)
    scene_object.hide_render = True
    link_object(scene_object, collection)
    return scene_object


def create_origin_marker(collection: bpy.types.Collection) -> bpy.types.Object:
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0.0, 0.0, 0.0))
    marker = bpy.context.active_object
    marker.name = "OriginMarker"
    marker.hide_render = True
    unlink_from_scene_root(marker)
    link_object(marker, collection)
    return marker


def create_floor_tile(collection: bpy.types.Collection) -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 0.0))
    scene_object = bpy.context.active_object
    scene_object.name = "001_floor_plain"
    assign_rotation_mode(scene_object, "none")
    assign_sample_metadata(
        scene_object,
        anchor_type="tile_center",
        footprint_width=1,
        footprint_height=1,
        height_class="flat",
        tags=["sample", "floor"],
    )
    unlink_from_scene_root(scene_object)
    link_object(scene_object, collection)
    return scene_object


def create_wall_tile(collection: bpy.types.Collection) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.5))
    scene_object = bpy.context.active_object
    scene_object.name = "101_wall_straight"
    scene_object.scale = (0.5, 0.1, 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bake_location_into_mesh_and_zero_origin(scene_object)
    assign_rotation_mode(scene_object, "rotate_90")
    assign_sample_metadata(
        scene_object,
        anchor_type="wall_base",
        footprint_width=1,
        footprint_height=1,
        height_class="tall",
        tags=["sample", "wall"],
    )
    unlink_from_scene_root(scene_object)
    link_object(scene_object, collection)
    return scene_object


def create_stair_tile(collection: bpy.types.Collection) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.125))
    base = bpy.context.active_object
    base.scale = (0.5, 0.5, 0.125)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.ops.mesh.primitive_cube_add(location=(0.0, -0.15, 0.375))
    step = bpy.context.active_object
    step.scale = (0.5, 0.35, 0.125)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.ops.object.select_all(action="DESELECT")
    base.select_set(True)
    step.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()

    scene_object = bpy.context.active_object
    scene_object.name = "201_stair_up"
    bake_location_into_mesh_and_zero_origin(scene_object)
    assign_rotation_mode(scene_object, "rotate_90")
    assign_sample_metadata(
        scene_object,
        anchor_type="tile_center",
        footprint_width=1,
        footprint_height=1,
        height_class="medium",
        tags=["sample", "stair"],
    )
    unlink_from_scene_root(scene_object)
    link_object(scene_object, collection)
    return scene_object


def create_prop(collection: bpy.types.Collection) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.12, depth=0.8, location=(0.0, 0.0, 0.4))
    post = bpy.context.active_object

    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.75))
    top = bpy.context.active_object
    top.scale = (0.2, 0.2, 0.05)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.ops.object.select_all(action="DESELECT")
    post.select_set(True)
    top.select_set(True)
    bpy.context.view_layer.objects.active = post
    bpy.ops.object.join()

    scene_object = bpy.context.active_object
    scene_object.name = "301_prop_switch"
    bake_location_into_mesh_and_zero_origin(scene_object)
    assign_rotation_mode(scene_object, "rotate_360")
    assign_sample_metadata(
        scene_object,
        anchor_type="floor_contact",
        footprint_width=1,
        footprint_height=1,
        height_class="medium",
        tags=["sample", "prop", "switch"],
    )
    unlink_from_scene_root(scene_object)
    link_object(scene_object, collection)
    return scene_object


def save_scene(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))


def build_sample_scene() -> dict:
    reset_scene()

    factory_rig = ensure_collection("Factory_Rig")
    factory_reference = ensure_collection("Factory_Reference")
    export_floor = ensure_collection("Export_Floor")
    export_walls = ensure_collection("Export_Walls")
    export_stairs = ensure_collection("Export_Stairs")
    export_props = ensure_collection("Export_Props")
    ensure_collection("Disabled_Archive")

    create_camera(factory_rig)
    create_square_camera(factory_rig)
    create_light(factory_rig, "KeyLight", (6.0, -6.0, 8.0), 2.0)
    create_light(factory_rig, "FillLight", (-4.0, 4.0, 6.0), 1.0)
    create_light(factory_rig, "RimLight", (-6.0, -6.0, 7.0), 0.5)

    create_reference_plane(factory_reference, "Guide_Tile_1x1", 1.0, 1.0)
    create_reference_plane(factory_reference, "Guide_Tile_2x1", 2.0, 1.0)
    create_reference_plane(factory_reference, "Guide_Height_1", 0.2, 0.2, z=1.0)
    create_origin_marker(factory_reference)

    create_floor_tile(export_floor)
    create_wall_tile(export_walls)
    create_stair_tile(export_stairs)
    create_prop(export_props)

    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    bpy.context.scene.render.film_transparent = True

    save_scene(OUTPUT_BLEND_PATH)

    return {
        "output_path": str(OUTPUT_BLEND_PATH),
        "collections": [
            "Factory_Rig",
            "Factory_Reference",
            "Export_Floor",
            "Export_Walls",
            "Export_Stairs",
            "Export_Props",
            "Disabled_Archive",
        ],
        "export_objects": [
            "001_floor_plain",
            "101_wall_straight",
            "201_stair_up",
            "301_prop_switch",
        ],
        "cameras": [
            "IsoCamera",
            "SquareCamera",
        ],
    }


def main() -> None:
    result = build_sample_scene()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
