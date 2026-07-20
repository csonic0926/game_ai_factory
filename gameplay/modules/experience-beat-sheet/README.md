# Module — Gameplay Experience Beat Sheet

This manual authoring module creates the gameplay span's highest semantic
authority. It answers what the player must notice, want, do, risk, learn, and
carry forward—and why that experience only works here.

Read first:

- `../../docs/GAMEPLAY_EXPERIENCE_BEAT_SHEET_CONTRACT.md`
- the approved Span Quant Sheet for this span and its `PASS_QUANT_REVIEW`
  (`../span-quant/`; without them, stop — demand precedes supply)
- the resolved `PROJECT_GAMEPLAY_PROFILE.md`
- exact story/current-state sources named by that profile
- the resolved `OBSERVATION_ADAPTER.md` for acceptance-kernel preflight

Use `../../templates/GAMEPLAY_EXPERIENCE_BEAT_SHEET.md`. Write the result in
the game repo at:

```text
<GAMEPLAY_ROOT>/experience_beat_sheets/<sheet_id>.md
```

## Live authoring

1. Receive span scope, duration, and content floors from the approved Span
   Quant Sheet; establish player frame, entering purpose, sources, and red
   lines. The sheet supplies the quant demand — it may tighten a floor but
   never loosen one.
2. Spread candidate **concrete player situations** at one abstraction level.
3. Ask only the 3–5 USER questions that can most alter the span; do not read a
   checklist as a questionnaire.
4. For each surviving beat, make the engagement mode complete: actual work,
   agency/challenge/payoff, commitment, response, intended change,
   carry-forward, and failure/recovery.
5. Write each confirmed USER ruling to the sheet immediately and keep AI
   assumptions separate.
6. Define each acceptance kernel and preflight its evidence path against the
   Observation Adapter. Mark gaps `BLOCKED_BY_OBSERVABILITY`.
7. Record curve/red lines, exact version token/checksum, and authority status.

If direction is not USER-approved, save the best supported draft as
`AI_DRAFT_FOR_REVIEW`; never label model assumptions as USER rulings.

## Fresh review

Use `../../templates/GAMEPLAY_EXPERIENCE_DESIGN_REVIEW.md` in a fresh context
with file-only handoff. The reviewer writes
`<GAMEPLAY_ROOT>/qa/<span_id>_DESIGN_REVIEW.md`, returns only
`PASS_DESIGN_REVIEW` or `FAIL_DESIGN_REVIEW`, names the first invalid
beat/transformation, and edits nothing.

A filled template is not automatically valid. Abstract situations,
compliance-only activity, empty engagement labels, completion receipts,
unrelated objectives, and unobservable kernels all fail.

## Revision discipline

Any source/ruling/beat/kernel/curve/red-line change creates a new version and
makes the walkthrough, packets, observation plans, and acceptance artifacts
bound to the prior version `STALE`. A changed Span Quant Sheet makes this
sheet `STALE` first. Re-review/regenerate downstream artifacts; never patch
their version label while retaining old semantics.
