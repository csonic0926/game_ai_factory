# Blender Workflow

## Goal

Use Blender to lock down geometry, camera, and silhouette before asking Gemini to generate final tile art.

## Core rule

Blender defines structure.
Gemini defines surface styling.
Validation checks that generated output still respects the Blender-defined structure.

## Scene organization

Use one factory-style scene with:

- fixed `IsoCamera`
- fixed light rig
- deterministic export collections
- deterministic object names

Do not tune camera framing per asset.

## Naming

Use stable object ids like:

- `001_floor_plain`
- `002_floor_half`
- `101_wall_straight`
- `201_stair_up`
- `301_prop_switch`

## Reference-pair role

For floor-height generation, the canonical pair is:

- `001_floor_plain` → full-height reference
- `002_floor_half` → half-height reference

Those Blender renders become the structural references sent to Gemini.

## Validation philosophy

A generated image is acceptable only if it preserves:

- camera angle
- silhouette
- bounding box placement
- full/half height relationship

That is why this repo keeps reference-pair validation as a first-class workflow.
