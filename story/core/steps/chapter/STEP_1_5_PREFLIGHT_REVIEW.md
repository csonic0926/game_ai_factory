# STEP 1.5 — Chapter Preflight Acceptance

## Purpose

- check that the saved preflight is ready to support chapter work
- confirm the chapter start, knowledge limits, and world supports are concrete

## Read inputs from

Read the saved preflight artifact:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT.md`

## Save output to

Write the acceptance result to:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT_REVIEW.md`

The note must say `STEP 1.5 PASS` or `STEP 1.5 FAIL`.

## Skill use

- No skill required for this step.

## Task

Review the saved preflight and decide whether it is complete enough to pass.

A passing preflight gives the chapter:

- one clear chapter start and time span
- concrete allowed knowledge and forbidden knowledge
- concrete world-grounding supports
- assumptions only for missing required source material

## Acceptance criteria

### `CHAPTER TIMEBOX`

Pass when the block states:

- where the chapter starts
- what span of time the chapter covers
- what is in scope for the chapter

### `KNOWLEDGE ALLOWED` and `KNOWLEDGE NOT ALLOWED`

Pass when both blocks are:

- concrete
- non-overlapping
- specific enough to guide chapter design
- limited to source-supported knowledge

### `WORLD GROUNDING`

Pass when the block names concrete supports such as:

- locations
- recurring NPCs
- objects
- routines
- institutions
- pressure patterns
- time-flow facts

### `ASSUMPTIONS`

Pass when the block:

- names the missing source clearly
- states only the minimum needed assumption
- stays at constraint level

## Required stop condition

- write a short acceptance note that says `STEP 1.5 PASS` or `STEP 1.5 FAIL`
- on `FAIL`, state the blocker clearly
