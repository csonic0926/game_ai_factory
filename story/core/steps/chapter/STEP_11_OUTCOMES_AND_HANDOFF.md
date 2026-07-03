# STEP 11 — Outcomes + Handoff Bundles

## Purpose

- package the accepted chapter into reusable outcome data
- write one handoff summary for the chapter

## Read inputs from

Read the latest synced chapter artifacts:

- `<STORY_ROOT>/state/frames/<artifact_stem>_sync_log_<yyyymmdd>.md`
- the landed chapter source, graph, and runtime ids that belong to the chapter

## Save output to

Write outcome bundles to:

- `<STORY_ROOT>/state/outcomes/<stage>/catalog.json`
- `<STORY_ROOT>/state/outcomes/<stage>/<outcome_id>.json`

Write one handoff summary to:

- `<STORY_ROOT>/state/outcomes/<stage>/<artifact_stem>_handoff.md`

## Skill use

- Use `the factory craft doc core/craft/world-state-snapshot.md` for world-state snapshot and delta packaging.

## Task

Build the chapter outcome set from the synced chapter state.

For each legal outcome:

1. add the outcome to the catalog
2. write one outcome bundle file
3. record carried knowledge, runtime tags, npc memory deltas, hooks, and handoff hints

Before saving, make sure the chapter already has the runtime rows needed to support in-game testing.

## Required output

The finished set must include:

- one complete outcome catalog for the chapter
- one outcome bundle per legal outcome
- one handoff summary md file for the chapter

The handoff summary must describe the outcome set in a form that can support the next chapter's transition work.
