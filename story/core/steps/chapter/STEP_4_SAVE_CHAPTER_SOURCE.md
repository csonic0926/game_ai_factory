# STEP 4 — Save Chapter Source

## Purpose

Package the accepted chapter artifacts into one chapter source JSON.

## Read inputs from

Read these saved chapter artifacts:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT.md`
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_STORY_LINE.md`
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DAY_SPINE.md`

## Save output to

Write the chapter source JSON to:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>.json`

Update this file when the chapter entry changes:

- `<STORY_ROOT>/state/chapter_sources/PROGRESS.md`

## Skill use

- No skill required for this step.

## Task

Create one chapter source JSON that combines the three accepted chapter artifacts.

## Required output format or fields

The JSON must include:

- `preflight`
- `story_line`
- `day_spine`
- optional `branch_points`

If this chapter opens a new dedicated branch or rebuild branch, add the matching entry to `PROGRESS.md`.
