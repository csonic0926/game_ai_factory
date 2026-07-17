# game_ai_factory

Umbrella for four game-production factories, each callable by an AI agent
through a landing doc and an explicit production contract:

- **`asset/`** — game asset factory. Blender-first isometric tile/wall reference
  pairs, prop/object sprites, tile re-skin, chroma-key cleanup. Python CLI
  (`itf.py` + spec JSON). *(retains this repo's original git history)*
- **`story/`** — game story factory. World / character / cast / chapter narrative
  production with hard `.5` review gates and file-based handoff, driven by the
  `game-story-factory` Claude skill and per-project adapters.
- **`gameplay/`** — gameplay factory. Document-first translation from story
  anchors to continuous player-time walkthroughs, delta-emergent beat packets,
  and blinded reception checks via per-project gameplay/production adapters.
- **`sound/`** — game sound factory. Text→SFX via ElevenLabs, then de-silence +
  peak-normalize so clips are drop-in. Python CLI (`sfx.py` + spec JSON).

Start at [`AI_CALLER_LANDING.md`](AI_CALLER_LANDING.md) to route to the right one.

## Design principle

One umbrella, four factories, **one ownership model**: an AI caller resolves
the factory contract and project inputs, produces and validates the requested
artifact, and versions the result with the game. Nothing produced for a game
lands under this umbrella. Gameplay is intentionally manual/document-first in
Phase 0; the other factories retain their existing CLI/skill workflows.

## Layout

```
AI_CALLER_LANDING.md     route here first
asset/   itf.py, pipeline/, docs/, examples/ …   (original git history)
story/   skills/, core/steps|craft|schemas/, adapters/
gameplay/ docs/contracts, adapters/, templates/  (Phase 0, no CLI/skill)
sound/   sfx.py, pipeline/, docs/, examples/
```

## Compatibility

`tools/game_asset_factory` and `tools/game_story_factory` are kept as symlinks
into `asset/` and `story/` for any caller still using the old paths. Remove when
no longer referenced.
