# STEP 6.75 — Staging & Realization Acceptance

## Purpose

Review the saved staging plan and decide whether it is ready for mechanical
runtime landing.

This gate checks shootability, binding decisions, pacing, and emotional
fidelity. It never edits the staging plan.

## Read inputs from

Read:

- `adapters/<PROJECT_ID>/VISUAL_GRAMMAR.md` — if missing or marked
  `NOT_AVAILABLE`, STOP and report `BLOCKED_BY_PROFILE`
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_STAGING_PLAN.md`
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_zh.md`
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_REVIEW.md`
- `<STORY_ROOT>/chapter_event_graphs/<ARTIFACT_STEM>.md`
- `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`, if present
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DELIVERY_PLAN.md`, if
  present and synchronized by STEP 1

## Save output to

Write the acceptance result to:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_STAGING_REVIEW.md`

The note must say `STEP 6.75 PASS` or `STEP 6.75 FAIL`.

## Skill use

- No skill required for this step.

## Task

Check whether the saved staging plan is complete, engine-shootable, and
faithful to the approved draft's emotional jobs.

## Acceptance criteria

### Visual grammar compliance

This step passes when:

- every operation in `STAGING OPERATIONS` is a primitive declared by
  `VISUAL_GRAMMAR.md`
- every camera operation is on the camera whitelist
- every actor operation is on the actor whitelist
- the plan does not use disallowed film-language instructions as if they
  were executable staging

Fail when the plan contains an operation the target visual grammar cannot
shoot and does not mark it as an engineering dependency.

### Cutscene / player-operation binding

This step passes when:

- every covered beat has a final binding
- the binding reason follows the STEP 6.7 standard: player-delivered emotion
  becomes `player_operation`; arranged timing / composition becomes
  `cutscene`
- any override of the delivery plan's rough channel intent is named and
  justified

Fail when a beat's binding is missing, arbitrary, or chosen from channel habit
instead of the beat's delivery method.

### Emotional acceptance（情感驗收）

Applies whenever the chapter has a beat sheet
(`<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`); without one,
record `NO BEAT SHEET — emotional acceptance not applicable`.

This step passes when:

- each covered beat's "why this feeling arrives" is still staged by a visible
  operation, player action, prop, line, emoji, sound, or pause
- hold beats stay held: no acquisition, reward, or premature payoff has been
  introduced during restaging
- release beats still release where the beat sheet placed them
- any restage preserves the beat's emotional job instead of merely replacing
  it with a shootable but different moment

### Cannot collisions

This step passes when:

- every forbidden presentation from the STEP 6 draft is listed in
  `CANNOT COLLISIONS`
- each collision has exactly one clear exit:
  - `restage` with a concrete whitelist operation sequence, or
  - `engineering_dependency` with the missing runtime capability named

The STEP 6 draft's use of cinematic language is not a failure by itself. It
only fails here if STEP 6.7 silently carries an unshootable instruction
forward or restages it into the wrong emotional beat.

### Pacing calibration

This step passes when:

- every covered beat has `stay`, `speak`, or `mixed` pacing
- dialogue-heavy holds have been challenged against the visual grammar's
  native pacing
- player movement and environment carry beats that should be felt through
  the player's own pacing
- estimated durations are plausible enough for STEP 7 to translate

## Required stop condition

- write a short acceptance note that says `STEP 6.75 PASS` or
  `STEP 6.75 FAIL`
- on `FAIL`, state the blocker clearly and route back to STEP 6.7
