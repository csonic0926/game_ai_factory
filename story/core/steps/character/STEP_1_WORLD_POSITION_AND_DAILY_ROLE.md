# STEP 1 — World Position and Daily Role

## Purpose

Place the character inside the accepted world baseline in concrete, usable daily-life terms.

## Read inputs from

- `<STORY_ROOT>/state/character_baselines/CHARACTER_CONCEPT.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_CONCEPT.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_RULES.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_GEOGRAPHY.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_INSTITUTIONS.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_LOGISTICS.md`

## Save output to

- `<STORY_ROOT>/state/character_baselines/CHARACTER_WORLD_ROLE.md`

## Skill use

- No skill required for this step.

## Task

Turn the character concept and the accepted world baseline into one concrete world-position contract for the character.

Use only information supported by the input files. If the inputs do not fully specify a detail, make the smallest safe inference and mark it as an assumption in the output.

Write for downstream steps, not prose readers. The result must let later agents answer:

- what social or institutional slot the character occupies
- what daily function defines the character’s ordinary life
- where the character can normally move without explanation
- who the character reports to, serves, depends on, or avoids
- what a normal day looks like in practical terms

Keep the language specific, grounded, and concrete. Avoid abstract labels unless the world baseline clearly uses them.

## Required output blocks

### `WORLD POSITION`

State the character's exact place inside the world's social, household, institutional, trade, service, faction, or class structure.

Include:

- the character’s role label or standing
- the group, place, or organization that defines that standing
- the character’s relationship to that structure

Keep this block to 2–4 sentences.

### `DAILY ROLE`

State the ordinary work, duty, service, study, labor, patrol, or recurring routine that defines the character’s normal day.

Include:

- the core activity performed most days
- what the character is expected to maintain, produce, protect, deliver, learn, or monitor
- the usual rhythm or time pattern if it is known

Keep this block to 2–4 sentences.

### `NORMAL RANGE OF MOVEMENT`

State where the character can normally go and what ordinary limits shape that movement.

Include:

- the ordinary locations the character may enter or travel through
- the places that are routine, restricted, or unusual for them
- the practical limits on movement created by rank, duty, law, habit, geography, or supervision

Keep this block to 2–3 sentences.

### `ORDINARY OBLIGATIONS`

State the duties, dependencies, reporting lines, or routine demands that the character normally lives under.

Include:

- who the character answers to or relies on
- what obligations are routine rather than exceptional
- what the character must not neglect if they want to keep their place

Keep this block to 2–4 sentences.

### `ASSUMPTIONS`

If any input detail was missing or implied, list the smallest safe assumptions used to complete the step.

If no assumptions were needed, write `None`.
