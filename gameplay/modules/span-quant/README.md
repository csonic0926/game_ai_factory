# Module — Span Quant Sheet

This manual authoring module fixes the quantity demand for one gameplay span
before any Beat Sheet exists. It answers, in order: where the span starts and
ends, how long it must hold the player, and what there is to play for that
long. Content sufficiency is decided here; the Beat Sheet then supplies it.

Read first:

- `../../docs/GAMEPLAY_EXPERIENCE_BEAT_SHEET_CONTRACT.md` (authority chain)
- the resolved `PROJECT_GAMEPLAY_PROFILE.md`
- exact story/current-state sources named by that profile

Use `../../templates/SPAN_QUANT_SHEET.md`. Write the result in the game repo:

```text
<GAMEPLAY_ROOT>/span_quants/<span_id>.md
```

## Why demand comes first

A budget written beside a Beat Sheet inherits the sheet's optimism: the sheet
has six clicks, the budget asks for six clicks, and every later gate passes a
span that plays like six clicks. Insufficiency must fail here, while the fix
is cheap — add content demand, shorten the duration, or narrow the span.

## Authoring order

1. **Span (step 0).** Fix recognizable start/end player situations and the
   observable runtime boundary each requires.
2. **Duration (step 1).** Rule how long the span must hold a first-time
   player. This is a pacing decision from story/arc rhythm, not from how much
   content happens to exist.
3. **Inventory (step 2).** Implementation-blind, answer from player
   expectation for this genre/situation/duration: what is there to play?
   Enumerate qualified units with concrete player work, defensible per-unit
   engaged time, and instance counts. Sum them against the duration.
4. **Derive the floors.** Content counts, control ratio, and gap maxima are
   arithmetic consequences of the inventory, not aspirations.

## The two failure modes this module exists to stop

- **Inflation:** six clicks claimed to sustain five minutes. Per-unit times
  must be defensible against player expectation for the genre; the fresh
  review challenges each one.
- **Dead loop:** reading game code or counting existing content to decide
  what is enough. Supply then defines demand and every thin span passes.
  Sufficiency comes from player expectation; if reality falls short, the game
  is thickened or the duration re-ruled through an explicit new quant
  version — never by silently bending this sheet to the implementation.

If the honest inventory cannot fill the duration, the sheet fails forward:
shorten the duration, narrow the span, or name the missing content demand
explicitly for design to supply. Do not pad the table.

## Fresh review

Use `../../templates/QUANT_REVIEW.md` in a fresh context with file-only
handoff. The reviewer writes `<GAMEPLAY_ROOT>/qa/<span_id>_QUANT_REVIEW.md`,
returns only `PASS_QUANT_REVIEW` or `FAIL_QUANT_REVIEW`, and edits nothing.

## Revision discipline

Any span/duration/inventory/floor change creates a new version and makes the
Beat Sheet and all downstream artifacts bound to the prior version `STALE`.
