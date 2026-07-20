# Span Quant Sheet — `<SPAN_ID>`

Quantity demand for one gameplay span, authored before any Beat Sheet. The
Beat Sheet must satisfy this sheet; this sheet never bends to fit an existing
implementation.

The unit of gameplay is one meaningful choice:
`information -> guess -> commitment -> consequence -> later-emotion influence`.
The demand is a cadence of choice arrivals, not a total duration.

## Identity, authority, and version

- **Quant id:** `<SPAN_ID>`
- **Scope:** `<RECOGNIZABLE_STARTING_SITUATION>` → `<RECOGNIZABLE_ENDING_SITUATION>`
- **Story-anchor source/range/version:**
- **World/player-state source/version:**
- **Project Gameplay Profile path/version:**
- **Revision date:**
- **Change record:**
- **Version token:**
- **Content checksum / rule:**
- **Status:** `USER_APPROVED | AI_DRAFT_FOR_REVIEW | STALE`
- **Approval or draft source:**

## USER rulings

Only USER-confirmed rulings, each with source/date.

## AI assumptions and open items

Never merge these into USER rulings.

## Step 0 — Span boundaries

- **Starting player situation (recognizable):**
- **Ending player situation (recognizable):**
- **Required observable runtime start boundary (description):**
- **Required observable runtime end boundary (description):**

Exact event selectors are bound later in the Beat Sheet's machine-readable
budget and preflighted against the Observation Adapter.

## Step 1 — Cadence contract

- **Factory canonical beat:** one new meaningful choice arrives every
  **3–5 seconds**; maximum arrival gap **5000 ms**.
- **Project override:** `NONE | <explicit USER-ruling ref in the game repo's
  PROJECT_GAMEPLAY_PROFILE.md>` — the factory never infers a different beat.
- **Cadence used by this sheet (target range / max arrival gap ms):**

Total span duration is free: a single choice (a search, a held objective) may
stay open for hours, provided new choices keep arriving on the beat inside
it. A choice need not resolve within one beat; arrivals hold the tempo,
resolutions do not.

- **Course length estimate (production scoping only — target / min / max ms):**
- **Estimate basis:** expected course of play at the cadence. This is never
  an experience target; do not shrink or pad content to hit it.

## Step 2 — Desire line and playable-content inventory (implementation-blind)

Answer from player expectation for this genre, situation, and cadence: what
is there to play? Do not read game code or count existing content to decide
what is enough — supply must never define demand.

- **Desire line (the span's main want):**

Every unit takes its emotional sign relative to the desire line: accelerating
it is positive, obstructing it is negative, deferred value is neutral now and
pays later.

| Unit id | Kind | The choice posed (what the player guesses) | Later emotion influenced + sign vs desire line | Info given → basic guess if all hints missed | Dwell per arrival ms (anticipate + watch) | Arrival rate or instances |
| --- | --- | --- | --- | --- | ---: | --- |
|  | generator \| one_shot |  |  |  |  |  |

- `generator`: a structure that keeps emitting choices while live (junctions
  during a search, roaming encounters, drop take/leave calls).
- `one_shot`: a choice that arises once.
- A unit with a certain outcome and nothing to guess may not enter the
  table. Non-gameplay activity (teleporter press, dialogue advance, raw
  input, straight commute, objective arrival, passive state change, control
  return, presentation) never qualifies on its own.
- Micro-arrivals inside an execution phrase (e.g. QTE pulses) hold the beat
  as arrivals; they are not separate quota units.
- Walking with a live guess is anticipation dwell inside an open choice.
  Commute with nothing to guess is dead time and counts against the arrival
  gap. Never shrink a search to satisfy a gap bound.

## Cadence sustainability walk

Walk the expected course; every stretch must hold the beat.

| Course stretch | Live generators / pending one-shots | Longest expected arrival gap ms | Within max gap? |
| --- | --- | ---: | --- |
|  |  |  |  |

- **Longest arrival gap anywhere in the course ms:**
- **Stretch where it occurs, and why it is acceptable or how it is fixed:**

## Chain rule — consequences carry the next hints

| Choice | Its observable consequence | Next choice it delivers hints for |
| --- | --- | --- |
|  |  |  |

A consequence that ends without seeding the next guess breaks the chain;
name the break and the missing hint material.

## Derived budget floors (legacy projection)

These values project into the Beat Sheet's machine-readable
`QUANTITATIVE_EXPERIENCE_BUDGET.json` (duration-based schema v1). They are
derived from the cadence and course estimate; runtime cadence measurement is
not yet implemented, so the gap caps below act as crude arrival-gap proxies.
The Beat Sheet may tighten them; it may never loosen them without a new
quant version.

- **Minimum player-control ratio (0–1):**
- **Maximum uninterrupted presentation-only gap ms:** (≤ max arrival gap
  unless an explicit override rules otherwise)
- **Maximum uninterrupted commute/no-guess traversal gap ms:** (≤ max
  arrival gap; searching with a live guess is not traversal dead time)

| Required content/time measure | Minimum | Maximum | Supplied by inventory units |
| --- | ---: | ---: | --- |
| Complete gameplay beats |  |  |  |
| Meaningful decisions |  |  |  |
| Combat encounters |  |  |  |
| World interactions |  |  |  |
| Narrative presentations |  |  |  |
| Narrative-presentation time ms |  |  |  |

## Blindness attestation

- **Sources read:** (Project Gameplay Profile, story anchors, current state
  only)
- **Game code, content data files, or existing-content counts read to decide
  sufficiency:** `NONE` (anything else invalidates this sheet)

## Author self-audit

- [ ] Span start/end are recognizable player situations with observable
      boundary requirements.
- [ ] The cadence is the factory canonical beat, or an explicit USER-ruled
      override is referenced; no inferred tempo.
- [ ] Every inventory unit poses a real guess and answers the three
      qualification questions: which later emotion it influences and how,
      what information lets the player guess, and whether a basic guess
      survives when every hint is missed.
- [ ] No certain-outcome click entered the table.
- [ ] Emotional signs are computed relative to the declared desire line.
- [ ] Dwell and arrival-rate claims are defensible against player
      expectation, not inflated to hold the beat on paper.
- [ ] The cadence walk covers the whole course and names the longest gap.
- [ ] Every major consequence delivers the next choice's hints; chain breaks
      are named.
- [ ] The course length estimate is scoping only; no content was shrunk or
      padded to fit it.
- [ ] Derived floors are arithmetic consequences of the inventory, and every
      content-count floor names its supplying units.
- [ ] The blindness attestation is truthful.
- [ ] USER rulings and AI assumptions are separate; version evidence is exact.
