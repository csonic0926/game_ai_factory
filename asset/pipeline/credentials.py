#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_ENV_PATH = REPO_ROOT / ".env"
GEMINI_OUTPUT_ENV_NAMES = (
    "GEMINI_API_KEY",
    "GEMINI_KEY_COMPANY",
    "GEMINI_KEY_PERSONAL",
)


class CredentialError(RuntimeError):
    pass


def load_repo_env_file(path: Path = REPO_ENV_PATH) -> dict[str, str]:
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


def _normalize_credential_source_type(source_type: str | None) -> str:
    normalized = str(source_type or "auto").strip().lower()
    if normalized not in {"auto", "process_env", "env_file"}:
        raise CredentialError(
            f"Unsupported credential source type '{normalized}'. Expected one of: auto, process_env, env_file."
        )
    return normalized


def resolve_gemini_credential(
    base_env: dict[str, str] | None = None,
    *,
    source_type: str | None = None,
    env_file: str | Path | None = None,
    allow_repo_fallback: bool | None = None,
) -> dict[str, Any]:
    env = base_env if base_env is not None else os.environ
    normalized_source_type = _normalize_credential_source_type(source_type)
    checked_sources: list[dict[str, Any]] = []

    env_value = env.get("GEMINI_API_KEY", "").strip()
    if env_value:
        checked_sources.append({"type": "process_env", "status": "found"})
        return {
            "gemini_api_key": env_value,
            "source_used": {"type": "process_env"},
            "checked_sources": checked_sources,
        }
    checked_sources.append({"type": "process_env", "status": "missing"})

    normalized_env_file: Path | None = None
    if env_file is not None:
        normalized_env_file = Path(env_file).expanduser().resolve()

    should_check_env_file = normalized_source_type in {"auto", "env_file"} and normalized_env_file is not None
    if normalized_source_type == "env_file" and normalized_env_file is None:
        raise CredentialError("credential_source.type=env_file requires a non-empty env_file path.")

    if should_check_env_file and normalized_env_file is not None:
        if not normalized_env_file.exists():
            checked_sources.append(
                {"type": "env_file", "path": str(normalized_env_file), "status": "missing_path"}
            )
            if normalized_source_type == "env_file":
                raise CredentialError(
                    f"Missing GEMINI_API_KEY. Credential source requested env_file at {normalized_env_file}, "
                    "but that path does not exist."
                )
        else:
            env_file_data = load_repo_env_file(normalized_env_file)
            env_file_value = env_file_data.get("GEMINI_API_KEY", "").strip()
            if env_file_value:
                checked_sources.append({"type": "env_file", "path": str(normalized_env_file), "status": "found"})
                return {
                    "gemini_api_key": env_file_value,
                    "source_used": {"type": "env_file", "env_file": str(normalized_env_file)},
                    "checked_sources": checked_sources,
                }
            checked_sources.append({"type": "env_file", "path": str(normalized_env_file), "status": "missing"})

    use_repo_fallback = allow_repo_fallback if allow_repo_fallback is not None else normalized_source_type == "auto"
    if use_repo_fallback:
        repo_env = load_repo_env_file()
        repo_value = repo_env.get("GEMINI_API_KEY", "").strip()
        if repo_value:
            checked_sources.append({"type": "repo_env", "path": str(REPO_ENV_PATH), "status": "found"})
            return {
                "gemini_api_key": repo_value,
                "source_used": {"type": "repo_env", "env_file": str(REPO_ENV_PATH)},
                "checked_sources": checked_sources,
            }
        checked_sources.append({"type": "repo_env", "path": str(REPO_ENV_PATH), "status": "missing"})

    checked_descriptions = []
    for checked_source in checked_sources:
        label = checked_source["type"]
        if checked_source.get("path"):
            label = f"{label}({checked_source['path']})"
        checked_descriptions.append(f"{label}={checked_source['status']}")

    raise CredentialError(
        "Missing GEMINI_API_KEY after checking sources: "
        + ", ".join(checked_descriptions)
        + ". Provide GEMINI_API_KEY in the process environment"
        + (f" or in {normalized_env_file}" if normalized_env_file is not None else "")
        + (f" or in {REPO_ENV_PATH}" if use_repo_fallback else "")
        + "."
    )


def resolve_gemini_api_key(base_env: dict[str, str] | None = None) -> str:
    return resolve_gemini_credential(base_env)["gemini_api_key"]

def build_gemini_provider_env(
    base_env: dict[str, str] | None = None,
    *,
    source_type: str | None = None,
    env_file: str | Path | None = None,
    allow_repo_fallback: bool | None = None,
    return_resolution: bool = False,
) -> dict[str, str] | tuple[dict[str, str], dict[str, Any]]:
    resolution = resolve_gemini_credential(
        base_env,
        source_type=source_type,
        env_file=env_file,
        allow_repo_fallback=allow_repo_fallback,
    )
    gemini_api_key = resolution["gemini_api_key"]
    env = dict(base_env if base_env is not None else os.environ)
    for key_name in GEMINI_OUTPUT_ENV_NAMES:
        env.pop(key_name, None)
    env["GEMINI_API_KEY"] = gemini_api_key
    env["GEMINI_KEY_COMPANY"] = gemini_api_key
    env["GEMINI_KEY_PERSONAL"] = gemini_api_key
    if return_resolution:
        return env, {
            "source_used": resolution["source_used"],
            "checked_sources": resolution["checked_sources"],
        }
    return env
