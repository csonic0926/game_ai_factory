# STEP 7.5 — Landing Integrity Acceptance

## Purpose

Review the landed runtime data and decide whether it passes.

## Read inputs from

Read the adapter landing contract FIRST, before any other input:

- `adapters/<PROJECT_ID>/LANDING_SPEC.md` — all landing details (target files, id & key grammar, integrity checks) defer to it. If it is missing or marked `NOT_AVAILABLE`, STOP and report `BLOCKED_BY_PROFILE`.

Review:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_STAGING_PLAN.md`
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_STAGING_REVIEW.md`
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_LANDING.md`
- the target runtime files and locale storage defined by the adapter `LANDING_SPEC.md`
- the chapter-entry wiring files defined by the adapter `LANDING_SPEC.md` when chapter start routing or intro-backed chapter entries were part of the landing

## Save output to

Write the acceptance result to:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_LANDING_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check whether the landed runtime data is complete, mechanically valid,
consistent with the STEP 7 landing contract, and faithful to the approved
STEP 6.7 staging plan.

## Acceptance criteria

### Landing log

This step passes when:

- the landing log exists
- the landing log records produced ids, row ranges, routing targets, and touched files clearly enough to audit the landing
- the landing log maps every STEP 6.7 operation group to landed runtime data
  or to a named engineering dependency

### Runtime rows and references

This step passes when:

- landed runtime rows exist in actual runtime data
- every referenced runtime event id resolves in the target runtime files
- every referenced story/timeline profile id resolves in the target runtime files
- every referenced locale key resolves in the locale storage
- every required location-node target resolves in the target runtime files
- the integrity checks defined by the adapter `LANDING_SPEC.md` pass

### Staging-plan fidelity

This step passes when:

- the saved staging review says `STEP 6.75 PASS`
- every landed cutscene, player-operation, scene-layout, dialogue, emote,
  sound, transition, and text element corresponds to an approved staging-plan
  operation
- STEP 7 did not invent new camera blocking, actor movement, pacing, or
  cutscene/player-operation binding
- any staging-plan operation that could not land is recorded as an explicit
  engineering dependency instead of silently dropped or converted to a
  different channel

Fail when landed runtime data re-stages the scene, drops an approved
operation without explanation, or changes player-operation beats into
cutscenes (or the reverse) without going back through STEP 6.7.

### Timeline integrity

This step passes when:

- each landed timeline profile is readable as one playable sequence
- each landed story line keeps one-click runtime rhythm
- the last row of each landed timeline profile ends with a valid continuation or close contract

### Routing integrity

This step passes when:

- chapter start wiring exists when the landing required in-game test entry wiring
- location-transition nodes function as location transitions instead of broken or dangling jumps
- linked spine segments preserve runtime continuity where the chapter requires it

### Locale landing

This step passes when:

- newly landed locale keys have values for all `<SHIPPED_LOCALES>`, authored in `<PRIMARY_LOCALE>`, per the locale landing rules in the adapter `LANDING_SPEC.md`
- narration-type keys read as runtime narration
- choice-type keys read as concrete clickable action wording
- location-description keys frame the present node decision
- final runtime prose does not leave graph-layer protagonist labels in player-facing text

## Required stop condition

- write a short acceptance note that says `STEP 7.5 PASS` or `STEP 7.5 FAIL`
- on `FAIL`, state the blocker clearly
