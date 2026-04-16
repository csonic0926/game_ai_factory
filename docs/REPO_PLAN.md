# Repository Plan

## Purpose

`isometric_tile_factory` exists to provide one stable production loop:

1. render canonical tile references from Blender
2. use those references to drive Gemini/Nano Banana tile generation
3. validate returned PNGs against the canonical reference silhouettes

## Repository Boundary

### Keep in repo

- Blender scene automation
- render + manifest validation
- sample scene creation
- atlas generation when useful for inspection
- reference-pair preparation/generation/validation
- example specs and canonical reference images
- concise docs for this workflow

### Do not optimize for

- generic multi-product orchestration
- AI texture cache systems
- square-mode product surfaces
- project-specific game runtime logic
- engine-specific behavior beyond thin adapters

## Current primary surfaces

- `python3 itf.py render`
- `python3 itf.py prepare-reference-pair`
- `python3 itf.py generate-reference-pair`
- `python3 itf.py validate-reference-pair`

## Planning rule

When adding or removing code, prefer the option that makes the reference-pair workflow simpler, more legible, and easier to verify.

When changing documentation, keep floor and wall workflow guidance separate:

- floor details belong in `docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md`
- wall details belong in `docs/WALL_REFERENCE_PAIR_WORKFLOW.md`
- `docs/REFERENCE_PAIR_WORKFLOW.md` should stay as the shared router / index
