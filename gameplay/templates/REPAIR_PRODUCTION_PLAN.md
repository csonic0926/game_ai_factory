# Repair Production Plan — `<PLAN_TITLE>`

- Plan id: `<PLAN_ID>`
- Status: `READY_FOR_EXECUTION | BLOCKED_BY_PLAN_GAP`
- Anchor objective: `<GAME_REPO_RELATIVE_OBJECTIVE_GAMEPLAY_PATH>`
- Anchor SHA-256: `<SHA256_OF_ANCHOR_OBJECTIVE_GAMEPLAY_UTF8_BYTES>`
- Source repair: `<GAME_REPO_RELATIVE_REPAIR_SOURCE_PATH>`
- Source SHA-256: `<SHA256_OF_REPAIR_SOURCE_UTF8_BYTES>`
- Repair rows: `<COMMA_SEPARATED_ROW_NUMBERS>`

## Source authority

State which repair rows this plan realizes, how they amend the anchored
objective, and which player-visible requirements remain authoritative. Do not
redesign unrelated objective rows.

## Required player-visible result

Describe the repaired causal contract in the anchored progression window:
visible information, available actions, consequences, and any meaningful
decision or execution that must remain.

## Existing repo evidence and reuse

List exact game-repo-relative files, symbols, data ids, scenes, assets, and
tests that already supply part of the repair. Distinguish verified reuse from
assumptions.

## Production changes

List only files/systems owned by this repair, their required behavior, and any
state migration or compatibility constraints. Do not opportunistically clean
up neighboring gameplay.

## Locked constraints and non-goals

Preserve the base objective, unrelated working behavior, current progression
handoffs, explicit user rulings, and the repair's declared non-goals.

## Verification

List deterministic regression checks plus the player-visible runtime evidence
needed to close the gap. Passing code tests does not self-award experience
acceptance.

## Dependencies and handoff

Name prerequisite repair plan ids, execution ordering, exclusive file
ownership, and the external/user/fresh-review boundary for final gap closure.
