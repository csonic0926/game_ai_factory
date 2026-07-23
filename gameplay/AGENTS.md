# Gameplay Factory Guide and AI Entry

This file is the canonical entry for an AI caller. Gameplay Factory currently
supports two **Case 3** production workflows:

1. **Progression production** — make/complete the primary progression's next
   unit and its gameplay.
2. **Gap repair** — close one concrete missing or broken gameplay contract
   inside an already-authored progression unit.

Runtime evidence reading remains independently invoked. Case 1 idea discovery
and Case 2 foreign-repo onboarding are not implemented here.

## 1. Resolve the target before routing

Resolve the game repo from explicit path -> current Git root -> ignored local
registry for an explicit project id. Never scan sibling repos.

Set:

```text
<GAMEPLAY_ROOT> = <GAME_REPO>/design/gameplay
```

Reject:

- this factory repo or any child as the game repo;
- any output outside the game repo;
- a blank or foreign repo disguised as Case 3;
- committed absolute developer paths.

Read the game-owned adapters/model before production:

```text
<GAMEPLAY_ROOT>/adapter/PROJECT_GAMEPLAY_PROFILE.md
<GAMEPLAY_ROOT>/adapter/PRODUCTION_ADAPTER.md
<GAMEPLAY_ROOT>/adapter/OBSERVATION_ADAPTER.md
<GAMEPLAY_ROOT>/adapter/GAMEPLAY_DESIGN_MODEL.json
```

Missing or inconsistent answers mean the repo is not ready for normal Case 3
work.

## 2. Route to exactly one workflow

| Current need | Operation | Workflow |
| --- | --- | --- |
| No concrete unresolved gap is known; continue or complete the main progression | `produce_objective` | [`docs/CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md`](docs/CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md) |
| A concrete player-visible causal contract is missing/broken inside an existing objective | `repair_gameplay_gap` | [`docs/CASE3_GAMEPLAY_REPAIR_WORKFLOW.md`](docs/CASE3_GAMEPLAY_REPAIR_WORKFLOW.md) |
| Only compile forward context | `prepare_objective` | Objective workflow Step 1 |
| Only author the forward gameplay table | `author_objective` | Objective workflow Step 2 |
| Explicit plan-only request for forward production | `plan_production` | Objective workflow Step 3 |
| Only compile a known repair context | `prepare_repair` | Repair workflow Step 1 |
| Explicit plan-only request for a repair | `plan_repair` | Repair workflow Step 3 |
| Validate/read runtime evidence | `observe_runtime` / `runtime_acceptance` | Reader/acceptance docs; never a creative entry |

### Routing priority

If a concrete repair gap and a request to advance progression are both active,
repair the known gap first unless the user explicitly defers it. Do not keep
advancing the main progression while leaving a known player-visible break
behind.

A gap must be concrete and evidenced. It may come from the user, runtime
observation, implementation research, a test failure, or fresh acceptance. Do
not invent a repair merely because a system could be improved.

For a continuing call, inspect the explicitly named/current game-owned
`design/gameplay/repairs/*/GAMEPLAY_GAP_INPUT.json` files:

- `OPEN` routes to repair before forward progression;
- `IMPLEMENTED_PENDING_ACCEPTANCE` routes to the named user/fresh-review
  closure boundary, not another production pass;
- `CLOSED` and user-authorized `DEFERRED` do not block forward progression.

Never scan sibling game repos for gaps.

If several gaps are `OPEN`, execute one repair at a time against the refreshed
repo. Prefer the gap that breaks the earliest currently reachable progression
window unless the user supplies another priority. Do not merge unrelated gaps
into one repair artifact or run overlapping repair plans concurrently.

### Fast distinction

Use **progression production** when the question is:

> What should the game's primary progression ask the player to do next, and
> what gameplay carries them to its completion?

Use **gap repair** when the question is:

> Within an existing objective, what promised action/consequence/state
> transition is missing or broken, and what is the smallest closure?

Use neither when:

- the request is only a genre/blank project — Case 1 / future idea factory;
- the repo lacks factory-readable progression/action state — Case 2 / future
  onboarding;
- it is an ordinary code bug with no material player-visible gameplay effect;
- it requests an unanchored new feature rather than a next objective or an
  evidenced existing gap.

## 3A. Progression production — mainline next unit

Read the full objective workflow. Its compact path is:

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
```

The primary progression driver answers **what is next**. Gameplay is **how**
the player reaches it through actions and their consequences/rewards.

Only `READY_FOR_HOW_DESIGN` or `READY_FOR_NEW_GAMEPLAY_DESIGN` starts the one
Step 2 author. Only `READY_FOR_EXECUTION` starts production. For an ordinary
make/continue request, the caller executes the plans automatically rather than
asking the user to say “write the code”.

## 3B. Gap repair — current/previous unit closure

Read the full repair workflow. It mirrors the compact four-step shape without
regenerating the base objective:

```text
exact existing OBJECTIVE_GAMEPLAY.md + one evidenced gap
  -> repair.py context
  -> GAMEPLAY_REPAIR_CONTEXT.md
  -> direct planning when authority already exists
     OR one bounded repair author -> GAMEPLAY_REPAIR.md
  -> user-selected repair planner
  -> REPAIR_PLAN_MANIFEST.json + production_plans/*.md
  -> repair_plan.py validate
  -> original caller executes dependency-ready repair plans
```

Step 1 returns:

- `READY_FOR_DIRECT_REPAIR_PLAN` — explicit design authority or a persisted
  user ruling already states the exact result; skip creative authoring;
- `READY_FOR_REPAIR_DESIGN` — the existing objective omitted or ambiguously
  specified the decision; author one small repair artifact;
- `BLOCKED_BY_REPAIR_MATERIAL` — evidence/anchor/authority is insufficient or
  conflicts with locked design.

The repair source and base objective are both SHA-bound. A bounded repair never
rewrites `OBJECTIVE_GAMEPLAY.md`, invents the successor progression unit, or
replans unrelated rows.

Only `READY_FOR_EXECUTION` begins implementation. Standard tests prove code,
data, and state behavior; final experiential closure remains with the user or
fresh acceptance reviewer named by the repair. Production changes the
game-owned gap status from `OPEN` to `IMPLEMENTED_PENDING_ACCEPTANCE`; it may
not self-mark `CLOSED`.

## Shared hard rules

- **Known gap before forward expansion.** Unless explicitly deferred, close a
  concrete known break before producing the next progression unit.
- **Primary progression first.** A mission, stage, spatial frontier, or
  equivalent driver answers what comes next; it need not branch.
- **What and how stay separate.** The progression objective is not itself the
  meaningful gameplay choice.
- **Script before creative tokens.** Never ask a creative worker to rediscover
  repo progression, scan all locales/code, or rebuild the stable action list.
- **Stable vocabulary is written once.** Keep progression/action/reward
  evidence in `GAMEPLAY_DESIGN_MODEL.json`; select ids per objective or repair.
- **Locale text is not code.** Runtime selection/completion wiring must exist.
- **Use the smallest sufficient escalation.** Reconfigure a situation,
  action, target, or consequence before adding a new action/system.
- **Plans compile; they do not redesign.** A real gap returns to the relevant
  author/authority owner rather than being silently invented by the planner.
- **Planning files are mandatory; Plan Mode is optional.** Downstream
  execution reads persisted files, never private chat state.
- **Plan ownership is exclusive.** Shared planned paths across plans are
  invalid.
- **Bind production to exact design authority.** A changed objective or repair
  source makes its plans stale.
- **`READY_FOR_EXECUTION` is intermediate.** Continue through standard
  production unless the user explicitly requested plan-only output.
- **Factory completion is not fun/acceptance.** Normal tests and structure do
  not self-award an experience verdict.
- **Artifacts land in the game repo.** Factory owns blank templates, schemas,
  tools, contracts, and tests only.
- **Ownership precedes writes.** Resolve all paths before any mkdir/write.
- **Paths stay portable.** Persist game-repo-relative paths.

## Runtime evidence boundary

`reader.py` validates and transforms runtime evidence. It does not prepare
creative context, invent gameplay, or issue a final experience verdict.

- Raw events, derived timelines, blind interpretations, and acceptance
  comparisons remain separate.
- Blind input contains no design semantics or hidden/future state.
- Evidence chains stay within one run/session/correlation chain.
- Controlled branch probes require complete independent branches.
- Negative checks distinguish satisfied no-match, violation, and incomplete
  coverage.
- Runtime observation may reveal a repair candidate; a user or fresh reviewer
  must record the concrete gap before the repair workflow treats it as work.

## Current contracts

### Entry and Case 3 production

- `docs/AI_CALLER_LANDING.md`
- `docs/CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md`
- `docs/CASE3_GAMEPLAY_REPAIR_WORKFLOW.md`

### Progression production

- `prepare.py`
- `schemas/next_gameplay_unit_input.schema.json`
- `schemas/gameplay_design_model.schema.json`
- `templates/GAMEPLAY_DESIGN_MODEL.json`
- `templates/NEXT_GAMEPLAY_UNIT_INPUT.json`
- `templates/OBJECTIVE_GAMEPLAY.md`
- `plan.py`
- `schemas/production_plan_manifest.schema.json`
- `templates/PRODUCTION_PLAN_MANIFEST.json`
- `templates/PRODUCTION_PLAN.md`

### Gap repair

- `repair.py`
- `schemas/gameplay_gap_input.schema.json`
- `templates/GAMEPLAY_GAP_INPUT.json`
- `templates/GAMEPLAY_REPAIR.md`
- `repair_plan.py`
- `schemas/repair_plan_manifest.schema.json`
- `templates/REPAIR_PLAN_MANIFEST.json`
- `templates/REPAIR_PRODUCTION_PLAN.md`

### Runtime evidence

- `reader.py`
- `docs/RUNTIME_OBSERVATION_AND_ACCEPTANCE_CONTRACT.md`
- `docs/PROJECT_ADAPTER_CONTRACT.md`
- `docs/OBSERVATION_READER.md`

The older Span Quant / Beat Sheet / walkthrough / packet lineage remains for
existing pilot artifacts. It is not the default entry for either compact Case
3 workflow.
