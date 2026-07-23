# Case 3 objective-gameplay workflow

This is the **progression-production** workflow: it makes or completes the
primary progression's next unit. A concrete gameplay gap inside an existing
unit belongs to
[`CASE3_GAMEPLAY_REPAIR_WORKFLOW.md`](CASE3_GAMEPLAY_REPAIR_WORKFLOW.md)
instead. If both are active, repair the known gap first unless the user
explicitly defers it.

This is the current token-efficiency pilot for a game repo that Gameplay
Factory can already continue. It replaces repeated repo study and the previous
multi-author design front end with one mechanical context compilation, one
complete creative artifact, and one persistent production-planning contract.

It does not onboard a blank or foreign repo and does not change the independent
runtime evidence reader. It also does not rewrite an already-authored objective
merely to close one local runtime/design omission.

## Case boundary

| Case | Meaning | Route |
| --- | --- | --- |
| 1 | Blank project or only a genre request | Future idea/brainstorm factory; not this workflow |
| 2 | Existing repo without factory-readable design/progression state | Future onboarding/refactoring flow |
| 3 | Factory-produced/onboarded repo with trustworthy state and adapters | This workflow |

If the primary progression driver, objective source, or action/reward source
cannot be established, the repo is not ready for Case 3 authoring.

If the requested work instead names a concrete player-visible causal break
inside an existing `OBJECTIVE_GAMEPLAY.md`, the repo may still be Case 3 but
the operation is `repair_gameplay_gap`, not `produce_objective`.

## Object model

The primary progression driver is the outer state transition:

```text
progression unit N -> completion -> progression unit N+1
```

It may be a linear mission chain, stage sequence, scenario sequence without a
level menu, or a spatial next-point-of-interest frontier. It answers **what is
next**; it need not branch and is not itself the meaningful choice.

Gameplay is the inner path:

```text
next objective
  -> player actions and their rewards/consequences
  -> concrete problems, activities, pressure, desires, and decisions
  -> objective completion
```

## Step 1 — prepare the next gameplay unit

Step 1 is script-first and non-creative. A stable game-owned
`<GAMEPLAY_ROOT>/adapter/GAMEPLAY_DESIGN_MODEL.json` records once:

- the primary progression driver and exact repo evidence;
- implemented player actions and their rewards/consequences;
- project-wide recent patterns and constraints.

A small per-objective input then declares:

- whether the factory must complete the active unit or advance one unit;
- the player-facing objective locale key and expected text;
- runtime objective-selection and completion evidence;
- whether the post-completion successor is wired;
- applicable action ids selected from the stable model;
- objective-local recent patterns and constraints.

Use the schema/template:

- `schemas/next_gameplay_unit_input.schema.json`
- `schemas/gameplay_design_model.schema.json`
- `templates/GAMEPLAY_DESIGN_MODEL.json`
- `templates/NEXT_GAMEPLAY_UNIT_INPUT.json`

Then run:

```bash
python3 gameplay/prepare.py context \
  --game-repo <GAME_REPO> \
  --input design/gameplay/objective_gameplay/<objective_id>/NEXT_GAMEPLAY_UNIT_INPUT.json \
  --out design/gameplay/objective_gameplay/<objective_id>/NEXT_GAMEPLAY_UNIT_CONTEXT.md
```

`prepare.py` resolves ownership before any mkdir/write, merges the stable model
without sending it to a creative worker, checks every repo path
and exact evidence token, reads the locale CSV, requires runtime selection and
completion proof, validates actions/rewards, and emits one compact context.

### Readiness states

- `READY_FOR_HOW_DESIGN` — objective and action/reward materials are proven.
- `READY_FOR_NEW_GAMEPLAY_DESIGN` — objective materials are proven but no
  applicable implemented action exists; this is a legitimate new-gameplay
  trigger, not missing evidence.
- `BLOCKED_BY_MATERIAL` — the progression/objective/action declaration is
  missing, stale, text-only, or cannot be verified against the repo.

The script checks structural/evidential readiness. It does not decide whether
the actions make good gameplay.

## Step 2 — author the whole objective gameplay

One creative worker reads only `NEXT_GAMEPLAY_UNIT_CONTEXT.md` plus an explicit
small source excerpt if the context names an unresolved design fact. It creates
one `OBJECTIVE_GAMEPLAY.md` from objective issue/current frontier through
objective completion.

Inside that single pass the author may recursively infer:

```text
objective
  -> necessary physical/game action
  -> thinness or repetition
  -> problem
  -> player activity
  -> pressure
  -> player desire
  -> existing action/reward response
  -> meaningful decision where rote play remains
```

These are internal micro-operations, not separate workflow steps or artifacts.
The output table directly records concrete situations, visible information,
available actions, rewards/consequences, meaningful decisions/execution, and
the resulting next situation.

### New-gameplay trigger

New gameplay is allowed. Use the smallest sufficient escalation:

```text
new situation
  -> new combination of existing actions
  -> new target or consequence for an existing action
  -> new player action
  -> new gameplay system
```

Escalate when a required activity is trivial, cannot causally express the
objective, or becomes deterministic/repetitive before objective completion.
Do not use a fixed novelty quota, create a main-progression branch merely to
prove choice, or require punishment where positive rewards provide legible
different consequences.

## Step 3 — compile persistent production plans

Step 3 leaves creative design and inspects the real repo to translate
`OBJECTIVE_GAMEPLAY.md` into executable change units. The factory user chooses
the planning model and protocol:

- a Plan Mode model may investigate and author the files;
- a model without Plan Mode may author the same files directly.

The choice never changes the artifact contract. Before production, both write:

```text
<objective_dir>/PRODUCTION_PLAN_MANIFEST.json
<objective_dir>/production_plans/<plan_id>_<change_unit>.md
```

Use:

- `schemas/production_plan_manifest.schema.json`
- `templates/PRODUCTION_PLAN_MANIFEST.json`
- `templates/PRODUCTION_PLAN.md`

The manifest binds to the exact UTF-8 SHA-256 of `OBJECTIVE_GAMEPLAY.md`, maps
every numbered row to `IMPLEMENT`, `VERIFY_EXISTING`, or
`NO_CHANGE_REQUIRED`, declares dependencies and exclusive planned-path
ownership, and records any blocking gap. Each Markdown plan preserves the
player-visible result, exact repo reuse/evidence, owned production changes,
locked non-goals, deterministic verification, and handoff.

`N` is determined by coherent execution and verification boundaries. Do not
make one plan per table row, split two plans that both mutate the same file, or
leave essential planning knowledge only in ephemeral Plan Mode/session state.
The planner may identify a precise `BLOCKED_BY_PLAN_GAP`, but it may not
redesign gameplay or start a generic review loop.

Validate before execution:

```bash
python3 gameplay/plan.py validate \
  --game-repo <GAME_REPO> \
  --manifest design/gameplay/objective_gameplay/<objective_id>/PRODUCTION_PLAN_MANIFEST.json
```

Only `READY_FOR_EXECUTION` hands the persistent plans to production. This is
structural planning readiness, not a gameplay-experience verdict.

## Step 4 — automatically execute production

For a normal high-level request to create or continue gameplay,
`READY_FOR_EXECUTION` is not a valid stopping point. The same caller, or its
outer orchestrator when the planning model cannot mutate the repo, must
immediately:

1. select plans whose declared dependencies are complete;
2. execute their owned code/data/UI/localization work directly;
3. invoke asset, sound, story, or other factories only when the plan's work
   types require them;
4. run the standard project tests/build/asset validation belonging to that
   production work;
5. continue until every plan is implemented or an exact external blocker is
   reached.

This step adds no Gameplay Factory author, packet, reviewer, or acceptance
gate. It is the control-flow instruction that prevents a user who simply asks
the AI Factory to make gameplay from receiving plans and then having to ask a
second time for implementation. Stop after Step 3 only for an explicit
plan-only request or an environment that has no execution-capable caller; in
the latter case report that exact capability blocker and the persisted plan
paths rather than implying the gameplay was produced.

## Calibration boundary

Do not regenerate Span Quant, Beat Sheet, walkthroughs, packets, or reviews
merely to preserve the previous workflow shape. The first real
`OBJECTIVE_GAMEPLAY.md` proved compact enough to proceed to production
planning; Step 3 now tests whether it can replace those prior intermediate
design artifacts. Runtime observation and fresh experience acceptance remain
separate, explicitly invoked concerns rather than automatic Step 4 gates.
