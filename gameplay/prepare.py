#!/usr/bin/env python3
"""Compile a game-owned Case 3 objective context before creative authoring.

The tool is deliberately mechanical.  It verifies that the declared primary
progression driver, current/next objective, locale text, runtime wiring, player
actions, and action rewards exist in the target game repo.  It does not invent
gameplay or decide whether an experience is good.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "next_gameplay_unit_input.v1"
READY_FOR_HOW_DESIGN = "READY_FOR_HOW_DESIGN"
READY_FOR_NEW_GAMEPLAY_DESIGN = "READY_FOR_NEW_GAMEPLAY_DESIGN"
BLOCKED_BY_MATERIAL = "BLOCKED_BY_MATERIAL"

FACTORY_ROOT = Path(__file__).resolve().parent.parent


class PreparationError(ValueError):
    """Raised before any output path is created or written."""


@dataclass
class PreparationResult:
    """Validated material state plus the locale text resolved from the repo."""

    status: str
    objective_text: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_game_repo(raw_path: str) -> Path:
    game_repo = Path(raw_path).expanduser().resolve()
    if not game_repo.is_dir():
        raise PreparationError(f"game repo does not exist: {game_repo}")
    if game_repo == FACTORY_ROOT or _is_within(game_repo, FACTORY_ROOT):
        raise PreparationError("game repo must not be this factory repo or a child of it")
    return game_repo


def _resolve_owned_path(
    game_repo: Path,
    raw_path: str,
    *,
    must_exist: bool = False,
) -> Path:
    game_repo = game_repo.resolve()
    candidate = Path(raw_path).expanduser()
    resolved = (candidate if candidate.is_absolute() else game_repo / candidate).resolve()
    if not _is_within(resolved, game_repo):
        raise PreparationError(f"path escapes game repo: {raw_path}")
    if must_exist and not resolved.exists():
        raise PreparationError(f"required path does not exist: {raw_path}")
    return resolved


def _require_text(value: Any, label: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return ""
    return value.strip()


def _validate_evidence_refs(
    game_repo: Path,
    refs: Any,
    label: str,
    errors: list[str],
) -> set[str]:
    roles: set[str] = set()
    if not isinstance(refs, list) or not refs:
        errors.append(f"{label} must contain at least one evidence ref")
        return roles
    for ref_index, ref in enumerate(refs):
        ref_label = f"{label}[{ref_index}]"
        if not isinstance(ref, dict):
            errors.append(f"{ref_label} must be an object")
            continue
        role = _require_text(ref.get("role"), f"{ref_label}.role", errors)
        path_text = _require_text(ref.get("path"), f"{ref_label}.path", errors)
        contains = ref.get("contains")
        if not isinstance(contains, list) or not contains:
            errors.append(f"{ref_label}.contains must be a non-empty array")
            contains = []
        if role:
            roles.add(role)
        if not path_text:
            continue
        try:
            evidence_path = _resolve_owned_path(game_repo, path_text, must_exist=True)
        except PreparationError as error:
            errors.append(str(error))
            continue
        if not evidence_path.is_file():
            errors.append(f"evidence ref is not a file: {path_text}")
            continue
        try:
            evidence_text = evidence_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"evidence ref is not UTF-8 text: {path_text}")
            continue
        for token_index, token in enumerate(contains):
            if not isinstance(token, str) or not token:
                errors.append(f"{ref_label}.contains[{token_index}] must be text")
            elif token not in evidence_text:
                errors.append(f"evidence token not found in {path_text}: {token}")
    return roles


def _read_locale_text(
    game_repo: Path,
    locale_spec: Any,
    errors: list[str],
) -> str:
    if not isinstance(locale_spec, dict):
        errors.append("frontier.objective_locale must be an object")
        return ""
    path_text = _require_text(locale_spec.get("path"), "objective_locale.path", errors)
    key_column = _require_text(
        locale_spec.get("key_column"), "objective_locale.key_column", errors
    )
    locale_column = _require_text(
        locale_spec.get("locale_column"), "objective_locale.locale_column", errors
    )
    locale_key = _require_text(locale_spec.get("key"), "objective_locale.key", errors)
    if not all((path_text, key_column, locale_column, locale_key)):
        return ""
    try:
        locale_path = _resolve_owned_path(game_repo, path_text, must_exist=True)
    except PreparationError as error:
        errors.append(str(error))
        return ""
    try:
        with locale_path.open(encoding="utf-8-sig", newline="") as locale_file:
            reader = csv.DictReader(locale_file)
            if reader.fieldnames is None:
                errors.append(f"locale CSV has no header: {path_text}")
                return ""
            for required_column in (key_column, locale_column):
                if required_column not in reader.fieldnames:
                    errors.append(
                        f"locale CSV {path_text} lacks column: {required_column}"
                    )
            matching_rows = [
                row for row in reader if str(row.get(key_column, "")).strip() == locale_key
            ]
    except (OSError, csv.Error) as error:
        errors.append(f"cannot read locale CSV {path_text}: {error}")
        return ""
    if len(matching_rows) != 1:
        errors.append(
            f"locale key must occur exactly once in {path_text}: {locale_key} "
            f"(found {len(matching_rows)})"
        )
        return ""
    objective_text = str(matching_rows[0].get(locale_column, "")).strip()
    if not objective_text:
        errors.append(f"locale value is blank for {locale_key} in {locale_column}")
    expected_text = locale_spec.get("expected_text")
    if isinstance(expected_text, str) and expected_text and objective_text != expected_text:
        errors.append(
            f"locale value changed for {locale_key}: expected {expected_text!r}, "
            f"found {objective_text!r}"
        )
    return objective_text


def validate_materials(payload: Any, game_repo: Path) -> PreparationResult:
    """Validate one game-owned Step 1 declaration without writing anything."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return PreparationResult(BLOCKED_BY_MATERIAL, errors=["input must be an object"])
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    _require_text(payload.get("project_id"), "project_id", errors)

    driver = payload.get("primary_progression_driver")
    if not isinstance(driver, dict):
        errors.append("primary_progression_driver must be an object")
        driver = {}
    for field_name in ("system_id", "system_kind", "progression_unit", "description"):
        _require_text(
            driver.get(field_name), f"primary_progression_driver.{field_name}", errors
        )
    driver_roles = _validate_evidence_refs(
        game_repo,
        driver.get("evidence_refs"),
        "primary_progression_driver.evidence_refs",
        errors,
    )
    if "progression_authority" not in driver_roles:
        errors.append("progression driver requires a progression_authority evidence ref")

    frontier = payload.get("frontier")
    if not isinstance(frontier, dict):
        errors.append("frontier must be an object")
        frontier = {}
    decision = _require_text(frontier.get("decision"), "frontier.decision", errors)
    if decision and decision not in {"COMPLETE_CURRENT_UNIT", "ADVANCE_TO_NEXT_UNIT"}:
        errors.append("frontier.decision has an unsupported value")
    for field_name in (
        "current_state",
        "objective_id",
        "completion_condition",
    ):
        _require_text(frontier.get(field_name), f"frontier.{field_name}", errors)
    objective_text = _read_locale_text(
        game_repo, frontier.get("objective_locale"), errors
    )
    frontier_roles = _validate_evidence_refs(
        game_repo,
        frontier.get("evidence_refs"),
        "frontier.evidence_refs",
        errors,
    )
    for required_role in ("runtime_selection", "runtime_completion"):
        if required_role not in frontier_roles:
            errors.append(f"frontier requires a {required_role} evidence ref")

    successor = frontier.get("successor_handoff")
    if not isinstance(successor, dict):
        errors.append("frontier.successor_handoff must be an object")
    else:
        successor_status = _require_text(
            successor.get("status"), "successor_handoff.status", errors
        )
        _require_text(
            successor.get("description"), "successor_handoff.description", errors
        )
        if successor_status not in {"WIRED", "MISSING", "UNKNOWN"}:
            errors.append("successor_handoff.status has an unsupported value")
        if successor_status != "WIRED":
            warnings.append(
                "the objective can be designed, but its post-completion successor "
                "is not proven wired"
            )

    player_actions = payload.get("player_actions")
    if not isinstance(player_actions, list):
        errors.append("player_actions must be an array")
        player_actions = []
    seen_action_ids: set[str] = set()
    for action_index, action in enumerate(player_actions):
        action_label = f"player_actions[{action_index}]"
        if not isinstance(action, dict):
            errors.append(f"{action_label} must be an object")
            continue
        action_id = _require_text(action.get("action_id"), f"{action_label}.action_id", errors)
        _require_text(action.get("description"), f"{action_label}.description", errors)
        _require_text(action.get("availability"), f"{action_label}.availability", errors)
        if action_id in seen_action_ids:
            errors.append(f"duplicate action_id: {action_id}")
        seen_action_ids.add(action_id)
        rewards = action.get("rewards")
        if not isinstance(rewards, list) or not rewards:
            errors.append(f"{action_label}.rewards must contain at least one reward")
        else:
            for reward_index, reward in enumerate(rewards):
                reward_label = f"{action_label}.rewards[{reward_index}]"
                if not isinstance(reward, dict):
                    errors.append(f"{reward_label} must be an object")
                    continue
                for field_name in ("reward_id", "kind", "description"):
                    _require_text(
                        reward.get(field_name), f"{reward_label}.{field_name}", errors
                    )
        action_roles = _validate_evidence_refs(
            game_repo,
            action.get("evidence_refs"),
            f"{action_label}.evidence_refs",
            errors,
        )
        if "runtime_action" not in action_roles:
            errors.append(f"{action_label} requires a runtime_action evidence ref")

    for list_field in ("recent_patterns", "design_constraints"):
        field_value = payload.get(list_field, [])
        if not isinstance(field_value, list) or any(
            not isinstance(item, str) or not item.strip() for item in field_value
        ):
            errors.append(f"{list_field} must be an array of non-empty strings")

    if errors:
        status = BLOCKED_BY_MATERIAL
    elif player_actions:
        status = READY_FOR_HOW_DESIGN
    else:
        status = READY_FOR_NEW_GAMEPLAY_DESIGN
    return PreparationResult(
        status=status,
        objective_text=objective_text,
        errors=errors,
        warnings=warnings,
    )


def _join_text(items: Iterable[str]) -> str:
    return "<br>".join(str(item).strip() for item in items if str(item).strip()) or "—"


def render_context(payload: dict[str, Any], result: PreparationResult) -> str:
    """Render the compact context that the Step 2 author is allowed to read."""

    driver = payload.get("primary_progression_driver", {})
    frontier = payload.get("frontier", {})
    successor = frontier.get("successor_handoff", {})
    lines = [
        "# Next Gameplay Unit Context",
        "",
        f"- Status: `{result.status}`",
        f"- Project: `{payload.get('project_id', '')}`",
        f"- Progression driver: `{driver.get('system_id', '')}` "
        f"(`{driver.get('progression_unit', '')}`)",
        f"- Frontier decision: `{frontier.get('decision', '')}`",
        "",
        "## Next objective",
        "",
        f"- Objective id: `{frontier.get('objective_id', '')}`",
        f"- Player-facing text: {result.objective_text or '—'}",
        f"- Current state: {frontier.get('current_state', '')}",
        f"- Completion condition: {frontier.get('completion_condition', '')}",
        f"- Successor handoff: `{successor.get('status', '')}` — "
        f"{successor.get('description', '')}",
        "",
        "## Player actions and rewards",
        "",
        "| Action | Available when | Rewards / consequences | Exact source refs |",
        "| --- | --- | --- | --- |",
    ]
    for action in payload.get("player_actions", []):
        rewards = [
            f"**{reward.get('kind', '')}:** {reward.get('description', '')}"
            for reward in action.get("rewards", [])
        ]
        source_paths = list(
            dict.fromkeys(
                str(ref.get("path", ""))
                for ref in action.get("evidence_refs", [])
                if isinstance(ref, dict) and str(ref.get("path", "")).strip()
            )
        )
        lines.append(
            f"| `{action.get('action_id', '')}` — {action.get('description', '')} "
            f"| {action.get('availability', '')} | {_join_text(rewards)} "
            f"| {_join_text(source_paths)} |"
        )
    if not payload.get("player_actions"):
        lines.append(
            "| — | No proven applicable action | New gameplay design is required | — |"
        )

    lines.extend(["", "## Recent patterns to avoid repeating", ""])
    recent_patterns = payload.get("recent_patterns", [])
    lines.extend(f"- {pattern}" for pattern in recent_patterns)
    if not recent_patterns:
        lines.append("- None recorded.")

    lines.extend(["", "## Design constraints", ""])
    constraints = payload.get("design_constraints", [])
    lines.extend(f"- {constraint}" for constraint in constraints)
    if not constraints:
        lines.append("- None recorded.")

    if result.warnings:
        lines.extend(["", "## Material warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.errors:
        lines.extend(["", "## Blocking material errors", ""])
        lines.extend(f"- {error}" for error in result.errors)
    lines.extend(
        [
            "",
            "## Step 2 boundary",
            "",
            "Use this context to author one complete `OBJECTIVE_GAMEPLAY.md` from "
            "objective issue/current frontier through objective completion. Do not "
            "re-scan the whole repo or turn internal causal micro-steps into separate "
            "worker artifacts.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PreparationError(f"cannot read {label} JSON: {error}") from error
    if not isinstance(payload, dict):
        raise PreparationError(f"{label} JSON must contain an object")
    return payload


def _compile_unit_payload(
    game_repo: Path,
    unit_input: dict[str, Any],
) -> dict[str, Any]:
    """Merge one small frontier request with the stable project model.

    Inline full payloads remain accepted for early fixtures, but real game repos
    should use ``project_model_path`` so progression/actions/rewards are not
    copied into every objective directory.
    """

    project_model_path_text = unit_input.get("project_model_path")
    if not isinstance(project_model_path_text, str) or not project_model_path_text.strip():
        return unit_input
    project_model_path = _resolve_owned_path(
        game_repo, project_model_path_text, must_exist=True
    )
    project_model = _load_json_object(project_model_path, "project model")
    if project_model.get("schema_version") != "gameplay_design_model.v1":
        raise PreparationError(
            "project model schema_version must be gameplay_design_model.v1"
        )
    request_project_id = unit_input.get("project_id")
    if request_project_id != project_model.get("project_id"):
        raise PreparationError("unit input project_id does not match project model")

    all_actions = project_model.get("player_actions", [])
    if not isinstance(all_actions, list):
        raise PreparationError("project model player_actions must be an array")
    actions_by_id = {
        action.get("action_id"): action
        for action in all_actions
        if isinstance(action, dict) and isinstance(action.get("action_id"), str)
    }
    applicable_action_ids = unit_input.get("applicable_action_ids")
    if not isinstance(applicable_action_ids, list) or any(
        not isinstance(action_id, str) or not action_id.strip()
        for action_id in applicable_action_ids
    ):
        raise PreparationError("applicable_action_ids must be an array of action ids")
    missing_action_ids = [
        action_id for action_id in applicable_action_ids if action_id not in actions_by_id
    ]
    if missing_action_ids:
        raise PreparationError(
            "applicable action ids are absent from project model: "
            + ", ".join(missing_action_ids)
        )

    request_patterns = unit_input.get("recent_patterns", [])
    request_constraints = unit_input.get("design_constraints", [])
    if not isinstance(request_patterns, list) or not isinstance(request_constraints, list):
        raise PreparationError("unit recent_patterns/design_constraints must be arrays")
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_model.get("project_id"),
        "primary_progression_driver": project_model.get(
            "primary_progression_driver"
        ),
        "frontier": unit_input.get("frontier"),
        "player_actions": [actions_by_id[action_id] for action_id in applicable_action_ids],
        "recent_patterns": project_model.get("recent_patterns", []) + request_patterns,
        "design_constraints": project_model.get("design_constraints", [])
        + request_constraints,
    }


def prepare_context(game_repo_text: str, input_text: str, output_text: str) -> PreparationResult:
    """Resolve ownership, validate materials, then and only then write output."""

    game_repo = _resolve_game_repo(game_repo_text)
    input_path = _resolve_owned_path(game_repo, input_text, must_exist=True)
    output_path = _resolve_owned_path(game_repo, output_text)
    if not input_path.is_file():
        raise PreparationError(f"input is not a file: {input_text}")
    unit_input = _load_json_object(input_path, "input")
    payload = _compile_unit_payload(game_repo, unit_input)
    result = validate_materials(payload, game_repo)
    rendered = render_context(payload if isinstance(payload, dict) else {}, result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["context"])
    parser.add_argument("--game-repo", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = prepare_context(args.game_repo, args.input, args.out)
    except PreparationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(result.status)
    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result.status != BLOCKED_BY_MATERIAL else 2


if __name__ == "__main__":
    raise SystemExit(main())
