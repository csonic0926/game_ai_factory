# Module — delivery-planner

The step that makes this a GAME story factory rather than a novel/screenplay
factory: after a chapter's emotional beat sheet is finalized, decide **which
delivery channel each beat seems to travel through at beat-sheet resolution**
— before anything is written for landing.

This module produces **rough channel intent**, not the final cutscene /
player-operation binding. The binding decision now belongs to CHAPTER STEP 6.7
(Staging & Realization), because that step reads the actual
`VISUAL_GRAMMAR.md` and can see what the engine can shoot.

The founding precedent: vinci_world CH1 was first landed as pure cutscenes,
then the USER re-cut it into "cutscene + six played mission segments"
(2026-07-05). That re-cut was this step done by hand, after the fact; this
module does it up front.

## Inputs

1. The chapter's beat sheet: `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`.
2. The game's `NARRATIVE_DELIVERY.md` (sovereignty file — how this game
   speaks decides the weighting: a Dark-Souls-dial game pushes beats into
   item copy and scenery; an Animal-Crossing-dial game pushes them into NPC
   dialogue).
3. The adapter's channel list: `adapters/<project_id>/DELIVERY_CHANNELS.md`
   (each game declares its own channels and their runtime status).
4. The sovereignty file `WORLD_RULES.md` for red lines the assignment must
   not cross.

## Input version binding

The delivery plan is not valid "for the chapter" in general; it is valid
only for the exact beat-sheet version it was produced from.

Before assigning channels, read the beat sheet header and capture:

- beat sheet path
- chapter unit / scope
- current status line
- current version evidence: explicit version token when present, otherwise
  the latest dated USER ruling / revision entry plus a content checksum when
  the local filesystem is available

If the beat sheet has no stable version evidence, create the best available
binding from the latest dated USER ruling / revision entry and a checksum,
and report that the beat sheet should be upgraded with an explicit version
token next time it is revised.

## Output

`<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DELIVERY_PLAN.md`, with,
at the top:

- `Based on beat sheet:` the source path
- `Beat sheet binding:` chapter unit / scope + exact version evidence used
- `Beat sheet checksum:` when available
- `Delivery plan status:` `CURRENT` when the binding matches the source used
  in this run, or `STALE` when a beat-sheet revision has invalidated it

Then, for EVERY beat of the beat sheet:

- the channel intent (or channel-intent combination — e.g. scenery carries
  the picture, one NPC line carries the feel);
- the reason, argued from `NARRATIVE_DELIVERY.md` and the beat's own curve
  mark (a HOLD beat must not be given to a channel that releases — e.g. a
  reward pop-up);
- landing status from the channel list (lands now / blocked by which
  missing runtime);
- what the channel must NOT do (the beat's red lines carried forward in
  plain words).

For beats that look like "cutscene vs played segment" decisions, record the
planner's best intent and why, but label it `ROUGH CHANNEL INTENT`. Do not
present it as the final binding. STEP 6.7 may refine or overturn it after
reading `VISUAL_GRAMMAR.md`.

Plus one coverage table: every beat appears exactly once as a primary
assignment; no beat is silently dropped; unassignable beats are flagged as
open items with a fallback.

## Discipline

- Place-first: when scenery, ritual, prop, or goods-flow can carry the
  picture, it outranks dialogue (`../../core/NARRATIVE_FOUNDATIONS.md` #2).
- The player's own walking (A-point-to-B-point play) is a channel, not dead
  time between cutscenes — the CH1 precedent exists because this was missed.
- Channel choice follows the beat's emotional delivery method, not the
  surface topic of the picture. For each beat, ask: what actually makes the
  feeling arrive for the player — the player's own movement, someone
  speaking, scenery/props, object text, a reward cue, or another declared
  channel? If that answer changes during beat-sheet revision, reassign the
  channel instead of carrying the old one forward. Precedent: a beat about
  "being on a boat" can be NPC dialogue if the emotion arrives by hearing
  fellow passengers speak, but it becomes mission/self-walk when the emotion
  arrives by giving control back to the player and letting them walk to the
  bow.
- The exact `cutscene` / `player_operation` binding is deliberately deferred
  to STEP 6.7. The planner does not know yet whether a drafted image can be
  staged by this engine's camera, actors, pacing, and primitives.
- The plan never rewrites beats. If a beat cannot be delivered by any
  declared channel, that goes back to the beat-sheet dialogue or waits for
  runtime — the planner reports, it does not bend the beat.
- Headless-able: in `auto` mode record every assignment's reason + open
  items; in `ask` mode put genuinely direction-level channel calls to the
  USER (e.g. "is the first pull a cutscene or played?").
- Revisions are full re-checks, not patch edits. When re-running against a
  revised beat sheet, revisit every row and ask the emotional-delivery
  question again; do not update only the visibly changed beats, because a new
  beat can shift the curve position and therefore the best channel for
  neighboring beats.

## Review

When run inside the chapter pipeline, the delivery plan is checked by the
chapter gates' emotional-acceptance line (did the assignment keep the
curve's holds and releases?) and by STEP 2 assignment mode, which reads it
as binding input. Run standalone, the module self-checks against the
coverage table before reporting done.
