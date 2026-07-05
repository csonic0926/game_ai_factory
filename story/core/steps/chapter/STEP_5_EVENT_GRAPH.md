# STEP 5 — Event Graph

## Purpose

Write one chapter event graph from the saved chapter source.

## Read inputs from

Read the saved chapter source artifact:

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>.json`

## Save output to

Write one event graph file to:

- `<STORY_ROOT>/chapter_event_graphs/<ARTIFACT_STEM>.md`

## Skill use

- No skill required for this step.

## Task

Turn the saved chapter source into one design-layer chapter event graph.

Write the graph as a playable sequence of beats that:

- follows the selected story line and the chapter spine
- keeps the spine's declared segments visible in event ordering
- stays grounded in concrete world supports such as locations, people, objects, routines, and the time pressure of the declared frame
- keeps graph summaries at beat-intent level rather than runtime prose level
- uses `玩家` or `主角` for protagonist references in graph-layer summaries

## Event graph shape

Write the graph as an event table with these columns:

- `event_key`
- `event_type`
- `segment`
- `beat_role`
- `what_happens`
- `involved_characters`
- `grounding`
- `decision_payload`
- `links_out`

Use these event types:

- `INTRO`
- `FLOW`
- `STORY`

Recommended baseline shape — one FLOW/STORY pair (or more) per spine
segment, in segment order:

```text
INTRO -> FLOW (first-segment location) -> STORY (first-segment action)
-> FLOW (next-segment location) -> STORY (next-segment drift)
-> ... repeated per declared segment ...
-> FLOW (final-segment location) -> STORY (final consequence)
```

## Writing standard

Write the graph so each beat shows:

- what happens at that beat
- what visible pressure or change pushes the chapter forward
- what concrete grounding support carries the beat
- where the graph moves next

Write `what_happens` as beat intent.
Write `decision_payload` as action intent.
Keep both readable, concrete, and ready for later runtime drafting.

## Required output blocks

Always include these blocks:

- `INTRO`
- `FLOW`
- `STORY`


## Block definitions

### `INTRO`

Write a short fixed-function opening that starts the chapter.

The `INTRO` should give the minimum information needed to begin the first playable movement.

Default line functions:

1. time cue
2. place cue
3. current errand or obligation
4. key object or task destination
5. one abnormal note for the chapter's opening
6. immediate next move

### `FLOW`

Use `FLOW` for location and movement structure.

Each `FLOW` beat should show:

- the concrete location reached or left
- the visible movement or transition
- continuity inside the current spine segment when the segment has not changed

### `STORY`

Use `STORY` for the chapter's main event sequence.

Each `STORY` beat should show:

- the main pressure or complication at that beat
- the causal change from the previous beat
- the visible consequence that carries into the next beat

## Expected result

- one saved chapter event graph under `<STORY_ROOT>/chapter_event_graphs/`
- one graph that is readable as chapter beat intent and ready for later runtime draft work
