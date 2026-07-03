# STEP 1.5 — World Position Review

## Purpose

Review the saved character world position and decide whether it is concrete enough to support later behavior, relations, and scene placement work.

## Read inputs from

- `<STORY_ROOT>/state/character_baselines/CHARACTER_WORLD_ROLE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_CONCEPT.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_RULES.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_GEOGRAPHY.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_INSTITUTIONS.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_LOGISTICS.md`

## Save output to

- `<STORY_ROOT>/state/character_baselines/CHARACTER_WORLD_ROLE_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Read the saved world-position material and write a focused review that states whether the character is now anchored in the world.

The review must do two things:

1. judge the current material against the checks below
2. produce an explicit pass/fail review artifact with the blocker, if any

## Required output blocks

Write `CHARACTER_WORLD_ROLE_REVIEW.md` with these blocks in this order:

1. `## Review result`
   - one line: `STEP 1.5 PASS` or `STEP 1.5 FAIL`
2. `## Summary`
   - 2-4 sentences on what is already working or what is still missing
3. `## Blockers`
   - include only if the result is `FAIL`
   - list the specific blocker or blockers that prevent passing
4. `## Review checks`
   - list each check below with `PASS` or `FAIL`
   - add a short note for any failed check

## Review checks

Use these checks directly as the review standard.

### World position

- The character's place in the world is legible from the saved material.
- The world position fits the accepted world baseline.
- The character does not feel detached from the world substrate.

### Daily role

- The character has a concrete ordinary role or routine.
- The daily role can be imagined in scene terms.
- The daily role fits the world's institutions, rules, and logistics.

### Range of movement

- The character's normal movement range is clear.
- The range fits the accepted geography and ordinary constraints.
- Later steps would not need to guess where this character can naturally appear.

### Ordinary obligations

- The character's ordinary obligations are concrete.
- Reporting lines, dependencies, or routine demands are readable.
- The obligations help explain how this character lives inside the world.

## Review decision rule

- Pass only when every review check passes.
- Fail when any review check is unclear, unsupported, or incompatible with the world baseline.
- On failure, name the main blocker in `## Blockers` and keep the note specific to the missing world-position grounding.
