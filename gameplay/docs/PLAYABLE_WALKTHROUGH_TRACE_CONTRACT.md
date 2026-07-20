# Playable Walkthrough Trace Contract v1

## Purpose and authority binding

The Playable Walkthrough Trace is one continuous **Intended Player**
realization of a Gameplay Experience Beat Sheet in actual player time. It is
not the highest design authority, a plot summary, or independent filler
between story anchors. Segmentation happens only after the full trace exists.

Before authoring, bind the exact Beat Sheet path, sheet id, version token,
checksum, authority status, and design-review result. A changed binding makes
the trace `STALE`. Bind the sheet's exact Quantitative Experience Budget and
machine-readable selector projection too. Every project verb, system,
presentation mode, rhythm axis, capacity, and budget resolves through the
game-owned adapters.

## Formal object map

For moment index `t`:

- `B`: exact Gameplay Experience Beat Sheet version;
- `S`: story anchors and causal constraints;
- `R_t`: runtime/system state known to design;
- `W_t`: narrative world state;
- `K_t`: player-knowledge ledger containing delivered knowledge only;
- `G_t`: derived gameplay grammar state;
- `A_g`: Project Gameplay Profile;
- `A_p`: Production Adapter;
- `A_o`: Observation Adapter;
- `m_t`: one trace moment, including Intended Player action `a_t` and typed
  deltas `d_t`.

```text
m_t = rollout(B, S, R_t, W_t, K_t, G_t, A_g, A_p, A_o, budget)
(R_{t+1}, W_{t+1}, K_{t+1}) = apply(R_t, W_t, K_t, a_t, response_t, d_t)
G_{t+1} = update_after_approved_trace(G_t, m_t)
```

These equations define causality, not an implementation. Drafting does not
mutate runtime state. Grammar state updates only from a human-approved trace.

Allowed arrows:

- `B` constrains experience, curve, red lines, and acceptance kernels;
- adapters constrain available action, delivery, cost, implementation, and
  evidence paths;
- visible state informs player intent/action;
- action plus response produces typed deltas;
- delivered evidence advances `K_t`.

Forbidden arrows:

- walkthrough realization rewriting a Beat Sheet beat;
- design intent or future knowledge entering `visible_and_known`;
- paper-stage verifier guesses becoming canonical production;
- paper projection/report becoming runtime observation or acceptance;
- trace annotation becoming runtime truth without implementation/evidence;
- one persisted field serving both player observation and hidden design state.

## Required artifact sections

1. **Header/source ledger** — trace id/status; exact Beat Sheet binding; story,
   state, grammar, and all three adapter versions; budget and constraints.
2. **Starting state** — separate runtime, world, player knowledge, grammar,
   allocation/budget, and external production state.
3. **Continuous rollout** — uninterrupted prose across the entire span.
4. **Moment annotations** — structured moments in the same order.
5. **Delta/Delivery/Proof ledger** — every required delta and blocker.
6. **Beat coverage/continuity audit** — ordered Beat Sheet coverage, curve,
   red lines, invariants, and segmentation signals.
7. **Paper-stage blind prefilter** — design-only reception evidence, never
   runtime acceptance.
8. **Quantitative allocation audit** — exact start/end, planned first-play
   time, control/presentation/traversal intervals, and one-to-one kernel refs
   for every required content count. This is a design allocation, not a
   substitute for the runtime `measure-budget` gate.

## Minimum moment schema

```yaml
moment_id: stable id ordered within the trace
source_experience_beats: exact Beat Sheet beat ids realized here
player_intent: current player purpose/question
visible_and_known: only perceptible or previously delivered information
available_actions: adapter-supported actions possible now
action_taken: Intended Player canonical action
game_response: immediate observable response
knowledge_update: qualified inference now fairly available
control_owner: adapter-declared owner
design_intent: hidden author intent, excluded from blind projection
engagement:
  primary_mode: decision | execution/mastery | discovery/interpretation | expression/social | payoff/recovery
  player_work: concrete work
  agency_or_challenge: mode-specific source
  commitment: concrete stake or zero-commitment rationale
  carry_forward: how this result forms the next purpose/question
state_deltas:
  runtime_delta: []
  world_delta: []
  player_knowledge_delta: []
  player_affect_delta: [] | NOT_FORMALIZED
delivery_and_proof_refs: []
acceptance_kernel_refs: []
boundary_signals: []
```

`knowledge_update` must agree with a formal `player_knowledge_delta` containing
before, after, delivery, and reception-proof refs. A fact cannot enter `K_t`
because it appears in design intent. Affect stays qualified; never claim a
player certainly felt an emotion.

## Delta -> Delivery -> Proof -> Observation

Every required delta contains:

```yaml
delta_id: stable id
delta_type: runtime | world | player_knowledge | player_affect
before: explicit prior state
after: explicit intended state
delivery: caused_by_player | witnessed_by_player | offstage
proof:
  kind: runtime_validation | reception_contract
  checks: []
observation_refs: acceptance kernel and Observation Adapter paths
source_anchor: exact source ref, or NONE for connective state
```

Runtime/world deltas use Production Adapter assertions. Knowledge/affect use
reception conditions, not forced-psychology claims. An offstage knowledge
delta is invalid until the player receives evidence.

If a mapping or evidence path is absent:

```yaml
unresolved_delta:
  delta_id: stable id
  reason: concrete capability, budget, pacing, story, or evidence constraint
  required_capability_or_story_revision: concrete requirement
  blocker: unresolved_delta | BLOCKED_BY_OBSERVABILITY
```

Do not drop or rewrite the source beat/anchor.

## Paper-stage blind projection

The paper prefilter is:

```text
B_paper(trace) = [visible_and_known(m_1), visible_and_known(m_2), ...]
```

A facilitator reveals one payload at a time. It excludes semantic moment ids,
anchors, future observations, available-action enumeration, canonical action,
response, deltas, proofs, kernels, boundary signals, and design intent. The
fresh reader records a response before the next reveal.

This can diagnose whether the design document offers sufficient cues. It
cannot prove the build presents them. Runtime blind input must later come only
from actual evidence through the observation reader.

## Fresh realization review gate

A fresh reviewer returns `PASS_REALIZATION_REVIEW` or
`FAIL_REALIZATION_REVIEW`, makes no source edits, and checks:

- exact Beat Sheet binding and complete ordered beat/kernel coverage;
- continuous state/control/time with no lookahead;
- mode-specific work, agency/challenge/payoff, commitment, and failure paths;
- build/hold/release/recovery/rest curve and red lines;
- observable response and causal carry-forward rather than unrelated tasks;
- action/control legality and adapter budget/capacity;
- every kernel has an Observation Adapter path or blocks before packets;
- the exact-span quantitative allocation meets every sheet threshold and does
  not count teleporter input, dialogue advance, raw inputs, straight
  locomotion, objective arrival, or passive state changes as gameplay;
- decision allocations identify controlled/equivalent evidence for two
  contemporaneously reachable alternatives with distinct response and
  carry-forward consequences;
- the paper projection contains only `visible_and_known`.

On failure, identify the first transformation that lost meaning and route to
Beat Sheet design or walkthrough realization. The reviewer never fixes and
passes its own work.

## Invariants

- **Continuity:** each moment begins from the prior resulting state.
- **No lookahead:** intent/action uses only current observation plus prior
  delivered knowledge.
- **Action/control legality:** action is possible and respects current owner.
- **Knowledge causality:** each update cites observable delivery.
- **State ownership:** runtime, world, knowledge, grammar, decision/budget,
  and external execution state remain distinct.
- **Authority fidelity:** trace never silently alters Beat Sheet work,
  response, curve, carry-forward, or red lines.
- **Engagement completeness:** the primary mode has real work and challenge or
  a valid upstream payoff; compliance-only moments are not gameplay beats.
- **Budget/capacity:** limits hold or an unresolved delta is explicit.
- **Blinding:** paper input derives from `visible_and_known` alone.
- **Kernel observability:** every required runtime chain resolves through
  `A_o`, or production is blocked.
- **Quantitative sufficiency:** an input/control/movement-bearing interval is
  not a gameplay beat without a complete engagement chain, and an under-budget
  span cannot be called a gameplay segment or proceed to packet compilation.
- **Canonical source:** packets cite approved trace slices; verifier behavior
  never becomes production source.

## Open pilot questions

- human-derived “feels like playing” reject rubric;
- affect formalization beyond a distinct qualified slot;
- acceptable paper/runtime reader drift neighborhoods;
- prose-first versus structured-first authoring order;
- ambiguous story-staging/gameplay-presentation boundary cases.
