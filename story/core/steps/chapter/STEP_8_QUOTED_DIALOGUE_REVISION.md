# STEP 8 — Quoted Dialogue Revision

## Purpose

Revise landed quoted dialogue so spoken lines sound more like the character who says them, while keeping chapter meaning and routing intact.

## Read inputs from

Read the latest landed chapter artifacts relevant to dialogue revision:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_LANDING.md`
- touched timeline / locale files for landed runtime review
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_zh.md` when the pre-landing runtime draft is needed for comparison

## Save output to

Write the revised runtime data back to the touched chapter-local rows in:

- the runtime timeline and locale files defined by the adapter `LANDING_SPEC.md`

Write one dialogue revision log to:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_DIALOGUE_REVISION.md`

## Skill use

- Use `the factory craft doc core/craft/quoted-dialogue.md` for quoted-line revision.

## Task

Revise only quoted dialogue lines for the current chapter.

Keep these invariants fixed:

- routing
- event ids and timeline structure
- knowledge order
- scene meaning
- speaker identity
- non-quoted narration unless a quoted line cannot work without a minimal adjacent adjustment

## Revision standard

Revise quoted lines so they:

- sound like the character who speaks them in this world and pressure
- preserve the current pragmatic function of the line
- stay aligned in intent across all `<SHIPPED_LOCALES>` when multilingual landing is present
- remain compatible with the already-landed scene logic

## Required checks

- only quoted lines are revised unless a minimal adjacent adjustment is required for coherence
- no new reveal is introduced earlier than before
- no route meaning changes
- no character voice collapses into generic dialogue
- the revision log records which lines were changed and why
