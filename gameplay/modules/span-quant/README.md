# Module — Span Quant Sheet

This manual authoring module fixes the quantity demand for one gameplay span
before any Beat Sheet exists. It answers, in order: where the span starts and
ends, what beat the choices must arrive on, and what there is to play that can
hold that beat. Content sufficiency is decided here; the Beat Sheet then
supplies it.

Read first:

- `../../docs/GAMEPLAY_EXPERIENCE_BEAT_SHEET_CONTRACT.md` (authority chain)
- the resolved `PROJECT_GAMEPLAY_PROFILE.md`
- exact story/current-state sources named by that profile

Use `../../templates/SPAN_QUANT_SHEET.md`. Write the result in the game repo:

```text
<GAMEPLAY_ROOT>/span_quants/<span_id>.md
```

## The unit and the beat

The unit of gameplay is one meaningful choice:
`information -> guess -> commitment -> consequence -> later-emotion influence`.
A choice is meaningful when it can influence later emotion (positive or
negative both count). A certain-outcome click poses no guess and is never a
unit.

The demand is a **cadence**: the factory's canonical beat is one new
meaningful choice arriving every **3–5 seconds** (max arrival gap 5000 ms).
A project changes tempo only through an explicit USER ruling in its Gameplay
Profile; the factory never infers a different beat. Total duration is free —
a search may stay open for hours — provided arrivals hold the beat inside it.
A choice need not resolve within one beat.

## Why demand comes first

A budget written beside a Beat Sheet inherits the sheet's optimism: the sheet
has six clicks, the budget asks for six clicks, and every later gate passes a
span that plays like six clicks. Insufficiency must fail here, while the fix
is cheap — add generators, narrow the span, or name the missing content
demand for design to supply.

## Authoring order

1. **Span (step 0).** Fix recognizable start/end player situations and the
   observable runtime boundary each requires.
2. **Cadence (step 1).** Adopt the factory beat, or cite the project's
   explicit USER-ruled override. Estimate course length for production
   scoping only.
3. **Desire line + inventory (step 2).** Implementation-blind, from player
   expectation for this genre/situation/cadence: name the span's main want,
   then enumerate generators and one-shots. Every unit answers three
   questions — which later emotion it influences and how; what information
   lets the player guess; whether a basic guess survives missed hints.
4. **Cadence walk.** Walk the expected course; find the longest arrival gap;
   every stretch must hold the beat.
5. **Chain rule.** Each choice's consequence must deliver the next choice's
   hint material. Name every break.
6. **Derive the legacy floors.** Content counts, control ratio, and gap
   proxies are arithmetic consequences of the inventory, not aspirations.

## The failure modes this module exists to stop

- **Inflation:** six clicks claimed to sustain five minutes. Dwell and
  arrival-rate claims must be defensible against player expectation; the
  fresh review challenges each one.
- **Dead loop:** reading game code or counting existing content to decide
  what is enough. Supply then defines demand and every thin span passes.
  Sufficiency comes from player expectation; if reality falls short, the game
  is thickened or the demand re-ruled through an explicit new quant version.
- **Cadence breach:** long stretches with zero choice arrival. The old
  traversal-gap cap measured motion types and once drove a search span to
  place its waymark on the same screen; the correct object is the arrival
  gap. Walking with a live guess is anticipation inside an open choice —
  never shrink a search to satisfy a gap bound.
- **Chain break:** a consequence that ends without seeding the next guess.
  The next choice then starts cold and the span falls apart into disconnected
  clicks.

If the honest inventory cannot hold the beat, the sheet fails forward:
narrow the span, add generator demand, or name the missing content
explicitly. Do not pad the table.

## Fresh review

Use `../../templates/QUANT_REVIEW.md` in a fresh context with file-only
handoff. The reviewer writes `<GAMEPLAY_ROOT>/qa/<span_id>_QUANT_REVIEW.md`,
returns only `PASS_QUANT_REVIEW` or `FAIL_QUANT_REVIEW`, and edits nothing.

## Revision discipline

Any span/cadence/inventory/floor change creates a new version and makes the
Beat Sheet and all downstream artifacts bound to the prior version `STALE`.
