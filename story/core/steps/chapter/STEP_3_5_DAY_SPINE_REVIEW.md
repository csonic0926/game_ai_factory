# STEP 3.5 — Day Spine Acceptance

## Purpose

Check whether the saved day spine is ready to accept into chapter source.

## Read inputs from

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DAY_SPINE.md`

## Save output to

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DAY_SPINE_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Review the saved day spine and decide whether it passes.

A passing day spine:

- carries the selected line across the full day
- gives morning, noon, and evening distinct work
- shows concrete carry-over from one time span to the next
- ends in a posture that cannot simply reset to normal

## Acceptance criteria

### `MORNING`

Pass when this block includes:

- a starting situation
- an intended task or obligation
- a first visible bend

### `NOON`

Pass when this block includes:

- the ongoing intended task
- the redirect, delay, or complication
- a concrete carry-over into evening

### `EVENING`

Pass when this block includes:

- the expected normal closure
- what blocks that closure
- the resulting end-of-day posture

### `THROUGHLINE`

Pass when this block includes:

- the original day-track
- the bending line across the day
- the consequence carried out of the day

## Required stop condition

- Write a short acceptance note that says `STEP 3.5 PASS` or `STEP 3.5 FAIL`.
- If the result is `FAIL`, name the blocker clearly.
