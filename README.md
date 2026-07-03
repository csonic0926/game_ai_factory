# game_ai_factory

Umbrella for three game-production factories, each callable by an AI agent the
same disciplined way (spec/skill + run artifacts + a landing doc):

- **`asset/`** — game asset factory. Blender-first isometric tile/wall reference
  pairs, prop/object sprites, tile re-skin, chroma-key cleanup. Python CLI
  (`itf.py` + spec JSON). *(retains this repo's original git history)*
- **`story/`** — game story factory. World / character / cast / chapter narrative
  production with hard `.5` review gates and file-based handoff, driven by the
  `game-story-factory` Claude skill and per-project adapters.
- **`sound/`** — game sound factory. Text→SFX via ElevenLabs, then de-silence +
  peak-normalize so clips are drop-in. Python CLI (`sfx.py` + spec JSON).

Start at [`AI_CALLER_LANDING.md`](AI_CALLER_LANDING.md) to route to the right one.

## Design principle

One umbrella, three factories, **one calling model**: an AI caller places an
order (spec or skill invocation), the factory runs + validates, and only
**validated deliverables** are copied into the game repo. Nothing produced by a
factory lands under this umbrella — artifacts version with the game.

## Layout

```
AI_CALLER_LANDING.md     route here first
asset/   itf.py, pipeline/, docs/, examples/ …   (original git history)
story/   skills/, core/steps|craft|schemas/, adapters/
sound/   sfx.py, pipeline/, docs/, examples/
```

## Compatibility

`tools/game_asset_factory` and `tools/game_story_factory` are kept as symlinks
into `asset/` and `story/` for any caller still using the old paths. Remove when
no longer referenced.
