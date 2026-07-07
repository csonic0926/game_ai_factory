# STEP 2.5 — Chapter Task Acceptance

## Purpose

Check whether the saved STEP 2 file fixes one usable chapter line — faithful
to the beat sheet in assignment mode, or discovered soundly from the
preflight in discovery mode.

## Read inputs from

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_STORY_LINE.md`
- assignment mode (per the file's `MODE` block): ALSO read
  `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md` — fidelity is
  checked against the SOURCE, never against the STEP 2 file's own restatement
- assignment mode, when present:
  `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_DELIVERY_PLAN.md`

## Save output to

- `<STORY_ROOT>/state/chapter_sources/<ARTIFACT_STEM>_STORY_LINE_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Review the STEP 2 file and decide whether it is ready to pass. First verify
the `MODE` block chose correctly: a beat sheet exists for this stem but the
file ran discovery ⇒ automatic FAIL; a beat sheet with zero USER-ruled beats
was used as an assignment source ⇒ automatic FAIL (correct outcome was
BLOCKED_BY_BEAT_SHEET).

## Acceptance criteria — assignment mode

The file passes when all of the following hold:

- `BEAT COVERAGE` lists every beat of the beat sheet exactly once; nothing
  was dropped, merged away, or invented
- each beat's picture is restated in full plain prose that preserves the
  source meaning (compare against the beat sheet itself; label- or
  count-matching is not evidence)
- the curve survived: HOLD beats still hold, the single RELEASE lands where
  the beat sheet put it, and no chapter-line addition releases earlier —
  this is the emotional-acceptance line at the chapter's root
  (`core/NARRATIVE_FOUNDATIONS.md` #3)
- draft beats (【草案待 USER 砍定】) are carried as open items, not treated
  as settled rulings
- unsupportable beats were flagged back toward the beat-sheet dialogue, not
  bent to fit
- `TIME FRAME` follows the beat order (or records the beat sheet's own span
  ruling); `SELECTED STORY LINE`, `NORMAL TRACK`, `BENDING POINT`, and
  `WHY THIS MUST BE THE CHAPTER` are filled and consistent with the beats

## Acceptance criteria — discovery mode

The file passes when it includes all of the following:

- `MODE` states DISCOVERY and the stated reason (no beat sheet) is true
- `STORY LINE CANDIDATES` lists plausible options from the preflight
- each candidate states the line, the ordinary track it starts from, and the kind of bend it creates
- `SELECTED STORY LINE` names one chosen line only
- `TIME FRAME` declares how much in-world time the chapter covers, justifies the span from the line's own needs (not from habit or from another chapter's shape), and sketches ordered segments named in the story's own words
- `NORMAL TRACK` states the ordinary track for the chosen line
- `BENDING POINT` names the concrete source of the bend
- `WHY THIS MUST BE THE CHAPTER` explains why this line matters now and why it should carry the chapter

Fail the file when the time frame reads as a default that was never argued —
for example a single day with morning / noon / evening segments justified
only by precedent, when the selected line clearly needs more room or less.

## Required stop condition

- write a short acceptance note that says `STEP 2.5 PASS` or `STEP 2.5 FAIL`
- on `FAIL`, state the blocker clearly
