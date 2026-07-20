# Gameplay Experience Beat Sheet Contract v1

## Purpose and authority

The **Gameplay Experience Beat Sheet** is the highest semantic authority for
one gameplay span. It states the player experience production must preserve;
it does not prescribe engine APIs, scene paths, data rows, or asset names.

Above it sits one quantity authority: the **Span Quant Sheet** fixes the
span's boundaries, cadence contract, and implementation-blind
playable-content inventory with derived budget floors before any Beat Sheet
is authored. The Beat Sheet decides what the experience means; the quant
sheet decides how often meaningful choices must arrive. Supply satisfies
demand, never the reverse.

The authority chain is:

```text
approved Span Quant Sheet version
  -> approved Beat Sheet version
  -> approved Playable Walkthrough Trace
  -> approved Playable Beat Packets and observation plans
  -> landed runtime plus instrumentation
  -> observed runtime evidence
  -> factory-conformance acceptance
```

A Beat Sheet is a supply against an approved quant demand, and a walkthrough
is a realization of a Beat Sheet, not a replacement for either. Every
downstream artifact must bind to the exact source path, version token,
authority status, and checksum. A changed quant sheet makes the Beat Sheet
`STALE`; a changed sheet makes downstream artifacts `STALE` until they are
reviewed or regenerated against the new version.

## Authority status and version evidence

Every sheet declares exactly one status:

- `USER_APPROVED` — the USER has ruled on the direction and the approval
  source/date are recorded.
- `AI_DRAFT_FOR_REVIEW` — auto/headless authoring may proceed, but every AI
  assumption is explicit and no artifact may claim USER direction approval.
- `STALE` — a source, ruling, or scope changed after this version was made.

The header must contain:

```yaml
sheet_id: stable project-owned id
scope: recognizable starting player situation -> ending player situation
revision_date: YYYY-MM-DD
change_record: plain-language description
version_token: stable revision token
content_checksum: sha256 of the sheet using the project-declared checksum rule
status: USER_APPROVED | AI_DRAFT_FOR_REVIEW | STALE
approval_or_draft_source: USER ruling ref/date or AI author/session ref
```

USER rulings and AI assumptions live in separate sections. Silence, prior
model output, a story document, and implementation convenience are not USER
rulings.

## Sheet-level required content

### 1. Identity and scope

Record the stable sheet id, exact start/end situations, story-anchor and
world/player-state sources, Project Gameplay Profile version, and target game
mode/platform assumptions. Sources use game-repo-relative paths or stable
interfaces.

### 2. Mandatory Quantitative Experience Budget

Every sheet owns one **Quantitative Experience Budget** for exactly the same
runtime span. It is not optional pacing commentary, and it is not authored
here: its floors restate the approved Span Quant Sheet's derived floors. The
sheet binds the quant sheet's exact path/version/checksum and its
`PASS_QUANT_REVIEW` artifact, may tighten a floor, and may never loosen one
without a new quant version. The sheet records the values and binds a
game-owned machine-readable projection conforming to
`../schemas/experience_budget.schema.json`; the projection must have the same
sheet path/id/version/checksum and must not silently differ from the sheet or
the quant floors.

The budget must declare:

- exact observable runtime start and end boundaries (not approximate story
  anchors or packet names);
- first-play duration target, minimum, and maximum, plus an optional replay
  target;
- minimum player-control ratio over the exact span;
- maximum uninterrupted presentation-only gap and maximum uninterrupted
  traversal-only/no-gameplay gap;
- required minimum/maximum counts for complete gameplay beats, meaningful
  decisions, combat encounters, world interactions, and narrative
  presentations;
- required minimum/maximum total narrative-presentation time.

Because the budget is Beat Sheet authority authored before runtime exists, it
must not contain a run id or session id. It owns only the boundary selectors;
the runtime run/session target is supplied when measurement is invoked and is
recorded in the measurement result.

Every count binds reviewed acceptance-kernel evidence or paired temporal
selectors. One complete chain always counts as one complete gameplay beat and
may satisfy at most one of the decision/combat/world-interaction quotas. Raw
event names/labels never self-certify gameplay. The
machine-readable budget also identifies non-gameplay activity evidence where
present so the reader can report why an input-bearing span still has no
complete gameplay engagement.

### 3. Target player frame

State what the entering player already knows, can do, and currently wants;
whether the target is first-time, returning, expert, or another
adapter-declared frame; and the allowed error, navigation, risk, and attention
assumptions.

### 4. Ordered experience curve

List the beats in player-time order. Mark every beat `build`, `hold`,
`release`, `recovery`, or `rest`. State the span's tension, curiosity,
mastery, and expression arcs and identify any open loops deliberately carried
past the end.

### 5. Rulings and red lines

Record player-facing meaning production must not rewrite, control/timing
boundaries that must survive, and forbidden degradations such as:

- following an objective marker as the only work;
- replacing player-earned action with a cutscene;
- releasing a hold early through a reward or completion popup;
- turning a meaningful alternative into cosmetic wording;
- making required evidence available only in hidden state or author notes.

## Per-beat required content

Every beat stays at the same abstraction level and is written in concrete
player time. Filling headings with abstract labels is a review failure.

### 1. Concrete player situation

What the player can see, hear, control, and bear now. “Explore,” “build
anticipation,” or “feel survival” without a playable situation is invalid.

### 2. Live player purpose or question

What the player is trying to complete, confirm, avoid, test, or express. The
purpose must be able to arise from evidence already available to the player;
an author declaration alone cannot create player intent.

### 3. Why this beat works here

Name the required prior knowledge, resource pressure, skill, relationship, or
open question. Say what the experience loses if the beat happens earlier or
later.

### 4. Primary engagement mode

Choose one primary mode and optional secondary modes:

- `decision`
- `execution/mastery`
- `discovery/interpretation`
- `expression/social`
- `payoff/recovery`

Labels never substitute for concrete work and response.

### 5. Player work

State the cognitive, spatial, sensory, rhythmic, strategic, operational,
memory, expressive, or social work. A beat with no work must be an explicit
payoff, recovery, or rest beat, cite the upstream loop it pays, and carry a
duration budget.

### 6. Agency or challenge source

Prove why the beat is not mere compliance:

- `decision`: contemporaneously knowable, actionable alternatives with
  materially different consequences and no obviously dominant answer. A
  decision counts only when runtime evidence supports at least two
  contemporaneously reachable alternatives and distinct observable
  response/carry-forward consequences;
- `execution/mastery`: readable pattern, improvable skill dimension, failure
  feedback, and another opportunity to adjust;
- `discovery/interpretation`: unresolved question, obtainable evidence, and a
  hypothesis that evidence can update;
- `expression/social`: expressible preference or stance and a world response
  that recognizes it;
- `payoff/recovery`: upstream commitment being paid; no unearned reward.

Not every beat needs a choice. It does need completeness for its declared
mode.

### 7. Commitment and pressure

What the player commits: time, position, resource, exposure, opportunity,
rhythmic accuracy, relationship stance, or attention. If commitment is zero,
explain why the beat still holds.

### 8. Observable world response

How the world answers the player's work and how camera, HUD, sound, animation,
dialogue, state change, or spatial consequence makes that answer receivable.
A completion receipt alone is not a world response.

### 9. Intended player change

The intended delta in knowledge, skill, strategy, desire, confidence,
relationship reading, or future expectation. This is an intention, never a
claim that every player certainly felt or understood it.

### 10. Carry-forward

How the response and intended change create the next intent, choice tendency,
or open question — and deliver the hint material for the next choice's guess
(chain rule). A consequence that ends without seeding the next guess breaks
the chain. A new unrelated objective issued by the system does not count as
carry-forward.

### 11. Failure, misread, and recovery

What happens if a cue is missed, an alternative is chosen, execution fails,
or the player forms another reasonable interpretation. Mark acceptable drift,
fail-forward behavior, and reset boundaries.

### 12. Acceptance kernel

State the smallest runtime-observable evidence chain required for this beat to
exist after production:

```text
cue presentation
  -> player action or attempt
  -> observable world response
  -> carry-forward consequence
```

The kernel also names required evidence modes and negative/red-line checks.
Unobservable understanding or emotion is represented as fair reception
conditions plus a blinded-reader question, never as a logger field.

Recommended structured shape:

```yaml
kernel_id: stable id
required_chain:
  cue: observable event/presentation requirement
  action_or_attempt: observable input/action requirement
  world_response: observable response requirement and latency budget
  carry_forward: observable later-state or player-situation requirement
required_evidence_modes:
  - LIVE_BLIND_RUN | RECORDED_RUN | CONTROLLED_BRANCH_PROBE | STATIC_RUNTIME_ASSERTION
blind_reader_question: purpose/forecast/alternative/update question, or NONE
negative_checks: []
acceptable_drift: []
```

Decision alternatives require a controlled branch probe or equivalent runtime
evidence that fails closed, begins from an equivalent contemporaneous player
situation, and proves distinct observable response/carry-forward
consequences. Different branch labels or inputs with identical consequences
do not count. Mastery that depends on learning from failure requires evidence
that distinguishes miss/partial/success and exposes adjustment. A single
golden path cannot satisfy either claim.

## Type-specific completeness rule

A beat fails if it contains no decision, mastery demand, discovery,
expression, or payoff from an existing loop. Merge it, remove it, identify it
as a non-gameplay presentation moment, or redesign it. Never insert fake
alternatives just to satisfy a schema.

Pressing a teleporter, advancing dialogue, accumulating raw button/input
counts, straight locomotion, reaching an objective trigger, and passive state
changes do **not** independently count as gameplay. Control return, movement,
input, or an arrival receipt does not repair the absence of a complete cue ->
attempt -> world response -> carry-forward engagement chain. A span containing
only those activities is `NO_GAMEPLAY`, not a gameplay segment.

## Authoring protocol

The contract is mandatory; the dialogue prompts are not a questionnaire.
Ask only the 3–5 questions that can most change the current span, such as:

- Which personally performed experience should the player later describe?
- Is satisfaction earned through judgment, mastery, discovery, expression,
  or being answered by the world?
- Which result must be earned rather than delivered by dialogue/cutscene/UI?
- Where should hesitation come from: uncertainty, cost, skill, or values?
- What should failure teach or redirect?

In a live session, write each confirmed USER ruling to the sheet when it is
made. In auto mode, make the best project-supported draft, mark it
`AI_DRAFT_FOR_REVIEW`, and list assumptions/open items.

## Fresh design review gate

A fresh reviewer receives the saved sheet and its declared sources through a
file-only handoff. It returns `PASS_DESIGN_REVIEW` or `FAIL_DESIGN_REVIEW` and
does not edit the sheet.

The reviewer checks:

- the sheet binds an approved Span Quant Sheet with `PASS_QUANT_REVIEW`, its
  budget floors equal or tighten the quant floors, every quant content-count
  floor names its supplying beats, and no padding beats were inserted only to
  reach a floor;
- the beat flow holds the quant cadence — no stretch runs past the maximum
  arrival gap without a live choice arrival — and every beat's world
  response delivers hint material for the next beat's choice (chain rule);
- every beat is a concrete player situation;
- purpose can grow from information available at runtime;
- the primary mode has real work and complete agency/challenge/payoff;
- response changes later play rather than only acknowledging completion;
- carry-forward creates a causal intent chain;
- build/hold/release/recovery/rest order is causal;
- every acceptance kernel can be supported by the Observation Adapter;
- the Quantitative Experience Budget is complete, exact-span bound, internally
  coherent, and its machine-readable selectors point to evidence rather than
  trusting raw gameplay/decision labels;
- prohibited non-gameplay actions are not counted independently and every
  decision requires controlled/equivalent branch-consequence proof;
- USER rulings and AI assumptions are separate and version evidence is exact.

Semantic emptiness fails even when every heading is filled. On failure, the
review artifact names the first invalid beat/transformation and routes back to
Beat Sheet authoring; the reviewer never repairs and passes its own work.
