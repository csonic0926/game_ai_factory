# AI caller landing — gameplay_factory

Use this factory to continue a factory-readable game's primary progression,
author the complete gameplay for one objective, later make production
observable, and compare actual runtime experience with locked design authority.

The current Case 3 creative entry is
[`CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md`](CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md):
script-first material preparation followed by one complete
`OBJECTIVE_GAMEPLAY.md`, then persistent production plans compiled by the
user's selected planning model. The older quant/Beat Sheet/walkthrough loop
below is retained for existing pilot lineages and is **not** automatically run
for new Case 3 work. `../reader.py` is a runtime evidence tool, not a creative
step machine or acceptance oracle.

## Invocation

Identify the operation and target game repo:

```text
factory: <FACTORY_REPO>/gameplay
operation: produce_objective | prepare_objective | author_objective | plan_production |
           legacy_quantify_span | realize_walkthrough | compile_packets | landing_review |
           observe_runtime | runtime_acceptance
game_repo: <explicit path, or CURRENT_GIT_ROOT>
project_id: <only for optional registry.local.md lookup>
span/sheet/run: <operation-specific id>
```

## Resolve ownership before reading/writing

Resolve `<GAME_REPO>` from explicit path -> current Git root -> ignored local
registry for an explicit project id. Set `<GAMEPLAY_ROOT>` to
`<GAME_REPO>/design/gameplay`. Reject a root inside this factory, any output
outside the game repo, sibling scanning, inferred projects, and committed
absolute developer paths.

Read `GAMEPLAY_DESIGN_MODEL.json`, `PROJECT_GAMEPLAY_PROFILE.md`,
`PRODUCTION_ADAPTER.md`, and `OBSERVATION_ADAPTER.md` at
`<GAMEPLAY_ROOT>/adapter/`. An ordinary production call never creates missing
answers. Missing/blank/inconsistent answers mean `BLOCKED_BY_ADAPTER`.

## Explicit onboarding only

Create only missing paths/files; never overwrite:

```text
<GAMEPLAY_ROOT>/adapter/PROJECT_GAMEPLAY_PROFILE.md
<GAMEPLAY_ROOT>/adapter/PRODUCTION_ADAPTER.md
<GAMEPLAY_ROOT>/adapter/OBSERVATION_ADAPTER.md
<GAMEPLAY_ROOT>/adapter/GAMEPLAY_DESIGN_MODEL.json
<GAMEPLAY_ROOT>/state/GAMEPLAY_GRAMMAR_STATE.md
<GAMEPLAY_ROOT>/state/EXPERIENCE_LESSONS.md
```

Seed from `../adapters/_template/` and `../templates/`. Create other artifact
directories only when their first real game-owned artifact is produced.

## Current Case 3 creative preconditions

- the repo is already factory-produced/onboarded rather than blank or foreign;
- its primary progression driver and production frontier can be evidenced;
- the current/next objective has locale text plus runtime selection and
  completion wiring;
- implemented player actions and their rewards can be evidenced, or their
  absence can be proven as a legitimate new-gameplay trigger.

Run Step 1:

```bash
python3 gameplay/prepare.py context \
  --game-repo <GAME_REPO> \
  --input design/gameplay/objective_gameplay/<objective_id>/NEXT_GAMEPLAY_UNIT_INPUT.json \
  --out design/gameplay/objective_gameplay/<objective_id>/NEXT_GAMEPLAY_UNIT_CONTEXT.md
```

Only `READY_FOR_HOW_DESIGN` or `READY_FOR_NEW_GAMEPLAY_DESIGN` starts Step 2.
One creative worker then writes the whole
`design/gameplay/objective_gameplay/<objective_id>/OBJECTIVE_GAMEPLAY.md`.
Do not split its internal necessary-action/problem/pressure/desire/choice
deductions into separate workers.

Then use either Plan Mode or an ordinary model chosen by the factory user to
inspect the repo and persist:

```text
design/gameplay/objective_gameplay/<objective_id>/
  PRODUCTION_PLAN_MANIFEST.json
  production_plans/<plan_id>_<change_unit>.md
```

Both planning protocols use the same schema/templates and must leave no
required production knowledge only in chat/session state. Split plans by
coherent code/data/state ownership and independent verification boundary, not
one plan per objective row. Validate before execution:

```bash
python3 gameplay/plan.py validate \
  --game-repo <GAME_REPO> \
  --manifest design/gameplay/objective_gameplay/<objective_id>/PRODUCTION_PLAN_MANIFEST.json
```

Only `READY_FOR_EXECUTION` begins production. `BLOCKED_BY_PLAN_GAP` routes the
specific contradiction or missing design decision back to Step 2; it does not
authorize the production planner to invent replacement gameplay.

`produce_objective` is the default interpretation of a natural-language request
to make, add, continue, or improve gameplay. `READY_FOR_EXECUTION` is therefore
an intermediate phase result: the original caller must immediately execute the
dependency-ready plans using ordinary repo production and other factories as
needed. Do not return a plan-only answer or wait for a second "write the code"
prompt unless the user explicitly selected `plan_production`, said plan-only,
or prohibited implementation. A planner-only model returns control and the
persisted paths to its outer orchestrator, which must continue with an
execution-capable model when available.

## Previous pilot preconditions (existing lineages only)

- exact story anchors and causal constraints;
- exact current runtime/world/player-knowledge state;
- three complete adapter answers;
- current grammar/experience derived state;
- a recognizable start/end gameplay span;
- an approved Span Quant Sheet (span boundaries, cadence contract,
  implementation-blind playable-content inventory, derived floors) before any
  Beat Sheet authoring;
- a sheet-level exact-span Quantitative Experience Budget restating the
  approved quant floors, with its game-owned machine-readable selector
  projection;
- an Observation Adapter evidence path for any acceptance claim.

Do not infer verbs, budgets, engine hooks, events, camera/HUD behavior, or
capture capability from code and silently convert inference into authority.

## Previous pilot production loop (not the default Case 3 creative entry)

### 1. Quantify the span — demand before supply

Use `../modules/span-quant/` and `../templates/SPAN_QUANT_SHEET.md`. In
order: fix the span's recognizable start/end situations and observable
boundary requirements (step 0); adopt the factory canonical cadence — one
new meaningful choice every 3–5 seconds, max arrival gap 5000 ms — unless
the game repo's Gameplay Profile records an explicit USER-ruled override
(step 1); then, implementation-blind, declare the desire line and inventory
the generators and one-shots that can hold that beat, from player
expectation for the genre/situation/cadence (step 2). Walk the course for
cadence sustainability, check the chain rule (each consequence delivers the
next choice's hints), and derive the legacy budget floors arithmetically.

The unit is a meaningful choice (information -> guess -> commitment ->
consequence -> later-emotion influence); a certain-outcome click never
enters the inventory. Do not read game code or count existing content to
decide sufficiency — supply defining demand is the dead loop that passes
six-click spans. Save to `<GAMEPLAY_ROOT>/span_quants/<span_id>.md`.

Run a fresh file-only quant review using `../templates/QUANT_REVIEW.md`. The
reviewer challenges every unit's guess, emotion mechanism, missed-hint
fallback, and dwell/arrival claims, verifies the beat holds across the whole
course without inflation or padding, edits nothing, and writes
`PASS_QUANT_REVIEW`/`FAIL_QUANT_REVIEW` under `qa/`. Only
`PASS_QUANT_REVIEW` may proceed to Beat Sheet authoring.

### 2. Author the Gameplay Experience Beat Sheet to satisfy the quant

Use `GAMEPLAY_EXPERIENCE_BEAT_SHEET_CONTRACT.md`,
`../modules/experience-beat-sheet/`, and the blank template. The sheet is the
highest semantic authority and contains concrete situations, player purpose,
mode-complete work/agency/challenge/payoff, commitment, observable response,
intended change, carry-forward, failure/recovery, curve/red lines, and an
acceptance kernel per beat. The sheet binds the approved Span Quant Sheet
path/version/checksum, and its Quantitative Experience Budget restates the
approved quant floors — exact observable runtime start/end boundaries,
first-play target/min/max duration (optional replay target), minimum control
ratio, maximum presentation/traversal-only gaps, and minimum/maximum
content/narrative counts and narrative time. The sheet may tighten a floor
but never loosen one without a new quant version.

Save to `<GAMEPLAY_ROOT>/experience_beat_sheets/<sheet_id>.md`. USER rulings
and AI assumptions remain separate. Auto/headless work is
`AI_DRAFT_FOR_REVIEW`, never USER-approved by implication.
Save its exact-bound machine-readable projection beside it using
`../templates/QUANTITATIVE_EXPERIENCE_BUDGET.json` and
`../schemas/experience_budget.schema.json`. Do not put a run id or session id
in this authority artifact; runtime ownership is supplied to the measurement
invocation.

Run a fresh file-only design review. The reviewer audits supply against the
quant demand — every content-count floor names its supplying beats, the beat
flow holds the cadence with no stretch past the max arrival gap, and every
carry-forward delivers the next choice's hints — edits nothing, and writes
`PASS_DESIGN_REVIEW`/`FAIL_DESIGN_REVIEW` under `qa/`.

### 3. Preflight adapters and observability

Bind the exact sheet version/checksum and read current state/three adapters.
For every acceptance kernel, identify cue, attempt, response, carry-forward,
captures, timing, and required live/recorded/branch/static evidence modes. If
any required chain is missing, stop `BLOCKED_BY_OBSERVABILITY` before
production.

### 4. Realize one continuous Intended Player walkthrough

Use `PLAYABLE_WALKTHROUGH_TRACE_CONTRACT.md` and its template. Roll out the
whole span in player time before segmenting. Keep observables, hidden design,
runtime/world/knowledge/grammar/allocation/external state distinct. Preserve
the Beat Sheet's engagement completeness, curve, red lines, and causal
carry-forward.

Run a fresh realization review. Then optionally run the paper-stage blind
prefilter by revealing only one design-authored `visible_and_known` value at a
time. Its PASS is `PASS_PAPER_PREFILTER`, not runtime evidence.

### 4.5 Run the quantitative sufficiency gate before packet compilation

Use the exact first-play observed timeline plus any required controlled branch
timelines, the acceptance kernels, and the sheet-bound budget:

```bash
python3 gameplay/reader.py measure-budget \
  --game-repo <GAME_REPO> \
  --run-id <FIRST_PLAY_RUN_ID> \
  --session-id <FIRST_PLAY_SESSION_ID> \
  --timeline <FIRST_PLAY_OBSERVED_GAMEPLAY_TRACE.json> \
  --timeline <CONTROLLED_BRANCH_TRACE_IF_REQUIRED.json> \
  --kernels <ACCEPTANCE_KERNELS.json> \
  --budget <QUANTITATIVE_EXPERIENCE_BUDGET.json> \
  --out <EXPERIENCE_BUDGET_RESULT.json>
```

Only `PASS_EXPERIENCE_BUDGET` may proceed to packet compilation. A result of
`FAIL_EXPERIENCE_BUDGET`, `NO_GAMEPLAY`, or `INCONCLUSIVE_EVIDENCE` blocks the
span. Pressing a teleporter, advancing dialogue, raw input counts, straight
locomotion, reaching an objective trigger, passive state change, control
return, movement, and arrival do not independently count as gameplay. Never
call a blocked/under-budget span a gameplay segment. One evidence chain may
fill at most one decision/combat/world-interaction quota, and presentation
overlap is removed from effective player-control time.

### 5. Compile production packets and observation plans

Segment only the approved full trace with its exact-span
`PASS_EXPERIENCE_BUDGET` result. Each packet contains experience,
player-action, runtime, and observation contracts; it binds the exact Beat
Sheet/trace/kernel versions. Instrumentation is part of the same job as
gameplay implementation. Fresh packet review returns PASS/FAIL without edits.

### 6. Production landing and fresh landing review

The caller implements game code/data plus instrumentation through the
Production/Observation Adapters. Story/asset/sound orders retain
sheet/beat/packet provenance. A fresh landing reviewer checks both runtime and
instrumentation mappings, not only happy-path deltas. Missing logging/capture
hooks prevents production-complete status.

### 7. Run the actual build and read evidence

Produce game-owned raw logs/captures with build, content, save/checkpoint,
seed, locale, input/platform/viewport, session, and evidence-mode provenance.
Use `OBSERVATION_READER.md` to validate, normalize, reconstruct, and build the
runtime blind input. Missing refs, bad order, mixed provenance, or forbidden
interpretation fields produce `INCONCLUSIVE_EVIDENCE`.

Run at least the modes required by the kernels. One recorded golden path
cannot prove alternatives or failure adjustment.

Re-run `measure-budget` against the production build's fresh exact-span
evidence. Only its `PASS_EXPERIENCE_BUDGET` result can enter runtime
acceptance; a pre-packet result never substitutes for fresh production
evidence.

### 8. Fresh blinded runtime reading

A fresh player/reader sees only actual sequential observations, one reveal at
a time. It records purpose, attempted action, alternatives, expected response,
confidence, misread, and model update. It sees no design/implementation/future
material. Save the separate report; never write interpretation into raw or
derived timeline state.

### 9. Fresh runtime acceptance

Only now may a fresh acceptance reviewer read both locked authority and
observation chains. It compares each kernel, allowed drift, curve/control/
presentation order, the fresh `PASS_EXPERIENCE_BUDGET` result, and red lines;
points to actual evidence; identifies the
first lost transformation; edits nothing; and emits exactly one factory
verdict:

```text
PASS_FACTORY_CONFORMANCE
FAIL_IMPLEMENTATION_FIDELITY
FAIL_RECEPTION
FAIL_DESIGN
BLOCKED_BY_ADAPTER
BLOCKED_BY_OBSERVABILITY
INCONCLUSIVE_EVIDENCE
```

A pass separately records `PENDING_HUMAN_PLAYTEST` unless humans have actually
accepted it. Factory conformance does not claim fun or universal emotion.

## Canonical game-owned outputs

See `PROJECT_ADAPTER_CONTRACT.md` for the complete layout. The three lineages
must remain separate and traceable:

```text
Authority: Span Quant Sheet -> Beat Sheet -> walkthrough -> packets/observation plans
Observation: actual build -> raw/captures -> canonical timeline -> blind report
Acceptance: locked authority + observed evidence -> verdict + failure route
```

## Pilot/automation boundary

Do not hard-code a creative step machine or claim factory completion from
contracts/tests alone. A real project span must close the full loop, a
deliberate implementation/reception mismatch must be rejected, and a second
different gameplay shape must prove portability before creative automation is
stabilized.
