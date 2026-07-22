#!/usr/bin/env python3
"""Validate persistent production plans compiled from objective gameplay.

The production planner may be a Plan Mode model or an ordinary author model.
This tool deliberately knows nothing about that choice.  It validates the
game-owned, model-independent handoff: one manifest plus one or more durable
Markdown production plans bound to the exact OBJECTIVE_GAMEPLAY.md revision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "production_plan_manifest.v1"
READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
BLOCKED_BY_PLAN_GAP = "BLOCKED_BY_PLAN_GAP"

FACTORY_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_MANIFEST_NAME = "PRODUCTION_PLAN_MANIFEST.json"
CANONICAL_PLAN_DIRECTORY = "production_plans"

PLAN_STATUSES = {READY_FOR_EXECUTION, BLOCKED_BY_PLAN_GAP}
COVERAGE_DISPOSITIONS = {
    "IMPLEMENT",
    "VERIFY_EXISTING",
    "NO_CHANGE_REQUIRED",
}
WORK_TYPES = {
    "CONTENT_DATA",
    "CODE",
    "UI",
    "ASSET",
    "AUDIO",
    "LOCALIZATION",
    "TEST",
    "OBSERVABILITY",
}
REQUIRED_PLAN_HEADINGS = (
    "## Source authority",
    "## Required player-visible result",
    "## Existing repo evidence and reuse",
    "## Production changes",
    "## Locked constraints and non-goals",
    "## Verification",
    "## Dependencies and handoff",
)

_OBJECTIVE_ROW_PATTERN = re.compile(r"^\|\s*(\d+)\s*\|")
_PLAN_ID_PATTERN = re.compile(r"^- Plan id:\s*`([^`]+)`\s*$", re.MULTILINE)
_PLAN_STATUS_PATTERN = re.compile(r"^- Status:\s*`([^`]+)`\s*$", re.MULTILINE)
_SOURCE_OBJECTIVE_PATTERN = re.compile(
    r"^- Source objective:\s*`([^`]+)`\s*$", re.MULTILINE
)
_SOURCE_HASH_PATTERN = re.compile(
    r"^- Source SHA-256:\s*`([0-9a-f]{64})`\s*$", re.MULTILINE
)
_OBJECTIVE_ROWS_PATTERN = re.compile(
    r"^- Objective rows:\s*`([0-9, ]+)`\s*$", re.MULTILINE
)


class PlanningError(ValueError):
    """Raised for invalid repository ownership or unreadable plan inputs."""


@dataclass
class PlanValidationResult:
    """Structural production-plan readiness without an experience verdict."""

    status: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    objective_rows: list[int] = field(default_factory=list)
    plan_count: int = 0


@dataclass(frozen=True)
class _ResolvedPlan:
    plan_id: str
    path: Path
    path_text: str
    status: str
    objective_rows: tuple[int, ...]
    depends_on: tuple[str, ...]
    existing_repo_refs: tuple[Path, ...]
    planned_paths: tuple[Path, ...]


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_game_repo(raw_path: str) -> Path:
    game_repo = Path(raw_path).expanduser().resolve()
    if not game_repo.is_dir():
        raise PlanningError(f"game repo does not exist: {game_repo}")
    if game_repo == FACTORY_ROOT or _is_within(game_repo, FACTORY_ROOT):
        raise PlanningError("game repo must not be this factory repo or a child of it")
    return game_repo


def _resolve_portable_owned_path(
    game_repo: Path,
    raw_path: Any,
    *,
    must_exist: bool = False,
    allow_absolute: bool = False,
) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise PlanningError("persisted paths must be non-empty strings")
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute() and not allow_absolute:
        raise PlanningError(f"persisted path must be game-repo-relative: {raw_path}")
    resolved = (candidate if candidate.is_absolute() else game_repo / candidate).resolve()
    if not _is_within(resolved, game_repo):
        raise PlanningError(f"path escapes game repo: {raw_path}")
    if must_exist and not resolved.exists():
        raise PlanningError(f"required path does not exist: {raw_path}")
    return resolved


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PlanningError(f"cannot read {label} JSON: {error}") from error
    if not isinstance(payload, dict):
        raise PlanningError(f"{label} JSON must contain an object")
    return payload


def _require_text(value: Any, label: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return ""
    return value.strip()


def _require_string_list(
    value: Any,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = True,
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return []
    if not allow_empty and not value:
        errors.append(f"{label} must contain at least one value")
    result: list[str] = []
    for index, item in enumerate(value):
        text = _require_text(item, f"{label}[{index}]", errors)
        if text:
            result.append(text)
    if len(result) != len(set(result)):
        errors.append(f"{label} must not contain duplicates")
    return result


def _require_integer_list(
    value: Any,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> list[int]:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return []
    if not allow_empty and not value:
        errors.append(f"{label} must contain at least one row")
    result: list[int] = []
    for index, item in enumerate(value):
        if not isinstance(item, int) or isinstance(item, bool) or item < 1:
            errors.append(f"{label}[{index}] must be a positive integer")
            continue
        result.append(item)
    if len(result) != len(set(result)):
        errors.append(f"{label} must not contain duplicate rows")
    return result


def _extract_objective_rows(objective_text: str, errors: list[str]) -> list[int]:
    rows: list[int] = []
    for line in objective_text.splitlines():
        match = _OBJECTIVE_ROW_PATTERN.match(line)
        if match:
            rows.append(int(match.group(1)))
    if not rows:
        errors.append("OBJECTIVE_GAMEPLAY.md contains no numbered gameplay rows")
        return []
    if len(rows) != len(set(rows)):
        errors.append("OBJECTIVE_GAMEPLAY.md contains duplicate row numbers")
    if rows != sorted(rows):
        errors.append("OBJECTIVE_GAMEPLAY.md row numbers must be in ascending order")
    return rows


def _parse_plan_rows(plan_text: str, label: str, errors: list[str]) -> list[int]:
    match = _OBJECTIVE_ROWS_PATTERN.search(plan_text)
    if match is None:
        errors.append(f"{label} lacks '- Objective rows: `...`' metadata")
        return []
    raw_values = [value.strip() for value in match.group(1).split(",")]
    rows = [int(value) for value in raw_values if value]
    if not rows or len(rows) != len(set(rows)):
        errors.append(f"{label} objective-row metadata is empty or duplicated")
    return rows


def _match_metadata(
    pattern: re.Pattern[str],
    plan_text: str,
    label: str,
    field_name: str,
    errors: list[str],
) -> str:
    match = pattern.search(plan_text)
    if match is None:
        errors.append(f"{label} lacks {field_name} metadata")
        return ""
    return match.group(1).strip()


def _has_dependency_cycle(plans: list[_ResolvedPlan]) -> bool:
    dependencies = {plan.plan_id: set(plan.depends_on) for plan in plans}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(plan_id: str) -> bool:
        if plan_id in visiting:
            return True
        if plan_id in visited:
            return False
        visiting.add(plan_id)
        for dependency in dependencies.get(plan_id, set()):
            if visit(dependency):
                return True
        visiting.remove(plan_id)
        visited.add(plan_id)
        return False

    return any(visit(plan_id) for plan_id in dependencies)


def _validate_plan_markdown(
    plan: _ResolvedPlan,
    plan_text: str,
    objective_path_text: str,
    objective_sha256: str,
    errors: list[str],
) -> None:
    label = f"plan {plan.plan_id} ({plan.path_text})"
    if not plan_text.startswith("# Production Plan —"):
        errors.append(f"{label} must begin with '# Production Plan —'")
    for heading in REQUIRED_PLAN_HEADINGS:
        if heading not in plan_text:
            errors.append(f"{label} lacks required heading: {heading}")

    markdown_plan_id = _match_metadata(
        _PLAN_ID_PATTERN, plan_text, label, "Plan id", errors
    )
    markdown_status = _match_metadata(
        _PLAN_STATUS_PATTERN, plan_text, label, "Status", errors
    )
    markdown_objective = _match_metadata(
        _SOURCE_OBJECTIVE_PATTERN, plan_text, label, "Source objective", errors
    )
    markdown_hash = _match_metadata(
        _SOURCE_HASH_PATTERN, plan_text, label, "Source SHA-256", errors
    )
    markdown_rows = _parse_plan_rows(plan_text, label, errors)

    if markdown_plan_id and markdown_plan_id != plan.plan_id:
        errors.append(f"{label} Plan id does not match the manifest")
    if markdown_status and markdown_status != plan.status:
        errors.append(f"{label} Status does not match the manifest")
    if markdown_objective and markdown_objective != objective_path_text:
        errors.append(f"{label} Source objective does not match the manifest")
    if markdown_hash and markdown_hash != objective_sha256:
        errors.append(f"{label} Source SHA-256 does not match the manifest")
    if markdown_rows and markdown_rows != list(plan.objective_rows):
        errors.append(f"{label} Objective rows do not match the manifest")
    if plan.status == READY_FOR_EXECUTION and re.search(r"\bTBD\b", plan_text):
        errors.append(f"{label} is READY_FOR_EXECUTION but still contains TBD")


def validate_production_plan(
    game_repo_text: str,
    manifest_text: str,
) -> PlanValidationResult:
    """Validate one game-owned manifest and every plan it owns."""

    game_repo = _resolve_game_repo(game_repo_text)
    manifest_path = _resolve_portable_owned_path(
        game_repo, manifest_text, must_exist=True, allow_absolute=True
    )
    if not manifest_path.is_file():
        raise PlanningError(f"manifest is not a file: {manifest_text}")
    if manifest_path.name != CANONICAL_MANIFEST_NAME:
        raise PlanningError(
            f"manifest must be named {CANONICAL_MANIFEST_NAME}: {manifest_text}"
        )
    payload = _load_json_object(manifest_path, "production plan manifest")

    errors: list[str] = []
    warnings: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    _require_text(payload.get("project_id"), "project_id", errors)
    objective_id = _require_text(payload.get("objective_id"), "objective_id", errors)
    objective_path_text = _require_text(
        payload.get("objective_gameplay_path"), "objective_gameplay_path", errors
    )
    declared_objective_sha256 = _require_text(
        payload.get("objective_gameplay_sha256"),
        "objective_gameplay_sha256",
        errors,
    )
    planning_status = _require_text(
        payload.get("planning_status"), "planning_status", errors
    )
    if planning_status and planning_status not in PLAN_STATUSES:
        errors.append("planning_status has an unsupported value")
    blocked_gaps = _require_string_list(
        payload.get("blocked_gaps"), "blocked_gaps", errors
    )

    if not objective_path_text:
        return PlanValidationResult(BLOCKED_BY_PLAN_GAP, errors=errors)

    # Resolve every persisted path before reading the objective or plans.
    objective_path = _resolve_portable_owned_path(
        game_repo, objective_path_text, must_exist=True
    )
    if not objective_path.is_file():
        raise PlanningError(f"objective gameplay path is not a file: {objective_path_text}")
    if manifest_path.parent != objective_path.parent:
        raise PlanningError(
            "manifest must live beside its source OBJECTIVE_GAMEPLAY.md"
        )
    canonical_plan_root = (objective_path.parent / CANONICAL_PLAN_DIRECTORY).resolve()

    raw_plans = payload.get("plans")
    if not isinstance(raw_plans, list) or not raw_plans:
        errors.append("plans must contain at least one production plan")
        raw_plans = []

    resolved_plans: list[_ResolvedPlan] = []
    seen_plan_ids: set[str] = set()
    seen_plan_paths: set[Path] = set()
    planned_path_owner: dict[Path, str] = {}
    for plan_index, raw_plan in enumerate(raw_plans):
        label = f"plans[{plan_index}]"
        if not isinstance(raw_plan, dict):
            errors.append(f"{label} must be an object")
            continue
        plan_id = _require_text(raw_plan.get("plan_id"), f"{label}.plan_id", errors)
        path_text = _require_text(raw_plan.get("path"), f"{label}.path", errors)
        _require_text(raw_plan.get("title"), f"{label}.title", errors)
        plan_status = _require_text(raw_plan.get("status"), f"{label}.status", errors)
        if plan_status and plan_status not in PLAN_STATUSES:
            errors.append(f"{label}.status has an unsupported value")
        objective_rows = _require_integer_list(
            raw_plan.get("objective_rows"), f"{label}.objective_rows", errors
        )
        depends_on = _require_string_list(
            raw_plan.get("depends_on"), f"{label}.depends_on", errors
        )
        work_types = _require_string_list(
            raw_plan.get("work_types"),
            f"{label}.work_types",
            errors,
            allow_empty=False,
        )
        for work_type in work_types:
            if work_type not in WORK_TYPES:
                errors.append(f"{label}.work_types has unsupported value: {work_type}")
        existing_ref_texts = _require_string_list(
            raw_plan.get("existing_repo_refs"),
            f"{label}.existing_repo_refs",
            errors,
            allow_empty=False,
        )
        planned_path_texts = _require_string_list(
            raw_plan.get("planned_paths"),
            f"{label}.planned_paths",
            errors,
            allow_empty=False,
        )

        if plan_id in seen_plan_ids:
            errors.append(f"duplicate plan_id: {plan_id}")
        seen_plan_ids.add(plan_id)
        if plan_id and plan_id in depends_on:
            errors.append(f"{label} cannot depend on itself")

        if not path_text:
            continue
        plan_path = _resolve_portable_owned_path(
            game_repo, path_text, must_exist=True
        )
        if not plan_path.is_file():
            raise PlanningError(f"production plan is not a file: {path_text}")
        if plan_path.suffix.lower() != ".md":
            raise PlanningError(f"production plan must be Markdown: {path_text}")
        if plan_path.parent != canonical_plan_root:
            raise PlanningError(
                f"production plan must live in {CANONICAL_PLAN_DIRECTORY}/: {path_text}"
            )
        if plan_path in seen_plan_paths:
            errors.append(f"duplicate production plan path: {path_text}")
        seen_plan_paths.add(plan_path)

        existing_refs = tuple(
            _resolve_portable_owned_path(game_repo, path, must_exist=True)
            for path in existing_ref_texts
        )
        planned_paths = tuple(
            _resolve_portable_owned_path(game_repo, path)
            for path in planned_path_texts
        )
        for planned_path in planned_paths:
            previous_owner = planned_path_owner.get(planned_path)
            if previous_owner is not None and previous_owner != plan_id:
                errors.append(
                    "planned path is owned by multiple production plans: "
                    f"{planned_path.relative_to(game_repo)} ({previous_owner}, {plan_id})"
                )
            planned_path_owner[planned_path] = plan_id

        resolved_plans.append(
            _ResolvedPlan(
                plan_id=plan_id,
                path=plan_path,
                path_text=path_text,
                status=plan_status,
                objective_rows=tuple(objective_rows),
                depends_on=tuple(depends_on),
                existing_repo_refs=existing_refs,
                planned_paths=planned_paths,
            )
        )

    objective_text = objective_path.read_text(encoding="utf-8")
    objective_sha256 = hashlib.sha256(objective_text.encode("utf-8")).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", declared_objective_sha256):
        errors.append("objective_gameplay_sha256 must be 64 lowercase hex characters")
    elif declared_objective_sha256 != objective_sha256:
        errors.append("objective_gameplay_sha256 does not match OBJECTIVE_GAMEPLAY.md")
    if objective_id and objective_id not in objective_text:
        errors.append("objective_id is not present in OBJECTIVE_GAMEPLAY.md")
    objective_rows = _extract_objective_rows(objective_text, errors)

    plan_ids = {plan.plan_id for plan in resolved_plans}
    for plan in resolved_plans:
        for dependency in plan.depends_on:
            if dependency not in plan_ids:
                errors.append(
                    f"plan {plan.plan_id} depends on unknown plan: {dependency}"
                )
    if _has_dependency_cycle(resolved_plans):
        errors.append("production plan dependencies contain a cycle")

    raw_coverage = payload.get("row_coverage")
    if not isinstance(raw_coverage, list) or not raw_coverage:
        errors.append("row_coverage must contain every objective row")
        raw_coverage = []
    coverage_by_row: dict[int, dict[str, Any]] = {}
    plan_rows_from_coverage: dict[str, set[int]] = {
        plan_id: set() for plan_id in plan_ids
    }
    for coverage_index, raw_entry in enumerate(raw_coverage):
        label = f"row_coverage[{coverage_index}]"
        if not isinstance(raw_entry, dict):
            errors.append(f"{label} must be an object")
            continue
        row_value = raw_entry.get("objective_row")
        if not isinstance(row_value, int) or isinstance(row_value, bool) or row_value < 1:
            errors.append(f"{label}.objective_row must be a positive integer")
            continue
        if row_value in coverage_by_row:
            errors.append(f"objective row has duplicate coverage: {row_value}")
        coverage_by_row[row_value] = raw_entry
        disposition = _require_text(
            raw_entry.get("disposition"), f"{label}.disposition", errors
        )
        if disposition and disposition not in COVERAGE_DISPOSITIONS:
            errors.append(f"{label}.disposition has an unsupported value")
        coverage_plan_ids = _require_string_list(
            raw_entry.get("plan_ids"), f"{label}.plan_ids", errors
        )
        _require_text(raw_entry.get("rationale"), f"{label}.rationale", errors)
        if disposition in {"IMPLEMENT", "VERIFY_EXISTING"} and not coverage_plan_ids:
            errors.append(f"{label} requires at least one responsible plan")
        if disposition == "NO_CHANGE_REQUIRED" and coverage_plan_ids:
            errors.append(f"{label} NO_CHANGE_REQUIRED must not name a plan")
        for coverage_plan_id in coverage_plan_ids:
            if coverage_plan_id not in plan_ids:
                errors.append(
                    f"{label} references unknown plan: {coverage_plan_id}"
                )
                continue
            plan_rows_from_coverage[coverage_plan_id].add(row_value)

    if objective_rows:
        objective_row_set = set(objective_rows)
        coverage_row_set = set(coverage_by_row)
        missing_rows = sorted(objective_row_set - coverage_row_set)
        extra_rows = sorted(coverage_row_set - objective_row_set)
        if missing_rows:
            errors.append(
                "row_coverage is missing objective rows: "
                + ", ".join(str(row) for row in missing_rows)
            )
        if extra_rows:
            errors.append(
                "row_coverage contains unknown objective rows: "
                + ", ".join(str(row) for row in extra_rows)
            )

    for plan in resolved_plans:
        manifest_rows = set(plan.objective_rows)
        covered_rows = plan_rows_from_coverage.get(plan.plan_id, set())
        if manifest_rows != covered_rows:
            errors.append(
                f"plan {plan.plan_id} objective_rows do not match row_coverage"
            )
        plan_text = plan.path.read_text(encoding="utf-8")
        _validate_plan_markdown(
            plan,
            plan_text,
            objective_path_text,
            objective_sha256,
            errors,
        )

    if planning_status == READY_FOR_EXECUTION:
        if blocked_gaps:
            errors.append("READY_FOR_EXECUTION manifest must have no blocked_gaps")
        blocked_plans = [
            plan.plan_id for plan in resolved_plans if plan.status != READY_FOR_EXECUTION
        ]
        if blocked_plans:
            errors.append(
                "READY_FOR_EXECUTION manifest contains blocked plans: "
                + ", ".join(blocked_plans)
            )
    elif planning_status == BLOCKED_BY_PLAN_GAP and not blocked_gaps:
        errors.append("BLOCKED_BY_PLAN_GAP manifest requires at least one blocked gap")

    status = BLOCKED_BY_PLAN_GAP if errors else planning_status
    return PlanValidationResult(
        status=status,
        errors=errors,
        warnings=warnings,
        objective_rows=objective_rows,
        plan_count=len(resolved_plans),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate"])
    parser.add_argument("--game-repo", required=True)
    parser.add_argument("--manifest", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = validate_production_plan(args.game_repo, args.manifest)
    except PlanningError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(result.status)
    print(f"PLANS: {result.plan_count}")
    print(f"OBJECTIVE_ROWS: {len(result.objective_rows)}")
    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result.status == READY_FOR_EXECUTION else 2


if __name__ == "__main__":
    raise SystemExit(main())
