# STEP 10.5 — Sync Acceptance

## Purpose

Confirm that the story logic frame and twin state are synced to the latest landed chapter data.

## Read inputs from

- `<STORY_ROOT>/state/frames/<artifact_stem>_sync_log_<yyyymmdd>.md`

## Save output to

- `<STORY_ROOT>/state/frames/<artifact_stem>_sync_review_<yyyymmdd>.md`

## Skill use

- No skill required for this step.

## Task

Review the saved sync log and decide whether the sync is ready to accept.

The acceptance note must be short and must state either `STEP 10.5 PASS` or `STEP 10.5 FAIL`.

## Acceptance criteria

Pass when all of the following are true:

- Part A (twin write-back): the write-back manifest was applied with the
  chapter's provenance stamp and `twin_db.py validate` exited clean — or
  the log records `NO TWIN DB` truthfully
- Part A judgment call: what was written back is ruling-grade canon (facts
  later chapters must not contradict), not prose or one-off scene dressing;
  and nothing that plainly qualifies (a new named character who stuck, a
  new location, a new law-grade ruling) was left out of the manifest
- Part B (adapter sync): the adapter's sync commands completed without
  blocking errors — or the log records `SKIPPED_BY_PROFILE` and the
  adapter really has no `SYNC_SPEC.md`
- frame queries (where the adapter defines frames) use the latest landed
  chapter state; stale runtime rows are no longer treated as current truth

## Required stop condition

- write a short acceptance note that says `STEP 10.5 PASS`
