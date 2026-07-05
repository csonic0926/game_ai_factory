# STEP 4.5 — Chapter Source Acceptance

## Purpose

- confirm that the chapter source JSON was saved in the right place
- confirm that the source JSON matches the saved chapter artifacts

## Read inputs from

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>.json`
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT.md`
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_STORY_LINE.md`
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_CHAPTER_SPINE.md`

## Save output to

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_SOURCE_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check the chapter source JSON and decide whether it is ready to pass.

Use these checks:

- the JSON exists at the expected path
- the JSON includes `preflight`, `story_line`, and `chapter_spine`
- the JSON content matches the saved preflight, story-line, and chapter-spine artifacts

## Acceptance criteria

### Source file

Pass when `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>.json` exists and is readable.

### Required fields

Pass when the JSON contains:

- `preflight`
- `story_line`
- `chapter_spine`

### Source consistency

Pass when the JSON content matches:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT.md`
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_STORY_LINE.md`
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_CHAPTER_SPINE.md`

## Required stop condition

- write a short acceptance note that says `STEP 4.5 PASS` or `STEP 4.5 FAIL`
- if the result is `FAIL`, state the blocker clearly
