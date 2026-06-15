from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from email.generator import _make_boundary
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from pipeline.credentials import CredentialError, build_gemini_provider_env

REPO_ROOT = Path(__file__).resolve().parents[1]
NANO_BANANA_ROOT = (REPO_ROOT.parent / "nano_banana").resolve()
NANO_BANANA_SCRIPT = NANO_BANANA_ROOT / "scripts" / "generate_image.js"
CLI_PROXY_API_CONFIG_PATH = Path("~/.cli-proxy-api/config.yaml").expanduser()
CLI_PROXY_DEFAULT_BASE_URL = "http://127.0.0.1:8317/v1"
CLI_PROXY_DEFAULT_API_KEY = "local-dev-image-key"
CLI_PROXY_DEFAULT_MODEL = "gpt-image-2"
SCHEMA_VERSION = "reference_pair_workflow_v1"
SUPPORTED_DIRECT_PROVIDERS = {"mock", "gemini_cli", "cliproxyapi", "nano_banana", "nano_banana_pro", "gpt_image_2", "imagegen"}
SUPPORTED_AGENT_HANDOFF_PROVIDERS = {"agent_handoff", "imagegen", "imagegen_handoff"}
SUPPORTED_PROVIDER_MODES = {"direct", "agent_handoff"}
SUPPORTED_CONVERSION_MODES = {"none", "transform"}
PROVIDER_MODEL_FAMILIES = {
    "mock": {"mock"},
    "gemini_cli": {"nano-banana-2", "nano-banana-pro"},
    "cliproxyapi": {CLI_PROXY_DEFAULT_MODEL},
    "agent_handoff": {CLI_PROXY_DEFAULT_MODEL},
}
LEGACY_PROVIDER_DEFAULTS = {
    "mock": ("mock", "mock"),
    "nano_banana": ("gemini_cli", "nano-banana-2"),
    "nano_banana_pro": ("gemini_cli", "nano-banana-pro"),
    "gpt_image_2": ("cliproxyapi", CLI_PROXY_DEFAULT_MODEL),
    "imagegen": ("cliproxyapi", CLI_PROXY_DEFAULT_MODEL),
    "imagegen_handoff": ("agent_handoff", CLI_PROXY_DEFAULT_MODEL),
}
ALPHA_THRESHOLD = 32


class ReferencePairWorkflowError(RuntimeError):
    pass


def _allowed_models_for_provider(*, provider_name: str, provider_mode: str) -> set[str]:
    if provider_mode == "direct":
        if provider_name == "mock":
            return PROVIDER_MODEL_FAMILIES["mock"]
        if provider_name == "gemini_cli":
            return PROVIDER_MODEL_FAMILIES["gemini_cli"]
        if provider_name == "cliproxyapi":
            return PROVIDER_MODEL_FAMILIES["cliproxyapi"]
    if provider_mode == "agent_handoff" and provider_name == "agent_handoff":
        return PROVIDER_MODEL_FAMILIES["agent_handoff"]
    raise ReferencePairWorkflowError(f"Unsupported provider contract provider.mode={provider_mode!r} provider.name={provider_name!r}.")


def _normalize_provider_contract(
    *,
    provider_name_raw: str,
    provider_mode: str,
    requested_model_name: str,
    provider_agent_tool: str,
) -> tuple[dict[str, str], dict[str, str], list[str]]:
    warnings: list[str] = []
    provider_name = provider_name_raw.lower()
    model_name = requested_model_name.strip().lower()
    canonical_provider_name = provider_name

    if provider_mode == "direct":
        if provider_name not in SUPPORTED_DIRECT_PROVIDERS:
            raise ReferencePairWorkflowError(
                f"Unsupported direct provider.name '{provider_name}'. Expected one of: {', '.join(sorted(SUPPORTED_DIRECT_PROVIDERS))}"
            )
        if provider_name in LEGACY_PROVIDER_DEFAULTS:
            canonical_provider_name, default_model_name = LEGACY_PROVIDER_DEFAULTS[provider_name]
            if provider_name != canonical_provider_name:
                warnings.append(
                    f"Legacy provider.name='{provider_name}' was normalized to canonical direct backend '{canonical_provider_name}'."
                )
        elif provider_name == "gemini_cli":
            default_model_name = "nano-banana-2"
        elif provider_name == "cliproxyapi":
            default_model_name = CLI_PROXY_DEFAULT_MODEL
        else:
            default_model_name = "mock"
        if not model_name:
            model_name = default_model_name
        if provider_agent_tool:
            warnings.append(f"provider.agent_tool='{provider_agent_tool}' was ignored because provider.mode=direct.")
    else:
        if provider_name not in SUPPORTED_AGENT_HANDOFF_PROVIDERS:
            raise ReferencePairWorkflowError(
                f"Unsupported agent_handoff provider.name '{provider_name}'. Expected one of: {', '.join(sorted(SUPPORTED_AGENT_HANDOFF_PROVIDERS))}"
            )
        if provider_name in LEGACY_PROVIDER_DEFAULTS:
            canonical_provider_name, default_model_name = LEGACY_PROVIDER_DEFAULTS[provider_name]
            if canonical_provider_name != "agent_handoff":
                canonical_provider_name = "agent_handoff"
                default_model_name = CLI_PROXY_DEFAULT_MODEL
            if provider_name != canonical_provider_name:
                warnings.append(
                    f"Legacy provider.name='{provider_name}' was normalized to canonical handoff backend '{canonical_provider_name}'."
                )
        else:
            canonical_provider_name = "agent_handoff"
            default_model_name = CLI_PROXY_DEFAULT_MODEL
        normalized_agent_tool = provider_agent_tool or "imagegen"
        if normalized_agent_tool != "imagegen":
            raise ReferencePairWorkflowError("provider.agent_tool must be 'imagegen' for provider.mode=agent_handoff.")
        provider_agent_tool = normalized_agent_tool
        if not model_name:
            model_name = default_model_name

    allowed_models = _allowed_models_for_provider(
        provider_name=canonical_provider_name,
        provider_mode=provider_mode,
    )
    if model_name not in allowed_models:
        raise ReferencePairWorkflowError(
            f"Unsupported model.name '{model_name}' for provider.name='{canonical_provider_name}' and provider.mode='{provider_mode}'. "
            f"Expected one of: {', '.join(sorted(allowed_models))}"
        )

    return (
        {
            "name": canonical_provider_name,
            "mode": provider_mode,
            "agent_tool": provider_agent_tool if provider_mode == "agent_handoff" else "",
        },
        {"name": model_name},
        warnings,
    )


def _normalize_text_list(value: Any, *, field_name: str) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        raw_values = value
    elif isinstance(value, str):
        raw_values = [value]
    else:
        raise ReferencePairWorkflowError(f"{field_name} must be a string or array of strings when provided.")
    normalized: list[str] = []
    for item in raw_values:
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_prompt_parts(raw: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    prompt_parts_raw = raw.get("prompt_parts", {})
    if prompt_parts_raw is None:
        prompt_parts_raw = {}
    if not isinstance(prompt_parts_raw, dict):
        raise ReferencePairWorkflowError("prompt_parts must be an object when provided.")

    warnings: list[str] = []
    style = str(prompt_parts_raw.get("style", "")).strip()
    material = str(prompt_parts_raw.get("material", "")).strip()
    decoration = str(prompt_parts_raw.get("decoration", "")).strip()
    negative_constraints = _normalize_text_list(
        prompt_parts_raw.get("negative_constraints", []),
        field_name="prompt_parts.negative_constraints",
    )

    legacy_prompt = str(raw.get("prompt", "")).strip()
    if not any((style, material, decoration)):
        if legacy_prompt:
            style = legacy_prompt
            warnings.append("Legacy top-level prompt was mapped to prompt_parts.style; prefer prompt_parts.style/material/decoration.")
        else:
            raise ReferencePairWorkflowError(
                "spec must provide either prompt_parts.style/material/decoration or legacy prompt."
            )

    legacy_negative_prompt = str(raw.get("negative_prompt", "")).strip()
    if not negative_constraints and legacy_negative_prompt:
        negative_constraints = [part.strip() for part in legacy_negative_prompt.split(",") if part.strip()]
        warnings.append("Legacy top-level negative_prompt was mapped to prompt_parts.negative_constraints; prefer the structured array.")

    return {
        "style": style,
        "material": material,
        "decoration": decoration,
        "negative_constraints": negative_constraints,
    }, warnings


def _infer_wall_side(profile_raw: dict[str, Any], *, variant_name: str) -> str:
    wall_side = str((profile_raw or {}).get("wall_side", "")).strip().lower()
    if wall_side in {"left", "right"}:
        return wall_side
    if variant_name in {"left", "right"}:
        return variant_name
    role_text = str((profile_raw or {}).get("role_text", "")).strip().lower()
    if "left-facing" in role_text or "left wall" in role_text:
        return "left"
    if "right-facing" in role_text or "right wall" in role_text:
        return "right"
    return ""


def _infer_wall_height_units(profile_raw: dict[str, Any]) -> int | None:
    raw_height = (profile_raw or {}).get("height_units")
    if raw_height is not None and str(raw_height).strip():
        try:
            height_units = int(raw_height)
        except (TypeError, ValueError) as error:
            raise ReferencePairWorkflowError("variant_profiles wall height_units must be an integer.") from error
        if height_units not in {1, 2}:
            raise ReferencePairWorkflowError("variant_profiles wall height_units must be 1 or 2.")
        return height_units
    role_text = str((profile_raw or {}).get("role_text", "")).strip().lower()
    if "two-tile-high" in role_text or "2u" in role_text:
        return 2
    if "single-tile-high" in role_text or "1u" in role_text:
        return 1
    return None


def _normalize_wall_variant_profile(profile_raw: dict[str, Any], *, variant_name: str) -> dict[str, Any]:
    wall_side = _infer_wall_side(profile_raw, variant_name=variant_name)
    height_units = _infer_wall_height_units(profile_raw)
    reference_rotation_raw = (profile_raw or {}).get("reference_rotation")
    reference_rotation: int | None = None
    if reference_rotation_raw is not None and str(reference_rotation_raw).strip():
        try:
            reference_rotation = int(reference_rotation_raw)
        except (TypeError, ValueError) as error:
            raise ReferencePairWorkflowError("variant_profiles wall reference_rotation must be an integer.") from error
    return {
        "wall_side": wall_side,
        "height_units": height_units,
        "reference_rotation": reference_rotation,
    }


def _expected_wall_reference_rotation(wall_side: str) -> int | None:
    if wall_side == "left":
        return 90
    if wall_side == "right":
        return 0
    return None


def _reference_rotation_from_path(path: Path) -> int | None:
    stem = path.stem.lower()
    if "_rot90" in stem:
        return 90
    if "_rot0" in stem:
        return 0
    return None


def _file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _validate_wall_reference_integrity(
    *,
    variants: list[str],
    normalized_reference_pair: dict[str, str],
    variant_profiles: dict[str, dict[str, Any]],
) -> None:
    wall_variants = [
        variant_name for variant_name in variants
        if str(variant_profiles.get(variant_name, {}).get("selector_profile", "")).strip().lower() == "wall"
    ]
    if not wall_variants:
        return

    for variant_name in wall_variants:
        profile = variant_profiles.get(variant_name, {})
        wall_meta = profile.get("wall_profile", {}) if isinstance(profile, dict) else {}
        wall_side = str(wall_meta.get("wall_side", "")).strip().lower()
        height_units = wall_meta.get("height_units")
        if wall_side and wall_side != variant_name:
            raise ReferencePairWorkflowError(
                f"variant_profiles.{variant_name}.wall_side='{wall_side}' conflicts with variant name '{variant_name}'."
            )
        if wall_side not in {"left", "right"}:
            raise ReferencePairWorkflowError(
                f"variant_profiles.{variant_name} must declare wall_side left/right or use a left/right variant name."
            )
        if height_units not in {1, 2}:
            raise ReferencePairWorkflowError(
                f"variant_profiles.{variant_name} must preserve wall height_units as 1 or 2; prose-only height is not allowed for wall specs."
            )
        reference_path = Path(normalized_reference_pair[variant_name])
        actual_rotation = _reference_rotation_from_path(reference_path)
        declared_rotation = wall_meta.get("reference_rotation")
        canonical_rotation = _expected_wall_reference_rotation(wall_side or variant_name)
        if declared_rotation is not None and canonical_rotation is not None and int(declared_rotation) != int(canonical_rotation):
            raise ReferencePairWorkflowError(
                f"variant_profiles.{variant_name}.reference_rotation={declared_rotation} conflicts with canonical {variant_name} wall rotation rot{canonical_rotation}."
            )
        expected_rotation = canonical_rotation
        if actual_rotation is not None and expected_rotation is not None and int(actual_rotation) != int(expected_rotation):
            raise ReferencePairWorkflowError(
                f"reference_pair.{variant_name} uses rotation rot{actual_rotation}, expected rot{expected_rotation} for the {variant_name} wall."
            )

    if {"left", "right"}.issubset(wall_variants):
        left_path = Path(normalized_reference_pair["left"])
        right_path = Path(normalized_reference_pair["right"])
        if _file_sha256(left_path) == _file_sha256(right_path):
            raise ReferencePairWorkflowError(
                "Wall reference_pair.left and reference_pair.right resolve to the same image content; handedness would collapse."
            )


@dataclass
class PairMetrics:
    image_path: str
    size: tuple[int, int]
    bbox: tuple[int, int, int, int] | None
    area_pixels: int
    center: tuple[float, float] | None


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    lowered = "_".join(value.strip().lower().split())
    cleaned = "".join(character if character.isalnum() or character == "_" else "_" for character in lowered)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "run"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _cleanup_artifact_token(name: str) -> str:
    text = str(name).strip()
    if not text:
        return "v00_unknown"
    if text.startswith("v"):
        return text
    if "_" in text:
        prefix, suffix = text.split("_", 1)
        if prefix.isdigit():
            return f"v{prefix}_{suffix}"
    return f"v_{text}"


def _copy_artifact(source: Path | None, destination: Path) -> str | None:
    if source is None or not source.exists():
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return str(destination)


def _strip_wrapped_yaml_scalar(value: str) -> str:
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def _load_cli_proxy_api_config(path: Path = CLI_PROXY_API_CONFIG_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    host = ""
    port = ""
    api_key = ""
    in_api_keys = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("host:"):
            host = _strip_wrapped_yaml_scalar(stripped.split(":", 1)[1])
            in_api_keys = False
            continue
        if stripped.startswith("port:"):
            port = _strip_wrapped_yaml_scalar(stripped.split(":", 1)[1])
            in_api_keys = False
            continue
        if stripped.startswith("api-keys:"):
            in_api_keys = True
            continue
        if in_api_keys:
            if stripped.startswith("- "):
                api_key = _strip_wrapped_yaml_scalar(stripped[2:])
                continue
            if not raw_line.startswith((" ", "\t")):
                in_api_keys = False
    payload: dict[str, str] = {}
    if host:
        payload["host"] = host
    if port:
        payload["port"] = port
    if api_key:
        payload["api_key"] = api_key
    return payload


def _resolve_cli_proxy_api_settings(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env if base_env is not None else os.environ)
    config_payload = _load_cli_proxy_api_config()
    base_url = (
        env.get("CLI_PROXY_API_BASE_URL", "").strip()
        or env.get("CLIPROXYAPI_BASE_URL", "").strip()
    )
    if not base_url:
        host = config_payload.get("host", "").strip()
        port = config_payload.get("port", "").strip()
        if host and port:
            base_url = f"http://{host}:{port}/v1"
    if not base_url:
        base_url = CLI_PROXY_DEFAULT_BASE_URL
    api_key = (
        env.get("CLI_PROXY_API_KEY", "").strip()
        or env.get("CLIPROXYAPI_API_KEY", "").strip()
        or config_payload.get("api_key", "").strip()
        or CLI_PROXY_DEFAULT_API_KEY
    )
    return {
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "config_path": str(CLI_PROXY_API_CONFIG_PATH),
    }


def _probe_cli_proxy_api_capabilities(*, base_url: str, api_key: str, timeout: int) -> dict[str, Any]:
    probe_root = base_url.rsplit("/v1", 1)[0] if base_url.endswith("/v1") else base_url
    request = urllib.request.Request(
        probe_root,
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _save_cli_proxy_api_response(payload: dict[str, Any], output_path: Path) -> Path:
    data = payload.get("data") or []
    if not isinstance(data, list) or not data:
        raise ReferencePairWorkflowError("CLIProxyAPI returned no image data.")
    item = data[0]
    if not isinstance(item, dict):
        raise ReferencePairWorkflowError("CLIProxyAPI returned an unexpected image payload.")
    if "b64_json" in item:
        raw_bytes = base64.b64decode(str(item["b64_json"]))
    elif "url" in item and str(item["url"]).startswith("data:"):
        raw_bytes = base64.b64decode(str(item["url"]).split(",", 1)[1])
    else:
        raise ReferencePairWorkflowError("CLIProxyAPI returned an unsupported image payload.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(raw_bytes)
    return output_path


def _multipart_form_request(
    *,
    url: str,
    api_key: str,
    fields: dict[str, str],
    file_field_name: str,
    file_path: Path,
    timeout: int,
) -> dict[str, Any]:
    boundary = _make_boundary()
    body = bytearray()
    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
        (
            f'Content-Disposition: form-data; name="{file_field_name}"; '
            f'filename="{file_path.name}"\r\n'
        ).encode("utf-8")
    )
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(file_path.read_bytes())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    request = urllib.request.Request(
        url,
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise ReferencePairWorkflowError(
            f"CLIProxyAPI edit request failed with HTTP {error.code}: {error_body}"
        ) from error
    except urllib.error.URLError as error:
        raise ReferencePairWorkflowError(f"CLIProxyAPI edit request failed: {error}") from error


def _image_file_to_data_url(image_path: Path) -> str:
    image_bytes = image_path.read_bytes()
    media_type = "image/png"
    suffix = image_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        media_type = "image/jpeg"
    elif suffix == ".webp":
        media_type = "image/webp"
    return f"data:{media_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def _json_post_request(
    *,
    url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout: int,
    error_label: str,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise ReferencePairWorkflowError(
            f"{error_label} failed with HTTP {error.code}: {error_body}"
        ) from error
    except urllib.error.URLError as error:
        raise ReferencePairWorkflowError(f"{error_label} failed: {error}") from error


def _generate_with_cli_proxy_api(
    *,
    provider_name: str,
    model_name: str,
    prompt_text: str,
    reference_images: Sequence[Path],
    output_path: Path,
    transparent_background: bool = False,
    size_override: str | None = None,
    timeout: int = 300,
) -> dict[str, Any]:
    settings = _resolve_cli_proxy_api_settings()
    capabilities = _probe_cli_proxy_api_capabilities(
        base_url=settings["base_url"],
        api_key=settings["api_key"],
        timeout=timeout,
    )
    advertised_endpoints = capabilities.get("endpoints", []) if isinstance(capabilities, dict) else []
    advertised_text = " | ".join(str(item) for item in advertised_endpoints) if isinstance(advertised_endpoints, list) else ""
    normalized_reference_images = [Path(path) for path in reference_images]
    if len(normalized_reference_images) > 1:
        raise ReferencePairWorkflowError(
            "CLIProxyAPI GPT Image 2 backend currently supports at most one reference image per variant in this repo."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if normalized_reference_images:
        # Local CLIProxyAPI builds since the GPT Image route migration accept a
        # JSON edit body with data URLs. Prefer that shape over multipart
        # because older proxy/Responses bridges can reject multipart while still
        # supporting image edits through JSON.
        response_payload = _json_post_request(
            url=f"{settings['base_url']}/images/edits",
            api_key=settings["api_key"],
            payload={
                "model": model_name,
                "prompt": prompt_text,
                "response_format": "b64_json",
                "images": [{"image_url": _image_file_to_data_url(normalized_reference_images[0])}],
                **({"size": size_override} if size_override else {}),
                **({"background": "transparent", "output_format": "png"} if transparent_background else {}),
            },
            timeout=timeout,
            error_label="CLIProxyAPI edit request",
        )
        request_mode = "edit"
    else:
        body = json.dumps(
            {
                "model": model_name,
                "prompt": prompt_text,
                "size": size_override or "1024x1024",
                "response_format": "b64_json",
                **({"background": "transparent", "output_format": "png"} if transparent_background else {}),
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{settings['base_url']}/images/generations",
            data=body,
            headers={
                "Authorization": f"Bearer {settings['api_key']}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            error_body = error.read().decode("utf-8", errors="replace")
            raise ReferencePairWorkflowError(
                "CLIProxyAPI generation request failed "
                f"(HTTP {error.code}). "
                f"base_url={settings['base_url']} "
                + (f"advertised_endpoints={advertised_text} " if advertised_text else "")
                + f"body={error_body}"
            ) from error
        except urllib.error.URLError as error:
            raise ReferencePairWorkflowError(f"CLIProxyAPI generation request failed: {error}") from error
        request_mode = "generate"
    _save_cli_proxy_api_response(response_payload, output_path)
    return {
        "provider": provider_name,
        "provider_alias": provider_name,
        "model": model_name,
        "request_mode": request_mode,
        "size": size_override or "1024x1024",
        "base_url": settings["base_url"],
        "config_path": settings["config_path"],
        "reference_images": [str(path) for path in normalized_reference_images],
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReferencePairWorkflowError(f"{label} must be a non-empty string.")
    return value.strip()


def resolve_input_path(path_value: str, *, base_path: Path) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = (base_path / path).resolve()
    else:
        path = path.resolve()
    return path


def load_and_validate_spec(spec_path: Path) -> tuple[dict[str, Any], list[str]]:
    raw = load_json(spec_path)
    if not isinstance(raw, dict):
        raise ReferencePairWorkflowError("Spec must be a JSON object.")

    schema_version = require_non_empty_string(raw.get("schema_version"), "schema_version")
    if schema_version != SCHEMA_VERSION:
        raise ReferencePairWorkflowError(
            f"Unsupported schema_version '{schema_version}'. Expected '{SCHEMA_VERSION}'."
        )

    provider_data = raw.get("provider", {})
    if not isinstance(provider_data, dict):
        raise ReferencePairWorkflowError("provider must be an object.")
    provider_name = require_non_empty_string(provider_data.get("name", "mock"), "provider.name").lower()
    provider_mode = str(provider_data.get("mode", "direct")).strip().lower() or "direct"
    if provider_mode not in SUPPORTED_PROVIDER_MODES:
        raise ReferencePairWorkflowError(
            f"Unsupported provider.mode '{provider_mode}'. Expected one of: {', '.join(sorted(SUPPORTED_PROVIDER_MODES))}"
        )
    provider_agent_tool = str(provider_data.get("agent_tool", "")).strip().lower()
    model_data = raw.get("model", {})
    if model_data is None:
        model_data = {}
    if not isinstance(model_data, dict):
        raise ReferencePairWorkflowError("model must be an object when provided.")
    legacy_provider_model_name = str(provider_data.get("model", "")).strip().lower()
    requested_model_name = str(model_data.get("name", "")).strip().lower()
    warnings: list[str] = []
    if not requested_model_name and legacy_provider_model_name:
        requested_model_name = legacy_provider_model_name
        warnings.append("Legacy provider.model was mapped to model.name; prefer the top-level model object.")
    normalized_provider, normalized_model, provider_warnings = _normalize_provider_contract(
        provider_name_raw=provider_name,
        provider_mode=provider_mode,
        requested_model_name=requested_model_name,
        provider_agent_tool=provider_agent_tool,
    )
    warnings.extend(provider_warnings)

    reference_pair = raw.get("reference_pair")
    if not isinstance(reference_pair, dict):
        raise ReferencePairWorkflowError("reference_pair must be an object.")
    normalized_reference_pair: dict[str, str] = {}
    for variant_name_raw, variant_path_raw in reference_pair.items():
        variant_name = require_non_empty_string(variant_name_raw, "reference_pair key").lower()
        if variant_name in normalized_reference_pair:
            raise ReferencePairWorkflowError(f"Duplicate reference_pair variant '{variant_name}'.")
        image_path = resolve_input_path(
            require_non_empty_string(variant_path_raw, f"reference_pair.{variant_name}"),
            base_path=spec_path.parent,
        )
        normalized_reference_pair[variant_name] = str(image_path)
    if not normalized_reference_pair:
        raise ReferencePairWorkflowError("reference_pair must define at least one variant.")
    for label, image_path_value in normalized_reference_pair.items():
        image_path = Path(image_path_value)
        if not image_path.exists():
            raise ReferencePairWorkflowError(f"reference_pair.{label} was not found: {image_path}")

    conversion_data = raw.get("conversion", {})
    if conversion_data is not None and not isinstance(conversion_data, dict):
        raise ReferencePairWorkflowError("conversion must be an object when provided.")
    conversion_mode = str(conversion_data.get("mode", "none")).strip().lower() or "none"
    if conversion_mode not in SUPPORTED_CONVERSION_MODES:
        raise ReferencePairWorkflowError(
            f"Unsupported conversion.mode '{conversion_mode}'. Expected one of: {', '.join(sorted(SUPPORTED_CONVERSION_MODES))}"
        )

    validation_data = raw.get("validation", {})
    if validation_data is not None and not isinstance(validation_data, dict):
        raise ReferencePairWorkflowError("validation must be an object when provided.")

    background_data = raw.get("background", {})
    if background_data is not None and not isinstance(background_data, dict):
        raise ReferencePairWorkflowError("background must be an object when provided.")
    background_mode = str(background_data.get("mode", "transparent")).strip().lower() or "transparent"
    if background_mode not in {"transparent", "color_key"}:
        raise ReferencePairWorkflowError("background.mode must be one of: transparent, color_key")
    prompt_color = str(background_data.get("prompt_color", "#FF00FF")).strip().upper() or "#FF00FF"
    fallback_colors_raw = background_data.get("fallback_colors", ["#00FF00"])
    if isinstance(fallback_colors_raw, str):
        fallback_colors_raw = [fallback_colors_raw]
    if not isinstance(fallback_colors_raw, list):
        raise ReferencePairWorkflowError("background.fallback_colors must be an array when provided.")
    fallback_colors = [require_non_empty_string(color, "background.fallback_colors[]").upper() for color in fallback_colors_raw]
    parse_hex_color(prompt_color)
    for fallback_color in fallback_colors:
        parse_hex_color(fallback_color)
    color_key_tolerance = int(background_data.get("tolerance", 24))
    if color_key_tolerance < 0 or color_key_tolerance > 255:
        raise ReferencePairWorkflowError("background.tolerance must be between 0 and 255.")

    default_variants = ["full", "half"] if {"full", "half"}.issubset(normalized_reference_pair.keys()) else list(normalized_reference_pair.keys())
    variants_raw = raw.get("variants", default_variants)
    if not isinstance(variants_raw, list) or not variants_raw:
        raise ReferencePairWorkflowError("variants must be a non-empty array when provided.")
    variants: list[str] = []
    for variant in variants_raw:
        variant_name = require_non_empty_string(variant, "variants[]").lower()
        if variant_name not in normalized_reference_pair:
            raise ReferencePairWorkflowError(f"Variant '{variant_name}' is missing from reference_pair.")
        if variant_name not in variants:
            variants.append(variant_name)

    variant_profiles_raw = raw.get("variant_profiles", {})
    if variant_profiles_raw is not None and not isinstance(variant_profiles_raw, dict):
        raise ReferencePairWorkflowError("variant_profiles must be an object when provided.")
    variant_profiles: dict[str, dict[str, Any]] = {}
    spec_warnings: list[str] = list(warnings)
    for variant_name in variants:
        profile_raw = variant_profiles_raw.get(variant_name, {}) if isinstance(variant_profiles_raw, dict) else {}
        if profile_raw is not None and not isinstance(profile_raw, dict):
            raise ReferencePairWorkflowError(f"variant_profiles.{variant_name} must be an object.")
        role_text = str((profile_raw or {}).get("role_text", "")).strip()
        geometry_guidance = str((profile_raw or {}).get("geometry_guidance", "")).strip()
        sheet_label = str((profile_raw or {}).get("sheet_label", "")).strip() or variant_name
        selector_profile = str((profile_raw or {}).get("selector_profile", "")).strip().lower()
        if selector_profile == "wall" and geometry_guidance:
            spec_warnings.append(
                f"variant_profiles.{variant_name}.geometry_guidance was ignored for wall prompts; wall geometry now comes from reference lock + structured wall metadata."
            )
            geometry_guidance = ""
        variant_profiles[variant_name] = {
            "role_text": role_text,
            "geometry_guidance": geometry_guidance,
            "sheet_label": sheet_label,
            "selector_profile": selector_profile,
            "wall_profile": _normalize_wall_variant_profile(profile_raw or {}, variant_name=variant_name),
        }

    _validate_wall_reference_integrity(
        variants=variants,
        normalized_reference_pair=normalized_reference_pair,
        variant_profiles=variant_profiles,
    )

    conversion_source_variant: str | None = None
    conversion_source_image: Path | None = None
    if conversion_mode == "transform":
        conversion_source_variant = require_non_empty_string(
            conversion_data.get("source_variant"),
            "conversion.source_variant",
        ).lower()
        if conversion_source_variant not in normalized_reference_pair:
            raise ReferencePairWorkflowError("conversion.source_variant must match a reference_pair variant.")
        if len(variants) != 1:
            raise ReferencePairWorkflowError(
                "conversion.mode=transform requires exactly one target variant in variants."
            )
        if variants[0] == conversion_source_variant:
            raise ReferencePairWorkflowError(
                "conversion.source_variant must be the opposite height of the requested target variant."
            )
        conversion_source_image = resolve_input_path(
            require_non_empty_string(conversion_data.get("source_image"), "conversion.source_image"),
            base_path=spec_path.parent,
        )
        if not conversion_source_image.exists():
            raise ReferencePairWorkflowError(f"conversion.source_image was not found: {conversion_source_image}")

    output_root = resolve_input_path(require_non_empty_string(raw.get("output_root"), "output_root"), base_path=spec_path.parent)
    theme = require_non_empty_string(raw.get("theme"), "theme")
    run_id = str(raw.get("run_id", "")).strip() or slugify(theme)
    prompt_parts, prompt_part_warnings = _normalize_prompt_parts(raw)
    spec_warnings.extend(prompt_part_warnings)

    normalized = {
        "schema_version": SCHEMA_VERSION,
        "theme": theme,
        "run_id": run_id,
        "output_root": str(output_root),
        "variants": variants,
        "provider": normalized_provider,
        "model": normalized_model,
        "reference_pair": normalized_reference_pair,
        "variant_profiles": variant_profiles,
        "conversion": {
            "mode": conversion_mode,
            "source_variant": conversion_source_variant,
            "source_image": str(conversion_source_image) if conversion_source_image else "",
        },
        "prompt_parts": prompt_parts,
        "prompt": prompt_parts["style"],
        "negative_prompt": ", ".join(prompt_parts["negative_constraints"]),
        "reference_intent": str(raw.get("reference_intent", "")).strip()
        or (
            "Use the references to preserve camera angle, silhouette, proportions, face visibility, "
            "height relationship, and single-tile framing."
        ),
        "generator_notes": str(raw.get("generator_notes", "")).strip(),
        "background": {
            "mode": background_mode,
            "prompt_color": prompt_color,
            "fallback_colors": fallback_colors,
            "tolerance": color_key_tolerance,
        },
        "validation": {
            "iou_soft_fail": float(validation_data.get("iou_soft_fail", 0.92)),
            "iou_hard_fail": float(validation_data.get("iou_hard_fail", 0.80)),
            "bbox_delta_soft_fail": int(validation_data.get("bbox_delta_soft_fail", 6)),
            "bbox_delta_hard_fail": int(validation_data.get("bbox_delta_hard_fail", 16)),
            "pair_height_ratio_soft_fail": float(validation_data.get("pair_height_ratio_soft_fail", 0.08)),
            "pair_height_ratio_hard_fail": float(validation_data.get("pair_height_ratio_hard_fail", 0.16)),
        },
    }
    canonical_provider_name = normalized_provider["name"]
    canonical_model_name = normalized_model["name"]
    if provider_mode == "direct" and canonical_provider_name == "gemini_cli":
        spec_warnings.append("Provider execution requires GEMINI_API_KEY in process env or repo .env.")
    if provider_mode == "direct" and canonical_provider_name == "cliproxyapi":
        spec_warnings.append(
            "Direct GPT Image 2 execution uses local CLIProxyAPI at CLI_PROXY_API_BASE_URL/CLI_PROXY_API_KEY or ~/.cli-proxy-api/config.yaml; defaults are http://127.0.0.1:8317/v1 and local-dev-image-key."
        )
    if provider_mode == "agent_handoff":
        spec_warnings.append(
            "agent_handoff mode does not call a provider itself; an external Codex agent must write Step 1 raw PNGs into the declared handoff paths before generate-reference-pair can continue."
        )
    if canonical_provider_name == "cliproxyapi" and canonical_model_name != CLI_PROXY_DEFAULT_MODEL:
        raise ReferencePairWorkflowError(f"CLIProxyAPI direct provider currently supports only model.name='{CLI_PROXY_DEFAULT_MODEL}'.")
    return normalized, spec_warnings


def run_root_for_spec(spec: dict[str, Any]) -> Path:
    return Path(spec["output_root"]).expanduser().resolve() / spec["run_id"]


def build_run_directories(run_root: Path) -> dict[str, Path]:
    legacy_removed_paths = [
        run_root / "step_2_keyed_default",
        run_root / "step_5_source",
    ]
    for legacy_path in legacy_removed_paths:
        if legacy_path.exists():
            shutil.rmtree(legacy_path)
    directories = {
        "run_root": run_root,
        "refs": run_root / "refs",
        "request": run_root / "request",
        "agent_handoff": run_root / "agent_handoff",
        "generated": run_root / "generated",
        "processed": run_root / "processed",
        "validation": run_root / "validation",
        "logs": run_root / "logs",
        "step_1_raw": run_root / "step_1_raw",
        "step_3_cleanup_pool": run_root / "step_3_cleanup_pool",
        "step_4_gate": run_root / "step_4_gate",
        "step_6_mapping": run_root / "step_6_mapping",
        "step_7_selection": run_root / "step_7_selection",
        "deliverables": run_root / "deliverables",
    }
    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)
    return directories


def _remove_step_status_keys(run_root: Path, *, step_keys: Sequence[str]) -> None:
    summary_path = run_root / "artifact_status.json"
    if not summary_path.exists():
        return
    payload = load_json(summary_path)
    variants_payload = payload.get("variants", {})
    if not isinstance(variants_payload, dict):
        return
    changed = False
    for variant_payload in variants_payload.values():
        if not isinstance(variant_payload, dict):
            continue
        for step_key in step_keys:
            if step_key in variant_payload:
                variant_payload.pop(step_key, None)
                changed = True
    if changed:
        write_json(summary_path, payload)


def _agent_handoff_raw_output_path(run_root: Path, *, variant: str) -> Path:
    return run_root / "agent_handoff" / "step_1_raw" / f"{variant}.png"


def _build_imagegen_codex_edit_prompt(
    *,
    variant: str,
    request_payload: dict[str, Any],
) -> str:
    base_prompt = str(request_payload.get("prompts", {}).get(variant, "")).strip()
    background = request_payload.get("background", {})
    variant_profiles = request_payload.get("variant_profiles", {})
    variant_profile = variant_profiles.get(variant, {}) if isinstance(variant_profiles, dict) else {}
    wall_profile = variant_profile.get("wall_profile", {}) if isinstance(variant_profile, dict) else {}
    wall_side = str(wall_profile.get("wall_side", "")).strip().lower() or str(variant).strip().lower()
    height_units = wall_profile.get("height_units")
    if wall_side in {"left", "right"}:
        role_text = f"{wall_side}-facing"
    else:
        role_text = str(variant)
    height_text = "2-tile-high" if height_units == 2 else "single-tile-high" if height_units == 1 else "isometric"
    allowed_colors = []
    if isinstance(background, dict) and background.get("mode") == "color_key":
        allowed_colors = [str(background.get("prompt_color", "")).strip(), *[str(color).strip() for color in background.get("fallback_colors", [])]]
        allowed_colors = [color for color in allowed_colors if color]
    background_rule = (
        f"Use one exact flat chroma background color outside the wall silhouette: {' or '.join(allowed_colors)}. "
        "No gradients, no noise, no transparency outside the silhouette, and no cast shadow."
        if allowed_colors
        else "Keep the background outside the wall silhouette clean and uniform."
    )
    return (
        "EDIT the currently visible reference image; do not generate a new wall from scratch. "
        f"The visible image is the exact edit target for the {role_text} {height_text} wall. "
        "Preserve the canvas size, framing, silhouette, handedness, occupied side, contact edge, perspective, and all transparent/background pixels exactly. "
        "Only repaint the existing plain white/gray wall surface with pixel-art dungeon stone texture: readable stone block seams, subtle bevels, restrained gray shading. "
        "Do not make the wall longer, wider, thicker, shorter, front-facing, corner-shaped, or horizontal. "
        "Do not add a floor tile, props, border, text, watermark, glow, scene background, or shadow. "
        f"{background_rule} "
        f"Source factory prompt for style context: {base_prompt}"
    ).strip()


def _build_imagegen_handoff_task(
    *,
    run_root: Path,
    request_payload: dict[str, Any],
) -> dict[str, Any]:
    variants = request_payload.get("variants", [])
    tasks: dict[str, Any] = {}
    for variant in variants:
        reference_images = list(request_payload["generation_inputs"][variant])
        tasks[str(variant)] = {
            "prompt_text": request_payload["prompts"][variant],
            "codex_imagegen_mode": "edit",
            "codex_prompt_text": _build_imagegen_codex_edit_prompt(
                variant=str(variant),
                request_payload=request_payload,
            ),
            "reference_images": reference_images,
            "edit_target_image": reference_images[0] if reference_images else "",
            "output_path": str(_agent_handoff_raw_output_path(run_root, variant=str(variant))),
        }
    return {
        "mode": "agent_handoff",
        "agent_tool": "imagegen",
        "model": request_payload.get("model", {}),
        "run_root": str(run_root),
        "background": request_payload.get("background", {}),
        "variants": variants,
        "tasks": tasks,
        "contract": {
            "purpose": "External Codex imagegen execution for Step 1 raw generation.",
            "write_step": "step_1_raw only",
            "codex_execution_protocol": [
                "For each variant, load edit_target_image into the conversation with view_image immediately before invoking image_gen.",
                "Invoke built-in image_gen in edit mode using codex_prompt_text; do not rely on the file path alone as an image input.",
                "After image_gen saves its output under CODEX_HOME/generated_images, copy the selected PNG to output_path.",
                "Do not run cleanup, selection, or final mapping in the Codex/imagegen step.",
            ],
            "do_not_modify": [
                "step_3_cleanup_pool semantics",
                "selector/finalizer behavior",
            ],
            "requirements": [
                "Write exactly one PNG per variant to the declared output_path.",
                "Use edit_target_image as an edit target, not just as a loose style reference.",
                "Preserve the supplied reference image's canvas, silhouette, handedness, occupied side, contact edge, and proportions.",
                "After staging raw PNGs, hand control back to the factory for Step 3+.",
            ],
        },
    }


def compose_reference_sheet(
    reference_image_paths: Sequence[Path],
    *,
    labels: Sequence[str] | None = None,
    output_path: Path,
) -> Path:
    if len(reference_image_paths) != 2:
        raise ReferencePairWorkflowError("compose_reference_sheet currently requires exactly two reference images.")
    first_image = Image.open(reference_image_paths[0]).convert("RGBA")
    second_image = Image.open(reference_image_paths[1]).convert("RGBA")
    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    first_resized = first_image.resize((384, 384), Image.LANCZOS)
    second_resized = second_image.resize((384, 384), Image.LANCZOS)
    canvas.alpha_composite(first_resized, ((1024 - 384) // 2, 96))
    canvas.alpha_composite(second_resized, ((1024 - 384) // 2, 544))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((300, 72, 724, 504), radius=24, outline=(255, 255, 255, 96), width=3)
    draw.rounded_rectangle((300, 520, 724, 952), radius=24, outline=(255, 255, 255, 96), width=3)
    if labels and len(labels) == 2:
        draw.text((320, 82), str(labels[0]), fill=(255, 255, 255, 180))
        draw.text((320, 530), str(labels[1]), fill=(255, 255, 255, 180))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    return output_path


def build_generation_prompt(
    spec: dict[str, Any],
    *,
    variant: str,
    use_reference_sheet: bool,
    conversion_mode: str = "none",
    conversion_source_variant: str | None = None,
) -> str:
    variant_profiles = spec.get("variant_profiles", {})
    variant_profile = variant_profiles.get(variant, {}) if isinstance(variant_profiles, dict) else {}
    prompt_parts = spec.get("prompt_parts", {}) if isinstance(spec.get("prompt_parts", {}), dict) else {}
    selector_profile = str(variant_profile.get("selector_profile", "")).strip().lower()
    wall_profile = variant_profile.get("wall_profile", {}) if isinstance(variant_profile, dict) else {}
    if selector_profile == "wall" and conversion_mode != "transform":
        wall_side = str(wall_profile.get("wall_side", "")).strip().lower() or str(variant).strip().lower()
        if wall_side in {"left", "right"}:
            role_text = f"{wall_side}-facing isometric wall segment"
        else:
            role_text = str(variant_profile.get("role_text", "")).strip() or f"{variant} isometric wall segment"
        reference_rule = (
            f"Use the supplied {role_text} reference image as the exact geometry lock for this wall tile. "
            "Keep the reference tile's structure unchanged: preserve the same camera angle, silhouette, handedness, occupied side, "
            "perspective, contact edge, and overall proportions. "
        )
        style_text = str(prompt_parts.get("style", "")).strip()
        negative_constraints = _normalize_text_list(
            prompt_parts.get("negative_constraints", []),
            field_name="prompt_parts.negative_constraints",
        )
        style_sentence = f" Style direction: {style_text}." if style_text else ""
        extra_negative = f" Negative constraints: {'; '.join(negative_constraints)}." if negative_constraints else ""
        background = spec.get("background", {})
        if background.get("mode") == "color_key":
            allowed_colors = [background["prompt_color"], *background.get("fallback_colors", [])]
            allowed_colors_text = ", ".join(allowed_colors)
            background_sentence = (
                f" Use a single flat solid background color chosen from this allowed set: {allowed_colors_text}. "
                "Estimate the RGB colors that will appear on the visible outer boundary of the generated tile silhouette, "
                "choose the allowed chroma-key color with the largest color-distance from those top-surface and upper-edge RGB values. "
                "Prefer the chroma key that is maximally separated from the top-surface colors and least likely to contaminate the tile edges. "
                "After choosing one of the allowed colors, use that one single chosen color consistently behind the tile "
                "for the entire canvas. This background is a temporary chroma-key mask only: no transparency, no gradient, "
                "no lighting variation, no shadow, no vignette, and no extra colored backdrop elements. "
            )
        else:
            background_sentence = " Keep the tile centered in frame with transparent background. "
        return (
            f"{'Edit' if conversion_mode == 'transform' else 'Create'} one isometric game tile PNG as a {role_text}. "
            f"{reference_rule}"
            "Do not add a scene, ground shadow, border, glow, extra objects, text, or watermark. "
            f"{background_sentence}"
            f"{style_sentence}"
            f"{extra_negative}"
        )
    if variant == "full":
        role_text = "full-height cube tile"
        geometry_sentence = (
            "Full-height means a normal tall cube tile with the expected full vertical side depth. "
            "Do not compress the side faces or turn it into a shallow slab. "
        )
    elif variant == "half":
        role_text = "half-height cube tile"
        geometry_sentence = (
            "Half-height means a shallow half-block slab: the visible side faces must be short, and the total visible tile height "
            "should be clearly about half of a full-height cube with the same footprint. Do not generate a full-height cube, "
            "do not use tall vertical side faces, and do not fake half-height by only changing texture."
        )
    else:
        role_text = str(variant_profile.get("role_text", "")).strip() or f"{variant} isometric asset"
        geometry_sentence = str(variant_profile.get("geometry_guidance", "")).strip()
        if selector_profile == "wall" and isinstance(wall_profile, dict):
            wall_side = str(wall_profile.get("wall_side", "")).strip().lower() or variant
            height_units = wall_profile.get("height_units")
            if not role_text:
                if wall_side in {"left", "right"} and height_units in {1, 2}:
                    height_text = "two-tile-high" if int(height_units) == 2 else "single-tile-high"
                    role_text = f"{wall_side}-facing {height_text} isometric wall segment"
            wall_geometry_parts: list[str] = []
            if height_units == 2:
                wall_geometry_parts.append(
                    "Keep the wall at the taller 2u height from the reference; do not shorten, compress, or reinterpret it as a 1u wall."
                )
            elif height_units == 1:
                wall_geometry_parts.append(
                    "Keep the wall at the normal 1u height from the reference; do not extend it into a 2u wall."
                )
            if geometry_sentence:
                wall_geometry_parts.append(geometry_sentence)
            geometry_sentence = " ".join(wall_geometry_parts).strip()
        if geometry_sentence and not geometry_sentence.endswith((" ", ".", "!", "?")):
            geometry_sentence += "."
        if geometry_sentence:
            geometry_sentence += " "
    if conversion_mode == "transform":
        if conversion_source_variant == "full":
            source_role_text = "full-height cube tile"
        elif conversion_source_variant == "half":
            source_role_text = "half-height cube tile"
        else:
            source_profile = variant_profiles.get(conversion_source_variant or "", {}) if isinstance(variant_profiles, dict) else {}
            source_role_text = str(source_profile.get("role_text", "")).strip() or f"{conversion_source_variant} isometric asset"
        reference_rule = (
            f"Two separate reference images are provided. The first image is the source {source_role_text} that must be transformed. "
            f"The second image is the target {role_text} geometry reference that defines the required height and silhouette. "
            f"Preserve the source tile's material identity, top-surface pattern, palette, shading language, edge character, and tile-family details; only change the height and geometry needed to become the target {role_text}. "
            "Do not redesign, re-theme, invent a different tile, or replace the source surface treatment with unrelated new content. "
        )
    else:
        sheet_labels = [spec["variant_profiles"][name]["sheet_label"] for name in spec.get("variants", []) if name in spec.get("variant_profiles", {})]
        if selector_profile == "wall" and isinstance(wall_profile, dict):
            wall_side = str(wall_profile.get("wall_side", "")).strip().lower() or variant
            height_units = wall_profile.get("height_units")
            side_text = wall_side if wall_side in {"left", "right"} else variant
            if use_reference_sheet:
                reference_rule = (
                    f"Use the supplied reference sheet as the exact geometry lock for this wall tile "
                    f"(upper reference = {sheet_labels[0]}; lower reference = {sheet_labels[1]}). "
                    f"Generate the {side_text} wall variant by following the corresponding reference on the sheet exactly. "
                )
            else:
                reference_rule = (
                    f"Use the supplied {role_text} reference image as the exact geometry lock for this wall tile. "
                )
            reference_rule += (
                "Keep the reference tile's structure unchanged: preserve the same camera angle, silhouette, handedness, occupied side, "
                "perspective, contact edge, and overall proportions. "
                "Do not reinterpret the wall as a corner piece, front-facing block, double-plane wall, or free-standing prop. "
            )
            if height_units == 2:
                reference_rule += "Treat the reference as the source of truth for the full 2u height. "
            elif height_units == 1:
                reference_rule += "Treat the reference as the source of truth for the normal 1u height. "
        else:
            reference_rule = (
                f"Use the supplied reference sheet for structure only (upper reference = {sheet_labels[0]}; lower reference = {sheet_labels[1]}). "
                if use_reference_sheet
                else f"Use the supplied {role_text} reference image for structure only. "
            )
    style_text = str(prompt_parts.get("style", "")).strip()
    material_text = str(prompt_parts.get("material", "")).strip()
    decoration_text = str(prompt_parts.get("decoration", "")).strip()
    negative_constraints = _normalize_text_list(
        prompt_parts.get("negative_constraints", []),
        field_name="prompt_parts.negative_constraints",
    )
    style_sentences: list[str] = []
    if style_text:
        style_sentences.append(f"Style direction: {style_text}.")
    if material_text:
        style_sentences.append(f"Material direction: {material_text}.")
    if decoration_text:
        style_sentences.append(f"Decoration direction: {decoration_text}.")
    style_sentence = f" {' '.join(style_sentences)}" if style_sentences else ""
    extra_negative = f" Negative constraints: {'; '.join(negative_constraints)}." if negative_constraints else ""
    generator_notes = spec.get("generator_notes", "")
    generator_sentence = f" Extra notes: {generator_notes}" if generator_notes else ""
    background = spec.get("background", {})
    if background.get("mode") == "color_key":
        allowed_colors = [background["prompt_color"], *background.get("fallback_colors", [])]
        allowed_colors_text = ", ".join(allowed_colors)
        background_sentence = (
            f" Use a single flat solid background color chosen from this allowed set: {allowed_colors_text}. "
            "Estimate the RGB colors that will appear on the visible outer boundary of the generated tile silhouette, "
            "but prioritize the top surface, top rim, upper silhouette, and ground material colors over the lower side walls. "
            "Choose the allowed chroma-key color with the largest color-distance from those top-surface and upper-edge RGB values. "
            "Treat the lower dirt or side-wall materials as secondary when choosing the chroma-key color. "
            "If the tile's top surface is grass, foliage, moss, or otherwise green-dominant, prefer #FF00FF and avoid #00FF00. "
            "Prefer the chroma key that is maximally separated from the top-surface colors and least likely to contaminate the tile edges. "
            "After choosing one of the allowed colors, use that one single chosen color consistently behind the tile "
            "for the entire canvas. This background is a temporary chroma-key mask only: no transparency, no gradient, "
            "no lighting variation, no shadow, no vignette, and no extra colored backdrop elements. "
            "The background must stay one exact uniform color across the whole non-tile area, with crisp edges and no contamination from the tile colors. "
        )
    else:
        background_sentence = " Keep the tile centered in frame with transparent background. "
    outline_sentence = (
        " Do not add any outline, border stroke, rim line, sticker edge, comic contour, or icon-style contour around the tile silhouette. "
        "Do not add a dark perimeter line between the tile and the background. "
        "Edge pixels must read as the tile material itself, not as a separating frame."
    )
    return (
        f"{'Edit' if conversion_mode == 'transform' else 'Create'} one isometric game tile PNG as a {role_text}. "
        f"{reference_rule}"
        f"{geometry_sentence}"
        f"For this output, match the {role_text} geometry exactly: keep camera angle, silhouette, perspective, "
        f"face visibility, footprint width, and overall proportions aligned to the corresponding reference. "
        "Do not add a scene, ground shadow, border, glow, extra objects, text, or watermark. "
        f"{background_sentence}"
        f"{outline_sentence}"
        f"Reference intent: {spec['reference_intent']} "
        f"{style_sentence}"
        f"{extra_negative}{generator_sentence}"
    )


def validate_prompt_background_consistency(prompt_text: str, *, background_mode: str) -> None:
    normalized_prompt = prompt_text.lower()
    normalized_mode = str(background_mode).strip().lower()
    if normalized_mode == "transparent":
        forbidden_fragments = (
            "single flat solid background color",
            "temporary chroma-key mask",
            "chroma-key color",
            "#ff00ff",
            "#00ff00",
        )
        for fragment in forbidden_fragments:
            if fragment in normalized_prompt:
                raise ReferencePairWorkflowError(
                    "Prompt/background mismatch: transparent mode prompt still contains color-key instructions."
                )
    elif normalized_mode == "color_key":
        if "transparent background" in normalized_prompt:
            raise ReferencePairWorkflowError(
                "Prompt/background mismatch: color_key mode prompt still contains transparent-background instructions."
            )


def prepare_reference_pair_run(spec_path: Path) -> dict[str, Any]:
    spec, warnings = load_and_validate_spec(spec_path)
    run_root = run_root_for_spec(spec)
    directories = build_run_directories(run_root)
    _remove_step_status_keys(run_root, step_keys=["step_2_keyed_default", "step_5_source"])
    variants = spec["variants"]
    provider = spec.get("provider", {})
    provider_mode = str(provider.get("mode", "direct")).strip().lower() or "direct"

    copied_references: dict[str, str] = {}
    for variant in variants:
        source_path = Path(spec["reference_pair"][variant])
        destination_path = directories["refs"] / f"{variant}.png"
        shutil.copy2(source_path, destination_path)
        copied_references[variant] = str(destination_path)

    all_wall_variants = all(
        str(spec.get("variant_profiles", {}).get(variant, {}).get("selector_profile", "")).strip().lower() == "wall"
        for variant in variants
    )

    reference_sheet_output_path = directories["refs"] / "reference_pair_sheet.png"
    reference_sheet_path: Path | None = None
    if len(variants) == 2 and not all_wall_variants:
        reference_sheet_path = compose_reference_sheet(
            [Path(copied_references[variant]) for variant in variants],
            labels=[spec["variant_profiles"][variant]["sheet_label"] for variant in variants],
            output_path=reference_sheet_output_path,
        )
    elif reference_sheet_output_path.exists():
        reference_sheet_output_path.unlink()

    prompts: dict[str, str] = {}
    prompt_paths: dict[str, str] = {}
    expected_outputs: dict[str, str] = {}
    generation_inputs: dict[str, Any] = {}
    conversion = spec.get("conversion", {"mode": "none"})
    conversion_mode = str(conversion.get("mode", "none"))
    use_reference_sheet = len(variants) == 2 and conversion_mode != "transform"
    for variant in variants:
        variant_profile = spec.get("variant_profiles", {}).get(variant, {}) if isinstance(spec.get("variant_profiles", {}), dict) else {}
        selector_profile = str(variant_profile.get("selector_profile", "")).strip().lower()
        variant_use_reference_sheet = use_reference_sheet and selector_profile != "wall"
        generation_input_paths: list[Path]
        if conversion_mode == "transform":
            source_image_src = Path(str(conversion["source_image"]))
            source_image_dst = directories["refs"] / f"conversion_source_{conversion['source_variant']}.png"
            shutil.copy2(source_image_src, source_image_dst)
            generation_input_paths = [
                source_image_dst,
                Path(copied_references[variant]),
            ]
        else:
            generation_input_paths = [
                reference_sheet_path if variant_use_reference_sheet and reference_sheet_path is not None else Path(copied_references[variant])
            ]
        prompt_text = build_generation_prompt(
            spec,
            variant=variant,
            use_reference_sheet=variant_use_reference_sheet,
            conversion_mode=conversion_mode,
            conversion_source_variant=conversion.get("source_variant"),
        )
        validate_prompt_background_consistency(
            prompt_text,
            background_mode=str(spec.get("background", {}).get("mode", "transparent")),
        )
        prompt_path = directories["request"] / f"prompt_{variant}.txt"
        prompt_path.write_text(prompt_text + "\n", encoding="utf-8")
        prompts[variant] = prompt_text
        prompt_paths[variant] = str(prompt_path)
        expected_outputs[variant] = str(directories["generated"] / f"generated_{variant}.png")
        generation_inputs[variant] = [str(path) for path in generation_input_paths]

    request_payload = {
        "schema_version": SCHEMA_VERSION,
        "prepared_at": now_iso(),
        "spec_path": str(spec_path.resolve()),
        "theme": spec["theme"],
        "variants": variants,
        "provider": spec["provider"],
        "model": spec["model"],
        "conversion": spec["conversion"],
        "references": {
            **copied_references,
            "pair_sheet": str(reference_sheet_path) if reference_sheet_path is not None else "",
        },
        "generation_inputs": generation_inputs,
        "expected_outputs": expected_outputs,
        "prompts": prompts,
        "prompt_parts": spec.get("prompt_parts", {}),
        "background": spec["background"],
        "validation": spec["validation"],
        "variant_profiles": spec.get("variant_profiles", {}),
        "warnings": warnings,
    }
    if provider_mode == "agent_handoff":
        request_payload["agent_handoff"] = {
            "enabled": True,
            "agent_tool": str(provider.get("agent_tool", "imagegen")).strip().lower() or "imagegen",
            "raw_output_paths": {variant: str(_agent_handoff_raw_output_path(run_root, variant=variant)) for variant in variants},
            "task_packet": str(directories["request"] / "imagegen_handoff.json"),
        }
    write_json(directories["request"] / "request.json", request_payload)
    if provider_mode == "agent_handoff":
        write_json(
            directories["request"] / "imagegen_handoff.json",
            _build_imagegen_handoff_task(run_root=run_root, request_payload=request_payload),
        )
    write_json(directories["logs"] / "prepare.json", {"ok": True, "prepared_at": now_iso(), "warnings": warnings})
    return {
        "run_root": str(run_root),
        "variants": variants,
        "request_path": str(directories["request"] / "request.json"),
        "agent_handoff_path": str(directories["request"] / "imagegen_handoff.json") if provider_mode == "agent_handoff" else None,
        "reference_sheet": str(reference_sheet_path) if reference_sheet_path is not None else None,
        "prompt_paths": prompt_paths,
        "warnings": warnings,
    }


def provider_env_for_generation(provider_name: str, model_name: str) -> dict[str, str]:
    if provider_name == "mock":
        return dict(os.environ)
    if provider_name == "cliproxyapi":
        return dict(os.environ)
    try:
        return build_gemini_provider_env()
    except CredentialError as error:
        raise ReferencePairWorkflowError(str(error)) from error


def generate_with_provider(
    *,
    provider_name: str,
    model_name: str,
    prompt_text: str,
    reference_images: Sequence[Path],
    output_path: Path,
    transparent_background: bool = False,
    size_override: str | None = None,
    aspect_ratio_override: str | None = None,
    image_size_override: str | None = None,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if provider_name == "mock":
        return {"provider": "mock", "model": "mock", "stdout": "mock mode skips external generation"}
    if provider_name == "cliproxyapi":
        return _generate_with_cli_proxy_api(
            provider_name=provider_name,
            model_name=model_name,
            prompt_text=prompt_text,
            reference_images=reference_images,
            output_path=output_path,
            transparent_background=transparent_background,
            size_override=size_override,
        )
    if not NANO_BANANA_SCRIPT.exists():
        raise ReferencePairWorkflowError(f"Nano Banana CLI not found: {NANO_BANANA_SCRIPT}")

    normalized_reference_images = list(reference_images)
    if not normalized_reference_images:
        raise ReferencePairWorkflowError("generate_with_provider requires at least one reference image.")

    command = [
        "node",
        str(NANO_BANANA_SCRIPT),
        f"--prompt={prompt_text}",
        f"--out={output_path}",
        "--key=company",
        f"--model={model_name}",
        f"--aspect-ratio={aspect_ratio_override or '1:1'}",
        f"--image-size={image_size_override or '1K'}",
    ]
    for reference_image in normalized_reference_images:
        command.append(f"--image={reference_image}")
    completed = subprocess.run(
        command,
        cwd=NANO_BANANA_ROOT,
        env=provider_env_for_generation(provider_name, model_name),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if completed.returncode != 0:
        stderr_text = completed.stderr.strip()
        stdout_text = completed.stdout.strip()
        combined_text = stderr_text or stdout_text or "Gemini provider failed"
        details = [
            "Gemini provider failed.",
            f"provider={provider_name}",
            f"model={model_name}",
            "reference_images=" + ",".join(str(path) for path in normalized_reference_images),
            f"output_path={output_path}",
            f"cwd={NANO_BANANA_ROOT}",
            f"exit_code={completed.returncode}",
        ]
        if "fetch failed" in combined_text.lower():
            details.append(
                "likely_causes=network blocked/unavailable, DNS/TLS failure reaching generativelanguage.googleapis.com, local fetch timeout, or external API access failure before any HTTP response was returned"
            )
        if stderr_text:
            details.append(f"stderr={stderr_text}")
        if stdout_text:
            details.append(f"stdout={stdout_text}")
        raise ReferencePairWorkflowError(" | ".join(details))
    return {
        "provider": provider_name,
        "model": model_name,
        "aspect_ratio": aspect_ratio_override or "1:1",
        "image_size": image_size_override or "1K",
        "stdout": completed.stdout.strip(),
    }


def _ingest_agent_handoff_output(
    *,
    run_root: Path,
    variant: str,
    request_payload: dict[str, Any],
    background: dict[str, Any],
    output_path: Path,
    raw_output_path: Path,
) -> dict[str, Any]:
    handoff_payload = request_payload.get("agent_handoff", {})
    if not isinstance(handoff_payload, dict) or not handoff_payload.get("enabled"):
        raise ReferencePairWorkflowError("agent_handoff provider mode requires request.agent_handoff metadata.")
    raw_output_map = handoff_payload.get("raw_output_paths", {})
    if not isinstance(raw_output_map, dict) or variant not in raw_output_map:
        raise ReferencePairWorkflowError(f"agent_handoff raw_output_paths is missing variant '{variant}'.")
    source_path = Path(str(raw_output_map[variant]))
    if not source_path.exists():
        task_packet = handoff_payload.get("task_packet", "")
        raise ReferencePairWorkflowError(
            f"agent_handoff output for variant '{variant}' is missing: {source_path}. "
            f"Stage the Step 1 raw PNG first using {task_packet or 'request/imagegen_handoff.json'}."
        )
    destination_path = raw_output_path if background.get("mode") == "color_key" else output_path
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination_path)
    return {
        "provider": "imagegen",
        "mode": "agent_handoff",
        "copied_from": str(source_path),
        "copied_to": str(destination_path),
    }


def _retry_suffix_from_failures(
    *,
    variant: str,
    selector_profile: str,
    raw_validation: dict[str, Any] | None,
    final_validation: dict[str, Any] | None,
) -> str:
    guidance: list[str] = [
        f"Retry attempt for variant '{variant}'. Previous output failed factory validation, so correct the geometry more strictly."
    ]
    variant_result = None
    if final_validation is not None and isinstance(final_validation.get(variant), dict):
        variant_result = final_validation.get(variant)
    elif raw_validation is not None and isinstance(raw_validation.get(variant), dict):
        variant_result = raw_validation.get(variant)

    failures = list(variant_result.get("failures", [])) if isinstance(variant_result, dict) else []
    if failures:
        guidance.append("Previous failure signals: " + "; ".join(str(item) for item in failures[:3]) + ".")

    lowered_failures = " | ".join(str(item).lower() for item in failures)
    if selector_profile == "wall":
        guidance.append(
            "Keep the wall tall and planar. Do not make it square, chunky, cube-like, or front-facing."
        )
        guidance.append(
            "Preserve the intended left/right handedness exactly and keep the wall attached to only the correct top edge."
        )
        if "iou" in lowered_failures or "square" in lowered_failures or "width" in lowered_failures:
            guidance.append(
                "Narrow the body silhouette to the canonical wall footprint and preserve the slanted isometric top edge."
            )
    elif variant in {"full", "half"}:
        guidance.append(
            "Preserve the floor diamond footprint exactly. Do not square it off, recenter it incorrectly, or change the tile family proportions."
        )
        if variant == "half":
            guidance.append(
                "Keep the half-height relationship consistent with the matching full tile and do not drift toward full height."
            )
    return " ".join(guidance)


def _supports_selector_closed_loop(request_payload: dict[str, Any]) -> tuple[bool, list[str]]:
    try:
        from pipeline.variant_selector import FAIL_RULES_BY_VARIANT
    except Exception:
        return False, []

    variants = request_payload.get("variants", ["full", "half"])
    variant_profiles = request_payload.get("variant_profiles", {})
    supported: list[str] = []
    for variant in variants:
        selector_profile = ""
        if isinstance(variant_profiles, dict):
            selector_profile = str(variant_profiles.get(variant, {}).get("selector_profile", "")).strip().lower()
        fail_rules_key = selector_profile or variant
        if fail_rules_key in FAIL_RULES_BY_VARIANT:
            supported.append(str(variant))
    return len(supported) == len(variants), supported


def _wall_variant_selector_profile(request_payload: dict[str, Any], variant: str) -> str:
    variant_profiles = request_payload.get("variant_profiles", {})
    if not isinstance(variant_profiles, dict):
        return ""
    return str(variant_profiles.get(variant, {}).get("selector_profile", "")).strip().lower()


def _maybe_apply_wall_mirror_fallback(
    run_root: Path,
    *,
    request_payload: dict[str, Any],
    selection_results: dict[str, Any],
    selected_outputs: dict[str, Path],
    errors: dict[str, str],
) -> None:
    variants = request_payload.get("variants", [])
    if not isinstance(variants, list):
        return
    if "left" not in variants or "right" not in variants:
        return
    if _wall_variant_selector_profile(request_payload, "left") != "wall":
        return
    if _wall_variant_selector_profile(request_payload, "right") != "wall":
        return

    for target_variant, source_variant in (("right", "left"), ("left", "right")):
        if target_variant in selected_outputs:
            continue
        source_output = selected_outputs.get(source_variant)
        if source_output is None or not source_output.exists():
            continue

        mirrored_image = Image.open(source_output).convert("RGBA").transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        final_dir = run_root / "final"
        final_dir.mkdir(parents=True, exist_ok=True)
        fallback_output = final_dir / f"selected_{target_variant}.png"
        mirrored_image.save(fallback_output)

        validation_result = validate_single_pair(
            Path(str(request_payload["references"][target_variant])),
            fallback_output,
            request_payload["validation"],
            selector_profile="wall",
        )
        if validation_result["status"] == "hard_fail":
            errors[target_variant] = (
                f"wall mirror fallback from {source_variant} failed validation: "
                + "; ".join(validation_result.get("failures", []))
            )
            continue

        selected_outputs[target_variant] = fallback_output
        errors.pop(target_variant, None)
        existing_result = selection_results.get(target_variant)
        if not isinstance(existing_result, dict):
            existing_result = {"ok": True, "variant": target_variant}
        existing_result["mirror_fallback"] = {
            "used": True,
            "source_variant": source_variant,
            "source_output": str(source_output),
            "generated_output": str(fallback_output),
            "validation": validation_result,
        }
        existing_result["selected_final_output"] = str(fallback_output)
        existing_result["selected"] = {
            "path": str(source_output),
            "final_path": str(fallback_output),
            "score": None,
            "passed": True,
            "selection_mode": "mirror_fallback",
            "source_variant": source_variant,
        }
        selection_results[target_variant] = existing_result
        write_json(run_root / "selection" / f"{target_variant}.selection.json", existing_result)
        try:
            from pipeline.variant_selector import _export_selector_stage_artifacts

            _export_selector_stage_artifacts(run_root, variant=target_variant, result=existing_result)
        except Exception:
            pass


def _run_selector_closed_loop(run_root: Path, *, request_payload: dict[str, Any], variants: list[str]) -> dict[str, Any]:
    from pipeline.variant_selector import VariantSelectorError, select_variant_pool

    selection_results: dict[str, Any] = {}
    selected_outputs: dict[str, Path] = {}
    errors: dict[str, str] = {}
    for variant in variants:
        try:
            selection_result = select_variant_pool(run_root, variant=variant)
            selection_results[variant] = selection_result
            selected_output = selection_result.get("selected_final_output")
            if selected_output:
                selected_outputs[variant] = Path(str(selected_output))
            else:
                errors[variant] = "mapped candidate failed verification"
        except VariantSelectorError as error:
            errors[variant] = str(error)

    _maybe_apply_wall_mirror_fallback(
        run_root,
        request_payload=request_payload,
        selection_results=selection_results,
        selected_outputs=selected_outputs,
        errors=errors,
    )

    return {
        "ok": not errors and len(selected_outputs) == len(variants),
        "mode": "mapping_verified",
        "selected_from_step": "step_7_selection",
        "results": selection_results,
        "selected_outputs": {variant: str(path) for variant, path in selected_outputs.items()},
        "errors": errors,
    }


def _copy_validated_outputs_to_final(run_root: Path, *, raw_validation: dict[str, Any], variants: list[str]) -> dict[str, Any]:
    final_dir = run_root / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    selected_outputs: dict[str, str] = {}
    errors: dict[str, str] = {}
    for variant in variants:
        variant_payload = raw_validation.get(variant, {})
        generated_payload = variant_payload.get("generated", {}) if isinstance(variant_payload, dict) else {}
        source_path_raw = generated_payload.get("image_path")
        if not source_path_raw:
            errors[variant] = "validated output image_path missing"
            continue
        source_path = Path(str(source_path_raw))
        if not source_path.exists():
            errors[variant] = f"validated output missing on disk: {source_path}"
            continue
        final_output_path = final_dir / f"selected_{variant}.png"
        shutil.copy2(source_path, final_output_path)
        selected_outputs[variant] = str(final_output_path)
    if selected_outputs:
        _update_deliverable_manifest(
            run_root,
            selected_outputs=selected_outputs,
            workflow_status="raw_validation_fallback",
            selected_from_step="step_3_cleanup_pool",
        )
    return {
        "ok": not errors and len(selected_outputs) == len(variants),
        "mode": "raw_validation_fallback",
        "selected_from_step": "step_3_cleanup_pool",
        "results": {},
        "selected_outputs": selected_outputs,
        "errors": errors,
    }


def _snapshot_attempt_state(run_root: Path, *, attempt_number: int) -> str:
    attempt_root = run_root / "attempts" / f"attempt_{attempt_number:02d}"
    if attempt_root.exists():
        shutil.rmtree(attempt_root)
    attempt_root.mkdir(parents=True, exist_ok=True)
    for name in ("generated", "processed", "validation", "validation_final", "selection", "final"):
        source = run_root / name
        if source.exists():
            shutil.copytree(source, attempt_root / name)
    return str(attempt_root)


def _selector_blocked_by_preprocessing_gate(raw_validation: dict[str, Any], *, variants: list[str]) -> dict[str, str]:
    errors: dict[str, str] = {}
    for variant in variants:
        variant_payload = raw_validation.get(variant, {})
        preprocessing_gate = variant_payload.get("preprocessing_gate", {}) if isinstance(variant_payload, dict) else {}
        if isinstance(preprocessing_gate, dict) and preprocessing_gate.get("usable") is False:
            errors[variant] = "mapping skipped because wall preprocessing produced no usable cleanup candidate"
    return errors


def _requires_mapping_selection(request_payload: dict[str, Any], *, variants: list[str]) -> bool:
    variant_profiles = request_payload.get("variant_profiles", {})
    if not isinstance(variant_profiles, dict):
        return False
    for variant in variants:
        selector_profile = str(variant_profiles.get(variant, {}).get("selector_profile", "")).strip().lower()
        if selector_profile == "wall":
            return True
    return False


def generate_reference_pair(spec_path: Path, *, max_attempts: int = 3) -> dict[str, Any]:
    if max_attempts <= 0:
        raise ReferencePairWorkflowError("max_attempts must be at least 1.")
    prepare_result = prepare_reference_pair_run(spec_path)
    run_root = Path(prepare_result["run_root"])
    request_payload = load_json(run_root / "request" / "request.json")
    provider_payload = request_payload["provider"]
    provider_name = provider_payload["name"]
    provider_mode = str(provider_payload.get("mode", "direct")).strip().lower() or "direct"
    model_payload = request_payload.get("model", {})
    model_name = str(model_payload.get("name", "")).strip().lower() or "mock"
    variants: list[str] = request_payload.get("variants", ["full", "half"])
    background = request_payload.get("background", {"mode": "transparent"})
    variant_profiles = request_payload.get("variant_profiles", {})
    selector_closed_loop_enabled, closed_loop_variants = _supports_selector_closed_loop(request_payload)
    requires_mapping_selection = _requires_mapping_selection(request_payload, variants=variants)

    attempts_payload: list[dict[str, Any]] = []
    previous_raw_validation: dict[str, Any] | None = None
    previous_final_validation: dict[str, Any] | None = None
    final_result: dict[str, Any] | None = None

    for attempt_index in range(1, max_attempts + 1):
        generation_logs: dict[str, Any] = {}
        generated_paths: dict[str, str] = {}
        for variant in variants:
            output_path = run_root / "generated" / f"generated_{variant}.png"
            raw_output_path = run_root / "generated" / f"generated_{variant}.raw.png"
            generation_inputs_raw = request_payload["generation_inputs"][variant]
            if isinstance(generation_inputs_raw, str):
                generation_input_paths = [Path(generation_inputs_raw)]
            elif isinstance(generation_inputs_raw, list) and generation_inputs_raw:
                generation_input_paths = [Path(str(value)) for value in generation_inputs_raw]
            else:
                raise ReferencePairWorkflowError(f"Invalid generation_inputs for variant '{variant}'.")
            generated_paths[variant] = str(output_path)
            selector_profile = ""
            if isinstance(variant_profiles, dict):
                selector_profile = str(variant_profiles.get(variant, {}).get("selector_profile", "")).strip().lower()
            prompt_text = str(request_payload["prompts"][variant])
            if attempt_index > 1:
                prompt_text = (
                    prompt_text
                    + "\n\n"
                    + _retry_suffix_from_failures(
                        variant=variant,
                        selector_profile=selector_profile,
                        raw_validation=previous_raw_validation,
                        final_validation=previous_final_validation,
                    )
                )
            prompt_attempt_path = run_root / "request" / f"prompt_{variant}.attempt_{attempt_index:02d}.txt"
            prompt_attempt_path.write_text(prompt_text + "\n", encoding="utf-8")
            if provider_mode == "agent_handoff":
                generation_logs[variant] = _ingest_agent_handoff_output(
                    run_root=run_root,
                    variant=variant,
                    request_payload=request_payload,
                    background=background,
                    output_path=output_path,
                    raw_output_path=raw_output_path,
                )
            elif provider_name == "mock":
                mock_source = Path(request_payload["references"][variant])
                shutil.copy2(mock_source, raw_output_path if background.get("mode") == "color_key" else output_path)
                generation_logs[variant] = {
                    "provider": "mock",
                    "copied_from": str(mock_source),
                    "note": "mock mode simulates a successful target-height transform",
                }
            else:
                generation_logs[variant] = generate_with_provider(
                    provider_name=provider_name,
                    model_name=model_name,
                    prompt_text=prompt_text,
                    reference_images=generation_input_paths,
                    output_path=raw_output_path if background.get("mode") == "color_key" else output_path,
                )
            _write_step1_raw_artifact(
                run_root,
                variant=variant,
                raw_image_path=raw_output_path if background.get("mode") == "color_key" else output_path,
            )
            generation_logs[variant]["attempt"] = attempt_index
            generation_logs[variant]["prompt_path"] = str(prompt_attempt_path)

        raw_validation = validate_reference_pair_run(run_root)
        selector_summary: dict[str, Any] | None = None
        final_validation: dict[str, Any] | None = None
        success = raw_validation["status"] == "pass"

        if selector_closed_loop_enabled:
            blocked_by_preprocessing = _selector_blocked_by_preprocessing_gate(raw_validation, variants=variants)
            if blocked_by_preprocessing:
                selector_summary = {
                    "ok": False,
                    "results": {},
                    "selected_outputs": {},
                    "errors": blocked_by_preprocessing,
                    "skipped_due_to_preprocessing_gate": True,
                }
            elif raw_validation["status"] == "pass" and not requires_mapping_selection:
                selector_summary = _copy_validated_outputs_to_final(run_root, raw_validation=raw_validation, variants=variants)
            else:
                selector_summary = _run_selector_closed_loop(
                    run_root,
                    request_payload=request_payload,
                    variants=variants,
                )
            if selector_summary["ok"]:
                _update_deliverable_manifest(
                    run_root,
                    selected_outputs=selector_summary["selected_outputs"],
                    workflow_status=str(selector_summary.get("mode", "selector_selected")),
                    selected_from_step=str(selector_summary.get("selected_from_step", "step_7_selection")),
                )
                final_validation = validate_reference_pair_run(
                    run_root,
                    variant_images={variant: Path(path) for variant, path in selector_summary["selected_outputs"].items()},
                    skip_preprocessing=True,
                    output_subdir="validation_final",
                    log_filename="validate.final.json",
                )
                success = final_validation["status"] == "pass"
            else:
                success = False

        attempt_payload = {
            "attempt": attempt_index,
            "generated_at": now_iso(),
            "generated": generated_paths,
            "generation": generation_logs,
            "raw_validation": raw_validation,
            "selection": selector_summary,
            "final_validation": final_validation,
        }
        attempt_payload["snapshot_root"] = _snapshot_attempt_state(run_root, attempt_number=attempt_index)
        attempts_payload.append(attempt_payload)
        previous_raw_validation = raw_validation
        previous_final_validation = final_validation
        final_result = attempt_payload
        if success:
            break

    if final_result is None:
        raise ReferencePairWorkflowError("reference pair generation did not execute any attempts.")

    closed_loop_mode = "selector_retry" if selector_closed_loop_enabled else "raw_validation_only"
    final_validation_result = final_result.get("final_validation")
    reported_validation = final_validation_result or final_result["raw_validation"]
    result = {
        "ok": bool(
            (final_validation_result and final_validation_result.get("status") == "pass")
            or (not selector_closed_loop_enabled and final_result["raw_validation"].get("status") == "pass")
        ),
        "run_root": str(run_root),
        "variants": variants,
        "generated": final_result["generated"],
        "validation": reported_validation,
        "raw_validation": final_result["raw_validation"],
        "final_validation": final_validation_result,
        "selection": final_result.get("selection"),
        "attempts": attempts_payload,
        "attempt_count": len(attempts_payload),
        "max_attempts": max_attempts,
        "closed_loop_mode": closed_loop_mode,
        "closed_loop_variants": closed_loop_variants,
    }
    write_json(
        run_root / "logs" / "generate.json",
        {
            "ok": result["ok"],
            "generated_at": now_iso(),
            "attempt_count": len(attempts_payload),
            "max_attempts": max_attempts,
            "closed_loop_mode": closed_loop_mode,
            "results": attempts_payload,
        },
    )
    return result


def alpha_mask(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    return alpha.point(lambda value: 255 if value >= ALPHA_THRESHOLD else 0, mode="L")


def parse_hex_color(value: str) -> tuple[int, int, int]:
    normalized = value.strip().lstrip("#")
    if len(normalized) != 6:
        raise ReferencePairWorkflowError(f"Invalid hex color '{value}'. Expected #RRGGBB.")
    try:
        return tuple(int(normalized[index : index + 2], 16) for index in range(0, 6, 2))  # type: ignore[return-value]
    except ValueError as error:
        raise ReferencePairWorkflowError(f"Invalid hex color '{value}'. Expected #RRGGBB.") from error


def pixel_matches_any_key(pixel: tuple[int, int, int, int], key_colors: list[tuple[int, int, int]], tolerance: int) -> bool:
    red, green, blue, _alpha = pixel
    for key_red, key_green, key_blue in key_colors:
        if (
            abs(red - key_red) <= tolerance
            and abs(green - key_green) <= tolerance
            and abs(blue - key_blue) <= tolerance
        ):
            return True
    return False


def color_key_pixel_mask(
    image: Image.Image,
    *,
    key_colors: list[tuple[int, int, int]],
    tolerance: int,
) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    mask = Image.new("L", rgba.size, 0)
    mask_pixels = mask.load()
    for y in range(height):
        for x in range(width):
            if pixel_matches_any_key(pixels[x, y], key_colors, tolerance):
                mask_pixels[x, y] = 255
    return mask


def color_key_connected_background_mask(
    image: Image.Image,
    *,
    key_colors: list[tuple[int, int, int]],
    tolerance: int,
) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    mask = Image.new("L", rgba.size, 0)
    mask_pixels = mask.load()
    queue: deque[tuple[int, int]] = deque()

    def enqueue_if_background(x: int, y: int) -> None:
        if mask_pixels[x, y] != 0:
            return
        if not pixel_matches_any_key(pixels[x, y], key_colors, tolerance):
            return
        mask_pixels[x, y] = 255
        queue.append((x, y))

    for x in range(width):
        enqueue_if_background(x, 0)
        enqueue_if_background(x, height - 1)
    for y in range(height):
        enqueue_if_background(0, y)
        enqueue_if_background(width - 1, y)

    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            next_x = x + dx
            next_y = y + dy
            if 0 <= next_x < width and 0 <= next_y < height:
                enqueue_if_background(next_x, next_y)
    return mask


def color_distance(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int]) -> float:
    return (
        (rgb_a[0] - rgb_b[0]) ** 2
        + (rgb_a[1] - rgb_b[1]) ** 2
        + (rgb_a[2] - rgb_b[2]) ** 2
    ) ** 0.5


def color_key_similarity(rgb: tuple[int, int, int], key_color: tuple[int, int, int]) -> float:
    max_distance = (3 * (255**2)) ** 0.5
    return max(0.0, 1.0 - (color_distance(rgb, key_color) / max_distance))


def best_key_color_match(
    rgb: tuple[int, int, int],
    key_colors: list[tuple[int, int, int]],
) -> tuple[tuple[int, int, int], float]:
    best_color = key_colors[0]
    best_similarity = color_key_similarity(rgb, best_color)
    for key_color in key_colors[1:]:
        similarity = color_key_similarity(rgb, key_color)
        if similarity > best_similarity:
            best_color = key_color
            best_similarity = similarity
    return best_color, best_similarity


def detect_active_key_color(
    image: Image.Image,
    *,
    key_colors: list[tuple[int, int, int]],
) -> tuple[tuple[int, int, int], dict[str, Any]]:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    scores = {key_color: 0.0 for key_color in key_colors}
    sample_count = 0

    def sample_pixel(x: int, y: int) -> None:
        nonlocal sample_count
        red, green, blue, _alpha = pixels[x, y]
        rgb = (red, green, blue)
        for key_color in key_colors:
            scores[key_color] += color_key_similarity(rgb, key_color)
        sample_count += 1

    for x in range(width):
        sample_pixel(x, 0)
        sample_pixel(x, height - 1)
    for y in range(1, height - 1):
        sample_pixel(0, y)
        sample_pixel(width - 1, y)

    best_color = max(scores, key=scores.get)
    normalized_scores = {
        "#{:02X}{:02X}{:02X}".format(*key_color): (scores[key_color] / sample_count if sample_count else 0.0)
        for key_color in key_colors
    }
    return best_color, {
        "detected_active_key_color": "#{:02X}{:02X}{:02X}".format(*best_color),
        "border_similarity_scores": normalized_scores,
        "border_sample_count": sample_count,
    }


def opaque_edge_distance(alpha: Image.Image, *, max_distance: int) -> list[list[int | None]]:
    width, height = alpha.size
    alpha_pixels = alpha.load()
    distances: list[list[int | None]] = [[None for _ in range(width)] for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()

    for y in range(height):
        for x in range(width):
            if alpha_pixels[x, y] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = x + dx
                ny = y + dy
                if nx < 0 or nx >= width or ny < 0 or ny >= height or alpha_pixels[nx, ny] == 0:
                    distances[y][x] = 1
                    queue.append((x, y))
                    break

    while queue:
        x, y = queue.popleft()
        current_distance = distances[y][x]
        if current_distance is None or current_distance >= max_distance:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x + dx
            ny = y + dy
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue
            if alpha_pixels[nx, ny] == 0 or distances[ny][nx] is not None:
                continue
            distances[ny][nx] = current_distance + 1
            queue.append((nx, ny))
    return distances


def average_neighbor_color(
    pixels: Any,
    alpha_pixels: Any,
    edge_distances: list[list[int | None]],
    *,
    center_x: int,
    center_y: int,
    min_edge_distance: int,
    search_radius: int,
    key_colors: list[tuple[int, int, int]],
) -> tuple[int, int, int] | None:
    width = len(edge_distances[0]) if edge_distances else 0
    height = len(edge_distances)
    total_red = 0
    total_green = 0
    total_blue = 0
    count = 0
    for dy in range(-search_radius, search_radius + 1):
        y = center_y + dy
        if y < 0 or y >= height:
            continue
        for dx in range(-search_radius, search_radius + 1):
            x = center_x + dx
            if x < 0 or x >= width:
                continue
            if dx == 0 and dy == 0:
                continue
            if alpha_pixels[x, y] == 0:
                continue
            neighbor_distance = edge_distances[y][x]
            if neighbor_distance is None or neighbor_distance < min_edge_distance:
                continue
            red, green, blue, _alpha = pixels[x, y]
            _matched_key, similarity = best_key_color_match((red, green, blue), key_colors)
            if similarity > 0.55:
                continue
            total_red += red
            total_green += green
            total_blue += blue
            count += 1
    if count == 0:
        return None
    return (round(total_red / count), round(total_green / count), round(total_blue / count))


def despill_key_fringe(
    image: Image.Image,
    *,
    key_colors: list[tuple[int, int, int]],
    max_edge_distance: int = 7,
    delete_similarity_threshold: float = 0.48,
    recolor_similarity_threshold: float = 0.18,
    neighbor_search_radius: int = 5,
    passes: int = 3,
) -> tuple[Image.Image, dict[str, Any]]:
    result = image.convert("RGBA").copy()
    pixels = result.load()
    alpha = result.getchannel("A")
    alpha_pixels = alpha.load()
    edge_distances = opaque_edge_distance(alpha, max_distance=max_edge_distance + neighbor_search_radius)
    changed_pixels = 0
    deleted_pixels = 0
    recolored_pixels = 0

    for _pass_index in range(passes):
        for y in range(result.height):
            for x in range(result.width):
                if alpha_pixels[x, y] == 0:
                    continue
                edge_distance = edge_distances[y][x]
                if edge_distance is None or edge_distance > max_edge_distance:
                    continue
                red, green, blue, alpha_value = pixels[x, y]
                matched_key, similarity = best_key_color_match((red, green, blue), key_colors)
                if similarity < recolor_similarity_threshold:
                    continue
                if similarity >= delete_similarity_threshold:
                    pixels[x, y] = (red, green, blue, 0)
                    alpha_pixels[x, y] = 0
                    changed_pixels += 1
                    deleted_pixels += 1
                    continue
                neighbor_color = average_neighbor_color(
                    pixels,
                    alpha_pixels,
                    edge_distances,
                    center_x=x,
                    center_y=y,
                    min_edge_distance=edge_distance + 1,
                    search_radius=neighbor_search_radius,
                    key_colors=key_colors,
                )
                if neighbor_color is None:
                    continue
                if neighbor_color != (red, green, blue):
                    pixels[x, y] = (neighbor_color[0], neighbor_color[1], neighbor_color[2], alpha_value)
                    changed_pixels += 1
                    recolored_pixels += 1
        alpha = result.getchannel("A")
        alpha_pixels = alpha.load()
        edge_distances = opaque_edge_distance(alpha, max_distance=max_edge_distance + neighbor_search_radius)

    return result, {
        "despill_enabled": True,
        "key_colors": ["#{:02X}{:02X}{:02X}".format(*key_color) for key_color in key_colors],
        "max_edge_distance": max_edge_distance,
        "delete_similarity_threshold": delete_similarity_threshold,
        "recolor_similarity_threshold": recolor_similarity_threshold,
        "neighbor_search_radius": neighbor_search_radius,
        "passes": passes,
        "changed_pixels": changed_pixels,
        "deleted_pixels": deleted_pixels,
        "recolored_pixels": recolored_pixels,
        "mode": "delete_near_purple_else_recolor_to_edge",
    }


COLOR_KEY_VARIANT_SPECS = [
    {
        "name": "01_conservative",
        "label": "Conservative",
        "max_edge_distance": 4,
        "delete_similarity_threshold": 0.60,
        "recolor_similarity_threshold": 0.26,
        "neighbor_search_radius": 4,
        "passes": 2,
        "is_default": False,
    },
    {
        "name": "02_conservative_plus",
        "label": "Conservative+",
        "max_edge_distance": 5,
        "delete_similarity_threshold": 0.56,
        "recolor_similarity_threshold": 0.24,
        "neighbor_search_radius": 4,
        "passes": 2,
        "is_default": False,
    },
    {
        "name": "03_balanced",
        "label": "Balanced",
        "max_edge_distance": 7,
        "delete_similarity_threshold": 0.48,
        "recolor_similarity_threshold": 0.18,
        "neighbor_search_radius": 5,
        "passes": 3,
        "is_default": True,
    },
    {
        "name": "04_balanced_plus",
        "label": "Balanced+",
        "max_edge_distance": 8,
        "delete_similarity_threshold": 0.46,
        "recolor_similarity_threshold": 0.16,
        "neighbor_search_radius": 5,
        "passes": 3,
        "is_default": False,
    },
    {
        "name": "05_aggressive",
        "label": "Aggressive",
        "max_edge_distance": 9,
        "delete_similarity_threshold": 0.42,
        "recolor_similarity_threshold": 0.14,
        "neighbor_search_radius": 6,
        "passes": 4,
        "is_default": False,
    },
    {
        "name": "06_aggressive_plus",
        "label": "Aggressive+",
        "max_edge_distance": 10,
        "delete_similarity_threshold": 0.39,
        "recolor_similarity_threshold": 0.12,
        "neighbor_search_radius": 6,
        "passes": 4,
        "is_default": False,
    },
]


def default_cleanup_variant_name() -> str:
    for variant_spec in COLOR_KEY_VARIANT_SPECS:
        if bool(variant_spec.get("is_default")):
            return str(variant_spec["name"])
    raise ReferencePairWorkflowError("No default cleanup variant was configured.")


def write_preview_variants(image: Image.Image, output_path: Path, variant_name: str) -> dict[str, str]:
    preview_paths: dict[str, str] = {}
    for background_rgba, suffix in (((240, 240, 240, 255), "light"), ((32, 32, 32, 255), "dark")):
        canvas = Image.new("RGBA", image.size, background_rgba)
        canvas.alpha_composite(image)
        preview_path = output_path.with_name(f"{output_path.stem}.{variant_name}.preview_{suffix}{output_path.suffix}")
        canvas.save(preview_path)
        preview_paths[suffix] = str(preview_path)
    return preview_paths


def mirror_variant_pool_to_generated(run_root: Path, *, variant: str, preprocessing_payload: dict[str, Any]) -> None:
    generated_dir = run_root / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    variants_payload = preprocessing_payload.get("variants", {})
    if not isinstance(variants_payload, dict):
        return
    for variant_name, variant_info in variants_payload.items():
        if not isinstance(variant_info, dict):
            continue
        output_value = variant_info.get("output")
        if not output_value:
            continue
        source_path = Path(str(output_value))
        if not source_path.exists():
            continue
        destination_path = generated_dir / f"generated_{variant}.{variant_name}{source_path.suffix}"
        shutil.copy2(source_path, destination_path)


def apply_color_key_to_image(
    image_path: Path,
    output_path: Path,
    *,
    prompt_color: str,
    fallback_colors: list[str],
    tolerance: int,
    emit_variant_pool: bool = False,
    remove_all_key_pixels: bool = False,
) -> dict[str, Any]:
    image = Image.open(image_path).convert("RGBA")
    colors = [parse_hex_color(prompt_color), *(parse_hex_color(color) for color in fallback_colors)]
    connected_background_mask = color_key_connected_background_mask(image, key_colors=colors, tolerance=tolerance)
    all_key_mask = color_key_pixel_mask(image, key_colors=colors, tolerance=tolerance)
    background_mask = ImageChops.lighter(connected_background_mask, all_key_mask) if remove_all_key_pixels else connected_background_mask
    active_key_color, detection_stats = detect_active_key_color(image, key_colors=colors)
    masked_result = image.copy()
    masked_result.putalpha(ImageChops.subtract(masked_result.getchannel("A"), background_mask))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not emit_variant_pool:
        result, despill_stats = despill_key_fringe(masked_result, key_colors=[active_key_color])
        result.save(output_path)
        variants_payload = {}
        selected_variant_name = default_cleanup_variant_name()
    else:
        variants_payload = {}
        selected_variant_name = default_cleanup_variant_name()
        despill_stats = None
        for variant_spec in COLOR_KEY_VARIANT_SPECS:
            variant_image, variant_stats = despill_key_fringe(
                masked_result.copy(),
                key_colors=[active_key_color],
                max_edge_distance=int(variant_spec["max_edge_distance"]),
                delete_similarity_threshold=float(variant_spec["delete_similarity_threshold"]),
                recolor_similarity_threshold=float(variant_spec["recolor_similarity_threshold"]),
                neighbor_search_radius=int(variant_spec["neighbor_search_radius"]),
                passes=int(variant_spec["passes"]),
            )
            variant_output_path = output_path.with_name(f"{output_path.stem}.{variant_spec['name']}{output_path.suffix}")
            variant_image.save(variant_output_path)
            preview_paths = write_preview_variants(variant_image, output_path, str(variant_spec["name"]))
            variants_payload[str(variant_spec["name"])] = {
                "label": variant_spec["label"],
                "output": str(variant_output_path),
                "previews": preview_paths,
                "despill": variant_stats,
            }
        if selected_variant_name not in variants_payload:
            raise ReferencePairWorkflowError("No default color-key variant was configured.")

    return {
        "input": str(image_path),
        "prompt_color": prompt_color,
        "fallback_colors": fallback_colors,
        "tolerance": tolerance,
        "remove_all_key_pixels": remove_all_key_pixels,
        "removed_background_pixels": mask_area(background_mask),
        "removed_connected_background_pixels": mask_area(connected_background_mask),
        "removed_internal_key_pixels": max(0, mask_area(background_mask) - mask_area(connected_background_mask)),
        "active_key_color": detection_stats["detected_active_key_color"],
        "key_color_detection": detection_stats,
        "variants": variants_payload,
        "despill": despill_stats,
    }


def default_cleanup_candidate_path(preprocessing_payload: dict[str, Any]) -> Path:
    variants_payload = preprocessing_payload.get("variants", {})
    if not isinstance(variants_payload, dict):
        raise ReferencePairWorkflowError("Cleanup preprocessing payload is missing variant outputs.")
    default_name = default_cleanup_variant_name()
    default_payload = variants_payload.get(default_name, {})
    if not isinstance(default_payload, dict) or not default_payload.get("output"):
        raise ReferencePairWorkflowError(f"Cleanup preprocessing payload is missing the default candidate '{default_name}'.")
    return Path(str(default_payload["output"]))


def _write_step1_raw_artifact(run_root: Path, *, variant: str, raw_image_path: Path) -> None:
    copied = _copy_artifact(raw_image_path, run_root / "step_1_raw" / f"s1_raw.{variant}{raw_image_path.suffix}")
    update_step_status_summary(
        run_root,
        variant=variant,
        step_key="step_1_raw",
        status="ok" if copied else "missing_output",
        summary="raw generation output written" if copied else "raw generation output missing",
        primary_artifact=copied,
        details_path=None,
    )


def run_cleanup_variant_pool(
    run_root: Path,
    *,
    variant: str,
    raw_image_path: Path,
    background: dict[str, Any],
) -> dict[str, Any]:
    keyed_output_path = run_root / "processed" / f"generated_{variant}.keyed.png"
    if keyed_output_path.exists():
        keyed_output_path.unlink()
    preprocessing_payload = apply_color_key_to_image(
        raw_image_path,
        keyed_output_path,
        prompt_color=str(background.get("prompt_color", "#FF00FF")),
        fallback_colors=list(background.get("fallback_colors", ["#00FF00"])),
        tolerance=int(background.get("tolerance", 24)),
        emit_variant_pool=True,
    )
    mirror_variant_pool_to_generated(run_root, variant=variant, preprocessing_payload=preprocessing_payload)
    _write_step3_cleanup_artifacts(run_root, variant=variant, preprocessing_payload=preprocessing_payload)
    return preprocessing_payload


def _write_step3_cleanup_artifacts(run_root: Path, *, variant: str, preprocessing_payload: dict[str, Any]) -> None:
    candidates: list[dict[str, Any]] = []
    variants_payload = preprocessing_payload.get("variants", {})
    if not isinstance(variants_payload, dict):
        variants_payload = {}
    for cleanup_name, variant_info in variants_payload.items():
        if not isinstance(variant_info, dict):
            continue
        source_path_raw = variant_info.get("output")
        if not source_path_raw:
            continue
        source_path = Path(str(source_path_raw))
        cleanup_token = _cleanup_artifact_token(str(cleanup_name))
        artifact_path = run_root / "step_3_cleanup_pool" / f"s3_cleanup.{variant}.{cleanup_token}{source_path.suffix}"
        copied_path = _copy_artifact(source_path, artifact_path)
        candidates.append(
            {
                "cleanup_id": cleanup_token,
                "cleanup_name": cleanup_name,
                "path": copied_path or str(source_path),
                "label": variant_info.get("label"),
                "despill": variant_info.get("despill"),
                "previews": variant_info.get("previews", []),
            }
        )
    write_json(
        run_root / "step_3_cleanup_pool" / f"s3_cleanup.{variant}.json",
        {
            "variant": variant,
            "active_key_color": preprocessing_payload.get("active_key_color"),
            "candidates": candidates,
        },
    )
    update_step_status_summary(
        run_root,
        variant=variant,
        step_key="step_3_cleanup_pool",
        status="ok" if candidates else "empty",
        summary=f"{len(candidates)} cleanup candidates exported",
        primary_artifact=candidates[0]["path"] if candidates else None,
        details_path=str(run_root / "step_3_cleanup_pool" / f"s3_cleanup.{variant}.json"),
    )


def _write_step4_gate_artifacts(run_root: Path, *, variant: str, preprocessing_gate: dict[str, Any]) -> None:
    pass_example = None
    fail_example = None
    usable_candidates = preprocessing_gate.get("usable_candidates", [])
    rejected_candidates = preprocessing_gate.get("rejected_candidates", [])
    if isinstance(usable_candidates, list) and usable_candidates:
        path_raw = usable_candidates[0].get("path")
        if path_raw:
            src = Path(str(path_raw))
            pass_example = _copy_artifact(src, run_root / "step_4_gate" / f"s4_gate_pass_example.{variant}{src.suffix}")
    if isinstance(rejected_candidates, list) and rejected_candidates:
        path_raw = rejected_candidates[0].get("path")
        if path_raw:
            src = Path(str(path_raw))
            fail_example = _copy_artifact(src, run_root / "step_4_gate" / f"s4_gate_fail_example.{variant}{src.suffix}")
    write_json(
        run_root / "step_4_gate" / f"s4_gate.{variant}.json",
        {
            "variant": variant,
            "usable": bool(preprocessing_gate.get("usable")),
            "chosen_candidate": preprocessing_gate.get("chosen_candidate"),
            "active_key_color": preprocessing_gate.get("active_key_color"),
            "removed_background_pixels": preprocessing_gate.get("removed_background_pixels"),
            "primary_pass_example": pass_example,
            "primary_fail_example": fail_example,
            "usable_candidate_ids": [Path(str(item.get("path", ""))).name for item in usable_candidates if isinstance(item, dict)],
            "rejected_candidate_ids": [Path(str(item.get("path", ""))).name for item in rejected_candidates if isinstance(item, dict)],
            "usable_candidates": usable_candidates,
            "rejected_candidates": rejected_candidates,
        },
    )
    update_step_status_summary(
        run_root,
        variant=variant,
        step_key="step_4_gate",
        status="pass" if bool(preprocessing_gate.get("usable")) else "fail",
        summary="usable cleanup candidate found and chosen" if bool(preprocessing_gate.get("usable")) else "no usable cleanup candidate",
        primary_artifact=pass_example or fail_example,
        details_path=str(run_root / "step_4_gate" / f"s4_gate.{variant}.json"),
    )


def _update_deliverable_manifest(
    run_root: Path,
    *,
    selected_outputs: dict[str, str],
    workflow_status: str,
    selected_from_step: str,
) -> None:
    deliverables_dir = run_root / "deliverables"
    deliverables_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = deliverables_dir / "deliverable_manifest.json"
    existing = load_json(manifest_path) if manifest_path.exists() else {}
    deliverables: list[dict[str, Any]] = []
    for variant, output_path in sorted(selected_outputs.items()):
        deliverable_path = deliverables_dir / f"deliverable.{variant}{Path(output_path).suffix}"
        copied_path = _copy_artifact(Path(output_path), deliverable_path)
        deliverables.append(
            {
                "variant": variant,
                "path": copied_path or output_path,
                "selected_from_candidate": Path(output_path).name,
                "selected_from_step": selected_from_step,
            }
        )
        update_step_status_summary(
            run_root,
            variant=variant,
            step_key="deliverable",
            status="ok" if copied_path else "missing_output",
            summary="final deliverable written" if copied_path else "final deliverable missing",
            primary_artifact=copied_path,
            details_path=str(deliverables_dir / "deliverable_manifest.json"),
        )
    payload = {
        "run_root": str(run_root),
        "variants": [item["variant"] for item in deliverables],
        "deliverables": deliverables,
        "workflow_status": workflow_status,
    }
    if isinstance(existing, dict):
        payload = {**existing, **payload}
    write_json(manifest_path, payload)


def update_step_status_summary(
    run_root: Path,
    *,
    variant: str,
    step_key: str,
    status: str,
    summary: str,
    primary_artifact: str | None = None,
    details_path: str | None = None,
) -> None:
    summary_path = run_root / "artifact_status.json"
    payload = load_json(summary_path) if summary_path.exists() else {"variants": {}}
    variants_payload = payload.get("variants", {})
    if not isinstance(variants_payload, dict):
        variants_payload = {}
    variant_payload = variants_payload.get(variant, {})
    if not isinstance(variant_payload, dict):
        variant_payload = {}
    variant_payload[step_key] = {
        "status": status,
        "summary": summary,
        "primary_artifact": primary_artifact,
        "details_path": details_path,
    }
    variants_payload[variant] = variant_payload
    payload["variants"] = variants_payload
    write_json(summary_path, payload)


def mask_area(mask: Image.Image) -> int:
    histogram = mask.histogram()
    return int(histogram[255]) if len(histogram) > 255 else 0


def mask_center(mask: Image.Image) -> tuple[float, float] | None:
    bbox = mask.getbbox()
    if bbox is None:
        return None
    pixels = mask.load()
    sum_x = 0.0
    sum_y = 0.0
    count = 0
    for y in range(mask.height):
        for x in range(mask.width):
            if pixels[x, y] >= 128:
                sum_x += x
                sum_y += y
                count += 1
    if count == 0:
        return None
    return (sum_x / count, sum_y / count)


def pair_metrics(image_path: Path) -> PairMetrics:
    image = Image.open(image_path).convert("RGBA")
    return pair_metrics_from_image(image, image_path=image_path)


def pair_metrics_from_image(image: Image.Image, *, image_path: Path | None = None) -> PairMetrics:
    mask = alpha_mask(image)
    return PairMetrics(
        image_path=str(image_path) if image_path is not None else "<in-memory>",
        size=image.size,
        bbox=mask.getbbox(),
        area_pixels=mask_area(mask),
        center=mask_center(mask),
    )


def _wall_preprocessing_gate(
    *,
    reference_path: Path,
    preprocessing_payload: dict[str, Any],
) -> dict[str, Any]:
    from pipeline.variant_selector import FAIL_RULES_BY_VARIANT, exterior_background_residue_check

    active_key_color = str(preprocessing_payload.get("active_key_color", "")).strip().upper()
    variant_entries = preprocessing_payload.get("variants", {})
    seen: set[str] = set()
    reference_metrics = pair_metrics(reference_path)
    usable_candidates: list[dict[str, Any]] = []
    rejected_candidates: list[dict[str, Any]] = []
    fail_rules = FAIL_RULES_BY_VARIANT["wall"]
    for variant_spec in COLOR_KEY_VARIANT_SPECS:
        cleanup_name = str(variant_spec["name"])
        variant_payload = variant_entries.get(cleanup_name, {}) if isinstance(variant_entries, dict) else {}
        candidate_output = variant_payload.get("output") if isinstance(variant_payload, dict) else None
        if not candidate_output:
            rejected_candidates.append(
                {
                    "cleanup_name": cleanup_name,
                    "cleanup_id": _cleanup_artifact_token(cleanup_name),
                    "label": variant_spec.get("label"),
                    "path": None,
                    "reject_reasons": ["missing_candidate_output"],
                }
            )
            continue
        candidate_path = Path(str(candidate_output))
        candidate_key = str(candidate_path)
        if candidate_key in seen or not candidate_path.exists():
            rejected_candidates.append(
                {
                    "cleanup_name": cleanup_name,
                    "cleanup_id": _cleanup_artifact_token(cleanup_name),
                    "label": variant_spec.get("label"),
                    "path": str(candidate_path),
                    "reject_reasons": ["missing_candidate_file"],
                }
            )
            continue
        seen.add(candidate_key)
        metrics = pair_metrics(candidate_path)
        bbox = metrics.bbox
        non_transparent_canvas = bbox == (0, 0, metrics.size[0], metrics.size[1])
        contamination = (
            exterior_background_residue_check(candidate_path, active_key_color=active_key_color, fail_rules=fail_rules)
            if active_key_color
            else {"fail": True, "reason": "missing_active_key_color"}
        )
        candidate_info = {
            "cleanup_name": cleanup_name,
            "cleanup_id": _cleanup_artifact_token(cleanup_name),
            "label": variant_spec.get("label"),
            "path": str(candidate_path),
            "bbox": list(bbox) if bbox is not None else None,
            "area_pixels": metrics.area_pixels,
            "non_transparent_canvas": non_transparent_canvas,
            "background_residue_check": contamination,
        }
        reject_reasons: list[str] = []
        if bbox is None:
            reject_reasons.append("missing_opaque_bbox")
        if non_transparent_canvas:
            reject_reasons.append("full_canvas_foreground")
        if contamination.get("fail", False):
            reject_reasons.append("background_residue_detected")
        if reference_metrics.area_pixels > 0 and metrics.area_pixels <= 0:
            reject_reasons.append("zero_effective_area")
        if reject_reasons:
            candidate_info["reject_reasons"] = reject_reasons
            rejected_candidates.append(candidate_info)
            continue
        usable_candidates.append(candidate_info)

    chosen_candidate = usable_candidates[0] if usable_candidates else None
    return {
        "usable": chosen_candidate is not None,
        "chosen_candidate": chosen_candidate,
        "active_key_color": active_key_color,
        "removed_background_pixels": int(preprocessing_payload.get("removed_background_pixels", 0)),
        "usable_candidates": usable_candidates,
        "rejected_candidates": rejected_candidates,
    }


def intersection_over_union(mask_a: Image.Image, mask_b: Image.Image) -> float:
    intersection = ImageChops.multiply(mask_a, mask_b)
    union = ImageChops.lighter(mask_a, mask_b)
    intersection_area = mask_area(intersection)
    union_area = mask_area(union)
    if union_area == 0:
        return 0.0
    return intersection_area / union_area


def bbox_deltas(bbox_a: tuple[int, int, int, int] | None, bbox_b: tuple[int, int, int, int] | None) -> dict[str, int] | None:
    if bbox_a is None or bbox_b is None:
        return None
    return {
        "left": bbox_b[0] - bbox_a[0],
        "top": bbox_b[1] - bbox_a[1],
        "right": bbox_b[2] - bbox_a[2],
        "bottom": bbox_b[3] - bbox_a[3],
        "width": (bbox_b[2] - bbox_b[0]) - (bbox_a[2] - bbox_a[0]),
        "height": (bbox_b[3] - bbox_b[1]) - (bbox_a[3] - bbox_a[1]),
    }


def mask_visual(mask: Image.Image, color: tuple[int, int, int, int]) -> Image.Image:
    rgba = Image.new("RGBA", mask.size, color)
    transparent = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    return Image.composite(rgba, transparent, mask)


def align_generated_to_reference_canvas(reference: Image.Image, generated: Image.Image) -> tuple[Image.Image, dict[str, Any] | None]:
    if reference.size == generated.size:
        return generated, None
    return (
        generated.resize(reference.size, Image.Resampling.LANCZOS),
        {
            "reference_size": list(reference.size),
            "generated_size": list(generated.size),
            "action": "resized_generated_to_reference_canvas",
        },
    )


WALL_NORMALIZED_VALIDATION = {
    "target_size": 128,
    "min_normalized_iou": 0.90,
    "max_anchor_error": 10.0,
}
WALL_RAW_OVERRIDE = {
    "max_bbox_delta_hard_fail": 56,
    "max_bbox_delta_soft_fail": 24,
}


def _effective_bbox(mask: Image.Image) -> tuple[int, int, int, int]:
    bbox = mask.getbbox()
    if bbox is None:
        raise ReferencePairWorkflowError("Mask has no opaque pixels.")
    left, top, right, bottom = bbox
    return left, top, right - 1, bottom - 1


def _normalize_mask(mask: Image.Image, *, target_size: int = 128) -> tuple[Image.Image, tuple[int, int, int, int]]:
    left, top, right, bottom = _effective_bbox(mask)
    cropped = mask.crop((left, top, right + 1, bottom + 1))
    normalized = cropped.resize((target_size, target_size), Image.NEAREST)
    return normalized, (left, top, right, bottom)


def _find_anchor(mask: Image.Image, target_y: int, side: str) -> tuple[int, int] | None:
    search_order = [0]
    for delta in range(1, mask.height):
        search_order.extend((delta, -delta))
    pixels = mask.load()
    for delta in search_order:
        y = target_y + delta
        if y < 0 or y >= mask.height:
            continue
        xs = [x for x in range(mask.width) if pixels[x, y] >= 128]
        if not xs:
            continue
        if side == "left":
            return min(xs), y
        if side == "right":
            return max(xs), y
    return None


def _mask_anchors(mask: Image.Image) -> dict[str, tuple[int, int] | None]:
    bbox = mask.getbbox()
    if bbox is None:
        return {"left_shoulder": None, "right_shoulder": None, "left_mid": None, "right_mid": None, "bottom_tip": None}
    left, top, right, bottom = bbox
    height = bottom - top
    shoulder_y = top + max(1, int(round(height * 0.18)))
    mid_y = top + max(1, int(round(height * 0.56)))
    pixels = mask.load()
    bottom_points = [(x, bottom - 1) for x in range(mask.width) if pixels[x, bottom - 1] >= 128]
    bottom_tip = None
    if bottom_points:
        bottom_tip = bottom_points[len(bottom_points) // 2]
    return {
        "left_shoulder": _find_anchor(mask, shoulder_y, "left"),
        "right_shoulder": _find_anchor(mask, shoulder_y, "right"),
        "left_mid": _find_anchor(mask, mid_y, "left"),
        "right_mid": _find_anchor(mask, mid_y, "right"),
        "bottom_tip": bottom_tip,
    }


def _anchor_error(candidate: dict[str, tuple[int, int] | None], reference: dict[str, tuple[int, int] | None]) -> float:
    total = 0.0
    count = 0
    for key, ref_value in reference.items():
        cand_value = candidate.get(key)
        if ref_value is None or cand_value is None:
            total += 128.0
            count += 1
            continue
        total += abs(cand_value[0] - ref_value[0]) + abs(cand_value[1] - ref_value[1])
        count += 1
    return total / count if count else 999.0


def wall_normalized_diagnostics(reference_image: Image.Image, generated_image: Image.Image) -> dict[str, Any]:
    reference_mask = alpha_mask(reference_image)
    generated_mask = alpha_mask(generated_image)
    normalized_reference_mask, reference_bbox = _normalize_mask(
        reference_mask, target_size=int(WALL_NORMALIZED_VALIDATION["target_size"])
    )
    normalized_generated_mask, generated_bbox = _normalize_mask(
        generated_mask, target_size=int(WALL_NORMALIZED_VALIDATION["target_size"])
    )
    reference_anchors = _mask_anchors(normalized_reference_mask)
    generated_anchors = _mask_anchors(normalized_generated_mask)
    return {
        "normalized_iou": intersection_over_union(normalized_reference_mask, normalized_generated_mask),
        "anchor_error": _anchor_error(generated_anchors, reference_anchors),
        "reference_effective_bbox": {
            "left": reference_bbox[0],
            "top": reference_bbox[1],
            "right": reference_bbox[2],
            "bottom": reference_bbox[3],
            "width": reference_bbox[2] - reference_bbox[0] + 1,
            "height": reference_bbox[3] - reference_bbox[1] + 1,
        },
        "generated_effective_bbox": {
            "left": generated_bbox[0],
            "top": generated_bbox[1],
            "right": generated_bbox[2],
            "bottom": generated_bbox[3],
            "width": generated_bbox[2] - generated_bbox[0] + 1,
            "height": generated_bbox[3] - generated_bbox[1] + 1,
        },
        "reference_anchors": {key: list(value) if value is not None else None for key, value in reference_anchors.items()},
        "generated_anchors": {key: list(value) if value is not None else None for key, value in generated_anchors.items()},
    }


def create_overlay(reference_path: Path, generated_path: Path, output_path: Path) -> None:
    reference = Image.open(reference_path).convert("RGBA")
    generated = Image.open(generated_path).convert("RGBA")
    generated, _alignment = align_generated_to_reference_canvas(reference, generated)
    ref_mask = alpha_mask(reference)
    gen_mask = alpha_mask(generated)
    ref_outline = ImageChops.subtract(ref_mask.filter(ImageFilter.MaxFilter(3)), ref_mask)
    gen_outline = ImageChops.subtract(gen_mask.filter(ImageFilter.MaxFilter(3)), gen_mask)
    canvas = Image.new("RGBA", reference.size, (0, 0, 0, 0))
    canvas.alpha_composite(reference)
    canvas.alpha_composite(mask_visual(ref_outline, (80, 255, 120, 220)))
    canvas.alpha_composite(mask_visual(gen_outline, (255, 64, 220, 220)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def create_diff_mask(reference_path: Path, generated_path: Path, output_path: Path) -> None:
    reference = Image.open(reference_path).convert("RGBA")
    generated = Image.open(generated_path).convert("RGBA")
    generated, _alignment = align_generated_to_reference_canvas(reference, generated)
    ref_mask = alpha_mask(reference)
    gen_mask = alpha_mask(generated)
    added = ImageChops.subtract(gen_mask, ref_mask)
    removed = ImageChops.subtract(ref_mask, gen_mask)
    canvas = Image.new("RGBA", reference.size, (0, 0, 0, 0))
    canvas.alpha_composite(mask_visual(removed, (255, 80, 80, 220)))
    canvas.alpha_composite(mask_visual(added, (80, 180, 255, 220)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)


def validate_single_pair(
    reference_path: Path,
    generated_path: Path,
    thresholds: dict[str, Any],
    *,
    selector_profile: str = "",
) -> dict[str, Any]:
    reference_image = Image.open(reference_path).convert("RGBA")
    generated_image = Image.open(generated_path).convert("RGBA")
    generated_image, canvas_alignment = align_generated_to_reference_canvas(reference_image, generated_image)

    reference_mask = alpha_mask(reference_image)
    generated_mask = alpha_mask(generated_image)
    reference_metrics = pair_metrics_from_image(reference_image, image_path=reference_path)
    generated_metrics = pair_metrics_from_image(generated_image, image_path=generated_path)
    iou = intersection_over_union(reference_mask, generated_mask)
    deltas = bbox_deltas(reference_metrics.bbox, generated_metrics.bbox)
    non_transparent_canvas = generated_metrics.bbox == (0, 0, generated_image.width, generated_image.height)
    wall_diagnostics: dict[str, Any] | None = None

    failures: list[str] = []
    severity = "pass"
    if generated_metrics.bbox is None:
        failures.append("generated image has no opaque tile silhouette")
        severity = "hard_fail"
    if non_transparent_canvas:
        failures.append("generated image appears to fill the whole canvas; background may not be transparent")
        severity = "hard_fail"
    if iou < thresholds["iou_hard_fail"]:
        failures.append(f"silhouette IOU too low: {iou:.4f}")
        severity = "hard_fail"
    elif iou < thresholds["iou_soft_fail"] and severity != "hard_fail":
        failures.append(f"silhouette IOU drift: {iou:.4f}")
        severity = "soft_fail"
    if deltas is not None:
        max_bbox_delta = max(abs(value) for value in deltas.values())
        if max_bbox_delta > thresholds["bbox_delta_hard_fail"]:
            failures.append(f"bbox delta too large: {deltas}")
            severity = "hard_fail"
        elif max_bbox_delta > thresholds["bbox_delta_soft_fail"] and severity == "pass":
            failures.append(f"bbox delta drift: {deltas}")
            severity = "soft_fail"

    if selector_profile == "wall" and generated_metrics.bbox is not None and not non_transparent_canvas:
        wall_diagnostics = wall_normalized_diagnostics(reference_image, generated_image)
        normalized_iou = float(wall_diagnostics["normalized_iou"])
        anchor_error = float(wall_diagnostics["anchor_error"])
        max_bbox_delta = max(abs(value) for value in deltas.values()) if deltas is not None else 0
        normalized_gate_passed = (
            normalized_iou >= float(WALL_NORMALIZED_VALIDATION["min_normalized_iou"])
            and anchor_error <= float(WALL_NORMALIZED_VALIDATION["max_anchor_error"])
        )
        if normalized_gate_passed and severity == "hard_fail":
            retained_failures: list[str] = []
            for failure in failures:
                if failure.startswith("silhouette IOU too low:"):
                    continue
                if failure.startswith("bbox delta too large:") and max_bbox_delta <= int(WALL_RAW_OVERRIDE["max_bbox_delta_hard_fail"]):
                    continue
                retained_failures.append(failure)
            failures = retained_failures
            if not failures:
                severity = "pass"
            elif any(
                failure.startswith("generated image has no opaque tile silhouette")
                or failure.startswith("generated image appears to fill the whole canvas")
                for failure in failures
            ):
                severity = "hard_fail"
            else:
                severity = "soft_fail"
        if severity == "pass" and deltas is not None and max_bbox_delta > int(WALL_RAW_OVERRIDE["max_bbox_delta_soft_fail"]):
            wall_diagnostics["raw_bbox_drift_tolerated"] = {
                "bbox_deltas": deltas,
                "soft_fail_threshold": int(WALL_RAW_OVERRIDE["max_bbox_delta_soft_fail"]),
                "hard_fail_threshold": int(WALL_RAW_OVERRIDE["max_bbox_delta_hard_fail"]),
            }

    return {
        "status": severity,
        "failures": failures,
        "reference": reference_metrics.__dict__,
        "generated": generated_metrics.__dict__,
        "canvas_alignment": canvas_alignment,
        "iou": iou,
        "bbox_deltas": deltas,
        "selector_profile": selector_profile,
        "normalized_diagnostics": wall_diagnostics,
    }


def validate_reference_pair_run(
    run_root: Path,
    *,
    full_image: Path | None = None,
    half_image: Path | None = None,
    variant_images: dict[str, Path] | None = None,
    skip_preprocessing: bool = False,
    output_subdir: str = "validation",
    log_filename: str = "validate.json",
) -> dict[str, Any]:
    request_payload = load_json(run_root / "request" / "request.json")
    thresholds = request_payload["validation"]
    variants: list[str] = request_payload.get("variants", ["full", "half"])
    variant_profiles = request_payload.get("variant_profiles", {})
    background = request_payload.get("background", {"mode": "transparent"})
    override_images = dict(variant_images or {})
    if full_image is not None:
        override_images["full"] = full_image
    if half_image is not None:
        override_images["half"] = half_image
    references = {variant: Path(request_payload["references"][variant]) for variant in variants}
    generated_inputs: dict[str, Path] = {}
    generated_outputs: dict[str, Path] = {}
    for variant in variants:
        raw_default = run_root / "generated" / f"generated_{variant}.raw.png"
        generated_inputs[variant] = override_images.get(variant) or (
            raw_default if background.get("mode") == "color_key" and raw_default.exists() else run_root / "generated" / f"generated_{variant}.png"
        )
        generated_outputs[variant] = generated_inputs[variant]
        if background.get("mode") == "color_key" and raw_default.exists():
            _write_step1_raw_artifact(run_root, variant=variant, raw_image_path=raw_default)
    preprocessing: dict[str, Any] = {}
    if background.get("mode") == "color_key" and not skip_preprocessing:
        for variant in variants:
            preprocessing[variant] = run_cleanup_variant_pool(
                run_root,
                variant=variant,
                raw_image_path=generated_inputs[variant],
                background=background,
            )
            generated_outputs[variant] = default_cleanup_candidate_path(preprocessing[variant])
    for variant in variants:
        if not generated_outputs[variant].exists():
            raise ReferencePairWorkflowError(f"Missing generated {variant} image: {generated_outputs[variant]}")

    per_variant_results: dict[str, Any] = {}
    for variant in variants:
        selector_profile = (
            str(variant_profiles.get(variant, {}).get("selector_profile", "")).strip().lower()
            if isinstance(variant_profiles, dict)
            else ""
        )
        candidate_for_validation = generated_outputs[variant]
        preprocessing_gate = None
        if selector_profile == "wall" and variant in preprocessing:
            preprocessing_gate = _wall_preprocessing_gate(
                reference_path=references[variant],
                preprocessing_payload=preprocessing[variant],
            )
            _write_step4_gate_artifacts(run_root, variant=variant, preprocessing_gate=preprocessing_gate)
            if preprocessing_gate.get("chosen_candidate", {}).get("path"):
                candidate_for_validation = Path(str(preprocessing_gate["chosen_candidate"]["path"]))
                generated_outputs[variant] = candidate_for_validation
        variant_result = validate_single_pair(
            references[variant],
            candidate_for_validation,
            thresholds,
            selector_profile=selector_profile,
        )
        if preprocessing_gate is not None:
            variant_result["preprocessing_gate"] = preprocessing_gate
            if not preprocessing_gate["usable"]:
                variant_result["failures"] = [
                    "wall preprocessing produced no usable keyed silhouette variant; skip geometry mapping and retry generation"
                ]
                variant_result["status"] = "hard_fail"
        per_variant_results[variant] = variant_result
    ref_metrics = {variant: pair_metrics(references[variant]) for variant in variants}
    gen_metrics = {variant: pair_metrics(generated_outputs[variant]) for variant in variants}

    def bbox_height(metrics: PairMetrics) -> int | None:
        if metrics.bbox is None:
            return None
        return metrics.bbox[3] - metrics.bbox[1]

    ref_ratio = None
    gen_ratio = None
    pair_status = "skipped"
    pair_failures: list[str] = []
    if "full" in variants and "half" in variants:
        pair_status = "pass"
        if bbox_height(ref_metrics["full"]) and bbox_height(ref_metrics["half"]):
            ref_ratio = bbox_height(ref_metrics["half"]) / bbox_height(ref_metrics["full"])
        if bbox_height(gen_metrics["full"]) and bbox_height(gen_metrics["half"]):
            gen_ratio = bbox_height(gen_metrics["half"]) / bbox_height(gen_metrics["full"])

        if ref_ratio is not None and gen_ratio is not None:
            ratio_delta = abs(gen_ratio - ref_ratio)
            if ratio_delta > thresholds["pair_height_ratio_hard_fail"]:
                pair_status = "hard_fail"
                pair_failures.append(
                    f"full/half height ratio drift too large: reference={ref_ratio:.4f}, generated={gen_ratio:.4f}"
                )
            elif ratio_delta > thresholds["pair_height_ratio_soft_fail"]:
                pair_status = "soft_fail"
                pair_failures.append(
                    f"full/half height ratio drift: reference={ref_ratio:.4f}, generated={gen_ratio:.4f}"
                )
        else:
            pair_status = "hard_fail"
            pair_failures.append("could not compute full/half bbox heights")
    else:
        pair_failures.append("pair relationship validation skipped because this run does not use the special full/half floor pair")

    validation_dir = run_root / output_subdir
    artifacts: dict[str, str] = {"validation_json": str(validation_dir / "validation.json")}
    for variant in variants:
        create_overlay(references[variant], generated_outputs[variant], validation_dir / f"overlay_{variant}.png")
        create_diff_mask(references[variant], generated_outputs[variant], validation_dir / f"diff_{variant}.png")
        artifacts[f"overlay_{variant}"] = str(validation_dir / f"overlay_{variant}.png")
        artifacts[f"diff_{variant}"] = str(validation_dir / f"diff_{variant}.png")

    statuses = [result["status"] for result in per_variant_results.values()]
    if pair_status != "skipped":
        statuses.append(pair_status)
    if "hard_fail" in statuses:
        final_status = "hard_fail"
    elif "soft_fail" in statuses:
        final_status = "soft_fail"
    else:
        final_status = "pass"

    result = {
        "ok": final_status == "pass",
        "status": final_status,
        "validated_at": now_iso(),
        "run_root": str(run_root),
        "variants": variants,
        "background": background,
        "preprocessing": preprocessing,
        "pair_relationship": {
            "status": pair_status,
            "failures": pair_failures,
            "reference_height_ratio_half_to_full": ref_ratio,
            "generated_height_ratio_half_to_full": gen_ratio,
        },
        "artifacts": artifacts,
    }
    for variant, variant_result in per_variant_results.items():
        result[variant] = variant_result
    write_json(validation_dir / "validation.json", result)
    write_json(run_root / "logs" / log_filename, {"ok": True, "validated_at": now_iso(), "status": final_status})
    return result
