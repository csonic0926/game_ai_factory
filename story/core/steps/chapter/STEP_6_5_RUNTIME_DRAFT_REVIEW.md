# STEP 6.5 — Runtime Draft Acceptance

## Purpose

Review the saved runtime draft and decide whether it passes.

## Read inputs from

Review the saved runtime draft artifact:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_zh.md`

If the draft was split into multiple scene-cluster files, review every file that shares the same `<ARTIFACT_STEM>` prefix.

When the chapter runs in assignment mode, ALSO read the source of emotional
truth:

- `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`

Also read the spoken-fluency log written by the pass that runs between
STEP 6 and this gate:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_FLUENCY.md`

Read `<ADAPTER>/GLOSSARY.csv` when it exists. Missing means
`NOT_AVAILABLE`, so glossary-only checks are skipped without changing legacy
behavior.

## Save output to

Write the acceptance result to:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check whether the saved runtime draft is complete, readable, and consistent with the STEP 6 runtime-draft contract.

Scope boundary: this gate reviews the draft's emotional and content fidelity,
readability, draft form, and scene continuity. It does **not** review whether
the target engine can literally shoot every image. Cinematic language such as
"wide shot", "parallel boats", or "close-up" is not a STEP 6.5 failure by
itself, because STEP 6 is medium-independent; STEP 6.7 / 6.75 own visual
grammar realization. Fail only when such language also breaks this gate's own
content, emotional, or readability criteria.

## Acceptance criteria

### File and coverage

This step passes when:

- the runtime draft file exists
- the saved draft covers the chapter scene clusters that were written for this pass
- the draft is readable as scene prose rather than graph notes

### Runtime point of view / draft form

The draft form is adapter-driven: check the adapter's `STYLE_GUIDE.md` for a
"runtime draft form" section and review against THAT form. Only when the
adapter defines no form, apply the default below.

This step passes when:

- the draft follows the adapter-prescribed form (e.g. screenplay format:
  scene headings + third-person stage directions + dialogue lines); default
  when none is prescribed: player-facing narration in second person with `你`
- protagonist names or third-person references appear only where the
  prescribed form allows them (in the default form: only inside spoken
  dialogue when another character uses them that way)
- the draft stays in `<PRIMARY_LOCALE>` for this pass

### Scene staging

This step passes when:

- the scene places `你` in a readable physical situation
- physically present characters are introduced on-screen
- visible action, dialogue, gesture, position, or object state carries the scene forward
- information that enters the scene is attached to an observable moment

### Line writing

This step passes when:

- lines land one dominant readable beat at a time
- line-to-line continuity is strong
- the prose advances through visible change instead of summary compression

### Emotional acceptance（情感驗收）

Applies whenever the chapter has a beat sheet
(`<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`); without one,
record `NO BEAT SHEET — emotional acceptance not applicable` and move on.

This step passes when, for the scenes covered by this draft:

- each covered beat can be pointed at in the draft: name the beat and the
  draft passage that transmits it — a beat that is merely mentioned or
  explained is NOT transmitted (`core/NARRATIVE_FOUNDATIONS.md` #1: the
  passage must work through a concrete picture, not through a carrying
  token that needs explaining first)
- the curve's holds and releases survived: a HOLD (壓) beat's passage
  releases nothing (no acquisition, no reward, no premature payoff), and
  the RELEASE (放) lands where the beat sheet put it — one early release
  anywhere in the draft is a FAIL even if every other check passes
- no beat covered by this draft's scenes is silently missing

### Spoken fluency（唸稿抽查）

This step passes when:

- the spoken-fluency pass ran as its own worker: the fluency log exists at
  `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_FLUENCY.md` with one
  original → repaired comparison entry per changed line
- sampling check: pick THREE quoted lines from the draft and read each one
  aloud. If any line reads as design-annotation register — subject or
  preposition elided past what speech allows, modifier clauses stacked
  before a noun, several information foci strung into one sentence with
  commas and dashes, a verb collocation no one says — this gate FAILS and
  routes back to STEP 6. Judge against the adapter `STYLE_GUIDE.md`
  spoken-grammar section when present, else the generic rules in
  `core/craft/spoken-fluency.md`.
- meaning survived the repair: spot-check the log's comparison entries —
  beat, pragmatic function, information content, and character voice are
  unchanged between original and repaired lines

### Glossary and term nomination

When `<ADAPTER>/GLOSSARY.csv` exists, run:

`python3 <FACTORY>/scripts/glossary_check.py --glossary <ADAPTER>/GLOSSARY.csv <artifact>`

This step passes when:

- exact `banned` forms are absent;
- every applicable canon `dialogue_protected=true` form that entered the
  clean-room pass is present unchanged in the result (verify the fluency log's
  extracted list and protected-term diff);
- the chosen register variant is allowed by `speaker_scope`;
- en/ko counterparts, when present in this artifact, use the registered
  glossary forms rather than a locale-file reverse-engineering guess.

Exact checker failures are failures. Synonym replacement, speaker/register
fit, and unregistered vocabulary remain gate judgments. If the draft
introduces an unregistered world noun, classifier convention, or register
variant, do **not** fail an otherwise valid draft merely because it is new.
Require a `status=pending` glossary nomination, or name the candidate and its
context in the review for USER ruling. The review worker does not edit the
glossary. Only the USER may promote a pending row to `canon`/`banned`; on a
world-term promotion, remind the USER to update `WORLD_RULES.md`.

### INTRO handling

If the chapter includes an `INTRO`, this step passes when:

- the opening still functions as chapter start
- the opening still covers time cue, place cue, current errand or obligation, key object or task destination, one abnormal note for today, and immediate next move

## Required stop condition

- write a short acceptance note that says `STEP 6.5 PASS` or `STEP 6.5 FAIL`
- on `FAIL`, state the blocker clearly
