# STEP 11.5 — Handoff Acceptance

## Purpose

Confirm that the chapter handoff bundle set is complete and ready for trunk completion.

## Read inputs from

Review these files:

1. `<STORY_ROOT>/state/outcomes/<stage>/catalog.json`
2. `<STORY_ROOT>/state/outcomes/<stage>/<artifact_stem>_handoff.md`
3. `<STORY_ROOT>/state/outcomes/<stage>/<outcome_id>.json` for every legal outcome

## Save output to

Write the acceptance note to:

- `<STORY_ROOT>/state/outcomes/<stage>/<artifact_stem>_handoff_review_<yyyymmdd>.md`

## Skill use

- No skill required for this step.

## Task

Check whether the handoff set is complete and internally consistent.

## Acceptance criteria

A passing result must confirm all of the following:

- the outcome catalog exists
- every legal outcome is listed in the catalog
- one handoff bundle exists for each legal outcome
- each bundle records carried knowledge, runtime tags, npc memory deltas, hooks, and handoff hints

## Required stop condition

- write a short note that says `STEP 11.5 PASS` or `STEP 11.5 FAIL`
- if the note says `PASS`, the handoff set is complete
