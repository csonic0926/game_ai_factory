import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from gameplay.repair import (
    BLOCKED_BY_REPAIR_MATERIAL,
    READY_FOR_DIRECT_REPAIR_PLAN,
    READY_FOR_REPAIR_DESIGN,
    RepairPreparationError,
    prepare_repair_context,
)


class RepairContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.game_repo = Path(self.temporary_directory.name) / "game"
        self.objective_dir = (
            self.game_repo / "design/gameplay/objective_gameplay/mission.next"
        )
        self.repair_dir = (
            self.game_repo / "design/gameplay/repairs/return_fire_unusable"
        )
        self.objective_dir.mkdir(parents=True)
        self.repair_dir.mkdir(parents=True)
        self.objective_relative = (
            "design/gameplay/objective_gameplay/mission.next/OBJECTIVE_GAMEPLAY.md"
        )
        self.objective_text = """# Objective Gameplay — `mission.next`

| # | Situation | Result |
| --- | --- | --- |
| 1 | Return to the fire. | Continue toward the gate. |
| 2 | Reach the gate. | Complete the mission. |
"""
        (self.objective_dir / "OBJECTIVE_GAMEPLAY.md").write_text(
            self.objective_text, encoding="utf-8"
        )
        self.objective_sha256 = hashlib.sha256(
            self.objective_text.encode("utf-8")
        ).hexdigest()
        (self.game_repo / "game.gd").write_text(
            "func use_fire():\n"
            "\tif tutorial_finished:\n"
            "\t\treturn false\n"
            "func cook():\n"
            "\treturn 'meal recovery'\n",
            encoding="utf-8",
        )
        model = {
            "schema_version": "gameplay_design_model.v1",
            "project_id": "sample",
            "primary_progression_driver": {
                "system_id": "mission",
                "system_kind": "mission_chain",
                "progression_unit": "mission",
                "description": "Missions advance linearly.",
                "evidence_refs": [
                    {
                        "role": "progression_authority",
                        "path": "game.gd",
                        "contains": ["func use_fire"],
                    }
                ],
            },
            "player_actions": [
                {
                    "action_id": "cook",
                    "description": "Cook ingredients at a usable fire.",
                    "availability": "When a cooking fire is interactable.",
                    "rewards": [
                        {
                            "reward_id": "meal_recovery",
                            "kind": "recovery",
                            "description": "Restore expedition resources.",
                        }
                    ],
                    "evidence_refs": [
                        {
                            "role": "runtime_action",
                            "path": "game.gd",
                            "contains": ["func cook"],
                        }
                    ],
                }
            ],
            "recent_patterns": ["Do not hide unavailable interactions."],
            "design_constraints": ["The mission remains linear."],
        }
        model_path = self.game_repo / "design/gameplay/adapter"
        model_path.mkdir(parents=True)
        (model_path / "GAMEPLAY_DESIGN_MODEL.json").write_text(
            json.dumps(model), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _payload(self, *, authority_state: str = "OMITTED_OR_AMBIGUOUS") -> dict:
        requirement = ""
        evidence_refs = []
        user_rulings = []
        if authority_state == "EXPLICIT_REQUIREMENT":
            requirement = "The returning player can cook at the visible fire."
            evidence_refs = [
                {
                    "role": "design_authority",
                    "path": self.objective_relative,
                    "contains": ["Return to the fire."],
                }
            ]
        elif authority_state == "USER_RULING":
            requirement = "The returning player can cook at the visible fire."
            user_rulings = ["The fire is a repeatable supply point."]
        return {
            "schema_version": "gameplay_gap_input.v1",
            "project_id": "sample",
            "gap_status": "OPEN",
            "project_model_path": (
                "design/gameplay/adapter/GAMEPLAY_DESIGN_MODEL.json"
            ),
            "anchor": {
                "objective_id": "mission.next",
                "objective_gameplay_path": self.objective_relative,
                "objective_gameplay_sha256": self.objective_sha256,
                "affected_rows": [1],
            },
            "gap": {
                "gap_id": "return_fire_unusable",
                "summary": "The visible fire cannot be reused.",
                "progression_window": "After tutorial completion and before the gate.",
                "observed_break": "use_fire returns false after the tutorial.",
                "player_visible_contradiction": (
                    "The player has ingredients and sees fire but cannot cook."
                ),
                "evidence_refs": [
                    {
                        "role": "implementation_state",
                        "path": "game.gd",
                        "contains": ["if tutorial_finished:", "return false"],
                    }
                ],
            },
            "authority": {
                "state": authority_state,
                "required_player_visible_result": requirement,
                "evidence_refs": evidence_refs,
            },
            "affected_action_ids": ["cook"],
            "preserve": ["Do not create a new mission branch."],
            "user_rulings": user_rulings,
        }

    def _write_input(self, payload: dict) -> None:
        (self.repair_dir / "GAMEPLAY_GAP_INPUT.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )

    def test_omitted_design_routes_to_one_bounded_repair_author(self) -> None:
        self._write_input(self._payload())
        result = prepare_repair_context(
            str(self.game_repo),
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_GAP_INPUT.json",
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md",
        )
        self.assertEqual(READY_FOR_REPAIR_DESIGN, result.status)
        context = (
            self.game_repo
            / "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md"
        ).read_text(encoding="utf-8")
        self.assertIn("One bounded repair author", context)
        self.assertNotIn("## Repair rows", context)
        self.assertEqual(
            self.objective_text,
            (self.objective_dir / "OBJECTIVE_GAMEPLAY.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_explicit_existing_authority_skips_creative_repair_design(self) -> None:
        self._write_input(self._payload(authority_state="EXPLICIT_REQUIREMENT"))
        result = prepare_repair_context(
            str(self.game_repo),
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_GAP_INPUT.json",
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md",
        )
        self.assertEqual(READY_FOR_DIRECT_REPAIR_PLAN, result.status)
        context = (
            self.game_repo
            / "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## Repair rows", context)
        self.assertIn("| 1 |", context)
        self.assertIn("do not spend a creative author", context)

    def test_persisted_user_ruling_skips_creative_repair_design(self) -> None:
        self._write_input(self._payload(authority_state="USER_RULING"))
        result = prepare_repair_context(
            str(self.game_repo),
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_GAP_INPUT.json",
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md",
        )
        self.assertEqual(READY_FOR_DIRECT_REPAIR_PLAN, result.status)

    def test_user_ruling_without_persisted_ruling_fails_closed(self) -> None:
        payload = self._payload(authority_state="USER_RULING")
        payload["user_rulings"] = []
        self._write_input(payload)
        result = prepare_repair_context(
            str(self.game_repo),
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_GAP_INPUT.json",
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md",
        )
        self.assertEqual(BLOCKED_BY_REPAIR_MATERIAL, result.status)
        self.assertTrue(any("USER_RULING" in error for error in result.errors))

    def test_stale_anchor_hash_fails_closed(self) -> None:
        payload = self._payload()
        payload["anchor"]["objective_gameplay_sha256"] = "0" * 64
        self._write_input(payload)
        result = prepare_repair_context(
            str(self.game_repo),
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_GAP_INPUT.json",
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md",
        )
        self.assertEqual(BLOCKED_BY_REPAIR_MATERIAL, result.status)
        self.assertTrue(any("SHA-256" in error for error in result.errors))

    def test_unknown_anchor_row_fails_closed(self) -> None:
        payload = self._payload()
        payload["anchor"]["affected_rows"] = [99]
        self._write_input(payload)
        result = prepare_repair_context(
            str(self.game_repo),
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_GAP_INPUT.json",
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md",
        )
        self.assertEqual(BLOCKED_BY_REPAIR_MATERIAL, result.status)
        self.assertTrue(any("unknown objective rows" in error for error in result.errors))

    def test_missing_gap_evidence_token_fails_closed(self) -> None:
        payload = self._payload()
        payload["gap"]["evidence_refs"][0]["contains"] = ["not in source"]
        self._write_input(payload)
        result = prepare_repair_context(
            str(self.game_repo),
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_GAP_INPUT.json",
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md",
        )
        self.assertEqual(BLOCKED_BY_REPAIR_MATERIAL, result.status)
        self.assertTrue(any("token not found" in error for error in result.errors))

    def test_locked_design_conflict_does_not_become_a_repair(self) -> None:
        self._write_input(
            self._payload(authority_state="CONFLICTS_WITH_LOCKED_DESIGN")
        )
        result = prepare_repair_context(
            str(self.game_repo),
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_GAP_INPUT.json",
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md",
        )
        self.assertEqual(BLOCKED_BY_REPAIR_MATERIAL, result.status)
        self.assertTrue(any("conflicts with locked design" in error for error in result.errors))

    def test_non_open_gap_cannot_restart_production(self) -> None:
        payload = self._payload()
        payload["gap_status"] = "IMPLEMENTED_PENDING_ACCEPTANCE"
        self._write_input(payload)
        result = prepare_repair_context(
            str(self.game_repo),
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_GAP_INPUT.json",
            "design/gameplay/repairs/return_fire_unusable/"
            "GAMEPLAY_REPAIR_CONTEXT.md",
        )
        self.assertEqual(BLOCKED_BY_REPAIR_MATERIAL, result.status)
        self.assertTrue(any("only an OPEN gap" in error for error in result.errors))

    def test_unknown_action_is_rejected_before_output_creation(self) -> None:
        payload = self._payload()
        payload["affected_action_ids"] = ["fly"]
        self._write_input(payload)
        output_path = self.repair_dir / "GAMEPLAY_REPAIR_CONTEXT.md"
        with self.assertRaises(RepairPreparationError):
            prepare_repair_context(
                str(self.game_repo),
                "design/gameplay/repairs/return_fire_unusable/"
                "GAMEPLAY_GAP_INPUT.json",
                "design/gameplay/repairs/return_fire_unusable/"
                "GAMEPLAY_REPAIR_CONTEXT.md",
            )
        self.assertFalse(output_path.exists())

    def test_outside_output_path_is_rejected_before_directory_creation(self) -> None:
        self._write_input(self._payload())
        outside_directory = Path(self.temporary_directory.name) / "outside" / "nested"
        with self.assertRaises(RepairPreparationError):
            prepare_repair_context(
                str(self.game_repo),
                "design/gameplay/repairs/return_fire_unusable/"
                "GAMEPLAY_GAP_INPUT.json",
                str(outside_directory / "context.md"),
            )
        self.assertFalse(outside_directory.exists())


if __name__ == "__main__":
    unittest.main()
