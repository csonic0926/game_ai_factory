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
| Continue a factory-readable game's next objective or repair a known gap inside an existing objective | **gameplay** | `gameplay/AGENTS.md` routes to the progression or repair workflow |
| A game SFX (generate + trim to drop-in) | **sound** | `sound/docs/AI_CALLER_LANDING.md` → `python3 sound/sfx.py run --spec ...` |

## Calling conventions (shared)

- **asset** and **sound** are Python CLIs driven by a **spec JSON**; run from
  their own dir, then read `<run>/artifact_status.json` first, then
  `deliverables/`.
- **story** is a Claude **skill** (`/game-story-factory <project_id> ...`) backed
  by adapter + step machines; artifacts land in the *game repo's* `<STORY_ROOT>`.
- **gameplay** currently supports two compact Case 3 pipelines. Progression
  production mechanically resolves the primary driver/next objective and
  proven actions/rewards before one complete objective authoring pass. Gap
  repair binds one evidenced break to an exact existing objective revision,
  skips creative authoring when authority already specifies the result, and
  otherwise authors one bounded repair without rewriting the base objective.
  Both persist model-independent production plans; `READY_FOR_EXECUTION`
  automatically returns control to the original caller for normal
  code/data/asset/sound production unless the user explicitly requested
  plan-only output. A known gap is repaired before forward expansion unless the
  user defers it. The prior quant/Beat Sheet/walkthrough chain remains for
  existing pilot artifacts but is not the default compact entry.
  `gameplay/reader.py` remains a separately invoked runtime-evidence reader,
  not a creative CLI/skill or acceptance oracle.
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
