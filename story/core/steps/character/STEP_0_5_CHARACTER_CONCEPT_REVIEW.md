# STEP 0.5 — Character Concept Review

## Purpose

Review the saved character concept and decide whether it is ready for downstream character creation work.

## Read inputs from

- `<STORY_ROOT>/state/character_baselines/CHARACTER_CONCEPT.md`
- packaged characters under `<STORY_ROOT>/state/characters/`, when they exist

## Save output to

- `<STORY_ROOT>/state/character_baselines/CHARACTER_CONCEPT_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check whether the saved character concept is concrete, story-usable, and distinct enough to support later character-creation work. Compare against packaged characters only when they exist, and call out the closest overlap if the concept is not distinct.

## Required output blocks

The review output must include these blocks in this order:

### Result

- Write exactly one line:
  - `STEP 0.5 PASS`
  - or `STEP 0.5 FAIL`

### Blockers

- If the result is `FAIL`, list each blocking issue as a short bullet.
- If the result is `PASS`, write `None`.

### Review notes

- Add one short bullet per check below.
- Each bullet must state the check result and the specific evidence or missing detail from the concept.

## Review checks

### Character premise

- Confirm the concept states one clear core idea in plain terms.
- Reject concepts that only name an inspiration, archetype, or vibe without a concrete character premise.

### Social reading

- Confirm the concept explains how ordinary people in the world would read this character at a glance.
- Reject concepts that stay abstract or do not support staging, status, or placement.

### Daily-life pressure

- Confirm the concept includes one ordinary pressure, duty, or obligation that shapes daily life.
- Reject concepts where the pressure cannot be pictured in a scene or does not affect routine behavior.

### Visible contradiction

- Confirm the concept includes one visible contradiction that can drive later story use.
- Reject contradictions that are only abstract personality labels or are not grounded in role, life, or position.

### Distinctness

- Compare the concept against packaged characters when they exist.
- Reject concepts that functionally duplicate an existing packaged character unless the review notes make the difference explicit and defensible.

## Decision rules

- `PASS` only when every review check is satisfied.
- `FAIL` when any review check is missing, unclear, or duplicated by an existing packaged character.
- Keep the decision tied to the concrete evidence in the saved concept, not to broad preference or future possibilities.
