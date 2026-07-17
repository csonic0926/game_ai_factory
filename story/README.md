# game_story_factory

Project-agnostic **story creation factory** for game projects: world baseline,
character baselines, cast management, and chapter production — with hard
review gates and file-based handoff, reusable by ANY game repo through a thin
per-project adapter.

Lineage: extracted and generalized from the proven `rpg-1-*` skill system
(progressive constraint closure; every `STEP n` has a `STEP n.5` review gate
that can hard-block bad output).

## Factory positioning

- caller = a game project, represented by an adapter whose canonical home is
  the game repo's `<STORY_ROOT>/adapter/` (factory keeps the phonebook
  `adapters/registry.md`; unmigrated projects still resolve via the legacy
  `adapters/<project_id>/` fallback)
- factory owns the **workflow** (step files, review gates, schemas, craft docs)
- the game repo owns the **artifacts** (everything lands under that repo's
  `<STORY_ROOT>`, so story versions with the game)
- the adapter owns the **runtime and staging knowledge** (how approved text can
  be staged: `VISUAL_GRAMMAR.md`; how staged beats become runnable game data:
  `LANDING_SPEC.md`; plus optional `SYNC_SPEC.md`) — it describes the game
  repo's code, so it lives with that code and versions with the game; the
  adapter also owns the optional `GLOSSARY.csv` operational termbase for that
  game's registered world vocabulary; the factory keeps the contract and the
  blank answer sheets (`adapters/_template/`)

The public order contract is `docs/PROJECT_PROFILE_CONTRACT.md`.

## Layout

```
modules/                                # the story department as five modules (see modules/README.md)
  world-rules-editor/                   # sovereignty files: WORLD_RULES + NARRATIVE_DELIVERY (interactive, USER holds the pen)
  twin-db/                              # story-world database: query/CRUD + per-chapter write-back
  beat-sheet-dialogue/                  # 攤田 → USER cuts → converge into an emotional beat sheet (interactive)
  delivery-planner/                     # assign each beat to rough channel intent
  step-pipelines/                       # pointer to core/steps (the headless step machines)
core/
  NARRATIVE_FOUNDATIONS.md              # the three universal foundations every module serves
  steps/world|character|cast|chapter/   # generalized step files (STEP n / STEP n.5)
  schemas/                              # CHARACTER_SCHEMA.md + templates (incl. the two sovereignty templates)
  craft/                                # reusable writing-technique docs
adapters/
  _template/                            # blank answer sheets — seeded into a game repo's <STORY_ROOT>/adapter/ on onboarding
  registry.md                           # phonebook: <project_id> → absolute adapter path (migrated projects)
  rpg-1/                                # reference adapter (Godot wuxia RPG, CSV runtime); legacy in-factory location; legacy WORKFLOW_CORE_VARIABLES
  vinci_world/                          # MOVED to the game repo (design/story/adapter/) — folder keeps only the pointer
docs/PROJECT_PROFILE_CONTRACT.md        # the adapter contract
skills/game-story-factory/SKILL.md      # the single orchestrator skill
scripts/init_story_root.sh              # bootstrap <STORY_ROOT> canonical layout
scripts/glossary_check.py                # exact glossary/schema/protected-term/locale review aid
scripts/twin_db.py                      # the twin-db CRUD/query CLI
```

## Use

Install the orchestrator skill once (symlink):

```bash
ln -sfn /Users/hunglingki/git_projects/tools/game_ai_factory/story/skills/game-story-factory \
  ~/.claude/skills/game-story-factory
```

Then from any session:

```
/game-story-factory vinci_world world start
/game-story-factory vinci_world character        # one character per run
/game-story-factory vinci_world cast
/game-story-factory vinci_world chapter resume
/game-story-factory vinci_world chapter start ask    # dialogue mode: direction questions first
/game-story-factory vinci_world chapter start auto   # headless: zero questions (AI callers use this)
```

Interaction modes: `ask` puts the run's few highest-leverage direction
questions to the user before the first step (answers land in a brief file);
`auto` runs straight through, recording every direction call + open items
for later review. Live human session defaults to ask; headless defaults to
auto. Details in the skill.

Master loop: `WORLD → CHARACTER → CAST ↔ CHARACTER → CAST_PASS → CHAPTER`.

## Onboarding a new game

1. `scripts/init_story_root.sh <STORY_ROOT>` inside the game repo — creates the
   canonical layout and seeds `<STORY_ROOT>/adapter/` with the blank answer
   sheets from `adapters/_template/`.
2. Fill `<STORY_ROOT>/adapter/PROJECT_PROFILE.md`, then register the project in
   `adapters/registry.md` (`<project_id> → <absolute adapter path>`).
   Fill `GLOSSARY.csv` when the project needs registered multilingual world
   vocabulary; leaving it absent is `NOT_AVAILABLE` and keeps legacy behavior.
3. World/character/cast production can start immediately.
4. Chapter production up to STEP 6 (approved runtime draft) needs no runtime;
   writing `VISUAL_GRAMMAR.md` unblocks STEP 6.7 (shootable staging plan), and
   writing `LANDING_SPEC.md` unblocks STEP 7 (landing into real game data).

## Rules that keep quality (do not weaken)

- The sovereignty files in each game's `<STORY_ROOT>/state/` —
  `WORLD_RULES.md` (what is true in the world) and `NARRATIVE_DELIVERY.md`
  (how the game speaks) — are USER-authored; AI reads, never edits. A
  not-yet-migrated project's legacy `WORKFLOW_CORE_VARIABLES.md` has the
  same protection.
- One fresh worker per step; the step file is the worker's only source of truth.
- Review steps never fix content — PASS/FAIL with reasons only.
- Fresh workers must be able to resume purely from disk artifacts.
