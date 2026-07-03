# STEP 4 — Character Packaging

## Purpose

Convert the approved character baseline into the project’s structured character artifacts so later workflows can load one normalized character record and the shared character index.

## Read inputs from

- `<STORY_ROOT>/state/character_baselines/CHARACTER_CONCEPT.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_WORLD_ROLE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_BEHAVIOR_AND_VOICE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_KNOWLEDGE_AND_RELATIONS.md`
- `<STORY_ROOT>/state/CHARACTER_SCHEMA.md`
- `<STORY_ROOT>/state/templates/character.template.json`

## Save output to

Write the packaged character artifacts to:

- `<STORY_ROOT>/state/characters/<character_id>.json`
- `<STORY_ROOT>/state/characters/index.json`

Prepare completion-tracking updates for:

- `<STORY_ROOT>/state/cast_management/CAST_CHARACTER_LIST.md`
- `<STORY_ROOT>/state/cast_management/CHARACTER_CREATION_PROGRESS.md`

## Skill use

- No skill required for this step.

## Task

Build the packaged character record from the saved baseline and template.

The packaged output must preserve the approved meaning of the baseline while making it machine-readable. Include the character’s:

- core concept and identity markers
- world role and daily position
- behavior baseline and speaking style
- knowledge boundaries and relationship facts
- index entry needed for downstream lookup

Use the schema and template as the source of structure. Keep the package scoped to the character’s confirmed baseline; do not add new creative content, implied backstory, or unsupported traits.

## Required outputs or required checks

The step is complete only when all of the following are true:

- `<STORY_ROOT>/state/characters/<character_id>.json` exists and follows the character schema
- the packaged character file includes the baseline-derived fields needed by later workflows
- `<STORY_ROOT>/state/characters/index.json` is updated or extended with the character’s entry
- the packaged fields remain consistent with the approved baseline documents
- the cast-management files listed above are ready for their completion updates
