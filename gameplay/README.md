# Gameplay Factory

Gameplay Factory is currently calibrating a compact **Case 3** creative front
end: continue a factory-readable game repo by resolving its primary progression
driver and next objective, mechanically compiling the implemented player
actions/rewards, authoring the whole objective gameplay in one pass, and
compiling it into persistent model-independent production plans.

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
prepare.py                             Step 1 context validator/compiler
plan.py                                Step 3 production-plan validator
schemas/next_gameplay_unit_input.schema.json
schemas/gameplay_design_model.schema.json
schemas/production_plan_manifest.schema.json
templates/GAMEPLAY_DESIGN_MODEL.json
templates/NEXT_GAMEPLAY_UNIT_INPUT.json
templates/OBJECTIVE_GAMEPLAY.md
templates/PRODUCTION_PLAN_MANIFEST.json
templates/PRODUCTION_PLAN.md
reader.py                              runtime evidence reference tool
tests/                                 preparation + planning + reader tests
docs/*_CONTRACT.md                     current and previous-pilot contracts
```

Factory-side files are project-agnostic. Filled inputs, contexts, objective
gameplay, implementation artifacts, and evidence always land in the game repo.
