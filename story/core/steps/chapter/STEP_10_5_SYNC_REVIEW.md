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

- twin sync commands completed without blocking errors
- frame queries use the latest landed chapter state
- stale runtime rows are no longer treated as current truth

## Required stop condition

- write a short acceptance note that says `STEP 10.5 PASS`
