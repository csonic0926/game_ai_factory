# STEP 8.5 — Quoted Dialogue Revision Acceptance

## Purpose

Review the saved quoted-dialogue revision and decide whether it passes.

## Read inputs from

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_DIALOGUE_REVISION.md`
- touched chapter-local rows in the runtime timeline and locale files defined by the adapter `LANDING_SPEC.md`

## Save output to

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_DIALOGUE_REVISION_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check whether the quoted-dialogue revision is complete, speaker-faithful, and safe to hand to final QA.

## Acceptance criteria

### Dialogue scope

This step passes when:

- the revision is limited to quoted dialogue lines, except for minimal adjacent coherence fixes when needed
- the revision log clearly records what changed

### Character voice

This step passes when:

- revised lines sound more like the specific speaker
- spoken lines keep their pragmatic role and scene pressure

### Structural safety

This step passes when:

- routing is unchanged
- knowledge order is unchanged
- scene meaning is unchanged
- no new contradiction is introduced into the landed chapter

## Required stop condition

- write a short note that says `STEP 8.5 PASS` or `STEP 8.5 FAIL`
- on `FAIL`, state the blocker clearly
