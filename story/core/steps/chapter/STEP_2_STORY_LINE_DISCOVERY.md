# STEP 2 — Chapter Task (Assignment / Discovery)

## Purpose

Fix what this chapter is FOR, in one of two modes:

- **Assignment mode** (the default whenever the chapter has an emotional
  beat sheet): take the chapter's task FROM the beat sheet — the emotional
  goal was decided upstream in the USER dialogue; this step translates it
  into a workable chapter line, it does not invent one.
- **Discovery mode** (legacy — only when NO beat sheet exists for this
  chapter, e.g. the rpg-1 back catalog): choose the one ordinary track that
  should carry the chapter, declare its time frame, and identify the
  concrete bend — exactly as this step always worked.

Mode selection is mechanical, not a judgment call:
`<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md` exists → assignment
mode; otherwise discovery mode. A beat sheet whose beats are still all
unconfirmed drafts (no `USER 定案` beat) is NOT a usable assignment source —
report BLOCKED_BY_BEAT_SHEET instead of falling back silently.

## Read inputs from

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_PREFLIGHT.md`
- assignment mode only:
  - `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md` (the task source)
  - `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DELIVERY_PLAN.md`,
    if present (binding channel assignments)
  - `<STORY_ROOT>/state/NARRATIVE_DELIVERY.md` (how this game speaks)

## Save output to

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_STORY_LINE.md`

## Skill use

- No skill required for this step.

## Task — assignment mode

Before translating the beat sheet into a chapter line, perform the same
upstream sync check as STEP 1:

- derive the beat sheet's current version evidence from its explicit version
  token when present, otherwise from its latest dated USER ruling / revision
  entry plus a content checksum when available
- if a delivery plan exists, read its header binding and compare beat-sheet
  path, version token / revision entry, and checksum when available
- a delivery plan with no binding stamp, a mismatched path, or an older
  version is stale

If the delivery plan is stale, write `BLOCKED_BY_STALE_DELIVERY_PLAN` to the
story-line output with the evidence, then stop. Do not use any old channel
assignment as binding input. If no delivery plan exists, continue without
binding channel assignments and record that absence as an open item.

Read the beat sheet as the chapter's commissioned task and produce the
chapter line that will deliver it.

Your result must state:

- the beat sheet's chapter unit, quoted scope, and status (which beats are
  USER-ruled, which are drafts — draft beats are carried as open items, not
  silently treated as settled)
- the upstream sync status: whether the delivery plan is synchronized,
  absent, or blocked as stale
- the emotional curve as ordered beats, restated in plain rich prose (the
  anti-compression rules apply: every beat's picture is restated in full,
  never reduced to a label)
- what ordinary track, in the preflight's world state, those beats hang on
- the chapter's time frame as the beat order implies it (if the beat sheet
  already fixes the span, record that source instead of re-deciding)
- how the curve's HOLD (壓) stretch and its RELEASE (放) point map onto the
  chapter's segments — name where the single top of the curve lands
- any beat the preflight's world state cannot support — flag it back
  toward the beat-sheet dialogue as an open item; NEVER bend or drop a beat
  to fit

Then fill the required output blocks below. In assignment mode
`STORY LINE CANDIDATES` may hold a single entry (the beat sheet already
chose the story); `BENDING POINT` names the beat where the ordinary track
stops being ordinary.

## Task — discovery mode

Read the preflight and select one story line that should become the chapter.

Your result must state:

- what the chapter is about
- what ordinary track it starts from
- what concrete thing bends that track
- how much in-world time the chapter covers, and why that span fits
- why this line is the best chapter line from the available preflight material

Choose a line that:

- starts from a believable ordinary track
- can carry pressure across the chapter's whole time frame
- can lead to visible movement and consequence
- stays grounded in the preflight material
- says something important about the current chapter state

Useful source material includes:

- obligation
- relationship
- object
- location-bound responsibility
- routine
- institution
- pressure pattern
- knowledge boundary

## Required output blocks

- `MODE`
- `DISCOVERY QUESTION`
- `STORY LINE CANDIDATES`
- `SELECTED STORY LINE`
- `TIME FRAME`
- `NORMAL TRACK`
- `BENDING POINT`
- `WHY THIS MUST BE THE CHAPTER`
- assignment mode also requires: `BEAT COVERAGE`

## Block definitions

### `MODE`

State `ASSIGNMENT` (with the beat sheet path and its status line) or
`DISCOVERY` (with the reason: no beat sheet exists for this stem).

### `BEAT COVERAGE` (assignment mode only)

One row per beat of the beat sheet: the beat's picture restated in plain
words, its curve mark (壓/放), where in the chapter line it lands, and its
delivery channel when a synchronized delivery plan exists. Every beat appears
exactly once; a beat the world state cannot support is listed with an
open-item flag, never dropped. Never fill this from an unstamped or stale
delivery plan.

### `DISCOVERY QUESTION`

State the chapter question this step answered. In assignment mode this is
the beat sheet's commissioned task, quoted.

### `STORY LINE CANDIDATES`

List 2-4 plausible lines from the preflight.
For each candidate, state:

- what the line is
- what ordinary track it begins from
- what kind of bend it creates

### `SELECTED STORY LINE`

State one chosen line only.

### `TIME FRAME`

Declare the chapter's time frame. This is a direction decision for THIS
chapter — the story's needs decide it, never a fixed factory default.

State:

- how much in-world time the chapter covers (a single day, one evening,
  several days, one leg of a journey, an open stretch of routine — whatever
  the line needs)
- why that span fits this line: where the bend needs room, and where the
  landing needs room
- roughly how the span divides into ordered segments, each named in the
  story's own words (segments may be times of day, days, places along a
  route, or stages of an event — whichever the story itself would use)

Choose the smallest span that lets the line bend and land with consequence.
A single day divided into morning / noon / evening is a proven shape for
routine-anchored chapters — use it when it fits, never because it is the
habit.

If the orchestrator's dispatch or a user brief already fixed the time
frame, follow it and record the source here instead of re-deciding.

### `NORMAL TRACK`

State what this stretch of time would have looked like if this line stayed
ordinary.

Include:

- what the player thought this stretch of time was going to be about
- what they were supposed to finish, return to, deliver, check, avoid, or handle

### `BENDING POINT`

State the concrete thing that makes the ordinary track stop staying ordinary.

Use a specific source of the bend, such as:

- person
- action
- interruption
- object
- demand
- discovery
- refusal
- delay
- mismatch between expectation and reality

### `WHY THIS MUST BE THE CHAPTER`

State why this line should become the chapter.

Explain:

- why this bend matters now
- why it is strong enough to shape the chapter's whole time frame
- why this is the line the chapter should follow
