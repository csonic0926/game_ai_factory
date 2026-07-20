# Playable Beat Packet Contract v1

## Purpose and source authority

A Playable Beat Packet is a production handoff compiled from a contiguous,
approved Intended Player trace slice that binds an exact Gameplay Experience
Beat Sheet version. It does not originate as an outline and must not invent,
simplify, or rewrite gameplay absent from its authority chain.

Packet compilation is blocked until the exact span's Quantitative Experience
Budget and selectors are bound and the required quantitative gate has run.
`NO_GAMEPLAY`, `FAIL_EXPERIENCE_BUDGET`, or `INCONCLUSIVE_EVIDENCE` cannot be
packaged or named as a gameplay segment.

Every packet has four layers:

1. **Experience contract** — Beat Sheet work, engagement, response, intended
   change, carry-forward, curve, failure/recovery, and red lines.
2. **Player-action contract** — what the player perceives, attempts, does, and
   receives in response.
3. **Runtime contract** — triggers, control, camera, presentation, objective,
   state, feedback, proof, and validation.
4. **Observation contract** — how actual evidence will expose cue, attempt,
   response, carry-forward, alternatives/failure, timing, and captures.

## Segmentation rule

Only after the full trace exists, a moment is a candidate boundary when player
intent, core verb, control mode, understanding, expected payoff, or handoff
changes/completes. Record every candidate. Adjacent candidates may merge only
when one coherent player-action arc remains and no experience contract,
control handoff, knowledge delivery, payoff, kernel, or blocker is hidden.
Presentation/dialogue advance, teleporter input, raw input counts, straight
locomotion, objective arrival, and passive state changes never create gameplay
packets or packet boundaries by themselves.

## Required packet schema

```yaml
packet_id: stable id
packet_status: DRAFT | PRODUCTION_READY | BLOCKED_BY_OBSERVABILITY | STALE

source_experience:
  sheet_path: game-repo-relative path
  sheet_id: id
  sheet_version: exact token
  sheet_checksum: exact checksum
  sheet_authority_status: USER_APPROVED | AI_DRAFT_FOR_REVIEW
  source_beat_ids: []
  acceptance_kernel_ids: []
  design_review: PASS ref
  quantitative_budget_path: exact game-owned JSON path
  quantitative_gate_result: PASS_EXPERIENCE_BUDGET ref

source_trace:
  trace_id: id
  first_moment: id
  last_moment: id
  trace_approval: PASS ref

entry_state:
  runtime: explicit relevant state
  world: explicit relevant state
  player_knowledge: explicit relevant state
  grammar: recent verbs/rhythm/expectations/budget

experience_contract:
  intended_experience: qualified player-facing target
  pacing_function: adapter-declared axis/value
  engagement_mode: primary/secondary modes
  player_work: concrete work
  agency_or_challenge: mode-specific source
  commitment_and_pressure: concrete commitment
  observable_world_response: receivable response
  intended_player_change: qualified intended delta
  carry_forward: next purpose/situation causality
  failure_misread_recovery: allowed drift and recovery
  red_lines: []

player_action_contract:
  immediate_intent: current purpose/question
  visible_and_known: trace-faithful evidence
  core_verb: adapter-declared verb
  action_arc: ordered attempts/actions
  game_responses: ordered responses
  knowledge_landing: before -> after with evidence
  control_arc: ordered owner/takeover/return

runtime_contract:
  entry_trigger: exact trigger
  control: exact takeover/return requirements
  camera: adapter-supported framing
  presentation: supported dialogue/cutscene/HUD/etc.
  objective_order: show/update/complete ordering
  state_transitions: typed delta refs
  completion_feedback: player-visible acknowledgement
  exit_handoff: resulting situation/owner
  production_mapping_refs: Production Adapter sections
  validation: exact commands/checks
  reception_contract: fair presentation conditions

observation_contract:
  observation_adapter_binding: path/version
  observation_plan_ref: game-owned path
  kernel_evidence:
    - kernel_id: id
      cue_events: []
      action_or_attempt_events: []
      world_response_events_and_latency: []
      carry_forward_events: []
      required_captures: []
      required_evidence_modes: []
      branch_failure_or_performance_probes: []
  instrumentation_mapping: code/data hooks and owners
  raw_evidence_location: game-owned run path/pattern
  validation_and_reader_commands: []
  blind_projection_exclusions: []
  observability_gaps: []

delta_delivery_proof: []
budget_and_dependencies: []
unresolved_deltas: []

exit_state:
  runtime: explicit relevant state
  world: explicit relevant state
  player_knowledge: explicit relevant state
  grammar_update: approved ledger changes
```

The prose blank template is canonical for the manual workflow. This shape
defines semantic completeness; it does not require a parser.

## Runtime, reception, and observation proof

Runtime assertions can prove triggers, flags, scenes, objectives, control, and
mechanical state. They cannot prove a cue was receivable or understood.

Reception contracts define fair presentation conditions: exact cue,
camera/focus, active/hidden UI layers, control order, presentation order, and
paper-prefilter/human obligations.

Observation contracts define how actual gameplay will be recorded and read
back. They must cover every acceptance kernel's cue -> action/attempt -> world
response -> carry-forward chain, including timing/captures and the evidence
mode needed for alternatives, failures, and performance outcomes.

## State, causality, and evidence invariants

- Entry/exit state equals the source trace boundaries; consecutive packets
  agree on shared state.
- All transitions cite Delta/Delivery/Proof entries; no implicit multi-ledger
  mutation exists.
- Exact Beat Sheet version and kernels remain traceable through trace, packet,
  observation plan, runtime run, and acceptance review.
- A production mapping is adapter-supported and within declared capacity.
- Implementation and instrumentation are one production job. Missing logging
  or capture hooks prevent `PRODUCTION_READY` and production-complete status.
- Raw/blind evidence cannot contain design ids, intent, psychology, fun, or
  meaningfulness claims.
- Decision alternatives and failure-dependent mastery cite controlled probes;
  a golden path alone is insufficient. A decision counts only with at least
  two contemporaneously reachable alternatives and distinct observable
  response/carry-forward consequences; different inputs/labels with identical
  consequences do not count.
- Quantitative counts come only from complete reviewed kernel chains or paired
  interval evidence. Input, control return, movement, presentation advance,
  arrival, or passive changes never independently certify gameplay.
- Unobservable kernels produce `BLOCKED_BY_OBSERVABILITY` before production.
- Paper/blind verifier behavior never becomes production source.

## Fresh packet review gate

A fresh reviewer returns `PASS_PACKET_REVIEW` or `FAIL_PACKET_REVIEW`, edits
nothing, and checks source fidelity, complete four-layer contracts, production
feasibility without experience rewrite, exact lineage, and fail-closed
observability. It also verifies a bound `PASS_EXPERIENCE_BUDGET` result for the
exact span; every other budget status blocks packet compilation/acceptance. It
identifies the first invalid transformation and routes back
to Beat Sheet, realization, packet compilation, or adapter/observability.

## Production handoff boundary

The packet specifies what must be implemented, received, and observed. The
Production and Observation Adapters describe how this game encodes/captures
it. Production must land both runtime behavior and instrumentation. Asset and
sound needs may become sibling-factory orders with sheet/beat/packet
provenance; outputs still land in the game repo.
