# Gameplay Project Adapter Contract v1

## Ownership model

Gameplay Factory core is project-agnostic. The factory owns contracts,
schemas, reader tools, and blank answer sheets. Each game repo owns filled
answers and versions them beside the code/data/evidence they describe.

There are three independent answer surfaces:

1. **Project Gameplay Profile** — player frames, verbs, systems, spaces,
   engagement generators, presentation/control, grammar, budgets, and review.
2. **Production Adapter** — how approved packets land into runtime code/data,
   other factories, and mechanical validation.
3. **Observation Adapter** — how instrumentation captures actual play, maps it
   to canonical evidence, supports reproducible sessions/probes, and blinds
   the runtime reader.

Production tests cannot substitute for observation. The Observation Adapter
may physically be a mandatory independent section of the Production Adapter,
but its ownership, completeness, version, and blocker semantics remain
separate. The factory blank template uses a separate file.

## Canonical location

```text
<GAME_REPO>/design/gameplay/adapter/
  PROJECT_GAMEPLAY_PROFILE.md
  PRODUCTION_ADAPTER.md
  OBSERVATION_ADAPTER.md
```

Factory blanks remain under `gameplay/adapters/_template/`.

## Portable roots and resolution

`<GAME_REPO>` is an active-call absolute Git root. `<GAMEPLAY_ROOT>` is the
fixed `<GAME_REPO>/design/gameplay`. Neither absolute path is stored in filled
answers. Versioned paths are relative to the game repo.

Resolve in this order:

1. explicit game-repo path in the invocation;
2. current working directory's Git root;
3. ignored `gameplay/adapters/registry.local.md`, only for an explicit
   project id.

Then read all three files at the fixed adapter location. Reject a game root
inside this factory. Never scan siblings, borrow another factory's registry,
infer a game from engine code, or commit developer paths.

A missing file, `TBD`, inconsistent version, missing referenced file, or
undeclared capability produces `BLOCKED_BY_ADAPTER`. A required acceptance
kernel that the Observation Adapter cannot support produces
`BLOCKED_BY_OBSERVABILITY` before packet production.

## Project Gameplay Profile answers

The profile declares:

- project id and authoritative story/current-state sources;
- primary locale, game mode/platform assumptions, and target player frames;
- core fantasy/player desires and gameplay sovereignty/red lines;
- implemented or production-approved verbs and their preconditions/results;
- systems, spaces, engagement/decision/challenge generators, and
  failure/retry conventions;
- presentation modes, control ownership, camera/HUD/feedback capabilities;
- gameplay grammar/rhythm/repetition/expectation/handoff conventions;
- explicit time, complexity, content, asset, sound, engineering, and
  attention budgets;
- approval owner, USER-ruling evidence, and human playtest evidence.

Project-specific verbs, modes, budgets, or commercial/fantasy rulings in
factory core are defects.

## Production Adapter answers

The production adapter declares:

- target runtime files/schemas and id/reference/order grammar;
- exact mappings for triggers, actions, control, camera, presentation, HUD,
  objectives, state transitions, feedback, failure/recovery, and handoff;
- how runtime/world deltas are asserted and validated;
- asset, sound, story, localization, and code integration surfaces while
  preserving Beat Sheet/beat/packet provenance;
- exact integrity, build, launch, headless, screenshot, and playtest commands;
- instrumentation landing surfaces shared with the Observation Adapter;
- unsupported capabilities and escalation owner.

Implementation must land gameplay and required instrumentation together.
Mechanical tests can prove state/reference behavior but not player reception.

## Observation Adapter answers

The observation adapter declares:

- instrumentation enablement, source log/capture schemas and paths;
- build/session/save/checkpoint/seed/locale/input/platform/viewport provenance;
- raw input versus resolved action, control, camera, HUD/modal, presentation,
  state before/delta/after, feedback/reward, audio/VFX, spatial, timing, and
  capture mappings;
- append-only order, monotonic clock, frame/sequence, and correlation rules;
- reproducible `LIVE_BLIND_RUN`, `RECORDED_RUN`,
  `CONTROLLED_BRANCH_PROBE`, and `STATIC_RUNTIME_ASSERTION` procedures;
- machine-readable normalization mapping or equivalent adapter tool;
- machine-readable exact-span boundary, control, presentation, traversal,
  non-gameplay activity, and acceptance-kernel measurement selectors used by
  the Quantitative Experience Budget gate;
- public observable versus hidden/private provenance fields;
- blind redaction and capture rules;
- observability matrix and explicit `NOT_OBSERVABLE` gaps;
- reader/integrity commands and evidence destinations.

Raw evidence and blind payloads never contain design intent, semantic
sheet/beat ids, canonical expected action, future data, or mental/evaluative
claims.

## State partitions

- runtime/world sources remain authoritative execution state;
- Span Quant Sheets, Beat Sheets, walkthroughs, packets, and plans are
  authority/decision state;
- grammar/experience lessons are derived design state;
- raw evidence is append-only observation state;
- canonical timelines are derived observable state;
- blind reports/acceptance are interpretation/QA state.

No persisted object silently serves more than one role.

## Canonical game-owned layout

```text
design/gameplay/
  adapter/
    PROJECT_GAMEPLAY_PROFILE.md
    PRODUCTION_ADAPTER.md
    OBSERVATION_ADAPTER.md
  span_quants/<span_id>.md
  experience_beat_sheets/<sheet_id>.md
  experience_beat_sheets/<sheet_id>_QUANTITATIVE_EXPERIENCE_BUDGET.json
  walkthroughs/<trace_id>/
    PLAYABLE_WALKTHROUGH_TRACE.md
    PAPER_BLIND_INPUT.md
    PAPER_BLIND_REPORT.md
  beat_packets/<packet_id>.md
  observation_plans/<packet_or_span_id>.md
  runtime_evidence/<run_id>/
    RAW_MANIFEST.json
    <project-native logs and captures>
    CANONICAL_EVENT_STREAM.json
    OBSERVED_GAMEPLAY_TRACE.json
    OBSERVED_GAMEPLAY_TRACE.md
    RUNTIME_BLIND_INPUT.json
    RUNTIME_BLIND_REPORT.md
    INTEGRITY_REPORT.json
    EXPERIENCE_BUDGET_RESULT.json
  qa/
    <span_id>_QUANT_REVIEW.md
    <span_id>_DESIGN_REVIEW.md
    <span_id>_REALIZATION_REVIEW.md
    <span_id>_PACKET_REVIEW.md
    <span_id>_LANDING_REVIEW.md
    <span_id>_RUNTIME_ACCEPTANCE.md
  state/
    GAMEPLAY_GRAMMAR_STATE.md
    EXPERIENCE_LESSONS.md
```

## Story/gameplay/production boundary

- Story owns canon, causality, character meaning, approved prose, and story
  anchors/staging constraints.
- Gameplay owns the approved experience curve and concrete player work,
  continuous player time, control/action/reception contracts, observation
  requirements, readback, and conformance acceptance.
- Production owns implementation through declared capabilities and returns
  runtime plus evidence.
- Asset/sound factories receive provenance-preserving orders; no gameplay core
  hard-coupling is allowed.

Conflicts never silently override authority. Route the first blocked/lost
transformation to story, experience design, realization, production,
presentation/reception, or observation.

## Onboarding

Only an explicit onboarding request may create game-owned adapter/state paths.
Seed the three blank adapter sheets plus the grammar/experience blank states;
never overwrite existing files. Ordinary production calls fail closed rather
than generating missing answers. No factory document preselects a pilot game.
