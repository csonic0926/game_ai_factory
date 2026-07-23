import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from gameplay.repair_plan import (
    BLOCKED_BY_PLAN_GAP,
    READY_FOR_EXECUTION,
    RepairPlanningError,
    validate_repair_plan,
)


class RepairPlanValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.game_repo = Path(self.temporary_directory.name) / "game"
        self.objective_dir = (
            self.game_repo / "design/gameplay/objective_gameplay/mission.next"
        )
        self.repair_dir = (
            self.game_repo / "design/gameplay/repairs/return_fire_unusable"
        )
        self.plan_dir = self.repair_dir / "production_plans"
        self.objective_dir.mkdir(parents=True)
        self.plan_dir.mkdir(parents=True)

        self.objective_relative = (
            "design/gameplay/objective_gameplay/mission.next/OBJECTIVE_GAMEPLAY.md"
        )
        self.repair_relative = (
            "design/gameplay/repairs/return_fire_unusable/GAMEPLAY_REPAIR.md"
        )
        self.manifest_relative = (
            "design/gameplay/repairs/return_fire_unusable/"
            "REPAIR_PLAN_MANIFEST.json"
        )
        self.plan_relative = (
            "design/gameplay/repairs/return_fire_unusable/"
            "production_plans/R01_fire.md"
        )

        self.objective_text = """# Objective Gameplay — `mission.next`

| # | Situation | Result |
| --- | --- | --- |
| 1 | Return to the fire. | Continue to the gate. |
"""
        (self.objective_dir / "OBJECTIVE_GAMEPLAY.md").write_text(
            self.objective_text, encoding="utf-8"
        )
        self.objective_sha256 = hashlib.sha256(
            self.objective_text.encode("utf-8")
        ).hexdigest()
        self.repair_text = f"""# Gameplay Repair — `return_fire_unusable`

- Step 1 context: `design/gameplay/repairs/return_fire_unusable/GAMEPLAY_REPAIR_CONTEXT.md`
- Context status: `READY_FOR_REPAIR_DESIGN`
- Anchor objective id: `mission.next`
- Anchor objective: `{self.objective_relative}`
- Anchor SHA-256: `{self.objective_sha256}`
- Repair status: `AI_DRAFT_FOR_REVIEW`

| # | Broken situation | Required closure |
| --- | --- | --- |
| 1 | The visible fire rejects interaction. | It opens cooking on return. |
| 2 | Hunger recovery is unclear. | The result reconciles meter feedback. |
"""
        (self.repair_dir / "GAMEPLAY_REPAIR.md").write_text(
            self.repair_text, encoding="utf-8"
        )
        self.repair_sha256 = hashlib.sha256(
            self.repair_text.encode("utf-8")
        ).hexdigest()
        (self.game_repo / "game.gd").write_text(
            "func use_fire():\n\tpass\n", encoding="utf-8"
        )
        self._write_plan()
        self._write_manifest()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _plan_text(
        self,
        *,
        plan_id: str = "R01",
        status: str = READY_FOR_EXECUTION,
        rows: str = "1",
    ) -> str:
        return f"""# Repair Production Plan — Reuse the fire

- Plan id: `{plan_id}`
- Status: `{status}`
- Anchor objective: `{self.objective_relative}`
- Anchor SHA-256: `{self.objective_sha256}`
- Source repair: `{self.repair_relative}`
- Source SHA-256: `{self.repair_sha256}`
- Repair rows: `{rows}`

## Source authority
Repair row {rows} closes the anchored gap.

## Required player-visible result
The returning player can use the visible fire.

## Existing repo evidence and reuse
`game.gd` owns fire interaction.

## Production changes
Update the existing fire state gate.

## Locked constraints and non-goals
Do not add a mission branch.

## Verification
Test tutorial and returning-player states independently.

## Dependencies and handoff
No prerequisite plan; runtime review closes the gap.
"""

    def _write_plan(
        self,
        *,
        plan_id: str = "R01",
        status: str = READY_FOR_EXECUTION,
        rows: str = "1",
        filename: str = "R01_fire.md",
    ) -> None:
        (self.plan_dir / filename).write_text(
            self._plan_text(plan_id=plan_id, status=status, rows=rows),
            encoding="utf-8",
        )

    def _manifest(self) -> dict:
        return {
            "schema_version": "repair_plan_manifest.v1",
            "project_id": "sample",
            "gap_id": "return_fire_unusable",
            "anchor_objective_id": "mission.next",
            "anchor_objective_gameplay_path": self.objective_relative,
            "anchor_objective_gameplay_sha256": self.objective_sha256,
            "repair_source_path": self.repair_relative,
            "repair_source_sha256": self.repair_sha256,
            "planning_status": READY_FOR_EXECUTION,
            "plans": [
                {
                    "plan_id": "R01",
                    "path": self.plan_relative,
                    "title": "Reuse the fire",
                    "status": READY_FOR_EXECUTION,
                    "repair_rows": [1],
                    "depends_on": [],
                    "work_types": ["CODE", "TEST"],
                    "existing_repo_refs": ["game.gd"],
                    "planned_paths": ["game.gd"],
                }
            ],
            "repair_coverage": [
                {
                    "repair_row": 1,
                    "disposition": "IMPLEMENT",
                    "plan_ids": ["R01"],
                    "rationale": "Runtime blocks the returning player.",
                },
                {
                    "repair_row": 2,
                    "disposition": "NO_CHANGE_REQUIRED",
                    "plan_ids": [],
                    "rationale": "Existing meter feedback already reconciles recovery.",
                },
            ],
            "blocked_gaps": [],
        }

    def _write_manifest(self, payload: dict | None = None) -> None:
        (self.repair_dir / "REPAIR_PLAN_MANIFEST.json").write_text(
            json.dumps(payload or self._manifest(), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

    def test_valid_repair_manifest_is_ready(self) -> None:
        result = validate_repair_plan(str(self.game_repo), self.manifest_relative)
        self.assertEqual(READY_FOR_EXECUTION, result.status)
        self.assertEqual([1, 2], result.repair_rows)
        self.assertEqual(1, result.plan_count)
        self.assertFalse(result.errors)

    def test_direct_context_may_be_the_repair_source(self) -> None:
        context_relative = (
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md"
        )
        context_text = self.repair_text.replace(
            "# Gameplay Repair —", "# Gameplay Repair Context —"
        )
        (self.repair_dir / "GAMEPLAY_REPAIR_CONTEXT.md").write_text(
            context_text, encoding="utf-8"
        )
        context_sha = hashlib.sha256(context_text.encode("utf-8")).hexdigest()
        plan_path = self.plan_dir / "R01_fire.md"
        plan_path.write_text(
            self._plan_text()
            .replace(self.repair_relative, context_relative)
            .replace(self.repair_sha256, context_sha),
            encoding="utf-8",
        )
        payload = self._manifest()
        payload["repair_source_path"] = context_relative
        payload["repair_source_sha256"] = context_sha
        self._write_manifest(payload)
        result = validate_repair_plan(str(self.game_repo), self.manifest_relative)
        self.assertEqual(READY_FOR_EXECUTION, result.status)

    def test_stale_anchor_hash_fails_closed(self) -> None:
        (self.objective_dir / "OBJECTIVE_GAMEPLAY.md").write_text(
            self.objective_text + "\nChanged.\n", encoding="utf-8"
        )
        result = validate_repair_plan(str(self.game_repo), self.manifest_relative)
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("anchor" in error.lower() for error in result.errors))

    def test_stale_repair_hash_fails_closed(self) -> None:
        (self.repair_dir / "GAMEPLAY_REPAIR.md").write_text(
            self.repair_text + "\nChanged.\n", encoding="utf-8"
        )
        result = validate_repair_plan(str(self.game_repo), self.manifest_relative)
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("repair_source_sha256" in error for error in result.errors))

    def test_missing_repair_row_coverage_fails_closed(self) -> None:
        payload = self._manifest()
        payload["repair_coverage"] = payload["repair_coverage"][:1]
        self._write_manifest(payload)
        result = validate_repair_plan(str(self.game_repo), self.manifest_relative)
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("missing repair rows: 2" in error for error in result.errors))

    def test_ready_plan_with_tbd_fails_closed(self) -> None:
        plan_path = self.plan_dir / "R01_fire.md"
        plan_path.write_text(self._plan_text() + "\nTBD\n", encoding="utf-8")
        result = validate_repair_plan(str(self.game_repo), self.manifest_relative)
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("still contains TBD" in error for error in result.errors))

    def test_shared_planned_path_is_rejected(self) -> None:
        self._write_plan(plan_id="R02", rows="2", filename="R02_fire.md")
        payload = self._manifest()
        payload["plans"].append(
            {
                "plan_id": "R02",
                "path": (
                    "design/gameplay/repairs/return_fire_unusable/"
                    "production_plans/R02_fire.md"
                ),
                "title": "Verify recovery",
                "status": READY_FOR_EXECUTION,
                "repair_rows": [2],
                "depends_on": [],
                "work_types": ["TEST"],
                "existing_repo_refs": ["game.gd"],
                "planned_paths": ["game.gd"],
            }
        )
        payload["repair_coverage"][1] = {
            "repair_row": 2,
            "disposition": "VERIFY_EXISTING",
            "plan_ids": ["R02"],
            "rationale": "Verify meter recovery.",
        }
        self._write_manifest(payload)
        result = validate_repair_plan(str(self.game_repo), self.manifest_relative)
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(any("owned by multiple" in error for error in result.errors))

    def test_absolute_persisted_plan_path_is_rejected(self) -> None:
        payload = self._manifest()
        payload["plans"][0]["path"] = str(self.plan_dir / "R01_fire.md")
        self._write_manifest(payload)
        with self.assertRaises(RepairPlanningError):
            validate_repair_plan(str(self.game_repo), self.manifest_relative)

    def test_repair_plan_cannot_mutate_base_objective_authority(self) -> None:
        payload = self._manifest()
        payload["plans"][0]["planned_paths"] = [self.objective_relative]
        self._write_manifest(payload)
        result = validate_repair_plan(str(self.game_repo), self.manifest_relative)
        self.assertEqual(BLOCKED_BY_PLAN_GAP, result.status)
        self.assertTrue(
            any("may not mutate its base" in error for error in result.errors)
        )

    def test_manifest_must_live_beside_repair_source(self) -> None:
        outside_manifest = self.game_repo / "REPAIR_PLAN_MANIFEST.json"
        outside_manifest.write_text(
            json.dumps(self._manifest()), encoding="utf-8"
        )
        with self.assertRaises(RepairPlanningError):
            validate_repair_plan(str(self.game_repo), str(outside_manifest))


if __name__ == "__main__":
    unittest.main()
