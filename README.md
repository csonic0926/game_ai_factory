# game_ai_factory

Umbrella for four game-production factories, each callable by an AI agent
through a landing doc and an explicit production contract:

- **`asset/`** — game asset factory. Blender-first isometric tile/wall reference
  pairs, prop/object sprites, tile re-skin, chroma-key cleanup. Python CLI
  (`itf.py` + spec JSON). *(retains this repo's original git history)*
- **`story/`** — game story factory. World / character / cast / chapter narrative
  production with hard `.5` review gates and file-based handoff, driven by the
  `game-story-factory` Claude skill and per-project adapters.
- **`gameplay/`** — gameplay factory. Continues a factory-readable game's
  primary progression one objective at a time, or repairs a concrete gameplay
  gap inside an existing objective. Uses compact script-first context,
  persistent model-independent production plans, and automatic caller
  handoff to normal code/data/asset/sound production.
- **`sound/`** — game sound factory. Text→SFX via ElevenLabs, then de-silence +
  peak-normalize so clips are drop-in. Python CLI (`sfx.py` + spec JSON).

Start at [`AI_CALLER_LANDING.md`](AI_CALLER_LANDING.md) to route to the right one.

## Setup

One-time per machine, after cloning this repo:

```bash
python3 setup.py sync
```

`sync` symlinks every factory-provided skill (`*/skills/*/SKILL.md`) into the
harness skill directories (default `~/.claude/skills` and `~/.codex/skills`,
deduplicated when they share one real directory). Because they are symlinks,
`git pull` on this repo **is** the skill update — no re-run needed. Use
`sync --copy` for harnesses/filesystems without symlink support; copied skills
carry a `.factory_version` stamp and are refreshed by re-running `sync` after a
pull. Both modes only ever touch factory-owned entries.

Once per game repo, when connecting it to the factory:

```bash
python3 setup.py link --game-repo <GAME_REPO>
```

`link` writes a harness-agnostic **Game AI Factory routing block** into the
game repo's `AGENTS.md` (between managed markers — idempotent, re-run safe),
creates a `CLAUDE.md` pointer if the repo has none, and records this machine's
factory path in the git-ignored `design/AI_FACTORY.local.md` so committed files
never contain absolute developer paths. After `link`, any agent session opened
in the game repo knows the four departments exist and when to consult each,
without the user having to name a factory in the prompt. Both commands support
`--dry-run`.

## Gameplay Factory — current Case 3 entry

[`gameplay/AGENTS.md`](gameplay/AGENTS.md) is both the Gameplay Factory guide
and its canonical AI entry. It resolves the game repo, confirms that it is
already factory-readable, then routes to one of two workflows:

| Need | Operation | Contract |
| --- | --- | --- |
| Complete or advance the primary progression's next unit | `produce_objective` | [`CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md`](gameplay/docs/CASE3_OBJECTIVE_GAMEPLAY_WORKFLOW.md) |
| Repair one evidenced player-visible gap inside an existing objective | `repair_gameplay_gap` | [`CASE3_GAMEPLAY_REPAIR_WORKFLOW.md`](gameplay/docs/CASE3_GAMEPLAY_REPAIR_WORKFLOW.md) |

If both are active, a concrete known gap is repaired before forward expansion
unless the user explicitly defers it.

Current scope is **Case 3**: the game repo has already been produced/onboarded
and contains trustworthy progression, action/reward, and adapter state.
Genre-only blank projects (Case 1) and foreign-repo onboarding (Case 2) are not
silently treated as Case 3.

### Progression production

```text
stable GAMEPLAY_DESIGN_MODEL.json + objective frontier
  -> prepare.py context
  -> NEXT_GAMEPLAY_UNIT_CONTEXT.md
  -> one complete OBJECTIVE_GAMEPLAY.md authoring pass
  -> user-selected Plan Mode or ordinary planner
  -> PRODUCTION_PLAN_MANIFEST.json + production_plans/*.md
  -> plan.py validate
  -> original caller automatically executes production
```

The primary progression answers **what the player does next**. Gameplay is the
**how** between objective issue and completion: player actions, problems,
information, consequences/rewards, and meaningful decisions or execution.

```bash
python3 gameplay/prepare.py context \
  --game-repo <GAME_REPO> \
  --input design/gameplay/objective_gameplay/<objective_id>/NEXT_GAMEPLAY_UNIT_INPUT.json \
  --out design/gameplay/objective_gameplay/<objective_id>/NEXT_GAMEPLAY_UNIT_CONTEXT.md

python3 gameplay/plan.py validate \
  --game-repo <GAME_REPO> \
  --manifest design/gameplay/objective_gameplay/<objective_id>/PRODUCTION_PLAN_MANIFEST.json
```

### Gameplay-gap repair

```text
exact existing OBJECTIVE_GAMEPLAY.md + one evidenced gap
  -> repair.py context
  -> GAMEPLAY_REPAIR_CONTEXT.md
  -> direct planning when authority already exists
     OR one bounded GAMEPLAY_REPAIR.md authoring pass
  -> REPAIR_PLAN_MANIFEST.json + production_plans/*.md
  -> repair_plan.py validate
  -> original caller automatically executes repair production
```

A repair is SHA-bound to both the base objective and its repair authority. It
does not rewrite the whole objective, redesign unrelated rows, or invent the
successor progression unit.

```bash
python3 gameplay/repair.py context \
  --game-repo <GAME_REPO> \
  --input design/gameplay/repairs/<gap_id>/GAMEPLAY_GAP_INPUT.json \
  --out design/gameplay/repairs/<gap_id>/GAMEPLAY_REPAIR_CONTEXT.md

python3 gameplay/repair_plan.py validate \
  --game-repo <GAME_REPO> \
  --manifest design/gameplay/repairs/<gap_id>/REPAIR_PLAN_MANIFEST.json
```

Gap state persists as `OPEN`, `IMPLEMENTED_PENDING_ACCEPTANCE`, `CLOSED`, or
user-authorized `DEFERRED`. Passing implementation tests may advance a gap to
pending acceptance, but cannot self-award experiential closure.

### Runtime evidence remains separate

[`gameplay/reader.py`](gameplay/reader.py) validates and transforms runtime
evidence, reconstructs same-run causal chains, produces blind-reader input, and
measures declared budgets. It does not invent gameplay or issue a final
experience verdict.

## Design principle

One umbrella, four factories, **one ownership model**: an AI caller resolves
the factory contract and project inputs, produces and validates the requested
artifact, and versions the result with the game. Nothing produced for a game
lands under this umbrella. Factory contracts, schemas, tools, and blank
templates remain here; filled designs, plans, runtime evidence, code, data,
assets, and sound land in the game repo.

## Layout

```
AI_CALLER_LANDING.md     route here first
asset/   itf.py, pipeline/, docs/, examples/ …   (original git history)
story/   skills/, core/steps|craft|schemas/, adapters/
gameplay/ AGENTS.md, prepare.py, plan.py, repair.py, repair_plan.py,
          reader.py, docs/, schemas/, adapters/, templates/, tests/
sound/   sfx.py, pipeline/, docs/, examples/
```

## Compatibility

`tools/game_asset_factory` and `tools/game_story_factory` are kept as symlinks
into `asset/` and `story/` for any caller still using the old paths. Remove when
no longer referenced.
