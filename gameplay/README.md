# Gameplay Factory

Gameplay Factory has two compact **Case 3** production paths for an already
factory-readable game repo. The canonical caller entry and router is
[`AGENTS.md`](AGENTS.md).

**Progression production** makes/completes the primary progression's next unit:

```text
stable game-owned progression/action model + objective frontier
  -> prepare.py context                         # Step 1, mechanical
  -> NEXT_GAMEPLAY_UNIT_CONTEXT.md
  -> one creative author                       # Step 2
  -> OBJECTIVE_GAMEPLAY.md
  -> user-selected planner                     # Step 3
  -> PRODUCTION_PLAN_MANIFEST.json + production_plans/*.md
  -> plan.py validate
  -> original caller executes plans            # Step 4, automatic
```

**Gap repair** closes one evidenced player-visible break inside an existing
objective without regenerating it:

```text
exact existing OBJECTIVE_GAMEPLAY.md + one evidenced gap
  -> repair.py context
  -> GAMEPLAY_REPAIR_CONTEXT.md
  -> direct planning when authority already exists
     OR one bounded author -> GAMEPLAY_REPAIR.md
  -> user-selected repair planner
  -> REPAIR_PLAN_MANIFEST.json + production_plans/*.md
  -> repair_plan.py validate
  -> original caller executes repair plans
```

When both a concrete known gap and forward progression are active, repair the
gap first unless the user explicitly defers it.

The previous quant-first chain remains present for existing pilot artifacts:

```text
Span Quant -> Gameplay Experience Beat Sheet -> walkthrough -> packets
```

It is not automatically run for new Case 3 objective design while the compact
format is measured on real repos. Runtime evidence validation and blinded
acceptance remain separate downstream concerns.

## Case boundary

- **Case 1:** blank/genre-only request — future idea factory.
- **Case 2:** non-factory repo — future onboarding/refactoring flow.
- **Case 3:** factory-produced/onboarded repo with readable progression and
  action/reward state — current supported creative workflow.

## Step 1

`GAMEPLAY_DESIGN_MODEL.json` stores the primary progression driver and
action/reward vocabulary once. `prepare.py context` merges it with a small
per-objective frontier input, then verifies game-repo ownership, progression evidence,
locale text plus runtime wiring, the current/next objective, completion state,
and player actions with rewards. It emits:

- `READY_FOR_HOW_DESIGN`
- `READY_FOR_NEW_GAMEPLAY_DESIGN`
- `BLOCKED_BY_MATERIAL`

It never treats locale-only text as implemented gameplay and never creates an
output directory before ownership validation.

## Step 2

One author uses the compact Step 1 result to produce one complete
`OBJECTIVE_GAMEPLAY.md`. Necessary-action, problem, pressure, player-desire,
action/reward, and meaningful-choice deductions occur inside that pass rather
than becoming separate workers and review artifacts.

## Step 3

The factory user may choose a Plan Mode model or an ordinary model. Both must
write the same persistent game-owned contract: one
`PRODUCTION_PLAN_MANIFEST.json` plus `N` Markdown plans split by coherent
change/file/state ownership. `plan.py validate` binds them to the exact
`OBJECTIVE_GAMEPLAY.md` SHA-256, requires coverage for every numbered row,
checks dependencies and portable repo paths, and rejects shared planned-file
ownership. The plans compile design into production requirements; they may
return `BLOCKED_BY_PLAN_GAP` but may not redesign gameplay silently.

## Step 4

`READY_FOR_EXECUTION` is an intermediate control signal, not a final answer to
an ordinary "make gameplay" request. The original caller automatically
executes dependency-ready plans with normal coding/data work and invokes asset,
story, or sound factories when the plan requires them. Only an explicit
plan-only request stops after Step 3. Step 4 adds no Gameplay Factory reviewer;
normal production tests and validation remain part of the implementation work.

See [`docs/CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md`](docs/CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md).

## Gap repair

`repair.py context` binds an exact existing objective id/path/SHA and affected
rows to one concrete gap, exact runtime/implementation/test evidence, and only
the affected actions from the stable project model. It emits:

- `READY_FOR_DIRECT_REPAIR_PLAN`
- `READY_FOR_REPAIR_DESIGN`
- `BLOCKED_BY_REPAIR_MATERIAL`

Explicit existing requirements and persisted user rulings skip creative
authoring. Missing/ambiguous design gets one compact `GAMEPLAY_REPAIR.md`; the
base `OBJECTIVE_GAMEPLAY.md` remains unchanged.

`repair_plan.py validate` binds every repair plan to both the exact base
objective and exact repair source SHA-256, requires coverage for every repair
row, and enforces dependencies, portable ownership, and non-overlapping
planned paths. `READY_FOR_EXECUTION` automatically returns to production.
Tests prove implementation behavior but do not self-award final experiential
closure. Gap inputs persist routing state: `OPEN` enters repair,
`IMPLEMENTED_PENDING_ACCEPTANCE` waits for the named closure authority, and
only that user/fresh reviewer may mark `CLOSED`; `DEFERRED` requires a user
decision.

See
[`docs/CASE3_GAMEPLAY_REPAIR_WORKFLOW.md`](docs/CASE3_GAMEPLAY_REPAIR_WORKFLOW.md).

## Runtime evidence tooling

`reader.py` remains the dependency-free evidence tool. It validates raw
evidence, normalizes project mappings, reconstructs timelines, produces
runtime-blind inputs, prepares same-run causal evidence chains, and measures
declared budgets. It does not create gameplay or claim that an experience is
fun.

## Layout

```text
AGENTS.md                              hard caller rules
docs/CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md
docs/CASE3_GAMEPLAY_REPAIR_WORKFLOW.md
prepare.py                             Step 1 context validator/compiler
plan.py                                Step 3 production-plan validator
repair.py                              repair context validator/compiler
repair_plan.py                         repair production-plan validator
schemas/next_gameplay_unit_input.schema.json
schemas/gameplay_design_model.schema.json
schemas/production_plan_manifest.schema.json
schemas/gameplay_gap_input.schema.json
schemas/repair_plan_manifest.schema.json
templates/GAMEPLAY_DESIGN_MODEL.json
templates/NEXT_GAMEPLAY_UNIT_INPUT.json
templates/OBJECTIVE_GAMEPLAY.md
templates/PRODUCTION_PLAN_MANIFEST.json
templates/PRODUCTION_PLAN.md
templates/GAMEPLAY_GAP_INPUT.json
templates/GAMEPLAY_REPAIR.md
templates/REPAIR_PLAN_MANIFEST.json
templates/REPAIR_PRODUCTION_PLAN.md
reader.py                              runtime evidence reference tool
tests/                                 preparation + planning + reader tests
docs/*_CONTRACT.md                     current and previous-pilot contracts
```

Factory-side files are project-agnostic. Filled inputs, contexts, objective
gameplay, implementation artifacts, and evidence always land in the game repo.
