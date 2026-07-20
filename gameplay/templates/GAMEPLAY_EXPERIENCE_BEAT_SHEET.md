# Gameplay Experience Beat Sheet — `<SHEET_ID>`

## Identity, authority, and version

- **Sheet id:**
- **Scope:** `<RECOGNIZABLE_STARTING_SITUATION>` → `<RECOGNIZABLE_ENDING_SITUATION>`
- **Story-anchor source/range/version:**
- **World/player-state source/version:**
- **Project Gameplay Profile path/version:**
- **Target game mode/platform assumptions:**
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

## Target player frame

- **Player frame:** first-time | returning | expert | adapter-declared
- **Already knows:**
- **Already can do:**
- **Current entering purpose:**
- **Allowed mistakes/navigation drift/risk:**
- **Attention and accessibility assumptions:**

## Quantitative Experience Budget — restates the approved quant floors

- **Approved Span Quant Sheet path/version/checksum:**
  `<GAMEPLAY_ROOT>/span_quants/<SPAN_ID>.md`
- **Quant review artifact/status:**
  `<GAMEPLAY_ROOT>/qa/<SPAN_ID>_QUANT_REVIEW.md` — `PASS_QUANT_REVIEW`
- **Machine-readable budget path:**
  `<GAMEPLAY_ROOT>/experience_beat_sheets/<SHEET_ID>_QUANTITATIVE_EXPERIENCE_BUDGET.json`
- **Schema:** `gameplay.experience_budget.v1`
- **Exact observable runtime start boundary:**
- **Exact observable runtime end boundary:**
- **First-play duration (target / minimum / maximum ms):**
- **Optional replay target duration ms:** `NONE | <NUMBER>`
- **Minimum player-control ratio (0–1):**
- **Maximum uninterrupted presentation-only gap ms:**
- **Maximum uninterrupted traversal-only/no-gameplay gap ms:**

| Required content/time measure | Minimum | Maximum | Supplying beats | Kernel or interval-selector refs |
| --- | ---: | ---: | --- | --- |
| Complete gameplay beats |  |  |  |  |
| Meaningful decisions |  |  |  | controlled/equivalent branch-consequence proof required |
| Combat encounters |  |  |  |  |
| World interactions |  |  |  |  |
| Narrative presentations |  |  |  |  |
| Narrative-presentation time ms |  |  |  |  |

Floors equal or tighten the approved quant floors; loosening any floor
requires a new quant version. The JSON projection must bind this exact sheet
path/id/version/checksum and contain the same thresholds and boundary
selectors. It must not contain a runtime run/session id; measurement supplies
those values separately. Each chain may count as a complete gameplay beat
plus at most one distinct content quota. Pressing a teleporter, advancing
dialogue, raw button/input counts, straight locomotion, reaching an objective
trigger, and passive state changes do not independently satisfy any gameplay
count.

## Experience curve

- **Tension arc:**
- **Curiosity arc:**
- **Mastery arc:**
- **Expression arc:**
- **Open loops carried past the span:**

| Order | Beat id | Curve mark | Primary engagement mode | One-line concrete situation |
| --- | --- | --- | --- | --- |
| 1 |  | build \| hold \| release \| recovery \| rest |  |  |

## Rulings and red lines

- **Meaning production must preserve:**
- **Player-control/timing boundary:**
- **Must not become:**

## Ordered beats

### Beat `<BEAT_ID>` — `<CONCRETE SITUATION, NOT AN ABSTRACT LABEL>`

- **Curve mark:** build | hold | release | recovery | rest
- **Primary engagement mode:** decision | execution/mastery | discovery/interpretation | expression/social | payoff/recovery
- **Secondary modes, if any:**

#### 1. Concrete player situation

What the player sees, hears, controls, and bears now.

#### 2. Live player purpose or question

What the player wants to complete, confirm, avoid, test, or express, and the
prior runtime evidence from which this purpose grows.

#### 3. Why this beat works here

Required prior condition and what is lost if moved earlier/later.

#### 4. Player work

Concrete cognitive/spatial/sensory/rhythmic/strategic/operational/memory/
expressive/social work. For payoff/recovery/rest, cite the upstream loop and
duration budget.

#### 5. Agency or challenge source

Mode-specific alternatives, pattern/skill/feedback, evidence/hypothesis,
expressible stance/world recognition, or upstream commitment being paid.

#### 6. Commitment and pressure

Time, position, resource, exposure, opportunity, rhythm, relationship stance,
or attention committed. Explain any zero-commitment beat.

#### 7. Observable world response

The response and player-receivable camera/HUD/sound/animation/dialogue/state/
spatial channels.

#### 8. Intended player change

Qualified intended delta in knowledge, skill, strategy, desire, confidence,
relationship reading, or expectation.

#### 9. Carry-forward

How the response/change creates the next intent, tendency, or open question,
and the hint material it delivers for the next choice's guess (chain rule).

#### 10. Failure, misread, and recovery

Reasonable miss/failure/alternate reading, acceptable drift, fail-forward,
and reset boundary.

#### 11. Acceptance kernel

```yaml
kernel_id:
required_chain:
  cue:
  action_or_attempt:
  world_response:
  carry_forward:
required_evidence_modes: []
blind_reader_question: NONE
negative_checks: []
acceptable_drift: []
```

## Author self-audit

- [ ] Every beat is a concrete player situation at the same abstraction level.
- [ ] Every purpose can form from player-available prior evidence.
- [ ] Every primary engagement mode is complete without fake choices.
- [ ] Every response changes or meaningfully hands off later play.
- [ ] Carry-forward forms one causal intent chain.
- [ ] The curve and open loops are causally ordered.
- [ ] Every acceptance kernel has an Observation Adapter evidence path.
- [ ] The budget binds an approved Span Quant Sheet with `PASS_QUANT_REVIEW`
      and every floor equals or tightens the quant floor.
- [ ] Every quant content-count floor names its supplying beats, with no
      padding beats inserted only to reach a floor.
- [ ] The beat flow holds the quant cadence: no stretch runs past the
      maximum arrival gap without a live choice arrival.
- [ ] Every beat's carry-forward delivers hint material for the next beat's
      choice; chain breaks are named and resolved.
- [ ] The exact-span Quantitative Experience Budget contains every mandatory
      threshold/range and matches its machine-readable projection.
- [ ] Gameplay counts use complete reviewed engagement chains, not event labels,
      input/movement/control/arrival, or passive state changes.
- [ ] Every counted decision has at least two contemporaneously reachable
      alternatives with distinct observed response/carry-forward consequences
      under controlled branch evidence or an equivalent fail-closed proof.
- [ ] USER rulings and AI assumptions are separate.
- [ ] Exact version evidence is present.
