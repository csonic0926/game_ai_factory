# Character Creation Step Output Map

This folder supports the step files used by `CHARACTER_CREATION_WORKFLOW.md`.
Use it as a local map for what to read, where to write, and how to report results.

## Read order before any new character work

Read these sources in order:

1. `<STORY_ROOT>/state/cast_management/CAST_CHARACTER_LIST.md`
2. `<STORY_ROOT>/state/cast_management/CAST_ACTION_REQUESTS.md`
3. `<STORY_ROOT>/state/cast_management/CHARACTER_CREATION_PROGRESS.md`
4. existing packaged characters in `<STORY_ROOT>/state/characters/`

## Working outputs before packaging

Write draft and approval-stage character notes to:

- `<STORY_ROOT>/state/character_baselines/`

Use these files for the working set:

- `CHARACTER_CONCEPT.md`
- `CHARACTER_WORLD_ROLE.md`
- `CHARACTER_BEHAVIOR_AND_VOICE.md`
- `CHARACTER_KNOWLEDGE_AND_RELATIONS.md`
- `CHARACTER_QA.md`

## Packaging outputs

When the baseline is accepted, write the final character data to:

- `<STORY_ROOT>/state/characters/<character_id>.json`
- `<STORY_ROOT>/state/characters/index.json`

Use the approved schema and template:

- `<STORY_ROOT>/state/CHARACTER_SCHEMA.md`
- `<STORY_ROOT>/state/templates/character.template.json`

## Reporting for each `STEP n` or `STEP n.5`

Report exactly:

- files created or updated
- pass or fail
- why the next step should or should not run

Keep the report short and tied to the files above.
