# STEP 6.7 — Staging & Realization

## Purpose

Turn the approved STEP 6 runtime draft into an engine-shootable staging plan.

STEP 6 is allowed to be medium-independent scene prose. STEP 6.7 is where the
factory decides how the target engine can actually present each beat, including
which beats are controlled cutscene beats and which beats become player
operation.

## Read inputs from

Read the adapter visual grammar FIRST:

- `adapters/<PROJECT_ID>/VISUAL_GRAMMAR.md` — camera, actor, pacing, cannot
  list, and allowed presentation primitives. If it is missing or marked
  `NOT_AVAILABLE`, STOP and report `BLOCKED_BY_PROFILE`.

Read the approved runtime draft and its review:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_zh.md`
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_REVIEW.md`

If the draft was split into multiple scene-cluster files, read every file that
shares the same `<ARTIFACT_STEM>` prefix and the corresponding review.

Read the sources that explain each beat's job:

- `<STORY_ROOT>/chapter_event_graphs/<ARTIFACT_STEM>.md`
- `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`, if present
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DELIVERY_PLAN.md`, if
  present and synchronized by STEP 1
- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT.md`, if present

## Save output to

Write the staging plan to:

- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_STAGING_PLAN.md`

## Skill use

- No skill required for this step.

## Task

Produce a beat-by-beat staging plan that STEP 7 can mechanically translate
into runtime data.

For every covered beat:

1. Decide whether the beat is bound to `cutscene` or `player_operation`.
2. Translate the draft's visible image into operations from
   `VISUAL_GRAMMAR.md` only.
3. If the draft asks for a forbidden presentation, record either a restage
   inside the visual grammar or a concrete engineering dependency.
4. Recalibrate pacing so "stay" beats become player movement / environment
   / pause where possible, and dialogue is used only when the beat needs
   speech.

The delivery plan gives rough channel intent. This step may refine or
override that intent because this step is the first one that sees the actual
visual grammar. When overriding it, state the original channel intent and the
reason the staging binding differs.

## Binding standard

Bind a beat to `player_operation` when the emotion arrives because the player
does something themselves:

- walks from one place to another
- reaches a tile
- enters a scene
- inspects or personally triggers an object
- slows down, pauses, or approaches under their own control

Bind a beat to `cutscene` when the emotion requires arranged timing or
composition:

- group blocking
- a timed reveal
- a focus / pan / fade
- dialogue timing
- controlled actor movement
- a ritual or threshold the game must frame for the player

A beat may contain both, but the staging plan must name the primary binding
and split the operations clearly, e.g. "player_operation leads into cutscene"
or "cutscene releases into player_operation".

## Visual-grammar standard

Every staging operation must be written as one of the primitives declared in
`VISUAL_GRAMMAR.md`.

Do not use film-language instructions such as close-up, wide shot, cut,
reverse shot, montage, dolly, tracking shot, moving background, or a moving
vehicle unless the visual grammar explicitly allows them.

When the STEP 6 draft uses a forbidden image:

- `restage` it when the same beat can be expressed with allowed operations
  without changing the beat's emotional job
- record `engineering_dependency` when the beat truly requires runtime
  capability outside the visual grammar

Never silently pass a forbidden image downstream to STEP 7.

## Pacing standard

For every beat, mark the pacing as:

- `stay` — the player or camera lives in a place; text is sparse
- `speak` — a dialogue line carries the beat
- `mixed` — player movement / environment and one small speech or cue share
  the beat

Use the adapter's native pacing rules. If a hold beat has become too many
consecutive dialogue lines, convert the hold into player movement,
environmental placement, a camera hold, an emote, or a pause whenever the
visual grammar can carry it.

## Required output blocks

The staging plan must include these blocks:

- `SOURCE STATUS` — draft path, review status, beat sheet / delivery plan
  status, and visual grammar path.
- `VISUAL GRAMMAR SUMMARY` — short list of the camera, actor, cannot, pacing,
  and primitive rules this plan relies on.
- `BINDING TABLE` — every covered beat, original channel intent when present,
  final `cutscene` / `player_operation` binding, and reason.
- `STAGING OPERATIONS` — beat-by-beat operation sequence using only
  `VISUAL_GRAMMAR.md` primitives.
- `CANNOT COLLISIONS` — every forbidden presentation found in the draft, with
  `restage` or `engineering_dependency`.
- `PACING CALIBRATION` — `stay` / `speak` / `mixed`, estimated duration, and
  any dialogue-to-environment conversion.
- `STEP 7 HANDOFF` — target operation groups that STEP 7 should translate,
  plus any runtime dependencies that must be resolved before landing.

## Required output

- one staging plan under `<STORY_ROOT>/runtime_scene_drafts/`
- the plan is concrete enough that STEP 7 can translate it without inventing
  new staging
