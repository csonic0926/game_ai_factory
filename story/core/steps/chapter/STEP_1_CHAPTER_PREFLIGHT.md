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
   assignment mode (see STEP 2). Record its current version evidence before
   using it: the explicit beat-sheet version token when present, otherwise
   the latest dated USER ruling / revision entry plus a content checksum when
   the local filesystem is available.
3. `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DELIVERY_PLAN.md`,
   if present — the beat-to-channel assignment. Before trusting it, compare
   its recorded beat-sheet binding against the current beat sheet. A delivery
   plan with no binding stamp, a different beat-sheet path, a different
   version token / revision entry, or a different checksum is stale for this
   run.
4. `<STORY_ROOT>/state/entry_states/<target_stage>/<entry_state_id>.json`, if present
5. `<STORY_ROOT>/state/outcomes/<source_stage>/<outcome_id>.json`, if present
6. the latest accepted chapter source for the same chapter stem, if this is a revision or rebuild
7. `<STORY_ROOT>/knowledge/<target_stage>.json`, if present
8. the story-world database under `<STORY_ROOT>/story_world/`, if present —
   query it (`<FACTORY>/scripts/twin_db.py --root <STORY_ROOT> search/get/list`)
   instead of transcribing world facts from summaries; also `<TWIN_ROOT>/`
   facts and seeds, if `<TWIN_ROOT>` is declared and present (skip if
   `NOT_AVAILABLE`)
9. assignment mode only: `adapters/<PROJECT_ID>/DELIVERY_CHANNELS.md` and
   `adapters/<PROJECT_ID>/LANDING_SPEC.md`, if present. Treat these as the
   adapter's declared delivery / landing contract, then inspect the concrete
   runtime files, enums, schemas, or tool specs they cite in `<GAME_REPO>`.
   Do not assume a scene, channel, enum value, or landing surface exists just
   because the beat sheet wants it.

## Save output to

Write the preflight file to:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT.md`

## Skill use

- No skill required for this step.

## Task

Produce one chapter preflight that states:

- whether the beat sheet and delivery plan are synchronized, when both exist
- where the chapter starts
- what span of time the chapter covers
- what the player may know at chapter start
- what the player may not know yet
- what concrete world-state supports the chapter
- which landing surfaces / runtime capabilities the beat sheet or delivery
  plan requires, and whether they exist now or need engineering
- what minimum assumptions are needed because a source is missing

Use only source-backed facts.

## Stale delivery-plan stop condition

When a beat sheet exists and a delivery plan exists, the delivery plan is
binding only if it proves which beat-sheet version it was made from.

If the delivery plan is missing the binding stamp, points to another beat
sheet, or was built from an older beat-sheet version, write a blocker
preflight with `UPSTREAM ARTIFACT SYNC` set to
`BLOCKED_BY_STALE_DELIVERY_PLAN`, state exactly what mismatched, and stop.
Do not continue by silently using the old channel assignments.

If no delivery plan exists, do not invent one. Record `NO_DELIVERY_PLAN` in
`UPSTREAM ARTIFACT SYNC` and continue with a landing-surface inventory based
on the beat sheet's visible needs and the adapter's declared channels.

## Required output blocks

For a non-blocker preflight, always output these blocks. For a
`BLOCKED_BY_STALE_DELIVERY_PLAN` preflight, output `UPSTREAM ARTIFACT SYNC`
and a clear blocker note; do not fill downstream blocks from stale input.

- `UPSTREAM ARTIFACT SYNC`
- `CHAPTER TIMEBOX`
- `KNOWLEDGE ALLOWED`
- `KNOWLEDGE NOT ALLOWED`
- `WORLD GROUNDING`
- `LANDING SURFACE INVENTORY`
- `ASSUMPTIONS` when needed

## Block definitions

### `UPSTREAM ARTIFACT SYNC`

State whether the upstream artifacts are safe to use.

For assignment mode, include:

- beat sheet path and current version evidence (version token, latest
  dated USER ruling / revision entry, and checksum when available)
- delivery plan path, if present
- delivery plan's recorded beat-sheet binding, if present
- one status:
  - `SYNCED` — delivery plan binding matches the current beat sheet
  - `NO_DELIVERY_PLAN` — no delivery plan exists; channel assignments are not
    binding yet
  - `BLOCKED_BY_STALE_DELIVERY_PLAN` — delivery plan is missing a binding
    stamp or no longer matches the current beat sheet

In discovery mode, state `DISCOVERY_MODE_NO_BEAT_SHEET`.

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

### `LANDING SURFACE INVENTORY`

Move the STEP 7 runtime-surfaces problem into preflight. Compare the beat
sheet and delivery plan (when synchronized) against the adapter and runtime.

List every scene, channel, or runtime capability this chapter appears to
need, with:

- the beat(s) that need it
- the requested surface / channel / scene / runtime capability
- adapter evidence from `DELIVERY_CHANNELS.md` and/or `LANDING_SPEC.md`
- runtime evidence from the concrete files, enums, schemas, or tool specs
  cited by the adapter, when available
- status:
  - `AVAILABLE_NOW` — declared by the adapter and found in runtime evidence
  - `ENGINEERING_DEPENDENCY` — design is valid, but runtime support must be
    created before landing
  - `FALLBACK_AVAILABLE` — another declared channel can carry the beat, and
    the fallback's cost is stated plainly
  - `NOT_DECLARED_OR_UNKNOWN` — the request has no reliable adapter/runtime
    evidence yet

Engineering dependencies do not stop STEP 2-6 design work by themselves.
They must be visible early: state plainly when the chapter is "design-ready,
landing waits on engineering." Do not mark a missing surface as available.

### `ASSUMPTIONS`

State the missing source and the minimum assumption needed to continue.
