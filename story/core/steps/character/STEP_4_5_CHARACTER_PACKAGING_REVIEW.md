# STEP 4.5 — Character Packaging Review

## Purpose

Review the saved character package and decide whether it is ready for downstream workflows without reconstruction.

## Read inputs from

- `<STORY_ROOT>/state/characters/<character_id>.json`
- `<STORY_ROOT>/state/characters/index.json`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_CONCEPT.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_WORLD_ROLE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_BEHAVIOR_AND_VOICE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_KNOWLEDGE_AND_RELATIONS.md`

## Save output to

- `<STORY_ROOT>/state/character_baselines/CHARACTER_PACKAGING_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Confirm whether the packaged character is present, indexed, baseline-aligned, and readable as a self-contained character artifact.

## Required output blocks

Produce a short review note with these blocks in order:

1. `Status`
2. `Review`
3. `Blockers`

### Status

- Write exactly one of:
  - `STEP 4.5 PASS`
  - `STEP 4.5 FAIL`

### Review

- Summarize what was checked.
- State whether the package is usable for later workflows.
- Mention the character id if available from the inputs.

### Blockers

- If the step fails, list the blocker or blockers explicitly.
- If the step passes, write `None`.

## Review checks

Mark the step as passing only if all checks below are true.

### Package exists as structured data

- The character JSON exists at `<STORY_ROOT>/state/characters/<character_id>.json`.
- The character is stored as a saved structured file, not only as design notes.

### Character is indexed

- `<STORY_ROOT>/state/characters/index.json` exists.
- The packaged character is included in the index.

### Baseline is preserved

- The packaged character still matches the accepted concept.
- The packaged character still matches the accepted world role.
- The packaged character still matches the accepted behavior and voice.
- The packaged character still matches the accepted knowledge and relations.

### Package is readable downstream

- Later workflows can read the package without rebuilding the character from scratch.
- The character's world position, behavior, knowledge, and relations are available in usable form.

## Pass / fail rule

- `PASS` only when every review check above is true.
- `FAIL` when any check is missing, inconsistent, or unreadable.

## Blocker rule

- On `FAIL`, name the specific missing file, mismatch, or readability problem that caused the failure.
