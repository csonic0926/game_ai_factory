import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gameplay import reader


class ReaderTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".git").mkdir()
        (self.root / "captures").mkdir()
        (self.root / "captures" / "frame-001.png").write_bytes(b"png")

        self.manifest = {
            "schema_version": reader.RAW_MANIFEST_VERSION,
            "run_id": "run-1",
            "session_id": "session-1",
            "evidence_mode": "LIVE_BLIND_RUN",
            "build": {"build_id": "build-7", "content_revision": "content-9"},
            "setup": {
                "save_or_checkpoint": "checkpoint-a",
                "seed": 42,
                "locale": "en",
                "input_mode": "keyboard",
                "platform": "test",
            },
            "display": {"viewport_width": 1280, "viewport_height": 720, "window_mode": "windowed"},
            "performance_context": {"target_fps": 60},
            "raw_events_path": "events.jsonl",
            "capture_roots": ["captures"],
        }
        self.events = [
            self.event(
                1,
                1000,
                "cue_shown",
                "cue",
                {
                    "summary": "Door light appears",
                    "channel": "visual",
                    "observable": {"visual": {"door_light": "on"}},
                    "state": {"door": "closed"},
                },
                ["captures/frame-001.png"],
            ),
            self.event(
                2,
                1100,
                "button_input",
                "action",
                {
                    "summary": "Interact input",
                    "channel": "input",
                    "observable": {"input": "interact"},
                    "state": {"door": "closed"},
                },
            ),
            self.event(
                3,
                1150,
                "door_response",
                "response",
                {
                    "summary": "Door opens",
                    "channel": "world_change",
                    "observable": {"result": "opened"},
                    "state": {"door": "open"},
                },
            ),
            self.event(
                4,
                1200,
                "state_changed",
                None,
                {
                    "summary": "Path is available",
                    "channel": "world_change",
                    "observable": {"path": "available"},
                    "state": {"path": "open"},
                },
            ),
        ]
        self.mapping = {
            "schema_version": reader.MAPPING_VERSION,
            "adapter_id": "fixture-adapter-v1",
            "source_schema_version": reader.RAW_EVENT_VERSION,
            "field_map": {
                "event_id": "source_event_id",
                "sequence": "sequence",
                "monotonic_ms": "monotonic_ms",
                "frame": "frame",
                "event_type": "event_type",
                "context": "context",
                "summary": "payload.summary",
                "observation_channel": "payload.channel",
                "correlation_id": "correlation_id",
                "correlation_role": "correlation_role",
                "capture_refs": "capture_refs",
            },
            "event_type_map": {
                "cue_shown": "cue",
                "button_input": "player_input",
                "door_response": "world_response",
                "state_changed": "state_change",
            },
            "observable_fields": [{"source": "payload.observable", "target": "data"}],
            "hidden_fields": [{"source": "payload.state", "target": "runtime_state"}],
            "public_context_fields": ["scene_id"],
        }
        self.manifest_path = self.root / "RAW_MANIFEST.json"
        self.events_path = self.root / "events.jsonl"
        self.mapping_path = self.root / "mapping.json"
        self.write_inputs()

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def event(sequence, timestamp, event_type, role, payload, captures=None):
        return {
            "schema_version": reader.RAW_EVENT_VERSION,
            "run_id": "run-1",
            "session_id": "session-1",
            "source_event_id": f"ev-{sequence}",
            "sequence": sequence,
            "monotonic_ms": timestamp,
            "frame": sequence * 10,
            "event_type": event_type,
            "context": {"scene_id": "entry", "map_id": "m1"},
            "payload": payload,
            "correlation_id": "door-try-1" if role else None,
            "correlation_role": role,
            "capture_refs": captures or [],
        }

    def write_inputs(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.events_path.write_text("\n".join(json.dumps(event) for event in self.events) + "\n", encoding="utf-8")
        self.mapping_path.write_text(json.dumps(self.mapping), encoding="utf-8")

    @staticmethod
    def acceptance_event(event_id, sequence, kind, correlation_id=None, observable=None):
        role_by_kind = {
            "cue": "cue",
            "player_input": "action",
            "gameplay_action": "action",
            "world_response": "response",
        }
        return {
            "event_id": event_id,
            "sequence": sequence,
            "elapsed_ms": sequence * 100,
            "frame": sequence,
            "kind": kind,
            "observation_channel": None,
            "summary": event_id,
            "public_context": {},
            "observable": observable or {},
            "mechanical_hidden": {},
            "correlation_id": correlation_id,
            "correlation_role": role_by_kind.get(kind) if correlation_id else None,
            "capture_refs": [],
            "raw_ref": {"path": "events.jsonl", "line": sequence, "source_event_id": event_id},
        }

    def acceptance_timeline(
        self,
        run_id="run-a",
        session_id=None,
        evidence_mode="LIVE_BLIND_RUN",
        events=None,
        branch_label=None,
        group_id="probe-group-1",
        observation_complete=False,
    ):
        probe_group = None
        if evidence_mode == "CONTROLLED_BRANCH_PROBE":
            probe_group = {
                "group_id": group_id,
                "baseline_checkpoint": "checkpoint-a",
                "branch_label": branch_label,
            }
        timeline_events = events if events is not None else self.complete_chain_events()
        observation_window = None
        if observation_complete:
            sequences = [event["sequence"] for event in timeline_events]
            observation_window = {
                "start_sequence": min(sequences),
                "end_sequence": max(sequences),
                "coverage_status": "COMPLETE",
                "coverage_basis": "test fixture contiguous flushed event stream",
            }
        return {
            "schema_version": reader.TIMELINE_VERSION,
            "run": {
                "run_id": run_id,
                "session_id": session_id or f"session-{run_id}",
                "evidence_mode": evidence_mode,
                "build": {"build_id": "build-7", "content_revision": "content-9"},
                "setup": {
                    "save_or_checkpoint": "checkpoint-a",
                    "seed": 42,
                    "locale": "en",
                    "input_mode": "keyboard",
                    "platform": "test",
                },
                "display": {"viewport_width": 1280, "viewport_height": 720, "window_mode": "windowed"},
                "performance_context": {"target_fps": 60},
                "probe_group": probe_group,
                "observation_window": observation_window,
            },
            "source_stream": {},
            "events": timeline_events,
            "latencies": [],
        }

    def complete_chain_events(self, correlation_id="chain-1"):
        return [
            self.acceptance_event("cue", 1, "cue", correlation_id, {"signal": "light"}),
            self.acceptance_event("action", 2, "player_input", correlation_id, {"input": "interact"}),
            self.acceptance_event("response", 3, "world_response", correlation_id, {"result": "opened"}),
            self.acceptance_event("carry", 4, "state_change", None, {"path": "available"}),
        ]

    def kernel_specific_chain_events(self, kernel_surface, branch_signature):
        events = self.complete_chain_events(correlation_id=f"{kernel_surface}-chain")
        for event in events:
            event["observable"]["kernel_surface"] = kernel_surface
        events[1]["observable"]["branch_signature"] = branch_signature
        events[2]["observable"]["response_branch"] = branch_signature
        events[3]["observable"]["carry_branch"] = branch_signature
        return events

    @staticmethod
    def acceptance_kernels(
        required_modes=None,
        negative_match=None,
        ordered_sequences=None,
        controlled_probe_group_ids=None,
    ):
        declared_modes = required_modes or ["LIVE_BLIND_RUN"]
        selectors = [
            {"phase": "cue", "match": {"event_kind": "cue"}},
            {"phase": "action_or_attempt", "match": {"event_kind": "player_input"}},
            {"phase": "world_response", "match": {"event_kind": "world_response"}},
            {"phase": "carry_forward", "match": {"event_kind": "state_change"}},
        ]
        if negative_match is not None:
            selectors.append(
                {
                    "phase": "negative_check",
                    "match": negative_match,
                    "window": {"start_phase": "cue", "end_phase": "carry_forward"},
                }
            )
        kernel = {
            "kernel_id": "door-open",
            "required_evidence_modes": declared_modes,
            "selectors": selectors,
        }
        if "CONTROLLED_BRANCH_PROBE" in declared_modes:
            kernel["controlled_probe_group_ids"] = (
                controlled_probe_group_ids
                if controlled_probe_group_ids is not None
                else ["probe-group-1"]
            )
        elif controlled_probe_group_ids is not None:
            kernel["controlled_probe_group_ids"] = controlled_probe_group_ids
        if ordered_sequences is not None:
            kernel["ordered_sequences"] = ordered_sequences
        return {
            "schema_version": reader.KERNEL_VERSION,
            "sheet_binding": {
                "path": "design/gameplay/experience_beat_sheets/door.md",
                "sheet_id": "door",
                "version_token": "v1",
                "checksum": "sha256:test",
            },
            "kernels": [kernel],
        }

    @staticmethod
    def ordered_sequence(sequence_id, after_phase, before_phase, matches):
        return {
            "sequence_id": sequence_id,
            "after_phase": after_phase,
            "before_phase": before_phase,
            "matches": [{"match": match} for match in matches],
        }

    def timed_event(self, event_id, sequence, elapsed_ms, kind, correlation_id=None, observable=None):
        event = self.acceptance_event(event_id, sequence, kind, correlation_id, observable)
        event["elapsed_ms"] = elapsed_ms
        return event

    def quantitative_budget_inputs(self, *, distinct_decision_consequences=True):
        base_events = [
            self.timed_event("span-start", 1, 0, "state_change", observable={"span": "start"}),
            self.timed_event("control-start", 2, 0, "control", observable={"owner": "player"}),
            self.timed_event("presentation-start", 3, 1000, "presentation", observable={"panel": "open"}),
            self.timed_event("presentation-end", 4, 4000, "presentation", observable={"panel": "closed"}),
            self.timed_event("decision-cue", 5, 10000, "cue", "decision-1", {"surface": "decision"}),
            self.timed_event(
                "decision-action",
                6,
                12000,
                "player_input",
                "decision-1",
                {"surface": "decision", "input": "left"},
            ),
            self.timed_event(
                "decision-response",
                7,
                14000,
                "world_response",
                "decision-1",
                {"surface": "decision", "outcome": "left-open"},
            ),
            self.timed_event(
                "decision-carry",
                8,
                16000,
                "state_change",
                observable={"surface": "decision", "route": "left"},
            ),
            self.timed_event("traversal-start", 9, 20000, "gameplay_action", observable={"travel": "start"}),
            self.timed_event("traversal-end", 10, 26000, "gameplay_action", observable={"travel": "end"}),
            self.timed_event("combat-cue", 11, 28000, "cue", "combat-1", {"surface": "combat"}),
            self.timed_event("combat-action", 12, 30000, "player_input", "combat-1", {"surface": "combat"}),
            self.timed_event("combat-response", 13, 32000, "world_response", "combat-1", {"surface": "combat"}),
            self.timed_event("combat-carry", 14, 34000, "state_change", observable={"surface": "combat"}),
            self.timed_event("interaction-cue", 15, 38000, "cue", "interaction-1", {"surface": "interaction"}),
            self.timed_event("interaction-action", 16, 40000, "player_input", "interaction-1", {"surface": "interaction"}),
            self.timed_event("interaction-response", 17, 42000, "world_response", "interaction-1", {"surface": "interaction"}),
            self.timed_event("interaction-carry", 18, 44000, "state_change", observable={"surface": "interaction"}),
            self.timed_event("control-end", 19, 50000, "control", observable={"owner": "system"}),
            self.timed_event("span-end", 20, 60000, "state_change", observable={"span": "end"}),
        ]
        base = self.acceptance_timeline(
            run_id="first-play",
            evidence_mode="RECORDED_RUN",
            events=base_events,
            observation_complete=True,
        )

        def branch_events(action, outcome, route):
            return [
                self.timed_event("branch-cue", 1, 0, "cue", "branch-chain", {"surface": "decision"}),
                self.timed_event(
                    "branch-action",
                    2,
                    100,
                    "player_input",
                    "branch-chain",
                    {"surface": "decision", "input": action},
                ),
                self.timed_event(
                    "branch-response",
                    3,
                    200,
                    "world_response",
                    "branch-chain",
                    {"surface": "decision", "outcome": outcome},
                ),
                self.timed_event(
                    "branch-carry",
                    4,
                    300,
                    "state_change",
                    observable={"surface": "decision", "route": route},
                ),
            ]

        branch_a = self.acceptance_timeline(
            run_id="decision-a",
            evidence_mode="CONTROLLED_BRANCH_PROBE",
            branch_label="route-a",
            group_id="decision-proof",
            events=branch_events("left", "left-open", "left"),
        )
        branch_b = self.acceptance_timeline(
            run_id="decision-b",
            evidence_mode="CONTROLLED_BRANCH_PROBE",
            branch_label="route-b",
            group_id="decision-proof",
            events=branch_events(
                "right",
                "right-open" if distinct_decision_consequences else "left-open",
                "right" if distinct_decision_consequences else "left",
            ),
        )
        def selectors(surface):
            return [
                {"phase": "cue", "match": {"event_kind": "cue", "observable": {"surface": surface}}},
                {"phase": "action_or_attempt", "match": {"event_kind": "player_input", "observable": {"surface": surface}}},
                {"phase": "world_response", "match": {"event_kind": "world_response", "observable": {"surface": surface}}},
                {"phase": "carry_forward", "match": {"event_kind": "state_change", "observable": {"surface": surface}}},
            ]
        binding = {
            "path": "design/gameplay/experience_beat_sheets/quantitative.md",
            "sheet_id": "quantitative",
            "version_token": "v1",
            "checksum": "sha256:quantitative",
        }
        kernels = {
            "schema_version": reader.KERNEL_VERSION,
            "sheet_binding": binding,
            "kernels": [
                {
                    "kernel_id": "decision-kernel",
                    "required_evidence_modes": ["RECORDED_RUN", "CONTROLLED_BRANCH_PROBE"],
                    "controlled_probe_group_ids": ["decision-proof"],
                    "selectors": selectors("decision"),
                },
                {
                    "kernel_id": "combat-kernel",
                    "required_evidence_modes": ["RECORDED_RUN"],
                    "selectors": selectors("combat"),
                },
                {
                    "kernel_id": "interaction-kernel",
                    "required_evidence_modes": ["RECORDED_RUN"],
                    "selectors": selectors("interaction"),
                },
            ],
        }
        budget = {
            "schema_version": reader.BUDGET_VERSION,
            "budget_id": "quantitative-budget-v1",
            "sheet_binding": binding,
            "exact_span": {
                "start_boundary": {"boundary_id": "runtime-start", "match": {"event_id": "span-start"}},
                "end_boundary": {"boundary_id": "runtime-end", "match": {"event_id": "span-end"}},
            },
            "thresholds": {
                "first_play_duration_ms": {"target": 60000, "minimum": 50000, "maximum": 70000},
                "replay_target_duration_ms": 45000,
                "minimum_player_control_ratio": 0.75,
                "maximum_presentation_only_gap_ms": 5000,
                "maximum_traversal_only_gap_ms": 8000,
                "content_counts": {
                    "complete_gameplay_beats": {"minimum": 3, "maximum": 3},
                    "meaningful_decisions": {"minimum": 1, "maximum": 1},
                    "combat_encounters": {"minimum": 1, "maximum": 1},
                    "world_interactions": {"minimum": 1, "maximum": 1},
                    "narrative_presentations": {"minimum": 1, "maximum": 2},
                },
                "narrative_presentation_time_ms": {"minimum": 1000, "maximum": 5000},
            },
            "interval_selectors": {
                "player_control": [
                    {
                        "interval_id": "player-control",
                        "start_match": {"event_id": "control-start"},
                        "end_match": {"event_id": "control-end"},
                    }
                ],
                "presentation": [
                    {
                        "interval_id": "opening-presentation",
                        "start_match": {"event_id": "presentation-start"},
                        "end_match": {"event_id": "presentation-end"},
                    }
                ],
                "traversal": [
                    {
                        "interval_id": "route-traversal",
                        "start_match": {"event_id": "traversal-start"},
                        "end_match": {"event_id": "traversal-end"},
                    }
                ],
            },
            "gameplay_measurements": [
                {
                    "measurement_id": "decision-beat",
                    "kernel_id": "decision-kernel",
                    "categories": ["complete_gameplay_beat", "meaningful_decision"],
                },
                {
                    "measurement_id": "combat-beat",
                    "kernel_id": "combat-kernel",
                    "categories": ["complete_gameplay_beat", "combat_encounter"],
                },
                {
                    "measurement_id": "interaction-beat",
                    "kernel_id": "interaction-kernel",
                    "categories": ["complete_gameplay_beat", "world_interaction"],
                },
            ],
            "non_gameplay_activity_selectors": [],
        }
        return [base, branch_a, branch_b], kernels, budget

    def test_quantitative_budget_passes_genuine_span_with_distinct_decision_consequences(self):
        timelines, kernels, budget = self.quantitative_budget_inputs()
        result = reader.measure_experience_budget(
            timelines,
            kernels,
            budget,
            measurement_run_id="first-play",
            measurement_session_id="session-first-play",
        )
        self.assertEqual("PASS_EXPERIENCE_BUDGET", result["status"])
        self.assertEqual(60000, result["measured"]["first_play_duration_ms"])
        self.assertEqual(50000, result["measured"]["raw_player_control_time_ms"])
        self.assertEqual(3000, result["measured"]["presentation_overlap_with_player_control_ms"])
        self.assertAlmostEqual(47 / 60, result["measured"]["player_control_ratio"])
        self.assertEqual(3000, result["measured"]["maximum_presentation_only_gap_ms"])
        self.assertEqual(6000, result["measured"]["maximum_traversal_only_gap_ms"])
        self.assertEqual(
            {
                "complete_gameplay_beats": 3,
                "meaningful_decisions": 1,
                "combat_encounters": 1,
                "world_interactions": 1,
                "narrative_presentations": 1,
            },
            result["measured"]["content_counts"],
        )
        self.assertTrue(all(comparison["source_evidence_refs"] for comparison in result["comparisons"]))
        self.assertNotIn("PASS_FACTORY_CONFORMANCE", json.dumps(result))

    def test_quantitative_budget_threshold_failure(self):
        timelines, kernels, budget = self.quantitative_budget_inputs()
        budget["thresholds"]["minimum_player_control_ratio"] = 0.9
        result = reader.measure_experience_budget(
            timelines,
            kernels,
            budget,
            measurement_run_id="first-play",
            measurement_session_id="session-first-play",
        )
        self.assertEqual("FAIL_EXPERIENCE_BUDGET", result["status"])
        comparison = next(
            item
            for item in result["comparisons"]
            if item["metric"] == "player_control_ratio"
        )
        self.assertFalse(comparison["passed"])
        self.assertAlmostEqual(47 / 60, comparison["actual"])

    def test_false_decision_labels_without_distinct_consequences_fail_budget(self):
        timelines, kernels, budget = self.quantitative_budget_inputs(
            distinct_decision_consequences=False
        )
        result = reader.measure_experience_budget(
            timelines,
            kernels,
            budget,
            measurement_run_id="first-play",
            measurement_session_id="session-first-play",
        )
        self.assertEqual("FAIL_EXPERIENCE_BUDGET", result["status"])
        self.assertEqual(2, result["measured"]["complete_gameplay_engagement_chain_count"])
        self.assertEqual(0, result["measured"]["content_counts"]["meaningful_decisions"])
        measurement = next(
            item
            for item in result["gameplay_measurements"]
            if item["measurement_id"] == "decision-beat"
        )
        self.assertFalse(measurement["decision_consequences_proven"])
        self.assertFalse(
            measurement["controlled_branch_evidence"][0][
                "branch_consequence_evidence_distinct"
            ]
        )

    def test_malformed_quantitative_evidence_is_inconclusive(self):
        timelines, kernels, budget = self.quantitative_budget_inputs()
        budget["exact_span"]["end_boundary"]["match"] = {"event_id": "missing-end"}
        result = reader.measure_experience_budget(
            timelines,
            kernels,
            budget,
            measurement_run_id="first-play",
            measurement_session_id="session-first-play",
        )
        self.assertEqual("INCONCLUSIVE_EVIDENCE", result["status"])
        self.assertIn("matched 0", result["findings"][0]["message"])
        self.assertEqual([], result["comparisons"])

    def test_budget_cannot_author_runtime_run_or_session_ownership(self):
        timelines, kernels, budget = self.quantitative_budget_inputs()
        budget["exact_span"]["measurement_run_id"] = "first-play"
        budget["exact_span"]["measurement_session_id"] = "session-first-play"
        result = reader.measure_experience_budget(
            timelines,
            kernels,
            budget,
            measurement_run_id="first-play",
            measurement_session_id="session-first-play",
        )
        self.assertEqual("INCONCLUSIVE_EVIDENCE", result["status"])
        self.assertIn("exact_span has invalid fields", result["findings"][0]["message"])

    def test_one_chain_cannot_fill_multiple_distinct_content_quotas(self):
        timelines, kernels, budget = self.quantitative_budget_inputs()
        budget["gameplay_measurements"][0]["categories"] = [
            "complete_gameplay_beat",
            "meaningful_decision",
            "combat_encounter",
        ]
        result = reader.measure_experience_budget(
            timelines,
            kernels,
            budget,
            measurement_run_id="first-play",
            measurement_session_id="session-first-play",
        )
        self.assertEqual("INCONCLUSIVE_EVIDENCE", result["status"])
        self.assertIn("at most one content category", result["findings"][0]["message"])

    def test_teleporter_avg_control_return_ten_second_walk_arrival_is_no_gameplay(self):
        events = [
            self.timed_event("span-start", 1, 0, "state_change", observable={"span": "start"}),
            self.timed_event("teleporter-activate", 2, 100, "player_input", observable={"teleporter": "pressed"}),
            self.timed_event("avg-open", 3, 200, "presentation", observable={"avg": "open"}),
            self.timed_event("avg-advance", 4, 1000, "gameplay_action", observable={"avg": "advance"}),
            self.timed_event("avg-close", 5, 3000, "presentation", observable={"avg": "closed"}),
            self.timed_event("control-return", 6, 3100, "control", observable={"owner": "player"}),
            self.timed_event("walk-start", 7, 3200, "gameplay_action", observable={"locomotion": "start"}),
            self.timed_event("move-input", 8, 5000, "player_input", observable={"input": "forward"}),
            self.timed_event("walk-end", 9, 13200, "gameplay_action", observable={"locomotion": "end"}),
            self.timed_event("supply-arrival", 10, 13300, "state_change", observable={"arrival": "supply-point"}),
            self.timed_event("control-end", 11, 13400, "control", observable={"owner": "system"}),
            self.timed_event("span-end", 12, 13500, "state_change", observable={"span": "end"}),
        ]
        timeline = self.acceptance_timeline(
            run_id="walking-only",
            evidence_mode="RECORDED_RUN",
            events=events,
            observation_complete=True,
        )
        binding = {
            "path": "design/gameplay/experience_beat_sheets/walking-only.md",
            "sheet_id": "walking-only",
            "version_token": "v1",
            "checksum": "sha256:walking-only",
        }
        kernels = {
            "schema_version": reader.KERNEL_VERSION,
            "sheet_binding": binding,
            "kernels": [
                {
                    "kernel_id": "real-gameplay-kernel",
                    "required_evidence_modes": ["RECORDED_RUN"],
                    "selectors": [
                        {"phase": "cue", "match": {"event_kind": "cue", "observable": {"surface": "real-gameplay"}}},
                        {"phase": "action_or_attempt", "match": {"event_kind": "player_input", "observable": {"surface": "real-gameplay"}}},
                        {"phase": "world_response", "match": {"event_kind": "world_response", "observable": {"surface": "real-gameplay"}}},
                        {"phase": "carry_forward", "match": {"event_kind": "state_change", "observable": {"surface": "real-gameplay"}}},
                    ],
                }
            ],
        }
        budget = {
            "schema_version": reader.BUDGET_VERSION,
            "budget_id": "walking-only-budget",
            "sheet_binding": binding,
            "exact_span": {
                "start_boundary": {"boundary_id": "start", "match": {"event_id": "span-start"}},
                "end_boundary": {"boundary_id": "end", "match": {"event_id": "span-end"}},
            },
            "thresholds": {
                "first_play_duration_ms": {"target": 13500, "minimum": 10000, "maximum": 20000},
                "minimum_player_control_ratio": 0.5,
                "maximum_presentation_only_gap_ms": 5000,
                "maximum_traversal_only_gap_ms": 12000,
                "content_counts": {
                    "complete_gameplay_beats": {"minimum": 1, "maximum": 2},
                    "meaningful_decisions": {"minimum": 0, "maximum": 1},
                    "combat_encounters": {"minimum": 0, "maximum": 1},
                    "world_interactions": {"minimum": 0, "maximum": 1},
                    "narrative_presentations": {"minimum": 1, "maximum": 2},
                },
                "narrative_presentation_time_ms": {"minimum": 1000, "maximum": 5000},
            },
            "interval_selectors": {
                "player_control": [
                    {"interval_id": "control", "start_match": {"event_id": "control-return"}, "end_match": {"event_id": "control-end"}}
                ],
                "presentation": [
                    {"interval_id": "avg", "start_match": {"event_id": "avg-open"}, "end_match": {"event_id": "avg-close"}}
                ],
                "traversal": [
                    {"interval_id": "straight-walk", "start_match": {"event_id": "walk-start"}, "end_match": {"event_id": "walk-end"}}
                ],
            },
            "gameplay_measurements": [
                {"measurement_id": "required-real-gameplay", "kernel_id": "real-gameplay-kernel", "categories": ["complete_gameplay_beat"]}
            ],
            "non_gameplay_activity_selectors": [
                {"activity_id": "teleporter", "activity_type": "teleporter_activation", "match": {"event_id": "teleporter-activate"}},
                {"activity_id": "dialogue", "activity_type": "dialogue_advance", "match": {"event_id": "avg-advance"}},
                {"activity_id": "movement", "activity_type": "straight_locomotion", "match": {"event_id": "move-input"}},
                {"activity_id": "arrival", "activity_type": "objective_arrival", "match": {"event_id": "supply-arrival"}},
            ],
        }
        result = reader.measure_experience_budget(
            [timeline],
            kernels,
            budget,
            measurement_run_id="walking-only",
            measurement_session_id="session-walking-only",
        )
        self.assertEqual("NO_GAMEPLAY", result["status"])
        self.assertEqual("ONLY_CONFIGURED_NON_GAMEPLAY_ACTIVITY", result["no_gameplay_reason"])
        self.assertEqual(0, result["measured"]["complete_gameplay_engagement_chain_count"])
        self.assertGreater(result["measured"]["player_control_ratio"], 0.7)
        self.assertEqual(10000, result["measured"]["maximum_traversal_only_gap_ms"])
        self.assertEqual(
            {"teleporter_activation", "dialogue_advance", "straight_locomotion", "objective_arrival"},
            {
                item["activity_type"]
                for item in result["non_gameplay_activity_evidence"]
                if item["source_evidence_refs"]
            },
        )

    def test_non_gameplay_events_cannot_self_certify_a_complete_gameplay_chain(self):
        avg_open = self.timed_event(
            "avg-open",
            3,
            200,
            "presentation",
            observable={"avg": "open"},
        )
        avg_open["correlation_id"] = "fake-gameplay"
        avg_open["correlation_role"] = "cue"
        avg_close = self.timed_event(
            "avg-close",
            5,
            3000,
            "presentation",
            observable={"avg": "closed"},
        )
        avg_close["correlation_id"] = "fake-gameplay"
        avg_close["correlation_role"] = "response"
        events = [
            self.timed_event("span-start", 1, 0, "state_change", observable={"span": "start"}),
            self.timed_event("teleporter-activate", 2, 100, "player_input", observable={"teleporter": "pressed"}),
            avg_open,
            self.timed_event(
                "avg-advance",
                4,
                1000,
                "gameplay_action",
                "fake-gameplay",
                {"avg": "advance"},
            ),
            avg_close,
            self.timed_event("control-return", 6, 3100, "control", observable={"owner": "player"}),
            self.timed_event("walk-start", 7, 3200, "gameplay_action", observable={"locomotion": "start"}),
            self.timed_event("move-input", 8, 5000, "player_input", observable={"input": "forward"}),
            self.timed_event("walk-end", 9, 13200, "gameplay_action", observable={"locomotion": "end"}),
            self.timed_event("supply-arrival", 10, 13300, "state_change", observable={"arrival": "supply-point"}),
            self.timed_event("control-end", 11, 13400, "control", observable={"owner": "system"}),
            self.timed_event("span-end", 12, 13500, "state_change", observable={"span": "end"}),
        ]
        timeline = self.acceptance_timeline(
            run_id="self-certifying-walk",
            evidence_mode="RECORDED_RUN",
            events=events,
            observation_complete=True,
        )
        binding = {
            "path": "design/gameplay/experience_beat_sheets/self-certifying-walk.md",
            "sheet_id": "self-certifying-walk",
            "version_token": "v1",
            "checksum": "sha256:self-certifying-walk",
        }
        kernels = {
            "schema_version": reader.KERNEL_VERSION,
            "sheet_binding": binding,
            "kernels": [
                {
                    "kernel_id": "fake-gameplay-kernel",
                    "required_evidence_modes": ["RECORDED_RUN"],
                    "selectors": [
                        {"phase": "cue", "match": {"event_id": "avg-open"}},
                        {"phase": "action_or_attempt", "match": {"event_id": "avg-advance"}},
                        {"phase": "world_response", "match": {"event_id": "avg-close"}},
                        {"phase": "carry_forward", "match": {"event_id": "control-return"}},
                    ],
                }
            ],
        }
        budget = {
            "schema_version": reader.BUDGET_VERSION,
            "budget_id": "self-certifying-walk-budget",
            "sheet_binding": binding,
            "exact_span": {
                "start_boundary": {"boundary_id": "start", "match": {"event_id": "span-start"}},
                "end_boundary": {"boundary_id": "end", "match": {"event_id": "span-end"}},
            },
            "thresholds": {
                "first_play_duration_ms": {"target": 13500, "minimum": 10000, "maximum": 20000},
                "minimum_player_control_ratio": 0.5,
                "maximum_presentation_only_gap_ms": 5000,
                "maximum_traversal_only_gap_ms": 12000,
                "content_counts": {
                    "complete_gameplay_beats": {"minimum": 1, "maximum": 2},
                    "meaningful_decisions": {"minimum": 0, "maximum": 1},
                    "combat_encounters": {"minimum": 0, "maximum": 1},
                    "world_interactions": {"minimum": 0, "maximum": 1},
                    "narrative_presentations": {"minimum": 1, "maximum": 2},
                },
                "narrative_presentation_time_ms": {"minimum": 1000, "maximum": 5000},
            },
            "interval_selectors": {
                "player_control": [
                    {"interval_id": "control", "start_match": {"event_id": "control-return"}, "end_match": {"event_id": "control-end"}}
                ],
                "presentation": [
                    {"interval_id": "avg", "start_match": {"event_id": "avg-open"}, "end_match": {"event_id": "avg-close"}}
                ],
                "traversal": [
                    {"interval_id": "walk", "start_match": {"event_id": "walk-start"}, "end_match": {"event_id": "walk-end"}}
                ],
            },
            "gameplay_measurements": [
                {
                    "measurement_id": "fake-gameplay",
                    "kernel_id": "fake-gameplay-kernel",
                    "categories": ["complete_gameplay_beat"],
                }
            ],
            "non_gameplay_activity_selectors": [
                {"activity_id": "teleporter", "activity_type": "teleporter_activation", "match": {"event_id": "teleporter-activate"}},
                {"activity_id": "avg-open", "activity_type": "presentation", "match": {"event_id": "avg-open"}},
                {"activity_id": "dialogue", "activity_type": "dialogue_advance", "match": {"event_id": "avg-advance"}},
                {"activity_id": "avg-close", "activity_type": "presentation", "match": {"event_id": "avg-close"}},
                {"activity_id": "control", "activity_type": "control_return", "match": {"event_id": "control-return"}},
                {"activity_id": "movement", "activity_type": "straight_locomotion", "match": {"event_id": "move-input"}},
                {"activity_id": "arrival", "activity_type": "objective_arrival", "match": {"event_id": "supply-arrival"}},
            ],
        }
        result = reader.measure_experience_budget(
            [timeline],
            kernels,
            budget,
            measurement_run_id="self-certifying-walk",
            measurement_session_id="session-self-certifying-walk",
        )
        self.assertEqual("NO_GAMEPLAY", result["status"])
        self.assertEqual(0, result["measured"]["complete_gameplay_engagement_chain_count"])
        measurement = result["gameplay_measurements"][0]
        self.assertTrue(measurement["base_chain_complete"])
        self.assertTrue(measurement["non_gameplay_only_chain"])
        self.assertFalse(measurement["gameplay_work_response_proven"])
        self.assertEqual("INCOMPLETE", measurement["status"])

    def test_presentation_overlap_does_not_inflate_player_control_ratio(self):
        events = [
            self.timed_event("span-start", 1, 0, "state_change", observable={"span": "start"}),
            self.timed_event("control-start", 2, 0, "control", observable={"owner": "player"}),
            self.timed_event("presentation-start", 3, 1000, "presentation", observable={"panel": "open"}),
            self.timed_event("work-cue", 4, 2000, "cue", "work", {"surface": "work"}),
            self.timed_event("work-action", 5, 3000, "player_input", "work", {"surface": "work"}),
            self.timed_event("work-response", 6, 4000, "world_response", "work", {"surface": "work"}),
            self.timed_event("work-carry", 7, 5000, "state_change", observable={"surface": "work"}),
            self.timed_event("presentation-end", 8, 9000, "presentation", observable={"panel": "closed"}),
            self.timed_event("control-end", 9, 10000, "control", observable={"owner": "system"}),
            self.timed_event("span-end", 10, 10000, "state_change", observable={"span": "end"}),
        ]
        timeline = self.acceptance_timeline(
            run_id="presentation-control",
            evidence_mode="RECORDED_RUN",
            events=events,
            observation_complete=True,
        )
        binding = {
            "path": "design/gameplay/experience_beat_sheets/presentation-control.md",
            "sheet_id": "presentation-control",
            "version_token": "v1",
            "checksum": "sha256:presentation-control",
        }
        kernels = {
            "schema_version": reader.KERNEL_VERSION,
            "sheet_binding": binding,
            "kernels": [
                {
                    "kernel_id": "work-kernel",
                    "required_evidence_modes": ["RECORDED_RUN"],
                    "selectors": [
                        {"phase": "cue", "match": {"event_id": "work-cue"}},
                        {"phase": "action_or_attempt", "match": {"event_id": "work-action"}},
                        {"phase": "world_response", "match": {"event_id": "work-response"}},
                        {"phase": "carry_forward", "match": {"event_id": "work-carry"}},
                    ],
                }
            ],
        }
        budget = {
            "schema_version": reader.BUDGET_VERSION,
            "budget_id": "presentation-control-budget",
            "sheet_binding": binding,
            "exact_span": {
                "start_boundary": {"boundary_id": "start", "match": {"event_id": "span-start"}},
                "end_boundary": {"boundary_id": "end", "match": {"event_id": "span-end"}},
            },
            "thresholds": {
                "first_play_duration_ms": {"target": 10000, "minimum": 9000, "maximum": 11000},
                "minimum_player_control_ratio": 0.5,
                "maximum_presentation_only_gap_ms": 10000,
                "maximum_traversal_only_gap_ms": 10000,
                "content_counts": {
                    "complete_gameplay_beats": {"minimum": 1, "maximum": 1},
                    "meaningful_decisions": {"minimum": 0, "maximum": 0},
                    "combat_encounters": {"minimum": 0, "maximum": 0},
                    "world_interactions": {"minimum": 0, "maximum": 0},
                    "narrative_presentations": {"minimum": 1, "maximum": 1},
                },
                "narrative_presentation_time_ms": {"minimum": 8000, "maximum": 8000},
            },
            "interval_selectors": {
                "player_control": [
                    {"interval_id": "control", "start_match": {"event_id": "control-start"}, "end_match": {"event_id": "control-end"}}
                ],
                "presentation": [
                    {"interval_id": "presentation", "start_match": {"event_id": "presentation-start"}, "end_match": {"event_id": "presentation-end"}}
                ],
                "traversal": [],
            },
            "gameplay_measurements": [
                {"measurement_id": "work", "kernel_id": "work-kernel", "categories": ["complete_gameplay_beat"]}
            ],
            "non_gameplay_activity_selectors": [],
        }
        result = reader.measure_experience_budget(
            [timeline],
            kernels,
            budget,
            measurement_run_id="presentation-control",
            measurement_session_id="session-presentation-control",
        )
        self.assertEqual("FAIL_EXPERIENCE_BUDGET", result["status"])
        self.assertEqual(10000, result["measured"]["raw_player_control_time_ms"])
        self.assertEqual(8000, result["measured"]["presentation_overlap_with_player_control_ms"])
        self.assertEqual(2000, result["measured"]["player_control_time_ms"])
        self.assertAlmostEqual(0.2, result["measured"]["player_control_ratio"])

    def test_validate_normalize_reconstruct_and_blind(self):
        _, _, report = reader.validate_evidence(self.manifest_path, self.events_path)
        self.assertEqual("PASS_INTEGRITY", report["status"])

        stream, _ = reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)
        self.assertEqual(["cue", "player_input", "world_response", "state_change"], [event["kind"] for event in stream["events"]])
        self.assertEqual({"data": {"visual": {"door_light": "on"}}}, stream["events"][0]["observable"])
        self.assertEqual("visual", stream["events"][0]["observation_channel"])
        self.assertEqual({"runtime_state": {"door": "closed"}}, stream["events"][0]["hidden"])

        timeline, timeline_report = reader.reconstruct_timeline(stream)
        self.assertEqual("PASS_INTEGRITY", timeline_report["status"])
        self.assertEqual(100, timeline["latencies"][0]["cue_to_action_ms"])
        self.assertEqual(50, timeline["latencies"][0]["action_to_response_ms"])

        blind = reader.build_blind_projection(timeline)
        first = blind["payloads"][0]
        self.assertNotIn("mechanical_hidden", first)
        self.assertNotIn("correlation_id", first)
        self.assertNotIn("summary", first)
        self.assertNotIn("kind", first)
        self.assertEqual("visual", first["observation_channel"])
        self.assertEqual("on", first["observable"]["data"]["visual"]["door_light"])

    def test_forbidden_interpretation_field_fails_closed(self):
        self.events[0]["payload"]["player_understood"] = True
        self.write_inputs()
        _, _, report = reader.validate_evidence(self.manifest_path, self.events_path)
        self.assertEqual("INCONCLUSIVE_EVIDENCE", report["status"])
        self.assertIn("FORBIDDEN_INTERPRETATION_FIELD", {item["code"] for item in report["findings"]})

    def test_missing_capture_fails_closed(self):
        self.events[0]["capture_refs"] = ["captures/missing.png"]
        self.write_inputs()
        _, _, report = reader.validate_evidence(self.manifest_path, self.events_path)
        self.assertEqual("INCONCLUSIVE_EVIDENCE", report["status"])
        self.assertIn("CAPTURE_REF_MISSING", {item["code"] for item in report["findings"]})

    def test_controlled_probe_requires_group_provenance(self):
        self.manifest["evidence_mode"] = "CONTROLLED_BRANCH_PROBE"
        self.write_inputs()
        _, _, report = reader.validate_evidence(self.manifest_path, self.events_path)
        self.assertEqual("INCONCLUSIVE_EVIDENCE", report["status"])
        self.assertIn("PROBE_GROUP_REQUIRED", {item["code"] for item in report["findings"]})

    def test_incomplete_correlation_is_inconclusive(self):
        self.events[2]["correlation_id"] = None
        self.events[2]["correlation_role"] = None
        self.write_inputs()
        stream, _ = reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)
        with self.assertRaises(reader.ReaderError):
            reader.reconstruct_timeline(stream)

    def test_duplicate_correlation_role_is_inconclusive(self):
        duplicate_cue = copy.deepcopy(self.events[0])
        duplicate_cue["source_event_id"] = "ev-duplicate-cue"
        self.events.insert(1, duplicate_cue)
        for sequence, event in enumerate(self.events, 1):
            event["sequence"] = sequence
            event["monotonic_ms"] = 1000 + sequence * 100
            event["frame"] = sequence * 10
        self.write_inputs()
        stream, _ = reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)
        with self.assertRaises(reader.ReaderError):
            reader.reconstruct_timeline(stream)

    def test_prepare_acceptance_attaches_refs_without_verdict(self):
        stream, _ = reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)
        timeline, _ = reader.reconstruct_timeline(stream)
        kernels = self.acceptance_kernels()
        prepared = reader.prepare_acceptance_input([timeline], kernels)
        self.assertIsNone(prepared["verdict"])
        self.assertEqual("COMPLETE_FOR_DECLARED_SELECTORS", prepared["kernels"][0]["evidence_availability"])
        run_result = prepared["kernels"][0]["run_results"][0]
        self.assertEqual("COMPLETE", run_result["chain_status"])
        self.assertEqual("door-try-1", run_result["complete_chains"][0]["correlation_id"])
        self.assertEqual(
            [1, 2, 3, 4],
            [
                run_result["complete_chains"][0]["phases"][phase]["sequence"]
                for phase in reader.POSITIVE_CHAIN_PHASES
            ],
        )

    def test_acceptance_does_not_stitch_four_runs_into_one_chain(self):
        complete = self.complete_chain_events()
        for event in complete:
            event["correlation_id"] = None
            event["correlation_role"] = None
        timelines = [
            self.acceptance_timeline(run_id=f"run-{index}", events=[event])
            for index, event in enumerate(complete, 1)
        ]
        prepared = reader.prepare_acceptance_input(timelines, self.acceptance_kernels())
        kernel = prepared["kernels"][0]
        self.assertEqual("INCOMPLETE", kernel["evidence_availability"])
        self.assertTrue(all(result["chain_status"] == "INCOMPLETE" for result in kernel["run_results"]))

    def test_acceptance_rejects_wrong_phase_order_in_one_run(self):
        events = [
            self.acceptance_event("cue", 1, "cue", "chain-1"),
            self.acceptance_event("response", 2, "world_response", "chain-1"),
            self.acceptance_event("action", 3, "player_input", "chain-1"),
            self.acceptance_event("carry", 4, "state_change"),
        ]
        with self.assertRaises(reader.ReaderError):
            reader.prepare_acceptance_input(
                [self.acceptance_timeline(events=events)],
                self.acceptance_kernels(),
            )

    def test_acceptance_rejects_time_reversal_even_when_sequence_increases(self):
        events = self.complete_chain_events()
        events[1]["elapsed_ms"] = 300
        events[2]["elapsed_ms"] = 200
        with self.assertRaises(reader.ReaderError):
            reader.prepare_acceptance_input(
                [self.acceptance_timeline(run_id="run-time-reversal", events=events)],
                self.acceptance_kernels(),
            )

    def test_acceptance_rejects_different_correlation_ids(self):
        events = [
            self.acceptance_event("cue-a", 1, "cue", "chain-a"),
            self.acceptance_event("action-a", 2, "player_input", "chain-a"),
            self.acceptance_event("response-a", 3, "world_response", "chain-a"),
            self.acceptance_event("cue-b", 4, "cue", "chain-b"),
            self.acceptance_event("action-b", 5, "player_input", "chain-b"),
            self.acceptance_event("response-b", 6, "world_response", "chain-b"),
            self.acceptance_event("cue-c", 7, "cue", "chain-c"),
            self.acceptance_event("action-c", 8, "player_input", "chain-c"),
            self.acceptance_event("response-c", 9, "world_response", "chain-c"),
            self.acceptance_event("carry", 10, "state_change"),
        ]
        kernels = self.acceptance_kernels()
        matches = kernels["kernels"][0]["selectors"]
        matches[0]["match"] = {"event_id": "cue-a"}
        matches[1]["match"] = {"event_id": "action-b"}
        matches[2]["match"] = {"event_id": "response-c"}
        matches[3]["match"] = {"event_id": "carry"}
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline(events=events)],
            kernels,
        )
        self.assertEqual("INCOMPLETE", prepared["kernels"][0]["evidence_availability"])

    def test_acceptance_requires_correlation_roles(self):
        events = self.complete_chain_events()
        for event in events[:3]:
            event["correlation_role"] = None
        with self.assertRaises(reader.ReaderError):
            reader.prepare_acceptance_input(
                [self.acceptance_timeline(run_id="roleless", events=events)],
                self.acceptance_kernels(),
            )

    def test_acceptance_requires_response_before_carry_forward(self):
        events = [
            self.acceptance_event("cue", 1, "cue", "chain-1"),
            self.acceptance_event("action", 2, "player_input", "chain-1"),
            self.acceptance_event("carry", 3, "state_change"),
            self.acceptance_event("response", 4, "world_response", "chain-1"),
        ]
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline(run_id="early-carry", events=events)],
            self.acceptance_kernels(),
        )
        self.assertEqual("INCOMPLETE", prepared["kernels"][0]["evidence_availability"])

    def test_acceptance_completes_legal_same_run_chain(self):
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline()],
            self.acceptance_kernels(),
        )
        kernel = prepared["kernels"][0]
        self.assertEqual("COMPLETE_FOR_DECLARED_SELECTORS", kernel["evidence_availability"])
        chain = kernel["run_results"][0]["complete_chains"][0]
        self.assertEqual({"run-a"}, {chain["phases"][phase]["run_id"] for phase in reader.POSITIVE_CHAIN_PHASES})
        self.assertEqual({"session-run-a"}, {chain["phases"][phase]["session_id"] for phase in reader.POSITIVE_CHAIN_PHASES})

    def test_ordered_sequence_missing_step_disqualifies_positive_chain(self):
        events = [
            self.acceptance_event("cue", 1, "cue", "chain-1"),
            self.acceptance_event("panel-open", 2, "presentation"),
            self.acceptance_event("action", 3, "player_input", "chain-1"),
            self.acceptance_event("response", 4, "world_response", "chain-1"),
            self.acceptance_event("carry", 5, "state_change"),
        ]
        ordered_sequence = self.ordered_sequence(
            "panel-cycle",
            "cue",
            "action_or_attempt",
            [{"event_id": "panel-open"}, {"event_id": "panel-close"}],
        )
        kernels = self.acceptance_kernels(
            negative_match={"observable": {"forbidden": True}},
            ordered_sequences=[ordered_sequence],
        )
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline(events=events)],
            kernels,
        )
        run_result = prepared["kernels"][0]["run_results"][0]
        self.assertEqual(1, run_result["positive_phase_chain_count"])
        self.assertEqual("INCOMPLETE", run_result["chain_status"])
        self.assertEqual("ORDERED_SEQUENCE_REQUIREMENTS_UNSATISFIED", run_result["chain_incomplete_reason"])
        sequence_result = run_result["incomplete_chains"][0]["ordered_sequences"][0]
        self.assertEqual("INCOMPLETE", sequence_result["status"])
        self.assertEqual("MISSING_MATCH", sequence_result["reason"])
        self.assertEqual(1, sequence_result["failed_step_index"])
        self.assertEqual([], run_result["negative_checks"][0]["windows"])
        self.assertEqual("INCONCLUSIVE_COVERAGE", run_result["negative_checks"][0]["status"])

    def test_ordered_sequence_reordered_steps_are_incomplete(self):
        events = [
            self.acceptance_event("cue", 1, "cue", "chain-1"),
            self.acceptance_event("second", 2, "presentation"),
            self.acceptance_event("first", 3, "presentation"),
            self.acceptance_event("action", 4, "player_input", "chain-1"),
            self.acceptance_event("response", 5, "world_response", "chain-1"),
            self.acceptance_event("carry", 6, "state_change"),
        ]
        ordered_sequence = self.ordered_sequence(
            "ordered-presentation",
            "cue",
            "action_or_attempt",
            [{"event_id": "first"}, {"event_id": "second"}],
        )
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline(events=events)],
            self.acceptance_kernels(ordered_sequences=[ordered_sequence]),
        )
        sequence_result = prepared["kernels"][0]["run_results"][0]["incomplete_chains"][0][
            "ordered_sequences"
        ][0]
        self.assertEqual("ORDER_VIOLATION", sequence_result["reason"])
        self.assertEqual(1, sequence_result["failed_step_index"])

    def test_ordered_sequence_event_outside_phase_boundaries_does_not_count(self):
        events = [
            self.acceptance_event("panel-open", 1, "presentation"),
            self.acceptance_event("cue", 2, "cue", "chain-1"),
            self.acceptance_event("action", 3, "player_input", "chain-1"),
            self.acceptance_event("response", 4, "world_response", "chain-1"),
            self.acceptance_event("carry", 5, "state_change"),
        ]
        ordered_sequence = self.ordered_sequence(
            "bounded-panel-open",
            "cue",
            "action_or_attempt",
            [{"event_id": "panel-open"}],
        )
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline(events=events)],
            self.acceptance_kernels(ordered_sequences=[ordered_sequence]),
        )
        sequence_result = prepared["kernels"][0]["run_results"][0]["incomplete_chains"][0][
            "ordered_sequences"
        ][0]
        self.assertEqual("OUTSIDE_BOUNDARY_ONLY", sequence_result["reason"])
        outside_refs = sequence_result["steps"][0]["outside_boundary_candidate_refs"]
        self.assertEqual(["panel-open"], [evidence_ref["event_id"] for evidence_ref in outside_refs])

    def test_ordered_sequence_does_not_mix_steps_across_runs(self):
        run_a_events = [
            self.acceptance_event("cue-a", 1, "cue", "chain-a"),
            self.acceptance_event("first", 2, "presentation"),
            self.acceptance_event("action-a", 3, "player_input", "chain-a"),
            self.acceptance_event("response-a", 4, "world_response", "chain-a"),
            self.acceptance_event("carry-a", 5, "state_change"),
        ]
        run_b_events = [
            self.acceptance_event("cue-b", 1, "cue", "chain-b"),
            self.acceptance_event("second", 2, "presentation"),
            self.acceptance_event("action-b", 3, "player_input", "chain-b"),
            self.acceptance_event("response-b", 4, "world_response", "chain-b"),
            self.acceptance_event("carry-b", 5, "state_change"),
        ]
        ordered_sequence = self.ordered_sequence(
            "two-run-trap",
            "cue",
            "action_or_attempt",
            [{"event_id": "first"}, {"event_id": "second"}],
        )
        prepared = reader.prepare_acceptance_input(
            [
                self.acceptance_timeline(run_id="run-a", events=run_a_events),
                self.acceptance_timeline(run_id="run-b", events=run_b_events),
            ],
            self.acceptance_kernels(ordered_sequences=[ordered_sequence]),
        )
        kernel = prepared["kernels"][0]
        self.assertEqual("INCOMPLETE", kernel["evidence_availability"])
        self.assertTrue(all(result["chain_status"] == "INCOMPLETE" for result in kernel["run_results"]))

    def test_ordered_sequence_cannot_reuse_one_event_for_two_steps(self):
        events = [
            self.acceptance_event("cue", 1, "cue", "chain-1"),
            self.acceptance_event("only-close", 2, "gameplay_action", None, {"panel": "closed"}),
            self.acceptance_event("action", 3, "player_input", "chain-1"),
            self.acceptance_event("response", 4, "world_response", "chain-1"),
            self.acceptance_event("carry", 5, "state_change"),
        ]
        ordered_sequence = self.ordered_sequence(
            "two-closes",
            "cue",
            "action_or_attempt",
            [
                {"event_kind": "gameplay_action", "observable": {"panel": "closed"}},
                {"event_kind": "gameplay_action", "observable": {"panel": "closed"}},
            ],
        )
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline(events=events)],
            self.acceptance_kernels(ordered_sequences=[ordered_sequence]),
        )
        sequence_result = prepared["kernels"][0]["run_results"][0]["incomplete_chains"][0][
            "ordered_sequences"
        ][0]
        self.assertEqual("EVENT_REUSE_REQUIRED", sequence_result["reason"])

    def test_overlapping_ordered_sequences_cannot_share_one_event(self):
        events = [
            self.acceptance_event("cue", 1, "cue", "chain-1"),
            self.acceptance_event("control-return", 2, "control", None, {"owner": "player"}),
            self.acceptance_event("action", 3, "player_input", "chain-1"),
            self.acceptance_event("response", 4, "world_response", "chain-1"),
            self.acceptance_event("carry", 5, "state_change"),
        ]
        ordered_sequences = [
            self.ordered_sequence(
                "control-proof-a",
                "cue",
                "action_or_attempt",
                [{"event_kind": "control", "observable": {"owner": "player"}}],
            ),
            self.ordered_sequence(
                "control-proof-b",
                "cue",
                "action_or_attempt",
                [{"event_kind": "control", "observable": {"owner": "player"}}],
            ),
        ]
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline(events=events)],
            self.acceptance_kernels(ordered_sequences=ordered_sequences),
        )
        incomplete_chain = prepared["kernels"][0]["run_results"][0]["incomplete_chains"][0]
        self.assertEqual("ORDERED_SEQUENCE_EVENT_REUSE_CONFLICT", incomplete_chain["incomplete_reason"])
        self.assertEqual(
            {"EVENT_REUSE_CONFLICT_ACROSS_SEQUENCES"},
            {sequence["reason"] for sequence in incomplete_chain["ordered_sequences"]},
        )

    def test_ordered_sequence_allows_unrelated_extra_events(self):
        events = [
            self.acceptance_event("cue", 1, "cue", "chain-1"),
            self.acceptance_event("first", 2, "presentation"),
            self.acceptance_event("unrelated", 3, "performance", None, {"fps": 60}),
            self.acceptance_event("second", 4, "control"),
            self.acceptance_event("action", 5, "player_input", "chain-1"),
            self.acceptance_event("response", 6, "world_response", "chain-1"),
            self.acceptance_event("carry", 7, "state_change"),
        ]
        ordered_sequence = self.ordered_sequence(
            "extra-tolerant",
            "cue",
            "action_or_attempt",
            [{"event_id": "first"}, {"event_id": "second"}],
        )
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline(events=events)],
            self.acceptance_kernels(ordered_sequences=[ordered_sequence]),
        )
        chain = prepared["kernels"][0]["run_results"][0]["complete_chains"][0]
        evidence_refs = chain["ordered_sequences"][0]["steps"]
        self.assertEqual(["first", "second"], [step["evidence_ref"]["event_id"] for step in evidence_refs])

    def test_branch_positive_phases_do_not_complete_when_sequence_fails(self):
        branch_a_events = [
            self.acceptance_event("cue-a", 1, "cue", "chain-a"),
            self.acceptance_event("action-a", 2, "player_input", "chain-a", {"input": "primary"}),
            self.acceptance_event("response-a", 3, "world_response", "chain-a"),
            self.acceptance_event("control-a", 4, "control", None, {"owner": "player"}),
            self.acceptance_event("carry-a", 5, "state_change"),
        ]
        branch_b_events = [
            self.acceptance_event("cue-b", 1, "cue", "chain-b"),
            self.acceptance_event("action-b", 2, "player_input", "chain-b", {"input": "alternate"}),
            self.acceptance_event("response-b", 3, "world_response", "chain-b"),
            self.acceptance_event("carry-b", 4, "state_change"),
        ]
        ordered_sequence = self.ordered_sequence(
            "control-return",
            "world_response",
            "carry_forward",
            [{"event_kind": "control", "observable": {"owner": "player"}}],
        )
        prepared = reader.prepare_acceptance_input(
            [
                self.acceptance_timeline(
                    run_id="branch-a-run",
                    evidence_mode="CONTROLLED_BRANCH_PROBE",
                    branch_label="branch-a",
                    events=branch_a_events,
                ),
                self.acceptance_timeline(
                    run_id="branch-b-run",
                    evidence_mode="CONTROLLED_BRANCH_PROBE",
                    branch_label="branch-b",
                    events=branch_b_events,
                ),
            ],
            self.acceptance_kernels(
                required_modes=["CONTROLLED_BRANCH_PROBE"],
                ordered_sequences=[ordered_sequence],
            ),
        )
        kernel = prepared["kernels"][0]
        self.assertEqual("INCOMPLETE", kernel["evidence_availability"])
        group = kernel["branch_probe_groups"][0]
        self.assertEqual("INCOMPLETE", group["status"])
        branch_statuses = {branch["branch_label"]: branch["status"] for branch in group["branches"]}
        self.assertEqual({"branch-a": "COMPLETE", "branch-b": "INCOMPLETE"}, branch_statuses)

    def test_avg_presentation_close_and_control_return_sequence_completes(self):
        events = [
            self.acceptance_event("avg-cue", 1, "cue", "avg-route"),
            self.acceptance_event("line-1", 2, "presentation", None, {"avg": {"line": 1}}),
            self.acceptance_event("advance-1", 3, "gameplay_action", None, {"avg": {"advance": 1}}),
            self.acceptance_event("line-2", 4, "presentation", None, {"avg": {"line": 2}}),
            self.acceptance_event("avg-close", 5, "presentation", None, {"avg": {"open": False}}),
            self.acceptance_event("hud-return", 6, "control", None, {"owner": "player", "hud": "visible"}),
            self.acceptance_event("route-action", 7, "player_input", "avg-route"),
            self.acceptance_event("route-response", 8, "world_response", "avg-route"),
            self.acceptance_event("route-carry", 9, "state_change"),
        ]
        ordered_sequence = self.ordered_sequence(
            "avg-close-before-route",
            "cue",
            "action_or_attempt",
            [
                {"event_kind": "presentation", "observable": {"avg": {"line": 1}}},
                {"event_kind": "gameplay_action", "observable": {"avg": {"advance": 1}}},
                {"event_kind": "presentation", "observable": {"avg": {"line": 2}}},
                {"event_kind": "presentation", "observable": {"avg": {"open": False}}},
                {"event_kind": "control", "observable": {"owner": "player", "hud": "visible"}},
            ],
        )
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline(run_id="avg-run", events=events)],
            self.acceptance_kernels(ordered_sequences=[ordered_sequence]),
        )
        sequence_result = prepared["kernels"][0]["run_results"][0]["complete_chains"][0][
            "ordered_sequences"
        ][0]
        self.assertEqual("COMPLETE", sequence_result["status"])
        self.assertEqual([2, 3, 4, 5, 6], [step["evidence_ref"]["sequence"] for step in sequence_result["steps"]])

    def test_cache_close_reopen_snapshot_and_final_close_sequence_completes(self):
        events = [
            self.acceptance_event("cache-cue", 1, "cue", "cache-route"),
            self.acceptance_event("cache-action", 2, "player_input", "cache-route"),
            self.acceptance_event("cache-response", 3, "world_response", "cache-route"),
            self.acceptance_event("cache-result", 4, "presentation", None, {"cache": {"result": "shown"}}),
            self.acceptance_event("first-close", 5, "gameplay_action", None, {"cache": {"close": 1}}),
            self.acceptance_event("control-return", 6, "control", None, {"owner": "player"}),
            self.acceptance_event("reopen", 7, "gameplay_action", None, {"cache": {"reopen": True}}),
            self.acceptance_event("snapshot", 8, "capture", None, {"cache": {"snapshot": "reopened"}}),
            self.acceptance_event("final-close", 9, "gameplay_action", None, {"cache": {"close": 2}}),
            self.acceptance_event("cache-carry", 10, "state_change"),
        ]
        ordered_sequence = self.ordered_sequence(
            "cache-reopen-proof",
            "world_response",
            "carry_forward",
            [
                {"observable": {"cache": {"result": "shown"}}},
                {"observable": {"cache": {"close": 1}}},
                {"event_kind": "control", "observable": {"owner": "player"}},
                {"observable": {"cache": {"reopen": True}}},
                {"event_kind": "capture", "observable": {"cache": {"snapshot": "reopened"}}},
                {"observable": {"cache": {"close": 2}}},
            ],
        )
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline(run_id="cache-run", events=events)],
            self.acceptance_kernels(ordered_sequences=[ordered_sequence]),
        )
        kernel = prepared["kernels"][0]
        self.assertEqual("COMPLETE_FOR_DECLARED_SELECTORS", kernel["evidence_availability"])
        steps = kernel["run_results"][0]["complete_chains"][0]["ordered_sequences"][0]["steps"]
        self.assertEqual(
            ["cache-result", "first-close", "control-return", "reopen", "snapshot", "final-close"],
            [step["evidence_ref"]["event_id"] for step in steps],
        )

    def test_single_branch_probe_is_incomplete(self):
        timeline = self.acceptance_timeline(
            run_id="branch-a-run",
            evidence_mode="CONTROLLED_BRANCH_PROBE",
            branch_label="branch-a",
        )
        prepared = reader.prepare_acceptance_input(
            [timeline],
            self.acceptance_kernels(["CONTROLLED_BRANCH_PROBE"]),
        )
        kernel = prepared["kernels"][0]
        self.assertEqual("INCOMPLETE", kernel["evidence_availability"])
        self.assertEqual("INCOMPLETE", kernel["branch_probe_groups"][0]["status"])

    def test_controlled_probe_mode_requires_non_empty_unique_group_bindings(self):
        missing = self.acceptance_kernels(["CONTROLLED_BRANCH_PROBE"])
        del missing["kernels"][0]["controlled_probe_group_ids"]

        empty = self.acceptance_kernels(
            ["CONTROLLED_BRANCH_PROBE"],
            controlled_probe_group_ids=[],
        )
        duplicate = self.acceptance_kernels(
            ["CONTROLLED_BRANCH_PROBE"],
            controlled_probe_group_ids=["probe-group-1", "probe-group-1"],
        )
        blank = self.acceptance_kernels(
            ["CONTROLLED_BRANCH_PROBE"],
            controlled_probe_group_ids=[""],
        )

        for invalid_kernels in (missing, empty, duplicate, blank):
            with self.subTest(kernel=invalid_kernels["kernels"][0]):
                with self.assertRaises(reader.ReaderError):
                    reader.prepare_acceptance_input(
                        [
                            self.acceptance_timeline(
                                evidence_mode="CONTROLLED_BRANCH_PROBE",
                                branch_label="branch-a",
                            )
                        ],
                        invalid_kernels,
                    )

    def test_non_controlled_mode_rejects_probe_group_bindings(self):
        kernels = self.acceptance_kernels(
            ["RECORDED_RUN"],
            controlled_probe_group_ids=["unexpected-group"],
        )
        with self.assertRaises(reader.ReaderError):
            reader.prepare_acceptance_input(
                [self.acceptance_timeline(evidence_mode="RECORDED_RUN")],
                kernels,
            )

    def test_different_branch_labels_with_identical_evidence_are_incomplete(self):
        timelines = [
            self.acceptance_timeline(
                run_id="branch-a-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="branch-a",
            ),
            self.acceptance_timeline(
                run_id="branch-b-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="branch-b",
            ),
        ]
        prepared = reader.prepare_acceptance_input(
            timelines,
            self.acceptance_kernels(["CONTROLLED_BRANCH_PROBE"]),
        )
        group = prepared["kernels"][0]["branch_probe_groups"][0]
        self.assertEqual("INCOMPLETE", group["status"])
        self.assertFalse(group["branch_evidence_distinct"])

    def test_two_environment_matched_branch_probes_are_complete(self):
        branch_b_events = self.complete_chain_events()
        branch_b_events[1]["observable"] = {"input": "alternate"}
        branch_b_events[2]["observable"] = {"result": "alternate-open"}
        branch_b_events[3]["observable"] = {"path": "alternate-route"}
        timelines = [
            self.acceptance_timeline(
                run_id="branch-a-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="branch-a",
            ),
            self.acceptance_timeline(
                run_id="branch-b-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="branch-b",
                events=branch_b_events,
            ),
        ]
        prepared = reader.prepare_acceptance_input(
            timelines,
            self.acceptance_kernels(["CONTROLLED_BRANCH_PROBE"]),
        )
        kernel = prepared["kernels"][0]
        self.assertEqual("COMPLETE_FOR_DECLARED_SELECTORS", kernel["evidence_availability"])
        group = kernel["branch_probe_groups"][0]
        self.assertEqual("COMPLETE", group["status"])
        self.assertTrue(group["environment_consistent"])
        self.assertTrue(group["branch_evidence_distinct"])
        self.assertTrue(group["branch_consequence_evidence_distinct"])
        self.assertEqual(["branch-a", "branch-b"], group["distinct_branch_labels"])

    def test_different_actions_without_distinct_consequences_do_not_prove_decision(self):
        branch_b_events = self.complete_chain_events()
        branch_b_events[1]["observable"] = {"input": "alternate"}
        timelines = [
            self.acceptance_timeline(
                run_id="branch-a-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="branch-a",
            ),
            self.acceptance_timeline(
                run_id="branch-b-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="branch-b",
                events=branch_b_events,
            ),
        ]
        prepared = reader.prepare_acceptance_input(
            timelines,
            self.acceptance_kernels(["CONTROLLED_BRANCH_PROBE"]),
        )
        group = prepared["kernels"][0]["branch_probe_groups"][0]
        self.assertEqual("INCOMPLETE", group["status"])
        self.assertTrue(group["branch_evidence_distinct"])
        self.assertFalse(group["branch_consequence_evidence_distinct"])

    def test_shared_phase_contamination_does_not_attach_undeclared_probe_group(self):
        kernels = self.acceptance_kernels(
            ["CONTROLLED_BRANCH_PROBE"],
            controlled_probe_group_ids=["route-group"],
        )
        selectors = kernels["kernels"][0]["selectors"]
        selectors[1]["match"]["observable"] = {"kernel_surface": "route"}
        selectors[2]["match"]["observable"] = {"kernel_surface": "route"}

        timelines = [
            self.acceptance_timeline(
                run_id="route-a-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="route-a",
                group_id="route-group",
                events=self.kernel_specific_chain_events("route", "marked"),
            ),
            self.acceptance_timeline(
                run_id="route-b-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="route-b",
                group_id="route-group",
                events=self.kernel_specific_chain_events("route", "detour"),
            ),
            self.acceptance_timeline(
                run_id="cache-a-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="cache-a",
                group_id="cache-group",
                events=self.kernel_specific_chain_events("cache", "use"),
            ),
            self.acceptance_timeline(
                run_id="cache-b-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="cache-b",
                group_id="cache-group",
                events=self.kernel_specific_chain_events("cache", "preserve"),
            ),
        ]

        prepared = reader.prepare_acceptance_input(timelines, kernels)
        probe_groups = prepared["kernels"][0]["branch_probe_groups"]
        self.assertEqual(["route-group"], [group["probe_group"] for group in probe_groups])

    def test_declared_but_absent_probe_group_fails_closed(self):
        kernels = self.acceptance_kernels(
            ["CONTROLLED_BRANCH_PROBE"],
            controlled_probe_group_ids=["present-group", "declared-missing-group"],
        )
        timelines = [
            self.acceptance_timeline(
                run_id="present-a-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="present-a",
                group_id="present-group",
                events=self.kernel_specific_chain_events("route", "marked"),
            ),
            self.acceptance_timeline(
                run_id="present-b-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="present-b",
                group_id="present-group",
                events=self.kernel_specific_chain_events("route", "detour"),
            ),
        ]

        prepared = reader.prepare_acceptance_input(timelines, kernels)
        kernel = prepared["kernels"][0]
        self.assertEqual("INCOMPLETE", kernel["evidence_availability"])
        self.assertEqual(["present-group", "declared-missing-group"], [
            group["probe_group"]
            for group in kernel["branch_probe_groups"]
        ])
        self.assertEqual("COMPLETE", kernel["branch_probe_groups"][0]["status"])
        missing_group = kernel["branch_probe_groups"][1]
        self.assertEqual("INCOMPLETE", missing_group["status"])
        self.assertFalse(missing_group["declared_group_present"])
        self.assertEqual([], missing_group["branches"])

    def test_non_controlled_kernel_reports_no_probe_groups(self):
        kernels = self.acceptance_kernels(["RECORDED_RUN"])
        timelines = [
            self.acceptance_timeline(
                run_id="recorded-run",
                evidence_mode="RECORDED_RUN",
            ),
            self.acceptance_timeline(
                run_id="controlled-a-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="controlled-a",
                group_id="controlled-group",
            ),
            self.acceptance_timeline(
                run_id="controlled-b-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="controlled-b",
                group_id="controlled-group",
                events=self.kernel_specific_chain_events("route", "alternate"),
            ),
        ]

        prepared = reader.prepare_acceptance_input(timelines, kernels)
        kernel = prepared["kernels"][0]
        self.assertEqual("COMPLETE_FOR_DECLARED_SELECTORS", kernel["evidence_availability"])
        self.assertEqual([], kernel["branch_probe_groups"])
        self.assertNotIn(
            "CONTROLLED_BRANCH_PROBE",
            {coverage["evidence_mode"] for coverage in kernel["mode_coverage"]},
        )

    def test_declared_probe_group_with_one_missing_branch_chain_is_incomplete(self):
        kernels = self.acceptance_kernels(
            ["CONTROLLED_BRANCH_PROBE"],
            controlled_probe_group_ids=["one-sided-group"],
        )
        for selector in kernels["kernels"][0]["selectors"]:
            selector["match"]["observable"] = {"kernel_surface": "route"}

        timelines = [
            self.acceptance_timeline(
                run_id="route-matching-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="matching",
                group_id="one-sided-group",
                events=self.kernel_specific_chain_events("route", "marked"),
            ),
            self.acceptance_timeline(
                run_id="route-missing-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="missing",
                group_id="one-sided-group",
                events=self.kernel_specific_chain_events("cache", "unrelated"),
            ),
        ]

        prepared = reader.prepare_acceptance_input(timelines, kernels)
        kernel = prepared["kernels"][0]
        self.assertEqual("INCOMPLETE", kernel["evidence_availability"])
        self.assertEqual(1, len(kernel["branch_probe_groups"]))
        group = kernel["branch_probe_groups"][0]
        self.assertEqual("INCOMPLETE", group["status"])
        branch_statuses = {
            branch["branch_label"]: branch["status"]
            for branch in group["branches"]
        }
        self.assertEqual({"matching": "COMPLETE", "missing": "INCOMPLETE"}, branch_statuses)

    def test_complete_declared_probe_group_passes_and_undeclared_group_is_omitted(self):
        kernels = self.acceptance_kernels(
            ["CONTROLLED_BRANCH_PROBE"],
            controlled_probe_group_ids=["relevant-group"],
        )
        for selector in kernels["kernels"][0]["selectors"]:
            selector["match"]["observable"] = {"kernel_surface": "route"}

        timelines = [
            self.acceptance_timeline(
                run_id="relevant-a-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="relevant-a",
                group_id="relevant-group",
                events=self.kernel_specific_chain_events("route", "marked"),
            ),
            self.acceptance_timeline(
                run_id="relevant-b-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="relevant-b",
                group_id="relevant-group",
                events=self.kernel_specific_chain_events("route", "detour"),
            ),
            self.acceptance_timeline(
                run_id="unrelated-a-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="unrelated-a",
                group_id="unrelated-group",
                events=self.kernel_specific_chain_events("cache", "use"),
            ),
            self.acceptance_timeline(
                run_id="unrelated-b-run",
                evidence_mode="CONTROLLED_BRANCH_PROBE",
                branch_label="unrelated-b",
                group_id="unrelated-group",
                events=self.kernel_specific_chain_events("cache", "preserve"),
            ),
        ]

        prepared = reader.prepare_acceptance_input(timelines, kernels)
        kernel = prepared["kernels"][0]
        self.assertEqual("COMPLETE_FOR_DECLARED_SELECTORS", kernel["evidence_availability"])
        self.assertEqual(["relevant-group"], [
            group["probe_group"]
            for group in kernel["branch_probe_groups"]
        ])
        self.assertEqual("COMPLETE", kernel["branch_probe_groups"][0]["status"])

    def test_branch_probes_with_different_setup_are_incomplete(self):
        branch_a = self.acceptance_timeline(
            run_id="branch-a-run",
            evidence_mode="CONTROLLED_BRANCH_PROBE",
            branch_label="branch-a",
        )
        branch_b = self.acceptance_timeline(
            run_id="branch-b-run",
            evidence_mode="CONTROLLED_BRANCH_PROBE",
            branch_label="branch-b",
        )
        branch_b["run"]["setup"]["seed"] = 99
        prepared = reader.prepare_acceptance_input(
            [branch_a, branch_b],
            self.acceptance_kernels(["CONTROLLED_BRANCH_PROBE"]),
        )
        group = prepared["kernels"][0]["branch_probe_groups"][0]
        self.assertEqual("INCOMPLETE", group["status"])
        self.assertFalse(group["environment_consistent"])

    def test_branch_probes_from_different_probe_groups_do_not_combine(self):
        branch_a = self.acceptance_timeline(
            run_id="branch-a-run",
            evidence_mode="CONTROLLED_BRANCH_PROBE",
            branch_label="branch-a",
            group_id="group-a",
        )
        branch_b = self.acceptance_timeline(
            run_id="branch-b-run",
            evidence_mode="CONTROLLED_BRANCH_PROBE",
            branch_label="branch-b",
            group_id="group-b",
        )
        prepared = reader.prepare_acceptance_input(
            [branch_a, branch_b],
            self.acceptance_kernels(
                ["CONTROLLED_BRANCH_PROBE"],
                controlled_probe_group_ids=["group-a", "group-b"],
            ),
        )
        kernel = prepared["kernels"][0]
        self.assertEqual("INCOMPLETE", kernel["evidence_availability"])
        self.assertEqual(["INCOMPLETE", "INCOMPLETE"], [group["status"] for group in kernel["branch_probe_groups"]])

    def test_observable_hidden_component_prefix_overlap_is_rejected(self):
        cases = [
            (
                [{"source": "payload", "target": "visible"}],
                [{"source": "payload.state", "target": "private"}],
            ),
            (
                [{"source": "payload.state.secret", "target": "visible"}],
                [{"source": "payload.state", "target": "private"}],
            ),
            (
                [{"source": "payload.observable", "target": "data"}],
                [{"source": "payload.state", "target": "data.secret"}],
            ),
        ]
        for observable, hidden in cases:
            with self.subTest(observable=observable, hidden=hidden):
                mapping = copy.deepcopy(self.mapping)
                mapping["observable_fields"] = observable
                mapping["hidden_fields"] = hidden
                with self.assertRaises(reader.ReaderError):
                    reader._validate_mapping(mapping, self.events)

    def test_blind_output_contains_no_semantic_event_role(self):
        stream, _ = reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)
        timeline, _ = reader.reconstruct_timeline(stream)
        blind = reader.build_blind_projection(timeline)
        serialized_payloads = json.dumps(blind["payloads"], sort_keys=True)
        for key in ("kind", "cue", "world_response", "correlation_role", "semantic_role"):
            self.assertNotIn(f'"{key}"', serialized_payloads)
        self.assertEqual("visual", blind["payloads"][0]["observation_channel"])
        self.assertEqual(["capture_000001"], blind["payloads"][0]["capture_refs"])

    def test_semantic_runtime_observation_channel_is_rejected(self):
        self.events[0]["payload"]["channel"] = "cue"
        self.write_inputs()
        with self.assertRaises(reader.ReaderError):
            reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)

    def test_observable_mapping_cannot_smuggle_semantic_event_type(self):
        self.mapping["observable_fields"].append({"source": "event_type", "target": "label"})
        self.write_inputs()
        with self.assertRaises(reader.ReaderError):
            reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)

    def test_observable_mapping_cannot_smuggle_capture_paths(self):
        self.mapping["observable_fields"].append({"source": "capture_refs", "target": "assets"})
        self.write_inputs()
        with self.assertRaises(reader.ReaderError):
            reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)

    def test_blind_aliases_preserve_private_evidence_traceability(self):
        stream, _ = reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)
        timeline, _ = reader.reconstruct_timeline(stream)
        blind = reader.build_blind_projection(timeline)
        first = blind["payloads"][0]
        self.assertEqual("evidence_000001", first["evidence_ref"])
        self.assertEqual(["capture_000001"], first["capture_refs"])
        private = blind["private_facilitator_metadata"]
        self.assertEqual("captures/frame-001.png", private["capture_aliases"]["capture_000001"])
        self.assertEqual(
            {"path": "events.jsonl", "line": 1, "source_event_id": "ev-1"},
            private["evidence_aliases"]["evidence_000001"]["raw_ref"],
        )

    def test_known_capture_path_in_public_data_is_replaced_by_alias(self):
        self.events[0]["context"]["scene_id"] = "captures/frame-001.png"
        self.write_inputs()
        stream, _ = reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)
        timeline, _ = reader.reconstruct_timeline(stream)
        blind = reader.build_blind_projection(timeline)
        self.assertEqual("capture_000001", blind["payloads"][0]["public_context"]["scene_id"])
        self.assertNotIn("captures/frame-001.png", json.dumps(blind["payloads"]))

    def test_negative_check_reports_satisfied_violation_and_inconclusive(self):
        kernels = self.acceptance_kernels(negative_match={"observable": {"forbidden": True}})

        satisfied = reader.prepare_acceptance_input(
            [self.acceptance_timeline(observation_complete=True)], kernels
        )
        satisfied_status = satisfied["kernels"][0]["run_results"][0]["negative_checks"][0]["status"]
        self.assertEqual("SATISFIED_NO_MATCH", satisfied_status)

        violation_events = [
            self.acceptance_event("cue", 1, "cue", "chain-1"),
            self.acceptance_event("action", 2, "player_input", "chain-1"),
            self.acceptance_event("forbidden", 3, "presentation", None, {"forbidden": True}),
            self.acceptance_event("response", 4, "world_response", "chain-1"),
            self.acceptance_event("carry", 5, "state_change"),
        ]
        violation = reader.prepare_acceptance_input(
            [
                self.acceptance_timeline(
                    run_id="run-violation",
                    events=violation_events,
                    observation_complete=True,
                )
            ],
            kernels,
        )
        violation_check = violation["kernels"][0]["run_results"][0]["negative_checks"][0]
        self.assertEqual("VIOLATION_MATCH_FOUND", violation_check["status"])
        self.assertEqual("forbidden", violation_check["forbidden_evidence_refs"][0]["event_id"])

        incomplete_events = self.complete_chain_events()[:-1]
        inconclusive = reader.prepare_acceptance_input(
            [self.acceptance_timeline(run_id="run-incomplete", events=incomplete_events)],
            kernels,
        )
        inconclusive_status = inconclusive["kernels"][0]["run_results"][0]["negative_checks"][0]["status"]
        self.assertEqual("INCONCLUSIVE_COVERAGE", inconclusive_status)

    def test_negative_absence_without_explicit_complete_window_is_inconclusive(self):
        kernels = self.acceptance_kernels(negative_match={"observable": {"forbidden": True}})
        prepared = reader.prepare_acceptance_input([self.acceptance_timeline()], kernels)
        check = prepared["kernels"][0]["run_results"][0]["negative_checks"][0]
        self.assertEqual("INCONCLUSIVE_COVERAGE", check["status"])
        self.assertEqual("INCONCLUSIVE", check["windows"][0]["observation_coverage"])

    def test_declared_complete_observation_window_rejects_sequence_gap(self):
        self.manifest["observation_window"] = {
            "start_sequence": 1,
            "end_sequence": 4,
            "coverage_status": "COMPLETE",
            "coverage_basis": "logger flush marker",
        }
        self.events.pop(1)
        self.write_inputs()
        _, _, report = reader.validate_evidence(self.manifest_path, self.events_path)
        self.assertEqual("INCONCLUSIVE_EVIDENCE", report["status"])
        self.assertIn("OBSERVATION_WINDOW_INCOMPLETE", {item["code"] for item in report["findings"]})

    def test_reader_acceptance_output_never_emits_gameplay_verdict(self):
        prepared = reader.prepare_acceptance_input(
            [self.acceptance_timeline()],
            self.acceptance_kernels(),
        )
        serialized = json.dumps(prepared, sort_keys=True)
        for verdict in (
            "PASS_FACTORY_CONFORMANCE",
            "FAIL_IMPLEMENTATION_FIDELITY",
            "FAIL_RECEPTION",
            "FAIL_DESIGN",
            "HUMAN_PLAYTEST_ACCEPTED",
        ):
            self.assertNotIn(verdict, serialized)
        self.assertIsNone(prepared["verdict"])

    def test_reader_schemas_are_valid_json_and_encode_window_and_chain_constraints(self):
        schema_root = Path(reader.__file__).parent / "schemas"
        schemas = {
            path.name: json.loads(path.read_text(encoding="utf-8"))
            for path in schema_root.glob("*.schema.json")
        }
        self.assertIn("observation_window", schemas["raw_manifest.schema.json"]["properties"])
        kernel_schema = schemas["acceptance_kernels.schema.json"]["properties"]["kernels"]["items"]
        probe_group_ids = kernel_schema["properties"]["controlled_probe_group_ids"]
        self.assertEqual(1, probe_group_ids["minItems"])
        self.assertTrue(probe_group_ids["uniqueItems"])
        self.assertEqual(1, len(kernel_schema["allOf"]))
        selectors = kernel_schema["properties"]["selectors"]
        self.assertEqual(4, selectors["minItems"])
        self.assertEqual(4, len(selectors["allOf"]))
        ordered_sequences = schemas["acceptance_kernels.schema.json"]["properties"]["kernels"]["items"][
            "properties"
        ]["ordered_sequences"]
        ordered_sequence = ordered_sequences["items"]
        self.assertFalse(ordered_sequence["additionalProperties"])
        self.assertEqual(1, ordered_sequence["properties"]["matches"]["minItems"])
        self.assertEqual(3, len(ordered_sequence["allOf"]))
        budget_schema = schemas["experience_budget.schema.json"]
        required_counts = budget_schema["properties"]["thresholds"]["properties"][
            "content_counts"
        ]["required"]
        self.assertEqual(
            {
                "complete_gameplay_beats",
                "meaningful_decisions",
                "combat_encounters",
                "world_interactions",
                "narrative_presentations",
            },
            set(required_counts),
        )
        self.assertIn(
            "minimum_player_control_ratio",
            budget_schema["properties"]["thresholds"]["required"],
        )
        exact_span_schema = budget_schema["properties"]["exact_span"]
        self.assertEqual(
            {"start_boundary", "end_boundary"},
            set(exact_span_schema["required"]),
        )
        self.assertNotIn("measurement_run_id", exact_span_schema["properties"])
        self.assertNotIn("measurement_session_id", exact_span_schema["properties"])
        categories_schema = budget_schema["properties"]["gameplay_measurements"]["items"][
            "properties"
        ]["categories"]
        self.assertEqual(2, categories_schema["maxItems"])
        activity_types = budget_schema["properties"]["non_gameplay_activity_selectors"][
            "items"
        ]["properties"]["activity_type"]["enum"]
        self.assertIn("control_transition", activity_types)
        self.assertIn("control_return", activity_types)

    def test_ordered_sequence_kernel_validation_rejects_invalid_contracts(self):
        valid_sequence = self.ordered_sequence(
            "valid-sequence",
            "cue",
            "action_or_attempt",
            [{"event_kind": "presentation"}],
        )
        invalid_sequences = []

        unknown_field = copy.deepcopy(valid_sequence)
        unknown_field["unexpected"] = True
        invalid_sequences.append(unknown_field)

        reversed_boundaries = copy.deepcopy(valid_sequence)
        reversed_boundaries["after_phase"] = "world_response"
        reversed_boundaries["before_phase"] = "action_or_attempt"
        invalid_sequences.append(reversed_boundaries)

        equal_boundaries = copy.deepcopy(valid_sequence)
        equal_boundaries["after_phase"] = "world_response"
        equal_boundaries["before_phase"] = "world_response"
        invalid_sequences.append(equal_boundaries)

        empty_matches = copy.deepcopy(valid_sequence)
        empty_matches["matches"] = []
        invalid_sequences.append(empty_matches)

        bad_match_grammar = copy.deepcopy(valid_sequence)
        bad_match_grammar["matches"] = [{"match": {"semantic_role": "close"}}]
        invalid_sequences.append(bad_match_grammar)

        bad_match_step = copy.deepcopy(valid_sequence)
        bad_match_step["matches"] = [{"match": {"event_kind": "presentation"}, "extra": True}]
        invalid_sequences.append(bad_match_step)

        for invalid_sequence in invalid_sequences:
            with self.subTest(invalid_sequence=invalid_sequence):
                with self.assertRaises(reader.ReaderError):
                    reader.prepare_acceptance_input(
                        [self.acceptance_timeline()],
                        self.acceptance_kernels(ordered_sequences=[invalid_sequence]),
                    )

    def test_run_command_writes_reference_outputs(self):
        output = self.root / "reader-output"
        with redirect_stdout(io.StringIO()):
            exit_code = reader.main(
                [
                    "run",
                    "--manifest",
                    str(self.manifest_path),
                    "--events",
                    str(self.events_path),
                    "--mapping",
                    str(self.mapping_path),
                    "--out-dir",
                    str(output),
                    "--game-repo",
                    str(self.root),
                ]
            )
        self.assertEqual(0, exit_code)
        self.assertEqual("PASS_INTEGRITY", json.loads((output / "INTEGRITY_REPORT.json").read_text())["status"])
        for name in (
            "CANONICAL_EVENT_STREAM.json",
            "OBSERVED_GAMEPLAY_TRACE.json",
            "OBSERVED_GAMEPLAY_TRACE.md",
            "RUNTIME_BLIND_INPUT.json",
        ):
            self.assertTrue((output / name).exists(), name)

    def test_run_mapping_failure_overwrites_pass_report_and_stops(self):
        self.mapping["event_type_map"].pop("door_response")
        self.write_inputs()
        output = self.root / "reader-failure"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            exit_code = reader.main(
                [
                    "run",
                    "--manifest",
                    str(self.manifest_path),
                    "--events",
                    str(self.events_path),
                    "--mapping",
                    str(self.mapping_path),
                    "--out-dir",
                    str(output),
                    "--game-repo",
                    str(self.root),
                ]
            )
        self.assertEqual(2, exit_code)
        report = json.loads((output / "INTEGRITY_REPORT.json").read_text())
        self.assertEqual("INCONCLUSIVE_EVIDENCE", report["status"])
        self.assertFalse((output / "CANONICAL_EVENT_STREAM.json").exists())

    def test_cli_rejects_output_outside_game_repo(self):
        outside = Path(self.temp.name).parent / "escaped-reader-output.json"
        with redirect_stderr(io.StringIO()):
            exit_code = reader.main(
                [
                    "normalize",
                    "--manifest",
                    str(self.manifest_path),
                    "--events",
                    str(self.events_path),
                    "--mapping",
                    str(self.mapping_path),
                    "--out",
                    str(outside),
                    "--game-repo",
                    str(self.root),
                ]
            )
        self.assertEqual(2, exit_code)
        self.assertFalse(outside.exists())

    def test_all_writer_commands_validate_ownership_before_side_effects(self):
        stream, _ = reader.normalize_events(self.manifest_path, self.events_path, self.mapping_path)
        timeline, _ = reader.reconstruct_timeline(stream)
        stream_path = self.root / "stream.json"
        timeline_path = self.root / "timeline.json"
        kernels_path = self.root / "kernels.json"
        stream_path.write_text(json.dumps(stream), encoding="utf-8")
        timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
        kernels_path.write_text(json.dumps(self.acceptance_kernels()), encoding="utf-8")

        outside_root = self.root.parent
        cases = [
            (
                [
                    "validate",
                    "--manifest", str(self.manifest_path),
                    "--events", str(self.events_path),
                    "--report", str(outside_root / f"{self.root.name}-validate.json"),
                    "--game-repo", str(self.root),
                ],
                [outside_root / f"{self.root.name}-validate.json"],
            ),
            (
                [
                    "reconstruct",
                    "--stream", str(stream_path),
                    "--out-json", str(self.root / "must-not-write-timeline.json"),
                    "--out-md", str(outside_root / f"{self.root.name}-timeline.md"),
                    "--report", str(self.root / "must-not-write-report.json"),
                    "--game-repo", str(self.root),
                ],
                [
                    self.root / "must-not-write-timeline.json",
                    outside_root / f"{self.root.name}-timeline.md",
                    self.root / "must-not-write-report.json",
                ],
            ),
            (
                [
                    "blind-project",
                    "--timeline", str(timeline_path),
                    "--out", str(outside_root / f"{self.root.name}-blind.json"),
                    "--game-repo", str(self.root),
                ],
                [outside_root / f"{self.root.name}-blind.json"],
            ),
            (
                [
                    "prepare-acceptance",
                    "--timeline", str(timeline_path),
                    "--kernels", str(kernels_path),
                    "--out", str(outside_root / f"{self.root.name}-acceptance.json"),
                    "--game-repo", str(self.root),
                ],
                [outside_root / f"{self.root.name}-acceptance.json"],
            ),
        ]
        for argv, forbidden_paths in cases:
            with self.subTest(command=argv[0]), redirect_stderr(io.StringIO()):
                self.assertEqual(2, reader.main(argv))
                self.assertTrue(all(not path.exists() for path in forbidden_paths))

    def test_run_rejects_illegal_out_dir_before_creating_any_artifact(self):
        outside = self.root.parent / f"{self.root.name}-escaped-reader-run"
        self.assertFalse(outside.exists())
        with redirect_stderr(io.StringIO()):
            exit_code = reader.main(
                [
                    "run",
                    "--manifest",
                    str(self.manifest_path),
                    "--events",
                    str(self.events_path),
                    "--mapping",
                    str(self.mapping_path),
                    "--out-dir",
                    str(outside),
                    "--game-repo",
                    str(self.root),
                ]
            )
        self.assertEqual(2, exit_code)
        self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
