# Module — beat-sheet-dialogue

Interactive module that produces a chapter's **emotional beat sheet** — the
topmost upstream artifact of chapter production. It answers the question no
other input answers: *what emotion is this story supposed to transmit, in
what order, with what curve.* (Foundations: `../../core/NARRATIVE_FOUNDATIONS.md`.)

**This cannot be automated.** The beat sheet is born from a dialogue; the
fixed protocol is:

1. **AI 攤田** (spread the field): lay out candidate beats at the SAME
   altitude — one line per beat, each line one CONCRETE picture, no
   derivation, no induction, no grouping into themes. A line like 「建立
   期望」(build anticipation) is an instruction, not a picture, and is
   invalid; 「同船的人聊自己想找什麼，有人的 want list 摺得又舊又軟」is a
   picture — the reader's chest moves before anything is explained.
2. **USER cuts and rules**: keeps, kills, reorders, rewrites; adds rulings
   (which pictures are emotionally usable in this world, which are not).
3. **Converge**: the surviving, ordered beats are written down as the beat
   sheet, with the emotional curve marked — where to HOLD (壓) and where to
   RELEASE (放).

In a headless run this module cannot execute; a pipeline that needs a beat
sheet and finds none reports it as an open USER dependency rather than
inventing one.

## The artifact

Location: `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`
(one beat sheet = one chapter unit, containing multiple scenes).

Required content, in the chapter's `<PRIMARY_LOCALE>`, rich prose per the
adapter's style guide:

- **Header**: chapter unit name; scope (where the unit begins and ends);
  sources (which conversation / which recorded rulings); **status** —
  every beat is either `USER 定案`(with date) or clearly marked as an
  unconfirmed draft (【草案待 USER 砍定】). A beat sheet whose beats are all
  drafts is a 攤田 record, not a finished beat sheet.
- **Ordered beats**: each beat is one transmitting picture (one short
  paragraph is fine; a label is not), grouped under the scene it belongs to.
- **Curve marks**: per beat, whether the acquisition/payoff pressure HOLDS
  (壓) or RELEASES (放), and where the single top of the curve sits.
- **Rulings carried**: the USER rulings that constrain these beats, stated
  in plain words with their source and date.

## Downstream consumers

- `../delivery-planner/` assigns each beat to a delivery channel.
- CHAPTER STEP 2 (assignment mode) takes its task from this file instead of
  discovering story lines on the spot.
- Chapter review gates run the emotional-acceptance line against this file:
  which beat did the output transmit; did the holds and releases survive?

## Revision

The beat sheet is USER-ruled content: revising a beat re-enters the dialogue
protocol (攤田 the alternatives → USER cuts → converge). Downstream artifacts
built on a revised beat re-run their steps; the beat sheet records the
revision date and what changed.
