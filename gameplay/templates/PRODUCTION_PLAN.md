# Production Plan — `<PLAN_TITLE>`

- Plan id: `<PLAN_ID>`
- Status: `READY_FOR_EXECUTION | BLOCKED_BY_PLAN_GAP`
- Source objective: `design/gameplay/objective_gameplay/<OBJECTIVE_ID>/OBJECTIVE_GAMEPLAY.md`
- Source SHA-256: `<SHA256_OF_OBJECTIVE_GAMEPLAY_UTF8_BYTES>`
- Objective rows: `<COMMA_SEPARATED_ROW_NUMBERS>`

## Source authority

State which objective rows this plan realizes and which player-visible
requirements remain authoritative. Do not redesign the objective here.

## Required player-visible result

Describe the end state that production must make playable and observable.
Use outcomes, visible information, available player actions, and consequences;
do not prescribe incidental implementation details as design requirements.

## Existing repo evidence and reuse

List exact game-repo-relative files, symbols, data ids, scenes, assets, and
tests that already supply part of the required result. Distinguish verified
reuse from assumptions.

## Production changes

List the owned files/systems to create or change, their required behavior, and
any state migration or compatibility requirements. Include enough code/data
orientation that the executor does not repeat the planner's repo study, but do
not write pseudocode that merely duplicates implementation.

## Locked constraints and non-goals

Preserve design red lines, current runtime invariants, ownership boundaries,
and explicit exclusions. A production planner may route a real gap back to
design but may not silently invent replacement gameplay.

## Verification

List deterministic tests, build/integrity checks, and the later player-visible
runtime evidence required. Tests prove implementation structure and state;
they do not self-award an experience verdict.

## Dependencies and handoff

Name prerequisite plan ids, execution ordering, file ownership, and what the
completed unit hands to the next plan or to runtime acceptance.
