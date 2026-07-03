# STEP 6.5 — World Baseline Acceptance Review

## Purpose

Check whether the completed world baseline is ready to support later character creation and chapter creation.

## Read inputs from

- `<STORY_ROOT>/state/world_baselines/WORLD_CONCEPT.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_RULES.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_GEOGRAPHY.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_INSTITUTIONS.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_LOGISTICS.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_QA.md`
- twin-facing artifacts under `<STORY_ROOT>/story_world/`

## Save output to

- `<STORY_ROOT>/state/world_baselines/WORLD_BASELINE_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Review the completed world baseline against the acceptance criteria below and write the result in the required output blocks.

## Acceptance criteria

### Baseline coverage

The baseline passes when all of these files exist:

- `WORLD_CONCEPT.md`
- `WORLD_RULES.md`
- `WORLD_GEOGRAPHY.md`
- `WORLD_INSTITUTIONS.md`
- `WORLD_LOGISTICS.md`

The baseline also passes when those files describe one coherent world substrate rather than unrelated notes.

### QA result

The baseline passes when `WORLD_QA.md` exists, the latest QA result is `PASS`, and the QA record contains no unresolved blockers.

### Workflow readiness

The baseline passes when the world baseline can support later character creation, can support later chapter creation, and the twin-facing package exists in a readable form under `<STORY_ROOT>/story_world/`.

## Required output blocks

### `CHECKS`

List each acceptance criterion with `PASS` or `FAIL`.

### `REVIEW RESULT`

Write exactly one line:

- `STEP 6.5 PASS`
- `STEP 6.5 FAIL`

### `BLOCKER`

If the result is `FAIL`, state the single blocking issue clearly. If the result is `PASS`, write `None`.
