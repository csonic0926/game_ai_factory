# STEP 1.5 — Chapter Preflight Acceptance

## Purpose

- check that the saved preflight is ready to support chapter work
- confirm the chapter start, knowledge limits, and world supports are concrete

## Read inputs from

Read the saved preflight artifact:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT.md`

When the preflight is in assignment mode, also spot-check the upstream
evidence it cites:

- `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DELIVERY_PLAN.md`, if present
- `adapters/<PROJECT_ID>/DELIVERY_CHANNELS.md`, if present
- `adapters/<PROJECT_ID>/LANDING_SPEC.md`, if present
- any concrete runtime files, enums, schemas, or tool specs the preflight
  names as evidence

## Save output to

Write the acceptance result to:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT_REVIEW.md`

The note must say `STEP 1.5 PASS` or `STEP 1.5 FAIL`.

## Skill use

- No skill required for this step.

## Task

Review the saved preflight and decide whether it is complete enough to pass.

A passing preflight gives the chapter:

- a clear sync status for the beat sheet and delivery plan
- one clear chapter start and time span
- concrete allowed knowledge and forbidden knowledge
- concrete world-grounding supports
- a visible landing-surface inventory for the chapter's required scenes,
  channels, and runtime capabilities
- assumptions only for missing required source material

## Acceptance criteria

### `UPSTREAM ARTIFACT SYNC`

Pass when the block proves one of these states:

- `SYNCED`: the delivery plan's beat-sheet binding matches the current beat
  sheet path and version evidence
- `NO_DELIVERY_PLAN`: no delivery plan exists, and the preflight does not
  treat any channel assignment as binding
- `DISCOVERY_MODE_NO_BEAT_SHEET`: no beat sheet exists, so the chapter is not
  in assignment mode

Fail when:

- the block is missing
- assignment mode has a delivery plan whose binding stamp is missing,
  unverifiable, or mismatched
- the preflight says `BLOCKED_BY_STALE_DELIVERY_PLAN`
- the preflight uses channel assignments from a delivery plan it has not
  proven synchronized

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

### `LANDING SURFACE INVENTORY`

Pass when the block:

- exists in assignment mode
- covers every beat/channel/scene/runtime capability the beat sheet or
  synchronized delivery plan visibly requires
- names evidence from `DELIVERY_CHANNELS.md`, `LANDING_SPEC.md`, and/or the
  concrete runtime files those adapter docs cite
- distinguishes `AVAILABLE_NOW`, `ENGINEERING_DEPENDENCY`,
  `FALLBACK_AVAILABLE`, and `NOT_DECLARED_OR_UNKNOWN`
- marks missing surfaces as engineering dependencies or unknowns instead of
  assuming they can land

Engineering dependencies are not a failure by themselves. A preflight may
PASS with engineering dependencies when they are explicit and the report says
the chapter is design-ready but landing waits on engineering.

Fail when the inventory is missing, skips an obvious beat requirement, claims
a runtime surface exists without adapter/runtime evidence, or hides a required
engineering dependency until STEP 7.

### `ASSUMPTIONS`

Pass when the block:

- names the missing source clearly
- states only the minimum needed assumption
- stays at constraint level

## Required stop condition

- write a short acceptance note that says `STEP 1.5 PASS` or `STEP 1.5 FAIL`
- on `FAIL`, state the blocker clearly
