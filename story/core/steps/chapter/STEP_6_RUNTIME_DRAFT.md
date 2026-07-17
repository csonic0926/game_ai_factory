# STEP 6 — Scene Runtime Draft

## Purpose

Write the chapter's zh-Hant runtime scene draft from the saved event graph.

## Read inputs from

Read the saved event graph:

- `<STORY_ROOT>/chapter_event_graphs/<ARTIFACT_STEM>.md`

Before writing any quoted dialogue, read `<ADAPTER>/GLOSSARY.csv` when it
exists. It is the sole canonical source for proprietary terms; do not use
`WORLD_RULES.md`, `STYLE_GUIDE.md`, shipped locale prose, or another artifact
as a competing term list. Missing glossary means `NOT_AVAILABLE` and
preserves the prior workflow.

## Save output to

Write the runtime draft to:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_zh.md`

If the chapter is split into multiple scene-cluster files, keep them in the same directory and use the same `<ARTIFACT_STEM>` prefix.

## Skill use

- No skill required for this step.

## Task

Turn the event graph into scene-level runtime prose.

Write one scene cluster at a time, usually one `STORY` beat with its adjacent `FLOW` beats, or one small location block.

**Draft FORM is adapter-driven.** Check the adapter's `STYLE_GUIDE.md` for a
"runtime draft form" section and use the form it prescribes (e.g. a screenplay
format for cutscene-based games: scene headings + third-person stage
directions + dialogue lines). Only when the adapter defines no form, default
to second-person `你` narrative prose (the text-game form this step
inherited from rpg-1).

Write the draft so it:

- follows the graph beat order exactly
- turns beat intent into on-screen scene action
- uses the adapter-prescribed draft form (default: second person with `你`)
- stays in `<PRIMARY_LOCALE>` for this pass
- lands one readable beat at a time
- is ready for STEP 6.7 to realize into the target visual grammar

This step is still a scene-writing step, not the final camera / controls
binding step. Do not contort the draft to solve every engine limitation here:
STEP 6.7 will translate medium-independent scene images into shootable
operations and decide cutscene vs. player operation.

## Scene draft standard

Write each scene cluster so the reader can perceive:

- where `你` are standing
- who is physically present
- what visible action is happening
- what object, document, doorway, counter, table, street position, or other support is carrying the beat
- what visible change pushes the next beat forward

Stage graph information through scene action, dialogue, gesture, position, and object state.

When a graph beat includes revealed information, write the moment that reveals it on-screen.

When a major character, institution face, or place appears for the first time in this chapter, introduce it in-scene through action and placement.

## Line writing standard

When the glossary is available:

- use its registered `<PRIMARY_LOCALE>` canon forms;
- obey `register` and `speaker_scope` before putting a variant in a
  character's mouth;
- keep `dialogue_protected=true` forms exact;
- use no `banned` form;
- report a new world noun, classifier convention, or register variant as a
  `status=pending` nomination rather than silently normalizing it.

Write each line as one dominant readable beat.

A strong line usually carries one of these:

- one action
- one spoken line
- one visible reaction
- one object-state change
- one small realization attached to the immediately previous action

Keep line-to-line continuity strong so each line feels pulled out of the previous one by sight, movement, speech, or pressure.

## Runtime prose standard

Write runtime-facing prose that stays on observable ground.

Write with:

- action
- position
- distance
- gesture
- dialogue
- object state
- visible environment
- visible signs of routine, rules, or institutional process

Write natural Chinese with short readable rhythm.

Prefer direct scene facts and direct spoken language.

## INTRO handling

If the chapter includes an `INTRO`, keep its opening function intact.

The opening should still cover:

1. time cue
2. place cue
3. current errand or obligation
4. key object or task destination
5. one abnormal note for today
6. immediate next move

## Required output

- one or more zh-Hant runtime draft files under `<STORY_ROOT>/runtime_scene_drafts/`
- each draft file readable as playable scene prose rather than graph summary

## Spoken-fluency pass (required before STEP 6.5)

This draft contains quoted spoken lines, so after it is saved it must pass
`core/craft/spoken-fluency.md` BEFORE the STEP 6.5 gate reads it. The pass
runs as a SEPARATE fresh worker dispatched by the orchestrator — the STEP 6
worker must NOT polish its own lines (a context full of design reasoning
cannot hear its own annotation register; same independence principle as the
review gates).

In the default clean-room mode, the orchestrator reads the glossary and
mechanically extracts the scene language's applicable canon
`dialogue_protected=true` forms and exact `banned` forms. It supplies those as
a plain-language hard-constraint list; the clean-room worker never reads the
CSV itself. After the rewrite, the canon-aware back-check reads the glossary,
runs `scripts/glossary_check.py` on the result (and a protected-term baseline
diff whenever separate before/after artifacts are available), and verifies
speaker/register constraints. The fluency/canon log records the original and
rewritten lines, the extracted constraints, and the back-check result at:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_FLUENCY.md`
