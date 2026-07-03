# STEP 6 — World Consistency QA

## Purpose

Check the saved world baseline for internal consistency and write a concrete QA result.

## Read inputs from

- `<STORY_ROOT>/state/world_baselines/WORLD_CONCEPT.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_RULES.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_GEOGRAPHY.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_INSTITUTIONS.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_LOGISTICS.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_TWIN_REVIEW.md`
- twin-facing artifacts under `<STORY_ROOT>/story_world/`, when needed for consistency checks

## Save output to

- `<STORY_ROOT>/state/world_baselines/WORLD_QA.md`

## Skill use

- No skill required for this step.

## Task

Compare the saved baseline artifacts against each other and identify any concrete mismatch, gap, or missing support that would block later character creation or chapter creation.

## Required output blocks

### `REVIEW SUMMARY`

State one short summary of the overall QA result in one or two sentences.

### `PASS OR FAIL`

Write `PASS` or `FAIL`.

### `ISSUES`

List each concrete mismatch, contradiction, or missing baseline support.

For each issue, state what files or world layers are in conflict.

### `FIXES`

List the specific baseline changes needed to resolve each issue.

## QA focus

Check the baseline for these kinds of consistency:

- rules and geography support each other
- geography and institutions support each other
- institutions and daily order support each other
- logistics and geography support each other
- logistics and institutions support each other
- the twin-facing package matches the saved world baseline
- later character and chapter workflows have enough concrete support
