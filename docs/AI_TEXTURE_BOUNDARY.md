# AI Texture Integration Boundary v1

## Purpose

This file defines where AI-assisted texture generation may connect to the repository without becoming part of the current core render contract.

v1 does not implement AI texture generation.

It only defines the boundary so later work stays modular.

## Current Non-Goals

The core pipeline does not currently do any of the following:

- prompt generation
- image model invocation
- texture upscaling
- texture inpainting
- texture selection UX
- automatic material graph authoring

## Future Integration Point

AI texture work should happen before the render stage and feed Blender materials through stable inputs.

High-level flow:

1. define texture request
2. generate candidate images
3. cache the generated outputs
4. approve or select a variant
5. bind the chosen texture variant to Blender material inputs
6. render through the existing pipeline

## Proposed Stable Concepts

### Material slot naming

Reserve stable names such as:

- `base_color`
- `normal`
- `orm`
- `emissive`

### Texture cache layout

Recommended future location:

- `texture_cache/<asset_or_material>/<variant>/`

### Variant identity

Reserve the core metadata field:

- `material_variant`

This field is already part of the core manifest contract and may later be used to distinguish:

- handcrafted
- ai_v1
- ai_v2
- painted_over

### Render preset identity

Reserve the core metadata field:

- `render_preset`

This may later distinguish:

- default
- daytime
- nighttime
- stylized_flat

## Boundary Rule

AI texture systems may prepare inputs for materials, but they should not directly redefine:

- atlas ordering
- object naming
- rotation rules
- manifest structure ownership

The existing render and atlas pipeline should stay usable even when AI texture tooling is absent.
