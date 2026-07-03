# STEP 3 — Knowledge Boundary and Relations

## Purpose

Produce a strict, usable baseline for what the character knows, what the character must not be treated as knowing, and which relationships shape the character's decisions.

## Read inputs from

- `<STORY_ROOT>/state/character_baselines/CHARACTER_CONCEPT.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_WORLD_ROLE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_BEHAVIOR_AND_VOICE.md`
- packaged characters under `<STORY_ROOT>/state/characters/`, when they exist

## Save output to

- `<STORY_ROOT>/state/character_baselines/CHARACTER_KNOWLEDGE_AND_RELATIONS.md`

## Skill use

- Use `the factory craft doc core/craft/character-memory-ledger.md` skill after completing this step to record the character's knowledge boundaries and update memory ledgers.

## Task

Read the input baselines and write a concrete knowledge-and-relations contract for the character.

Use only information supported by the inputs. Do not invent biography, hidden history, or extra social structure.

The output must let later steps answer these questions without reinterpretation:

- What facts, systems, places, roles, dangers, and norms does this character already know?
- What facts are absent, unknown, hidden, mistaken, or off-limits for this character?
- Which individuals, groups, institutions, rivals, allies, dependents, protectors, users, watchers, or misreaders matter most?
- What practical pressure comes from each relation?
- What social pressure is most likely to steer the character's behavior in scenes and choices?

Keep the content local to this step. Do not add worldbuilding outside the character's own knowledge boundary and relation map.

If a category has no supported content, write `NONE`.

## Required output blocks

### `KNOWLEDGE ALLOWED`

List the concrete things this character definitely knows, understands, recognizes, or can safely act on.

Write short bullets. Each bullet must state one usable fact or competence.

Include only knowledge that is explicitly supported by the input files.

### `KNOWLEDGE NOT ALLOWED`

List the concrete things this character definitely does not know, cannot assume, or should not be treated as having access to.

Write short bullets. Each bullet must state one clear boundary.

Use this block to prevent later steps from accidentally giving the character privileged knowledge, secret facts, or unearned certainty.

### `RELATION MAP`

List the major people or groups that matter to this character.

For each relation, include all of the following in one bullet:

- `who`: the person, group, institution, or role
- `tie`: the relationship type
- `effect`: the practical effect on the character's life, choices, status, safety, work, or resources

Only include relations that are supported by the inputs or directly implied by the character's role.

### `SOCIAL PRESSURES`

List the strongest pressures that shape this character's decisions.

Cover only pressures that are concrete and scene-relevant, such as:

- obligation
- dependence
- surveillance
- reputation
- hierarchy
- debt
- fear of punishment
- loyalty
- duty
- family expectation
- workplace pressure
- faction pressure

Each bullet must name the pressure and state how it affects the character's likely choices.
