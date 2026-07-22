# AI Caller Landing — gameplay_factory

You are an AI agent extending and producing a concrete game's gameplay. Runtime
evidence checking remains an independently invoked capability. The current
creative pilot is limited to **Case 3**: a game repo already
produced/onboarded by Gameplay Factory and therefore safe to continue from
game-owned state.

## Start here

1. Read `docs/CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md`.
2. Resolve the target game repo: explicit path -> current Git root -> ignored
   local registry for an explicit project id. Never scan sibling repos.
3. Set `<GAMEPLAY_ROOT>` to `<GAME_REPO>/design/gameplay`; reject any output
   inside this factory or outside the game repo.
4. Confirm the repo is Case 3. Blank projects belong to a future idea factory;
   foreign repos missing factory-readable progression/action state belong to a
   future onboarding/refactoring flow. Do not disguise either as gameplay
   authoring.
5. Run the script-first Step 1 material gate, then use its compact result for
   one Step 2 creative pass. After `OBJECTIVE_GAMEPLAY.md` is stable, use any
   user-selected planning model/protocol to write the persistent Step 3
   manifest plus production plan files. When validation returns
   `READY_FOR_EXECUTION`, immediately perform Step 4 by executing those plans;
   do not wait for the user to say "write the code". Stop at planning only when
   the user explicitly requests plan-only output. Do not run the legacy
   quant/Beat Sheet/walkthrough tower automatically.
6. `reader.py` remains a runtime-evidence tool. It does not prepare creative
   context, invent gameplay, or issue an experience verdict.

## Current Case 3 creative loop

```text
stable GAMEPLAY_DESIGN_MODEL.json + small objective frontier input
  -> prepare.py context
  -> NEXT_GAMEPLAY_UNIT_CONTEXT.md
  -> one creative author
  -> OBJECTIVE_GAMEPLAY.md
  -> user-selected production planner
  -> PRODUCTION_PLAN_MANIFEST.json + production_plans/*.md
  -> plan.py validate
  -> original caller executes dependency-ready plans
  -> normal code/data/asset/sound production checks
```

The stable project model records the primary progression driver and implemented
player actions/rewards once; do not copy that vocabulary into every objective.
Step 1 determines the current production
frontier, whether to complete the active unit or advance one unit, the next
player-facing objective, and the implemented player actions plus their rewards.
Locales are an index, never implementation proof: runtime selection and
completion wiring must also exist.

Step 2 authors the whole gameplay between objective issue/current frontier and
objective completion. `objective -> necessary player action` is an internal
micro-deduction, not a separate worker, file, or review. The same pass expands
thin actions through problems, activities, pressure, player desires, existing
actions/rewards, and meaningful decisions until the objective is complete.

Step 3 is model-independent at the artifact boundary. A Plan Mode model and an
ordinary author model must produce the same game-owned manifest and durable
Markdown plans. The factory user chooses the model; downstream execution reads
the files, never private chat/Plan Mode state. Split `N` by coherent file/state
ownership and independent verification boundaries, not by table row count.

Step 4 is an automatic control handoff, not another design/review artifact. The
original caller remains responsible for the user's end-to-end request: it
selects dependency-ready plans, performs ordinary repo production, and invokes
the asset, story, sound, or other factory only when a plan requires it. A
planner-only model hands the persisted paths back to its outer orchestrator,
which chooses an execution-capable model without asking the user to repeat the
gameplay request.

## Hard rules

- **Primary progression first.** The main quest/mission, level sequence,
  spatial point-of-interest frontier, or equivalent driver answers what the
  player does next. It need not branch and is not itself the gameplay choice.
- **What and how stay separate.** The progression driver supplies the next
  objective; gameplay is how the player reaches it through actions and their
  consequences/rewards.
- **Script before creative tokens.** Do not ask a creative worker to rediscover
  repo progression, scan all locales/code, or rebuild the action/reward list.
  `prepare.py context` must return `READY_FOR_HOW_DESIGN` or
  `READY_FOR_NEW_GAMEPLAY_DESIGN` first.
- **Stable vocabulary is written once.** Keep progression-driver and
  action/reward evidence in
  `<GAMEPLAY_ROOT>/adapter/GAMEPLAY_DESIGN_MODEL.json`; each objective input
  names only its frontier and applicable action ids.
- **Locale text is not code.** A locale key counts only when the Step 1 input
  also proves runtime objective selection and completion wiring.
- **Missing action coverage is not missing material.** Complete objective
  evidence plus no applicable implemented action returns
  `READY_FOR_NEW_GAMEPLAY_DESIGN`; it is a candidate trigger to add gameplay.
  Missing or unverifiable source material returns `BLOCKED_BY_MATERIAL`.
- **One useful creative artifact.** Step 2 emits one complete
  `OBJECTIVE_GAMEPLAY.md`; never spend separate workers on necessary-action,
  thinness, problem, pressure, desire, opportunity, or choice micro-steps.
- **Planning mode is selectable; planning files are mandatory.** The factory
  never requires Plan Mode or a named model. Every planner persists one
  `PRODUCTION_PLAN_MANIFEST.json` and `N` production plan Markdown files using
  the same contract before execution begins.
- **Plans compile; they do not redesign.** Production planning maps objective
  rows to reuse, implementation, existing-behavior verification, or explicit
  no-change. A real design gap returns `BLOCKED_BY_PLAN_GAP`; it does not start
  another full design/review tower or silently invent replacement gameplay.
- **Plan ownership is non-overlapping.** Split work by coherent change unit.
  Every objective row has exactly one coverage entry; shared planned paths
  across plan files are invalid because they hide executor conflicts.
- **Bind production to exact design authority.** The manifest and every plan
  record the source `OBJECTIVE_GAMEPLAY.md` SHA-256. Any source change makes
  the plans stale until regenerated or intentionally revised.
- **`READY_FOR_EXECUTION` is not user-facing completion.** For an ordinary
  request to create/extend gameplay, never stop after writing or validating
  plans. Continue through their standard production work in dependency order.
  Planning-only is opt-in, not the default.
- **Step 4 adds no Factory review gate.** Run the normal tests/build/asset
  validation required by production, then report the implemented result. Do
  not regenerate design artifacts or automatically invoke runtime acceptance.
- **New gameplay is allowed, but escalates minimally.** Reconfigure an existing
  situation, combine existing actions, or add a target/consequence before
  adding a new action or whole system. Add gameplay when the required activity
  is trivial, cannot express the objective, or becomes deterministic/repetitive
  before completion.
- **Rewards need not be punishment or permanent branching.** Local consequences
  may be positive information, access, power, items, relationships, expression,
  mastery, or objective progress. A linear main progression remains valid.
- **Do not make a reward checklist look like choice.** If every opportunity can
  be cleared without judgment and order has no effect on later play, it is
  content inventory, not a meaningful decision.
- **Non-gameplay does not self-promote.** Teleporter input, dialogue advance,
  raw inputs, straight locomotion, objective arrival, passive state change,
  control return, or presentation do not independently count as gameplay.
- **Game-owned state is authority.** Core never invents project verbs, runtime
  hooks, objective keys, rewards, or source paths. A Step 2 author may propose
  new gameplay only after Step 1 exposes the existing vocabulary and gap.
- **Artifacts land in the game repo.** Factory owns contracts, schemas, tools,
  tests, and blank templates only.
- **Ownership precedes writes.** Resolve and validate every input/output path
  before creating a directory or file.
- **Paths stay portable.** Persist game-repo-relative paths; absolute paths are
  active-run values only.

## Runtime evidence invariants (unchanged)

- Instrumentation ships with later gameplay production; missing evidence paths
  fail closed before a conformance claim.
- Raw events, derived timelines, blind interpretations, and acceptance
  comparisons remain separate artifacts.
- Runtime blind input contains no design semantics, hidden/future state, code,
  canonical action, or available-action enumeration.
- One golden path cannot prove alternatives or failure adjustment. Controlled
  branches must have complete independent evidence chains.
- Factory conformance is not a claim that gameplay is fun, and remains separate
  from human playtest acceptance.

## Current contracts

- `docs/CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md`
- `schemas/next_gameplay_unit_input.schema.json`
- `schemas/gameplay_design_model.schema.json`
- `templates/GAMEPLAY_DESIGN_MODEL.json`
- `templates/NEXT_GAMEPLAY_UNIT_INPUT.json`
- `templates/OBJECTIVE_GAMEPLAY.md`
- `schemas/production_plan_manifest.schema.json`
- `templates/PRODUCTION_PLAN_MANIFEST.json`
- `templates/PRODUCTION_PLAN.md`
- `plan.py`
- `docs/RUNTIME_OBSERVATION_AND_ACCEPTANCE_CONTRACT.md`
- `docs/PROJECT_ADAPTER_CONTRACT.md`
- `docs/OBSERVATION_READER.md`

The Span Quant / Gameplay Experience Beat Sheet / walkthrough / packet
contracts remain in the repo as the previous pilot lineage and for existing
artifacts. They are not the default Case 3 creative entry while this compact
objective workflow is being measured on real projects.
