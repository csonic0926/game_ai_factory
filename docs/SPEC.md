# isometric_tile_factory Spec

## Goal

Provide a Blender-backed factory for canonical isometric tile references and reference-validated Gemini outputs.

## Primary product

The repo's primary product is a validated reference-driven tile generation workflow.

### Inputs

- a canonical Blender scene
- a reference-pair spec
- optional Gemini/Nano Banana provider credentials

### Outputs

- prepared reference images
- prompt files
- generated tile PNGs
- validation JSON and overlays

## Primary commands

- `validate`
- `render`
- `build-atlas`
- `inspect-manifest`
- `create-sample-scene`
- `sample-regression`
- `smoke-sample`
- `prepare-reference-pair`
- `generate-reference-pair`
- `validate-reference-pair`

## Canonical sample scene

- `examples/sample_factory.blend`

Important sample objects:

- `001_floor_plain`
- `002_floor_half`

## Non-goals for the current repo direction

- generic external orchestration contracts
- AI texture cache workflows
- square-mode product surfaces
- multiple parallel top-level workflows
