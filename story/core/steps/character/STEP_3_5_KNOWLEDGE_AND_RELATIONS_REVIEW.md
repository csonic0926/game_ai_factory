# STEP 3.5 — Knowledge and Relations Review Contract

## Purpose

Review the saved knowledge-and-relations baseline and decide whether it is ready for later packaging and chapter use.

## Read inputs from

- `<STORY_ROOT>/state/character_baselines/CHARACTER_KNOWLEDGE_AND_RELATIONS.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_WORLD_ROLE.md`
- `<STORY_ROOT>/state/character_baselines/CHARACTER_BEHAVIOR_AND_VOICE.md`
- packaged characters under `<STORY_ROOT>/state/characters/`, when they exist

## Save output to

- `<STORY_ROOT>/state/character_baselines/CHARACTER_KNOWLEDGE_AND_RELATIONS_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check the saved knowledge-and-relations baseline for clarity, usability, and consistency.

Treat this as a review-only contract:

- do not rewrite the baseline
- do not invent missing character facts
- do not broaden scope beyond knowledge, relations, and social pressure
- make the pass/fail decision from what is already written

## Required output blocks

Write the review artifact with these blocks in this order:

1. `# STEP 3.5 PASS` or `# STEP 3.5 FAIL`
2. `## Verdict`
3. `## Blockers`
4. `## Review notes`
5. `## Review checks`

### Verdict block

- State whether the baseline passes or fails.
- Keep the verdict to one short sentence.

### Blockers block

- If the step passes, write `None`.
- If the step fails, list the exact blocker(s) that prevent approval.
- Each blocker must be concrete and actionable.

### Review notes block

- Record the most important evidence from the source files.
- Keep this short and factual.
- Only include notes that support the verdict.

### Review checks block

- Copy the check headings below.
- Mark each check as `PASS` or `FAIL`.
- If a check fails, explain why in one line.

## Review checks

### Knowledge boundaries

PASS only if:

- the character’s known and unknown areas are explicit
- later chapter writing does not need to guess what the character already knows, can infer, or cannot know
- the knowledge boundary is usable without reinterpreting the baseline

### Relation map

PASS only if:

- the relation map is concrete
- the major ties have practical effect, not just labels
- later scenes can use the relation map without rebuilding it from scratch

### Social pressures

PASS only if:

- the social pressures are concrete enough to drive choices, conflict, hesitation, or obligation
- the pressures clearly come from readable people, ties, or structures

### Fit with the character baseline

PASS only if:

- the knowledge and relations fit the character’s world role and behavior baseline
- the character’s social world reads as one coherent person, not a separate note layer

## Required stop condition

- End with a short line that says `STEP 3.5 PASS` or `STEP 3.5 FAIL`
- If the result is `FAIL`, state the blocker immediately after that line
