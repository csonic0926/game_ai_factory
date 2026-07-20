#!/usr/bin/env python3
"""Project-agnostic gameplay runtime evidence reader.

The reader validates a canonical raw evidence envelope, maps project event
payloads through a game-owned Observation Adapter mapping, reconstructs player
time, builds a sequential blind projection, and prepares auditable evidence
references for a fresh acceptance reviewer. It never emits an acceptance
verdict or a claim about player psychology.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


RAW_MANIFEST_VERSION = "gameplay.raw_manifest.v1"
RAW_EVENT_VERSION = "gameplay.raw_event.v1"
MAPPING_VERSION = "gameplay.observation_mapping.v1"
STREAM_VERSION = "gameplay.canonical_event_stream.v1"
TIMELINE_VERSION = "gameplay.observed_timeline.v1"
BLIND_VERSION = "gameplay.runtime_blind_input.v1"
KERNEL_VERSION = "gameplay.acceptance_kernels.v1"
ACCEPTANCE_INPUT_VERSION = "gameplay.acceptance_comparison_input.v1"
INTEGRITY_VERSION = "gameplay.evidence_integrity.v1"
BUDGET_VERSION = "gameplay.experience_budget.v1"
BUDGET_RESULT_VERSION = "gameplay.experience_budget_result.v1"

EVIDENCE_MODES = {
    "LIVE_BLIND_RUN",
    "RECORDED_RUN",
    "CONTROLLED_BRANCH_PROBE",
    "STATIC_RUNTIME_ASSERTION",
}

CANONICAL_KINDS = {
    "player_input",
    "gameplay_action",
    "control",
    "cue",
    "presentation",
    "world_response",
    "state_change",
    "capture",
    "performance",
}

NEUTRAL_OBSERVATION_CHANNELS = {
    "visual",
    "audio",
    "ui",
    "input",
    "world_change",
}

# Exact normalized field names that turn an observation into design or
# psychological self-certification. Values are not semantically interpreted;
# adapters remain responsible for neutral runtime ids and copy.
FORBIDDEN_KEYS = {
    "acceptance_kernel",
    "acceptance_kernel_id",
    "beat_id",
    "canonical_action",
    "design_id",
    "design_intent",
    "emotion",
    "felt_fun",
    "feeling",
    "fun",
    "meaningful_alternative",
    "player_felt",
    "player_forecast",
    "player_understood",
    "sheet_id",
    "understood",
}

FUTURE_OR_INTERPRETIVE_BLIND_KEYS = FORBIDDEN_KEYS | {
    "available_actions",
    "branch_label",
    "correlation_role",
    "cue",
    "event_kind",
    "event_role",
    "event_type",
    "expected_action",
    "future",
    "future_state",
    "group_id",
    "importance",
    "intent",
    "kind",
    "latency",
    "next_action",
    "outcome_quality",
    "phase",
    "probe_group",
    "response",
    "run_id",
    "schema_version",
    "semantic_role",
    "session_id",
    "source_event_id",
    "world_response",
}

CAPTURE_PATH_KEYS = {
    "audio_path",
    "capture_path",
    "capture_paths",
    "capture_ref",
    "capture_refs",
    "screenshot_path",
    "screenshot_paths",
    "video_path",
    "video_paths",
}

# Envelope/provenance fields have reader meaning but are never player-facing
# observations. They must flow through the dedicated canonical fields instead
# of being remapped under a neutral-looking observable target.
PRIVATE_OBSERVABLE_SOURCE_PATHS = {
    "schema_version",
    "run_id",
    "session_id",
    "source_event_id",
    "event_type",
    "correlation_id",
    "correlation_role",
    "capture_refs",
}

SEMANTIC_OBSERVABLE_SOURCE_KEYS = FORBIDDEN_KEYS | {
    "acceptance_phase",
    "branch_label",
    "design_role",
    "event_kind",
    "event_role",
    "event_type",
    "group_id",
    "probe_group",
    "run_id",
    "schema_version",
    "semantic_kind",
    "semantic_role",
    "session_id",
    "source_event_id",
} | CAPTURE_PATH_KEYS

MAPPING_KEYS = {
    "schema_version",
    "adapter_id",
    "source_schema_version",
    "field_map",
    "event_type_map",
    "observable_fields",
    "hidden_fields",
    "public_context_fields",
}

FIELD_MAP_KEYS = {
    "event_id",
    "sequence",
    "monotonic_ms",
    "frame",
    "event_type",
    "context",
    "summary",
    "observation_channel",
    "correlation_id",
    "correlation_role",
    "capture_refs",
}

MANIFEST_KEYS = {
    "schema_version",
    "run_id",
    "session_id",
    "evidence_mode",
    "build",
    "setup",
    "display",
    "performance_context",
    "started_at",
    "raw_events_path",
    "capture_roots",
    "probe_group",
    "observation_window",
}

EVENT_KEYS = {
    "schema_version",
    "run_id",
    "session_id",
    "source_event_id",
    "sequence",
    "monotonic_ms",
    "frame",
    "event_type",
    "context",
    "payload",
    "correlation_id",
    "correlation_role",
    "capture_refs",
}


class ReaderError(Exception):
    """Expected fail-closed reader error."""


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_game_ownership(game_repo_value: str, paths: Iterable[Path]) -> Path:
    """Fail closed when game-owned evidence/output escapes its explicit repo."""

    game_repo = Path(game_repo_value).expanduser().resolve()
    factory_repo = Path(__file__).resolve().parent.parent
    if not game_repo.is_dir() or not (game_repo / ".git").exists():
        raise ReaderError(f"game repo must be an existing Git root: {game_repo}")
    if _inside(game_repo, factory_repo):
        raise ReaderError(f"game repo cannot be inside the factory repo: {game_repo}")
    for path in paths:
        resolved = path.expanduser().resolve()
        if not _inside(resolved, game_repo):
            raise ReaderError(f"game-owned reader path escapes game repo: {resolved}")
    return game_repo


def _norm_key(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _finding(code: str, path: str, message: str, severity: str = "ERROR") -> dict[str, str]:
    return {"severity": severity, "code": code, "path": path, "message": message}


def _integrity_report(
    run_id: str | None,
    findings: list[dict[str, str]],
    checked: dict[str, Any],
) -> dict[str, Any]:
    errors = [item for item in findings if item["severity"] == "ERROR"]
    return {
        "schema_version": INTEGRITY_VERSION,
        "run_id": run_id,
        "status": "INCONCLUSIVE_EVIDENCE" if errors else "PASS_INTEGRITY",
        "checked": checked,
        "findings": findings,
    }


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ReaderError(f"cannot read JSON {path}: {exc}") from exc


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ReaderError(f"invalid JSONL {path}:{line_number}: {exc}") from exc
                if not isinstance(value, dict):
                    raise ReaderError(f"invalid JSONL {path}:{line_number}: event must be an object")
                value = dict(value)
                value["__raw_line__"] = line_number
                records.append(value)
    except OSError as exc:
        raise ReaderError(f"cannot read JSONL {path}: {exc}") from exc
    return records


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _required_string(container: Any, key: str, path: str, findings: list[dict[str, str]]) -> None:
    if not isinstance(container, dict) or not isinstance(container.get(key), str) or not container[key].strip():
        findings.append(_finding("REQUIRED_STRING", f"{path}.{key}", "required non-empty string"))


def _unknown_fields(container: Any, allowed: set[str], path: str, findings: list[dict[str, str]]) -> None:
    if isinstance(container, dict):
        unknown = sorted(set(container) - allowed)
        if unknown:
            findings.append(_finding("UNKNOWN_FIELDS", path, f"unknown fields: {unknown}"))


def _walk_forbidden(value: Any, path: str, findings: list[dict[str, str]]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "__raw_line__":
                continue
            normalized = _norm_key(key)
            if normalized in FORBIDDEN_KEYS:
                findings.append(
                    _finding(
                        "FORBIDDEN_INTERPRETATION_FIELD",
                        f"{path}.{key}",
                        "raw/canonical evidence cannot assert design intent or player psychology",
                    )
                )
            _walk_forbidden(child, f"{path}.{key}", findings)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden(child, f"{path}[{index}]", findings)


def _safe_relative(value: str) -> bool:
    if not value.strip():
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_evidence(
    manifest_path: Path,
    events_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Validate canonical raw evidence and return manifest, events, report."""

    manifest = _load_json(manifest_path)
    events = _load_jsonl(events_path)
    findings: list[dict[str, str]] = []

    if not isinstance(manifest, dict):
        findings.append(_finding("MANIFEST_TYPE", "$", "manifest must be an object"))
        manifest = {}

    _unknown_fields(manifest, MANIFEST_KEYS, "$", findings)

    if manifest.get("schema_version") != RAW_MANIFEST_VERSION:
        findings.append(_finding("MANIFEST_VERSION", "$.schema_version", f"expected {RAW_MANIFEST_VERSION}"))
    for key in ("run_id", "session_id", "raw_events_path"):
        _required_string(manifest, key, "$", findings)
    if manifest.get("evidence_mode") not in EVIDENCE_MODES:
        findings.append(_finding("EVIDENCE_MODE", "$.evidence_mode", "unsupported evidence mode"))

    build = manifest.get("build")
    if not isinstance(build, dict):
        findings.append(_finding("BUILD", "$.build", "required object"))
    else:
        _unknown_fields(build, {"build_id", "content_revision"}, "$.build", findings)
        for key in ("build_id", "content_revision"):
            _required_string(build, key, "$.build", findings)

    setup = manifest.get("setup")
    if not isinstance(setup, dict):
        findings.append(_finding("SETUP", "$.setup", "required object"))
    else:
        _unknown_fields(setup, {"save_or_checkpoint", "seed", "locale", "input_mode", "platform"}, "$.setup", findings)
        for key in ("save_or_checkpoint", "locale", "input_mode", "platform"):
            _required_string(setup, key, "$.setup", findings)
        if (
            "seed" not in setup
            or not isinstance(setup.get("seed"), (str, int))
            or isinstance(setup.get("seed"), bool)
        ):
            findings.append(_finding("SEED", "$.setup.seed", "required string or integer"))

    display = manifest.get("display")
    if not isinstance(display, dict):
        findings.append(_finding("DISPLAY", "$.display", "required object"))
    else:
        _unknown_fields(display, {"viewport_width", "viewport_height", "window_mode"}, "$.display", findings)
        for key in ("viewport_width", "viewport_height"):
            if not _is_integer(display.get(key)) or display[key] < 1:
                findings.append(_finding("VIEWPORT", f"$.display.{key}", "required positive integer"))
        _required_string(display, "window_mode", "$.display", findings)

    performance_context = manifest.get("performance_context")
    if manifest.get("evidence_mode") == "CONTROLLED_BRANCH_PROBE" and not isinstance(performance_context, dict):
        findings.append(
            _finding(
                "PROBE_PERFORMANCE_CONTEXT_REQUIRED",
                "$.performance_context",
                "controlled branch probe requires explicit test-environment performance context",
            )
        )
    if performance_context is not None and not isinstance(performance_context, dict):
        findings.append(_finding("PERFORMANCE_CONTEXT", "$.performance_context", "must be an object"))
    if "started_at" in manifest and not isinstance(manifest.get("started_at"), str):
        findings.append(_finding("STARTED_AT", "$.started_at", "must be a string"))

    probe_group = manifest.get("probe_group")
    if manifest.get("evidence_mode") == "CONTROLLED_BRANCH_PROBE" and not isinstance(probe_group, dict):
        findings.append(_finding("PROBE_GROUP_REQUIRED", "$.probe_group", "controlled branch probe requires group provenance"))
    if probe_group is not None:
        if not isinstance(probe_group, dict):
            findings.append(_finding("PROBE_GROUP", "$.probe_group", "must be an object"))
        else:
            _unknown_fields(probe_group, {"group_id", "baseline_checkpoint", "branch_label"}, "$.probe_group", findings)
            required_probe_fields = (
                ("group_id", "baseline_checkpoint", "branch_label")
                if manifest.get("evidence_mode") == "CONTROLLED_BRANCH_PROBE"
                else ("group_id", "baseline_checkpoint")
            )
            for key in required_probe_fields:
                _required_string(probe_group, key, "$.probe_group", findings)
            if "branch_label" in probe_group and not isinstance(probe_group.get("branch_label"), str):
                findings.append(_finding("BRANCH_LABEL", "$.probe_group.branch_label", "must be a string"))
            if isinstance(setup, dict) and probe_group.get("baseline_checkpoint") != setup.get("save_or_checkpoint"):
                findings.append(
                    _finding(
                        "PROBE_CHECKPOINT_MISMATCH",
                        "$.probe_group.baseline_checkpoint",
                        "must equal setup.save_or_checkpoint",
                    )
                )

    observation_window = manifest.get("observation_window")
    if observation_window is not None:
        if not isinstance(observation_window, dict):
            findings.append(_finding("OBSERVATION_WINDOW", "$.observation_window", "must be an object"))
        else:
            _unknown_fields(
                observation_window,
                {"start_sequence", "end_sequence", "coverage_status", "coverage_basis"},
                "$.observation_window",
                findings,
            )
            for key in ("start_sequence", "end_sequence"):
                if not _is_integer(observation_window.get(key)) or observation_window[key] < 0:
                    findings.append(
                        _finding(
                            "OBSERVATION_WINDOW_SEQUENCE",
                            f"$.observation_window.{key}",
                            "must be a non-negative integer",
                        )
                    )
            if observation_window.get("coverage_status") != "COMPLETE":
                findings.append(
                    _finding(
                        "OBSERVATION_WINDOW_STATUS",
                        "$.observation_window.coverage_status",
                        "explicit observation coverage must be COMPLETE",
                    )
                )
            _required_string(observation_window, "coverage_basis", "$.observation_window", findings)
            start_sequence = observation_window.get("start_sequence")
            end_sequence = observation_window.get("end_sequence")
            if _is_integer(start_sequence) and _is_integer(end_sequence) and start_sequence > end_sequence:
                findings.append(
                    _finding(
                        "OBSERVATION_WINDOW_ORDER",
                        "$.observation_window",
                        "start_sequence must be <= end_sequence",
                    )
                )

    capture_roots = manifest.get("capture_roots")
    if (
        not isinstance(capture_roots, list)
        or any(not isinstance(item, str) or not _safe_relative(item) for item in capture_roots)
        or (isinstance(capture_roots, list) and len(capture_roots) != len(set(capture_roots)))
    ):
        findings.append(_finding("CAPTURE_ROOTS", "$.capture_roots", "must be a list of safe relative paths"))
    else:
        for root_ref in capture_roots:
            capture_root = (manifest_path.parent / root_ref).resolve()
            if not _inside(capture_root, manifest_path.parent.resolve()):
                findings.append(_finding("CAPTURE_ROOT_ESCAPE", "$.capture_roots", f"path escapes evidence root: {root_ref}"))
            elif not capture_root.is_dir():
                findings.append(_finding("CAPTURE_ROOT_MISSING", "$.capture_roots", f"missing directory: {root_ref}"))

    raw_path_value = manifest.get("raw_events_path")
    if isinstance(raw_path_value, str):
        if not _safe_relative(raw_path_value):
            findings.append(_finding("RAW_EVENTS_PATH", "$.raw_events_path", "must be a safe relative path"))
        else:
            declared = (manifest_path.parent / raw_path_value).resolve()
            if not _inside(declared, manifest_path.parent.resolve()):
                findings.append(_finding("RAW_EVENTS_ESCAPE", "$.raw_events_path", "resolved path escapes evidence root"))
            if declared != events_path.resolve():
                findings.append(
                    _finding(
                        "RAW_EVENTS_PROVENANCE",
                        "$.raw_events_path",
                        f"declared path {declared} does not match supplied events {events_path.resolve()}",
                    )
                )

    previous_sequence: int | None = None
    previous_time: float | None = None
    previous_frame: int | None = None
    seen_sequences: set[int] = set()
    seen_source_event_ids: set[str] = set()

    for index, event in enumerate(events):
        line = event.pop("__raw_line__", index + 1)
        base = f"events[{index}]@line{line}"
        _unknown_fields(event, EVENT_KEYS, base, findings)
        if event.get("schema_version") != RAW_EVENT_VERSION:
            findings.append(_finding("EVENT_VERSION", f"{base}.schema_version", f"expected {RAW_EVENT_VERSION}"))
        if event.get("run_id") != manifest.get("run_id"):
            findings.append(_finding("RUN_PROVENANCE", f"{base}.run_id", "does not match manifest"))
        if event.get("session_id") != manifest.get("session_id"):
            findings.append(_finding("SESSION_PROVENANCE", f"{base}.session_id", "does not match manifest"))

        sequence = event.get("sequence")
        if not _is_integer(sequence) or sequence < 0:
            findings.append(_finding("SEQUENCE", f"{base}.sequence", "must be a non-negative integer"))
        else:
            if sequence in seen_sequences:
                findings.append(_finding("SEQUENCE_DUPLICATE", f"{base}.sequence", "sequence is duplicated"))
            if previous_sequence is not None and sequence <= previous_sequence:
                findings.append(_finding("SEQUENCE_ORDER", f"{base}.sequence", "must be strictly increasing"))
            seen_sequences.add(sequence)
            previous_sequence = sequence

        monotonic = event.get("monotonic_ms")
        if not isinstance(monotonic, (int, float)) or isinstance(monotonic, bool) or monotonic < 0:
            findings.append(_finding("MONOTONIC_TIME", f"{base}.monotonic_ms", "must be a non-negative number"))
        else:
            if previous_time is not None and monotonic < previous_time:
                findings.append(_finding("CLOCK_ORDER", f"{base}.monotonic_ms", "must be non-decreasing"))
            previous_time = float(monotonic)

        frame = event.get("frame")
        if frame is not None:
            if not _is_integer(frame) or frame < 0:
                findings.append(_finding("FRAME", f"{base}.frame", "must be null or a non-negative integer"))
            else:
                if previous_frame is not None and frame < previous_frame:
                    findings.append(_finding("FRAME_ORDER", f"{base}.frame", "must be non-decreasing"))
                previous_frame = frame

        _required_string(event, "event_type", base, findings)
        if "source_event_id" in event:
            source_event_id = event.get("source_event_id")
            if not isinstance(source_event_id, str) or not source_event_id.strip():
                findings.append(_finding("SOURCE_EVENT_ID", f"{base}.source_event_id", "must be a non-empty string"))
            elif source_event_id in seen_source_event_ids:
                findings.append(_finding("SOURCE_EVENT_ID_DUPLICATE", f"{base}.source_event_id", "must be unique within the run"))
            else:
                seen_source_event_ids.add(source_event_id)
        if not isinstance(event.get("context"), dict):
            findings.append(_finding("CONTEXT", f"{base}.context", "required object"))
        else:
            for context_key in ("scene_id", "map_id", "encounter_id"):
                if event["context"].get(context_key) is not None and not isinstance(event["context"].get(context_key), str):
                    findings.append(
                        _finding(
                            "CONTEXT_FIELD",
                            f"{base}.context.{context_key}",
                            "must be null or a string",
                        )
                    )
        if not isinstance(event.get("payload"), dict):
            findings.append(_finding("PAYLOAD", f"{base}.payload", "required object"))

        correlation_role = event.get("correlation_role")
        if correlation_role not in (None, "cue", "action", "response"):
            findings.append(_finding("CORRELATION_ROLE", f"{base}.correlation_role", "invalid role"))
        if correlation_role is not None and not event.get("correlation_id"):
            findings.append(_finding("CORRELATION_ID", f"{base}.correlation_id", "role requires a correlation id"))
        if event.get("correlation_id") is not None and (
            not isinstance(event.get("correlation_id"), str) or not event["correlation_id"]
        ):
            findings.append(_finding("CORRELATION_ID", f"{base}.correlation_id", "must be null or a non-empty string"))
        if event.get("correlation_id") is not None and correlation_role is None:
            findings.append(_finding("CORRELATION_ROLE", f"{base}.correlation_role", "correlation id requires a role"))

        refs = event.get("capture_refs", [])
        if (
            not isinstance(refs, list)
            or any(not isinstance(ref, str) for ref in refs)
            or (isinstance(refs, list) and len(refs) != len(set(refs)))
        ):
            findings.append(_finding("CAPTURE_REFS", f"{base}.capture_refs", "must be a string list"))
        else:
            for ref in refs:
                if not _safe_relative(ref):
                    findings.append(_finding("CAPTURE_REF_PATH", f"{base}.capture_refs", f"unsafe path: {ref}"))
                else:
                    artifact = (manifest_path.parent / ref).resolve()
                    if not _inside(artifact, manifest_path.parent.resolve()):
                        findings.append(_finding("CAPTURE_REF_ESCAPE", f"{base}.capture_refs", f"artifact escapes evidence root: {ref}"))
                    elif not artifact.is_file():
                        findings.append(_finding("CAPTURE_REF_MISSING", f"{base}.capture_refs", f"missing artifact: {ref}"))

        _walk_forbidden(event, base, findings)

    if not events:
        findings.append(_finding("NO_EVENTS", "events", "raw event log is empty"))

    if isinstance(observation_window, dict):
        start_sequence = observation_window.get("start_sequence")
        end_sequence = observation_window.get("end_sequence")
        if _is_integer(start_sequence) and _is_integer(end_sequence) and start_sequence <= end_sequence:
            window_sequences = sorted(
                sequence
                for sequence in seen_sequences
                if start_sequence <= sequence <= end_sequence
            )
            expected_sequences = list(range(start_sequence, end_sequence + 1))
            if window_sequences != expected_sequences:
                findings.append(
                    _finding(
                        "OBSERVATION_WINDOW_INCOMPLETE",
                        "$.observation_window",
                        "declared complete window must contain every sequence from start_sequence through end_sequence",
                    )
                )

    report = _integrity_report(
        manifest.get("run_id"),
        findings,
        {
            "manifest": str(manifest_path),
            "events": str(events_path),
            "event_count": len(events),
            "capture_refs": sum(len(event.get("capture_refs", [])) for event in events),
        },
    )
    return manifest, events, report


def _ensure_pass(report: dict[str, Any]) -> None:
    if report.get("status") != "PASS_INTEGRITY":
        errors = [item for item in report.get("findings", []) if item.get("severity") == "ERROR"]
        first = errors[0] if errors else {"code": "UNKNOWN", "message": "integrity failed"}
        raise ReaderError(f"{report['status']}: {first['code']}: {first['message']}")


_NO_DEFAULT = object()
_MISSING = object()


def _get_path(value: Any, dotted: str, default: Any = _NO_DEFAULT) -> Any:
    current = value
    if not dotted:
        return current
    for part in dotted.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            if default is _NO_DEFAULT:
                raise ReaderError(f"mapping source field not found: {dotted}")
            return default
    return current


def _set_path(target: dict[str, Any], dotted: str, value: Any) -> None:
    current = target
    parts = dotted.split(".")
    for part in parts[:-1]:
        child = current.get(part)
        if child is None:
            child = {}
            current[part] = child
        if not isinstance(child, dict):
            raise ReaderError(f"mapping target collision at {dotted}")
        current = child
    current[parts[-1]] = value


def _path_components(path: str) -> tuple[str, ...]:
    components = tuple(path.split("."))
    if not components or any(not component for component in components):
        raise ReaderError(f"mapping path must contain non-empty dot-separated components: {path!r}")
    return components


def _paths_overlap(left: str, right: str) -> bool:
    left_parts = _path_components(left)
    right_parts = _path_components(right)
    shared = min(len(left_parts), len(right_parts))
    return left_parts[:shared] == right_parts[:shared]


def _mapping_unknown_fields(value: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ReaderError(f"{path} has unknown fields: {unknown}")


def _source_is_private_or_semantic(path: str) -> bool:
    if any(_paths_overlap(path, private_path) for private_path in PRIVATE_OBSERVABLE_SOURCE_PATHS):
        return True
    return any(_norm_key(component) in SEMANTIC_OBSERVABLE_SOURCE_KEYS for component in _path_components(path))


def _target_is_blind_excluded(path: str) -> bool:
    excluded = FUTURE_OR_INTERPRETIVE_BLIND_KEYS | CAPTURE_PATH_KEYS
    return any(_norm_key(component) in excluded for component in _path_components(path))


def _validate_mapping(mapping: Any, events: list[dict[str, Any]]) -> None:
    if not isinstance(mapping, dict):
        raise ReaderError("observation mapping must be an object")
    if mapping.get("schema_version") != MAPPING_VERSION:
        raise ReaderError(f"observation mapping must use {MAPPING_VERSION}")
    _mapping_unknown_fields(mapping, MAPPING_KEYS, "mapping")
    if mapping.get("source_schema_version") != RAW_EVENT_VERSION:
        raise ReaderError(f"mapping source_schema_version must be {RAW_EVENT_VERSION}")
    if not isinstance(mapping.get("adapter_id"), str) or not mapping["adapter_id"].strip():
        raise ReaderError("mapping adapter_id is required")
    field_map = mapping.get("field_map")
    if not isinstance(field_map, dict):
        raise ReaderError("mapping field_map is required")
    _mapping_unknown_fields(field_map, FIELD_MAP_KEYS, "mapping.field_map")
    for field in ("sequence", "monotonic_ms", "event_type"):
        if not isinstance(field_map.get(field), str) or not field_map[field]:
            raise ReaderError(f"mapping field_map.{field} is required")
    for field, source in field_map.items():
        if not isinstance(source, str) or not source.strip():
            raise ReaderError(f"mapping field_map.{field} must be a non-empty source path")
        _path_components(source)
    type_map = mapping.get("event_type_map")
    if not isinstance(type_map, dict):
        raise ReaderError("mapping event_type_map is required")
    if any(not isinstance(source_type, str) or not source_type for source_type in type_map):
        raise ReaderError("mapping event_type_map keys must be non-empty strings")
    invalid_kinds = sorted(
        {str(value) for value in type_map.values() if not isinstance(value, str) or value not in CANONICAL_KINDS}
    )
    if invalid_kinds:
        raise ReaderError(f"mapping contains invalid canonical kinds: {invalid_kinds}")
    source_types = {_get_path(event, field_map["event_type"], None) for event in events}
    missing_types = sorted(str(value) for value in source_types if value not in type_map)
    if missing_types:
        raise ReaderError(f"event_type_map does not map source types: {missing_types}")

    projections_by_section: dict[str, list[dict[str, str]]] = {}
    for section in ("observable_fields", "hidden_fields"):
        projections = mapping.get(section)
        if not isinstance(projections, list):
            raise ReaderError(f"mapping {section} must be a list")
        validated_projections: list[dict[str, str]] = []
        for index, projection in enumerate(projections):
            if (
                not isinstance(projection, dict)
                or not isinstance(projection.get("source"), str)
                or not projection["source"].strip()
                or not isinstance(projection.get("target"), str)
                or not projection["target"].strip()
            ):
                raise ReaderError(f"mapping {section}[{index}] requires source and target strings")
            _mapping_unknown_fields(projection, {"source", "target"}, f"mapping.{section}[{index}]")
            _path_components(projection["source"])
            _path_components(projection["target"])
            if section == "observable_fields" and _source_is_private_or_semantic(projection["source"]):
                raise ReaderError(
                    "mapping observable source is private, semantic, or a capture path: "
                    f"{projection['source']}"
                )
            if section == "observable_fields" and _target_is_blind_excluded(projection["target"]):
                raise ReaderError(f"mapping observable target is blind-excluded: {projection['target']}")
            if any(
                _norm_key(component) in FORBIDDEN_KEYS
                for component in _path_components(projection["target"])
            ):
                raise ReaderError(f"mapping target is a prohibited interpretation field: {projection['target']}")
            validated_projections.append(projection)
        projections_by_section[section] = validated_projections

    for section, projections in projections_by_section.items():
        for left_index, left in enumerate(projections):
            for right in projections[left_index + 1 :]:
                if _paths_overlap(left["target"], right["target"]):
                    raise ReaderError(
                        f"mapping {section} target paths overlap: {left['target']} vs {right['target']}"
                    )

    for observable in projections_by_section["observable_fields"]:
        for hidden in projections_by_section["hidden_fields"]:
            if _paths_overlap(observable["source"], hidden["source"]):
                raise ReaderError(
                    "observable and hidden source paths overlap: "
                    f"{observable['source']} vs {hidden['source']}"
                )
            if _paths_overlap(observable["target"], hidden["target"]):
                raise ReaderError(
                    "observable and hidden target paths overlap: "
                    f"{observable['target']} vs {hidden['target']}"
                )

    public_context_fields = mapping.get("public_context_fields", [])
    if not isinstance(public_context_fields, list):
        raise ReaderError("mapping public_context_fields must be a list")
    for index, source in enumerate(public_context_fields):
        if not isinstance(source, str) or not source.strip():
            raise ReaderError(f"mapping public_context_fields[{index}] must be a non-empty path")
        _path_components(source)
        if _target_is_blind_excluded(source):
            raise ReaderError(f"mapping public_context_fields[{index}] is blind-excluded: {source}")
    if len(public_context_fields) != len(set(public_context_fields)):
        raise ReaderError("mapping public_context_fields must be unique")


def normalize_events(
    manifest_path: Path,
    events_path: Path,
    mapping_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest, events, report = validate_evidence(manifest_path, events_path)
    _ensure_pass(report)
    mapping = _load_json(mapping_path)
    _validate_mapping(mapping, events)

    field_map: dict[str, str] = mapping["field_map"]
    type_map: dict[str, str] = mapping["event_type_map"]
    normalized: list[dict[str, Any]] = []

    for index, event in enumerate(events):
        sequence = _get_path(event, field_map["sequence"])
        monotonic_ms = _get_path(event, field_map["monotonic_ms"])
        source_type = _get_path(event, field_map["event_type"])
        event_id = _get_path(event, field_map.get("event_id", "source_event_id"), None)
        if event_id is None:
            event_id = f"{manifest['run_id']}:event:{sequence}"
        frame = _get_path(event, field_map.get("frame", "frame"), None)
        context = _get_path(event, field_map.get("context", "context"), {})
        if not isinstance(context, dict):
            raise ReaderError(f"mapped context must be an object at event {index}")
        summary = _get_path(event, field_map.get("summary", "payload.summary"), None)
        if summary is None:
            summary = f"{type_map[source_type]} event"
        if not isinstance(summary, str):
            raise ReaderError(f"mapped summary must be a string at event {index}")

        observable: dict[str, Any] = {}
        hidden: dict[str, Any] = {}
        for projection in mapping["observable_fields"]:
            value = _get_path(event, projection["source"], _MISSING)
            if value is not _MISSING:
                _set_path(observable, projection["target"], value)
        for projection in mapping["hidden_fields"]:
            value = _get_path(event, projection["source"], _MISSING)
            if value is not _MISSING:
                _set_path(hidden, projection["target"], value)

        public_context: dict[str, Any] = {}
        for source in mapping.get("public_context_fields", []):
            value = _get_path(context, source, _MISSING)
            if value is not _MISSING:
                _set_path(public_context, source, value)

        correlation_id = _get_path(event, field_map.get("correlation_id", "correlation_id"), None)
        correlation_role = _get_path(event, field_map.get("correlation_role", "correlation_role"), None)
        capture_refs = _get_path(event, field_map.get("capture_refs", "capture_refs"), [])
        if capture_refs is None:
            capture_refs = []
        observation_channel = None
        if "observation_channel" in field_map:
            observation_channel = _get_path(event, field_map["observation_channel"], None)
            if observation_channel is not None and observation_channel not in NEUTRAL_OBSERVATION_CHANNELS:
                raise ReaderError(
                    f"mapped observation channel at event {index} must be one of "
                    f"{sorted(NEUTRAL_OBSERVATION_CHANNELS)}"
                )

        canonical = {
            "schema_version": "gameplay.canonical_event.v1",
            "event_id": str(event_id),
            "sequence": sequence,
            "monotonic_ms": monotonic_ms,
            "frame": frame,
            "kind": type_map[source_type],
            "observation_channel": observation_channel,
            "summary": summary,
            "context": context,
            "public_context": public_context,
            "observable": observable,
            "hidden": hidden,
            "correlation_id": correlation_id,
            "correlation_role": correlation_role,
            "capture_refs": capture_refs,
            "raw_ref": {
                "path": manifest["raw_events_path"],
                "line": index + 1,
                "source_event_id": event.get("source_event_id"),
            },
        }
        canonical_findings: list[dict[str, str]] = []
        _walk_forbidden(canonical, f"canonical[{index}]", canonical_findings)
        if canonical_findings:
            first = canonical_findings[0]
            raise ReaderError(f"{first['code']}: {first['path']}")
        normalized.append(canonical)

    stream = {
        "schema_version": STREAM_VERSION,
        "run": {
            "run_id": manifest["run_id"],
            "session_id": manifest["session_id"],
            "evidence_mode": manifest["evidence_mode"],
            "build": manifest["build"],
            "setup": manifest["setup"],
            "display": manifest["display"],
            "performance_context": manifest.get("performance_context", {}),
            "started_at": manifest.get("started_at"),
            "probe_group": manifest.get("probe_group"),
            "observation_window": manifest.get("observation_window"),
        },
        "source": {
            "manifest": str(manifest_path),
            "events": str(events_path),
            "observation_adapter_mapping": str(mapping_path),
            "adapter_id": mapping["adapter_id"],
        },
        "events": normalized,
    }
    return stream, report


def _timeline_integrity(stream: Any) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    findings: list[dict[str, str]] = []
    latencies: list[dict[str, Any]] = []
    if not isinstance(stream, dict) or stream.get("schema_version") != STREAM_VERSION:
        findings.append(_finding("STREAM_VERSION", "$.schema_version", f"expected {STREAM_VERSION}"))
        return findings, latencies
    events = stream.get("events")
    if not isinstance(events, list) or not events:
        findings.append(_finding("STREAM_EVENTS", "$.events", "non-empty list required"))
        return findings, latencies

    run = stream.get("run")
    if not isinstance(run, dict):
        findings.append(_finding("STREAM_RUN", "$.run", "run metadata object required"))
    else:
        for key in ("run_id", "session_id"):
            if not isinstance(run.get(key), str) or not run[key]:
                findings.append(_finding("STREAM_RUN_IDENTITY", f"$.run.{key}", "non-empty string required"))
        if run.get("evidence_mode") not in EVIDENCE_MODES:
            findings.append(_finding("STREAM_EVIDENCE_MODE", "$.run.evidence_mode", "invalid evidence mode"))

    groups: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    previous_sequence: int | None = None
    previous_time: float | None = None
    seen_event_ids: set[str] = set()
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            findings.append(_finding("CANONICAL_EVENT", f"$.events[{index}]", "must be an object"))
            continue
        if event.get("kind") not in CANONICAL_KINDS:
            findings.append(_finding("CANONICAL_KIND", f"$.events[{index}].kind", "invalid kind"))
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            findings.append(_finding("CANONICAL_EVENT_ID", f"$.events[{index}].event_id", "non-empty string required"))
        elif event_id in seen_event_ids:
            findings.append(_finding("CANONICAL_EVENT_ID_DUPLICATE", f"$.events[{index}].event_id", "must be unique within the run"))
        else:
            seen_event_ids.add(event_id)
        sequence = event.get("sequence")
        timestamp = event.get("monotonic_ms")
        if not _is_integer(sequence) or (previous_sequence is not None and sequence <= previous_sequence):
            findings.append(_finding("CANONICAL_SEQUENCE", f"$.events[{index}].sequence", "must be strictly increasing integer"))
        else:
            previous_sequence = sequence
        if (
            not isinstance(timestamp, (int, float))
            or isinstance(timestamp, bool)
            or (previous_time is not None and timestamp < previous_time)
        ):
            findings.append(_finding("CANONICAL_CLOCK", f"$.events[{index}].monotonic_ms", "must be non-decreasing number"))
        else:
            previous_time = float(timestamp)
        correlation_id = event.get("correlation_id")
        role = event.get("correlation_role")
        if correlation_id is not None and (not isinstance(correlation_id, str) or not correlation_id):
            findings.append(_finding("CANONICAL_CORRELATION_ID", f"$.events[{index}].correlation_id", "must be null or a non-empty string"))
        if role is not None and role not in {"cue", "action", "response"}:
            findings.append(_finding("CANONICAL_CORRELATION_ROLE", f"$.events[{index}].correlation_role", "invalid role"))
        if (correlation_id is None) != (role is None):
            findings.append(
                _finding(
                    "CANONICAL_CORRELATION_PAIR",
                    f"$.events[{index}]",
                    "correlation_id and correlation_role must either both be present or both be null",
                )
            )
        if isinstance(correlation_id, str) and correlation_id and role in {"cue", "action", "response"}:
            groups[correlation_id][role].append(event)

    for correlation_id, roles in sorted(groups.items()):
        missing = [role for role in ("cue", "action", "response") if not roles.get(role)]
        if missing:
            findings.append(
                _finding(
                    "CORRELATION_INCOMPLETE",
                    f"correlation.{correlation_id}",
                    f"missing roles: {missing}",
                )
            )
            continue
        duplicates = [role for role in ("cue", "action", "response") if len(roles.get(role, [])) != 1]
        if duplicates:
            findings.append(
                _finding(
                    "CORRELATION_ROLE_DUPLICATE",
                    f"correlation.{correlation_id}",
                    f"expected exactly one event for roles: {duplicates}",
                )
            )
            continue
        cue = roles["cue"][0]
        action = roles["action"][0]
        response = roles["response"][0]
        cue_time = float(cue["monotonic_ms"])
        action_time = float(action["monotonic_ms"])
        response_time = float(response["monotonic_ms"])
        if not (
            cue["sequence"] < action["sequence"] < response["sequence"]
            and cue_time <= action_time <= response_time
        ):
            findings.append(
                _finding(
                    "CORRELATION_ORDER",
                    f"correlation.{correlation_id}",
                    "expected cue <= action <= response",
                )
            )
            continue
        latencies.append(
            {
                "correlation_id": correlation_id,
                "cue_event_id": cue["event_id"],
                "action_event_id": action["event_id"],
                "response_event_id": response["event_id"],
                "cue_to_action_ms": action_time - cue_time,
                "action_to_response_ms": response_time - action_time,
            }
        )
    return findings, latencies


def reconstruct_timeline(stream: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    findings, latencies = _timeline_integrity(stream)
    run = stream.get("run", {}) if isinstance(stream, dict) else {}
    report = _integrity_report(
        run.get("run_id"),
        findings,
        {"canonical_event_count": len(stream.get("events", [])) if isinstance(stream, dict) else 0},
    )
    _ensure_pass(report)

    events = stream["events"]
    start = float(events[0]["monotonic_ms"])
    timeline_events: list[dict[str, Any]] = []
    for event in events:
        timeline_events.append(
            {
                "event_id": event["event_id"],
                "sequence": event["sequence"],
                "elapsed_ms": float(event["monotonic_ms"]) - start,
                "frame": event.get("frame"),
                "kind": event["kind"],
                "observation_channel": event.get("observation_channel"),
                "summary": event["summary"],
                "public_context": event.get("public_context", {}),
                "observable": event.get("observable", {}),
                "mechanical_hidden": event.get("hidden", {}),
                "correlation_id": event.get("correlation_id"),
                "correlation_role": event.get("correlation_role"),
                "capture_refs": event.get("capture_refs", []),
                "raw_ref": event["raw_ref"],
            }
        )
    timeline = {
        "schema_version": TIMELINE_VERSION,
        "run": run,
        "source_stream": stream.get("source", {}),
        "events": timeline_events,
        "latencies": latencies,
    }
    return timeline, report


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def timeline_markdown(timeline: dict[str, Any]) -> str:
    run = timeline["run"]
    lines = [
        f"# Observed Gameplay Trace — `{run['run_id']}`",
        "",
        "Derived from actual runtime evidence. This file describes observations, not player psychology or an acceptance verdict.",
        "",
        "## Provenance",
        "",
        f"- Session: `{run['session_id']}`",
        f"- Evidence mode: `{run['evidence_mode']}`",
        f"- Build: `{run['build']['build_id']}`",
        f"- Content revision: `{run['build']['content_revision']}`",
        f"- Save/checkpoint: `{run['setup']['save_or_checkpoint']}`",
        f"- Seed: `{run['setup']['seed']}`",
        "",
        "## Player-time events",
        "",
        "| Seq | Time ms | Kind | Observable summary/data | Evidence refs |",
        "| ---: | ---: | --- | --- | --- |",
    ]
    for event in timeline["events"]:
        observable = _compact_json(event.get("observable", {})).replace("|", "\\|")
        summary = str(event.get("summary", "")).replace("|", "\\|")
        refs = [f"`{event['raw_ref']['path']}:{event['raw_ref']['line']}`"]
        refs.extend(f"[{Path(ref).name}]({ref})" for ref in event.get("capture_refs", []))
        lines.append(
            f"| {event['sequence']} | {event['elapsed_ms']:g} | `{event['kind']}` | {summary}; `{observable}` | {'; '.join(refs)} |"
        )
    lines.extend(["", "## Correlated latency", ""])
    if not timeline["latencies"]:
        lines.append("No complete cue/action/response correlation groups were present.")
    else:
        lines.extend(
            [
                "| Correlation | Cue -> action ms | Action -> response ms | Evidence |",
                "| --- | ---: | ---: | --- |",
            ]
        )
        for item in timeline["latencies"]:
            lines.append(
                f"| `{item['correlation_id']}` | {item['cue_to_action_ms']:g} | {item['action_to_response_ms']:g} | "
                f"`{item['cue_event_id']}` -> `{item['action_event_id']}` -> `{item['response_event_id']}` |"
            )
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "Mechanical hidden fields remain in the JSON for the acceptance reviewer and are excluded from runtime blind input. This trace does not claim what the player understood, felt, or enjoyed.",
            "",
        ]
    )
    return "\n".join(lines)


def _scrub_blind(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if _norm_key(key) in FUTURE_OR_INTERPRETIVE_BLIND_KEYS | CAPTURE_PATH_KEYS:
                continue
            result[key] = _scrub_blind(child)
        return result
    if isinstance(value, list):
        return [_scrub_blind(child) for child in value]
    return value


def _replace_known_capture_refs(value: Any, aliases_by_ref: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _replace_known_capture_refs(child, aliases_by_ref) for key, child in value.items()}
    if isinstance(value, list):
        return [_replace_known_capture_refs(child, aliases_by_ref) for child in value]
    if isinstance(value, str) and value in aliases_by_ref:
        return aliases_by_ref[value]
    return value


def build_blind_projection(timeline: dict[str, Any]) -> dict[str, Any]:
    if timeline.get("schema_version") != TIMELINE_VERSION:
        raise ReaderError(f"timeline must use {TIMELINE_VERSION}")
    _validate_acceptance_timeline(timeline)
    payloads = []
    capture_aliases: dict[str, str] = {}
    aliases_by_capture_ref: dict[str, str] = {}
    evidence_aliases: dict[str, dict[str, Any]] = {}

    def capture_alias(ref: str) -> str:
        if ref in aliases_by_capture_ref:
            return aliases_by_capture_ref[ref]
        alias = f"capture_{len(capture_aliases) + 1:06d}"
        capture_aliases[alias] = ref
        aliases_by_capture_ref[ref] = alias
        return alias

    for event in timeline.get("events", []):
        for ref in event.get("capture_refs", []):
            capture_alias(ref)

    for index, event in enumerate(timeline.get("events", []), 1):
        event_capture_aliases = [capture_alias(ref) for ref in event.get("capture_refs", [])]
        evidence_alias = f"evidence_{index:06d}"
        evidence_aliases[evidence_alias] = {
            "raw_ref": event.get("raw_ref"),
            "capture_refs": event_capture_aliases,
        }
        payload = {
            "reveal_index": index,
            "elapsed_ms": event["elapsed_ms"],
            "evidence_ref": evidence_alias,
            "public_context": _replace_known_capture_refs(
                _scrub_blind(event.get("public_context", {})), aliases_by_capture_ref
            ),
            "observable": _replace_known_capture_refs(
                _scrub_blind(event.get("observable", {})), aliases_by_capture_ref
            ),
            "capture_refs": event_capture_aliases,
        }
        observation_channel = event.get("observation_channel")
        if observation_channel is not None:
            if observation_channel not in NEUTRAL_OBSERVATION_CHANNELS:
                raise ReaderError(f"blind projection received invalid observation channel: {observation_channel}")
            payload["observation_channel"] = observation_channel
        blind_findings: list[dict[str, str]] = []
        _walk_forbidden(payload, f"payloads[{index - 1}]", blind_findings)
        if blind_findings:
            first = blind_findings[0]
            raise ReaderError(f"blind projection contaminated: {first['path']}")
        payloads.append(payload)
    run = timeline["run"]
    return {
        "schema_version": BLIND_VERSION,
        "private_facilitator_metadata": {
            "source_run_id": run["run_id"],
            "source_session_id": run["session_id"],
            "source_build_id": run["build"]["build_id"],
            "evidence_mode": run["evidence_mode"],
            "capture_aliases": capture_aliases,
            "evidence_aliases": evidence_aliases,
            "reveal_rule": "Reveal exactly one payload, record the response, then reveal the next.",
        },
        "payloads": payloads,
    }


def _is_subset(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(key in actual and _is_subset(value, actual[key]) for key, value in expected.items())
    if isinstance(expected, list):
        return expected == actual
    return expected == actual


def _event_matches(event: dict[str, Any], match: dict[str, Any]) -> bool:
    if "event_kind" in match and event.get("kind") != match["event_kind"]:
        return False
    if "event_id" in match and event.get("event_id") != match["event_id"]:
        return False
    if "correlation_id" in match and event.get("correlation_id") != match["correlation_id"]:
        return False
    if "observable" in match and not _is_subset(match["observable"], event.get("observable", {})):
        return False
    return True


POSITIVE_CHAIN_PHASES = ("cue", "action_or_attempt", "world_response", "carry_forward")
CORRELATED_CHAIN_PHASES = ("cue", "action_or_attempt", "world_response")
PHASE_ORDER = {phase: index for index, phase in enumerate(POSITIVE_CHAIN_PHASES)}

BUDGET_CONTENT_CATEGORIES = {
    "complete_gameplay_beat",
    "meaningful_decision",
    "combat_encounter",
    "world_interaction",
}

NON_GAMEPLAY_ACTIVITY_TYPES = {
    "teleporter_activation",
    "dialogue_advance",
    "raw_input",
    "straight_locomotion",
    "objective_arrival",
    "passive_state_change",
    "presentation",
    "control_transition",
    "control_return",
}


def _event_ref(run: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run["run_id"],
        "session_id": run["session_id"],
        "evidence_mode": run["evidence_mode"],
        "event_id": event["event_id"],
        "sequence": event["sequence"],
        "elapsed_ms": event["elapsed_ms"],
        "correlation_id": event.get("correlation_id"),
        "raw_ref": event["raw_ref"],
        "capture_refs": event.get("capture_refs", []),
    }


def _timeline_run_identity(timeline: dict[str, Any]) -> tuple[str, str]:
    run = timeline.get("run")
    if not isinstance(run, dict):
        raise ReaderError("timeline run metadata is required")
    run_id = run.get("run_id")
    session_id = run.get("session_id")
    if not isinstance(run_id, str) or not run_id or not isinstance(session_id, str) or not session_id:
        raise ReaderError("timeline requires non-empty run_id and session_id")
    if run.get("evidence_mode") not in EVIDENCE_MODES:
        raise ReaderError(f"timeline {run_id}/{session_id} has invalid evidence mode")
    return run_id, session_id


def _validate_acceptance_timeline(timeline: dict[str, Any]) -> None:
    """Validate the generated-timeline assumptions used by selector matching."""

    run_id, session_id = _timeline_run_identity(timeline)
    run = timeline["run"]
    build = run.get("build")
    if not isinstance(build, dict) or set(build) != {"build_id", "content_revision"} or any(
        not isinstance(build.get(key), str) or not build[key]
        for key in ("build_id", "content_revision")
    ):
        raise ReaderError(f"timeline {run_id}/{session_id} has invalid build provenance")
    setup = run.get("setup")
    if not isinstance(setup, dict) or set(setup) != {
        "save_or_checkpoint",
        "seed",
        "locale",
        "input_mode",
        "platform",
    }:
        raise ReaderError(f"timeline {run_id}/{session_id} has invalid setup provenance")
    if any(
        not isinstance(setup.get(key), str) or not setup[key]
        for key in ("save_or_checkpoint", "locale", "input_mode", "platform")
    ) or not isinstance(setup.get("seed"), (str, int)) or isinstance(setup.get("seed"), bool):
        raise ReaderError(f"timeline {run_id}/{session_id} has invalid setup provenance")
    display = run.get("display")
    if not isinstance(display, dict) or set(display) != {
        "viewport_width",
        "viewport_height",
        "window_mode",
    }:
        raise ReaderError(f"timeline {run_id}/{session_id} has invalid display provenance")
    if (
        not _is_integer(display.get("viewport_width"))
        or display["viewport_width"] < 1
        or not _is_integer(display.get("viewport_height"))
        or display["viewport_height"] < 1
        or not isinstance(display.get("window_mode"), str)
        or not display["window_mode"]
    ):
        raise ReaderError(f"timeline {run_id}/{session_id} has invalid display provenance")
    if not isinstance(run.get("performance_context"), dict):
        raise ReaderError(f"timeline {run_id}/{session_id} has invalid performance context")
    probe_group = run.get("probe_group")
    if run["evidence_mode"] == "CONTROLLED_BRANCH_PROBE":
        if not isinstance(probe_group, dict) or set(probe_group) != {
            "group_id",
            "baseline_checkpoint",
            "branch_label",
        }:
            raise ReaderError(f"timeline {run_id}/{session_id} has invalid controlled-probe provenance")
        if any(not isinstance(probe_group.get(key), str) or not probe_group[key] for key in probe_group):
            raise ReaderError(f"timeline {run_id}/{session_id} has invalid controlled-probe provenance")
        if probe_group["baseline_checkpoint"] != setup["save_or_checkpoint"]:
            raise ReaderError(f"timeline {run_id}/{session_id} controlled-probe checkpoint does not match setup")
    elif probe_group is not None:
        raise ReaderError(f"timeline {run_id}/{session_id} has probe_group outside controlled-probe mode")

    events = timeline.get("events")
    if not isinstance(events, list) or not events:
        raise ReaderError(f"timeline {run_id}/{session_id} requires a non-empty event list")
    if not _timeline_order_is_complete(events):
        raise ReaderError(f"timeline {run_id}/{session_id} is not strictly ordered")

    seen_event_ids: set[str] = set()
    correlation_groups: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ReaderError(f"timeline {run_id}/{session_id} event {index} must be an object")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise ReaderError(f"timeline {run_id}/{session_id} event {index} requires event_id")
        if event_id in seen_event_ids:
            raise ReaderError(f"timeline {run_id}/{session_id} has duplicate event_id {event_id}")
        seen_event_ids.add(event_id)
        if event.get("kind") not in CANONICAL_KINDS:
            raise ReaderError(f"timeline {run_id}/{session_id} event {event_id} has invalid kind")
        if not isinstance(event.get("summary"), str):
            raise ReaderError(f"timeline {run_id}/{session_id} event {event_id} requires string summary")
        frame = event.get("frame")
        if frame is not None and (not _is_integer(frame) or frame < 0):
            raise ReaderError(f"timeline {run_id}/{session_id} event {event_id} has invalid frame")
        channel = event.get("observation_channel")
        if channel is not None and channel not in NEUTRAL_OBSERVATION_CHANNELS:
            raise ReaderError(f"timeline {run_id}/{session_id} event {event_id} has invalid observation channel")
        for key in ("public_context", "observable", "mechanical_hidden", "raw_ref"):
            if not isinstance(event.get(key), dict):
                raise ReaderError(f"timeline {run_id}/{session_id} event {event_id} requires object {key}")
        capture_refs = event.get("capture_refs")
        if (
            not isinstance(capture_refs, list)
            or any(not isinstance(ref, str) or not _safe_relative(ref) for ref in capture_refs)
            or len(capture_refs) != len(set(capture_refs))
        ):
            raise ReaderError(f"timeline {run_id}/{session_id} event {event_id} has invalid capture refs")
        raw_ref = event["raw_ref"]
        if set(raw_ref) != {"path", "line", "source_event_id"}:
            raise ReaderError(f"timeline {run_id}/{session_id} event {event_id} has invalid raw ref")
        if (
            not isinstance(raw_ref.get("path"), str)
            or not _safe_relative(raw_ref["path"])
            or not _is_integer(raw_ref.get("line"))
            or raw_ref["line"] < 1
            or (
                raw_ref.get("source_event_id") is not None
                and (not isinstance(raw_ref["source_event_id"], str) or not raw_ref["source_event_id"])
            )
        ):
            raise ReaderError(f"timeline {run_id}/{session_id} event {event_id} has invalid raw ref")
        semantic_findings: list[dict[str, str]] = []
        _walk_forbidden(event, f"timeline.events[{index}]", semantic_findings)
        if semantic_findings:
            raise ReaderError(
                f"timeline {run_id}/{session_id} event {event_id} contains forbidden interpretation fields"
            )
        correlation_id = event.get("correlation_id")
        role = event.get("correlation_role")
        if correlation_id is not None and (not isinstance(correlation_id, str) or not correlation_id):
            raise ReaderError(f"timeline {run_id}/{session_id} event {event_id} has invalid correlation id")
        if role is not None and role not in {"cue", "action", "response"}:
            raise ReaderError(f"timeline {run_id}/{session_id} event {event_id} has invalid correlation role")
        if (correlation_id is None) != (role is None):
            raise ReaderError(
                f"timeline {run_id}/{session_id} event {event_id} must pair correlation id and role"
            )
        if isinstance(correlation_id, str) and role in {"cue", "action", "response"}:
            correlation_groups[correlation_id][role].append(event)

    for correlation_id, roles in correlation_groups.items():
        if any(len(roles.get(role, [])) != 1 for role in ("cue", "action", "response")):
            raise ReaderError(
                f"timeline {run_id}/{session_id} correlation {correlation_id} requires exactly one cue/action/response"
            )
        if not _chain_ordered([roles["cue"][0], roles["action"][0], roles["response"][0]]):
            raise ReaderError(
                f"timeline {run_id}/{session_id} correlation {correlation_id} is not cue/action/response ordered"
            )

    observation_window = timeline["run"].get("observation_window")
    if observation_window is not None:
        if not isinstance(observation_window, dict):
            raise ReaderError(f"timeline {run_id}/{session_id} observation_window must be an object")
        if set(observation_window) != {
            "start_sequence",
            "end_sequence",
            "coverage_status",
            "coverage_basis",
        }:
            raise ReaderError(f"timeline {run_id}/{session_id} observation_window has invalid fields")
        start_sequence = observation_window.get("start_sequence")
        end_sequence = observation_window.get("end_sequence")
        if (
            not _is_integer(start_sequence)
            or not _is_integer(end_sequence)
            or start_sequence < 0
            or start_sequence > end_sequence
            or observation_window.get("coverage_status") != "COMPLETE"
            or not isinstance(observation_window.get("coverage_basis"), str)
            or not observation_window["coverage_basis"].strip()
        ):
            raise ReaderError(f"timeline {run_id}/{session_id} observation_window is invalid")
        observed_sequences = [
            event["sequence"]
            for event in events
            if start_sequence <= event["sequence"] <= end_sequence
        ]
        if observed_sequences != list(range(start_sequence, end_sequence + 1)):
            raise ReaderError(f"timeline {run_id}/{session_id} observation_window is not complete")


def _observation_window_covers(
    run: dict[str, Any],
    start_event: dict[str, Any],
    end_event: dict[str, Any],
) -> bool:
    window = run.get("observation_window")
    return (
        isinstance(window, dict)
        and window.get("coverage_status") == "COMPLETE"
        and _is_integer(window.get("start_sequence"))
        and _is_integer(window.get("end_sequence"))
        and window["start_sequence"] <= start_event["sequence"]
        and end_event["sequence"] <= window["end_sequence"]
    )


def _validate_match_grammar(match: Any, context: str) -> None:
    """Validate the canonical public-event selector grammar."""

    if not isinstance(match, dict) or not match:
        raise ReaderError(f"{context} requires a non-empty match object")
    unknown_match_fields = sorted(set(match) - {"event_kind", "event_id", "correlation_id", "observable"})
    if unknown_match_fields:
        raise ReaderError(f"{context} has unknown match fields: {unknown_match_fields}")
    if "event_kind" in match and match["event_kind"] not in CANONICAL_KINDS:
        raise ReaderError(f"{context} has invalid event_kind")
    for key in ("event_id", "correlation_id"):
        if key in match and (not isinstance(match[key], str) or not match[key]):
            raise ReaderError(f"{context} has invalid {key}")
    if "observable" in match and (not isinstance(match["observable"], dict) or not match["observable"]):
        raise ReaderError(f"{context} observable match must be a non-empty object")


def _validate_kernel_selectors(kernel: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    selectors = kernel.get("selectors")
    if not isinstance(selectors, list) or not selectors:
        raise ReaderError(f"kernel {kernel['kernel_id']} requires selectors")

    positive: dict[str, dict[str, Any]] = {}
    negative: list[dict[str, Any]] = []
    for index, selector in enumerate(selectors):
        if not isinstance(selector, dict):
            raise ReaderError(f"kernel {kernel['kernel_id']} selector {index} is invalid")
        unknown_selector_fields = sorted(set(selector) - {"phase", "match", "window"})
        if unknown_selector_fields:
            raise ReaderError(
                f"kernel {kernel['kernel_id']} selector {index} has unknown fields: {unknown_selector_fields}"
            )
        phase = selector.get("phase")
        match = selector.get("match")
        if phase not in {*POSITIVE_CHAIN_PHASES, "negative_check"} or not isinstance(match, dict) or not match:
            raise ReaderError(f"kernel {kernel['kernel_id']} selector {index} is invalid")
        _validate_match_grammar(match, f"kernel {kernel['kernel_id']} selector {index}")
        if phase == "negative_check":
            window = selector.get("window")
            if not isinstance(window, dict):
                raise ReaderError(f"kernel {kernel['kernel_id']} negative selector {index} requires a phase window")
            if set(window) != {"start_phase", "end_phase"}:
                raise ReaderError(f"kernel {kernel['kernel_id']} negative selector {index} has invalid window fields")
            start_phase = window.get("start_phase")
            end_phase = window.get("end_phase")
            if start_phase not in PHASE_ORDER or end_phase not in PHASE_ORDER:
                raise ReaderError(f"kernel {kernel['kernel_id']} negative selector {index} has invalid window phases")
            if PHASE_ORDER[start_phase] > PHASE_ORDER[end_phase]:
                raise ReaderError(f"kernel {kernel['kernel_id']} negative selector {index} has reversed window phases")
            negative.append(selector)
        else:
            if "window" in selector:
                raise ReaderError(f"kernel {kernel['kernel_id']} positive selector {index} cannot define a window")
            if phase in positive:
                raise ReaderError(f"kernel {kernel['kernel_id']} must define exactly one {phase} selector")
            positive[phase] = selector

    missing = [phase for phase in POSITIVE_CHAIN_PHASES if phase not in positive]
    if missing:
        raise ReaderError(f"kernel {kernel['kernel_id']} is missing positive chain phases: {missing}")
    return positive, negative


def _validate_ordered_sequences(kernel: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate optional ordered events required between positive phases."""

    ordered_sequences = kernel.get("ordered_sequences", [])
    if not isinstance(ordered_sequences, list):
        raise ReaderError(f"kernel {kernel['kernel_id']} ordered_sequences must be an array")

    seen_sequence_ids: set[str] = set()
    for sequence_index, ordered_sequence in enumerate(ordered_sequences):
        context = f"kernel {kernel['kernel_id']} ordered sequence {sequence_index}"
        if not isinstance(ordered_sequence, dict):
            raise ReaderError(f"{context} must be an object")
        unknown_fields = sorted(
            set(ordered_sequence) - {"sequence_id", "after_phase", "before_phase", "matches"}
        )
        if unknown_fields:
            raise ReaderError(f"{context} has unknown fields: {unknown_fields}")
        sequence_id = ordered_sequence.get("sequence_id")
        if not isinstance(sequence_id, str) or not sequence_id:
            raise ReaderError(f"{context} requires a non-empty sequence_id")
        if sequence_id in seen_sequence_ids:
            raise ReaderError(f"kernel {kernel['kernel_id']} has duplicate ordered sequence id: {sequence_id}")
        seen_sequence_ids.add(sequence_id)

        after_phase = ordered_sequence.get("after_phase")
        before_phase = ordered_sequence.get("before_phase")
        if after_phase not in PHASE_ORDER or before_phase not in PHASE_ORDER:
            raise ReaderError(f"{context} has invalid phase boundaries")
        if PHASE_ORDER[after_phase] >= PHASE_ORDER[before_phase]:
            raise ReaderError(f"{context} phase boundaries must be strictly increasing")

        matches = ordered_sequence.get("matches")
        if not isinstance(matches, list) or not matches:
            raise ReaderError(f"{context} requires at least one match step")
        for match_index, match_step in enumerate(matches):
            match_context = f"{context} match step {match_index}"
            if not isinstance(match_step, dict) or set(match_step) != {"match"}:
                raise ReaderError(f"{match_context} must contain only match")
            _validate_match_grammar(match_step["match"], match_context)
    return ordered_sequences


def _timeline_order_is_complete(events: list[dict[str, Any]]) -> bool:
    previous_sequence: int | None = None
    previous_time: float | None = None
    for event in events:
        sequence = event.get("sequence")
        elapsed = event.get("elapsed_ms")
        if not isinstance(sequence, int) or not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool):
            return False
        if previous_sequence is not None and sequence <= previous_sequence:
            return False
        if previous_time is not None and float(elapsed) < previous_time:
            return False
        previous_sequence = sequence
        previous_time = float(elapsed)
    return bool(events)


def _chain_ordered(events: list[dict[str, Any]]) -> bool:
    sequences = [event["sequence"] for event in events]
    times = [float(event["elapsed_ms"]) for event in events]
    return all(left < right for left, right in zip(sequences, sequences[1:])) and all(
        left <= right for left, right in zip(times, times[1:])
    )


def _find_positive_chains(
    events: list[dict[str, Any]],
    selectors: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    phase_matches = {
        phase: [event for event in events if _event_matches(event, selector["match"])]
        for phase, selector in selectors.items()
    }
    required_roles = {
        "cue": "cue",
        "action_or_attempt": "action",
        "world_response": "response",
    }
    for phase, role in required_roles.items():
        phase_matches[phase] = [
            event for event in phase_matches[phase] if event.get("correlation_role") == role
        ]
    correlation_sets = []
    for phase in CORRELATED_CHAIN_PHASES:
        correlation_sets.append(
            {
                str(event["correlation_id"])
                for event in phase_matches[phase]
                if isinstance(event.get("correlation_id"), str) and event["correlation_id"]
            }
        )
    shared_correlations = set.intersection(*correlation_sets) if correlation_sets else set()

    chains: list[dict[str, Any]] = []
    carry_matches = phase_matches["carry_forward"]
    for correlation_id in sorted(shared_correlations):
        cues = [event for event in phase_matches["cue"] if str(event.get("correlation_id")) == correlation_id]
        actions = [event for event in phase_matches["action_or_attempt"] if str(event.get("correlation_id")) == correlation_id]
        responses = [event for event in phase_matches["world_response"] if str(event.get("correlation_id")) == correlation_id]
        for cue in cues:
            for action in actions:
                for response in responses:
                    if not _chain_ordered([cue, action, response]):
                        continue
                    for carry_forward in carry_matches:
                        if not _chain_ordered([response, carry_forward]):
                            continue
                        chains.append(
                            {
                                "correlation_id": correlation_id,
                                "events": {
                                    "cue": cue,
                                    "action_or_attempt": action,
                                    "world_response": response,
                                    "carry_forward": carry_forward,
                                },
                            }
                        )
    return phase_matches, chains


def _ordered_assignments(
    candidates_by_step: list[list[dict[str, Any]]],
) -> list[list[dict[str, Any]]]:
    """Return every strictly ordered, distinct assignment for one sequence."""

    assignments: list[list[dict[str, Any]]] = []

    def visit(step_index: int, previous_sequence: int | None, selected: list[dict[str, Any]]) -> None:
        if step_index == len(candidates_by_step):
            assignments.append(list(selected))
            return
        for event in candidates_by_step[step_index]:
            if previous_sequence is not None and event["sequence"] <= previous_sequence:
                continue
            selected.append(event)
            visit(step_index + 1, event["sequence"], selected)
            selected.pop()

    visit(0, None, [])
    return assignments


def _sequence_failure_reason(
    all_candidates_by_step: list[list[dict[str, Any]]],
    bounded_candidates_by_step: list[list[dict[str, Any]]],
) -> tuple[str, int]:
    """Classify why one ordered sequence has no valid in-boundary assignment."""

    for step_index, candidates in enumerate(all_candidates_by_step):
        if not candidates:
            return "MISSING_MATCH", step_index
    for step_index, candidates in enumerate(bounded_candidates_by_step):
        if not candidates:
            return "OUTSIDE_BOUNDARY_ONLY", step_index

    previous_sequence: int | None = None
    for step_index, candidates in enumerate(bounded_candidates_by_step):
        available = [
            event
            for event in candidates
            if previous_sequence is None or event["sequence"] > previous_sequence
        ]
        if available:
            previous_sequence = available[0]["sequence"]
            continue
        reusable = [
            event
            for event in candidates
            if previous_sequence is not None and event["sequence"] == previous_sequence
        ]
        if reusable:
            return "EVENT_REUSE_REQUIRED", step_index
        return "ORDER_VIOLATION", step_index
    return "ORDER_VIOLATION", len(bounded_candidates_by_step) - 1


def _ordered_sequence_options(
    events: list[dict[str, Any]],
    chain: dict[str, Any],
    ordered_sequence: dict[str, Any],
) -> tuple[list[list[dict[str, Any]]], dict[str, Any]]:
    """Build valid assignments and diagnostics for one chain-bound sequence."""

    after_event = chain["events"][ordered_sequence["after_phase"]]
    before_event = chain["events"][ordered_sequence["before_phase"]]
    all_candidates_by_step = [
        [event for event in events if _event_matches(event, match_step["match"])]
        for match_step in ordered_sequence["matches"]
    ]
    bounded_candidates_by_step = [
        [
            event
            for event in candidates
            if after_event["sequence"] < event["sequence"] < before_event["sequence"]
        ]
        for candidates in all_candidates_by_step
    ]
    assignments = _ordered_assignments(bounded_candidates_by_step)
    diagnostic = {
        "sequence_id": ordered_sequence["sequence_id"],
        "after_phase": ordered_sequence["after_phase"],
        "before_phase": ordered_sequence["before_phase"],
        "matches": [match_step["match"] for match_step in ordered_sequence["matches"]],
        "bounded_candidates_by_step": bounded_candidates_by_step,
        "all_candidates_by_step": all_candidates_by_step,
    }
    if assignments:
        diagnostic.update(
            {
                "status": "COMPLETE",
                "reason": "SATISFIED",
                "evidence_events": assignments[0],
                "failed_step_index": None,
            }
        )
    else:
        reason, failed_step_index = _sequence_failure_reason(
            all_candidates_by_step,
            bounded_candidates_by_step,
        )
        diagnostic.update(
            {
                "status": "INCOMPLETE",
                "reason": reason,
                "evidence_events": [],
                "failed_step_index": failed_step_index,
            }
        )
    return assignments, diagnostic


def _select_disjoint_sequence_assignments(
    assignment_options: list[list[list[dict[str, Any]]]],
) -> list[list[dict[str, Any]]] | None:
    """Choose one assignment per sequence without reusing an event."""

    selected_assignments: list[list[dict[str, Any]]] = []

    def visit(sequence_index: int, used_event_ids: set[str]) -> bool:
        if sequence_index == len(assignment_options):
            return True
        for assignment in assignment_options[sequence_index]:
            assignment_ids = {event["event_id"] for event in assignment}
            if assignment_ids & used_event_ids:
                continue
            selected_assignments.append(assignment)
            if visit(sequence_index + 1, used_event_ids | assignment_ids):
                return True
            selected_assignments.pop()
        return False

    return selected_assignments if visit(0, set()) else None


def _qualify_chain_with_ordered_sequences(
    events: list[dict[str, Any]],
    chain: dict[str, Any],
    ordered_sequences: list[dict[str, Any]],
) -> dict[str, Any]:
    """Require all ordered sequences to resolve jointly inside one phase chain."""

    qualified_chain = dict(chain)
    if not ordered_sequences:
        qualified_chain.update(
            {
                "qualification_status": "COMPLETE",
                "incomplete_reason": None,
                "ordered_sequence_results": [],
            }
        )
        return qualified_chain

    assignment_options: list[list[list[dict[str, Any]]]] = []
    diagnostics: list[dict[str, Any]] = []
    for ordered_sequence in ordered_sequences:
        options, diagnostic = _ordered_sequence_options(events, chain, ordered_sequence)
        assignment_options.append(options)
        diagnostics.append(diagnostic)

    if any(not options for options in assignment_options):
        qualified_chain.update(
            {
                "qualification_status": "INCOMPLETE",
                "incomplete_reason": "REQUIRED_ORDERED_SEQUENCE_INCOMPLETE",
                "ordered_sequence_results": diagnostics,
            }
        )
        return qualified_chain

    selected_assignments = _select_disjoint_sequence_assignments(assignment_options)
    if selected_assignments is None:
        for diagnostic in diagnostics:
            diagnostic.update(
                {
                    "status": "INCOMPLETE",
                    "reason": "EVENT_REUSE_CONFLICT_ACROSS_SEQUENCES",
                    "evidence_events": [],
                    "failed_step_index": None,
                }
            )
        qualified_chain.update(
            {
                "qualification_status": "INCOMPLETE",
                "incomplete_reason": "ORDERED_SEQUENCE_EVENT_REUSE_CONFLICT",
                "ordered_sequence_results": diagnostics,
            }
        )
        return qualified_chain

    for diagnostic, selected_assignment in zip(diagnostics, selected_assignments):
        diagnostic["evidence_events"] = selected_assignment
    qualified_chain.update(
        {
            "qualification_status": "COMPLETE",
            "incomplete_reason": None,
            "ordered_sequence_results": diagnostics,
        }
    )
    return qualified_chain


def _branch_signature(chain: dict[str, Any]) -> dict[str, Any]:
    """Return run-neutral observed evidence that distinguishes a branch."""

    signature = {
        phase: {
            "public_context": chain["events"][phase].get("public_context", {}),
            "observable": chain["events"][phase].get("observable", {}),
        }
        for phase in ("action_or_attempt", "world_response", "carry_forward")
    }
    if chain.get("ordered_sequence_results"):
        signature["ordered_sequences"] = {
            result["sequence_id"]: [
                {
                    "public_context": event.get("public_context", {}),
                    "observable": event.get("observable", {}),
                }
                for event in result["evidence_events"]
            ]
            for result in chain["ordered_sequence_results"]
        }
    return signature


def _branch_consequence_signature(chain: dict[str, Any]) -> dict[str, Any]:
    """Return only observable response/carry evidence for decision proof.

    Different inputs or branch labels do not establish a meaningful decision.
    Controlled alternatives must produce distinct observable consequences.
    """

    return {
        phase: {
            "public_context": chain["events"][phase].get("public_context", {}),
            "observable": chain["events"][phase].get("observable", {}),
        }
        for phase in ("world_response", "carry_forward")
    }


def _serialize_ordered_sequence_result(run: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    serialized = {
        "sequence_id": result["sequence_id"],
        "status": result["status"],
        "reason": result["reason"],
        "after_phase": result["after_phase"],
        "before_phase": result["before_phase"],
        "failed_step_index": result["failed_step_index"],
        "steps": [],
    }
    evidence_events = result.get("evidence_events", [])
    for step_index, match in enumerate(result["matches"]):
        step = {
            "step_index": step_index,
            "match": match,
            "evidence_ref": (
                _event_ref(run, evidence_events[step_index])
                if step_index < len(evidence_events)
                else None
            ),
            "bounded_candidate_refs": [
                _event_ref(run, event)
                for event in result["bounded_candidates_by_step"][step_index]
            ],
        }
        if not step["bounded_candidate_refs"]:
            step["outside_boundary_candidate_refs"] = [
                _event_ref(run, event)
                for event in result["all_candidates_by_step"][step_index]
            ]
        serialized["steps"].append(step)
    return serialized


def _serialize_chain(run: dict[str, Any], chain: dict[str, Any]) -> dict[str, Any]:
    return {
        "correlation_id": chain["correlation_id"],
        "run_id": run["run_id"],
        "session_id": run["session_id"],
        "status": chain.get("qualification_status", "COMPLETE"),
        "incomplete_reason": chain.get("incomplete_reason"),
        "phases": {
            phase: _event_ref(run, chain["events"][phase])
            for phase in POSITIVE_CHAIN_PHASES
        },
        "ordered_sequences": [
            _serialize_ordered_sequence_result(run, result)
            for result in chain.get("ordered_sequence_results", [])
        ],
    }


def _evaluate_negative_checks(
    run: dict[str, Any],
    events: list[dict[str, Any]],
    chains: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for selector_index, selector in enumerate(selectors):
        window_spec = selector["window"]
        if not chains:
            results.append(
                {
                    "selector_index": selector_index,
                    "match": selector["match"],
                    "status": "INCONCLUSIVE_COVERAGE",
                    "windows": [],
                    "requested_window": {
                        "start_phase": window_spec["start_phase"],
                        "end_phase": window_spec["end_phase"],
                    },
                    "forbidden_evidence_refs": [],
                }
            )
            continue

        windows = []
        all_forbidden: list[dict[str, Any]] = []
        complete_window_coverage = True
        for chain in chains:
            start_event = chain["events"][window_spec["start_phase"]]
            end_event = chain["events"][window_spec["end_phase"]]
            in_window = [
                event
                for event in events
                if start_event["sequence"] <= event["sequence"] <= end_event["sequence"]
                and float(start_event["elapsed_ms"]) <= float(event["elapsed_ms"]) <= float(end_event["elapsed_ms"])
            ]
            forbidden = [event for event in in_window if _event_matches(event, selector["match"])]
            forbidden_refs = [_event_ref(run, event) for event in forbidden]
            all_forbidden.extend(forbidden_refs)
            chain_window_complete = _observation_window_covers(run, start_event, end_event)
            complete_window_coverage = complete_window_coverage and chain_window_complete
            windows.append(
                {
                    "run_id": run["run_id"],
                    "session_id": run["session_id"],
                    "correlation_id": chain["correlation_id"],
                    "start_phase": window_spec["start_phase"],
                    "end_phase": window_spec["end_phase"],
                    "start_sequence": start_event["sequence"],
                    "end_sequence": end_event["sequence"],
                    "start_elapsed_ms": start_event["elapsed_ms"],
                    "end_elapsed_ms": end_event["elapsed_ms"],
                    "observation_coverage": "COMPLETE" if chain_window_complete else "INCONCLUSIVE",
                }
            )
        if all_forbidden:
            status = "VIOLATION_MATCH_FOUND"
        elif complete_window_coverage:
            status = "SATISFIED_NO_MATCH"
        else:
            status = "INCONCLUSIVE_COVERAGE"
        results.append(
            {
                "selector_index": selector_index,
                "match": selector["match"],
                "status": status,
                "windows": windows,
                "forbidden_evidence_refs": all_forbidden,
            }
        )
    return results


def _prepare_run_result(
    timeline: dict[str, Any],
    positive_selectors: dict[str, dict[str, Any]],
    negative_selectors: list[dict[str, Any]],
    ordered_sequences: list[dict[str, Any]],
) -> dict[str, Any]:
    run = timeline["run"]
    events = timeline.get("events", [])
    if not isinstance(events, list):
        events = []
    timeline_complete = _timeline_order_is_complete(events)
    if timeline_complete:
        phase_matches, positive_chains = _find_positive_chains(events, positive_selectors)
        evaluated_chains = [
            _qualify_chain_with_ordered_sequences(events, chain, ordered_sequences)
            for chain in positive_chains
        ]
        complete_chains = [
            chain for chain in evaluated_chains
            if chain["qualification_status"] == "COMPLETE"
        ]
        incomplete_chains = [
            chain for chain in evaluated_chains
            if chain["qualification_status"] == "INCOMPLETE"
        ]
    else:
        phase_matches = {phase: [] for phase in POSITIVE_CHAIN_PHASES}
        positive_chains = []
        complete_chains = []
        incomplete_chains = []
    if complete_chains:
        chain_incomplete_reason = None
    elif positive_chains:
        chain_incomplete_reason = "ORDERED_SEQUENCE_REQUIREMENTS_UNSATISFIED"
    else:
        chain_incomplete_reason = "NO_POSITIVE_PHASE_CHAIN"
    return {
        "run_id": run["run_id"],
        "session_id": run["session_id"],
        "evidence_mode": run["evidence_mode"],
        "build": run.get("build"),
        "setup": run.get("setup"),
        "display": run.get("display"),
        "performance_context": run.get("performance_context"),
        "probe_group": run.get("probe_group"),
        "timeline_coverage": "VALIDATED_ORDERED_TIMELINE" if timeline_complete else "INCONCLUSIVE_TIMELINE_ORDER",
        "observation_window": run.get("observation_window"),
        "phase_match_counts": {phase: len(matches) for phase, matches in phase_matches.items()},
        "positive_phase_chain_count": len(positive_chains),
        "chain_status": "COMPLETE" if complete_chains else "INCOMPLETE",
        "chain_incomplete_reason": chain_incomplete_reason,
        "complete_chains": [_serialize_chain(run, chain) for chain in complete_chains],
        "incomplete_chains": [_serialize_chain(run, chain) for chain in incomplete_chains],
        "branch_signatures": [_branch_signature(chain) for chain in complete_chains],
        "branch_consequence_signatures": [
            _branch_consequence_signature(chain) for chain in complete_chains
        ],
        "negative_checks": _evaluate_negative_checks(run, events, complete_chains, negative_selectors),
    }


def _branch_environment(run_result: dict[str, Any]) -> dict[str, Any]:
    setup = run_result.get("setup") if isinstance(run_result.get("setup"), dict) else {}
    return {
        "build": run_result.get("build"),
        "checkpoint": setup.get("save_or_checkpoint"),
        "seed": setup.get("seed"),
        "locale": setup.get("locale"),
        "input_mode": setup.get("input_mode"),
        "platform": setup.get("platform"),
        "display": run_result.get("display"),
        "performance_context": run_result.get("performance_context"),
    }


def _branch_environment_complete(run_result: dict[str, Any]) -> bool:
    build = run_result.get("build")
    setup = run_result.get("setup")
    display = run_result.get("display")
    performance_context = run_result.get("performance_context")
    probe_group = run_result.get("probe_group")
    if not isinstance(build, dict) or any(
        not isinstance(build.get(key), str) or not build[key]
        for key in ("build_id", "content_revision")
    ):
        return False
    if not isinstance(setup, dict):
        return False
    if any(
        not isinstance(setup.get(key), str) or not setup[key]
        for key in ("save_or_checkpoint", "locale", "input_mode", "platform")
    ) or setup.get("seed") is None:
        return False
    if not isinstance(display, dict) or any(key not in display for key in ("viewport_width", "viewport_height", "window_mode")):
        return False
    if not isinstance(performance_context, dict):
        return False
    if not isinstance(probe_group, dict) or any(
        not isinstance(probe_group.get(key), str) or not probe_group[key]
        for key in ("group_id", "baseline_checkpoint", "branch_label")
    ):
        return False
    return probe_group["baseline_checkpoint"] == setup["save_or_checkpoint"]


def _validate_controlled_probe_group_ids(
    kernel: dict[str, Any],
    required_modes: list[str],
) -> list[str]:
    """Validate explicit per-kernel controlled-probe applicability bindings."""

    field_name = "controlled_probe_group_ids"
    controlled_probe_required = "CONTROLLED_BRANCH_PROBE" in required_modes
    if not controlled_probe_required:
        if field_name in kernel:
            raise ReaderError(
                f"kernel {kernel['kernel_id']} cannot declare {field_name} "
                "without requiring CONTROLLED_BRANCH_PROBE"
            )
        return []

    group_ids = kernel.get(field_name)
    if (
        not isinstance(group_ids, list)
        or not group_ids
        or any(not isinstance(group_id, str) or not group_id.strip() for group_id in group_ids)
        or len(group_ids) != len(set(group_ids))
    ):
        raise ReaderError(
            f"kernel {kernel['kernel_id']} requires a non-empty unique {field_name} list"
        )
    return group_ids


def _evaluate_branch_groups(
    run_results: list[dict[str, Any]],
    controlled_probe_group_ids: list[str],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in run_results:
        if result["evidence_mode"] != "CONTROLLED_BRANCH_PROBE":
            continue
        probe_group = result.get("probe_group")
        group_id = probe_group.get("group_id") if isinstance(probe_group, dict) else None
        if isinstance(group_id, str) and group_id:
            groups[group_id].append(result)

    evaluations: list[dict[str, Any]] = []
    for group_id in controlled_probe_group_ids:
        results = groups.get(group_id, [])
        if not results:
            evaluations.append(
                {
                    "probe_group": group_id,
                    "status": "INCOMPLETE",
                    "declared_group_present": False,
                    "incomplete_reason": "DECLARED_PROBE_GROUP_MISSING",
                    "environment_consistent": False,
                    "branch_evidence_distinct": False,
                    "branch_consequence_evidence_distinct": False,
                    "distinct_branch_labels": [],
                    "branches": [],
                }
            )
            continue

        environments = {_compact_json(_branch_environment(result)) for result in results}
        baseline_checkpoints = {
            result["probe_group"].get("baseline_checkpoint")
            for result in results
            if isinstance(result.get("probe_group"), dict)
        }
        labels: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for result in results:
            label = result["probe_group"].get("branch_label") if isinstance(result.get("probe_group"), dict) else None
            if isinstance(label, str) and label:
                labels[label].append(result)
        branch_results = []
        label_signature_sets: dict[str, set[str]] = {}
        label_consequence_signature_sets: dict[str, set[str]] = {}
        for label, label_runs in sorted(labels.items()):
            complete_runs = [
                {"run_id": result["run_id"], "session_id": result["session_id"]}
                for result in label_runs
                if result["chain_status"] == "COMPLETE"
            ]
            signatures = {
                _compact_json(signature)
                for result in label_runs
                if result["chain_status"] == "COMPLETE"
                for signature in result.get("branch_signatures", [])
            }
            label_signature_sets[label] = signatures
            consequence_signatures = {
                _compact_json(signature)
                for result in label_runs
                if result["chain_status"] == "COMPLETE"
                for signature in result.get("branch_consequence_signatures", [])
            }
            label_consequence_signature_sets[label] = consequence_signatures
            branch_results.append(
                {
                    "branch_label": label,
                    "status": "COMPLETE" if complete_runs else "INCOMPLETE",
                    "complete_runs": complete_runs,
                    "all_runs": [
                        {"run_id": result["run_id"], "session_id": result["session_id"]}
                        for result in label_runs
                    ],
                    "observed_signatures": [json.loads(signature) for signature in sorted(signatures)],
                    "observed_consequence_signatures": [
                        json.loads(signature) for signature in sorted(consequence_signatures)
                    ],
                }
            )
        environment_consistent = (
            all(_branch_environment_complete(result) for result in results)
            and len(environments) == 1
            and len(baseline_checkpoints) == 1
        )
        two_distinct_branches = len(labels) >= 2
        label_names = sorted(label_signature_sets)
        branch_evidence_distinct = len(label_names) >= 2 and all(
            label_signature_sets[left].isdisjoint(label_signature_sets[right])
            for left_index, left in enumerate(label_names)
            for right in label_names[left_index + 1 :]
        )
        branch_consequence_evidence_distinct = len(label_names) >= 2 and all(
            label_consequence_signature_sets[left].isdisjoint(
                label_consequence_signature_sets[right]
            )
            for left_index, left in enumerate(label_names)
            for right in label_names[left_index + 1 :]
        )
        every_branch_complete = bool(branch_results) and all(
            branch["status"] == "COMPLETE" for branch in branch_results
        )
        evaluations.append(
            {
                "probe_group": group_id,
                "status": "COMPLETE"
                if environment_consistent
                and two_distinct_branches
                and every_branch_complete
                and branch_consequence_evidence_distinct
                else "INCOMPLETE",
                "declared_group_present": True,
                "environment_consistent": environment_consistent,
                "branch_evidence_distinct": branch_evidence_distinct,
                "branch_consequence_evidence_distinct": branch_consequence_evidence_distinct,
                "distinct_branch_labels": sorted(labels),
                "branches": branch_results,
            }
        )
    return evaluations


def prepare_acceptance_input(timelines: list[dict[str, Any]], kernels: Any) -> dict[str, Any]:
    if not isinstance(kernels, dict) or kernels.get("schema_version") != KERNEL_VERSION:
        raise ReaderError(f"acceptance kernels must use {KERNEL_VERSION}")
    _mapping_unknown_fields(kernels, {"schema_version", "sheet_binding", "kernels"}, "acceptance kernels")
    if not isinstance(kernels.get("sheet_binding"), dict) or not isinstance(kernels.get("kernels"), list):
        raise ReaderError("acceptance kernels require sheet_binding and kernels")
    sheet_binding = kernels["sheet_binding"]
    _mapping_unknown_fields(
        sheet_binding,
        {"path", "sheet_id", "version_token", "checksum"},
        "acceptance kernels.sheet_binding",
    )
    for key in ("path", "sheet_id", "version_token", "checksum"):
        if not isinstance(sheet_binding.get(key), str) or not sheet_binding[key].strip():
            raise ReaderError(f"acceptance kernels.sheet_binding.{key} requires a non-empty string")
    if not kernels["kernels"]:
        raise ReaderError("acceptance kernels requires at least one kernel")
    seen_run_sessions: set[tuple[str, str]] = set()
    for timeline in timelines:
        if timeline.get("schema_version") != TIMELINE_VERSION:
            raise ReaderError(f"all timelines must use {TIMELINE_VERSION}")
        _validate_acceptance_timeline(timeline)
        identity = _timeline_run_identity(timeline)
        if identity in seen_run_sessions:
            raise ReaderError(f"duplicate timeline for run/session {identity[0]}/{identity[1]}")
        seen_run_sessions.add(identity)

    available_modes = sorted({timeline["run"]["evidence_mode"] for timeline in timelines})

    kernel_results: list[dict[str, Any]] = []
    seen_kernel_ids: set[str] = set()
    for kernel in kernels["kernels"]:
        if not isinstance(kernel, dict) or not isinstance(kernel.get("kernel_id"), str) or not kernel["kernel_id"]:
            raise ReaderError("each acceptance kernel requires kernel_id")
        _mapping_unknown_fields(
            kernel,
            {
                "kernel_id",
                "required_evidence_modes",
                "controlled_probe_group_ids",
                "selectors",
                "ordered_sequences",
            },
            f"kernel {kernel['kernel_id']}",
        )
        if kernel["kernel_id"] in seen_kernel_ids:
            raise ReaderError(f"duplicate acceptance kernel id: {kernel['kernel_id']}")
        seen_kernel_ids.add(kernel["kernel_id"])

        required_modes = kernel.get("required_evidence_modes", [])
        if (
            not isinstance(required_modes, list)
            or not required_modes
            or any(not isinstance(mode, str) for mode in required_modes)
            or len(required_modes) != len(set(required_modes))
        ):
            raise ReaderError(f"kernel {kernel['kernel_id']} requires a non-empty unique evidence-mode list")
        invalid_modes = [mode for mode in required_modes if mode not in EVIDENCE_MODES]
        if invalid_modes:
            raise ReaderError(f"kernel {kernel['kernel_id']} has invalid evidence modes: {invalid_modes}")
        controlled_probe_group_ids = _validate_controlled_probe_group_ids(kernel, required_modes)

        positive_selectors, negative_selectors = _validate_kernel_selectors(kernel)
        ordered_sequences = _validate_ordered_sequences(kernel)
        run_results = [
            _prepare_run_result(
                timeline,
                positive_selectors,
                negative_selectors,
                ordered_sequences,
            )
            for timeline in timelines
        ]
        branch_groups = (
            _evaluate_branch_groups(run_results, controlled_probe_group_ids)
            if controlled_probe_group_ids
            else []
        )

        mode_coverage = []
        complete_modes = set()
        for mode in required_modes:
            if mode == "CONTROLLED_BRANCH_PROBE":
                complete_groups = [
                    group["probe_group"] for group in branch_groups if group["status"] == "COMPLETE"
                ]
                all_declared_groups_complete = (
                    len(branch_groups) == len(controlled_probe_group_ids)
                    and all(group["status"] == "COMPLETE" for group in branch_groups)
                )
                status = "COMPLETE" if all_declared_groups_complete else "INCOMPLETE"
                if all_declared_groups_complete:
                    complete_modes.add(mode)
                mode_coverage.append(
                    {
                        "evidence_mode": mode,
                        "status": status,
                        "complete_probe_groups": complete_groups,
                    }
                )
            else:
                complete_runs = [
                    {"run_id": result["run_id"], "session_id": result["session_id"]}
                    for result in run_results
                    if result["evidence_mode"] == mode and result["chain_status"] == "COMPLETE"
                ]
                if complete_runs:
                    complete_modes.add(mode)
                mode_coverage.append(
                    {
                        "evidence_mode": mode,
                        "status": "COMPLETE" if complete_runs else "INCOMPLETE",
                        "complete_runs": complete_runs,
                    }
                )
        missing_modes = sorted(set(required_modes) - complete_modes)
        kernel_results.append(
            {
                "kernel_id": kernel["kernel_id"],
                "required_evidence_modes": required_modes,
                "controlled_probe_group_ids": controlled_probe_group_ids,
                "ordered_sequence_ids": [
                    ordered_sequence["sequence_id"]
                    for ordered_sequence in ordered_sequences
                ],
                "missing_required_evidence_modes": missing_modes,
                "mode_coverage": mode_coverage,
                "run_results": run_results,
                "branch_probe_groups": branch_groups,
                "evidence_availability": "INCOMPLETE" if missing_modes else "COMPLETE_FOR_DECLARED_SELECTORS",
            }
        )

    return {
        "schema_version": ACCEPTANCE_INPUT_VERSION,
        "sheet_binding": kernels["sheet_binding"],
        "source_timelines": [
            {
                "run_id": timeline["run"]["run_id"],
                "session_id": timeline["run"]["session_id"],
                "build": timeline["run"]["build"],
                "setup": timeline["run"].get("setup"),
                "display": timeline["run"].get("display"),
                "performance_context": timeline["run"].get("performance_context", {}),
                "probe_group": timeline["run"].get("probe_group"),
                "evidence_mode": timeline["run"]["evidence_mode"],
            }
            for timeline in timelines
        ],
        "available_evidence_modes": available_modes,
        "kernels": kernel_results,
        "verdict": None,
        "boundary": "Evidence references only. A fresh acceptance reviewer must judge conformance.",
    }


def _budget_inconclusive(budget: Any, message: str) -> dict[str, Any]:
    sheet_binding = budget.get("sheet_binding") if isinstance(budget, dict) else None
    budget_id = budget.get("budget_id") if isinstance(budget, dict) else None
    return {
        "schema_version": BUDGET_RESULT_VERSION,
        "budget_id": budget_id,
        "sheet_binding": sheet_binding,
        "status": "INCONCLUSIVE_EVIDENCE",
        "exact_span": None,
        "measured": {},
        "comparisons": [],
        "gameplay_measurements": [],
        "non_gameplay_activity_evidence": [],
        "findings": [
            {
                "code": "BUDGET_EVIDENCE_INCONCLUSIVE",
                "message": message,
            }
        ],
        "boundary": (
            "Objective evidence measurement only. This result does not infer fun, "
            "player psychology, or factory conformance."
        ),
    }


def _budget_number(value: Any, context: str, *, minimum: float | None = None) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ReaderError(f"{context} must be a number")
    result = float(value)
    if minimum is not None and result < minimum:
        raise ReaderError(f"{context} must be >= {minimum:g}")
    return result


def _validate_min_max(value: Any, context: str, *, integer: bool) -> None:
    if not isinstance(value, dict) or set(value) != {"minimum", "maximum"}:
        raise ReaderError(f"{context} must contain exactly minimum and maximum")
    if integer:
        if any(not _is_integer(value.get(key)) or value[key] < 0 for key in ("minimum", "maximum")):
            raise ReaderError(f"{context} minimum/maximum must be non-negative integers")
    else:
        for key in ("minimum", "maximum"):
            _budget_number(value.get(key), f"{context}.{key}", minimum=0)
    if value["minimum"] > value["maximum"]:
        raise ReaderError(f"{context} minimum must be <= maximum")


def _validate_experience_budget(budget: Any, kernels: Any) -> None:
    if not isinstance(budget, dict) or budget.get("schema_version") != BUDGET_VERSION:
        raise ReaderError(f"experience budget must use {BUDGET_VERSION}")
    _mapping_unknown_fields(
        budget,
        {
            "schema_version",
            "budget_id",
            "sheet_binding",
            "exact_span",
            "thresholds",
            "interval_selectors",
            "gameplay_measurements",
            "non_gameplay_activity_selectors",
        },
        "experience budget",
    )
    if not isinstance(budget.get("budget_id"), str) or not budget["budget_id"].strip():
        raise ReaderError("experience budget requires a non-empty budget_id")
    if not isinstance(kernels, dict) or not isinstance(kernels.get("sheet_binding"), dict):
        raise ReaderError("acceptance kernels require sheet_binding")
    if budget.get("sheet_binding") != kernels.get("sheet_binding"):
        raise ReaderError("experience budget and acceptance kernels must have identical sheet_binding")

    span = budget.get("exact_span")
    if not isinstance(span, dict) or set(span) != {
        "start_boundary",
        "end_boundary",
    }:
        raise ReaderError("experience budget exact_span has invalid fields")
    for boundary_name in ("start_boundary", "end_boundary"):
        boundary = span.get(boundary_name)
        if not isinstance(boundary, dict) or set(boundary) != {"boundary_id", "match"}:
            raise ReaderError(f"experience budget {boundary_name} has invalid fields")
        if not isinstance(boundary.get("boundary_id"), str) or not boundary["boundary_id"].strip():
            raise ReaderError(f"experience budget {boundary_name}.boundary_id requires a non-empty string")
        _validate_match_grammar(boundary.get("match"), f"experience budget {boundary_name}")
    if span["start_boundary"]["boundary_id"] == span["end_boundary"]["boundary_id"]:
        raise ReaderError("experience budget boundary ids must be distinct")

    thresholds = budget.get("thresholds")
    required_thresholds = {
        "first_play_duration_ms",
        "minimum_player_control_ratio",
        "maximum_presentation_only_gap_ms",
        "maximum_traversal_only_gap_ms",
        "content_counts",
        "narrative_presentation_time_ms",
    }
    if not isinstance(thresholds, dict) or not required_thresholds.issubset(thresholds):
        raise ReaderError("experience budget thresholds are incomplete")
    unknown_thresholds = set(thresholds) - (required_thresholds | {"replay_target_duration_ms"})
    if unknown_thresholds:
        raise ReaderError(f"experience budget thresholds have unknown fields: {sorted(unknown_thresholds)}")
    duration = thresholds["first_play_duration_ms"]
    if not isinstance(duration, dict) or set(duration) != {"target", "minimum", "maximum"}:
        raise ReaderError("first_play_duration_ms must contain exactly target, minimum, maximum")
    duration_values = {
        key: _budget_number(duration.get(key), f"first_play_duration_ms.{key}", minimum=0)
        for key in ("target", "minimum", "maximum")
    }
    if not duration_values["minimum"] <= duration_values["target"] <= duration_values["maximum"]:
        raise ReaderError("first-play duration target must be within minimum/maximum")
    if "replay_target_duration_ms" in thresholds:
        _budget_number(thresholds["replay_target_duration_ms"], "replay_target_duration_ms", minimum=0)
    control_ratio = _budget_number(
        thresholds["minimum_player_control_ratio"],
        "minimum_player_control_ratio",
        minimum=0,
    )
    if control_ratio > 1:
        raise ReaderError("minimum_player_control_ratio must be <= 1")
    for key in ("maximum_presentation_only_gap_ms", "maximum_traversal_only_gap_ms"):
        _budget_number(thresholds[key], key, minimum=0)
    _validate_min_max(
        thresholds["narrative_presentation_time_ms"],
        "narrative_presentation_time_ms",
        integer=False,
    )
    content_counts = thresholds["content_counts"]
    required_counts = {
        "complete_gameplay_beats",
        "meaningful_decisions",
        "combat_encounters",
        "world_interactions",
        "narrative_presentations",
    }
    if not isinstance(content_counts, dict) or set(content_counts) != required_counts:
        raise ReaderError("content_counts must define every required quantitative category")
    for category in sorted(required_counts):
        _validate_min_max(content_counts[category], f"content_counts.{category}", integer=True)

    interval_selectors = budget.get("interval_selectors")
    if not isinstance(interval_selectors, dict) or set(interval_selectors) != {
        "player_control",
        "presentation",
        "traversal",
    }:
        raise ReaderError("interval_selectors must define player_control, presentation, and traversal")
    seen_interval_ids: set[str] = set()
    for interval_kind, rules in interval_selectors.items():
        if not isinstance(rules, list):
            raise ReaderError(f"interval_selectors.{interval_kind} must be an array")
        for index, rule in enumerate(rules):
            context = f"interval_selectors.{interval_kind}[{index}]"
            if not isinstance(rule, dict) or set(rule) != {"interval_id", "start_match", "end_match"}:
                raise ReaderError(f"{context} has invalid fields")
            interval_id = rule.get("interval_id")
            if not isinstance(interval_id, str) or not interval_id.strip():
                raise ReaderError(f"{context}.interval_id requires a non-empty string")
            if interval_id in seen_interval_ids:
                raise ReaderError(f"duplicate interval_id: {interval_id}")
            seen_interval_ids.add(interval_id)
            _validate_match_grammar(rule.get("start_match"), f"{context}.start_match")
            _validate_match_grammar(rule.get("end_match"), f"{context}.end_match")

    kernel_by_id = {
        kernel.get("kernel_id"): kernel
        for kernel in kernels.get("kernels", [])
        if isinstance(kernel, dict) and isinstance(kernel.get("kernel_id"), str)
    }
    measurements = budget.get("gameplay_measurements")
    if not isinstance(measurements, list) or not measurements:
        raise ReaderError("experience budget requires at least one gameplay_measurement")
    seen_measurement_ids: set[str] = set()
    seen_kernel_ids: set[str] = set()
    for index, measurement in enumerate(measurements):
        context = f"gameplay_measurements[{index}]"
        if not isinstance(measurement, dict) or set(measurement) != {
            "measurement_id",
            "kernel_id",
            "categories",
        }:
            raise ReaderError(f"{context} has invalid fields")
        measurement_id = measurement.get("measurement_id")
        kernel_id = measurement.get("kernel_id")
        categories = measurement.get("categories")
        if not isinstance(measurement_id, str) or not measurement_id.strip():
            raise ReaderError(f"{context}.measurement_id requires a non-empty string")
        if measurement_id in seen_measurement_ids:
            raise ReaderError(f"duplicate gameplay measurement id: {measurement_id}")
        seen_measurement_ids.add(measurement_id)
        if not isinstance(kernel_id, str) or kernel_id not in kernel_by_id:
            raise ReaderError(f"{context}.kernel_id must reference a declared acceptance kernel")
        if kernel_id in seen_kernel_ids:
            raise ReaderError(f"acceptance kernel {kernel_id} cannot be counted more than once")
        seen_kernel_ids.add(kernel_id)
        if (
            not isinstance(categories, list)
            or not categories
            or len(categories) > 2
            or len(categories) != len(set(categories))
            or any(category not in BUDGET_CONTENT_CATEGORIES for category in categories)
            or "complete_gameplay_beat" not in categories
        ):
            raise ReaderError(
                f"{context}.categories must contain complete_gameplay_beat and at most one content category"
            )
        if "meaningful_decision" in categories and "CONTROLLED_BRANCH_PROBE" not in kernel_by_id[kernel_id].get(
            "required_evidence_modes", []
        ):
            raise ReaderError(
                f"decision measurement {measurement_id} requires a CONTROLLED_BRANCH_PROBE kernel"
            )

    non_gameplay = budget.get("non_gameplay_activity_selectors")
    if not isinstance(non_gameplay, list):
        raise ReaderError("non_gameplay_activity_selectors must be an array")
    seen_activity_ids: set[str] = set()
    for index, activity in enumerate(non_gameplay):
        context = f"non_gameplay_activity_selectors[{index}]"
        if not isinstance(activity, dict) or set(activity) != {"activity_id", "activity_type", "match"}:
            raise ReaderError(f"{context} has invalid fields")
        activity_id = activity.get("activity_id")
        if not isinstance(activity_id, str) or not activity_id.strip() or activity_id in seen_activity_ids:
            raise ReaderError(f"{context}.activity_id must be non-empty and unique")
        seen_activity_ids.add(activity_id)
        if activity.get("activity_type") not in NON_GAMEPLAY_ACTIVITY_TYPES:
            raise ReaderError(f"{context}.activity_type is invalid")
        _validate_match_grammar(activity.get("match"), f"{context}.match")


def _unique_match(events: list[dict[str, Any]], match: dict[str, Any], context: str) -> dict[str, Any]:
    matches = [event for event in events if _event_matches(event, match)]
    if len(matches) != 1:
        raise ReaderError(f"{context} must match exactly one event; matched {len(matches)}")
    return matches[0]


def _measure_interval_rules(
    run: dict[str, Any],
    span_events: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    interval_kind: str,
) -> list[dict[str, Any]]:
    intervals: list[dict[str, Any]] = []
    for rule in rules:
        open_event: dict[str, Any] | None = None
        for event in span_events:
            is_start = _event_matches(event, rule["start_match"])
            is_end = _event_matches(event, rule["end_match"])
            if is_start and is_end:
                raise ReaderError(
                    f"interval {rule['interval_id']} has an event matching both start and end"
                )
            if is_start:
                if open_event is not None:
                    raise ReaderError(f"interval {rule['interval_id']} has a nested/unclosed start")
                open_event = event
            elif is_end:
                if open_event is None:
                    raise ReaderError(f"interval {rule['interval_id']} has an end without a start")
                if event["sequence"] <= open_event["sequence"]:
                    raise ReaderError(f"interval {rule['interval_id']} is not strictly ordered")
                intervals.append(
                    {
                        "interval_id": rule["interval_id"],
                        "kind": interval_kind,
                        "start_elapsed_ms": float(open_event["elapsed_ms"]),
                        "end_elapsed_ms": float(event["elapsed_ms"]),
                        "duration_ms": float(event["elapsed_ms"]) - float(open_event["elapsed_ms"]),
                        "start_evidence_ref": _event_ref(run, open_event),
                        "end_evidence_ref": _event_ref(run, event),
                    }
                )
                open_event = None
        if open_event is not None:
            raise ReaderError(f"interval {rule['interval_id']} has no end within the exact span")

    intervals.sort(key=lambda item: (item["start_elapsed_ms"], item["end_elapsed_ms"]))
    for left, right in zip(intervals, intervals[1:]):
        if right["start_elapsed_ms"] < left["end_elapsed_ms"]:
            raise ReaderError(f"{interval_kind} interval evidence overlaps")
    return intervals


def _flatten_interval_refs(intervals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        ref
        for interval in intervals
        for ref in (interval["start_evidence_ref"], interval["end_evidence_ref"])
    ]


def _maximum_uninterrupted_gap(
    intervals: list[dict[str, Any]],
    gameplay_ranges: list[tuple[float, float]],
) -> float:
    maximum = 0.0
    for interval in intervals:
        start = interval["start_elapsed_ms"]
        end = interval["end_elapsed_ms"]
        cursor = start
        for gameplay_start, gameplay_end in sorted(gameplay_ranges):
            if gameplay_end <= cursor or gameplay_start >= end:
                continue
            maximum = max(maximum, max(0.0, gameplay_start - cursor))
            cursor = max(cursor, min(end, gameplay_end))
        maximum = max(maximum, max(0.0, end - cursor))
    return maximum


def _total_interval_overlap_ms(
    left_intervals: list[dict[str, Any]],
    right_intervals: list[dict[str, Any]],
) -> float:
    """Return temporal overlap between two internally non-overlapping interval sets."""

    total_overlap_ms = 0.0
    for left_interval in left_intervals:
        for right_interval in right_intervals:
            overlap_start = max(
                left_interval["start_elapsed_ms"],
                right_interval["start_elapsed_ms"],
            )
            overlap_end = min(
                left_interval["end_elapsed_ms"],
                right_interval["end_elapsed_ms"],
            )
            total_overlap_ms += max(0.0, overlap_end - overlap_start)
    return total_overlap_ms


def _comparison(
    metric: str,
    operator: str,
    actual: float | int,
    threshold: float | int,
    evidence_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    passed = actual >= threshold if operator == ">=" else actual <= threshold
    return {
        "metric": metric,
        "operator": operator,
        "actual": actual,
        "threshold": threshold,
        "passed": passed,
        "source_evidence_refs": evidence_refs,
    }


def _measure_experience_budget(
    timelines: list[dict[str, Any]],
    kernels: Any,
    budget: Any,
    measurement_run_id: str,
    measurement_session_id: str,
) -> dict[str, Any]:
    _validate_experience_budget(budget, kernels)
    if not isinstance(measurement_run_id, str) or not measurement_run_id.strip():
        raise ReaderError("measurement_run_id requires a non-empty runtime-owned value")
    if not isinstance(measurement_session_id, str) or not measurement_session_id.strip():
        raise ReaderError("measurement_session_id requires a non-empty runtime-owned value")
    prepared = prepare_acceptance_input(timelines, kernels)

    span_spec = budget["exact_span"]
    base_timelines = [
        timeline
        for timeline in timelines
        if timeline["run"]["run_id"] == measurement_run_id
        and timeline["run"]["session_id"] == measurement_session_id
    ]
    if len(base_timelines) != 1:
        raise ReaderError("runtime measurement run/session must select exactly one timeline")
    base_timeline = base_timelines[0]
    run = base_timeline["run"]
    if run["evidence_mode"] not in {"LIVE_BLIND_RUN", "RECORDED_RUN"}:
        raise ReaderError("exact-span first-play measurement requires LIVE_BLIND_RUN or RECORDED_RUN")
    events = base_timeline["events"]
    start_event = _unique_match(events, span_spec["start_boundary"]["match"], "start boundary")
    end_event = _unique_match(events, span_spec["end_boundary"]["match"], "end boundary")
    if not _chain_ordered([start_event, end_event]):
        raise ReaderError("exact-span start boundary must precede end boundary")
    if not _observation_window_covers(run, start_event, end_event):
        raise ReaderError("complete contiguous observation coverage must include the exact span")
    duration_ms = float(end_event["elapsed_ms"]) - float(start_event["elapsed_ms"])
    if duration_ms <= 0:
        raise ReaderError("exact-span duration must be greater than zero")
    span_events = [
        event
        for event in events
        if start_event["sequence"] <= event["sequence"] <= end_event["sequence"]
    ]

    intervals_by_kind = {
        kind: _measure_interval_rules(
            run,
            span_events,
            budget["interval_selectors"][kind],
            kind,
        )
        for kind in ("player_control", "presentation", "traversal")
    }

    non_gameplay_evidence = []
    non_gameplay_event_ids: set[str] = set()
    for activity in budget["non_gameplay_activity_selectors"]:
        matching_events = [
            event
            for event in span_events
            if _event_matches(event, activity["match"])
        ]
        non_gameplay_event_ids.update(event["event_id"] for event in matching_events)
        non_gameplay_evidence.append(
            {
                "activity_id": activity["activity_id"],
                "activity_type": activity["activity_type"],
                "source_evidence_refs": [
                    _event_ref(run, event) for event in matching_events
                ],
            }
        )

    kernel_results = {item["kernel_id"]: item for item in prepared["kernels"]}
    gameplay_measurements: list[dict[str, Any]] = []
    selected_base_chain_keys: set[tuple[str, ...]] = set()
    complete_base_chain_keys: set[tuple[str, ...]] = set()
    gameplay_ranges: list[tuple[float, float]] = []
    for measurement in budget["gameplay_measurements"]:
        kernel_result = kernel_results[measurement["kernel_id"]]
        run_results = [
            item
            for item in kernel_result["run_results"]
            if item["run_id"] == run["run_id"] and item["session_id"] == run["session_id"]
        ]
        if len(run_results) != 1:
            raise ReaderError(f"kernel {measurement['kernel_id']} has no unique exact-span run result")
        chains = [
            chain
            for chain in run_results[0]["complete_chains"]
            if start_event["sequence"] <= chain["phases"]["cue"]["sequence"]
            and chain["phases"]["carry_forward"]["sequence"] <= end_event["sequence"]
        ]
        if len(chains) > 1:
            raise ReaderError(
                f"gameplay measurement {measurement['measurement_id']} matched multiple complete chains"
            )
        chain = chains[0] if chains else None
        chain_key: tuple[str, ...] | None = None
        chain_refs: list[dict[str, Any]] = []
        if chain is not None:
            chain_key = tuple(chain["phases"][phase]["event_id"] for phase in POSITIVE_CHAIN_PHASES)
            if chain_key in selected_base_chain_keys:
                raise ReaderError("two gameplay measurements select the same evidence chain")
            selected_base_chain_keys.add(chain_key)
            chain_refs = [chain["phases"][phase] for phase in POSITIVE_CHAIN_PHASES]

        work_response_phases = ("action_or_attempt", "world_response", "carry_forward")
        non_gameplay_only_chain = chain is not None and all(
            chain["phases"][phase]["event_id"] in non_gameplay_event_ids
            for phase in work_response_phases
        )

        decision_required = "meaningful_decision" in measurement["categories"]
        decision_groups = kernel_result["branch_probe_groups"] if decision_required else []
        decision_proven = bool(decision_groups) and all(
            group["status"] == "COMPLETE"
            and group.get("branch_consequence_evidence_distinct") is True
            for group in decision_groups
        ) if decision_required else True
        complete = (
            chain is not None
            and kernel_result["evidence_availability"] == "COMPLETE_FOR_DECLARED_SELECTORS"
            and decision_proven
            and not non_gameplay_only_chain
        )
        if complete and chain_key is not None:
            complete_base_chain_keys.add(chain_key)
            gameplay_ranges.append(
                (
                    float(chain["phases"]["cue"]["elapsed_ms"]),
                    float(chain["phases"]["carry_forward"]["elapsed_ms"]),
                )
            )
        gameplay_measurements.append(
            {
                "measurement_id": measurement["measurement_id"],
                "kernel_id": measurement["kernel_id"],
                "categories": measurement["categories"],
                "status": "COMPLETE" if complete else "INCOMPLETE",
                "base_chain_complete": chain is not None,
                "non_gameplay_only_chain": non_gameplay_only_chain,
                "gameplay_work_response_proven": chain is not None and not non_gameplay_only_chain,
                "required_mode_evidence_complete": (
                    kernel_result["evidence_availability"] == "COMPLETE_FOR_DECLARED_SELECTORS"
                ),
                "decision_consequences_proven": decision_proven if decision_required else None,
                "source_evidence_refs": chain_refs,
                "controlled_branch_evidence": decision_groups,
            }
        )

    content_counts = {
        "complete_gameplay_beats": sum(
            item["status"] == "COMPLETE" and "complete_gameplay_beat" in item["categories"]
            for item in gameplay_measurements
        ),
        "meaningful_decisions": sum(
            item["status"] == "COMPLETE" and "meaningful_decision" in item["categories"]
            for item in gameplay_measurements
        ),
        "combat_encounters": sum(
            item["status"] == "COMPLETE" and "combat_encounter" in item["categories"]
            for item in gameplay_measurements
        ),
        "world_interactions": sum(
            item["status"] == "COMPLETE" and "world_interaction" in item["categories"]
            for item in gameplay_measurements
        ),
        "narrative_presentations": len(intervals_by_kind["presentation"]),
    }
    raw_control_time_ms = sum(
        interval["duration_ms"] for interval in intervals_by_kind["player_control"]
    )
    presentation_control_overlap_ms = _total_interval_overlap_ms(
        intervals_by_kind["player_control"],
        intervals_by_kind["presentation"],
    )
    control_time_ms = max(0.0, raw_control_time_ms - presentation_control_overlap_ms)
    player_control_ratio = control_time_ms / duration_ms
    narrative_time_ms = sum(interval["duration_ms"] for interval in intervals_by_kind["presentation"])
    presentation_gap_ms = _maximum_uninterrupted_gap(
        intervals_by_kind["presentation"], gameplay_ranges
    )
    traversal_gap_ms = _maximum_uninterrupted_gap(intervals_by_kind["traversal"], gameplay_ranges)

    boundary_refs = [_event_ref(run, start_event), _event_ref(run, end_event)]
    control_refs = _flatten_interval_refs(intervals_by_kind["player_control"])
    presentation_refs = _flatten_interval_refs(intervals_by_kind["presentation"])
    traversal_refs = _flatten_interval_refs(intervals_by_kind["traversal"])
    completed_gameplay_refs = [
        ref
        for measurement in gameplay_measurements
        if measurement["status"] == "COMPLETE"
        for ref in measurement["source_evidence_refs"]
    ]
    thresholds = budget["thresholds"]
    comparisons = [
        _comparison(
            "first_play_duration_ms",
            ">=",
            duration_ms,
            thresholds["first_play_duration_ms"]["minimum"],
            boundary_refs,
        ),
        _comparison(
            "first_play_duration_ms",
            "<=",
            duration_ms,
            thresholds["first_play_duration_ms"]["maximum"],
            boundary_refs,
        ),
        _comparison(
            "player_control_ratio",
            ">=",
            player_control_ratio,
            thresholds["minimum_player_control_ratio"],
            control_refs,
        ),
        _comparison(
            "maximum_presentation_only_gap_ms",
            "<=",
            presentation_gap_ms,
            thresholds["maximum_presentation_only_gap_ms"],
            presentation_refs + completed_gameplay_refs,
        ),
        _comparison(
            "maximum_traversal_only_gap_ms",
            "<=",
            traversal_gap_ms,
            thresholds["maximum_traversal_only_gap_ms"],
            traversal_refs + completed_gameplay_refs,
        ),
    ]
    count_refs_by_category = {
        category: [
            ref
            for measurement in gameplay_measurements
            if measurement["status"] == "COMPLETE" and category in measurement["categories"]
            for ref in measurement["source_evidence_refs"]
        ]
        for category in BUDGET_CONTENT_CATEGORIES
    }
    count_refs_by_category["narrative_presentations"] = presentation_refs
    category_key = {
        "complete_gameplay_beats": "complete_gameplay_beat",
        "meaningful_decisions": "meaningful_decision",
        "combat_encounters": "combat_encounter",
        "world_interactions": "world_interaction",
        "narrative_presentations": "narrative_presentations",
    }
    for metric, actual in content_counts.items():
        threshold_range = thresholds["content_counts"][metric]
        refs = count_refs_by_category[category_key[metric]]
        comparisons.extend(
            [
                _comparison(metric, ">=", actual, threshold_range["minimum"], refs),
                _comparison(metric, "<=", actual, threshold_range["maximum"], refs),
            ]
        )
    comparisons.extend(
        [
            _comparison(
                "narrative_presentation_time_ms",
                ">=",
                narrative_time_ms,
                thresholds["narrative_presentation_time_ms"]["minimum"],
                presentation_refs,
            ),
            _comparison(
                "narrative_presentation_time_ms",
                "<=",
                narrative_time_ms,
                thresholds["narrative_presentation_time_ms"]["maximum"],
                presentation_refs,
            ),
        ]
    )

    complete_chain_count = len(complete_base_chain_keys)
    if complete_chain_count == 0:
        status = "NO_GAMEPLAY"
        no_gameplay_reason = (
            "ONLY_CONFIGURED_NON_GAMEPLAY_ACTIVITY"
            if any(item["source_evidence_refs"] for item in non_gameplay_evidence)
            else "ZERO_COMPLETE_GAMEPLAY_ENGAGEMENT_CHAINS"
        )
    else:
        status = (
            "PASS_EXPERIENCE_BUDGET"
            if all(comparison["passed"] for comparison in comparisons)
            else "FAIL_EXPERIENCE_BUDGET"
        )
        no_gameplay_reason = None

    return {
        "schema_version": BUDGET_RESULT_VERSION,
        "budget_id": budget["budget_id"],
        "sheet_binding": budget["sheet_binding"],
        "status": status,
        "exact_span": {
            "run_id": run["run_id"],
            "session_id": run["session_id"],
            "evidence_mode": run["evidence_mode"],
            "start_boundary_id": span_spec["start_boundary"]["boundary_id"],
            "end_boundary_id": span_spec["end_boundary"]["boundary_id"],
            "start_evidence_ref": boundary_refs[0],
            "end_evidence_ref": boundary_refs[1],
        },
        "measured": {
            "first_play_duration_ms": duration_ms,
            "first_play_duration_target_ms": thresholds["first_play_duration_ms"]["target"],
            "replay_target_duration_ms": thresholds.get("replay_target_duration_ms"),
            "raw_player_control_time_ms": raw_control_time_ms,
            "presentation_overlap_with_player_control_ms": presentation_control_overlap_ms,
            "player_control_time_ms": control_time_ms,
            "player_control_ratio": player_control_ratio,
            "maximum_presentation_only_gap_ms": presentation_gap_ms,
            "maximum_traversal_only_gap_ms": traversal_gap_ms,
            "narrative_presentation_time_ms": narrative_time_ms,
            "complete_gameplay_engagement_chain_count": complete_chain_count,
            "content_counts": content_counts,
            "intervals": intervals_by_kind,
        },
        "comparisons": comparisons,
        "gameplay_measurements": gameplay_measurements,
        "non_gameplay_activity_evidence": non_gameplay_evidence,
        "no_gameplay_reason": no_gameplay_reason,
        "findings": [],
        "boundary": (
            "Objective evidence measurement only. This result does not infer fun, "
            "player psychology, or factory conformance."
        ),
    }


def measure_experience_budget(
    timelines: list[dict[str, Any]],
    kernels: Any,
    budget: Any,
    *,
    measurement_run_id: str,
    measurement_session_id: str,
) -> dict[str, Any]:
    """Measure an exact observed span and fail closed without a human/fun verdict."""

    try:
        return _measure_experience_budget(
            timelines,
            kernels,
            budget,
            measurement_run_id,
            measurement_session_id,
        )
    except ReaderError as exc:
        return _budget_inconclusive(budget, str(exc))


def _cmd_validate(args: argparse.Namespace) -> None:
    owned_paths = [Path(args.manifest), Path(args.events)]
    if args.report:
        owned_paths.append(Path(args.report))
    _validate_game_ownership(args.game_repo, owned_paths)
    _, _, report = validate_evidence(Path(args.manifest), Path(args.events))
    if args.report:
        _write_json(Path(args.report), report)
    _ensure_pass(report)
    print(json.dumps(report, ensure_ascii=False))


def _cmd_normalize(args: argparse.Namespace) -> None:
    _validate_game_ownership(
        args.game_repo,
        [Path(args.manifest), Path(args.events), Path(args.mapping), Path(args.out)],
    )
    stream, _ = normalize_events(Path(args.manifest), Path(args.events), Path(args.mapping))
    _write_json(Path(args.out), stream)


def _cmd_reconstruct(args: argparse.Namespace) -> None:
    owned_paths = [Path(args.stream), Path(args.out_json), Path(args.out_md)]
    if args.report:
        owned_paths.append(Path(args.report))
    _validate_game_ownership(args.game_repo, owned_paths)
    stream = _load_json(Path(args.stream))
    try:
        timeline, report = reconstruct_timeline(stream)
    except ReaderError as exc:
        if args.report:
            run = stream.get("run", {}) if isinstance(stream, dict) else {}
            failure = _integrity_report(
                run.get("run_id"),
                [_finding("RECONSTRUCTION_FAILURE", "$", str(exc))],
                {"stream": str(args.stream)},
            )
            _write_json(Path(args.report), failure)
        raise
    _write_json(Path(args.out_json), timeline)
    Path(args.out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out_md).write_text(timeline_markdown(timeline), encoding="utf-8")
    if args.report:
        _write_json(Path(args.report), report)


def _cmd_blind(args: argparse.Namespace) -> None:
    _validate_game_ownership(args.game_repo, [Path(args.timeline), Path(args.out)])
    timeline = _load_json(Path(args.timeline))
    _write_json(Path(args.out), build_blind_projection(timeline))


def _cmd_prepare_acceptance(args: argparse.Namespace) -> None:
    _validate_game_ownership(
        args.game_repo,
        [*[Path(path) for path in args.timeline], Path(args.kernels), Path(args.out)],
    )
    timelines = [_load_json(Path(path)) for path in args.timeline]
    kernels = _load_json(Path(args.kernels))
    _write_json(Path(args.out), prepare_acceptance_input(timelines, kernels))


def _cmd_measure_budget(args: argparse.Namespace) -> None:
    owned_paths = [*[Path(path) for path in args.timeline], Path(args.kernels), Path(args.budget), Path(args.out)]
    _validate_game_ownership(args.game_repo, owned_paths)
    budget: Any = None
    try:
        timelines = [_load_json(Path(path)) for path in args.timeline]
        kernels = _load_json(Path(args.kernels))
        budget = _load_json(Path(args.budget))
        result = measure_experience_budget(
            timelines,
            kernels,
            budget,
            measurement_run_id=args.run_id,
            measurement_session_id=args.session_id,
        )
    except ReaderError as exc:
        result = _budget_inconclusive(budget, str(exc))
    _write_json(Path(args.out), result)
    print(json.dumps({"status": result["status"], "out": str(args.out)}, ensure_ascii=False))


def _cmd_run(args: argparse.Namespace) -> None:
    output = Path(args.out_dir)
    manifest_path = Path(args.manifest)
    events_path = Path(args.events)
    mapping_path = Path(args.mapping)
    _validate_game_ownership(
        args.game_repo,
        [manifest_path, events_path, mapping_path, output],
    )
    output.mkdir(parents=True, exist_ok=True)

    try:
        manifest, _, validation_report = validate_evidence(manifest_path, events_path)
        _write_json(output / "INTEGRITY_REPORT.json", validation_report)
        _ensure_pass(validation_report)
        stream, _ = normalize_events(manifest_path, events_path, mapping_path)
        _write_json(output / "CANONICAL_EVENT_STREAM.json", stream)
        timeline, reconstruction_report = reconstruct_timeline(stream)
        _write_json(output / "INTEGRITY_REPORT.json", reconstruction_report)
        _write_json(output / "OBSERVED_GAMEPLAY_TRACE.json", timeline)
        (output / "OBSERVED_GAMEPLAY_TRACE.md").write_text(timeline_markdown(timeline), encoding="utf-8")
        _write_json(output / "RUNTIME_BLIND_INPUT.json", build_blind_projection(timeline))
    except ReaderError as exc:
        # Validation already wrote a fail-closed report. Mapping/reconstruction
        # errors may not have one yet; write a concrete reader finding.
        current_report = None
        if (output / "INTEGRITY_REPORT.json").exists():
            try:
                current_report = _load_json(output / "INTEGRITY_REPORT.json")
            except ReaderError:
                current_report = None
        if not isinstance(current_report, dict) or current_report.get("status") == "PASS_INTEGRITY":
            report = _integrity_report(
                manifest.get("run_id") if "manifest" in locals() else None,
                [_finding("READER_FAILURE", "$", str(exc))],
                {"manifest": str(manifest_path), "events": str(events_path), "mapping": str(mapping_path)},
            )
            _write_json(output / "INTEGRITY_REPORT.json", report)
        raise
    print(f"PASS_INTEGRITY {manifest['run_id']} -> {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate raw evidence")
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--events", required=True)
    validate.add_argument("--report")
    validate.add_argument("--game-repo", required=True)
    validate.set_defaults(func=_cmd_validate)

    normalize = subparsers.add_parser("normalize", help="normalize events using an Observation Adapter mapping")
    normalize.add_argument("--manifest", required=True)
    normalize.add_argument("--events", required=True)
    normalize.add_argument("--mapping", required=True)
    normalize.add_argument("--out", required=True)
    normalize.add_argument("--game-repo", required=True)
    normalize.set_defaults(func=_cmd_normalize)

    reconstruct = subparsers.add_parser("reconstruct", help="reconstruct observed player time")
    reconstruct.add_argument("--stream", required=True)
    reconstruct.add_argument("--out-json", required=True)
    reconstruct.add_argument("--out-md", required=True)
    reconstruct.add_argument("--report")
    reconstruct.add_argument("--game-repo", required=True)
    reconstruct.set_defaults(func=_cmd_reconstruct)

    blind = subparsers.add_parser("blind-project", help="build sequential runtime blind input")
    blind.add_argument("--timeline", required=True)
    blind.add_argument("--out", required=True)
    blind.add_argument("--game-repo", required=True)
    blind.set_defaults(func=_cmd_blind)

    acceptance = subparsers.add_parser("prepare-acceptance", help="attach evidence refs to acceptance-kernel selectors")
    acceptance.add_argument("--timeline", required=True, action="append", help="repeat for multiple runs/probes")
    acceptance.add_argument("--kernels", required=True)
    acceptance.add_argument("--out", required=True)
    acceptance.add_argument("--game-repo", required=True)
    acceptance.set_defaults(func=_cmd_prepare_acceptance)

    budget = subparsers.add_parser(
        "measure-budget",
        help="measure and gate an exact runtime span against its quantitative experience budget",
    )
    budget.add_argument("--timeline", required=True, action="append", help="repeat for base run and probes")
    budget.add_argument("--kernels", required=True)
    budget.add_argument("--budget", required=True)
    budget.add_argument("--run-id", required=True, help="runtime-owned first-play run id")
    budget.add_argument("--session-id", required=True, help="runtime-owned first-play session id")
    budget.add_argument("--out", required=True)
    budget.add_argument("--game-repo", required=True)
    budget.set_defaults(func=_cmd_measure_budget)

    run = subparsers.add_parser("run", help="validate, normalize, reconstruct, and blind-project")
    run.add_argument("--manifest", required=True)
    run.add_argument("--events", required=True)
    run.add_argument("--mapping", required=True)
    run.add_argument("--out-dir", required=True)
    run.add_argument("--game-repo", required=True)
    run.set_defaults(func=_cmd_run)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        args.func(args)
    except ReaderError as exc:
        print(f"INCONCLUSIVE_EVIDENCE: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
