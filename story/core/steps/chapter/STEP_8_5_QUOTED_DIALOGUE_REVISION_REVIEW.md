# STEP 8.5 — Quoted Dialogue Revision Acceptance

## Purpose

Review the saved quoted-dialogue revision and decide whether it passes.

## Read inputs from

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_DIALOGUE_REVISION.md`
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_DIALOGUE_REVISION_FLUENCY.md` — the spoken-fluency log written by the pass that runs between STEP 8 and this gate
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

### Spoken fluency（唸稿抽查）

This step passes when:

- the spoken-fluency pass ran as its own worker: the fluency log exists at
  `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_DIALOGUE_REVISION_FLUENCY.md`
  with one original → repaired comparison entry per changed line
- sampling check: pick THREE revised quoted lines (across locales, not
  only `<PRIMARY_LOCALE>`) and read each one aloud. If any line reads as
  design-annotation register — subject or preposition elided past what
  speech allows, modifier clauses stacked before a noun, several
  information foci strung into one sentence, a verb collocation no one
  says — this gate FAILS and routes back to STEP 8. Judge against the
  adapter `STYLE_GUIDE.md` spoken-grammar section when present, else the
  generic rules in `core/craft/spoken-fluency.md`.
- meaning survived the repair: spot-check the log's comparison entries —
  beat, pragmatic function, information content, and character voice are
  unchanged between original and repaired lines

### Structural safety

This step passes when:

- routing is unchanged
- knowledge order is unchanged
- scene meaning is unchanged
- no new contradiction is introduced into the landed chapter

## Required stop condition

- write a short note that says `STEP 8.5 PASS` or `STEP 8.5 FAIL`
- on `FAIL`, state the blocker clearly
