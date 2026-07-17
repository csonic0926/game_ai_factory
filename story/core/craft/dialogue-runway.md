# Craft — dialogue-runway

Build a short line-by-line conversation runway that lands on a USER-set
destination line (a creative KPI), so that when the destination line arrives
it feels EARNED — an invitation, never a questionnaire item.

Origin: vinci_world entry rework (2026-07-07). The USER defined the KPI
「這段對話最終要落在『你喜歡收藏卡牌嗎？』」 and named the gap: a
professional screenwriter knows how to pave the approach; the USER sets the
destination and the arrival emotion, this craft paves. The division of labor
is fixed: **the USER owns the KPI and the cut; this craft owns candidate
paths only.**

## Input

1. Scene constraints: who speaks, where, and the line budget (default 4–7
   lines; small is the point — a runway is not a scene).
2. The KPI destination line, verbatim, in `<PRIMARY_LOCALE>`.
3. The arrival emotion: what should be true in the player's chest at the
   moment the destination line lands (e.g. "my just-formed wish has an
   answer ready" / "this is a fellow, not a clerk").
4. The world's sovereignty files (world rules, narrative delivery) — the
   runway must not spend any token the world forbids.
5. `<ADAPTER>/GLOSSARY.csv` when present. Missing means `NOT_AVAILABLE` and
   the craft keeps its previous behavior. When present it is the sole
   canonical proprietary-term source; never manufacture or override a term
   entry from sovereignty prose, style/lint files, or shipped locale prose.

## Rules (also the self-check list)

1. **The question must be earned.** Whoever asks the destination question
   pays FIRST with a self-disclosure of the same kind (their own affection,
   their own loss). An unearned destination line reads as a form field.
2. **Exposition rides on objects, not on lines.** If the world's law or
   backstory must show, put it in a thing the NPC handles (a worn empty
   card sleeve says the projection law; no line explains it).
3. **One line, one move.** Every line advances the emotional state by
   exactly one step, and the runway annotates that move per line. A line
   that only decorates is cut.
4. **The destination line comes last and lands as an invitation.** Nothing
   after it; no follow-up question stacked on it.
5. **Observation before interrogation.** Any line that turns attention to
   the player states something SEEN (「你兩手空空」), never demands
   something told.
6. **Use the registered term for this mouth.** When the glossary exists,
   canon forms and en/ko counterparts are authoritative. Apply `register` and
   `speaker_scope`, keep `dialogue_protected=true` forms exact, and use no
   `banned` form. If the runway needs a new world noun, classifier convention,
   or spoken variant, list it as a `status=pending` nomination; do not decide
   it for the USER.

## Output

THREE candidate runways taking distinctly different approach angles (e.g.
affection-first / place-first / object-first), each formatted as:

- numbered lines in `<PRIMARY_LOCALE>`, natural speech per the adapter
  style guide;
- per line, one short annotation: what this line moves;
- one closing note: which rule was hardest to satisfy in this candidate
  (honesty loop — the next gate or the USER adjudicates it).

The USER cuts (picks one, splices, or kills all three and re-briefs). In a
headless pipeline run, produce the three candidates and report
BLOCKED_ON_USER_CUT rather than picking one — the cut is USER-owned.

Before handoff, run `scripts/glossary_check.py` when the glossary exists, then
chain the separate `spoken-fluency` worker. In clean-room mode, that worker
receives only the mechanically extracted protected/banned forms as plain
speech, never the CSV itself; the canon-aware back-check reads the glossary.

## Downstream

The chosen runway lands through the normal chapter steps (script → landing);
review gates check the landed lines against the runway's annotations — the
emotional-acceptance line applies (which beat did this transmit; did the
hold survive).
