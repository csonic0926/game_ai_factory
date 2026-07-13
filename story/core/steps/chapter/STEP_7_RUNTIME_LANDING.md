# STEP 7 — Runtime Landing

## Purpose

Mechanically translate the approved staging plan into the runtime files defined
by the adapter `LANDING_SPEC.md`, then record one landing log.

STEP 7 does not invent camera blocking, actor movement, pacing, or
cutscene/player-operation binding. Those decisions belong to STEP 6.7 and must
already be present in the approved staging plan.

## Read inputs from

Read the adapter landing contract FIRST, before any other input:

- `adapters/<PROJECT_ID>/LANDING_SPEC.md` — all landing details (target files, id & key grammar, granularity, choice & routing encoding, locale landing, integrity checks) defer to it. If it is missing or marked `NOT_AVAILABLE`, STOP and report `BLOCKED_BY_PROFILE`.

Read the approved staging plan and its review:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_STAGING_PLAN.md`
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_STAGING_REVIEW.md`

Read the saved runtime draft for wording / meaning reference only:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_zh.md`

Read the saved event graph when ids, links, or target checks are needed:

- `<STORY_ROOT>/chapter_event_graphs/<ARTIFACT_STEM>.md`

## Save output to

Write runtime data to:

- the target runtime files defined by the adapter `LANDING_SPEC.md`
- the chapter-entry wiring files defined by the adapter `LANDING_SPEC.md` when chapter start routing or intro-backed chapter entries are needed

Write one landing log to:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_LANDING.md`

## Skill use

- Use the adapter `LANDING_SPEC.md` for file-level runtime landing mechanics.
- When the landing surface is a scripted cutscene, use
  `core/craft/cutscene-staging.md` only as a document-conversion discipline:
  map the approved STEP 6.7 operations into the target `.cutscene.json`
  schema. Do not use it to redesign the staging.

## Task

Turn the approved staging plan into runnable runtime data.

Land structure first, then land final runtime text.

Keep the landed result aligned with the saved event graph, the saved runtime
draft meaning, and the approved STEP 6.7 operation sequence.

If the staging plan is missing, has no `STEP 6.75 PASS`, or does not define a
needed operation concretely enough to translate, STOP and report
`BLOCKED_BY_STAGING_PLAN`. Do not repair the staging inside STEP 7.


## Landing standard

Write the landing so it:

- creates real runtime rows instead of design-only notes
- keeps runtime file shape and column order unchanged, per the adapter `LANDING_SPEC.md`
- keeps diffs minimal and append-oriented where possible
- translates each approved staging operation into the matching runtime row,
  cutscene beat, mission definition, locale key, scene layout entry, or other
  adapter-declared landing surface
- maps every referenced event id, story profile, location node, and locale key to a real runtime row, following the id & key grammar defined by the adapter `LANDING_SPEC.md`
- keeps location-transition nodes as location transitions rather than automatic time jumps, where the runtime has them
- preserves time continuity across linked spine segments
- preserves STEP 6.7's cutscene / player-operation binding and records any
  operation that cannot currently land as an engineering dependency instead
  of silently converting it to another channel
- records the ids, row ranges, routing targets, and touched files in the landing log

## Runtime text standard

Write final player-facing runtime text into the locale storage defined by the adapter `LANDING_SPEC.md`.

For every new locale key:

- author the text in `<PRIMARY_LOCALE>` and add values for all `<SHIPPED_LOCALES>`, following the locale landing rules in the adapter `LANDING_SPEC.md`
- keep narration-type keys as in-game narration
- keep choice-type keys as concrete clickable action wording
- keep location-description keys as present-tense decision framing for the current node

Rewrite draft wording into final runtime wording before landing.

Keep player-facing narration in the form required by the adapter landing
surface and the staging plan. For dialogue or cutscene surfaces, use speaker
lines and locale keys; for second-person narration surfaces, keep `你`
narration.

Keep graph-layer protagonist labels such as `玩家` or `主角` out of final runtime prose.

Do not add lines just to explain staging. If an operation needs a prompt,
label, or locale key, write only the player-facing text required by that
operation's intended meaning.

## Id and mapping standard

When landing chapter runtime data, follow the id & key grammar defined by the adapter `LANDING_SPEC.md`, and make sure:

- every referenced runtime event id exists in the target runtime files
- every referenced story/timeline profile id resolves in the target runtime files
- every locale key referenced by runtime rows exists in the locale storage
- every graph `FLOW` target used at runtime resolves to a real runtime location node
- every graph `INTRO` or `STORY` target used at runtime resolves to a real runtime event
- every staging-plan mark, actor, target, prompt intent, scene transition, and
  locale-key intent has a real runtime representation or is recorded as a
  named engineering dependency

Use stable meaningful ids and keys that match existing project patterns.

## Timeline standard

Treat each landed `say` line as one in-game click unless the adapter
`LANDING_SPEC.md` states otherwise.

When a line is too dense for one click, split it into shorter runtime rows while keeping the same beat order.

The last row of a landed timeline profile must end in one of these ways:

- a visible choice that can continue
- a routed or inline `event_id`
- an engine-supported close path that resolves the story overlay

## Required output checks

The landed result must satisfy all of these checks:

1. every referenced runtime id exists in actual runtime data
2. every referenced locale key exists in the locale storage
3. every landed timeline profile has a valid continuation or close contract
4. any chapter start path needed for in-game testing is wired through the chapter-entry mechanism defined by the adapter `LANDING_SPEC.md`
5. the landing log records the produced ids, row ranges, routing targets, and language status
6. the landing log records how each STEP 6.7 operation group landed, or which
   operation is still blocked by a named engineering dependency
7. the integrity checks defined by the adapter `LANDING_SPEC.md` pass

## Block definitions

### `Mechanical landing work`

This step handles runtime-data and locale landing, id mapping, routing wiring,
and obvious conversion fixes. It does not re-stage scenes. If the staging plan
is wrong or incomplete, route back to STEP 6.7.
