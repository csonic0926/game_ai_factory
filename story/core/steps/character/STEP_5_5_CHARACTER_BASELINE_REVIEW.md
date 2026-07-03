# STEP 5.5 — Character Baseline Review

## Purpose

Review the completed character baseline as a sub-agent contract and decide whether it is ready to hand off to later chapter, transition, and memory workflows.

## Read inputs from

- `<STORY_ROOT>/state/character_baselines/CHARACTER_CONCEPT.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_WORLD_ROLE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_BEHAVIOR_AND_VOICE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_KNOWLEDGE_AND_RELATIONS.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_QA.md`
- `<STORY_ROOT>/state/characters/<character_id>.json`
- `<STORY_ROOT>/state/characters/index.json`
- `<STORY_ROOT>/state/cast_management/CAST_CHARACTER_LIST.md`
- `<STORY_ROOT>/state/cast_management/CHARACTER_CREATION_PROGRESS.md`
- packaged characters under `<STORY_ROOT>/state/characters/`, when distinctness comparison is needed

## Save output to

- `<STORY_ROOT>/state/character_baselines/CHARACTER_BASELINE_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Inspect the saved character baseline and write a local review artifact that states:

- whether the baseline is complete
- whether QA passed
- whether the character is distinct enough from other packaged characters
- whether the character is ready for downstream workflow use

Do not expand scope beyond this review step. Do not revise source baseline files. Report only what is supported by the inputs.

## Required output blocks

Write `CHARACTER_BASELINE_REVIEW.md` with these blocks in this order:

1. `## Review status`
2. `## Reviewed inputs`
3. `## Findings`
4. `## Blockers`
5. `## Decision`

### Review status

State the outcome in one line:

- `PASS` when every review check passes
- `FAIL` when at least one blocker remains

### Reviewed inputs

List the files or packaged character artifacts actually used for this review.

### Findings

Summarize the baseline coverage, QA result, workflow readiness, and distinctness check in short concrete bullets.

### Blockers

- If there are no blockers, write `None`
- If there are blockers, list each blocker explicitly and keep them actionable

### Decision

Include a final one-line decision:

- `STEP 5.5 PASS`
- `STEP 5.5 FAIL`

On `FAIL`, name the blocker directly in the same block.

## Review checks

Treat the following as pass/fail checks.

### Baseline coverage

Pass only if:

- `CHARACTER_CONCEPT.md` exists and is usable
- `CHARACTER_WORLD_ROLE.md` exists and is usable
- `CHARACTER_BEHAVIOR_AND_VOICE.md` exists and is usable
- `CHARACTER_KNOWLEDGE_AND_RELATIONS.md` exists and is usable
- the packaged character exists in readable structured form
- the baseline reads as one coherent substrate, not isolated notes

### QA result

Pass only if:

- `CHARACTER_QA.md` exists
- the latest QA result is `PASS`
- there are no unresolved blockers left in the QA record

### Workflow readiness

Pass only if:

- the character is usable by later chapter creation
- the character is usable by later transition and memory work
- later workflows can read the packaged character directly without reinterpretation

### Distinctness and tracking

Pass only if:

- the character remains distinguishable from other packaged characters in functional terms when comparison is needed
- `CAST_CHARACTER_LIST.md` has been updated
- `CHARACTER_CREATION_PROGRESS.md` has been updated

### Final decision rule

- If every review check passes, write `PASS` and `STEP 5.5 PASS`
- If any review check fails, write `FAIL`, identify the blocker, and end with `STEP 5.5 FAIL`
