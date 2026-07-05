# STEP 3 — Chapter Spine

## Purpose

Shape the selected story line into one chapter spine across the declared
time frame, and save it as the chapter source's spine artifact.

## Read inputs from

Read:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_STORY_LINE.md`

## Save output to

Write:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_CHAPTER_SPINE.md`

## Skill use

- No skill required for this step.

## Task

Turn the selected story line into a chapter spine.

The spine covers the time frame declared in the story-line file, divided
into the ordered segments sketched there (refine the segment cut if the
line needs it, but do not silently change the declared time frame — a
frame change routes back through STEP 2). Segments carry names in the
story's own words: times of day, days, places along a route, stages of an
event — whatever the story itself would use. Use as many segments as the
frame needs; do not pad a short frame or flatten a long one into three
spans by habit.

Build the spine so it states:

- how the line begins in the first segment
- where the bend lands, and how each segment redirects, delays, or
  complicates what the player is trying to do
- how the chapter avoids a clean return to normal by its final segment
- what concrete thing carries from each segment into the next
- what the player carries out of the chapter

Use concrete supports from the selected line and the preflight, such as:

- locations
- recurring NPCs
- objects
- routines
- institutions
- pressure patterns
- time-flow facts

## Required output blocks

Always include:

- one `SEGMENT — <name>` block per declared segment, in chapter order
- `THROUGHLINE`

## Block definitions

### `SEGMENT — <name>` (repeated, ordered)

For the first segment, state:

- the starting situation
- the intended task or obligation
- the first visible bend

For each middle segment, state:

- what the player is still trying to finish
- what redirects, delays, or complicates that effort
- the concrete thing that carries into the next segment

For the final segment, state:

- what should have been normal closure
- what now blocks that closure (or transforms it)
- the posture the player carries out of the chapter

Every segment must do distinct work. If two adjacent segments state the
same effort with the same pressure and nothing new carries between them,
merge them.

### `THROUGHLINE`

State:

- the original ordinary track
- the bending line across the whole time frame
- the consequence carried out of the chapter
