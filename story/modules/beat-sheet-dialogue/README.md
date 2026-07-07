# Module — beat-sheet-dialogue

Interactive module that produces a chapter's **emotional beat sheet** — the
topmost upstream artifact of chapter production. It answers the question no
other input answers: *what should happen inside the player's chest, in what
order, and why does each step only work after the one before it.*
(Foundations: `../../core/NARRATIVE_FOUNDATIONS.md`.)

**This cannot be automated, and it always runs in ask mode** — the USER and
the AI build the sheet together in live dialogue. In a headless run this
module cannot execute; a pipeline that needs a beat sheet and finds none
reports it as an open USER dependency rather than inventing one.

## Protocol — from zero, for ANY project

**Phase 0 — emotional field (first run on a project only).** Before any
beats: spread the transmitting moments of the game's real-world domain —
concrete lived moments that move the chest unexplained (for a collecting
game: 「媽媽大掃除把整盒卡丟了」). The USER circles the founding emotions
and, just as importantly, kills the dead ones (vinci_world precedent: a
premise everyone had accepted — daily private communion with one's
collection — was killed here as a non-emotion). What survives feeds the
game's sovereignty files (world rules / narrative delivery) BEFORE beats
are attempted. Skipping Phase 0 on a fresh project reproduces the
"well-crafted, no story" failure.

**Phase 1 — 攤田 (spread the field).** Lay out candidate beats at the SAME
altitude — one line per beat, each line one CONCRETE picture, no derivation,
no induction, no grouping into themes. A line like 「建立期望」(build
anticipation) is an instruction, not a picture, and is invalid.

**Phase 2 — USER cuts and rules.** Keeps, kills, reorders, rewrites; adds
rulings. Where the USER cannot author the craft themselves, they may set a
**creative KPI** instead — a destination (e.g. a final line the scene must
land on) plus the arrival emotion — and a craft doc paves candidate paths
(`../../core/craft/dialogue-runway.md` for conversation runways). The KPI
and the cut stay USER-owned; the paving is factory work.

**Phase 3 — converge AND WRITE TO DISK AT THE MOMENT OF EACH CUT.** The
instant the USER confirms a beat (「對，就這樣」), it is written into the
beat sheet file — conversation memory is never the store. When the dialogue
ends, the file IS the single source of truth; there is no "collect it
later". (Rule learned the hard way: the vinci_world 1-9 list lived only in
chat, and a later worker reconstructing it from secondhand records dropped
three USER-confirmed beats and inverted one.)

Every disk write that changes a USER-ruled beat must also update the beat
sheet's version evidence in the header: record the revision date, what
changed in plain words, and a stable version token (for example the latest
revision line plus a short content checksum when available). This token is
what the delivery-planner stamps into its own output.

If a delivery plan already exists for this chapter, a beat-sheet change in
the same interactive session must immediately do one of two things:

1. re-run `../delivery-planner/` so the channel assignments bind to the new
   beat-sheet version, or
2. mark the existing delivery plan `STALE — beat sheet revised on <date>`
   at the top of that plan and report that the next chapter pipeline run
   must re-run delivery planning before STEP 2 may use it.

Never leave a revised beat sheet beside an apparently-current delivery plan.

## The artifact

Location: `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`
(one beat sheet = one chapter unit, containing multiple scenes).

Required content, in the chapter's `<PRIMARY_LOCALE>`, rich prose per the
adapter's style guide:

- **Header**: chapter unit name; scope (where the unit begins and ends);
  sources (which conversation / which recorded rulings); **version
  evidence** — the current revision date, what changed, and a stable version
  token or checksum for downstream binding; **status** — every beat is
  either `USER 定案`(with date) or clearly marked as an unconfirmed draft
  (【草案待 USER 砍定】). A beat sheet whose beats are all drafts is a 攤田
  record, not a finished beat sheet.
- **Ordered beats — THREE layers each, all required**:
  1. **畫面** (the picture): one transmitting picture, a short paragraph,
     never a label.
  2. **玩家心裡發生什麼** (what happens in the player's chest): the
     emotional state this beat induces.
  3. **憑什麼到位** (what makes it land HERE): the emotional precondition
     from earlier beats that makes this beat work in this position — beat
     order is justified by emotional preconditions, not by plot sequence.
     (vinci_world precedent: 「你來找什麼？」asked one beat early is a form
     field; asked after the wish has been drawn out, it is being seen.)
- **Curve marks**: per beat, whether the payoff pressure HOLDS (壓) or
  RELEASES (放), and where the single top of the curve sits.
- **Rulings carried**: the USER rulings that constrain these beats, stated
  in plain words with their source and date.
- **攤田區**: surviving unconverged candidates, explicitly outside the curve.

## Downstream consumers

- `../delivery-planner/` assigns each beat to a delivery channel.
- CHAPTER STEP 2 (assignment mode) takes its task from this file instead of
  discovering story lines on the spot.
- Chapter review gates run the emotional-acceptance line against this file:
  which beat did the output transmit; did the holds and releases survive;
  **did the landed order preserve each beat's 憑什麼到位.**

## Revision

The beat sheet is USER-ruled content: revising a beat re-enters the dialogue
protocol (攤田 the alternatives → USER cuts → converge, writing at the moment
of the cut). Downstream artifacts built on a revised beat re-run their steps;
the beat sheet records the revision date, what changed, and the new version
evidence. Any existing delivery plan is invalid until it is either re-run
from that new version or explicitly marked stale. This applies even when the
picture changes but the chapter premise still sounds similar: downstream
channel assignments are allowed to survive only after the delivery-planner
re-checks them against the revised beat.
