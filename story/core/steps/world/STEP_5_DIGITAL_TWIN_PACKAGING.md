# STEP 5 — Digital Twin Packaging

## Purpose

Package the saved world baseline into twin-facing artifacts that can be read without rebuilding the world model.

## Read inputs from

- `<STORY_ROOT>/state/world_baselines/WORLD_CONCEPT.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_RULES.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_GEOGRAPHY.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_INSTITUTIONS.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_LOGISTICS.md`
- existing twin-facing files under `<STORY_ROOT>/story_world/` when this is a revision pass

## Save output to

Write twin-facing artifacts under:

- `<STORY_ROOT>/story_world/seed_entities.json`
- `<STORY_ROOT>/story_world/seeds/*.json`
- supporting documentation under `<STORY_ROOT>/story_world/`

## Skill use

- No skill required for this step.

## Task

Turn the saved world baseline into a compact twin-facing package.

Build the package so a fresh reader can identify:

- the first canonical entities the twin should know
- the grouped seed records that organize the world
- the stable facts that must stay unchanged across reuse
- the main relations between entities, places, institutions, routes, and facts
- the short query guidance needed to read the package correctly

If this is a revision pass, update the existing twin-facing files so they
stay consistent with the current baseline — and MERGE, never blind-
regenerate: the package is a live database after its first build
(`<FACTORY>/modules/twin-db/README.md`), and chapters write records back
into it. `<STORY_ROOT>/story_world/changelog.jsonl` shows which records
chapters added (`source: chapter:<STEM>`); a revision pass must preserve
them unless the current baseline explicitly contradicts one, in which case
report the conflict instead of silently deleting. The USER sovereignty file
`<STORY_ROOT>/state/WORLD_RULES.md` outranks both baseline and package.

## Required output blocks

### `SEED ENTITIES`

List the canonical entities the twin should recognize first.

For each entity, state:

- the entity name
- the entity type
- why it should be included in the twin package

### `SEEDS`

List the seed record groups and where each group is written.

For each group, state:

- the seed file path or documentation target
- what world layer it covers
- which entities or structures it groups together

### `FACTS`

List the stable world facts the twin package must preserve.

Each fact should be short, reusable, and concrete.

### `RELATIONS`

List the major links between entities, places, institutions, routes, or facts.

For each relation, state:

- the two sides of the relation
- the relation type
- why the relation matters for reuse

### `QUERY GUIDE`

State how later workflows should read or query the packaged twin.

Keep the guidance short and operational.

### `REFERENCES`

List the world-baseline artifacts used to build the package.
