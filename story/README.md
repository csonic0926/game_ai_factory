# game_story_factory

Project-agnostic **story creation factory** for game projects: world baseline,
character baselines, cast management, and chapter production — with hard
review gates and file-based handoff, reusable by ANY game repo through a thin
per-project adapter.

Lineage: extracted and generalized from the proven `rpg-1-*` skill system
(progressive constraint closure; every `STEP n` has a `STEP n.5` review gate
that can hard-block bad output).

## Factory positioning

- caller = a game project, represented by an adapter under `adapters/<project_id>/`
- factory owns the **workflow** (step files, review gates, schemas, craft docs)
- the game repo owns the **artifacts** (everything lands under that repo's
  `<STORY_ROOT>`, so story versions with the game)
- the adapter owns the **runtime knowledge** (how approved text becomes
  runnable game data: `LANDING_SPEC.md`, plus optional `SYNC_SPEC.md`)

The public order contract is `docs/PROJECT_PROFILE_CONTRACT.md`.

## Layout

```
core/
  steps/world|character|cast|chapter/   # generalized step files (STEP n / STEP n.5)
  schemas/                              # CHARACTER_SCHEMA.md + templates
  craft/                                # reusable writing-technique docs
adapters/
  _template/                            # copy to onboard a new game
  rpg-1/                                # reference adapter (Godot wuxia RPG, CSV runtime)
  vinci_world/                          # Vinci World (web); landing spec pending
docs/PROJECT_PROFILE_CONTRACT.md        # the adapter contract
skills/game-story-factory/SKILL.md      # the single orchestrator skill
scripts/init_story_root.sh              # bootstrap <STORY_ROOT> canonical layout
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
```

Master loop: `WORLD → CHARACTER → CAST ↔ CHARACTER → CAST_PASS → CHAPTER`.

## Onboarding a new game

1. `cp -r adapters/_template adapters/<project_id>` and fill `PROJECT_PROFILE.md`.
2. `scripts/init_story_root.sh <STORY_ROOT>` inside the game repo.
3. World/character/cast production can start immediately.
4. Chapter production up to STEP 6 (approved runtime draft) needs no runtime;
   writing `LANDING_SPEC.md` unblocks STEP 7 (landing into real game data).

## Rules that keep quality (do not weaken)

- `WORKFLOW_CORE_VARIABLES.md` in each game's `<STORY_ROOT>/state/` is
  USER-authored; AI reads, never edits.
- One fresh worker per step; the step file is the worker's only source of truth.
- Review steps never fix content — PASS/FAIL with reasons only.
- Fresh workers must be able to resume purely from disk artifacts.
