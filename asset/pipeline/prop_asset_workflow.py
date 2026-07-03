from __future__ import annotations

import json
import math
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from PIL import Image, ImageDraw

from pipeline.prop_cleanup_scorer import score_cleanup_candidates
from pipeline.prop_validator import PropValidationError, validate_prop_asset_set
from pipeline.reference_pair_workflow import (
    CLI_PROXY_DEFAULT_MODEL,
    ReferencePairWorkflowError,
    _cleanup_artifact_token,
    _normalize_provider_contract,
    apply_color_key_to_image,
    default_cleanup_candidate_path,
    generate_with_provider,
    parse_hex_color,
    resolve_input_path,
    slugify,
    update_step_status_summary,
    write_json,
)

SCHEMA_VERSION = "prop_asset_workflow_v1"
MANIFEST_SCHEMA_VERSION = "prop_asset_manifest_v1"
ATLAS_METADATA_SCHEMA_VERSION = "prop_asset_atlas_metadata_v1"
IMT_HANDOFF_SCHEMA_VERSION = "imt_prop_handoff_v1"
DEFAULT_OUTPUT_ROOT = "output/prop_asset_runs"
GPT_TRANSPARENT_PROVIDER = "gpt_image"
GPT_TRANSPARENT_MODE = "gpt_image_transparent_prop"
GPT_COLOR_KEY_MODE = "gpt_image_prop_color_key"
DEFAULT_GENERATION_CANVAS = {
    "strategy": "derive_from_final_canvas",
    "target_long_edge": 1024,
    "preserve_aspect_ratio": True,
}
GPT_IMAGE_SUPPORTED_SIZES = (
    (1024, 1024),
    (1536, 1024),
    (1024, 1536),
)
GEMINI_SUPPORTED_ASPECT_RATIOS = ("1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "21:9")
GEMINI_SUPPORTED_IMAGE_SIZES = (
    ("1K", 1024),
    ("2K", 2048),
    ("4K", 4096),
)


class PropAssetWorkflowError(RuntimeError):
    pass


def _ratio_string(width: int, height: int) -> str:
    divisor = math.gcd(max(1, width), max(1, height))
    return f"{max(1, width) // divisor}:{max(1, height) // divisor}"


def _ratio_value(ratio_text: str) -> float:
    left_text, right_text = str(ratio_text).split(":", 1)
    left = max(1, int(left_text))
    right = max(1, int(right_text))
    return left / float(right)


def _size_string(width: int, height: int) -> str:
    return f"{int(width)}x{int(height)}"


def _normalize_generation_canvas(raw: Any, *, final_canvas: dict[str, Any]) -> dict[str, Any]:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise PropAssetWorkflowError("generation_canvas must be an object when provided.")
    strategy = str(raw.get("strategy", DEFAULT_GENERATION_CANVAS["strategy"])).strip().lower() or DEFAULT_GENERATION_CANVAS["strategy"]
    if strategy != "derive_from_final_canvas":
        raise PropAssetWorkflowError("generation_canvas.strategy currently supports only 'derive_from_final_canvas'.")
    target_long_edge = int(raw.get("target_long_edge", DEFAULT_GENERATION_CANVAS["target_long_edge"]))
    if target_long_edge <= 0:
        raise PropAssetWorkflowError("generation_canvas.target_long_edge must be a positive integer.")
    preserve_aspect_ratio = bool(raw.get("preserve_aspect_ratio", DEFAULT_GENERATION_CANVAS["preserve_aspect_ratio"]))
    final_width = int(final_canvas.get("width", 128))
    final_height = int(final_canvas.get("height", 256))
    longest_edge = max(final_width, final_height)
    scale = target_long_edge / float(max(1, longest_edge))
    derived_width = max(1, int(round(final_width * scale)))
    derived_height = max(1, int(round(final_height * scale)))
    return {
        "strategy": strategy,
        "target_long_edge": target_long_edge,
        "preserve_aspect_ratio": preserve_aspect_ratio,
        "final_canvas": {"width": final_width, "height": final_height},
        "derived_aspect_ratio": _ratio_string(final_width, final_height),
        "derived_size": {"width": derived_width, "height": derived_height},
    }


def _closest_supported_ratio(requested_ratio: str, *, supported_ratios: Sequence[str]) -> str:
    requested_value = _ratio_value(requested_ratio)
    return min(
        supported_ratios,
        key=lambda candidate: (
            abs(_ratio_value(candidate) - requested_value),
            abs(math.log(_ratio_value(candidate)) - math.log(requested_value)),
            candidate,
        ),
    )


def _build_prop_provider_adapter(
    *,
    provider_name: str,
    provider_mode: str,
    model_name: str,
    generation_canvas: dict[str, Any],
) -> dict[str, Any]:
    derived_size = generation_canvas["derived_size"]
    requested_width = int(derived_size["width"])
    requested_height = int(derived_size["height"])
    requested_ratio = str(generation_canvas["derived_aspect_ratio"])
    requested_size = _size_string(requested_width, requested_height)
    requested_long_edge = max(requested_width, requested_height)

    if provider_name == "mock":
        adapter_decision = {
            "provider": "mock",
            "requested_aspect_ratio": requested_ratio,
            "requested_size": requested_size,
            "provider_size": requested_size,
            "provider_aspect_ratio": requested_ratio,
            "fallback_used": False,
        }
        return {
            "adapter": "mock",
            "backend_provider_name": "mock",
            "provider_generation_args": {},
            "adapter_decision": adapter_decision,
            "generation_canvas": {
                **generation_canvas,
                "adapter": "mock",
                "provider_size": requested_size,
                "provider_aspect_ratio": requested_ratio,
            },
        }

    if provider_mode in {GPT_TRANSPARENT_MODE, GPT_COLOR_KEY_MODE} or (provider_name == "cliproxyapi" and model_name == CLI_PROXY_DEFAULT_MODEL):
        supported_choice = min(
            GPT_IMAGE_SUPPORTED_SIZES,
            key=lambda size: (
                abs((size[0] / float(size[1])) - (requested_width / float(requested_height))),
                abs(max(size) - requested_long_edge),
                abs((size[0] * size[1]) - (requested_width * requested_height)),
            ),
        )
        provider_size = _size_string(*supported_choice)
        provider_ratio = _ratio_string(*supported_choice)
        fallback_used = provider_size != requested_size
        adapter_decision = {
            "provider": "gpt_image",
            "requested_aspect_ratio": requested_ratio,
            "requested_size": requested_size,
            "provider_size": provider_size,
            "provider_aspect_ratio": provider_ratio,
            "fallback_used": fallback_used,
            **({"reason": "closest_supported_size"} if fallback_used else {}),
        }
        return {
            "adapter": "gpt_image",
            "backend_provider_name": "cliproxyapi",
            "provider_generation_args": {"size": provider_size},
            "adapter_decision": adapter_decision,
            "generation_canvas": {
                **generation_canvas,
                "adapter": "gpt_image",
                "provider_size": provider_size,
                "provider_aspect_ratio": provider_ratio,
            },
        }

    provider_aspect_ratio = _closest_supported_ratio(requested_ratio, supported_ratios=GEMINI_SUPPORTED_ASPECT_RATIOS)
    provider_image_size, provider_long_edge = min(
        GEMINI_SUPPORTED_IMAGE_SIZES,
        key=lambda entry: (abs(entry[1] - generation_canvas["target_long_edge"]), entry[1]),
    )
    fallback_used = provider_aspect_ratio != requested_ratio or provider_long_edge != generation_canvas["target_long_edge"]
    if provider_aspect_ratio != requested_ratio and provider_long_edge != generation_canvas["target_long_edge"]:
        reason = "closest_supported_ratio_and_image_size"
    elif provider_aspect_ratio != requested_ratio:
        reason = "closest_supported_ratio"
    elif provider_long_edge != generation_canvas["target_long_edge"]:
        reason = "closest_supported_image_size"
    else:
        reason = ""
    adapter_decision = {
        "provider": provider_name,
        "requested_aspect_ratio": requested_ratio,
        "requested_size": requested_size,
        "provider_aspect_ratio": provider_aspect_ratio,
        "image_size": provider_image_size,
        "fallback_used": fallback_used,
        **({"reason": reason} if reason else {}),
    }
    return {
        "adapter": "gemini_cli",
        "backend_provider_name": provider_name,
        "provider_generation_args": {
            "aspect_ratio": provider_aspect_ratio,
            "image_size": provider_image_size,
        },
        "adapter_decision": adapter_decision,
        "generation_canvas": {
            **generation_canvas,
            "adapter": "gemini_cli",
            "provider_aspect_ratio": provider_aspect_ratio,
            "provider_image_size": provider_image_size,
        },
    }


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PropAssetWorkflowError(f"{label} must be a non-empty string.")
    return value.strip()


def _normalize_provider(raw: dict[str, Any]) -> tuple[dict[str, str], dict[str, str], list[str]]:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise PropAssetWorkflowError("provider must be an object when provided.")
    provider_name = str(raw.get("name", "mock")).strip().lower() or "mock"
    provider_mode = str(raw.get("mode", "direct")).strip().lower() or "direct"
    provider_agent_tool = str(raw.get("agent_tool", "")).strip().lower()
    model_raw = raw.get("model", "")
    requested_model = str(model_raw).strip().lower()
    return _normalize_provider_contract(
        provider_name_raw=provider_name,
        provider_mode=provider_mode,
        requested_model_name=requested_model,
        provider_agent_tool=provider_agent_tool,
    )


def _normalize_model(raw_model: Any, provider_raw: dict[str, Any]) -> str:
    if isinstance(raw_model, dict):
        model_name = str(raw_model.get("name", "")).strip().lower()
    else:
        model_name = ""
    if not model_name:
        model_name = str(provider_raw.get("model", "")).strip().lower()
    return model_name


def _normalize_background(raw: Any) -> dict[str, Any]:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise PropAssetWorkflowError("background must be an object when provided.")
    mode = str(raw.get("mode", "color_key")).strip().lower() or "color_key"
    if mode not in {"transparent", "transparent_native", "color_key"}:
        raise PropAssetWorkflowError("background.mode must be transparent, transparent_native, or color_key.")
    prompt_color = str(raw.get("prompt_color", "#FF00FF")).strip().upper() or "#FF00FF"
    fallback_colors = raw.get("fallback_colors", ["#00FF00"])
    if isinstance(fallback_colors, str):
        fallback_colors = [fallback_colors]
    if not isinstance(fallback_colors, list):
        raise PropAssetWorkflowError("background.fallback_colors must be an array when provided.")
    parse_hex_color(prompt_color)
    normalized_fallback_colors = [str(color).strip().upper() for color in fallback_colors if str(color).strip()]
    for color in normalized_fallback_colors:
        parse_hex_color(color)
    tolerance = int(raw.get("tolerance", 24))
    if tolerance < 0 or tolerance > 255:
        raise PropAssetWorkflowError("background.tolerance must be between 0 and 255.")
    return {
        "mode": mode,
        "prompt_color": prompt_color,
        "fallback_colors": normalized_fallback_colors,
        "tolerance": tolerance,
    }


def _normalize_prompt_parts(raw: Any, *, asset_family: str) -> dict[str, Any]:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise PropAssetWorkflowError("prompt_parts must be an object when provided.")
    style = str(raw.get("style", "")).strip() or "readable isometric pixel-art dungeon prop"
    material = str(raw.get("material", "")).strip() or "aged bronze brazier, dark iron rim, soot, warm ember accents"
    decoration = str(raw.get("decoration", "")).strip() or "compact silhouette suitable for a 1x1 dungeon interaction prop"
    negative = raw.get("negative_constraints", [])
    if isinstance(negative, str):
        negative = [negative]
    if not isinstance(negative, list):
        raise PropAssetWorkflowError("prompt_parts.negative_constraints must be an array when provided.")
    negative_constraints = [str(item).strip() for item in negative if str(item).strip()]
    if not negative_constraints:
        negative_constraints = [
            "no text",
            "no watermark",
            "no baked-in floor tile",
            "no large cast shadow",
            "no scene background",
            "no extra props",
        ]
    return {
        "style": style,
        "material": material,
        "decoration": decoration,
        "negative_constraints": negative_constraints,
        "asset_family": asset_family,
    }


def _normalize_state(raw_state: Any, *, index: int) -> dict[str, Any]:
    if not isinstance(raw_state, dict):
        raise PropAssetWorkflowError("states[] must be objects.")
    asset_id = require_non_empty_string(raw_state.get("asset_id"), f"states[{index}].asset_id")
    role = require_non_empty_string(raw_state.get("role"), f"states[{index}].role")
    generation = raw_state.get("generation", {})
    if generation is None:
        generation = {}
    if not isinstance(generation, dict):
        raise PropAssetWorkflowError(f"states[{index}].generation must be an object when provided.")
    mode = str(generation.get("mode", "base")).strip().lower() or "base"
    if mode not in {"base", "edit_from"}:
        raise PropAssetWorkflowError(f"states[{index}].generation.mode must be base or edit_from.")
    source_asset_id = str(generation.get("source_asset_id", "")).strip()
    prompt_delta = str(generation.get("prompt_delta", "")).strip()
    style_constraints = raw_state.get("style_constraints", [])
    if isinstance(style_constraints, str):
        style_constraints = [style_constraints]
    if not isinstance(style_constraints, list):
        raise PropAssetWorkflowError(f"states[{index}].style_constraints must be an array when provided.")
    return {
        "asset_id": asset_id,
        "role": role,
        "view": str(raw_state.get("view", "")).strip(),
        "background": str(raw_state.get("background", "")).strip(),
        "silhouette": str(raw_state.get("silhouette", "")).strip(),
        "style_constraints": [str(item).strip() for item in style_constraints if str(item).strip()],
        "generation": {
            "mode": mode,
            "source_asset_id": source_asset_id,
            "prompt_delta": prompt_delta,
        },
    }


def load_and_validate_prop_spec(spec_path: Path) -> tuple[dict[str, Any], list[str]]:
    raw = load_json(spec_path)
    if not isinstance(raw, dict):
        raise PropAssetWorkflowError("Spec must be a JSON object.")
    schema_version = require_non_empty_string(raw.get("schema_version"), "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise PropAssetWorkflowError(f"Unsupported schema_version '{schema_version}'. Expected '{SCHEMA_VERSION}'.")

    asset_family = require_non_empty_string(raw.get("asset_family"), "asset_family")
    target_project_folder = str(raw.get("target_project_folder", "")).strip()
    canvas = raw.get("canvas", {})
    if not isinstance(canvas, dict):
        raise PropAssetWorkflowError("canvas must be an object.")
    canvas_width = int(canvas.get("width", 128))
    canvas_height = int(canvas.get("height", 256))
    if canvas_width <= 0 or canvas_height <= 0:
        raise PropAssetWorkflowError("canvas width/height must be positive integers.")

    projection_mode = str(raw.get("projection_mode", "isometric")).strip().lower() or "isometric"
    if projection_mode != "isometric":
        raise PropAssetWorkflowError("projection_mode currently supports only 'isometric'.")

    anchor = raw.get("anchor", {})
    if not isinstance(anchor, dict):
        raise PropAssetWorkflowError("anchor must be an object.")
    anchor_type = str(anchor.get("type", "bottom_center")).strip() or "bottom_center"
    anchor_x = int(anchor.get("x", canvas_width // 2))
    anchor_y = int(anchor.get("y", canvas_height - 1))

    footprint = raw.get("footprint", {})
    if not isinstance(footprint, dict):
        raise PropAssetWorkflowError("footprint must be an object.")
    tile_width = int(footprint.get("tile_width", 1))
    tile_height = int(footprint.get("tile_height", 1))
    if tile_width <= 0 or tile_height <= 0:
        raise PropAssetWorkflowError("footprint tile_width/tile_height must be positive integers.")

    states_raw = raw.get("states")
    if not isinstance(states_raw, list) or not states_raw:
        raise PropAssetWorkflowError("states must be a non-empty array.")
    states = [_normalize_state(state, index=index) for index, state in enumerate(states_raw)]
    seen_asset_ids: set[str] = set()
    for state in states:
        asset_id = state["asset_id"]
        if asset_id in seen_asset_ids:
            raise PropAssetWorkflowError(f"duplicate state asset_id '{asset_id}'.")
        seen_asset_ids.add(asset_id)
        source_asset_id = state["generation"].get("source_asset_id", "")
        if state["generation"]["mode"] == "edit_from" and source_asset_id and source_asset_id not in seen_asset_ids:
            raise PropAssetWorkflowError(
                f"state '{asset_id}' edits from '{source_asset_id}', but the source must appear earlier in states for the first vertical slice."
            )

    provider_raw = raw.get("provider", {"name": "mock"})
    if provider_raw is None:
        provider_raw = {"name": "mock"}
    if not isinstance(provider_raw, dict):
        raise PropAssetWorkflowError("provider must be an object when provided.")
    requested_model_name = _normalize_model(raw.get("model", {}), provider_raw)
    provider_name_raw = str(provider_raw.get("name", "mock")).strip().lower() or "mock"
    provider_mode_raw = str(provider_raw.get("mode", "direct")).strip().lower() or "direct"
    if provider_name_raw in {GPT_TRANSPARENT_PROVIDER, GPT_TRANSPARENT_MODE} or provider_mode_raw in {GPT_TRANSPARENT_MODE, GPT_COLOR_KEY_MODE}:
        if provider_mode_raw == GPT_TRANSPARENT_MODE:
            raise PropAssetWorkflowError(
                "gpt_image_transparent_prop is not supported because gpt-image-2 rejects native transparent background. "
                "Use provider.name=gpt_image with provider.mode=gpt_image_prop_color_key and background.mode=color_key."
            )
        provider = {"name": GPT_TRANSPARENT_PROVIDER, "mode": GPT_COLOR_KEY_MODE, "agent_tool": ""}
        model = {"name": requested_model_name or CLI_PROXY_DEFAULT_MODEL}
        warnings = []
    else:
        provider, model, warnings = _normalize_provider_contract(
            provider_name_raw=provider_name_raw,
            provider_mode=provider_mode_raw,
            requested_model_name=requested_model_name,
            provider_agent_tool=str(provider_raw.get("agent_tool", "")).strip().lower(),
        )

    background = _normalize_background(raw.get("background", {}))
    constraints = raw.get("constraints", {})
    if constraints is None:
        constraints = {}
    if not isinstance(constraints, dict):
        raise PropAssetWorkflowError("constraints must be an object when provided.")
    normalized_constraints = {
        "transparent_background": bool(constraints.get("transparent_background", True)),
        "no_text": bool(constraints.get("no_text", True)),
        "no_watermark": bool(constraints.get("no_watermark", True)),
        "no_floor_tile_baked_in": bool(constraints.get("no_floor_tile_baked_in", True)),
        "no_large_cast_shadow": bool(constraints.get("no_large_cast_shadow", True)),
    }

    validation = raw.get("validation", {})
    if validation is None:
        validation = {}
    if not isinstance(validation, dict):
        raise PropAssetWorkflowError("validation must be an object when provided.")
    validation = {"profile": str(validation.get("profile", "prop_engineering_v1")), **validation}

    atlas = raw.get("atlas", {})
    if atlas is None:
        atlas = {}
    if not isinstance(atlas, dict):
        raise PropAssetWorkflowError("atlas must be an object when provided.")

    output_root = resolve_input_path(str(raw.get("output_root", DEFAULT_OUTPUT_ROOT)), base_path=spec_path.parent)
    run_id = str(raw.get("run_id", "")).strip() or slugify(asset_family)

    prompt_parts = _normalize_prompt_parts(raw.get("prompt_parts", {}), asset_family=asset_family)
    generation_canvas = _normalize_generation_canvas(raw.get("generation_canvas", {}), final_canvas={"width": canvas_width, "height": canvas_height})
    return {
        "schema_version": SCHEMA_VERSION,
        "asset_family": asset_family,
        "target_project_folder": target_project_folder,
        "run_id": run_id,
        "output_root": str(output_root),
        "canvas": {"width": canvas_width, "height": canvas_height},
        "generation_canvas": generation_canvas,
        "projection_mode": projection_mode,
        "anchor": {"type": anchor_type, "x": anchor_x, "y": anchor_y},
        "footprint": {"tile_width": tile_width, "tile_height": tile_height},
        "states": states,
        "provider": provider,
        "model": model,
        "background": background,
        "constraints": normalized_constraints,
        "prompt_parts": prompt_parts,
        "validation": validation,
        "atlas": {"enabled": bool(atlas.get("enabled", True)), "padding": int(atlas.get("padding", 0))},
    }, warnings


def run_root_for_spec(spec: dict[str, Any]) -> Path:
    return Path(spec["output_root"]).expanduser().resolve() / spec["run_id"]


def build_run_directories(run_root: Path) -> dict[str, Path]:
    directories = {
        "run_root": run_root,
        "request": run_root / "request",
        "generated": run_root / "generated",
        "processed": run_root / "processed",
        "validation": run_root / "validation",
        "logs": run_root / "logs",
        "step_1_raw": run_root / "step_1_raw",
        "step_3_cleanup_pool": run_root / "step_3_cleanup_pool",
        "deliverables": run_root / "deliverables",
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)
    return directories


def build_prop_generation_prompt(spec: dict[str, Any], *, state: dict[str, Any]) -> str:
    prompt_parts = spec.get("prompt_parts", {})
    constraints = spec.get("constraints", {})
    generation = state.get("generation", {}) if isinstance(state.get("generation"), dict) else {}
    prompt_delta = str(generation.get("prompt_delta", "")).strip()
    role = str(state["role"])
    asset_id = str(state["asset_id"])
    canvas = spec["canvas"]
    generation_canvas = spec.get("generation_canvas", _normalize_generation_canvas({}, final_canvas=canvas))
    anchor = spec["anchor"]
    footprint = spec["footprint"]
    negative = list(prompt_parts.get("negative_constraints", []))
    provider_mode = str(spec.get("provider", {}).get("mode", "")).strip().lower()
    if constraints.get("no_floor_tile_baked_in", True):
        negative.append("do not include any floor diamond, ground tile, platform, shadow blob, or baked-in terrain under the prop")
    if constraints.get("no_text", True):
        negative.append("no letters, symbols, UI labels, captions, or readable text")
    if constraints.get("no_watermark", True):
        negative.append("no watermark, logo, signature, or corner mark")
    if constraints.get("no_large_cast_shadow", True):
        negative.append("no large cast shadow")
    delta_sentence = f" State delta: {prompt_delta}." if prompt_delta else ""
    role_lower = role.lower()
    state_constraint = ""
    if "source" in role_lower or "active" in role_lower:
        state_constraint = (
            " Active-state constraint: preserve the unlit prop body, base, anchor, and silhouette size; "
            "keep any flame/light effect compact and contained, and avoid a tall torch plume or oversized magical column."
        )
    elif "target" in role_lower or "unlit" in role_lower:
        state_constraint = " Unlit-state constraint: no flame plume; only dark coals, dry wood, or a very small ember bed."
    state_view = str(state.get("view", "")).strip()
    state_background = str(state.get("background", "")).strip()
    state_silhouette = str(state.get("silhouette", "")).strip()
    state_style_constraints = list(state.get("style_constraints", [])) if isinstance(state.get("style_constraints"), list) else []
    background = spec.get("background", {}) if isinstance(spec.get("background"), dict) else {}
    background_mode = str(background.get("mode", "color_key")).strip().lower()
    prompt_color = str(background.get("prompt_color", "#FF00FF")).strip().upper() or "#FF00FF"
    derived_aspect_ratio = str(generation_canvas.get("derived_aspect_ratio", _ratio_string(int(canvas["width"]), int(canvas["height"]))))
    source_size = generation_canvas.get("derived_size", canvas)
    source_size_text = _size_string(int(source_size.get("width", canvas["width"])), int(source_size.get("height", canvas["height"])))
    final_canvas_text = f"{canvas['width']}x{canvas['height']}"
    provider = spec.get("provider", {}) if isinstance(spec.get("provider"), dict) else {}
    model = spec.get("model", {}) if isinstance(spec.get("model"), dict) else {}
    provider_adapter = _build_prop_provider_adapter(
        provider_name=str(provider.get("name", "mock")),
        provider_mode=str(provider.get("mode", "direct")).strip().lower() or "direct",
        model_name=str(model.get("name", "mock")),
        generation_canvas=generation_canvas,
    )
    prompt_canvas = provider_adapter.get("generation_canvas", generation_canvas)
    provider_aspect_ratio = str(prompt_canvas.get("provider_aspect_ratio", derived_aspect_ratio))
    provider_size_text = str(prompt_canvas.get("provider_size", source_size_text))
    provider_ratio_value = _ratio_value(provider_aspect_ratio)
    provider_shape_word = "tall" if provider_ratio_value < 0.8 else ("wide" if provider_ratio_value > 1.2 else "square")
    provider_composition_sentence = (
        f"Use a {provider_shape_word} provider composition matching {provider_aspect_ratio} at about {provider_size_text}; "
        f"keep the object suitable for the final {derived_aspect_ratio} {final_canvas_text} sprite."
    )
    if background_mode in {"transparent", "transparent_native"} or provider_mode == GPT_TRANSPARENT_MODE:
        positive_constraints = [
            "one centered object only",
            "transparent background",
            "PNG with alpha channel",
            "no scene",
            "no floor tile",
            "no frame or border",
            "readable at small game scale",
            "2D isometric / three-quarter top-down game prop",
            *state_style_constraints,
        ]
        if state_view:
            positive_constraints.append(f"view: {state_view}")
        if state_background:
            positive_constraints.append(f"background: {state_background}")
        if state_silhouette:
            positive_constraints.append(f"silhouette: {state_silhouette}")
        return (
            f"Generate a high-resolution source image for a final {final_canvas_text} transparent-background game prop for asset_id={asset_id}, role={role}. "
            f"{provider_composition_sentence} Place one centered isometric object with bottom-center anchor intent at ({anchor['x']},{anchor['y']}); footprint is {footprint['tile_width']}x{footprint['tile_height']} tile. "
            "The background must be fully transparent alpha, not white, black, gray, checkerboard, or chroma key. "
            "Do not include a scene, floor tile, platform, frame, UI, text, watermark, or detached cast shadow. "
            f"The factory will normalize the selected source image into the final {final_canvas_text} asset. "
            f"Style direction: {prompt_parts.get('style')}. Material direction: {prompt_parts.get('material')}. Decoration direction: {prompt_parts.get('decoration')}."
            f"{delta_sentence}{state_constraint} "
            f"Required output constraints: {'; '.join(dict.fromkeys(positive_constraints))}. "
            f"Negative constraints: {'; '.join(dict.fromkeys(negative))}."
        ).strip()
    background_sentence = ""
    if background_mode == "color_key":
        fallback = ", ".join(str(color).strip().upper() for color in background.get("fallback_colors", []) if str(color).strip())
        fallback_sentence = f" If {prompt_color} is impossible, use one of these solid fallback background colors: {fallback}." if fallback else ""
        background_sentence = (
            f" Use a perfectly flat solid chroma-key background color {prompt_color} across the entire background; "
            "do not use gradients, shadows, scenery, checkerboard, texture, transparency, floor, frame, or vignette in the background."
            f"{fallback_sentence}"
        )
    return (
        f"Generate a high-resolution source image for a final {final_canvas_text} isometric game prop/object asset PNG for asset_id={asset_id}, role={role}. "
        f"{provider_composition_sentence} Place one centered prop with bottom-center anchor intent at ({anchor['x']},{anchor['y']}); footprint is {footprint['tile_width']}x{footprint['tile_height']} tile. "
        "The object should stand alone as a cutout-ready sprite and must not include a baked floor tile. "
        f"{background_sentence} "
        f"The factory will crop, clean, and normalize the selected candidate into the final {final_canvas_text} asset. "
        f"Style direction: {prompt_parts.get('style')}. Material direction: {prompt_parts.get('material')}. Decoration direction: {prompt_parts.get('decoration')}."
        f"{delta_sentence}{state_constraint} "
        f"Negative constraints: {'; '.join(dict.fromkeys(negative))}."
    ).strip()


def prepare_prop_asset_run(spec_path: Path) -> dict[str, Any]:
    spec, warnings = load_and_validate_prop_spec(spec_path)
    run_root = run_root_for_spec(spec)
    directories = build_run_directories(run_root)
    prompts: dict[str, str] = {}
    prompt_paths: dict[str, str] = {}
    expected_outputs: dict[str, str] = {}
    generation_plan: dict[str, Any] = {}
    generation_canvas = spec["generation_canvas"]
    for state in spec["states"]:
        asset_id = state["asset_id"]
        prompt_text = build_prop_generation_prompt(spec, state=state)
        prompt_path = directories["request"] / f"prompt_{asset_id}.txt"
        prompt_path.write_text(prompt_text + "\n", encoding="utf-8")
        prompts[asset_id] = prompt_text
        prompt_paths[asset_id] = str(prompt_path)
        expected_outputs[asset_id] = str(directories["generated"] / f"{asset_id}.png")
        generation = state.get("generation", {}) if isinstance(state.get("generation"), dict) else {}
        generation_plan[asset_id] = {
            "asset_id": asset_id,
            "role": state.get("role"),
            "generation_mode": generation.get("mode", "base"),
            "source_asset_id": generation.get("source_asset_id", ""),
            "prompt_path": str(prompt_path),
            "expected_raw_output_path": str(directories["generated"] / f"{asset_id}.raw.png"),
            "expected_clean_output_path": str(directories["processed"] / f"{asset_id}.keyed.03_balanced.png")
            if spec.get("background", {}).get("mode") == "color_key"
            else "",
            "expected_validated_output_path": str(directories["generated"] / f"{asset_id}.png")
            if spec.get("background", {}).get("mode") == "transparent_native"
            else str(directories["processed"] / f"{asset_id}.normalized.png"),
            "generation_canvas": generation_canvas,
            "reference_image_path": None,
            "reference_image_resolution": "resolved at generation time for edit_from states",
        }
    request_payload = {
        **spec,
        "prepared_at": now_iso(),
        "spec_path": str(spec_path.resolve()),
        "prompts": prompts,
        "prompt_paths": prompt_paths,
        "expected_outputs": expected_outputs,
        "generation_plan": generation_plan,
        "warnings": warnings,
    }
    write_json(directories["request"] / "request.json", request_payload)
    if spec.get("provider", {}).get("mode") == "agent_handoff":
        write_json(
            directories["request"] / "prop_agent_handoff.json",
            {
                "schema_version": "prop_agent_handoff_v1",
                "status": "unsupported",
                "message": "prop_asset_workflow_v1 currently supports mock and direct providers only. agent_handoff is intentionally not supported yet.",
                "asset_family": spec["asset_family"],
                "states": spec["states"],
                "prompts": prompts,
                "generation_plan": generation_plan,
                "background": spec["background"],
                "canvas": spec["canvas"],
                "generation_canvas": spec["generation_canvas"],
                "anchor": spec["anchor"],
                "footprint": spec["footprint"],
                "expected_agent_output_dir": str(run_root / "agent_handoff" / "step_1_raw"),
            },
        )
    write_json(directories["logs"] / "prepare.json", {"ok": True, "prepared_at": now_iso(), "warnings": warnings})
    return {
        "run_root": str(run_root),
        "asset_family": spec["asset_family"],
        "states": spec["states"],
        "request_path": str(directories["request"] / "request.json"),
        "prompt_paths": prompt_paths,
        "warnings": warnings,
    }


def _mock_prop_image(spec: dict[str, Any], *, state: dict[str, Any], background: dict[str, Any]) -> Image.Image:
    width = int(spec["canvas"]["width"])
    height = int(spec["canvas"]["height"])
    prop = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(prop)
    active = "active" in str(state.get("role", "")).lower() or "source" in str(state.get("role", "")).lower()
    asset_family = str(spec.get("asset_family", "")).lower()
    if "field_cooking" in asset_family or "campfire_pot" in asset_family:
        iron_dark = (45, 39, 34, 255)
        iron_mid = (82, 72, 62, 255)
        iron_hi = (142, 126, 100, 255)
        wood = (98, 58, 31, 255)
        stone = (100, 92, 80, 255)
        # Tripod and chain.
        draw.line((64, 50, 24, 255), fill=iron_mid, width=5)
        draw.line((64, 50, 108, 255), fill=iron_mid, width=5)
        draw.line((64, 50, 64, 142), fill=iron_dark, width=3)
        draw.ellipse((54, 37, 74, 59), outline=iron_hi, width=4)
        for y in range(70, 130, 13):
            draw.ellipse((60, y, 68, y + 10), outline=iron_hi, width=2)
        # Pot.
        draw.ellipse((37, 134, 91, 179), fill=(54, 50, 46, 255), outline=iron_dark, width=3)
        draw.rectangle((39, 151, 89, 176), fill=(54, 50, 46, 255))
        draw.arc((37, 126, 91, 162), start=0, end=180, fill=iron_hi, width=3)
        # Fire ring / wood, bottom-anchored.
        for box in [(31, 223, 47, 239), (48, 214, 64, 230), (66, 214, 82, 230), (84, 223, 100, 239), (37, 238, 55, 255), (72, 238, 90, 255)]:
            draw.rounded_rectangle(box, radius=3, fill=stone, outline=(55, 50, 45, 255), width=2)
        draw.line((43, 225, 84, 250), fill=wood, width=7)
        draw.line((86, 225, 43, 250), fill=wood, width=7)
        if active:
            draw.polygon([(64, 183), (48, 225), (80, 225)], fill=(244, 91, 20, 255))
            draw.polygon([(64, 193), (54, 225), (73, 225)], fill=(255, 213, 63, 255))
            draw.arc((51, 107, 63, 139), start=250, end=70, fill=(190, 180, 165, 165), width=2)
            draw.arc((68, 103, 80, 139), start=250, end=70, fill=(190, 180, 165, 130), width=2)
        else:
            draw.ellipse((52, 205, 76, 221), fill=(48, 40, 33, 255))
            draw.point((64, 213), fill=(180, 72, 28, 255))
    else:
        # Brazier body, deliberately centered and bottom-anchored for validator tests.
        bronze_dark = (72, 45, 26, 255)
        bronze_mid = (126, 78, 38, 255)
        bronze_hi = (190, 128, 58, 255)
        draw.ellipse((33, 164, 95, 205), fill=bronze_mid, outline=bronze_dark, width=3)
        draw.rectangle((39, 180, 89, 203), fill=bronze_mid)
        draw.arc((33, 153, 95, 191), start=0, end=180, fill=bronze_hi, width=4)
        draw.rectangle((58, 202, 70, 239), fill=bronze_dark)
        draw.polygon([(49, 239), (79, 239), (89, 255), (39, 255)], fill=bronze_dark)
        draw.line((48, 205, 35, 252), fill=bronze_dark, width=5)
        draw.line((80, 205, 93, 252), fill=bronze_dark, width=5)
        if active:
            draw.polygon([(64, 128), (49, 166), (79, 166)], fill=(255, 118, 26, 255))
            draw.polygon([(64, 140), (54, 167), (73, 167)], fill=(255, 214, 72, 255))
            draw.ellipse((52, 149, 76, 181), fill=(255, 154, 34, 230))
        else:
            draw.ellipse((48, 157, 80, 179), fill=(45, 40, 36, 255))
            draw.arc((50, 156, 78, 176), start=0, end=180, fill=(95, 80, 70, 255), width=2)
    generation_size = (
        int(spec.get("generation_canvas", {}).get("derived_size", {}).get("width", width)),
        int(spec.get("generation_canvas", {}).get("derived_size", {}).get("height", height)),
    )
    if background.get("mode") == "color_key":
        bg_rgb = parse_hex_color(str(background.get("prompt_color", "#FF00FF")))
        image = Image.new("RGBA", generation_size, (*bg_rgb, 255))
    else:
        image = Image.new("RGBA", generation_size, (0, 0, 0, 0))
    paste_x = (generation_size[0] - prop.width) // 2
    paste_y = generation_size[1] - prop.height
    image.alpha_composite(prop, (paste_x, paste_y))
    return image


def _copy_artifact(source: Path, destination: Path) -> str | None:
    if not source.exists():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return str(destination)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _sample_corner_background_colors(image_path: Path, *, sample_size: int = 24) -> list[str]:
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size
    corners = [
        (0, 0, min(sample_size, width), min(sample_size, height)),
        (max(0, width - sample_size), 0, width, min(sample_size, height)),
        (0, max(0, height - sample_size), min(sample_size, width), height),
        (max(0, width - sample_size), max(0, height - sample_size), width, height),
    ]
    colors: list[str] = []
    seen: set[str] = set()
    for box in corners:
        crop = image.crop(box)
        crop_pixels = crop.load()
        pixels = [
            crop_pixels[x, y]
            for y in range(crop.height)
            for x in range(crop.width)
        ]
        opaque_pixels = [(r, g, b) for r, g, b, a in pixels if a >= 128]
        if not opaque_pixels:
            continue
        red = round(sum(pixel[0] for pixel in opaque_pixels) / len(opaque_pixels))
        green = round(sum(pixel[1] for pixel in opaque_pixels) / len(opaque_pixels))
        blue = round(sum(pixel[2] for pixel in opaque_pixels) / len(opaque_pixels))
        color = _rgb_to_hex((red, green, blue))
        if color not in seen:
            colors.append(color)
            seen.add(color)
    return colors


def _write_step1_artifact(run_root: Path, *, asset_id: str, raw_image_path: Path) -> None:
    copied = _copy_artifact(raw_image_path, run_root / "step_1_raw" / f"s1_raw.{asset_id}{raw_image_path.suffix}")
    update_step_status_summary(
        run_root,
        variant=asset_id,
        step_key="step_1_raw",
        status="ok" if copied else "missing_output",
        summary="raw prop generation output written" if copied else "raw prop generation output missing",
        primary_artifact=copied,
        details_path=None,
    )


def _cleanup_prop_raw(run_root: Path, *, asset_id: str, raw_path: Path, background: dict[str, Any]) -> Path:
    keyed_output_path = run_root / "processed" / f"{asset_id}.keyed.png"
    fallback_colors = list(background.get("fallback_colors", ["#00FF00"]))
    auto_corner_colors = _sample_corner_background_colors(raw_path)
    for color in auto_corner_colors:
        if color not in fallback_colors:
            fallback_colors.append(color)
    preprocessing = apply_color_key_to_image(
        raw_path,
        keyed_output_path,
        prompt_color=str(background.get("prompt_color", "#FF00FF")),
        fallback_colors=fallback_colors,
        tolerance=int(background.get("tolerance", 24)),
        emit_variant_pool=True,
        remove_all_key_pixels=True,
    )
    candidates: list[dict[str, Any]] = []
    variants_payload = preprocessing.get("variants", {})
    if isinstance(variants_payload, dict):
        for cleanup_name, payload in variants_payload.items():
            if not isinstance(payload, dict) or not payload.get("output"):
                continue
            source = Path(str(payload["output"]))
            cleanup_id = _cleanup_artifact_token(str(cleanup_name))
            copied = _copy_artifact(source, run_root / "step_3_cleanup_pool" / f"s3_cleanup.{asset_id}.{cleanup_id}{source.suffix}")
            candidates.append({"cleanup_id": cleanup_id, "path": copied or str(source), "label": payload.get("label")})
    write_json(
        run_root / "step_3_cleanup_pool" / f"s3_cleanup.{asset_id}.json",
        {
            "asset_id": asset_id,
            "active_key_color": preprocessing.get("active_key_color"),
            "auto_corner_background_colors": auto_corner_colors,
            "removed_background_pixels": preprocessing.get("removed_background_pixels"),
            "candidates": candidates,
        },
    )
    scorer_key_colors = [str(background.get("prompt_color", "#FF00FF")), *fallback_colors]
    active_key_color = preprocessing.get("active_key_color")
    if isinstance(active_key_color, str) and active_key_color.strip() and active_key_color not in scorer_key_colors:
        scorer_key_colors.append(active_key_color)
    score_path = run_root / "step_3_cleanup_pool" / f"prop_cleanup_score.{asset_id}.json"
    scoring = score_cleanup_candidates(
        raw_path=raw_path,
        candidates=candidates,
        key_colors=scorer_key_colors,
        tolerance=int(background.get("tolerance", 24)),
        output_path=score_path,
    )
    selected_path_raw = scoring.get("selected_path")
    update_step_status_summary(
        run_root,
        variant=asset_id,
        step_key="step_3_cleanup_pool",
        status="ok" if candidates else "empty",
        summary=f"{len(candidates)} prop cleanup candidates exported; selected {scoring.get('selected_cleanup_id') or 'none'} by pixel-change score",
        primary_artifact=str(selected_path_raw) if selected_path_raw else (candidates[0]["path"] if candidates else None),
        details_path=str(score_path),
    )
    if selected_path_raw:
        return Path(str(selected_path_raw))
    return default_cleanup_candidate_path(preprocessing)


def _write_base_reference_guide(run_root: Path, *, spec: dict[str, Any], asset_id: str) -> Path:
    """Small engineering guide used only when a direct provider requires an input image."""
    width = int(spec.get("generation_canvas", {}).get("derived_size", {}).get("width", spec["canvas"]["width"]))
    height = int(spec.get("generation_canvas", {}).get("derived_size", {}).get("height", spec["canvas"]["height"]))
    anchor = spec["anchor"]
    canvas_width = int(spec["canvas"]["width"])
    canvas_height = int(spec["canvas"]["height"])
    scale_x = width / float(max(1, canvas_width))
    scale_y = height / float(max(1, canvas_height))
    anchor_x = int(round(int(anchor.get("x", canvas_width // 2)) * scale_x))
    anchor_y = int(round(int(anchor.get("y", canvas_height - 1)) * scale_y))
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        (
            int(round(28 * scale_x)),
            int(round(120 * scale_y)),
            int(round(100 * scale_x)),
            int(round(254 * scale_y)),
        ),
        outline=(80, 160, 255, 180),
        width=max(1, int(round(scale_x))),
    )
    draw.ellipse(
        (
            int(round(36 * scale_x)),
            int(round(164 * scale_y)),
            int(round(92 * scale_x)),
            int(round(204 * scale_y)),
        ),
        outline=(255, 180, 80, 220),
        width=max(1, int(round(2 * scale_x))),
    )
    guide_span = max(8, int(round(8 * scale_x)))
    guide_height = max(8, int(round(8 * scale_y)))
    draw.line((anchor_x - guide_span, anchor_y, anchor_x + guide_span, anchor_y), fill=(80, 160, 255, 220), width=1)
    draw.line((anchor_x, anchor_y - guide_height, anchor_x, anchor_y), fill=(80, 160, 255, 220), width=1)
    output_path = run_root / "request" / "reference_guides" / f"{asset_id}_engineering_guide.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path




def _assert_native_transparency(source_path: Path) -> None:
    """Reject provider outputs that only simulate transparency in RGB pixels."""
    image = Image.open(source_path)
    if image.mode != "RGBA":
        raise PropAssetWorkflowError(f"native transparent provider returned {image.mode} image instead of RGBA: {source_path}")
    alpha = image.getchannel("A")
    if alpha.getextrema() == (255, 255):
        raise PropAssetWorkflowError(f"native transparent provider returned fully opaque alpha: {source_path}")
    corner_size = max(1, min(image.width, image.height, 32))
    corners = [
        alpha.crop((0, 0, corner_size, corner_size)),
        alpha.crop((image.width - corner_size, 0, image.width, corner_size)),
        alpha.crop((0, image.height - corner_size, corner_size, image.height)),
        alpha.crop((image.width - corner_size, image.height - corner_size, image.width, image.height)),
    ]
    max_corner_alpha_mean = max(sum(corner.getdata()) / (corner.width * corner.height) for corner in corners)
    if max_corner_alpha_mean > 8.0:
        raise PropAssetWorkflowError(
            f"native transparent provider returned non-transparent canvas corners: {source_path}"
        )

def _normalize_prop_canvas(
    run_root: Path,
    *,
    asset_id: str,
    source_path: Path,
    spec: dict[str, Any],
) -> Path:
    """Place provider output on the requested prop canvas without hand editing."""
    target_width = int(spec["canvas"]["width"])
    target_height = int(spec["canvas"]["height"])
    anchor = spec["anchor"]
    anchor_x = int(anchor.get("x", target_width // 2))
    anchor_y = int(anchor.get("y", target_height - 1))
    image = Image.open(source_path).convert("RGBA")
    bbox = image.getchannel("A").point(lambda value: 255 if value >= 32 else 0, mode="L").getbbox()
    canvas = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
    if bbox is None:
        output_path = run_root / "processed" / f"{asset_id}.normalized.png"
        canvas.save(output_path)
        return output_path
    crop = image.crop(bbox)
    side_margin = int(spec.get("validation", {}).get("min_side_margin_px", 3))
    max_width = max(1, target_width - 2 * side_margin - 1)
    max_height = max(1, target_height - int(spec.get("validation", {}).get("min_top_margin_px", 3)))
    scale = min(max_width / crop.width, max_height / crop.height, 1.0)
    new_size = (max(1, int(round(crop.width * scale))), max(1, int(round(crop.height * scale))))
    if new_size != crop.size:
        crop = crop.resize(new_size, Image.Resampling.LANCZOS)
    paste_x = int(round(anchor_x - (crop.width - 1) / 2.0))
    paste_y = int(round(anchor_y - (crop.height - 1)))
    canvas.alpha_composite(crop, (paste_x, paste_y))
    output_path = run_root / "processed" / f"{asset_id}.normalized.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return output_path


def _state_reference_images(state: dict[str, Any], final_outputs: dict[str, Path]) -> list[Path]:
    generation = state.get("generation", {}) if isinstance(state.get("generation"), dict) else {}
    if generation.get("mode") != "edit_from":
        return []
    source_asset_id = str(generation.get("source_asset_id", "")).strip()
    if not source_asset_id:
        return []
    source_path = final_outputs.get(source_asset_id)
    return [source_path] if source_path is not None else []


def _provider_reference_images(
    *,
    provider_name: str,
    run_root: Path,
    state: dict[str, Any],
    final_outputs: dict[str, Path],
    spec: dict[str, Any],
) -> list[Path]:
    reference_images = _state_reference_images(state, final_outputs)
    if reference_images:
        return reference_images
    if provider_name == "gemini_cli":
        return [_write_base_reference_guide(run_root, spec=spec, asset_id=str(state["asset_id"]))]
    return []


def _write_provider_request_payload(
    run_root: Path,
    *,
    asset_id: str,
    provider_name: str,
    backend_provider_name: str,
    model_name: str,
    prompt_text: str,
    reference_images: Sequence[Path],
    output_path: Path,
    background: dict[str, Any],
    generation_canvas: dict[str, Any],
    adapter_decision: dict[str, Any],
    provider_generation_args: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "asset_id": asset_id,
        "provider": provider_name,
        "backend_provider": backend_provider_name,
        "model": model_name,
        "prompt": prompt_text,
        "reference_images": [str(path) for path in reference_images],
        "output_path": str(output_path),
        "final_canvas": generation_canvas.get("final_canvas", {}),
        "generation_aspect_ratio": generation_canvas.get("derived_aspect_ratio"),
        "generation_size_hint": generation_canvas.get("derived_size", {}),
        "background": background,
        "generation_canvas": generation_canvas,
        "adapter_decision": adapter_decision,
        "provider_generation_args": provider_generation_args,
    }
    write_json(run_root / "request" / f"provider_request_{asset_id}.json", payload)
    return payload


def generate_prop_assets(spec_path: Path) -> dict[str, Any]:
    prepare_result = prepare_prop_asset_run(spec_path)
    run_root = Path(prepare_result["run_root"])
    request_payload = load_json(run_root / "request" / "request.json")
    provider = request_payload.get("provider", {})
    provider_name = str(provider.get("name", "mock"))
    provider_mode = str(provider.get("mode", "direct")).strip().lower() or "direct"
    model_name = str(request_payload.get("model", {}).get("name", "mock"))
    background = request_payload.get("background", {})
    generation_canvas = request_payload.get("generation_canvas", _normalize_generation_canvas({}, final_canvas=request_payload["canvas"]))
    provider_adapter = _build_prop_provider_adapter(
        provider_name=provider_name,
        provider_mode=provider_mode,
        model_name=model_name,
        generation_canvas=generation_canvas,
    )
    transparent_native = background.get("mode") == "transparent_native" or provider_mode == GPT_TRANSPARENT_MODE
    if provider_mode == "agent_handoff":
        raise PropAssetWorkflowError("prop asset workflow does not implement agent_handoff yet; use provider.mode=direct or mock for the first vertical slice.")

    generation_logs: dict[str, Any] = {}
    provider_requests: dict[str, Any] = {}
    final_outputs: dict[str, Path] = {}
    for state in request_payload["states"]:
        asset_id = state["asset_id"]
        raw_path = run_root / "generated" / f"{asset_id}.raw.png"
        transparent_output_path = run_root / "generated" / f"{asset_id}.png"
        if provider_name == "mock":
            image = _mock_prop_image(request_payload, state=state, background=background)
            output_path = raw_path if background.get("mode") == "color_key" else transparent_output_path
            image.save(output_path)
            generation_logs[asset_id] = {
                "provider": "mock",
                "output_path": str(output_path),
                "generation_canvas": provider_adapter["generation_canvas"],
                "adapter_decision": provider_adapter["adapter_decision"],
            }
            provider_requests[asset_id] = _write_provider_request_payload(
                run_root,
                asset_id=asset_id,
                provider_name=provider_name,
                backend_provider_name=provider_adapter["backend_provider_name"],
                model_name=model_name,
                prompt_text=str(request_payload["prompts"][asset_id]),
                reference_images=_state_reference_images(state, final_outputs),
                output_path=output_path,
                background=background,
                generation_canvas=provider_adapter["generation_canvas"],
                adapter_decision=provider_adapter["adapter_decision"],
                provider_generation_args=provider_adapter["provider_generation_args"],
            )
        else:
            reference_images = _provider_reference_images(
                provider_name=provider_name,
                run_root=run_root,
                state=state,
                final_outputs=final_outputs,
                spec=request_payload,
            )
            output_path = raw_path if background.get("mode") == "color_key" else transparent_output_path
            backend_provider_name = str(provider_adapter["backend_provider_name"])
            provider_requests[asset_id] = _write_provider_request_payload(
                run_root,
                asset_id=asset_id,
                provider_name=provider_name,
                backend_provider_name=backend_provider_name,
                model_name=model_name,
                prompt_text=str(request_payload["prompts"][asset_id]),
                reference_images=reference_images,
                output_path=output_path,
                background=background,
                generation_canvas=provider_adapter["generation_canvas"],
                adapter_decision=provider_adapter["adapter_decision"],
                provider_generation_args=provider_adapter["provider_generation_args"],
            )
            try:
                generation_logs[asset_id] = generate_with_provider(
                    provider_name=backend_provider_name,
                    model_name=model_name,
                    prompt_text=str(request_payload["prompts"][asset_id]),
                    reference_images=reference_images,
                    output_path=output_path,
                    transparent_background=transparent_native,
                    size_override=str(provider_adapter["provider_generation_args"].get("size", "")) or None,
                    aspect_ratio_override=str(provider_adapter["provider_generation_args"].get("aspect_ratio", "")) or None,
                    image_size_override=str(provider_adapter["provider_generation_args"].get("image_size", "")) or None,
                )
                generation_logs[asset_id]["generation_canvas"] = provider_adapter["generation_canvas"]
                generation_logs[asset_id]["adapter_decision"] = provider_adapter["adapter_decision"]
            except Exception as error:
                write_json(run_root / "request" / "provider_requests.json", provider_requests)
                write_json(
                    run_root / "logs" / "generate_error.json",
                    {
                        "ok": False,
                        "failed_at": now_iso(),
                        "asset_id": asset_id,
                        "provider": provider_name,
                        "backend_provider": backend_provider_name,
                        "model": model_name,
                        "error": str(error),
                        "provider_requests": provider_requests,
                        "generation": generation_logs,
                    },
                )
                raise
        _write_step1_artifact(run_root, asset_id=asset_id, raw_image_path=output_path)
        if background.get("mode") == "color_key":
            cleaned_path = _cleanup_prop_raw(run_root, asset_id=asset_id, raw_path=raw_path, background=background)
            final_outputs[asset_id] = _normalize_prop_canvas(
                run_root,
                asset_id=asset_id,
                source_path=cleaned_path,
                spec=request_payload,
            )
        elif transparent_native:
            _assert_native_transparency(transparent_output_path)
            final_outputs[asset_id] = _normalize_prop_canvas(
                run_root,
                asset_id=asset_id,
                source_path=transparent_output_path,
                spec=request_payload,
            )
        else:
            final_outputs[asset_id] = _normalize_prop_canvas(
                run_root,
                asset_id=asset_id,
                source_path=transparent_output_path,
                spec=request_payload,
            )

    write_json(run_root / "request" / "provider_requests.json", provider_requests)
    validation = validate_prop_asset_run(run_root, asset_paths=final_outputs)
    deliverables = None
    if validation["ok"]:
        deliverables = write_prop_deliverables(run_root, spec=request_payload, asset_paths=final_outputs, validation=validation)
    write_json(
        run_root / "logs" / "generate.json",
        {
            "ok": bool(validation["ok"]),
            "generated_at": now_iso(),
            "generation": generation_logs,
            "provider_requests": provider_requests,
            "validation": validation,
            "deliverables": deliverables,
        },
    )
    return {
        "ok": bool(validation["ok"]),
        "run_root": str(run_root),
        "asset_family": request_payload["asset_family"],
        "outputs": {asset_id: str(path) for asset_id, path in final_outputs.items()},
        "validation": validation,
        "deliverables": deliverables,
    }


def _default_asset_path_for_run(run_root: Path, *, asset_id: str, background: dict[str, Any]) -> Path:
    if background.get("mode") == "color_key":
        normalized = run_root / "processed" / f"{asset_id}.normalized.png"
        if normalized.exists():
            return normalized
        default_name = "03_balanced"
        candidate = run_root / "processed" / f"{asset_id}.keyed.{default_name}.png"
        if candidate.exists():
            return candidate
    normalized = run_root / "processed" / f"{asset_id}.normalized.png"
    if normalized.exists():
        return normalized
    return run_root / "generated" / f"{asset_id}.png"


def validate_prop_asset_run(run_root: Path, *, asset_paths: dict[str, Path] | None = None) -> dict[str, Any]:
    request_payload = load_json(run_root / "request" / "request.json")
    background = request_payload.get("background", {})
    normalized_paths = dict(asset_paths or {})
    for state in request_payload.get("states", []):
        asset_id = str(state.get("asset_id", ""))
        if asset_id and asset_id not in normalized_paths:
            normalized_paths[asset_id] = _default_asset_path_for_run(run_root, asset_id=asset_id, background=background)
    try:
        result = validate_prop_asset_set(spec=request_payload, asset_paths=normalized_paths, output_dir=run_root / "validation")
    except PropValidationError as error:
        raise PropAssetWorkflowError(str(error)) from error
    for asset_id, asset_result in result.get("assets", {}).items():
        update_step_status_summary(
            run_root,
            variant=asset_id,
            step_key="validation",
            status="pass" if asset_result.get("status") == "pass" else "fail",
            summary="prop engineering validation passed" if asset_result.get("status") == "pass" else "prop engineering validation failed",
            primary_artifact=asset_result.get("debug_overlay"),
            details_path=str(run_root / "validation" / "validation_summary.json"),
        )
    write_json(run_root / "logs" / "validate.json", {"ok": result["ok"], "validated_at": now_iso(), "status": result["status"]})
    return result


def _draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str) -> None:
    try:
        draw.text(xy, text, fill=(255, 255, 255, 255))
    except Exception:
        pass


def write_preview_sheet(deliverables_dir: Path, *, spec: dict[str, Any], asset_paths: dict[str, Path]) -> str:
    width = int(spec["canvas"]["width"])
    height = int(spec["canvas"]["height"])
    label_h = 32
    padding = 8
    sheet_width = len(asset_paths) * width + max(0, len(asset_paths) - 1) * padding
    sheet = Image.new("RGBA", (sheet_width, height + label_h), (32, 32, 32, 255))
    draw = ImageDraw.Draw(sheet)
    x = 0
    for state in spec["states"]:
        asset_id = state["asset_id"]
        path = asset_paths[asset_id]
        _draw_label(draw, (x + 4, 8), str(state.get("role", asset_id))[:22])
        image = Image.open(path).convert("RGBA")
        sheet.alpha_composite(image, (x, label_h))
        x += width + padding
    output_path = deliverables_dir / "preview_sheet.png"
    sheet.save(output_path)
    return str(output_path)


def write_atlas(deliverables_dir: Path, *, spec: dict[str, Any], asset_paths: dict[str, Path]) -> dict[str, Any]:
    width = int(spec["canvas"]["width"])
    height = int(spec["canvas"]["height"])
    padding = int(spec.get("atlas", {}).get("padding", 0))
    columns = len(asset_paths)
    atlas_width = columns * width + max(0, columns - 1) * padding
    atlas = Image.new("RGBA", (atlas_width, height), (0, 0, 0, 0))
    entries: list[dict[str, Any]] = []
    x = 0
    for index, state in enumerate(spec["states"]):
        asset_id = state["asset_id"]
        path = asset_paths[asset_id]
        image = Image.open(path).convert("RGBA")
        atlas.alpha_composite(image, (x, 0))
        entries.append(
            {
                "asset_id": asset_id,
                "role": state.get("role"),
                "atlas_index": index,
                "atlas_x": x,
                "atlas_y": 0,
                "atlas_w": width,
                "atlas_h": height,
                "atlas_rect": {"x": x, "y": 0, "w": width, "h": height},
                "anchor": spec["anchor"],
                "footprint": spec["footprint"],
            }
        )
        x += width + padding
    atlas_path = deliverables_dir / "prop_asset_atlas.png"
    atlas.save(atlas_path)
    metadata = {
        "schema_version": ATLAS_METADATA_SCHEMA_VERSION,
        "asset_family": spec["asset_family"],
        "atlas_path": str(atlas_path),
        "tile_width": width,
        "tile_height": height,
        "padding": padding,
        "columns": columns,
        "rows": 1,
        "tile_asset_registry_compat": True,
        "entries": entries,
    }
    metadata_path = deliverables_dir / "prop_asset_atlas_metadata.json"
    write_json(metadata_path, metadata)
    return {"atlas_path": str(atlas_path), "metadata_path": str(metadata_path), "metadata": metadata}


def write_imt_prop_handoff(
    deliverables_dir: Path,
    *,
    spec: dict[str, Any],
    validation: dict[str, Any],
    atlas_payload: dict[str, Any] | None,
) -> str:
    atlas_metadata = atlas_payload.get("metadata") if isinstance(atlas_payload, dict) else None
    atlas_entries = {
        str(entry.get("asset_id")): entry
        for entry in (atlas_metadata or {}).get("entries", [])
        if isinstance(entry, dict)
    }
    atlas_path = deliverables_dir / "prop_asset_atlas.png"
    atlas_block: dict[str, Any] | None = None
    if atlas_path.exists():
        with Image.open(atlas_path) as atlas_image:
            atlas_block = {
                "path": atlas_path.name,
                "width": atlas_image.width,
                "height": atlas_image.height,
            }

    assets: list[dict[str, Any]] = []
    for state in spec["states"]:
        asset_id = state["asset_id"]
        entry = atlas_entries.get(asset_id, {})
        rect = entry.get("atlas_rect") or {
            "x": entry.get("atlas_x", 0),
            "y": entry.get("atlas_y", 0),
            "w": entry.get("atlas_w", spec["canvas"]["width"]),
            "h": entry.get("atlas_h", spec["canvas"]["height"]),
        }
        asset_validation = validation.get("assets", {}).get(asset_id, {})
        assets.append(
            {
                "asset_id": asset_id,
                "role": state.get("role"),
                "file": f"{asset_id}.png",
                "atlas_rect": rect,
                "anchor": spec["anchor"],
                "footprint": spec["footprint"],
                "validation_status": asset_validation.get("status"),
            }
        )

    handoff = {
        "schema_version": IMT_HANDOFF_SCHEMA_VERSION,
        "asset_family": spec["asset_family"],
        **({"target_project_folder": spec.get("target_project_folder")} if spec.get("target_project_folder") else {}),
        "generation_provider": "gpt_image" if spec.get("provider", {}).get("mode") == GPT_TRANSPARENT_MODE else spec.get("provider", {}).get("name"),
        "background_mode": "transparent_native" if spec.get("background", {}).get("mode") == "transparent_native" else spec.get("background", {}).get("mode"),
        "alpha_validated": bool(validation.get("ok")) and spec.get("background", {}).get("mode") in {"transparent", "transparent_native", "color_key"},
        "atlas": atlas_block,
        "assets": assets,
    }
    handoff_path = deliverables_dir / "imt_prop_handoff.json"
    write_json(handoff_path, handoff)
    return str(handoff_path)


def write_prop_deliverables(
    run_root: Path,
    *,
    spec: dict[str, Any],
    asset_paths: dict[str, Path],
    validation: dict[str, Any],
) -> dict[str, Any]:
    deliverables_dir = run_root / "deliverables"
    deliverables_dir.mkdir(parents=True, exist_ok=True)
    copied_assets: dict[str, Path] = {}
    manifest_assets: list[dict[str, Any]] = []
    for state in spec["states"]:
        asset_id = state["asset_id"]
        source = asset_paths[asset_id]
        destination = deliverables_dir / f"{asset_id}.png"
        shutil.copy2(source, destination)
        copied_assets[asset_id] = destination
        asset_validation = validation.get("assets", {}).get(asset_id, {})
        manifest_assets.append(
            {
                "asset_id": asset_id,
                "role": state.get("role"),
                "file": str(destination),
                "file_name": destination.name,
                "width": spec["canvas"]["width"],
                "height": spec["canvas"]["height"],
                "projection_mode": spec["projection_mode"],
                "anchor": spec["anchor"],
                "footprint": spec["footprint"],
                "bbox": asset_validation.get("bbox"),
                "validation_status": asset_validation.get("status"),
            }
        )
        update_step_status_summary(
            run_root,
            variant=asset_id,
            step_key="deliverable",
            status="ok",
            summary="prop deliverable written",
            primary_artifact=str(destination),
            details_path=str(deliverables_dir / "prop_asset_manifest.json"),
        )
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "asset_family": spec["asset_family"],
        **({"target_project_folder": spec.get("target_project_folder")} if spec.get("target_project_folder") else {}),
        "projection_mode": spec["projection_mode"],
        "canvas": spec["canvas"],
        "anchor": spec["anchor"],
        "footprint": spec["footprint"],
        "constraints": spec.get("constraints", {}),
        "assets": manifest_assets,
    }
    manifest_path = deliverables_dir / "prop_asset_manifest.json"
    write_json(manifest_path, manifest)
    validation_path = deliverables_dir / "validation_summary.json"
    write_json(validation_path, validation)
    preview_path = write_preview_sheet(deliverables_dir, spec=spec, asset_paths=copied_assets)
    atlas_payload = None
    if spec.get("atlas", {}).get("enabled", True):
        atlas_payload = write_atlas(deliverables_dir, spec=spec, asset_paths=copied_assets)
    imt_handoff_path = write_imt_prop_handoff(
        deliverables_dir,
        spec=spec,
        validation=validation,
        atlas_payload=atlas_payload,
    )
    return {
        "deliverables_dir": str(deliverables_dir),
        "manifest_path": str(manifest_path),
        "validation_summary_path": str(validation_path),
        "preview_sheet_path": preview_path,
        "imt_prop_handoff_path": imt_handoff_path,
        "assets": {asset_id: str(path) for asset_id, path in copied_assets.items()},
        "atlas": atlas_payload,
    }
