# Playable Walkthrough Trace Contract v0

## Purpose

The first gameplay-factory artifact is one continuous **Intended Player**
rollout through actual player time. It is not a plot summary and not a set of
independent fillers between story beats. Beat segmentation happens only after
the trace exists.

This contract is project-agnostic. Every verb, system, presentation mode,
rhythm axis, capacity, and budget named in a real trace must resolve through
the game-owned adapter.

## Settled decisions carried by v0

- **D1:** walkthrough-first continuous rollout;
- **D2:** beat candidates emerge from player-state delta detection;
- **D3:** runtime, world, player-knowledge, and player-affect are distinct
  delta classes; `player_knowledge_delta` is a formal moment annotation;
- **D4:** Intended Player authors the canonical trace; a fresh First-time
  Player receives a blinded observable projection only;
- **D5:** every required delta has a Delivery and Proof or becomes an
  `unresolved_delta`;
- **D6:** project and production facts enter through game-owned adapters;
- **D7:** v0 remains document-first.

## Formal object map

For moment index `t`:

- `S`: immutable story anchors and causal constraints for this trace;
- `R_t`: runtime/system state known to design (flags, objective stage, map,
  control mode, and other adapter-declared state);
- `W_t`: narrative world state;
- `K_t`: player-knowledge ledger—only knowledge already delivered;
- `G_t`: persistent gameplay grammar state (recent verbs, rhythm position,
  expectations, budget/cost history, feedback/handoff conventions);
- `A_g`: project gameplay adapter (capabilities and constraints);
- `A_p`: production adapter (runtime mappings and validators);
- `m_t`: one trace moment;
- `a_t`: the canonical Intended Player action in `m_t`;
- `d_t`: typed state deltas caused or exposed by the moment.

The conceptual transition is:

```text
m_t = rollout(S, R_t, W_t, K_t, G_t, A_g, A_p, declared_budget)
(R_{t+1}, W_{t+1}, K_{t+1}) = apply(R_t, W_t, K_t, a_t, game_response_t, d_t)
G_{t+1} = update_grammar_after_approved_moment(G_t, m_t)
```

The equations define causality, not an implementation requirement. Drafting a
moment does not itself write runtime state. Persistent grammar state is updated
only from the human-approved canonical trace, never from verifier guesses.

### Allowed and forbidden causal arrows

Allowed:

- adapters constrain available actions, delivery, cost, and runtime proof;
- visible game state informs player intent and action;
- action plus game response produces typed deltas;
- delivered evidence advances `K_t`;
- approved trace history updates `G_t`.

Forbidden:

- `design_intent -> visible_and_known` without an actual delivery event;
- future story anchors or future knowledge -> current player decision;
- First-time Player guesses -> canonical production trace;
- trace annotation -> runtime truth without production implementation and
  validation;
- one persisted field silently serving as both player observation and hidden
  design state.

## Artifact sections

A trace contains:

1. **Header and source ledger** — trace id, scope, source paths/versions,
   adapter resolution, starting state, declared budget, and open constraints.
2. **Continuous rollout** — natural prose following the player's actual time
   across the whole scope.
3. **Moment annotations** — the minimum schema below, in the same sequence as
   the prose.
4. **Delta/Delivery/Proof ledger** — all required deltas, including unresolved
   ones.
5. **Continuity audit** — invariants and candidate segmentation signals.

Both prose and structured moments are required. v0 does not decide whether the
author writes prose-first or structured-first; that is Phase 0 question O4.

## Minimum moment schema

```yaml
moment_id: stable id, ordered within the trace
player_intent: what the player currently wants to do
visible_and_known: >
  only what is perceptible or already known to the player at this exact time;
  include visible affordance/control/feedback cues here when they truly exist
available_actions:
  - adapter-supported actions actually possible now
action_taken: the Intended Player's canonical action
game_response: immediate visible/audible/system response in player time
knowledge_update: human-readable description of what the player can now infer
control_owner: adapter-declared owner that distinguishes player and game control
design_intent: hidden author intent; never copied into the blinded projection
state_deltas:
  runtime_delta: []
  world_delta: []
  player_knowledge_delta: []
  player_affect_delta: [] | NOT_FORMALIZED_IN_V0
delivery_and_proof_refs: []
boundary_signals: []
```

`knowledge_update` is the readable landing point. Each non-empty update must
agree with a formal `player_knowledge_delta` entry containing before, after,
delivery, and reception-proof reference. A fact cannot enter `K_{t+1}` merely
because it appears in `design_intent`.

`player_affect_delta` is a distinct slot so it cannot be conflated with player
knowledge. Its required granularity is unresolved in O2: v0 permits a
beat-level affect intent, or the explicit value `NOT_FORMALIZED_IN_V0`, but
does not permit an unqualified claim that a player definitely felt an emotion.

## Delta → Delivery → Proof

Every required delta entry contains:

```yaml
delta_id: stable id
delta_type: runtime | world | player_knowledge | player_affect
before: explicit prior state
after: explicit intended state
delivery: caused_by_player | witnessed_by_player | offstage
proof:
  kind: runtime_validation | reception_contract
  checks: []
source_anchor: source reference, or NONE for authored connective state
```

- Required runtime/world deltas use exact validation declared by the production
  adapter. A missing exact mapping produces `unresolved_delta`; it does not
  downgrade silently to design opinion.
- Knowledge/affect deltas use a **reception contract** proving that the game
  provided fair, clear, non-interfering conditions—not that a human mind was
  forced into a state.
- An `offstage` player-knowledge delta is invalid unless the player later
  receives observable evidence; until then it may change world state but not
  `K_t`.

Reception checks cover, when applicable:

- required information is actually perceptible;
- camera frames the relevant object/event;
- HUD and presentation layers do not interfere;
- control takeover and return are signaled and ordered;
- dialogue, objective, state change, and completion feedback appear in the
  intended order.

If delivery or proof cannot be supplied:

```yaml
unresolved_delta:
  delta_id: stable id
  reason: concrete capability, budget, pacing, or story constraint
  required_capability_or_story_revision: concrete requirement
```

Do not quietly drop or rewrite the anchor.

## Blinded verifier projection

The First-time Player input is the ordered projection:

```text
B(trace) = [visible_and_known(m_1), visible_and_known(m_2), ...]
```

Each value is revealed one at a time by a facilitator. The projection excludes
all other fields, including moment ids when they carry semantic hints, story
anchors, future observations, `available_actions`, canonical `action_taken`,
`game_response`, deltas, proofs, boundary signals, and `design_intent`.

If the verifier's intended action meaningfully diverges, record the reception
finding before revealing canonical future material. The verifier report is QA
evidence only; production compiles exclusively from the approved Intended
Player trace.

## Invariants and review

- **Continuity:** each moment begins from the prior moment's resulting state;
  no teleporting intent, knowledge, control, or world state.
- **No lookahead:** intent/action uses only current `visible_and_known` plus
  prior `K_t`.
- **Action legality:** canonical `action_taken` is in `available_actions` and
  supported by `A_g`.
- **Control legality:** actions and response respect `control_owner`; takeover
  and return are explicit.
- **Knowledge causality:** every knowledge update cites observable delivery in
  this or a prior moment.
- **State ownership:** runtime/world/knowledge/grammar state remain separately
  identifiable; no field mutates two layers implicitly.
- **Budget/capacity:** declared costs stay inside adapter limits or emit an
  unresolved delta.
- **Blinding:** the stored verifier input can be derived from
  `visible_and_known` alone.
- **Canonical-source rule:** packets cite trace slices; verifier behavior never
  becomes production source.

## Open questions preserved

- O1: human-derived “feels like playing” reject rubric;
- O2: player-affect formalization beyond the distinct v0 slot;
- O3: First-time Player drift neighborhood;
- O4: prose-first versus structured-first authoring order;
- O5: edge cases at the story-staging/gameplay-presentation boundary (the v0
  ownership rule is in `PROJECT_ADAPTER_CONTRACT.md`).
