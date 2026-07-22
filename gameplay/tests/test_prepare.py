import json
import tempfile
import unittest
from pathlib import Path

from gameplay.prepare import (
    BLOCKED_BY_MATERIAL,
    READY_FOR_HOW_DESIGN,
    READY_FOR_NEW_GAMEPLAY_DESIGN,
    PreparationError,
    prepare_context,
    validate_materials,
)


class PrepareContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.game_repo = Path(self.temporary_directory.name) / "game"
        self.game_repo.mkdir()
        (self.game_repo / "locales.csv").write_text(
            "keys,en,zh\nmission.next,Reach the gate.,前往大門。\n",
            encoding="utf-8",
        )
        (self.game_repo / "progress.gd").write_text(
            "PRIMARY_DRIVER = 'mission'\n"
            "OBJECTIVE = 'mission.next'\n"
            "func complete_objective():\n\treturn true\n",
            encoding="utf-8",
        )
        (self.game_repo / "actions.gd").write_text(
            "func explore():\n\treturn 'map knowledge'\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _payload(self) -> dict:
        return {
            "schema_version": "next_gameplay_unit_input.v1",
            "project_id": "sample",
            "primary_progression_driver": {
                "system_id": "mission",
                "system_kind": "mission_chain",
                "progression_unit": "mission",
                "description": "One mission selects the next objective.",
                "evidence_refs": [
                    {
                        "role": "progression_authority",
                        "path": "progress.gd",
                        "contains": ["PRIMARY_DRIVER"],
                    }
                ],
            },
            "frontier": {
                "decision": "COMPLETE_CURRENT_UNIT",
                "current_state": "mission.next is active",
                "objective_id": "mission.next",
                "objective_locale": {
                    "path": "locales.csv",
                    "key_column": "keys",
                    "locale_column": "zh",
                    "key": "mission.next",
                    "expected_text": "前往大門。",
                },
                "completion_condition": "complete_objective returns true",
                "successor_handoff": {
                    "status": "MISSING",
                    "description": "The following mission is not wired yet.",
                },
                "evidence_refs": [
                    {
                        "role": "runtime_selection",
                        "path": "progress.gd",
                        "contains": ["OBJECTIVE = 'mission.next'"],
                    },
                    {
                        "role": "runtime_completion",
                        "path": "progress.gd",
                        "contains": ["complete_objective"],
                    },
                ],
            },
            "player_actions": [
                {
                    "action_id": "explore",
                    "description": "Reveal routes.",
                    "availability": "During player-controlled traversal.",
                    "rewards": [
                        {
                            "reward_id": "map_knowledge",
                            "kind": "information",
                            "description": "New route knowledge.",
                        }
                    ],
                    "evidence_refs": [
                        {
                            "role": "runtime_action",
                            "path": "actions.gd",
                            "contains": ["func explore"],
                        }
                    ],
                }
            ],
            "recent_patterns": [],
            "design_constraints": [],
        }

    def test_valid_materials_are_ready_for_how_design(self) -> None:
        result = validate_materials(self._payload(), self.game_repo)
        self.assertEqual(READY_FOR_HOW_DESIGN, result.status)
        self.assertEqual("前往大門。", result.objective_text)
        self.assertFalse(result.errors)

    def test_locale_without_runtime_completion_fails_closed(self) -> None:
        payload = self._payload()
        payload["frontier"]["evidence_refs"] = [
            payload["frontier"]["evidence_refs"][0]
        ]
        result = validate_materials(payload, self.game_repo)
        self.assertEqual(BLOCKED_BY_MATERIAL, result.status)
        self.assertTrue(any("runtime_completion" in error for error in result.errors))

    def test_empty_action_list_is_a_new_gameplay_trigger_not_missing_material(self) -> None:
        payload = self._payload()
        payload["player_actions"] = []
        result = validate_materials(payload, self.game_repo)
        self.assertEqual(READY_FOR_NEW_GAMEPLAY_DESIGN, result.status)

    def test_missing_action_reward_blocks_authoring(self) -> None:
        payload = self._payload()
        payload["player_actions"][0]["rewards"] = []
        result = validate_materials(payload, self.game_repo)
        self.assertEqual(BLOCKED_BY_MATERIAL, result.status)
        self.assertTrue(any("rewards" in error for error in result.errors))

    def test_outside_output_path_is_rejected_before_directory_creation(self) -> None:
        payload_path = self.game_repo / "input.json"
        payload_path.write_text(json.dumps(self._payload()), encoding="utf-8")
        outside_directory = Path(self.temporary_directory.name) / "outside" / "nested"
        with self.assertRaises(PreparationError):
            prepare_context(
                str(self.game_repo),
                "input.json",
                str(outside_directory / "context.md"),
            )
        self.assertFalse(outside_directory.exists())

    def test_small_unit_input_merges_stable_project_model(self) -> None:
        inline_payload = self._payload()
        project_model = {
            "schema_version": "gameplay_design_model.v1",
            "project_id": inline_payload["project_id"],
            "primary_progression_driver": inline_payload[
                "primary_progression_driver"
            ],
            "player_actions": inline_payload["player_actions"],
            "recent_patterns": ["project pattern"],
            "design_constraints": ["project constraint"],
        }
        (self.game_repo / "model.json").write_text(
            json.dumps(project_model), encoding="utf-8"
        )
        unit_input = {
            "schema_version": "next_gameplay_unit_input.v1",
            "project_id": inline_payload["project_id"],
            "project_model_path": "model.json",
            "frontier": inline_payload["frontier"],
            "applicable_action_ids": ["explore"],
            "recent_patterns": ["unit pattern"],
            "design_constraints": ["unit constraint"],
        }
        (self.game_repo / "unit.json").write_text(
            json.dumps(unit_input), encoding="utf-8"
        )
        result = prepare_context(
            str(self.game_repo), "unit.json", "work/context.md"
        )
        self.assertEqual(READY_FOR_HOW_DESIGN, result.status)
        rendered = (self.game_repo / "work/context.md").read_text(encoding="utf-8")
        self.assertIn("project pattern", rendered)
        self.assertIn("unit pattern", rendered)
        self.assertIn("`explore`", rendered)


if __name__ == "__main__":
    unittest.main()
