# World Creation Step Output Map

## Purpose

This folder maps each world-creation step to its input files, output files, and required result shape.

## Read inputs from

- The matching `STEP_*.md` file in this folder
- Any world baseline notes or review artifacts named by that step

## Save output to

### Approval-stage world notes

Store working world-baseline artifacts under:

- `<STORY_ROOT>/state/world_baselines/`

Typical files:

- `WORLD_CONCEPT.md`
- `WORLD_RULES.md`
- `WORLD_GEOGRAPHY.md`
- `WORLD_INSTITUTIONS.md`
- `WORLD_LOGISTICS.md`
- `WORLD_QA.md`

### Twin packaging

When the world baseline is accepted, save the packaged outputs under:

- `<STORY_ROOT>/story_world/seed_entities.json`
- `<STORY_ROOT>/story_world/seeds/*.json`
- supporting documentation under `<STORY_ROOT>/story_world/`

## Task

Use the matching step file to identify:

- the file to read
- the file to write
- the required output shape for that step

## Required report

For each `STEP n` or `STEP n.5` block, report:

- files created or updated
- `PASS` or `FAIL`
- the blocker or reason to stop before the next step
