import json
import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.validation import ValidationError, load_and_validate_config

SLOT_COLORS = {
    "base_color": "sRGB",
    "normal": "Non-Color",
    "orm": "Non-Color",
    "emissive": "sRGB",
}


def pack_directory(cache_root: Path, source_object: str, variant: str) -> Path:
    return cache_root / source_object / variant


def pack_path(cache_root: Path, source_object: str, variant: str) -> Path:
    return pack_directory(cache_root, source_object, variant) / "pack.json"


def textures_directory(cache_root: Path, source_object: str, variant: str) -> Path:
    return pack_directory(cache_root, source_object, variant) / "textures"


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
    config_data, warnings = load_and_validate_config(Path(config_path).expanduser().resolve())
    for warning in warnings:
        print(f"WARNING: {warning}")
    return config_data


def ensure_material(export_object: bpy.types.Object, variant: str) -> bpy.types.Material:
    material_name = f"{export_object.name}__{variant}"
    material = bpy.data.materials.get(material_name)
    if material is None:
        material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    if export_object.data.materials:
        export_object.data.materials[0] = material
    else:
        export_object.data.materials.append(material)
    return material


def reset_node_tree(material: bpy.types.Material) -> tuple[bpy.types.NodeTree, bpy.types.Node, bpy.types.Node]:
    node_tree = material.node_tree
    for node in list(node_tree.nodes):
        node_tree.nodes.remove(node)
    output_node = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (900, 200)
    bsdf_node = node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf_node.location = (600, 200)
    node_tree.links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])
    return node_tree, bsdf_node, output_node


def load_image(image_path: Path, slot_name: str) -> bpy.types.Image:
    image = bpy.data.images.load(str(image_path), check_existing=True)
    image.colorspace_settings.name = SLOT_COLORS.get(slot_name, "sRGB")
    return image


def bind_slot(node_tree: bpy.types.NodeTree, bsdf_node: bpy.types.Node, slot_name: str, image_path: Path, y: int) -> None:
    image_node = node_tree.nodes.new(type="ShaderNodeTexImage")
    image_node.location = (0, y)
    image_node.label = slot_name
    image_node.image = load_image(image_path, slot_name)

    if slot_name == "base_color":
        node_tree.links.new(image_node.outputs["Color"], bsdf_node.inputs["Base Color"])
        if "Alpha" in image_node.outputs and "Alpha" in bsdf_node.inputs:
            node_tree.links.new(image_node.outputs["Alpha"], bsdf_node.inputs["Alpha"])
        return

    if slot_name == "normal":
        normal_map = node_tree.nodes.new(type="ShaderNodeNormalMap")
        normal_map.location = (300, y)
        node_tree.links.new(image_node.outputs["Color"], normal_map.inputs["Color"])
        node_tree.links.new(normal_map.outputs["Normal"], bsdf_node.inputs["Normal"])
        return

    if slot_name == "orm":
        separate = node_tree.nodes.new(type="ShaderNodeSeparateColor")
        separate.location = (300, y)
        node_tree.links.new(image_node.outputs["Color"], separate.inputs["Color"])
        node_tree.links.new(separate.outputs["Green"], bsdf_node.inputs["Roughness"])
        node_tree.links.new(separate.outputs["Blue"], bsdf_node.inputs["Metallic"])
        return

    if slot_name == "emissive":
        target_name = "Emission Color" if "Emission Color" in bsdf_node.inputs else "Emission"
        node_tree.links.new(image_node.outputs["Color"], bsdf_node.inputs[target_name])
        if "Emission Strength" in bsdf_node.inputs:
            bsdf_node.inputs["Emission Strength"].default_value = 1.0


def eligible_export_objects(collection_names: list[str]) -> list[bpy.types.Object]:
    seen = set()
    objects = []
    for collection_name in collection_names:
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            raise ValidationError(f'Export collection "{collection_name}" was not found.')
        for scene_object in sorted(collection.objects, key=lambda item: item.name):
            if scene_object.type != "MESH":
                continue
            if scene_object.name in seen:
                continue
            seen.add(scene_object.name)
            objects.append(scene_object)
    return objects


def bind_ai_textures(config: dict, cache_root: Path, variant: str) -> dict:
    bound_objects = []
    export_objects = eligible_export_objects(config["export_collections"])

    for export_object in export_objects:
        source_object = export_object.name
        pack_file = pack_path(cache_root, source_object, variant)
        if not pack_file.exists():
            continue
        pack_data = json.loads(pack_file.read_text(encoding="utf-8"))
        if pack_data.get("status") != "ready":
            continue

        texture_dir = textures_directory(cache_root, source_object, variant)
        present_slots = []
        material = ensure_material(export_object, variant)
        node_tree, bsdf_node, _ = reset_node_tree(material)
        y = 400

        for slot_name, slot_info in pack_data.get("slots", {}).items():
            file_value = slot_info.get("file")
            if not slot_info.get("present") or not file_value:
                continue
            image_path = pack_file.parent / file_value
            if not image_path.exists():
                continue
            bind_slot(node_tree, bsdf_node, slot_name, image_path, y)
            y -= 250
            present_slots.append(slot_name)

        if present_slots:
            bound_objects.append(
                {
                    "source_object": source_object,
                    "material": material.name,
                    "slots": present_slots,
                }
            )

    bpy.ops.wm.save_mainfile()
    return {
        "cache_root": str(cache_root),
        "variant": variant,
        "bound_count": len(bound_objects),
        "objects": bound_objects,
    }


def main() -> None:
    config = load_config()
    cache_root = Path(get_cli_argument("cache-root") or "texture_cache").expanduser().resolve()
    variant = get_cli_argument("variant") or "ai_v1"
    result = bind_ai_textures(config, cache_root, variant)
    print(json.dumps({"ok": True, "result": result}, indent=2))


if __name__ == "__main__":
    main()
