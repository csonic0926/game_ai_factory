# game_asset_factory Spec

## Goal

Provide a Blender-backed factory for canonical isometric tile references, reference-validated image outputs, and engineering-spec-validated game prop assets.

## Primary product

The repo's primary tile product is a validated reference-driven tile generation workflow.

Workflow docs are split by tile family:

- `docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md`
- `docs/WALL_REFERENCE_PAIR_WORKFLOW.md`
- `docs/REFERENCE_PAIR_WORKFLOW.md` is now the shared router / index

Prop/object workflow is intentionally separate:

- `docs/PROP_ASSET_WORKFLOW.md`
- schema: `prop_asset_workflow_v1`
- case studies: IMT `flame_relay_brazier` and `field_cooking_campfire_pot`
- GPT Image prop mode: `provider.name=gpt_image`,
  `provider.mode=gpt_image_prop_color_key`,
  `background.mode=color_key`
- `gpt-image-2` does not support native transparent background; prop runs use flat `#FF00FF` / `#00FF00` source backgrounds plus cleanup scoring.
- `edit_from` prop states use the cleaned source-state PNG as an image reference; local CLIProxyAPI GPT Image edits are sent as JSON data-URL edit requests.

### Inputs

- a canonical Blender scene
- a reference-pair spec
- optional provider credentials depending on `provider.name`

## Public execution contract

The external order contract should distinguish:

- `provider` = backend / execution path
- `model` = concrete model used on that backend

Canonical provider backends:

- `mock`
- `gemini_cli`
- `cliproxyapi`
- `agent_handoff`

Current model support:

- `mock` -> `mock`
- `gemini_cli` -> `nano-banana-2`, `nano-banana-pro`
- `cliproxyapi` -> `gpt-image-2`
- `agent_handoff` -> `gpt-image-2`

Legacy provider aliases are still accepted for compatibility, but new callers should use the canonical provider/model split.

### Outputs

- prepared reference images
- prompt files
- generated tile PNGs
- validation JSON and overlays
- prop deliverable PNGs, `prop_asset_manifest.json`, `prop_asset_atlas.png`,
  `prop_asset_atlas_metadata.json`, `imt_prop_handoff.json`,
  `validation_summary.json`, `preview_sheet.png`

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
- `prepare-prop-assets`
- `generate-prop-assets`
- `validate-prop-assets`

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
