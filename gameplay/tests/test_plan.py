import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from gameplay.plan import (
    BLOCKED_BY_PLAN_GAP,
    READY_FOR_EXECUTION,
    PlanningError,
    validate_production_plan,
)


class ProductionPlanValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.game_repo = Path(self.temporary_directory.name) / "game"
        self.objective_dir = (
            self.game_repo / "design/gameplay/objective_gameplay/mission.next"
        )
        self.plan_dir = self.objective_dir / "production_plans"
        self.plan_dir.mkdir(parents=True)
        self.objective_relative = (
            "design/gameplay/objective_gameplay/mission.next/OBJECTIVE_GAMEPLAY.md"
        )
        self.manifest_relative = (
            "design/gameplay/objective_gameplay/mission.next/"
            "PRODUCTION_PLAN_MANIFEST.json"
        )
        self.plan_relative = (
            "design/gameplay/objective_gameplay/mission.next/"
            "production_plans/P01_gate.md"
        )
        self.objective_text = """# Objective Gameplay — `mission.next`

| # | Situation | Result |
| --- | --- | --- |
| 1 | Reach a fork. | Pick a route. |
| 2 | Reach the gate. | Open it. |
"""
        (self.objective_dir / "OBJECTIVE_GAMEPLAY.md").write_text(
            self.objective_text, encoding="utf-8"
        )
        self.objective_sha256 = hashlib.sha256(
            self.objective_text.encode("utf-8")
        ).hexdigest()
        (self.game_repo / "game.gd").write_text("func open_gate():\n\tpass\n", encoding="utf-8")
        self._write_plan()
        self._write_manifest()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _plan_text(self, *, status: str = READY_FOR_EXECUTION) -> str:
        return f"""# Production Plan — Gate route

- Plan id: `P01`
- Status: `{status}`
- Source objective: `{self.objective_relative}`
- Source SHA-256: `{self.objective_sha256}`
- Objective rows: `1`

## Source authority
Row 1 defines the route fork.

## Required player-visible result
The player sees and can use both routes.

## Existing repo evidence and reuse
`game.gd` already opens the gate.

## Production changes
Add the fork to `game.gd`.

## Locked constraints and non-goals
Do not add a mission branch.

## Verification
Test both routes independently.

## Dependencies and handoff
No prerequisite plan.
"""

    def _write_plan(self, *, status: str = READY_FOR_EXECUTION) -> None:
        (self.plan_dir / "P01_gate.md").write_text(
            self._plan_text(status=status), encoding="utf-8"
        )

    def _manifest(self) -> dict:
        return {
            "schema_version": "production_plan_manifest.v1",
            "project_id": "sample",
            "objective_id": "mission.next",
            "objective_gameplay_path": self.objective_relative,
            "objective_gameplay_sha256": self.objective_sha256,
            "planning_status": READY_FOR_EXECUTION,
            "plans": [
                {
                    "plan_id": "P01",
                    "path": self.plan_relative,
                    "title": "Gate route",
                    "status": READY_FOR_EXECUTION,
                    "objective_rows": [1],
                    "depends_on": [],
                    "work_types": ["CONTENT_DATA", "TEST"],
                    "existing_repo_refs": ["game.gd"],
                    "planned_paths": ["game.gd"],
                }
            ],
            "row_coverage": [
                {
                    "objective_row": 1,
                    "disposition": "IMPLEMENT",
                    "plan_ids": ["P01"],
                    "rationale": "The fork is not implemented.",
                },
                {
                    "objective_row": 2,
                    "disposition": "NO_CHANGE_REQUIRED",
                    "plan_ids": [],
                    "rationale": "The existing gate behavior already realizes the transport row.",
                },
            ],
            "blocked_gaps": [],
        }

    def _write_manifest(self, payload: dict | None = None) -> None:
        (self.objective_dir / "PRODUCTION_PLAN_MANIFEST.json").write_text(
            json.dumps(payload or self._manifest(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_valid_manifest_and_persisted_plan_are_ready(self) -> None:
        result = validate_production_plan(
            str(self.game_repo), self.manifest_relative
        )
        self.assertEqual(READY_FOR_EXECUTION, result.status)
        self.assertEqual([1, 2], result.objective_rows)
        self.assertEqual(1, result.plan_count)
        self.assertFalse(result.errors)

    def test_absolute_active_manifest_argument_is_allowed(self) -> None:
        result = validate_production_plan(
            str(self.game_repo),
            str(self.objective_dir / "PRODUCTION_PLAN_MANIFEST.json"),
        )
        self.assertEqual(READY_FOR_EXECUTION, result.status)

    def test_explicit_blocked_plan_gap_is_preserved_without_fake_readiness(self) -> None:
        payload = self._manifest()
        payload["planning_status"] = BLOCKED_BY_PLAN_GAP
        payload["blocked_gaps"] = ["The gate target is not specified."]
        payload["plans"][0]["status"] = BLOCKED_BY_PLAN_GAP
        self._write_plan(status=BLOCKED_BY_PLAN_GAP)
        self._write_manifest(payload)
        result = validate_production_plan(
            str(self.game_repo), self.manifest_relative
        )
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertFalse(result.errors)

    def test_missing_objective_row_coverage_fails_closed(self) -> None:
        payload = self._manifest()
        payload["row_coverage"] = payload["row_coverage"][:1]
        self._write_manifest(payload)
        result = validate_production_plan(
            str(self.game_repo), self.manifest_relative
        )
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("missing objective rows: 2" in error for error in result.errors))

    def test_stale_objective_hash_fails_closed(self) -> None:
        (self.objective_dir / "OBJECTIVE_GAMEPLAY.md").write_text(
            self.objective_text + "\nChanged.\n", encoding="utf-8"
        )
        result = validate_production_plan(
            str(self.game_repo), self.manifest_relative
        )
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("does not match" in error for error in result.errors))

    def test_ready_plan_with_tbd_fails_closed(self) -> None:
        plan_path = self.plan_dir / "P01_gate.md"
        plan_path.write_text(
            self._plan_text() + "\nTBD\n", encoding="utf-8"
        )
        result = validate_production_plan(
            str(self.game_repo), self.manifest_relative
        )
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("still contains TBD" in error for error in result.errors))

    def test_plan_metadata_must_match_manifest(self) -> None:
        plan_path = self.plan_dir / "P01_gate.md"
        plan_path.write_text(
            self._plan_text().replace("- Plan id: `P01`", "- Plan id: `P99`"),
            encoding="utf-8",
        )
        result = validate_production_plan(
            str(self.game_repo), self.manifest_relative
        )
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("Plan id does not match" in error for error in result.errors))

    def test_shared_planned_path_is_rejected(self) -> None:
        second_plan_relative = (
            "design/gameplay/objective_gameplay/mission.next/"
            "production_plans/P02_gate.md"
        )
        second_plan = self._plan_text().replace("P01", "P02").replace(
            "- Objective rows: `1`", "- Objective rows: `2`"
        )
        (self.plan_dir / "P02_gate.md").write_text(second_plan, encoding="utf-8")
        payload = self._manifest()
        payload["plans"].append(
            {
                "plan_id": "P02",
                "path": second_plan_relative,
                "title": "Gate verification",
                "status": READY_FOR_EXECUTION,
                "objective_rows": [2],
                "depends_on": [],
                "work_types": ["TEST"],
                "existing_repo_refs": ["game.gd"],
                "planned_paths": ["game.gd"],
            }
        )
        payload["row_coverage"][1] = {
            "objective_row": 2,
            "disposition": "VERIFY_EXISTING",
            "plan_ids": ["P02"],
            "rationale": "The gate behavior needs a regression test.",
        }
        self._write_manifest(payload)
        result = validate_production_plan(
            str(self.game_repo), self.manifest_relative
        )
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("owned by multiple" in error for error in result.errors))

    def test_dependency_cycle_is_rejected(self) -> None:
        second_plan_relative = (
            "design/gameplay/objective_gameplay/mission.next/"
            "production_plans/P02_gate.md"
        )
        second_plan = self._plan_text().replace("P01", "P02").replace(
            "- Objective rows: `1`", "- Objective rows: `2`"
        )
        (self.plan_dir / "P02_gate.md").write_text(second_plan, encoding="utf-8")
        payload = self._manifest()
        payload["plans"][0]["depends_on"] = ["P02"]
        payload["plans"].append(
            {
                "plan_id": "P02",
                "path": second_plan_relative,
                "title": "Gate verification",
                "status": READY_FOR_EXECUTION,
                "objective_rows": [2],
                "depends_on": ["P01"],
                "work_types": ["TEST"],
                "existing_repo_refs": ["game.gd"],
                "planned_paths": ["tests/test_gate.gd"],
            }
        )
        payload["row_coverage"][1] = {
            "objective_row": 2,
            "disposition": "VERIFY_EXISTING",
            "plan_ids": ["P02"],
            "rationale": "The gate behavior needs a regression test.",
        }
        self._write_manifest(payload)
        result = validate_production_plan(
            str(self.game_repo), self.manifest_relative
        )
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("contain a cycle" in error for error in result.errors))

    def test_absolute_persisted_plan_path_is_rejected(self) -> None:
        payload = self._manifest()
        payload["plans"][0]["path"] = str(self.plan_dir / "P01_gate.md")
        self._write_manifest(payload)
        with self.assertRaises(PlanningError):
            validate_production_plan(str(self.game_repo), self.manifest_relative)

    def test_plan_outside_canonical_directory_is_rejected(self) -> None:
        outside_plan = self.objective_dir / "P01_gate.md"
        outside_plan.write_text(self._plan_text(), encoding="utf-8")
        payload = self._manifest()
        payload["plans"][0]["path"] = (
            "design/gameplay/objective_gameplay/mission.next/P01_gate.md"
        )
        self._write_manifest(payload)
        with self.assertRaises(PlanningError):
            validate_production_plan(str(self.game_repo), self.manifest_relative)


if __name__ == "__main__":
    unittest.main()
