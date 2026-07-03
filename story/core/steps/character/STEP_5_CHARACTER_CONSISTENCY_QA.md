# STEP 5 — Character Consistency QA

## Purpose

Verify that the saved character baseline is internally consistent, package-aligned, and ready for later story workflows without requiring reinterpretation.

## Read inputs from

- `<STORY_ROOT>/state/character_baselines/CHARACTER_CONCEPT.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_WORLD_ROLE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_BEHAVIOR_AND_VOICE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_KNOWLEDGE_AND_RELATIONS.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_PACKAGING_REVIEW.md`
- `<STORY_ROOT>/state/characters/<character_id>.json`
- `<STORY_ROOT>/state/characters/index.json`

## Save output to

- `<STORY_ROOT>/state/character_baselines/CHARACTER_QA.md`

## Skill use

- No skill required for this step.

## Task

Audit the completed character baseline against the saved character record and packaging review.

Decide whether the character is ready for:

- chapter writing
- transition or handoff work
- memory and knowledge tracking

Report only concrete mismatches, missing support, or readiness blockers.

## Required output blocks

### `REVIEW SUMMARY`

Write 1–3 sentences that name the overall QA result and the main reason for it.

### `PASS OR FAIL`

Write exactly one of:

- `PASS`
- `FAIL`

### `ISSUES`

If there are no issues, write:

- `None`

If there are issues, list each one as a bullet with:

- the concrete problem
- the exact baseline layers involved
- why it blocks consistency or readiness

Use this format:

- `Issue: <problem>`
  - `Layers: <layer A> / <layer B> / ...`
  - `Impact: <why this matters>`

### `FIXES`

If there are no fixes, write:

- `None`

If there are fixes, list one bullet per issue with the smallest specific change that would resolve it.

Use this format:

- `Fix: <specific change>`
  - `Target: <file or baseline section>`
  - `Result: <what becomes consistent after the change>`

## QA checks

Check each item directly and mark it as supported, unsupported, or conflicting.

- `world role -> behavior`
  - The character's stated role must explain or support the behavior pattern.
- `behavior -> voice`
  - The speaking style must fit the character's social position, habits, and tone.
- `knowledge -> relations`
  - The character's knowledge limits must match who they know, trust, oppose, or avoid.
- `baseline -> scene effect`
  - The character must affect scenes through decisions, pressure, or leverage, not just descriptive flavor.
- `package -> saved baseline`
  - The packaged character must match the saved character record and not add unsupported traits.
- `memory / knowledge readiness`
  - The character must have enough concrete facts for later chapter work, state tracking, and continuity use.

For each failed check, identify the exact mismatch and the affected layer(s).
