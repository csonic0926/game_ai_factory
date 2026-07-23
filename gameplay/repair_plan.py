#!/usr/bin/env python3
"""Validate persistent production plans for one Case 3 gameplay repair.

Repair planning is deliberately separate from objective production planning:
it binds an exact repair source and its exact base OBJECTIVE_GAMEPLAY.md
revision, covers every numbered repair row once, and prevents small repairs
from silently widening into unrelated redesign or overlapping file ownership.
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


SCHEMA_VERSION = "repair_plan_manifest.v1"
READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
BLOCKED_BY_PLAN_GAP = "BLOCKED_BY_PLAN_GAP"

FACTORY_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_MANIFEST_NAME = "REPAIR_PLAN_MANIFEST.json"
CANONICAL_PLAN_DIRECTORY = "production_plans"
ALLOWED_REPAIR_SOURCE_NAMES = {
    "GAMEPLAY_REPAIR_CONTEXT.md",
    "GAMEPLAY_REPAIR.md",
}

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

_REPAIR_ROW_PATTERN = re.compile(r"^\|\s*(\d+)\s*\|")
_PLAN_ID_PATTERN = re.compile(r"^- Plan id:\s*`([^`]+)`\s*$", re.MULTILINE)
_PLAN_STATUS_PATTERN = re.compile(r"^- Status:\s*`([^`]+)`\s*$", re.MULTILINE)
_ANCHOR_OBJECTIVE_PATTERN = re.compile(
    r"^- Anchor objective:\s*`([^`]+)`\s*$", re.MULTILINE
)
_ANCHOR_HASH_PATTERN = re.compile(
    r"^- Anchor SHA-256:\s*`([0-9a-f]{64})`\s*$", re.MULTILINE
)
_SOURCE_REPAIR_PATTERN = re.compile(
    r"^- Source repair:\s*`([^`]+)`\s*$", re.MULTILINE
)
_SOURCE_HASH_PATTERN = re.compile(
    r"^- Source SHA-256:\s*`([0-9a-f]{64})`\s*$", re.MULTILINE
)
_REPAIR_ROWS_PATTERN = re.compile(
    r"^- Repair rows:\s*`([0-9, ]+)`\s*$", re.MULTILINE
)


class RepairPlanningError(ValueError):
    """Raised for invalid ownership or unreadable repair plan inputs."""


@dataclass
class RepairPlanValidationResult:
    """Structural repair-plan readiness without an experience verdict."""

    status: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    repair_rows: list[int] = field(default_factory=list)
    plan_count: int = 0


@dataclass(frozen=True)
class _ResolvedPlan:
    plan_id: str
    path: Path
    path_text: str
    status: str
    repair_rows: tuple[int, ...]
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
        raise RepairPlanningError(f"game repo does not exist: {game_repo}")
    if game_repo == FACTORY_ROOT or _is_within(game_repo, FACTORY_ROOT):
        raise RepairPlanningError(
            "game repo must not be this factory repo or a child of it"
        )
    return game_repo


def _resolve_portable_owned_path(
    game_repo: Path,
    raw_path: Any,
    *,
    must_exist: bool = False,
    allow_absolute: bool = False,
) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise RepairPlanningError("persisted paths must be non-empty strings")
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute() and not allow_absolute:
        raise RepairPlanningError(
            f"persisted path must be game-repo-relative: {raw_path}"
        )
    resolved = (candidate if candidate.is_absolute() else game_repo / candidate).resolve()
    if not _is_within(resolved, game_repo):
        raise RepairPlanningError(f"path escapes game repo: {raw_path}")
    if must_exist and not resolved.exists():
        raise RepairPlanningError(f"required path does not exist: {raw_path}")
    return resolved


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RepairPlanningError(f"cannot read {label} JSON: {error}") from error
    if not isinstance(payload, dict):
        raise RepairPlanningError(f"{label} JSON must contain an object")
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


def _extract_repair_rows(repair_text: str, errors: list[str]) -> list[int]:
    rows: list[int] = []
    for line in repair_text.splitlines():
        match = _REPAIR_ROW_PATTERN.match(line)
        if match:
            rows.append(int(match.group(1)))
    if not rows:
        errors.append("repair source contains no numbered repair rows")
        return []
    if len(rows) != len(set(rows)):
        errors.append("repair source contains duplicate repair row numbers")
    if rows != sorted(rows):
        errors.append("repair source row numbers must be in ascending order")
    return rows


def _parse_plan_rows(plan_text: str, label: str, errors: list[str]) -> list[int]:
    match = _REPAIR_ROWS_PATTERN.search(plan_text)
    if match is None:
        errors.append(f"{label} lacks '- Repair rows: `...`' metadata")
        return []
    raw_values = [value.strip() for value in match.group(1).split(",")]
    rows = [int(value) for value in raw_values if value]
    if not rows or len(rows) != len(set(rows)):
        errors.append(f"{label} repair-row metadata is empty or duplicated")
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
    anchor_path_text: str,
    anchor_sha256: str,
    repair_source_path_text: str,
    repair_source_sha256: str,
    errors: list[str],
) -> None:
    label = f"plan {plan.plan_id} ({plan.path_text})"
    if not plan_text.startswith("# Repair Production Plan —"):
        errors.append(f"{label} must begin with '# Repair Production Plan —'")
    for heading in REQUIRED_PLAN_HEADINGS:
        if heading not in plan_text:
            errors.append(f"{label} lacks required heading: {heading}")

    markdown_plan_id = _match_metadata(
        _PLAN_ID_PATTERN, plan_text, label, "Plan id", errors
    )
    markdown_status = _match_metadata(
        _PLAN_STATUS_PATTERN, plan_text, label, "Status", errors
    )
    markdown_anchor = _match_metadata(
        _ANCHOR_OBJECTIVE_PATTERN, plan_text, label, "Anchor objective", errors
    )
    markdown_anchor_hash = _match_metadata(
        _ANCHOR_HASH_PATTERN, plan_text, label, "Anchor SHA-256", errors
    )
    markdown_repair_source = _match_metadata(
        _SOURCE_REPAIR_PATTERN, plan_text, label, "Source repair", errors
    )
    markdown_source_hash = _match_metadata(
        _SOURCE_HASH_PATTERN, plan_text, label, "Source SHA-256", errors
    )
    markdown_rows = _parse_plan_rows(plan_text, label, errors)

    if markdown_plan_id and markdown_plan_id != plan.plan_id:
        errors.append(f"{label} Plan id does not match the manifest")
    if markdown_status and markdown_status != plan.status:
        errors.append(f"{label} Status does not match the manifest")
    if markdown_anchor and markdown_anchor != anchor_path_text:
        errors.append(f"{label} Anchor objective does not match the manifest")
    if markdown_anchor_hash and markdown_anchor_hash != anchor_sha256:
        errors.append(f"{label} Anchor SHA-256 does not match the manifest")
    if markdown_repair_source and markdown_repair_source != repair_source_path_text:
        errors.append(f"{label} Source repair does not match the manifest")
    if markdown_source_hash and markdown_source_hash != repair_source_sha256:
        errors.append(f"{label} Source SHA-256 does not match the manifest")
    if markdown_rows and markdown_rows != list(plan.repair_rows):
        errors.append(f"{label} Repair rows do not match the manifest")
    if plan.status == READY_FOR_EXECUTION and re.search(r"\bTBD\b", plan_text):
        errors.append(f"{label} is READY_FOR_EXECUTION but still contains TBD")


def validate_repair_plan(
    game_repo_text: str,
    manifest_text: str,
) -> RepairPlanValidationResult:
    """Validate one repair manifest and every production plan it owns."""

    game_repo = _resolve_game_repo(game_repo_text)
    manifest_path = _resolve_portable_owned_path(
        game_repo, manifest_text, must_exist=True, allow_absolute=True
    )
    if not manifest_path.is_file():
        raise RepairPlanningError(f"manifest is not a file: {manifest_text}")
    if manifest_path.name != CANONICAL_MANIFEST_NAME:
        raise RepairPlanningError(
            f"manifest must be named {CANONICAL_MANIFEST_NAME}: {manifest_text}"
        )
    payload = _load_json_object(manifest_path, "repair plan manifest")

    errors: list[str] = []
    warnings: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    _require_text(payload.get("project_id"), "project_id", errors)
    gap_id = _require_text(payload.get("gap_id"), "gap_id", errors)
    if gap_id and not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", gap_id):
        errors.append(
            "gap_id must be a portable lowercase path component ([a-z0-9._-])"
        )
    anchor_objective_id = _require_text(
        payload.get("anchor_objective_id"), "anchor_objective_id", errors
    )
    anchor_path_text = _require_text(
        payload.get("anchor_objective_gameplay_path"),
        "anchor_objective_gameplay_path",
        errors,
    )
    declared_anchor_sha256 = _require_text(
        payload.get("anchor_objective_gameplay_sha256"),
        "anchor_objective_gameplay_sha256",
        errors,
    )
    repair_source_path_text = _require_text(
        payload.get("repair_source_path"), "repair_source_path", errors
    )
    declared_repair_source_sha256 = _require_text(
        payload.get("repair_source_sha256"), "repair_source_sha256", errors
    )
    planning_status = _require_text(
        payload.get("planning_status"), "planning_status", errors
    )
    if planning_status and planning_status not in PLAN_STATUSES:
        errors.append("planning_status has an unsupported value")
    blocked_gaps = _require_string_list(
        payload.get("blocked_gaps"), "blocked_gaps", errors
    )

    if not anchor_path_text or not repair_source_path_text:
        return RepairPlanValidationResult(BLOCKED_BY_PLAN_GAP, errors=errors)

    # Resolve all manifest-owned paths before reading or mutating anything.
    anchor_path = _resolve_portable_owned_path(
        game_repo, anchor_path_text, must_exist=True
    )
    repair_source_path = _resolve_portable_owned_path(
        game_repo, repair_source_path_text, must_exist=True
    )
    if not anchor_path.is_file():
        raise RepairPlanningError(
            f"anchor objective gameplay is not a file: {anchor_path_text}"
        )
    if not repair_source_path.is_file():
        raise RepairPlanningError(
            f"repair source is not a file: {repair_source_path_text}"
        )
    if repair_source_path.name not in ALLOWED_REPAIR_SOURCE_NAMES:
        raise RepairPlanningError(
            "repair source must be GAMEPLAY_REPAIR_CONTEXT.md or "
            "GAMEPLAY_REPAIR.md"
        )
    canonical_objective_root = (
        game_repo / "design/gameplay/objective_gameplay"
    ).resolve()
    if (
        anchor_path.name != "OBJECTIVE_GAMEPLAY.md"
        or not _is_within(anchor_path, canonical_objective_root)
    ):
        raise RepairPlanningError(
            "anchor objective must be a canonical "
            "design/gameplay/objective_gameplay/**/OBJECTIVE_GAMEPLAY.md"
        )
    canonical_repair_directory = (
        game_repo / "design/gameplay/repairs" / gap_id
    ).resolve()
    if repair_source_path.parent != canonical_repair_directory:
        raise RepairPlanningError(
            "repair source must live in "
            "design/gameplay/repairs/<gap_id>/"
        )
    if manifest_path.parent != repair_source_path.parent:
        raise RepairPlanningError("repair manifest must live beside its repair source")
    canonical_plan_root = (
        repair_source_path.parent / CANONICAL_PLAN_DIRECTORY
    ).resolve()

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
        repair_rows = _require_integer_list(
            raw_plan.get("repair_rows"), f"{label}.repair_rows", errors
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
                errors.append(
                    f"{label}.work_types has unsupported value: {work_type}"
                )
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
            raise RepairPlanningError(f"repair production plan is not a file: {path_text}")
        if plan_path.suffix.lower() != ".md":
            raise RepairPlanningError(
                f"repair production plan must be Markdown: {path_text}"
            )
        if plan_path.parent != canonical_plan_root:
            raise RepairPlanningError(
                f"repair production plan must live in "
                f"{CANONICAL_PLAN_DIRECTORY}/: {path_text}"
            )
        if plan_path in seen_plan_paths:
            errors.append(f"duplicate repair production plan path: {path_text}")
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
            if planned_path == anchor_path:
                errors.append(
                    "repair plan may not mutate its base OBJECTIVE_GAMEPLAY.md"
                )
            if planned_path in {
                repair_source_path,
                manifest_path,
                plan_path,
            }:
                errors.append(
                    "repair plan may not mutate its repair authority or planning "
                    f"contract: {planned_path.relative_to(game_repo)}"
                )
            previous_owner = planned_path_owner.get(planned_path)
            if previous_owner is not None and previous_owner != plan_id:
                errors.append(
                    "planned path is owned by multiple repair plans: "
                    f"{planned_path.relative_to(game_repo)} "
                    f"({previous_owner}, {plan_id})"
                )
            planned_path_owner[planned_path] = plan_id

        resolved_plans.append(
            _ResolvedPlan(
                plan_id=plan_id,
                path=plan_path,
                path_text=path_text,
                status=plan_status,
                repair_rows=tuple(repair_rows),
                depends_on=tuple(depends_on),
                existing_repo_refs=existing_refs,
                planned_paths=planned_paths,
            )
        )

    anchor_text = anchor_path.read_text(encoding="utf-8")
    anchor_sha256 = hashlib.sha256(anchor_text.encode("utf-8")).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", declared_anchor_sha256):
        errors.append(
            "anchor_objective_gameplay_sha256 must be 64 lowercase hex characters"
        )
    elif declared_anchor_sha256 != anchor_sha256:
        errors.append(
            "anchor_objective_gameplay_sha256 does not match "
            "OBJECTIVE_GAMEPLAY.md"
        )
    if anchor_objective_id and anchor_objective_id not in anchor_text:
        errors.append(
            "anchor_objective_id is not present in OBJECTIVE_GAMEPLAY.md"
        )

    repair_source_text = repair_source_path.read_text(encoding="utf-8")
    repair_source_sha256 = hashlib.sha256(
        repair_source_text.encode("utf-8")
    ).hexdigest()
    if not re.fullmatch(r"[0-9a-f]{64}", declared_repair_source_sha256):
        errors.append("repair_source_sha256 must be 64 lowercase hex characters")
    elif declared_repair_source_sha256 != repair_source_sha256:
        errors.append("repair_source_sha256 does not match the repair source")
    if gap_id and gap_id not in repair_source_text:
        errors.append("gap_id is not present in the repair source")
    if f"- Anchor objective: `{anchor_path_text}`" not in repair_source_text:
        errors.append("repair source Anchor objective does not match the manifest")
    if f"- Anchor SHA-256: `{anchor_sha256}`" not in repair_source_text:
        errors.append("repair source Anchor SHA-256 does not match the manifest")
    repair_rows = _extract_repair_rows(repair_source_text, errors)

    plan_ids = {plan.plan_id for plan in resolved_plans}
    for plan in resolved_plans:
        for dependency in plan.depends_on:
            if dependency not in plan_ids:
                errors.append(
                    f"plan {plan.plan_id} depends on unknown plan: {dependency}"
                )
    if _has_dependency_cycle(resolved_plans):
        errors.append("repair plan dependencies contain a cycle")

    raw_coverage = payload.get("repair_coverage")
    if not isinstance(raw_coverage, list) or not raw_coverage:
        errors.append("repair_coverage must contain every repair row")
        raw_coverage = []
    coverage_by_row: dict[int, dict[str, Any]] = {}
    plan_rows_from_coverage: dict[str, set[int]] = {
        plan_id: set() for plan_id in plan_ids
    }
    for coverage_index, raw_entry in enumerate(raw_coverage):
        label = f"repair_coverage[{coverage_index}]"
        if not isinstance(raw_entry, dict):
            errors.append(f"{label} must be an object")
            continue
        row_value = raw_entry.get("repair_row")
        if not isinstance(row_value, int) or isinstance(row_value, bool) or row_value < 1:
            errors.append(f"{label}.repair_row must be a positive integer")
            continue
        if row_value in coverage_by_row:
            errors.append(f"repair row has duplicate coverage: {row_value}")
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

    if repair_rows:
        repair_row_set = set(repair_rows)
        coverage_row_set = set(coverage_by_row)
        missing_rows = sorted(repair_row_set - coverage_row_set)
        extra_rows = sorted(coverage_row_set - repair_row_set)
        if missing_rows:
            errors.append(
                "repair_coverage is missing repair rows: "
                + ", ".join(str(row) for row in missing_rows)
            )
        if extra_rows:
            errors.append(
                "repair_coverage contains unknown repair rows: "
                + ", ".join(str(row) for row in extra_rows)
            )

    for plan in resolved_plans:
        manifest_rows = set(plan.repair_rows)
        covered_rows = plan_rows_from_coverage.get(plan.plan_id, set())
        if manifest_rows != covered_rows:
            errors.append(
                f"plan {plan.plan_id} repair_rows do not match repair_coverage"
            )
        plan_text = plan.path.read_text(encoding="utf-8")
        _validate_plan_markdown(
            plan,
            plan_text,
            anchor_path_text,
            anchor_sha256,
            repair_source_path_text,
            repair_source_sha256,
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
    return RepairPlanValidationResult(
        status=status,
        errors=errors,
        warnings=warnings,
        repair_rows=repair_rows,
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
        result = validate_repair_plan(args.game_repo, args.manifest)
    except RepairPlanningError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(result.status)
    print(f"PLANS: {result.plan_count}")
    print(f"REPAIR_ROWS: {len(result.repair_rows)}")
    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result.status == READY_FOR_EXECUTION else 2


if __name__ == "__main__":
    raise SystemExit(main())
