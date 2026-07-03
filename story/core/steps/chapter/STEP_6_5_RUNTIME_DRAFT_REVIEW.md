# STEP 6.5 — Runtime Draft Acceptance

## Purpose

Review the saved runtime draft and decide whether it passes.

## Read inputs from

Review the saved runtime draft artifact:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_zh.md`

If the draft was split into multiple scene-cluster files, review every file that shares the same `<ARTIFACT_STEM>` prefix.

## Save output to

Write the acceptance result to:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check whether the saved runtime draft is complete, readable, and consistent with the STEP 6 runtime-draft contract.

## Acceptance criteria

### File and coverage

This step passes when:

- the runtime draft file exists
- the saved draft covers the chapter scene clusters that were written for this pass
- the draft is readable as scene prose rather than graph notes

### Runtime point of view

This step passes when:

- player-facing narration reads in second person with `你`
- protagonist names or third-person references appear only inside spoken dialogue when another character uses them that way
- the draft stays in zh-Hant for this pass

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

### INTRO handling

If the chapter includes an `INTRO`, this step passes when:

- the opening still functions as chapter start
- the opening still covers time cue, place cue, current errand or obligation, key object or task destination, one abnormal note for today, and immediate next move

## Required stop condition

- write a short acceptance note that says `STEP 6.5 PASS` or `STEP 6.5 FAIL`
- on `FAIL`, state the blocker clearly
