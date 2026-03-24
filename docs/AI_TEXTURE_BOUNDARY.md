# AI Texture Integration Boundary

## Purpose

This file defines how AI-assisted texture generation fits into the repository product plan without collapsing the core render pipeline into provider-specific code.

The repository already has a local cache workflow.

Provider-backed generation is still a planned layer on top.

## Product Role

AI texture generation is not a side experiment.

It is planned as one of the main subsystems of the tool:

1. geometry/render pipeline
2. texture generation/cache pipeline
3. engine adapter pipeline

## Current Baseline

The repository currently supports:

- request file generation
- texture cache layout
- pack metadata sync
- cache validation
- cache inspection

The repository does not yet support:

- prompt generation
- provider API calls
- candidate ranking/selection UX
- automatic Blender material binding

## Provider Direction

Planned user-facing model:

- users pull or fork the repository
- users provide provider credentials through local `.env`
- the repository calls supported providers directly

Initial intended providers:

- `nano_banana`
- `nano_banana_pro`

This direction fits local-first open-source usage and AI-agent orchestration better than asking users to manually run a separate image generation stack.

## Integration Point

High-level flow:

1. define texture request
2. generate candidate images
3. cache generated outputs
4. approve or select a variant
5. bind the chosen variant to Blender material inputs
6. render through the existing pipeline

## Stable Concepts

### Material slots

Reserve stable slot names such as:

- `base_color`
- `normal`
- `orm`
- `emissive`

### Cache layout

Recommended root:

- `texture_cache/`

### Variant identity

Use core metadata fields:

- `material_variant`
- `render_preset`

## Boundary Rule

Provider integrations may:

- read local `.env`
- create or update files inside the texture cache
- update cache/pack state

Provider integrations should not:

- redefine atlas ordering
- redefine object naming
- redefine rotation rules
- redefine manifest ownership

The render and atlas pipeline must remain usable even when AI texture tooling is absent.

## Executable Workflow

See:

- `docs/AI_TEXTURE_WORKFLOW.md`
