#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

try:
    from PIL import Image
except ImportError as import_error:
    raise SystemExit("Pillow is required. Install with: python3 -m pip install -r requirements.txt") from import_error

from pipeline.validation import load_and_validate_manifest

SCHEMA_REQUEST = "ai_texture_request_v1"
SCHEMA_PACK = "ai_texture_pack_v1"
SLOT_ORDER = ["base_color", "normal", "orm", "emissive"]
DEFAULT_REQUIRED_SLOTS = ["base_color"]
DEFAULT_OPTIONAL_SLOTS = ["normal", "orm", "emissive"]
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
DEMO_COLORS = {
    "floor": (120, 170, 120, 255),
    "wall": (155, 135, 120, 255),
    "stair": (145, 145, 160, 255),
    "prop": (180, 140, 80, 255),
}


class AITextureError(RuntimeError):
    pass


def parse_slot_list(raw_slots: str | None) -> list[str]:
    if not raw_slots:
        return []
    slots = [slot.strip() for slot in raw_slots.split(",") if slot.strip()]
    invalid_slots = [slot for slot in slots if slot not in SLOT_ORDER]
    if invalid_slots:
        raise AITextureError(f"Unsupported material slot(s): {', '.join(invalid_slots)}")
    return slots


def grouped_manifest_objects(manifest_data: dict) -> list[dict]:
    grouped: dict[str, dict] = {}
    for entry in manifest_data["entries"]:
        source_object = entry["source_object"]
        if source_object not in grouped:
            grouped[source_object] = entry
    return [grouped[key] for key in sorted(grouped.keys())]


def pack_directory(cache_root: Path, source_object: str, variant: str) -> Path:
    return cache_root / source_object / variant


def request_path(cache_root: Path, source_object: str, variant: str) -> Path:
    return pack_directory(cache_root, source_object, variant) / "request.json"


def pack_path(cache_root: Path, source_object: str, variant: str) -> Path:
    return pack_directory(cache_root, source_object, variant) / "pack.json"


def textures_directory(cache_root: Path, source_object: str, variant: str) -> Path:
    return pack_directory(cache_root, source_object, variant) / "textures"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_request(entry: dict, *, variant: str, required_slots: list[str], optional_slots: list[str]) -> dict:
    return {
        "schema_version": SCHEMA_REQUEST,
        "source_object": entry["source_object"],
        "category": entry["category"],
        "anchor_type": entry["anchor_type"],
        "footprint_width": entry["footprint_width"],
        "footprint_height": entry["footprint_height"],
        "height_class": entry["height_class"],
        "tags": entry["tags"],
        "source_collection": entry["source_collection"],
        "variant": variant,
        "material_variant": variant,
        "render_preset": entry["render_preset"],
        "required_slots": required_slots,
        "optional_slots": optional_slots,
        "prompt_hints": [
            entry["category"],
            entry["height_class"],
            *entry["tags"],
        ],
        "notes": "Place selected texture files into textures/<slot>.<ext> and run sync-ai-textures.",
    }


def init_texture_cache(
    manifest_path: Path,
    cache_root: Path,
    *,
    variant: str,
    required_slots: list[str],
    optional_slots: list[str],
) -> dict:
    manifest_data, _ = load_and_validate_manifest(manifest_path, require_files=True)
    created_requests = []

    for entry in grouped_manifest_objects(manifest_data):
        request_data = build_request(
            entry,
            variant=variant,
            required_slots=required_slots,
            optional_slots=optional_slots,
        )
        request_file_path = request_path(cache_root, entry["source_object"], variant)
        write_json(request_file_path, request_data)
        textures_directory(cache_root, entry["source_object"], variant).mkdir(parents=True, exist_ok=True)
        created_requests.append(str(request_file_path))

    return {
        "cache_root": str(cache_root),
        "variant": variant,
        "request_count": len(created_requests),
        "requests": created_requests,
    }


def find_texture_file(texture_dir: Path, slot_name: str) -> Path | None:
    for extension in sorted(ALLOWED_EXTENSIONS):
        candidate = texture_dir / f"{slot_name}{extension}"
        if candidate.exists():
            return candidate
    return None


def load_request(request_file_path: Path) -> dict:
    if not request_file_path.exists():
        raise AITextureError(f"Missing texture request file: {request_file_path}")
    return json.loads(request_file_path.read_text(encoding="utf-8"))


def sync_texture_cache(manifest_path: Path, cache_root: Path, *, variant: str) -> dict:
    manifest_data, _ = load_and_validate_manifest(manifest_path, require_files=True)
    pack_summaries = []

    for entry in grouped_manifest_objects(manifest_data):
        source_object = entry["source_object"]
        request_data = load_request(request_path(cache_root, source_object, variant))
        texture_dir = textures_directory(cache_root, source_object, variant)
        texture_dir.mkdir(parents=True, exist_ok=True)

        slots = {}
        missing_required_slots = []
        for slot_name in SLOT_ORDER:
            texture_file = find_texture_file(texture_dir, slot_name)
            slots[slot_name] = {
                "present": texture_file is not None,
                "file": str(texture_file.relative_to(pack_directory(cache_root, source_object, variant)))
                if texture_file
                else None,
            }
            if slot_name in request_data["required_slots"] and texture_file is None:
                missing_required_slots.append(slot_name)

        if missing_required_slots and all(not slot["present"] for slot in slots.values()):
            status = "draft"
        elif missing_required_slots:
            status = "partial"
        else:
            status = "ready"

        pack_data = {
            "schema_version": SCHEMA_PACK,
            "source_object": source_object,
            "variant": variant,
            "material_variant": request_data["material_variant"],
            "render_preset": request_data["render_preset"],
            "required_slots": request_data["required_slots"],
            "optional_slots": request_data["optional_slots"],
            "status": status,
            "slots": slots,
        }
        write_json(pack_path(cache_root, source_object, variant), pack_data)
        pack_summaries.append(
            {
                "source_object": source_object,
                "status": status,
                "present_slots": [slot for slot, data in slots.items() if data["present"]],
            }
        )

    return {
        "cache_root": str(cache_root),
        "variant": variant,
        "pack_count": len(pack_summaries),
        "packs": pack_summaries,
    }


def validate_texture_cache(manifest_path: Path, cache_root: Path, *, variant: str) -> dict:
    manifest_data, _ = load_and_validate_manifest(manifest_path, require_files=True)
    errors: list[str] = []
    pack_statuses = []

    for entry in grouped_manifest_objects(manifest_data):
        source_object = entry["source_object"]
        request_data = load_request(request_path(cache_root, source_object, variant))
        pack_file_path = pack_path(cache_root, source_object, variant)
        if not pack_file_path.exists():
            errors.append(f"Missing pack.json for {source_object}/{variant}")
            continue

        pack_data = json.loads(pack_file_path.read_text(encoding="utf-8"))
        if pack_data.get("schema_version") != SCHEMA_PACK:
            errors.append(f"Invalid pack schema for {source_object}/{variant}")
        if pack_data.get("source_object") != source_object:
            errors.append(f"Pack source_object mismatch for {source_object}/{variant}")
        if pack_data.get("variant") != variant:
            errors.append(f"Pack variant mismatch for {source_object}/{variant}")

        for slot_name in request_data["required_slots"]:
            slot_info = pack_data.get("slots", {}).get(slot_name)
            if not slot_info or not slot_info.get("present"):
                errors.append(f"Required slot {slot_name} missing for {source_object}/{variant}")

        for slot_name, slot_info in pack_data.get("slots", {}).items():
            if slot_name not in SLOT_ORDER:
                errors.append(f"Unknown slot {slot_name} in {source_object}/{variant}")
                continue
            file_value = slot_info.get("file")
            if slot_info.get("present"):
                if not file_value:
                    errors.append(f"Slot {slot_name} marked present without file in {source_object}/{variant}")
                    continue
                texture_file_path = pack_directory(cache_root, source_object, variant) / file_value
                if not texture_file_path.exists():
                    errors.append(f"Texture file missing on disk: {texture_file_path}")
                elif texture_file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                    errors.append(f"Unsupported texture extension for {texture_file_path}")

        pack_statuses.append({"source_object": source_object, "status": pack_data.get("status", "unknown")})

    return {
        "ok": not errors,
        "cache_root": str(cache_root),
        "variant": variant,
        "errors": errors,
        "packs": pack_statuses,
    }


def inspect_texture_cache(manifest_path: Path, cache_root: Path, *, variant: str) -> dict:
    manifest_data, _ = load_and_validate_manifest(manifest_path, require_files=True)
    status_counter: Counter[str] = Counter()
    slot_counter: Counter[str] = Counter()
    objects = []

    for entry in grouped_manifest_objects(manifest_data):
        source_object = entry["source_object"]
        pack_file_path = pack_path(cache_root, source_object, variant)
        if not pack_file_path.exists():
            status_counter["missing_pack"] += 1
            objects.append({"source_object": source_object, "status": "missing_pack"})
            continue

        pack_data = json.loads(pack_file_path.read_text(encoding="utf-8"))
        status = pack_data.get("status", "unknown")
        status_counter[status] += 1
        for slot_name, slot_info in pack_data.get("slots", {}).items():
            if slot_info.get("present"):
                slot_counter[slot_name] += 1
        objects.append(
            {
                "source_object": source_object,
                "status": status,
                "present_slots": [slot for slot, info in pack_data.get("slots", {}).items() if info.get("present")],
            }
        )

    return {
        "cache_root": str(cache_root),
        "variant": variant,
        "object_count": len(objects),
        "status_counts": dict(sorted(status_counter.items())),
        "slot_presence_counts": dict(sorted(slot_counter.items())),
        "objects": objects,
    }


def create_demo_textures(manifest_path: Path, cache_root: Path, *, variant: str, size: int = 256) -> dict:
    manifest_data, _ = load_and_validate_manifest(manifest_path, require_files=True)
    created = []

    for entry in grouped_manifest_objects(manifest_data):
        source_object = entry["source_object"]
        texture_dir = textures_directory(cache_root, source_object, variant)
        texture_dir.mkdir(parents=True, exist_ok=True)
        image_path = texture_dir / "base_color.png"
        image = Image.new("RGBA", (size, size), DEMO_COLORS.get(entry["category"], (160, 160, 160, 255)))
        image.save(image_path)
        created.append(str(image_path))

    return {
        "cache_root": str(cache_root),
        "variant": variant,
        "created_textures": created,
        "count": len(created),
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI texture cache workflow helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--manifest", required=True, help="Path to manifest.json")
    common_parser.add_argument("--cache-root", default="texture_cache", help="Texture cache root")
    common_parser.add_argument("--variant", default="ai_v1", help="Texture variant name")

    init_parser = subparsers.add_parser("init", parents=[common_parser], help="Initialize request files and cache layout")
    init_parser.add_argument("--required-slots", default="base_color", help="Comma-separated required slots")
    init_parser.add_argument(
        "--optional-slots",
        default="normal,orm,emissive",
        help="Comma-separated optional slots",
    )

    subparsers.add_parser("sync", parents=[common_parser], help="Sync pack.json files from current textures/")
    subparsers.add_parser("validate", parents=[common_parser], help="Validate texture pack contents")
    subparsers.add_parser("inspect", parents=[common_parser], help="Inspect texture pack summary")

    demo_parser = subparsers.add_parser("create-demo", parents=[common_parser], help="Create demo base_color textures")
    demo_parser.add_argument("--size", type=int, default=256, help="Demo texture size")

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    manifest_path = Path(args.manifest).expanduser().resolve()
    cache_root = Path(args.cache_root).expanduser().resolve()

    if args.command == "init":
        result = init_texture_cache(
            manifest_path,
            cache_root,
            variant=args.variant,
            required_slots=parse_slot_list(args.required_slots) or DEFAULT_REQUIRED_SLOTS,
            optional_slots=parse_slot_list(args.optional_slots) or DEFAULT_OPTIONAL_SLOTS,
        )
        print(json.dumps({"ok": True, "mode": "init", "result": result}, indent=2))
        return

    if args.command == "sync":
        result = sync_texture_cache(manifest_path, cache_root, variant=args.variant)
        print(json.dumps({"ok": True, "mode": "sync", "result": result}, indent=2))
        return

    if args.command == "validate":
        result = validate_texture_cache(manifest_path, cache_root, variant=args.variant)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["ok"] else 1)

    if args.command == "inspect":
        result = inspect_texture_cache(manifest_path, cache_root, variant=args.variant)
        print(json.dumps({"ok": True, "mode": "inspect", "result": result}, indent=2))
        return

    if args.command == "create-demo":
        result = create_demo_textures(manifest_path, cache_root, variant=args.variant, size=args.size)
        print(json.dumps({"ok": True, "mode": "create-demo", "result": result}, indent=2))
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
