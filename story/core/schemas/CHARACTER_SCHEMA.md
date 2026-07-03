# Character Schema

This file defines the canonical target schema for character creation output.

Use it as the packaging target for:

- `<STORY_ROOT>/state/CHARACTER_CREATION_WORKFLOW.md`

Do not treat older character JSON files as authoritative schema by themselves.
They may contain useful content, but this file defines the current packaging contract.

## Purpose

The schema should support three downstream needs at once:

1. chapter creation
2. chapter transition and memory work
3. writing-facing character consistency

The schema is not meant to be a maximal lore dump.
It is meant to be a usable baseline for later workflows.

## Required Top-Level Fields

- `id`
- `name`
- `aliases`
- `concept`
- `world_position`
- `behavior`
- `knowledge`
- `relationships`

## Optional Top-Level Fields

- `capabilities`
- `pressure_points`
- `hooks`
- `assumptions`

## Field Definitions

### `id`

- stable character id
- use project naming such as `ch_player`, `ch_player_sister`

### `name`

- primary name used by authoring tools

### `aliases`

- alternate names, titles, public-facing labels
- include names likely to appear in dialogue or query contexts

### `concept`

Required subfields:

- `role_in_story`
- `social_read`
- `core_pressure`
- `visible_contradiction`

This block answers:

- why this character matters
- how other people read them
- what pressure defines daily life
- what visible contradiction can drive scenes

### `world_position`

Required subfields:

- `household_or_institution`
- `daily_role`
- `range_of_movement`
- `ordinary_obligations`

This block anchors the character inside the accepted world baseline.

### `behavior`

Required subfields:

- `observable_habits`
- `pressure_reaction`
- `speaking_pattern`
- `avoidances`

This block should be scene-usable.
It should describe how the character can be recognized in action and speech.

### `knowledge`

Required subfields:

- `knows`
- `does_not_know`
- `blind_spots`

This block should be explicit enough for chapter preflight and later memory tracking.

### `relationships`

Required type:

- array of relationship objects

Each relationship object should include:

- `target`
- `stance`
- `dependency_or_leverage`
- `risk`

### `capabilities`

Optional but recommended when the character's practical abilities affect scenes.

Suggested subfields:

- `combat`
- `social`
- `practical`
- `limits`

### `pressure_points`

- concrete triggers that destabilize this character
- should be directly usable by story design

### `hooks`

- reusable story hooks tied to this character
- should describe action-facing triggers, not vague flavor

### `assumptions`

- working assumptions made during creation
- use when the setting or future plot may later falsify the current read

## Schema Principles

- prefer observable and playable fields over abstract personality prose
- prefer explicit knowledge boundaries over implied omniscience
- prefer relation objects over freeform social summary
- keep the schema stable enough that future workflows can read it directly

## Packaging Rule

Character packaging should target:

- `<STORY_ROOT>/state/characters/<character_id>.json`
- `<STORY_ROOT>/state/characters/index.json`

If older character JSON files use a different grouping, treat them as migration candidates rather than schema authority.
