# Playable Walkthrough Trace — `<TRACE_ID>`

## Source ledger

- **Trace status:** `DRAFT | PASS_REALIZATION_REVIEW | STALE`
- **Gameplay Experience Beat Sheet path:**
- **Sheet id/version token/checksum/status:**
- **Beat Sheet design-review PASS ref:**
- **Story-anchor source/range/version:**
- **Current-state source/version:**
- **Gameplay grammar source/version:**
- **Project Gameplay Profile path/version:**
- **Production Adapter path/version:**
- **Observation Adapter path/version:**
- **Primary locale:**
- **Declared budget/capacity:**
- **Quantitative Experience Budget path/id + exact sheet binding:**
- **Intended Player author/session:**
- **Human approval status/reference:**

## Starting state

### Runtime/system state

### World state

### Player-knowledge ledger

### Derived gameplay grammar state

### Decision/allocation state and budget

### External production/runtime state

### Constraints and unresolved inputs

## Continuous player-time rollout

Write one uninterrupted rollout across the full span before packet
compilation. Preserve concrete player time, control, work, response, curve,
and carry-forward. This is not a plot summary.

## Moment annotations

### `<MOMENT_ID>`

- **source_experience_beats:**
- **player_intent:**
- **visible_and_known:**
- **available_actions:**
- **action_taken:**
- **game_response:**
- **knowledge_update:**
- **control_owner:**
- **design_intent:**
- **engagement:**
  - primary_mode:
  - player_work:
  - agency_or_challenge:
  - commitment:
  - carry_forward:
- **state_deltas:**
  - runtime_delta:
  - world_delta:
  - player_knowledge_delta:
  - player_affect_delta: `NOT_FORMALIZED` or a qualified proposal
- **delivery_and_proof_refs:**
- **acceptance_kernel_refs:**
- **boundary_signals:**

## Delta -> Delivery -> Proof -> Observation ledger

### `<DELTA_ID>`

- **delta_type:** runtime | world | player_knowledge | player_affect
- **before:**
- **after:**
- **delivery:** caused_by_player | witnessed_by_player | offstage
- **proof kind/checks:** runtime_validation | reception_contract
- **Observation Adapter/kernel refs:**
- **source anchor:**

### Unresolved deltas / observability blockers

```yaml
unresolved_delta:
  delta_id:
  reason:
  required_capability_or_story_revision:
  blocker: unresolved_delta | BLOCKED_BY_OBSERVABILITY
```

## Beat coverage and continuity audit

| Beat/kernel | Realized moments | Work/agency preserved | Response/carry-forward | Curve/red lines | Observation path |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

## Quantitative allocation audit

- Exact runtime start/end boundary realization:
- Planned first-play duration and optional replay target:
- Planned player-control time/ratio:
- Longest presentation-only interval:
- Longest traversal-only/no-gameplay interval:
- Planned complete gameplay beat / decision / combat / world-interaction counts:
- Planned narrative presentation count/time:
- Kernel and interval-selector refs:
- Activities explicitly excluded from gameplay counts:

- [ ] No intent/action uses future information.
- [ ] Every action is adapter-supported and currently available.
- [ ] Control takeover/return is explicit and ordered.
- [ ] Every knowledge update has player-visible delivery evidence.
- [ ] Runtime, world, knowledge, grammar, allocation, and external state remain distinct.
- [ ] Budget holds or a blocker is recorded.
- [ ] Teleporter/dialogue advance/raw input/straight locomotion/objective
      arrival/passive state changes are not independently counted as gameplay.
- [ ] Every counted decision identifies two contemporaneously reachable
      alternatives and controlled/equivalent evidence for distinct observable
      response/carry-forward consequences.
- [ ] `visible_and_known` contains no hidden design intent.
- [ ] Boundaries were marked after the continuous rollout.
- [ ] Every Beat Sheet beat/kernel is covered in order and exact-bound.
- [ ] Engagement-mode work/agency/challenge/payoff remains complete.
- [ ] World responses create carry-forward rather than unrelated objectives.
- [ ] Curve and red lines survive.
- [ ] Every kernel has an Observation Adapter evidence path.

## Fresh realization review

- Reviewer/session:
- Result: `PASS_REALIZATION_REVIEW | FAIL_REALIZATION_REVIEW`
- First invalid transformation boundary:
- Reviewer made no source edits: yes | no

## Paper-stage blinded player prefilter

- **Evidence class:** `DESIGN_RECEPTION_PREFILTER_ONLY`
- Derived paper projection path:
- Fresh verifier session/report:
- First meaningful divergence:
- Reception finding/revision/rerun:
- Runtime acceptance remains required: yes
