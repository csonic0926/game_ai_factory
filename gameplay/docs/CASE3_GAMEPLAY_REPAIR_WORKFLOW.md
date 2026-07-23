# Case 3 gameplay-gap repair workflow

This workflow closes one evidenced gameplay gap inside an existing primary
progression unit. It is the closure-side companion to
[`CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md`](CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md),
which moves the game's primary progression forward by producing one objective.

It does **not** discover a new game idea, onboard a foreign repo, rewrite the
whole anchored objective, or claim that a repaired experience is accepted.

## When to route here

Route to `repair_gameplay_gap` when all of these are true:

1. the target repo is already Case 3 / factory-readable;
2. a concrete missing or broken player-visible causal contract is known from a
   user report, runtime observation, implementation research, test failure, or
   fresh acceptance result;
3. the gap occurs inside an existing
   `OBJECTIVE_GAMEPLAY.md` progression window and can name affected rows;
4. fixing it should preserve that objective rather than replace its primary
   progression purpose.

Examples include:

- a visible interaction promises an action but the action is unavailable in a
  reachable state;
- a resource, meter, reward, or consequence is present but cannot causally
  affect play as the objective implies;
- an already designed choice has one route missing, one consequence
  disconnected, or one state transition unavailable;
- a runtime implementation fails an explicit objective requirement.

Do **not** route here for:

- the next primary objective when no existing gap is known — use
  `produce_objective`;
- an unanchored desired feature — attach it to a real next objective or obtain
  a user ruling;
- a production planner's unresolved requirement — return the exact
  `BLOCKED_BY_PLAN_GAP` to the objective author;
- a locked-design contradiction — obtain a user ruling or revise the base
  authority first;
- a code defect with no material player-visible gameplay consequence — use the
  repo's ordinary bug-fix workflow;
- a vague request to “make it better” without an evidenced broken contract.

If a concrete repair gap and a request to advance progression arrive together,
repair the known gap first unless the user explicitly defers it.

## Object model

Objective production advances the outer state:

```text
progression unit N -> completion -> progression unit N+1
```

Gameplay repair closes a known hole inside one existing unit:

```text
exact OBJECTIVE_GAMEPLAY revision
  + exact progression window / affected rows
  + observed player-visible contradiction
  + stable affected actions/rewards
  -> smallest authoritative repair
  -> bounded production plans
  -> implementation and external closure evidence
```

The base `OBJECTIVE_GAMEPLAY.md` stays immutable during a bounded repair. A
repair is an additive authority bound to its exact SHA-256. If the base design
must be replaced or contradicted, stop treating the work as a bounded repair.

## Game-owned artifact layout

```text
design/gameplay/repairs/<gap_id>/
  GAMEPLAY_GAP_INPUT.json
  GAMEPLAY_REPAIR_CONTEXT.md
  GAMEPLAY_REPAIR.md                 # only when design is missing/ambiguous
  REPAIR_PLAN_MANIFEST.json
  production_plans/
    R01_<change_unit>.md
```

Only create the optional `GAMEPLAY_REPAIR.md` when Step 1 returns
`READY_FOR_REPAIR_DESIGN`.

### Gap lifecycle and future routing

`GAMEPLAY_GAP_INPUT.json` carries one mutable routing field:

- `OPEN` — eligible for repair and takes priority over forward progression;
- `IMPLEMENTED_PENDING_ACCEPTANCE` — production finished, but no more repair
  work should start until user/fresh-review evidence decides closure;
- `CLOSED` — the named closure authority accepted the gap as closed;
- `DEFERRED` — the user explicitly allowed forward progression first.

Only an `OPEN` input may enter Step 1. Ordinary production may advance it to
`IMPLEMENTED_PENDING_ACCEPTANCE`; code/tests alone may not set `CLOSED`.
Future callers inspect explicit/current game-owned repair inputs before routing
to progression production, without scanning sibling game repos.

When several gaps are `OPEN`, repair one at a time against the refreshed repo.
Prefer the earliest currently reachable broken progression window unless the
user provides another priority. Unrelated gaps never share one repair artifact
or concurrent overlapping plans.

## Step 1 — compile the gap context mechanically

Start from:

- `schemas/gameplay_gap_input.schema.json`
- `templates/GAMEPLAY_GAP_INPUT.json`

The input binds:

- the exact anchored objective id, path, UTF-8 SHA-256, and affected rows;
- the current `OPEN` lifecycle status;
- one stable gap id and its progression window;
- the observed break and player-visible contradiction;
- exact game-repo-relative runtime, implementation, or test evidence;
- the design-authority state;
- only affected action ids from the stable
  `GAMEPLAY_DESIGN_MODEL.json`;
- explicit preservation constraints and user rulings.

Run:

```bash
python3 gameplay/repair.py context \
  --game-repo <GAME_REPO> \
  --input design/gameplay/repairs/<gap_id>/GAMEPLAY_GAP_INPUT.json \
  --out design/gameplay/repairs/<gap_id>/GAMEPLAY_REPAIR_CONTEXT.md
```

`repair.py` resolves all ownership before creating the output, rejects stale
objective hashes and unknown rows/actions, requires the canonical
`design/gameplay/repairs/<gap_id>/` paths, verifies exact evidence tokens, and
routes by authority:

- `READY_FOR_DIRECT_REPAIR_PLAN`
  - an existing design requirement or persisted user ruling already states the
    required player-visible result;
  - the rendered context contains numbered repair rows and is itself the
    planning authority;
  - skip creative Step 2.
- `READY_FOR_REPAIR_DESIGN`
  - the objective omitted the decision or is ambiguous without contradicting
    locked design;
  - use exactly one bounded repair author in Step 2.
- `BLOCKED_BY_REPAIR_MATERIAL`
  - evidence, anchor, action material, hash, user authority, or design
    consistency is missing;
  - do not author or plan.

### Authority states

The input must use one:

- `EXPLICIT_REQUIREMENT` — exact base design evidence already requires the
  behavior;
- `USER_RULING` — a persisted user ruling supplies the exact requirement;
- `OMITTED_OR_AMBIGUOUS` — the runtime exposes a real gap but the repair choice
  is not yet design authority;
- `CONFLICTS_WITH_LOCKED_DESIGN` — repair is blocked until authority changes.

An AI suggestion is not a `USER_RULING`. An absence of design text is not
proof of the desired replacement behavior.

## Step 2 — author only the missing repair decision

Run this step only for `READY_FOR_REPAIR_DESIGN`.

One author reads `GAMEPLAY_REPAIR_CONTEXT.md` and writes
`GAMEPLAY_REPAIR.md` using the template. The repair table records only:

- the broken situation/causal contract;
- the required player-visible closure;
- affected actions and consequences;
- any meaningful decision or execution that remains;
- preserved behavior/non-goals;
- the evidence required to close the gap.

Use the smallest sufficient escalation:

```text
clarify affordance
  -> restore an existing action/consequence
  -> recompose existing actions
  -> add a target/consequence
  -> add a player action
  -> add a gameplay system
```

Do not regenerate the whole objective, invent the successor objective, or run
the legacy quant/Beat Sheet/walkthrough tower merely because one gap needs a
repair decision.

## Step 3 — compile bounded persistent repair plans

A Plan Mode model or ordinary model may inspect the related repo surface. Both
must persist the same contract:

- `schemas/repair_plan_manifest.schema.json`
- `templates/REPAIR_PLAN_MANIFEST.json`
- `templates/REPAIR_PRODUCTION_PLAN.md`

The planning source is:

- `GAMEPLAY_REPAIR_CONTEXT.md` for
  `READY_FOR_DIRECT_REPAIR_PLAN`; or
- `GAMEPLAY_REPAIR.md` for `READY_FOR_REPAIR_DESIGN`.

The manifest binds both:

1. the exact base `OBJECTIVE_GAMEPLAY.md` path and SHA-256; and
2. the exact repair source path and SHA-256.

Every numbered repair row has exactly one coverage entry. Plans split by
coherent file/state ownership and verification boundary, not by table row.
Shared planned paths are invalid.

Validate:

```bash
python3 gameplay/repair_plan.py validate \
  --game-repo <GAME_REPO> \
  --manifest design/gameplay/repairs/<gap_id>/REPAIR_PLAN_MANIFEST.json
```

Only `READY_FOR_EXECUTION` may enter production.
`BLOCKED_BY_PLAN_GAP` returns the precise missing repair decision to Step 2 or
the authority owner; the planner may not widen the repair or rewrite the base
objective.

## Step 4 — execute automatically, then preserve the closure boundary

For a normal request to fix the gameplay gap, `READY_FOR_EXECUTION` is
intermediate. The original caller immediately:

1. executes dependency-ready repair plans;
2. changes only paths owned by those plans;
3. runs ordinary repo tests/build/data/asset validation;
4. captures the player-visible runtime evidence required by the repair source;
5. updates `GAMEPLAY_GAP_INPUT.json` to
   `IMPLEMENTED_PENDING_ACCEPTANCE`;
6. reports implementation completion separately from final experiential
   closure.

Code tests may prove the state transition and prevent regression. They do not
self-award “the gap is experientially closed.” That remains with the user or a
fresh acceptance reviewer named by the repair source.

Stop after planning only when the user explicitly asks for plan-only output or
the caller cannot execute.

## Token discipline

- Do not re-scan the whole repo: Step 1 supplies the anchor, exact gap evidence,
  affected stable actions, and constraints.
- Do not rewrite `OBJECTIVE_GAMEPLAY.md`: the repair binds and preserves it.
- Do not spend a creative author when an explicit requirement or user ruling
  already exists.
- Do not plan or verify unrelated objective rows.
- Do not turn gap discovery into an automatic general review tower. This
  workflow consumes a known concrete gap; runtime observation, user playtest,
  or fresh acceptance remains the source of newly discovered gaps.
