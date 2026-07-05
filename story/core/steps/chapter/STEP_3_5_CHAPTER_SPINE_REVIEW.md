# STEP 3.5 — Chapter Spine Acceptance

## Purpose

Check whether the saved chapter spine is ready to accept into chapter source.

## Read inputs from

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_CHAPTER_SPINE.md`
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_STORY_LINE.md` (for the declared time frame)

## Save output to

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_CHAPTER_SPINE_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Review the saved chapter spine and decide whether it passes.

A passing chapter spine:

- covers the time frame declared in the story-line file, with the spine's
  segments matching that declaration (a silently changed frame is a FAIL —
  frame changes route back through STEP 2)
- carries the selected line across the whole frame with no dead stretch
- gives every segment distinct work
- shows a concrete carry-over from each segment into the next
- ends in a posture that cannot simply reset to normal

## Acceptance criteria

### First `SEGMENT` block

Pass when it includes:

- a starting situation
- an intended task or obligation
- a first visible bend

### Each middle `SEGMENT` block

Pass when it includes:

- the ongoing intended effort
- the redirect, delay, or complication
- a concrete carry-over into the next segment

Fail when two adjacent segments repeat the same effort under the same
pressure with nothing new carried between them.

### Final `SEGMENT` block

Pass when it includes:

- the expected normal closure
- what blocks or transforms that closure
- the posture the player carries out of the chapter

### `THROUGHLINE`

Pass when this block includes:

- the original ordinary track
- the bending line across the whole time frame
- the consequence carried out of the chapter

## Required stop condition

- Write a short acceptance note that says `STEP 3.5 PASS` or `STEP 3.5 FAIL`.
- If the result is `FAIL`, name the blocker clearly.
