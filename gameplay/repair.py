#!/usr/bin/env python3
"""Prepare one compact Case 3 gameplay-gap repair context.

This is the repair-side counterpart to ``prepare.py context``.  It does not
advance the primary progression driver and it does not rediscover the whole
game.  It binds one evidenced gameplay gap to an exact existing
OBJECTIVE_GAMEPLAY.md revision, selects only the affected stable actions, and
routes the gap either directly to production planning or through one small
repair-design artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "gameplay_gap_input.v1"
MODEL_SCHEMA_VERSION = "gameplay_design_model.v1"

READY_FOR_DIRECT_REPAIR_PLAN = "READY_FOR_DIRECT_REPAIR_PLAN"
READY_FOR_REPAIR_DESIGN = "READY_FOR_REPAIR_DESIGN"
BLOCKED_BY_REPAIR_MATERIAL = "BLOCKED_BY_REPAIR_MATERIAL"

AUTHORITY_STATES = {
    "EXPLICIT_REQUIREMENT",
    "USER_RULING",
    "OMITTED_OR_AMBIGUOUS",
    "CONFLICTS_WITH_LOCKED_DESIGN",
}
GAP_STATUSES = {
    "OPEN",
    "IMPLEMENTED_PENDING_ACCEPTANCE",
    "CLOSED",
    "DEFERRED",
}
GAP_EVIDENCE_ROLES = {
    "runtime_observation",
    "implementation_state",
    "test_failure",
}

FACTORY_ROOT = Path(__file__).resolve().parent.parent
_OBJECTIVE_ROW_PATTERN = re.compile(r"^\|\s*(\d+)\s*\|")


class RepairPreparationError(ValueError):
    """Raised before any output path is created or written."""


@dataclass
class RepairPreparationResult:
    """Validated repair material state."""

    status: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    objective_rows: list[int] = field(default_factory=list)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_game_repo(raw_path: str) -> Path:
    game_repo = Path(raw_path).expanduser().resolve()
    if not game_repo.is_dir():
        raise RepairPreparationError(f"game repo does not exist: {game_repo}")
    if game_repo == FACTORY_ROOT or _is_within(game_repo, FACTORY_ROOT):
        raise RepairPreparationError(
            "game repo must not be this factory repo or a child of it"
        )
    return game_repo


def _resolve_cli_owned_path(
    game_repo: Path,
    raw_path: str,
    *,
    must_exist: bool = False,
) -> Path:
    candidate = Path(raw_path).expanduser()
    resolved = (candidate if candidate.is_absolute() else game_repo / candidate).resolve()
    if not _is_within(resolved, game_repo):
        raise RepairPreparationError(f"path escapes game repo: {raw_path}")
    if must_exist and not resolved.exists():
        raise RepairPreparationError(f"required path does not exist: {raw_path}")
    return resolved


def _resolve_persisted_owned_path(
    game_repo: Path,
    raw_path: Any,
    *,
    must_exist: bool = False,
) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise RepairPreparationError("persisted paths must be non-empty strings")
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        raise RepairPreparationError(
            f"persisted path must be game-repo-relative: {raw_path}"
        )
    return _resolve_cli_owned_path(game_repo, raw_path, must_exist=must_exist)


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RepairPreparationError(f"cannot read {label} JSON: {error}") from error
    if not isinstance(payload, dict):
        raise RepairPreparationError(f"{label} JSON must contain an object")
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
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        text = _require_text(item, f"{label}[{index}]", errors)
        if text:
            result.append(text)
    if len(result) != len(set(result)):
        errors.append(f"{label} must not contain duplicates")
    return result


def _validate_evidence_refs(
    game_repo: Path,
    refs: Any,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> set[str]:
    roles: set[str] = set()
    if not isinstance(refs, list) or (not refs and not allow_empty):
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
            evidence_path = _resolve_persisted_owned_path(
                game_repo, path_text, must_exist=True
            )
        except RepairPreparationError as error:
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


def _extract_objective_rows(objective_text: str, errors: list[str]) -> list[int]:
    rows: list[int] = []
    for line in objective_text.splitlines():
        match = _OBJECTIVE_ROW_PATTERN.match(line)
        if match:
            rows.append(int(match.group(1)))
    if not rows:
        errors.append("anchor OBJECTIVE_GAMEPLAY.md contains no numbered gameplay rows")
        return []
    if len(rows) != len(set(rows)):
        errors.append("anchor OBJECTIVE_GAMEPLAY.md contains duplicate row numbers")
    if rows != sorted(rows):
        errors.append("anchor OBJECTIVE_GAMEPLAY.md rows must be in ascending order")
    return rows


def _compile_gap_payload(
    game_repo: Path,
    gap_input: dict[str, Any],
) -> dict[str, Any]:
    project_model_path = _resolve_persisted_owned_path(
        game_repo, gap_input.get("project_model_path"), must_exist=True
    )
    project_model = _load_json_object(project_model_path, "project model")
    if project_model.get("schema_version") != MODEL_SCHEMA_VERSION:
        raise RepairPreparationError(
            f"project model schema_version must be {MODEL_SCHEMA_VERSION}"
        )
    if gap_input.get("project_id") != project_model.get("project_id"):
        raise RepairPreparationError(
            "gap input project_id does not match project model"
        )

    all_actions = project_model.get("player_actions")
    if not isinstance(all_actions, list):
        raise RepairPreparationError("project model player_actions must be an array")
    actions_by_id = {
        action.get("action_id"): action
        for action in all_actions
        if isinstance(action, dict) and isinstance(action.get("action_id"), str)
    }
    affected_action_ids = gap_input.get("affected_action_ids")
    if not isinstance(affected_action_ids, list) or any(
        not isinstance(action_id, str) or not action_id.strip()
        for action_id in affected_action_ids
    ):
        raise RepairPreparationError(
            "affected_action_ids must be an array of action ids"
        )
    if len(affected_action_ids) != len(set(affected_action_ids)):
        raise RepairPreparationError("affected_action_ids must not contain duplicates")
    missing_action_ids = [
        action_id for action_id in affected_action_ids if action_id not in actions_by_id
    ]
    if missing_action_ids:
        raise RepairPreparationError(
            "affected action ids are absent from project model: "
            + ", ".join(missing_action_ids)
        )

    preserve = gap_input.get("preserve", [])
    user_rulings = gap_input.get("user_rulings", [])
    if not isinstance(preserve, list) or not isinstance(user_rulings, list):
        raise RepairPreparationError("preserve and user_rulings must be arrays")
    model_patterns = project_model.get("recent_patterns", [])
    model_constraints = project_model.get("design_constraints", [])
    if not isinstance(model_patterns, list) or not isinstance(model_constraints, list):
        raise RepairPreparationError(
            "project model recent_patterns/design_constraints must be arrays"
        )

    return {
        "schema_version": gap_input.get("schema_version"),
        "project_id": gap_input.get("project_id"),
        "gap_status": gap_input.get("gap_status"),
        "anchor": gap_input.get("anchor"),
        "gap": gap_input.get("gap"),
        "authority": gap_input.get("authority"),
        "player_actions": [actions_by_id[action_id] for action_id in affected_action_ids],
        "recent_patterns": model_patterns,
        "design_constraints": model_constraints,
        "preserve": preserve,
        "user_rulings": user_rulings,
    }


def validate_repair_materials(
    payload: Any,
    game_repo: Path,
) -> RepairPreparationResult:
    """Validate one compiled repair request without writing anything."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return RepairPreparationResult(
            BLOCKED_BY_REPAIR_MATERIAL, errors=["input must be an object"]
        )
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    _require_text(payload.get("project_id"), "project_id", errors)
    gap_status = _require_text(payload.get("gap_status"), "gap_status", errors)
    if gap_status and gap_status not in GAP_STATUSES:
        errors.append("gap_status has an unsupported value")
    elif gap_status and gap_status != "OPEN":
        errors.append(
            f"gap_status is {gap_status}; only an OPEN gap may enter repair "
            "preparation"
        )

    anchor = payload.get("anchor")
    if not isinstance(anchor, dict):
        errors.append("anchor must be an object")
        anchor = {}
    objective_id = _require_text(
        anchor.get("objective_id"), "anchor.objective_id", errors
    )
    objective_path_text = _require_text(
        anchor.get("objective_gameplay_path"),
        "anchor.objective_gameplay_path",
        errors,
    )
    declared_objective_sha256 = _require_text(
        anchor.get("objective_gameplay_sha256"),
        "anchor.objective_gameplay_sha256",
        errors,
    )
    affected_rows = anchor.get("affected_rows")
    if not isinstance(affected_rows, list) or not affected_rows:
        errors.append("anchor.affected_rows must contain at least one row")
        affected_rows = []
    valid_affected_rows: list[int] = []
    for index, row in enumerate(affected_rows):
        if not isinstance(row, int) or isinstance(row, bool) or row < 1:
            errors.append(f"anchor.affected_rows[{index}] must be a positive integer")
        else:
            valid_affected_rows.append(row)
    if len(valid_affected_rows) != len(set(valid_affected_rows)):
        errors.append("anchor.affected_rows must not contain duplicates")

    objective_rows: list[int] = []
    if objective_path_text:
        try:
            objective_path = _resolve_persisted_owned_path(
                game_repo, objective_path_text, must_exist=True
            )
        except RepairPreparationError as error:
            errors.append(str(error))
        else:
            canonical_objective_root = (
                game_repo / "design/gameplay/objective_gameplay"
            ).resolve()
            if (
                objective_path.name != "OBJECTIVE_GAMEPLAY.md"
                or not _is_within(objective_path, canonical_objective_root)
            ):
                errors.append(
                    "anchor objective must be a canonical "
                    "design/gameplay/objective_gameplay/**/OBJECTIVE_GAMEPLAY.md"
                )
            if not objective_path.is_file():
                errors.append(
                    f"anchor objective gameplay is not a file: {objective_path_text}"
                )
            else:
                try:
                    objective_text = objective_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    errors.append(
                        f"anchor objective gameplay is not UTF-8: {objective_path_text}"
                    )
                    objective_text = ""
                if objective_text:
                    objective_rows = _extract_objective_rows(objective_text, errors)
                    objective_sha256 = hashlib.sha256(
                        objective_text.encode("utf-8")
                    ).hexdigest()
                    if not re.fullmatch(
                        r"[0-9a-f]{64}", declared_objective_sha256
                    ):
                        errors.append(
                            "anchor.objective_gameplay_sha256 must be 64 lowercase "
                            "hex characters"
                        )
                    elif declared_objective_sha256 != objective_sha256:
                        errors.append(
                            "anchor objective SHA-256 does not match "
                            "OBJECTIVE_GAMEPLAY.md"
                        )
                    if objective_id and objective_id not in objective_text:
                        errors.append(
                            "anchor.objective_id is not present in "
                            "OBJECTIVE_GAMEPLAY.md"
                        )
                    unknown_rows = sorted(
                        set(valid_affected_rows) - set(objective_rows)
                    )
                    if unknown_rows:
                        errors.append(
                            "anchor.affected_rows contains unknown objective rows: "
                            + ", ".join(str(row) for row in unknown_rows)
                        )

    gap = payload.get("gap")
    if not isinstance(gap, dict):
        errors.append("gap must be an object")
        gap = {}
    gap_id = _require_text(gap.get("gap_id"), "gap.gap_id", errors)
    if gap_id and not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", gap_id):
        errors.append(
            "gap.gap_id must be a portable lowercase path component "
            "([a-z0-9._-])"
        )
    for field_name in (
        "summary",
        "progression_window",
        "observed_break",
        "player_visible_contradiction",
    ):
        _require_text(gap.get(field_name), f"gap.{field_name}", errors)
    gap_roles = _validate_evidence_refs(
        game_repo, gap.get("evidence_refs"), "gap.evidence_refs", errors
    )
    if not gap_roles.intersection(GAP_EVIDENCE_ROLES):
        errors.append(
            "gap evidence requires at least one runtime_observation, "
            "implementation_state, or test_failure ref"
        )

    authority = payload.get("authority")
    if not isinstance(authority, dict):
        errors.append("authority must be an object")
        authority = {}
    authority_state = _require_text(
        authority.get("state"), "authority.state", errors
    )
    if authority_state and authority_state not in AUTHORITY_STATES:
        errors.append("authority.state has an unsupported value")
    requirement = authority.get("required_player_visible_result")
    authority_roles = _validate_evidence_refs(
        game_repo,
        authority.get("evidence_refs", []),
        "authority.evidence_refs",
        errors,
        allow_empty=True,
    )
    user_rulings = _require_string_list(
        payload.get("user_rulings", []), "user_rulings", errors
    )
    if authority_state == "EXPLICIT_REQUIREMENT":
        _require_text(
            requirement, "authority.required_player_visible_result", errors
        )
        if "design_authority" not in authority_roles:
            errors.append(
                "EXPLICIT_REQUIREMENT requires a design_authority evidence ref"
            )
    elif authority_state == "USER_RULING":
        _require_text(
            requirement, "authority.required_player_visible_result", errors
        )
        if not user_rulings:
            errors.append("USER_RULING requires at least one persisted user ruling")
    elif authority_state == "OMITTED_OR_AMBIGUOUS":
        if isinstance(requirement, str) and requirement.strip():
            warnings.append(
                "omitted/ambiguous authority includes a proposed result; Step 2 "
                "must treat it as a hypothesis, not locked design"
            )
    elif authority_state == "CONFLICTS_WITH_LOCKED_DESIGN":
        errors.append(
            "gap conflicts with locked design; obtain a user ruling or revise the "
            "base authority before repair planning"
        )

    actions = payload.get("player_actions")
    if not isinstance(actions, list):
        errors.append("player_actions must be an array")
        actions = []
    seen_action_ids: set[str] = set()
    for action_index, action in enumerate(actions):
        label = f"player_actions[{action_index}]"
        if not isinstance(action, dict):
            errors.append(f"{label} must be an object")
            continue
        action_id = _require_text(action.get("action_id"), f"{label}.action_id", errors)
        _require_text(action.get("description"), f"{label}.description", errors)
        _require_text(action.get("availability"), f"{label}.availability", errors)
        if action_id in seen_action_ids:
            errors.append(f"duplicate action_id: {action_id}")
        seen_action_ids.add(action_id)
        rewards = action.get("rewards")
        if not isinstance(rewards, list) or not rewards:
            errors.append(f"{label}.rewards must contain at least one reward")
        else:
            for reward_index, reward in enumerate(rewards):
                reward_label = f"{label}.rewards[{reward_index}]"
                if not isinstance(reward, dict):
                    errors.append(f"{reward_label} must be an object")
                    continue
                for field_name in ("reward_id", "kind", "description"):
                    _require_text(
                        reward.get(field_name),
                        f"{reward_label}.{field_name}",
                        errors,
                    )
        action_roles = _validate_evidence_refs(
            game_repo,
            action.get("evidence_refs"),
            f"{label}.evidence_refs",
            errors,
        )
        if "runtime_action" not in action_roles:
            errors.append(f"{label} requires a runtime_action evidence ref")
    if not actions:
        warnings.append(
            "no stable player action is affected; keep the repair scoped to the "
            "player-visible contract rather than inventing a new system by default"
        )

    for list_field in ("recent_patterns", "design_constraints", "preserve"):
        _require_string_list(payload.get(list_field, []), list_field, errors)

    if errors:
        status = BLOCKED_BY_REPAIR_MATERIAL
    elif authority_state in {"EXPLICIT_REQUIREMENT", "USER_RULING"}:
        status = READY_FOR_DIRECT_REPAIR_PLAN
    else:
        status = READY_FOR_REPAIR_DESIGN
    return RepairPreparationResult(
        status=status,
        errors=errors,
        warnings=warnings,
        objective_rows=objective_rows,
    )


def _join_text(items: Iterable[str]) -> str:
    return "<br>".join(str(item).strip() for item in items if str(item).strip()) or "—"


def render_repair_context(
    payload: dict[str, Any],
    result: RepairPreparationResult,
) -> str:
    """Render the bounded input for repair design or direct repair planning."""

    anchor = payload.get("anchor", {})
    gap = payload.get("gap", {})
    authority = payload.get("authority", {})
    lines = [
        f"# Gameplay Repair Context — `{gap.get('gap_id', '')}`",
        "",
        f"- Status: `{result.status}`",
        f"- Gap lifecycle: `{payload.get('gap_status', '')}`",
        f"- Project: `{payload.get('project_id', '')}`",
        f"- Anchor objective id: `{anchor.get('objective_id', '')}`",
        f"- Anchor objective: `{anchor.get('objective_gameplay_path', '')}`",
        f"- Anchor SHA-256: `{anchor.get('objective_gameplay_sha256', '')}`",
        f"- Affected objective rows: "
        f"`{', '.join(str(row) for row in anchor.get('affected_rows', []))}`",
        "",
        "## Known gap",
        "",
        f"- Summary: {gap.get('summary', '')}",
        f"- Progression window: {gap.get('progression_window', '')}",
        f"- Observed break: {gap.get('observed_break', '')}",
        f"- Player-visible contradiction: "
        f"{gap.get('player_visible_contradiction', '')}",
        "",
        "### Exact gap evidence",
        "",
    ]
    for ref in gap.get("evidence_refs", []):
        if not isinstance(ref, dict):
            continue
        lines.append(
            f"- `{ref.get('role', '')}` — `{ref.get('path', '')}` — "
            f"{_join_text(ref.get('contains', []))}"
        )

    lines.extend(
        [
            "",
            "## Design authority state",
            "",
            f"- State: `{authority.get('state', '')}`",
            "- Required player-visible result: "
            + (
                str(authority.get("required_player_visible_result", "")).strip()
                or "Not yet decided."
            ),
        ]
    )
    for ref in authority.get("evidence_refs", []):
        if not isinstance(ref, dict):
            continue
        lines.append(
            f"- Authority ref: `{ref.get('path', '')}` — "
            f"{_join_text(ref.get('contains', []))}"
        )

    user_rulings = payload.get("user_rulings", [])
    lines.extend(["", "## User rulings", ""])
    lines.extend(f"- {ruling}" for ruling in user_rulings)
    if not user_rulings:
        lines.append("- None persisted.")

    lines.extend(
        [
            "",
            "## Affected player actions and rewards",
            "",
            "| Action | Available when | Rewards / consequences | Exact source refs |",
            "| --- | --- | --- | --- |",
        ]
    )
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
        lines.append("| — | — | No stable affected action declared | — |")

    lines.extend(["", "## Preserve", ""])
    preserved = (
        payload.get("design_constraints", [])
        + payload.get("preserve", [])
    )
    lines.extend(f"- {constraint}" for constraint in preserved)
    if not preserved:
        lines.append("- No additional constraint recorded.")

    lines.extend(["", "## Recent patterns to avoid repeating", ""])
    patterns = payload.get("recent_patterns", [])
    lines.extend(f"- {pattern}" for pattern in patterns)
    if not patterns:
        lines.append("- None recorded.")

    if result.warnings:
        lines.extend(["", "## Material warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.errors:
        lines.extend(["", "## Blocking material errors", ""])
        lines.extend(f"- {error}" for error in result.errors)

    if result.status == READY_FOR_DIRECT_REPAIR_PLAN:
        lines.extend(
            [
                "",
                "## Repair rows",
                "",
                "| # | Broken causal contract | Required player-visible closure | "
                "Preserve | Verification boundary |",
                "| --- | --- | --- | --- | --- |",
                f"| 1 | {gap.get('player_visible_contradiction', '')} "
                f"| {authority.get('required_player_visible_result', '')} "
                f"| {_join_text(preserved)} "
                "| Prove the required behavior in the anchored progression window; "
                "tests do not self-award experience acceptance. |",
                "",
                "## Next boundary",
                "",
                "The design requirement is already authoritative. Use this exact "
                "context as the repair planning source; do not spend a creative "
                "author or rewrite the base `OBJECTIVE_GAMEPLAY.md`.",
            ]
        )
    elif result.status == READY_FOR_REPAIR_DESIGN:
        lines.extend(
            [
                "",
                "## Next boundary",
                "",
                "One bounded repair author writes `GAMEPLAY_REPAIR.md`. Resolve only "
                "this broken causal contract, preserve the base objective, and use "
                "the smallest sufficient escalation: clarify an affordance, restore "
                "an existing action/consequence, recompose existing actions, then "
                "add a new action/system only if those cannot close the gap.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Next boundary",
                "",
                "Stop. Do not author or plan a repair until the listed material or "
                "authority conflict is resolved.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def prepare_repair_context(
    game_repo_text: str,
    input_text: str,
    output_text: str,
) -> RepairPreparationResult:
    """Resolve all ownership, validate, then and only then create the context."""

    game_repo = _resolve_game_repo(game_repo_text)
    input_path = _resolve_cli_owned_path(game_repo, input_text, must_exist=True)
    output_path = _resolve_cli_owned_path(game_repo, output_text)
    if not input_path.is_file():
        raise RepairPreparationError(f"input is not a file: {input_text}")
    gap_input = _load_json_object(input_path, "gap input")
    payload = _compile_gap_payload(game_repo, gap_input)
    result = validate_repair_materials(payload, game_repo)

    gap = payload.get("gap", {})
    gap_id = gap.get("gap_id") if isinstance(gap, dict) else None
    if not isinstance(gap_id, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9._-]*", gap_id
    ):
        raise RepairPreparationError(
            "gap.gap_id must be known and portable before resolving canonical paths"
        )
    canonical_repair_directory = (
        game_repo / "design/gameplay/repairs" / gap_id
    ).resolve()
    if input_path != canonical_repair_directory / "GAMEPLAY_GAP_INPUT.json":
        raise RepairPreparationError(
            "gap input must be design/gameplay/repairs/<gap_id>/"
            "GAMEPLAY_GAP_INPUT.json"
        )
    if output_path != canonical_repair_directory / "GAMEPLAY_REPAIR_CONTEXT.md":
        raise RepairPreparationError(
            "repair context output must be design/gameplay/repairs/<gap_id>/"
            "GAMEPLAY_REPAIR_CONTEXT.md"
        )

    rendered = render_repair_context(payload, result)
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
        result = prepare_repair_context(args.game_repo, args.input, args.out)
    except RepairPreparationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(result.status)
    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result.status != BLOCKED_BY_REPAIR_MATERIAL else 2


if __name__ == "__main__":
    raise SystemExit(main())
