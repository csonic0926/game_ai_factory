# STEP 8 — Quoted Dialogue Revision

## Purpose

Revise landed quoted dialogue so spoken lines sound more like the character who says them, while keeping chapter meaning and routing intact.

## Read inputs from

Read the latest landed chapter artifacts relevant to dialogue revision:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_LANDING.md`
- touched timeline / locale files for landed runtime review
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_zh.md` when the pre-landing runtime draft is needed for comparison

Before revising dialogue, read `<ADAPTER>/GLOSSARY.csv` when it exists.
It is the sole canonical proprietary-term source. Missing means
`NOT_AVAILABLE` and preserves the old behavior. Do not infer or override
authoritative terms from `WORLD_RULES.md`, `STYLE_GUIDE.md`, shipped locale
prose, or another artifact.

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
- glossary canon forms marked `dialogue_protected=true`
- glossary `banned` forms remaining absent

## Revision standard

Revise quoted lines so they:

- sound like the character who speaks them in this world and pressure
- preserve the current pragmatic function of the line
- stay aligned in intent across all `<SHIPPED_LOCALES>` when multilingual landing is present
- use the glossary's registered form in each locale and obey its `register`
  and `speaker_scope`; unregistered new vocabulary becomes a pending
  nomination, never a worker-made canon decision
- remain compatible with the already-landed scene logic

## Required checks

- only quoted lines are revised unless a minimal adjacent adjustment is required for coherence
- no new reveal is introduced earlier than before
- no route meaning changes
- no character voice collapses into generic dialogue
- the revision log records which lines were changed and why

## Spoken-fluency pass (required before STEP 8.5)

After the revision is saved, the revised quoted lines must pass
`core/craft/spoken-fluency.md` BEFORE the STEP 8.5 gate reads them. The
pass runs as a SEPARATE fresh worker dispatched by the orchestrator — the
STEP 8 worker must NOT polish its own lines (same independence principle
as the review gates). The fluency worker repairs sentence grammar of the
touched dialogue text only — routing, ids, keys, and file structure stay
untouched — across all `<SHIPPED_LOCALES>`, and writes the comparison log
to:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_DIALOGUE_REVISION_FLUENCY.md`

For default clean-room mode, the orchestrator extracts applicable protected
and banned forms from the glossary into a plain-language constraint list; the
clean-room worker does not read the CSV. The canon-aware back-check reads the
glossary, runs `scripts/glossary_check.py`, and records the protected-term and
locale correspondence result in the same fluency log.
