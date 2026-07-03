# Story Logic Ledger

*Causality-first ledger for generating or revising story scenes (especially fights): forces stakes, constraints, info distribution, beat reasons, fight trigger, and aftermath deltas before any prose or runtime data is written.*

Use this doc when you need to:
- Revise a scene motivation ("why are they fighting?")
- Generate new plot beats without hand-waving causality
- Keep scenes consistent across branches/timelines

This is writing-only. The canonical artifacts live in:
- <STORY_ROOT>/templates/scene_logic_ledger.md
- <STORY_ROOT>/battle_reason_*.md

## Hard rules

1) No prose first: do not write narrative lines until the ledger is coherent.
2) Every beat must answer: why now / why this action / why this character.
3) Fight scenes must have: trigger, optimization goal, and stop condition.
4) If you cannot justify a beat with visible evidence, revise the beat.

## Inputs to request (if missing)

- Scene name + where it sits in the timeline
- Which characters/factions are present
- What the player can do (choices)

If details are missing, proceed with explicit assumptions and mark them.

## Output format (always)

### 1) Scene Logic Ledger (filled)
Fill the template fields as bullets.

### 2) Evidence list
List 3–6 on-screen evidence anchors that make the ledger feel inevitable.

### 3) Aftermath deltas
List what changes in:
- knowledge (who learns what),
- leverage/debts,
- pressure level.

### 4) Next-step routing
Pick one:
- If user wants runtime implementation: land via the adapter `LANDING_SPEC.md`.
- If user wants tone pass: hand off to the project `STYLE_GUIDE.md` (if present).
- If user wants quoted lines only: hand off to the factory craft doc `core/craft/quoted-dialogue.md`.

## Quality bar (fail conditions)

- "They fight because they are enemies" (insufficient)
- Beat reasons that could swap between characters with no change
- Fights that have no clear end condition
