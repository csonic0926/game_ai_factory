# Module — delivery-planner

The step that makes this a GAME story factory rather than a novel/screenplay
factory: after a chapter's emotional beat sheet is finalized, decide **which
delivery channel each beat travels through** — before anything is written
for landing.

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

## Output

`<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DELIVERY_PLAN.md`, with,
for EVERY beat of the beat sheet:

- the assigned channel (or channel combination — e.g. scenery carries the
  picture, one NPC line carries the feel);
- the reason, argued from `NARRATIVE_DELIVERY.md` and the beat's own curve
  mark (a HOLD beat must not be given to a channel that releases — e.g. a
  reward pop-up);
- landing status from the channel list (lands now / blocked by which
  missing runtime);
- what the channel must NOT do (the beat's red lines carried forward in
  plain words).

Plus one coverage table: every beat appears exactly once as a primary
assignment; no beat is silently dropped; unassignable beats are flagged as
open items with a fallback.

## Discipline

- Place-first: when scenery, ritual, prop, or goods-flow can carry the
  picture, it outranks dialogue (`../../core/NARRATIVE_FOUNDATIONS.md` #2).
- The player's own walking (A-point-to-B-point play) is a channel, not dead
  time between cutscenes — the CH1 precedent exists because this was missed.
- The plan never rewrites beats. If a beat cannot be delivered by any
  declared channel, that goes back to the beat-sheet dialogue or waits for
  runtime — the planner reports, it does not bend the beat.
- Headless-able: in `auto` mode record every assignment's reason + open
  items; in `ask` mode put genuinely direction-level channel calls to the
  USER (e.g. "is the first pull a cutscene or played?").

## Review

When run inside the chapter pipeline, the delivery plan is checked by the
chapter gates' emotional-acceptance line (did the assignment keep the
curve's holds and releases?) and by STEP 2 assignment mode, which reads it
as binding input. Run standalone, the module self-checks against the
coverage table before reporting done.
