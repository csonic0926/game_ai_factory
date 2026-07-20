# Gameplay Observation Reader

`gameplay/reader.py` is the project-agnostic reference implementation for
validating and reading actual gameplay evidence. It uses only the Python 3
standard library.

## Inputs

- raw manifest JSON conforming to `../schemas/raw_manifest.schema.json`;
- append-only raw event JSONL conforming to
  `../schemas/raw_event.schema.json`;
- game-owned observation mapping JSON conforming to
  `../schemas/observation_mapping.schema.json`;
- optionally, an acceptance-kernel selector file conforming to
  `../schemas/acceptance_kernels.schema.json`;
- for quantitative gating, the exact sheet-bound game-owned budget/selector
  file conforming to `../schemas/experience_budget.schema.json`.

All inputs and generated outputs belong in the game repo. The fixture under
`tests/fixtures/` is test data, not a project answer or production artifact.

## Commands

Run from the umbrella root:

```bash
python3 gameplay/reader.py validate \
  --game-repo <GAME_REPO> \
  --manifest <RAW_MANIFEST.json> \
  --events <raw_events.jsonl> \
  --report <INTEGRITY_REPORT.json>

python3 gameplay/reader.py normalize \
  --game-repo <GAME_REPO> \
  --manifest <RAW_MANIFEST.json> \
  --events <raw_events.jsonl> \
  --mapping <observation_mapping.json> \
  --out <CANONICAL_EVENT_STREAM.json>

python3 gameplay/reader.py reconstruct \
  --game-repo <GAME_REPO> \
  --stream <CANONICAL_EVENT_STREAM.json> \
  --out-json <OBSERVED_GAMEPLAY_TRACE.json> \
  --out-md <OBSERVED_GAMEPLAY_TRACE.md> \
  --report <INTEGRITY_REPORT.json>

python3 gameplay/reader.py blind-project \
  --game-repo <GAME_REPO> \
  --timeline <OBSERVED_GAMEPLAY_TRACE.json> \
  --out <RUNTIME_BLIND_INPUT.json>

python3 gameplay/reader.py prepare-acceptance \
  --game-repo <GAME_REPO> \
  --timeline <OBSERVED_GAMEPLAY_TRACE.json> \
  --kernels <acceptance_kernels.json> \
  --out <ACCEPTANCE_COMPARISON_INPUT.json>

python3 gameplay/reader.py measure-budget \
  --game-repo <GAME_REPO> \
  --run-id <FIRST_PLAY_RUN_ID> \
  --session-id <FIRST_PLAY_SESSION_ID> \
  --timeline <FIRST_PLAY_OBSERVED_GAMEPLAY_TRACE.json> \
  --timeline <CONTROLLED_BRANCH_TRACE_A.json> \
  --timeline <CONTROLLED_BRANCH_TRACE_B.json> \
  --kernels <acceptance_kernels.json> \
  --budget <quantitative_experience_budget.json> \
  --out <EXPERIENCE_BUDGET_RESULT.json>
```

`run` performs validate, normalize, reconstruct, and blind-project in a single
output directory:

```bash
python3 gameplay/reader.py run \
  --game-repo <GAME_REPO> \
  --manifest <RAW_MANIFEST.json> \
  --events <raw_events.jsonl> \
  --mapping <observation_mapping.json> \
  --out-dir <GAMEPLAY_ROOT>/runtime_evidence/<run_id>/reader
```

If validation or reconstruction integrity fails, the command exits non-zero,
writes the integrity report when requested, and does not manufacture later
outputs.

Every command requires the explicit game Git root and rejects inputs/outputs
outside it or a game root inside this factory. This is a tool-level ownership
guard, not only a caller convention. Every writer validates all input and
output ownership before its first directory creation or file write.

## Mapping model

The mapping is deliberately small and declarative. Dotted source paths map
project records to canonical values. `event_type_map` maps project event
names to one of:

```text
player_input, gameplay_action, control, cue, presentation,
world_response, state_change, capture, performance
```

`observable_fields` lists source fields that a player could actually receive;
`hidden_fields` lists mechanically useful but blind-excluded state. The
adapter must not place design ids or interpretations in either raw input or
observable output. Observable and hidden source/target paths may not be equal
or component-prefix parent/children. Observable projections also cannot remap
raw provenance, event/correlation semantics, branch labels, or capture paths
under neutral-looking targets. A project that needs more complex parsing may
generate the same canonical stream with its own adapter tool and start at
`reconstruct`, but the reconstructed stream must satisfy the same integrity
invariants.

## Correlation and latency

Mapped records may carry a neutral `correlation_id` and a role of `cue`,
`action`, or `response`. Reconstruction reports:

- cue-to-action latency when both exist;
- action-to-response latency when both exist;
- missing, duplicated, roleless, or time-reversed correlation members as
  integrity findings.

Each correlation has exactly one ordered cue/action/response member. Acceptance
preparation finds a positive chain only within one timeline/run/session, uses
the same correlation for those three phases, and requires the selected
carry-forward after the selected response. It never stitches phases across
runs.

These are observations, not judgments about player understanding.

## Blind projection

The stored projection is a facilitator artifact. Each reveal payload includes
only elapsed time, a neutral observation channel when supplied by runtime,
scrubbed public context/data, neutral capture aliases, and a neutral evidence
alias. It contains no canonical event kind/role, summary, raw path, correlation
internals, hidden state, semantic design ids, or future-derived latency.
`private_facilitator_metadata` maps evidence aliases back to raw refs and
capture aliases back to paths; the facilitator does not reveal that private
map. Known capture paths found in public data are replaced by the same aliases,
preserving audit traceability without revealing filesystem paths.

## Acceptance preparation

Kernel selectors query event kind, public event id, correlation id, and/or
observable key/value. The output lists same-run ordered complete chains and
reports required-mode coverage. Controlled branch probe groups are complete
only when build/setup/display/performance provenance is comparable, at least
two branch labels have complete chains, and their run-neutral observed
response/carry-forward consequences are actually distinct. Different labels
or action/input values with identical response/carry-forward evidence are not
proof of different alternatives.

Applicability is explicit rather than selector-inferred. A kernel requiring
`CONTROLLED_BRANCH_PROBE` declares `controlled_probe_group_ids`, a non-empty
unique list of exact manifest `probe_group.group_id` values. The reader emits
and evaluates only those groups for that kernel. Every declared group must be
present and complete for controlled-probe mode coverage; missing groups and
partial branches remain `INCOMPLETE`. Undeclared groups are omitted even if a
generic cue or carry selector matches them. Kernels that do not require
controlled probes must omit `controlled_probe_group_ids` and emit no
`branch_probe_groups`.

A kernel may add `ordered_sequences` when cue/action/response/carry selectors
alone are too coarse to prove required runtime order. Each entry has a stable
`sequence_id`, an `after_phase`, a later `before_phase`, and one or more
ordered `matches`. Match objects use the same `event_kind`/`event_id`/
`correlation_id`/`observable` grammar as phase selectors. Omit the field when
the four positive phases are sufficient; existing kernels are unchanged.

For each candidate positive phase chain, every ordered-sequence step must bind
to a different event in the same run/session. Bound events must have strictly
increasing event sequence numbers and lie strictly between that chain's
selected boundary events. Extra unrelated events are allowed. Events from
other runs cannot fill gaps, and one event cannot satisfy multiple steps,
including steps in overlapping ordered sequences. The reader searches all
eligible carry-forward candidates rather than letting an earlier unqualified
carry hide a later qualified chain.

`chain_status: COMPLETE`, required-mode coverage, and controlled branch-group
completeness use only sequence-qualified chains. `complete_chains` contains
phase refs plus ordered step evidence refs. Positive-phase candidates that
fail qualification appear in `incomplete_chains`, with per-chain and
per-sequence status, failed step, candidate refs, and one of these reasons:

- `MISSING_MATCH`;
- `OUTSIDE_BOUNDARY_ONLY`;
- `ORDER_VIOLATION`;
- `EVENT_REUSE_REQUIRED`;
- `EVENT_REUSE_CONFLICT_ACROSS_SEQUENCES`.

For a `negative_check`, the selector's phase window is evaluated separately in
each sequence-qualified complete chain; an unqualified positive-phase chain
does not open a negative-check window. `VIOLATION_MATCH_FOUND` is positive
evidence and can be reported whenever a forbidden match is present in a
qualified window. Absence is
`SATISFIED_NO_MATCH` only when the raw manifest supplied an
`observation_window` with `coverage_status: COMPLETE`, a non-empty coverage
basis, and a contiguous sequence range covering the selected phase window.
Otherwise absence is `INCONCLUSIVE_COVERAGE`.

Preparation intentionally emits `verdict: null`, no gameplay-experience
verdict, and no psychological inference. A fresh acceptance reviewer must
compare the evidence with the authoritative Beat Sheet and blind report.

## Quantitative Experience Budget measurement

`measure-budget` selects one exact `LIVE_BLIND_RUN` or `RECORDED_RUN` from the
runtime-owned `--run-id` and `--session-id` invocation arguments. The
Beat-Sheet-owned budget must not contain either runtime id; it owns unique
observable start/end boundary selectors plus the sheet binding, thresholds,
paired interval selectors, reviewed kernel measurement refs, and optional
selectors identifying evidence for known non-gameplay-only activities. A
complete contiguous observation window must cover the selected boundaries.

The reader mechanically calculates:

- first-play duration and target/min/max comparisons;
- raw player-control time, overlapping presentation time, and effective
  gameplay-capable control ratio after subtracting that overlap;
- maximum uninterrupted presentation-only and traversal-only/no-gameplay gaps;
- complete gameplay-engagement chains and configured complete beat,
  meaningful decision, combat, and world-interaction counts;
- narrative presentation count and total time.

Each counted gameplay measurement references one exact acceptance kernel and
one complete same-span evidence chain. A chain counts as one complete gameplay
beat and at most one of decision, combat, or world-interaction content. Broad
selectors that match multiple
chains, duplicate measurements of one chain, ambiguous boundaries, unpaired
or overlapping intervals, incomplete exact-span coverage, or malformed
bindings produce `INCONCLUSIVE_EVIDENCE`. A decision measurement additionally
requires controlled/equivalent branch evidence for at least two alternatives
from comparable contemporaneous state and distinct observable response/
carry-forward consequences.

Non-gameplay selectors are also a fail-closed overlap partition. If the
action/attempt, world-response, and carry-forward evidence of a nominally
complete chain are all classified as teleporter/dialogue/raw input/straight
locomotion/objective arrival/passive state/presentation/control transition or
control return, that chain is disqualified. Such events may support a real
chain, but cannot be its only work/response proof.

The objective output status is one of:

- `PASS_EXPERIENCE_BUDGET` — at least one complete engagement chain and every
  threshold comparison passes;
- `FAIL_EXPERIENCE_BUDGET` — gameplay evidence exists but one or more
  thresholds/counts fail;
- `NO_GAMEPLAY` — zero configured complete gameplay-engagement chains,
  including spans consisting only of presentation/dialogue advance,
  teleporter input, raw inputs, control return, straight locomotion, objective
  arrival, or passive state changes;
- `INCONCLUSIVE_EVIDENCE` — evidence/configuration cannot support an objective
  measurement.

Every measured/comparison item carries source evidence refs. The budget
configuration—not a raw event label—binds reviewed kernels and interval
selectors. The reader does not infer fun, engagement psychology, player
understanding, or semantic quality, and this command never emits
`PASS_FACTORY_CONFORMANCE`.
