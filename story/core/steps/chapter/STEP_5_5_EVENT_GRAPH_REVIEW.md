# STEP 5.5 — Event Graph Acceptance

## Purpose

Review the saved event graph and decide whether it passes.

## Read inputs from

Read the saved event graph:

- `<STORY_ROOT>/chapter_event_graphs/<ARTIFACT_STEM>.md`

## Save output to

Write the acceptance result to:

- `<STORY_ROOT>/chapter_event_graphs/<ARTIFACT_STEM>_REVIEW.md`

The note must explicitly say `STEP 5.5 PASS` or `STEP 5.5 FAIL`.

## Skill use

- No skill required for this step.

## Task

Check whether the saved event graph is complete, readable, and consistent with the STEP 5 event-graph contract.

## Acceptance criteria

### File and structure

This step passes when:

- the event graph file exists
- the graph is readable as one event table
- the table uses these columns:
  - `event_key`
  - `event_type`
  - `segment`
  - `beat_role`
  - `what_happens`
  - `involved_characters`
  - `grounding`
  - `decision_payload`
  - `links_out`

### Event types and ordering

This step passes when:

- the graph includes `INTRO`, `FLOW`, and `STORY`
- event ordering keeps the spine's declared segments visible
- the graph reads as one chapter sequence rather than disconnected notes

### Graph writing

This step passes when:

- graph summaries use `玩家` or `主角` for protagonist references
- `what_happens` reads as beat intent
- `decision_payload` reads as action intent
- graph wording stays at design-layer summary level

### Grounding

This step passes when:

- each major beat is carried by concrete world supports
- grounding names visible supports such as locations, people, objects, routines, or time-of-day pressure
- the graph reads as lived chapter action inside the world rather than abstract summary

## Required stop condition

- write a short acceptance note that says `STEP 5.5 PASS` or `STEP 5.5 FAIL`
- on `FAIL`, state the blocker clearly
