# Playable Beat Packet Contract v0

## Purpose

A Playable Beat Packet is a production handoff compiled from a contiguous,
approved slice of an Intended Player walkthrough. It does not originate as an
outline and must not invent gameplay missing from its source trace.

Every packet has three semantic layers:

1. **Experience beat** — the intended player-facing experience.
2. **Player-action beat** — what the player perceives, understands, does, and
   receives in response.
3. **Runtime contract** — triggers, control, camera, presentation, objective,
   state changes, feedback, proof, and validation.

## Segmentation rule

After the full trace exists, moment `t` is a candidate boundary when any of
these changes or completes:

```text
player intent
core player verb
control mode
player understanding
expected payoff
handoff into the next playable situation
```

These signals are annotations on the trace, not pre-authored outline slots.
Record every candidate. Adjacent candidates may remain in one production
packet only when the merge preserves a single coherent player-action arc and
the packet records why no contract is lost. A merge must never hide a control
handoff, knowledge delivery, expectation payoff, or unresolved delta.

## Required packet schema

```yaml
packet_id: stable id
source_trace:
  trace_id: id
  first_moment: id
  last_moment: id
  trace_approval: reviewer/date/status reference

entry_state:
  runtime: explicit relevant state
  world: explicit relevant state
  player_knowledge: explicit relevant state
  grammar: recent verbs, rhythm position, open expectations, budget position

experience_beat:
  intended_experience: beat-level intent, not a claim of guaranteed emotion
  pacing_function: adapter-declared rhythm axis/value

player_action_beat:
  immediate_intent: what the player wants now
  visible_and_known: trace-faithful player evidence
  core_verb: adapter-declared verb
  action_arc: ordered player actions
  game_responses: ordered immediate responses
  knowledge_landing: before -> after, with evidence
  control_arc: ordered owner/takeover/return states

runtime_contract:
  entry_trigger: exact trigger
  control: exact takeover/return requirements
  camera: adapter-supported framing requirements
  presentation: dialogue/AVG/cutscene/HUD or adapter-declared mode
  objective_order: show/update/complete ordering
  state_transitions: typed delta refs
  completion_feedback: exact player-visible acknowledgement
  exit_handoff: resulting situation and owner
  production_mapping_refs: PRODUCTION_ADAPTER sections
  validation: exact commands/checks when available
  reception_contract: checklist

delta_delivery_proof: []
budget_and_dependencies: []
unresolved_deltas: []
exit_state:
  runtime: explicit relevant state
  world: explicit relevant state
  player_knowledge: explicit relevant state
  grammar_update: approved ledger changes
```

The prose form in the blank template is canonical for Phase 0; this YAML block
defines semantic completeness, not a requirement to build a parser.

## Runtime versus reception proof

Runtime validation may prove that a trigger fired, a flag changed, a scene
loaded, an objective advanced, or control ownership transitioned. It cannot
prove that a person noticed or understood the result.

For every intended knowledge or affect delta, the reception contract records:

- what exact information/cue is available;
- what frames or focuses it;
- which presentation/HUD layers are active or hidden;
- when control is taken and returned;
- the order of dialogue, objective, transition, and completion feedback;
- the blinded-verifier finding and the unresolved human-playtest obligation.

Passing a reception contract means the design provided fair conditions. It is
not evidence that every player will receive the intended meaning.

## State and causality invariants

- Packet entry state equals the source trace state before `first_moment`.
- Packet exit state equals the trace state after `last_moment`.
- Consecutive packets agree on their shared boundary state.
- State transitions cite Delta/Delivery/Proof entries; no implicit multi-ledger
  mutation is allowed.
- A production mapping is supported by the resolved adapter and stays within
  declared budget/capacity.
- Runtime execution cannot consume the verifier report as a decision source.
- If a required mapping is absent, the packet carries `unresolved_delta`
  rather than a guessed engine implementation.

## Production handoff boundary

The packet describes **what must be implemented and received**. The resolved
production adapter describes **how this game encodes it**. Asset and sound
needs may become sibling-factory orders; game code/data work lands in the game
repo. Production must not rewrite the trace's experience or action arc merely
to fit an undeclared capability—route the mismatch back as an unresolved
delta.
