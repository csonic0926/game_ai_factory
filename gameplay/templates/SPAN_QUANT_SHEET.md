# Span Quant Sheet — `<SPAN_ID>`

Quantity demand for one gameplay span, authored before any Beat Sheet. The
Beat Sheet must satisfy this sheet; this sheet never bends to fit an existing
implementation.

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

## Step 1 — Duration ruling

- **First-play duration (target / minimum / maximum ms):**
- **Optional replay target duration ms:** `NONE | <NUMBER>`
- **Ruling source:** USER ruling ref/date, or explicit AI draft assumption

Duration is a pacing decision from story/arc rhythm, never from how much
content happens to exist.

## Step 2 — Playable-content inventory (implementation-blind)

Answer from player expectation for this genre, situation, and duration: what
is there to play? Do not read game code or count existing content to decide
what is enough — supply must never define demand.

| Unit id | Engagement kind | Concrete player work | Engaged time per unit ms (min / typical) | Instances | Subtotal ms (min) | Why this is not a click |
| --- | --- | --- | ---: | ---: | ---: | --- |
|  | decision \| combat \| world_interaction \| execution/mastery \| discovery \| expression \| payoff/recovery |  |  |  |  |  |

Non-gameplay activity (teleporter press, dialogue advance, raw input,
straight locomotion, objective arrival, passive state change, control return,
presentation) may not enter this table.

- **Sum of minimum engaged time ms:**
- **Duration minimum ms it must fill:**
- **Engaged-time fill ratio (sum / duration minimum):**
- **Expected narrative/presentation time ms (total / longest single gap):**
- **Expected traversal time ms (total / longest single gap):**

A sum that only reaches the duration by inflating per-unit time is the exact
failure this sheet exists to prevent.

## Derived budget floors

These values become the Beat Sheet's Quantitative Experience Budget. The Beat
Sheet may tighten them; it may never loosen them without a new quant version.

- **Minimum player-control ratio (0–1):**
- **Maximum uninterrupted presentation-only gap ms:**
- **Maximum uninterrupted traversal-only/no-gameplay gap ms:**

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
- [ ] The duration ruling has an explicit source.
- [ ] Every inventory unit is qualified gameplay with concrete player work.
- [ ] No non-gameplay activity entered the inventory.
- [ ] Per-unit engaged times are defensible against genre expectation, not
      inflated to make the sum reach the duration.
- [ ] Minimum engaged time fills the duration minimum at the declared control
      ratio, with the remainder explicitly presentation/traversal inside the
      gap limits.
- [ ] Derived floors are arithmetic consequences of the inventory, and every
      content-count floor names its supplying units.
- [ ] The blindness attestation is truthful.
- [ ] USER rulings and AI assumptions are separate; version evidence is exact.
