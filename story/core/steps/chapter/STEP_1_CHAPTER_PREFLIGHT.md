# STEP 1 — Chapter Preflight

## Purpose

Lock the chapter start, time span, knowledge boundaries, and world supports for one chapter.

## Read inputs from

Read the source artifacts for the target chapter:

1. the sovereignty files `<STORY_ROOT>/state/WORLD_RULES.md` and
   `<STORY_ROOT>/state/NARRATIVE_DELIVERY.md` (legacy projects: the full
   `<STORY_ROOT>/state/WORKFLOW_CORE_VARIABLES.md`) — highest authority
2. `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`, if present —
   the chapter's emotional beat sheet; when it exists the chapter runs in
   assignment mode (see STEP 2)
3. `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DELIVERY_PLAN.md`,
   if present — the beat-to-channel assignment
4. `<STORY_ROOT>/state/entry_states/<target_stage>/<entry_state_id>.json`, if present
5. `<STORY_ROOT>/state/outcomes/<source_stage>/<outcome_id>.json`, if present
6. the latest accepted chapter source for the same chapter stem, if this is a revision or rebuild
7. `<STORY_ROOT>/knowledge/<target_stage>.json`, if present
8. the story-world database under `<STORY_ROOT>/story_world/`, if present —
   query it (`<FACTORY>/scripts/twin_db.py --root <STORY_ROOT> search/get/list`)
   instead of transcribing world facts from summaries; also `<TWIN_ROOT>/`
   facts and seeds, if `<TWIN_ROOT>` is declared and present (skip if
   `NOT_AVAILABLE`)

## Save output to

Write the preflight file to:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT.md`

## Skill use

- No skill required for this step.

## Task

Produce one chapter preflight that states:

- where the chapter starts
- what span of time the chapter covers
- what the player may know at chapter start
- what the player may not know yet
- what concrete world-state supports the chapter
- what minimum assumptions are needed because a source is missing

Use only source-backed facts.

## Required output blocks

Always output these blocks:

- `CHAPTER TIMEBOX`
- `KNOWLEDGE ALLOWED`
- `KNOWLEDGE NOT ALLOWED`
- `WORLD GROUNDING`
- `ASSUMPTIONS` when needed

## Block definitions

### `CHAPTER TIMEBOX`

State:

- absolute placement
- chapter duration
- day span in scope

### `KNOWLEDGE ALLOWED`

State 2-4 concrete bullets drawn from `<STORY_ROOT>/knowledge/*.json`.

### `KNOWLEDGE NOT ALLOWED`

State 1-3 concrete bullets that are not yet supported by the source set.

### `WORLD GROUNDING`

State concrete supports such as:

- locations
- recurring NPCs
- objects
- routines
- institutions
- pressure patterns
- time-flow facts

### `ASSUMPTIONS`

State the missing source and the minimum assumption needed to continue.
