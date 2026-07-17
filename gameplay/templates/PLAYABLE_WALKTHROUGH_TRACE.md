# Playable Walkthrough Trace — `<TRACE_ID>`

## Source ledger

- Project / adapter path:
- Story-anchor source and range/version:
- Current-state source and version:
- Grammar-state source and version:
- Primary locale:
- Declared budget/capacity:
- Intended Player author:
- Human approval status/reference:

## Starting state

### Runtime state

### World state

### Player-knowledge ledger

### Gameplay grammar state

### Constraints and unresolved inputs

## Continuous player-time rollout

Write one uninterrupted rollout across the full requested span before packet
compilation. This is not a plot summary.

## Moment annotations

### `<MOMENT_ID>`

- **player_intent:**
- **visible_and_known:**
- **available_actions:**
- **action_taken:**
- **game_response:**
- **knowledge_update:**
- **control_owner:**
- **design_intent:**
- **state_deltas:**
  - runtime_delta:
  - world_delta:
  - player_knowledge_delta:
  - player_affect_delta: `NOT_FORMALIZED_IN_V0` or a qualified proposal
- **delivery_and_proof_refs:**
- **boundary_signals:**

## Delta → Delivery → Proof ledger

### `<DELTA_ID>`

- **delta_type:** runtime | world | player_knowledge | player_affect
- **before:**
- **after:**
- **delivery:** caused_by_player | witnessed_by_player | offstage
- **proof kind:** runtime_validation | reception_contract
- **proof checks:**
- **source_anchor:**

### Unresolved deltas

```yaml
unresolved_delta:
  delta_id:
  reason:
  required_capability_or_story_revision:
```

## Continuity audit

- [ ] No player intent/action uses future information.
- [ ] Every action is adapter-supported and currently available.
- [ ] Control takeover/return is explicit and ordered.
- [ ] Every knowledge update has player-visible delivery evidence.
- [ ] Runtime, world, knowledge, and grammar ledgers remain distinct.
- [ ] Budget/capacity holds or an unresolved delta is recorded.
- [ ] `visible_and_known` contains no hidden design intent.
- [ ] Candidate beat boundaries are marked only after the continuous trace.

## Blinded First-time Player audit

- Derived projection path:
- Fresh verifier session/reference:
- First meaningful divergence:
- Reception failures:
- Canonical trace revision and rerun:
- Human review:
