#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw
except ImportError as import_error:
    raise SystemExit("Pillow is required. Install with: python3 -m pip install -r requirements.txt") from import_error

from pipeline.validation import load_and_validate_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_REQUEST = "ai_texture_request_v2"
SCHEMA_PACK = "ai_texture_pack_v2"
SCHEMA_CANDIDATE = "ai_texture_candidate_v1"
SCHEMA_SELECTION = "ai_texture_selection_v1"
SLOT_ORDER = ["base_color", "normal", "orm", "emissive"]
DEFAULT_REQUIRED_SLOTS = ["base_color"]
DEFAULT_OPTIONAL_SLOTS = ["normal", "orm", "emissive"]
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
PROVIDER_MODELS = {
    "nano_banana": "nano-banana-2",
    "nano_banana_pro": "nano-banana-pro",
}
DEMO_COLORS = {
    "floor": (120, 170, 120, 255),
    "wall": (155, 135, 120, 255),
    "stair": (145, 145, 160, 255),
    "prop": (180, 140, 80, 255),
}


class AITextureError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def parse_slot_list(raw_slots: str | None) -> list[str]:
    if not raw_slots:
        return []
    slots = [slot.strip() for slot in raw_slots.split(",") if slot.strip()]
    invalid_slots = [slot for slot in slots if slot not in SLOT_ORDER]
    if invalid_slots:
        raise AITextureError(f"Unsupported material slot(s): {', '.join(invalid_slots)}")
    return slots


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    loaded: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        loaded[key.strip()] = value.strip().strip('"').strip("'")
    return loaded


def repo_env() -> dict[str, str]:
    env = load_env_file(REPO_ROOT / ".env")
    merged = dict(env)
    merged.update({key: value for key, value in os.environ.items() if value is not None})
    return merged


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


def selection_path(cache_root: Path, source_object: str, variant: str) -> Path:
    return pack_directory(cache_root, source_object, variant) / "selection.json"


def textures_directory(cache_root: Path, source_object: str, variant: str) -> Path:
    return pack_directory(cache_root, source_object, variant) / "textures"


def candidates_directory(cache_root: Path, source_object: str, variant: str, slot_name: str) -> Path:
    return pack_directory(cache_root, source_object, variant) / "candidates" / slot_name


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_slot_prompt(entry: dict, slot_name: str) -> str:
    projection_mode = entry.get("projection_mode", "isometric")
    category = entry.get("category", "tile")
    height_class = entry.get("height_class", "medium")
    tags = ", ".join(entry.get("tags", [])) or "none"
    footprint = f"{entry.get('footprint_width', 1)}x{entry.get('footprint_height', 1)}"
    core_description = (
        f"Create a game-ready {slot_name.replace('_', ' ')} texture for a {projection_mode} {category} tile asset. "
        f"Footprint {footprint}. Height class {height_class}. Tags: {tags}. "
        f"Clean production asset, no UI, no text, no watermark, no scene background."
    )
    if slot_name == "base_color":
        return core_description + " Output a readable stylized PBR base color map with even lighting assumptions."
    if slot_name == "normal":
        return core_description + " Output a tangent-space normal map texture only."
    if slot_name == "orm":
        return core_description + " Output a packed ORM texture map only, suitable for occlusion/roughness/metallic workflows."
    if slot_name == "emissive":
        return core_description + " Output an emissive texture map only with black where there is no glow."
    return core_description


def build_request(entry: dict, *, variant: str, required_slots: list[str], optional_slots: list[str]) -> dict:
    prompts = {
        slot_name: build_slot_prompt(entry, slot_name)
        for slot_name in list(dict.fromkeys(required_slots + optional_slots))
    }
    return {
        "schema_version": SCHEMA_REQUEST,
        "source_object": entry["source_object"],
        "category": entry["category"],
        "projection_mode": entry.get("projection_mode"),
        "tile_shape": entry.get("tile_shape"),
        "render_profile": entry.get("render_profile"),
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
        "reference_render_file": entry.get("file"),
        "prompt_hints": [
            entry["category"],
            entry["height_class"],
            *entry["tags"],
        ],
        "prompts": prompts,
        "notes": "Generate candidate images, select one per slot into textures/<slot>.<ext>, then sync/bind.",
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
    return load_json(request_file_path)


def load_selection(selection_file_path: Path) -> dict[str, Any] | None:
    if not selection_file_path.exists():
        return None
    return load_json(selection_file_path)


def candidate_metadata_paths(candidate_dir: Path) -> list[Path]:
    return sorted(candidate_dir.glob("*.json"))


def generate_mock_image(output_path: Path, *, category: str, slot_name: str, size: int) -> None:
    base_color = DEMO_COLORS.get(category, (160, 160, 160, 255))
    image = Image.new("RGBA", (size, size), base_color)
    draw = ImageDraw.Draw(image)
    draw.rectangle((12, 12, size - 12, size - 12), outline=(255, 255, 255, 255), width=4)
    draw.text((20, 20), slot_name, fill=(20, 20, 20, 255))
    image.save(output_path)


def provider_settings(provider: str) -> dict[str, Any]:
    env = repo_env()
    sibling_root = (REPO_ROOT.parent / "nano_banana").resolve()
    nano_banana_root = Path(env.get("ITF_NANO_BANANA_ROOT", str(sibling_root))).expanduser().resolve()
    provider_key = env.get("ITF_NANO_BANANA_KEY", "company")
    timeout_seconds = int(env.get("ITF_NANO_BANANA_TIMEOUT_SECONDS", "180"))
    return {
        "provider": provider,
        "nano_banana_root": nano_banana_root,
        "provider_key": provider_key,
        "timeout_seconds": timeout_seconds,
        "env": env,
    }


def generate_with_nano_banana(
    provider: str,
    *,
    prompt_text: str,
    output_path: Path,
    reference_image: str | None,
    settings: dict[str, Any],
) -> dict[str, Any]:
    provider_root = Path(settings["nano_banana_root"])
    script_path = provider_root / "scripts" / "generate_image.js"
    if not script_path.exists():
        raise AITextureError(f"Nano Banana CLI not found: {script_path}")

    model_name = PROVIDER_MODELS[provider]
    command = [
        "node",
        str(script_path),
        f"--prompt={prompt_text}",
        f"--out={output_path}",
        f"--key={settings['provider_key']}",
        f"--model={model_name}",
    ]
    if reference_image:
        command.append(f"--image={reference_image}")

    provider_env = os.environ.copy()
    for key_name in ("GEMINI_KEY_COMPANY", "GEMINI_KEY_PERSONAL"):
        if settings["env"].get(key_name):
            provider_env[key_name] = settings["env"][key_name]

    completed = subprocess.run(
        command,
        cwd=provider_root,
        env=provider_env,
        capture_output=True,
        text=True,
        timeout=settings["timeout_seconds"],
    )
    if completed.returncode != 0:
        raise AITextureError(
            f"Provider {provider} failed for {output_path.name}: {completed.stderr.strip() or completed.stdout.strip()}"
        )

    return {
        "provider": provider,
        "model": model_name,
        "stdout": completed.stdout.strip(),
    }


def candidate_file_path(cache_root: Path, source_object: str, variant: str, slot_name: str, candidate_id: str) -> Path:
    return candidates_directory(cache_root, source_object, variant, slot_name) / f"{candidate_id}.png"


def candidate_metadata_file_path(cache_root: Path, source_object: str, variant: str, slot_name: str, candidate_id: str) -> Path:
    return candidates_directory(cache_root, source_object, variant, slot_name) / f"{candidate_id}.json"


def generate_texture_candidates(
    manifest_path: Path,
    cache_root: Path,
    *,
    variant: str,
    provider: str,
    slots: list[str],
    candidate_count: int = 1,
    size: int = 256,
) -> dict:
    if candidate_count <= 0:
        raise AITextureError("candidate_count must be a positive integer")
    if provider not in {"mock", *PROVIDER_MODELS.keys()}:
        raise AITextureError(f"Unsupported provider: {provider}")

    manifest_data, _ = load_and_validate_manifest(manifest_path, require_files=True)
    settings = provider_settings(provider)
    generated: list[dict[str, Any]] = []

    for entry in grouped_manifest_objects(manifest_data):
        source_object = entry["source_object"]
        request_data = load_request(request_path(cache_root, source_object, variant))
        slot_list = slots or request_data["required_slots"]
        reference_image = request_data.get("reference_render_file")

        for slot_name in slot_list:
            prompt_text = request_data.get("prompts", {}).get(slot_name) or build_slot_prompt(request_data, slot_name)
            for index in range(candidate_count):
                candidate_id = f"{provider}_{index + 1:03d}"
                image_path = candidate_file_path(cache_root, source_object, variant, slot_name, candidate_id)
                metadata_path = candidate_metadata_file_path(cache_root, source_object, variant, slot_name, candidate_id)
                image_path.parent.mkdir(parents=True, exist_ok=True)

                provider_result: dict[str, Any]
                if provider == "mock":
                    generate_mock_image(image_path, category=request_data["category"], slot_name=slot_name, size=size)
                    provider_result = {"provider": provider, "model": "mock", "stdout": "mock image generated"}
                else:
                    provider_result = generate_with_nano_banana(
                        provider,
                        prompt_text=prompt_text,
                        output_path=image_path,
                        reference_image=reference_image,
                        settings=settings,
                    )

                metadata = {
                    "schema_version": SCHEMA_CANDIDATE,
                    "source_object": source_object,
                    "variant": variant,
                    "slot": slot_name,
                    "candidate_id": candidate_id,
                    "provider": provider_result["provider"],
                    "model": provider_result["model"],
                    "prompt": prompt_text,
                    "reference_image": reference_image,
                    "file": str(image_path.relative_to(pack_directory(cache_root, source_object, variant))),
                    "created_at": now_iso(),
                    "rank_score": float(index + 1),
                    "rank_reason": "generation order",
                    "status": "generated",
                }
                write_json(metadata_path, metadata)
                generated.append(metadata)

    return {
        "cache_root": str(cache_root),
        "variant": variant,
        "provider": provider,
        "candidate_count": len(generated),
        "generated": generated,
    }


def rank_candidates(cache_root: Path, source_object: str, variant: str, slot_name: str) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for metadata_path in candidate_metadata_paths(candidates_directory(cache_root, source_object, variant, slot_name)):
        metadata = load_json(metadata_path)
        image_path = pack_directory(cache_root, source_object, variant) / metadata["file"]
        if not image_path.exists():
            continue
        stat = image_path.stat()
        metadata["rank_score"] = float(stat.st_mtime)
        metadata["rank_reason"] = "newest candidate first"
        ranked.append(metadata)
    ranked.sort(key=lambda item: (item.get("rank_score", 0.0), item.get("candidate_id", "")), reverse=True)
    return ranked


def copy_selected_candidate(image_path: Path, destination_path: Path) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(image_path, destination_path)


def select_texture_candidates(
    manifest_path: Path,
    cache_root: Path,
    *,
    variant: str,
    slots: list[str],
    strategy: str = "latest",
) -> dict:
    if strategy != "latest":
        raise AITextureError("Only strategy=latest is currently supported")

    manifest_data, _ = load_and_validate_manifest(manifest_path, require_files=True)
    selections: list[dict[str, Any]] = []

    for entry in grouped_manifest_objects(manifest_data):
        source_object = entry["source_object"]
        request_data = load_request(request_path(cache_root, source_object, variant))
        slot_list = slots or list(dict.fromkeys(request_data["required_slots"] + request_data["optional_slots"]))
        chosen_slots: dict[str, Any] = {}

        for slot_name in slot_list:
            ranked = rank_candidates(cache_root, source_object, variant, slot_name)
            if not ranked:
                continue
            top_candidate = ranked[0]
            candidate_image = pack_directory(cache_root, source_object, variant) / top_candidate["file"]
            destination = textures_directory(cache_root, source_object, variant) / f"{slot_name}{candidate_image.suffix.lower()}"
            copy_selected_candidate(candidate_image, destination)
            chosen_slots[slot_name] = {
                "candidate_id": top_candidate["candidate_id"],
                "provider": top_candidate["provider"],
                "model": top_candidate["model"],
                "file": str(destination.relative_to(pack_directory(cache_root, source_object, variant))),
                "rank_score": top_candidate["rank_score"],
                "rank_reason": top_candidate["rank_reason"],
                "selected_at": now_iso(),
            }

        selection_data = {
            "schema_version": SCHEMA_SELECTION,
            "source_object": source_object,
            "variant": variant,
            "strategy": strategy,
            "slots": chosen_slots,
        }
        write_json(selection_path(cache_root, source_object, variant), selection_data)
        selections.append(selection_data)

    sync_result = sync_texture_cache(manifest_path, cache_root, variant=variant)
    return {
        "cache_root": str(cache_root),
        "variant": variant,
        "strategy": strategy,
        "selection_count": len(selections),
        "selections": selections,
        "sync": sync_result,
    }


def sync_texture_cache(manifest_path: Path, cache_root: Path, *, variant: str) -> dict:
    manifest_data, _ = load_and_validate_manifest(manifest_path, require_files=True)
    pack_summaries = []

    for entry in grouped_manifest_objects(manifest_data):
        source_object = entry["source_object"]
        request_data = load_request(request_path(cache_root, source_object, variant))
        selection_data = load_selection(selection_path(cache_root, source_object, variant))
        texture_dir = textures_directory(cache_root, source_object, variant)
        texture_dir.mkdir(parents=True, exist_ok=True)

        slots = {}
        missing_required_slots = []
        candidate_counts = {}
        selected_slots = selection_data.get("slots", {}) if selection_data else {}

        for slot_name in SLOT_ORDER:
            texture_file = find_texture_file(texture_dir, slot_name)
            slots[slot_name] = {
                "present": texture_file is not None,
                "file": str(texture_file.relative_to(pack_directory(cache_root, source_object, variant)))
                if texture_file
                else None,
                "selected_candidate": selected_slots.get(slot_name),
            }
            candidate_counts[slot_name] = len(rank_candidates(cache_root, source_object, variant, slot_name))
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
            "candidate_counts": candidate_counts,
            "selection": selection_data,
            "slots": slots,
        }
        write_json(pack_path(cache_root, source_object, variant), pack_data)
        pack_summaries.append(
            {
                "source_object": source_object,
                "status": status,
                "present_slots": [slot for slot, data in slots.items() if data["present"]],
                "candidate_counts": candidate_counts,
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

        pack_data = load_json(pack_file_path)
        if pack_data.get("schema_version") != SCHEMA_PACK:
            errors.append(f"Invalid pack schema for {source_object}/{variant}")
        if pack_data.get("source_object") != source_object:
            errors.append(f"Pack source_object mismatch for {source_object}/{variant}")
        if pack_data.get("variant") != variant:
            errors.append(f"Pack variant mismatch for {source_object}/{variant}")

        selection_data = pack_data.get("selection")
        if selection_data and selection_data.get("schema_version") != SCHEMA_SELECTION:
            errors.append(f"Invalid selection schema for {source_object}/{variant}")

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

                selected_candidate = slot_info.get("selected_candidate")
                if selected_candidate:
                    candidate_id = selected_candidate.get("candidate_id")
                    if candidate_id:
                        metadata_path = candidate_metadata_file_path(
                            cache_root,
                            source_object,
                            variant,
                            slot_name,
                            candidate_id,
                        )
                        if not metadata_path.exists():
                            errors.append(f"Selected candidate metadata missing: {metadata_path}")

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
    candidate_counter: Counter[str] = Counter()
    objects = []

    for entry in grouped_manifest_objects(manifest_data):
        source_object = entry["source_object"]
        pack_file_path = pack_path(cache_root, source_object, variant)
        if not pack_file_path.exists():
            status_counter["missing_pack"] += 1
            objects.append({"source_object": source_object, "status": "missing_pack"})
            continue

        pack_data = load_json(pack_file_path)
        status = pack_data.get("status", "unknown")
        status_counter[status] += 1
        for slot_name, slot_info in pack_data.get("slots", {}).items():
            if slot_info.get("present"):
                slot_counter[slot_name] += 1
        for slot_name, count in pack_data.get("candidate_counts", {}).items():
            candidate_counter[slot_name] += int(count)
        objects.append(
            {
                "source_object": source_object,
                "status": status,
                "present_slots": [slot for slot, info in pack_data.get("slots", {}).items() if info.get("present")],
                "candidate_counts": pack_data.get("candidate_counts", {}),
                "selection": (pack_data.get("selection") or {}).get("slots", {}),
            }
        )

    return {
        "cache_root": str(cache_root),
        "variant": variant,
        "object_count": len(objects),
        "status_counts": dict(sorted(status_counter.items())),
        "slot_presence_counts": dict(sorted(slot_counter.items())),
        "candidate_counts": dict(sorted(candidate_counter.items())),
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

    generate_parser = subparsers.add_parser("generate", parents=[common_parser], help="Generate provider candidates")
    generate_parser.add_argument("--provider", default="mock", help="mock | nano_banana | nano_banana_pro")
    generate_parser.add_argument("--slots", default="base_color", help="Comma-separated slots to generate")
    generate_parser.add_argument("--candidate-count", type=int, default=1, help="Candidates per slot")
    generate_parser.add_argument("--size", type=int, default=256, help="Mock generation size")

    select_parser = subparsers.add_parser("select", parents=[common_parser], help="Select top-ranked candidates into textures/")
    select_parser.add_argument("--slots", default="base_color", help="Comma-separated slots to select")
    select_parser.add_argument("--strategy", default="latest", help="Selection strategy")

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

    if args.command == "generate":
        result = generate_texture_candidates(
            manifest_path,
            cache_root,
            variant=args.variant,
            provider=args.provider,
            slots=parse_slot_list(args.slots),
            candidate_count=args.candidate_count,
            size=args.size,
        )
        print(json.dumps({"ok": True, "mode": "generate", "result": result}, indent=2))
        return

    if args.command == "select":
        result = select_texture_candidates(
            manifest_path,
            cache_root,
            variant=args.variant,
            slots=parse_slot_list(args.slots),
            strategy=args.strategy,
        )
        print(json.dumps({"ok": True, "mode": "select", "result": result}, indent=2))
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
