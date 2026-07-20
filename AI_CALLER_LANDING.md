# AI caller landing — game_ai_factory

Umbrella for four game-production factories. If you are an AI agent from another
repo, **start here**, pick the factory, then read that factory's own landing doc.

```
game_ai_factory/
  asset/   game asset factory  — isometric tiles, walls, props, tile re-skin, bg cleanup
  story/   game story factory  — world / character / cast / chapter narrative production
  gameplay/ gameplay factory   — player-time trace, beat packets, reception contracts
  sound/   game sound factory  — text->SFX (ElevenLabs) + de-silence/normalize
```

## Route by need

| You need | Factory | Entry point |
| --- | --- | --- |
| Floor/wall iso tiles, props, tile re-skin, validated sprites | **asset** | `asset/docs/AI_CALLER_LANDING.md` → `python3 asset/itf.py ...` |
| World/characters/cast/chapters, staged story text | **story** | skill `game-story-factory` (installed) → `story/skills/game-story-factory/SKILL.md` |
| Author, realize, instrument, observe, and independently verify a gameplay experience against actual runtime evidence | **gameplay** | `gameplay/AGENTS.md` → `gameplay/docs/AI_CALLER_LANDING.md` |
| A game SFX (generate + trim to drop-in) | **sound** | `sound/docs/AI_CALLER_LANDING.md` → `python3 sound/sfx.py run --spec ...` |

## Calling conventions (shared)

- **asset** and **sound** are Python CLIs driven by a **spec JSON**; run from
  their own dir, then read `<run>/artifact_status.json` first, then
  `deliverables/`.
- **story** is a Claude **skill** (`/game-story-factory <project_id> ...`) backed
  by adapter + step machines; artifacts land in the *game repo's* `<STORY_ROOT>`.
- **gameplay** is quant-first: a Span Quant Sheet fixes span/duration and an
  implementation-blind playable-content demand before any Beat Sheet, then
  versioned Experience Beat Sheet authority, continuous player-time
  realization, observation-bearing production packets, actual runtime
  evidence, blinded readback, and fresh conformance acceptance. The creative
  workflow is manual during pilots; `gameplay/reader.py` is a
  runtime-evidence reader, not a creative CLI/skill or acceptance oracle.
- CLI factories ship a `mock`/offline path where applicable for credit-free smoke.

## Cross-factory flows (why the umbrella)

The factories compose. A playable story sequence can draw on all four:

- **story** produces the scene's staged beats + dialogue (locale keys),
- **gameplay** turns its anchors into a continuous player-action/control/reception contract,
- **asset** produces any new props/tiles the scene needs,
- **sound** produces the SFX cues each beat fires.

Keep each factory's outputs landing in the **game repo**, never under this
umbrella. Factory-side changes (new workflow, provider, stage) belong in the
relevant sub-factory via normal commits.

## Repo notes

- This repo was `game_asset_factory`; it was promoted to the umbrella. `asset/`
  retains the original git history.
- `tools/game_asset_factory` and `tools/game_story_factory` remain as
  **backward-compat symlinks** into `asset/` and `story/`; safe to remove once
  no caller depends on the old paths.
