# isometric_tile_factory

## Goal

Create a Blender-backed tile asset factory that produces stable tile outputs with stable geometry shape.

## Product Direction

The repository is planned as:

- a tile asset factory callable by vibe-coding AI
- able to produce atlas outputs, individual PNG outputs, or both
- eventually able to support both isometric and regular square tiles
- eventually able to support built-in AI texture generation providers through local configuration
- engine-agnostic at the core

## Current Baseline Scope

The current baseline includes:

- fixed orthographic camera workflow
- collection and object based batch render
- projection-aware config via `projection_mode`
- rotation variants
- manifest export
- atlas assembly
- metadata export
- sample smoke/regression flow
- dual sample smoke orchestration for isometric + square fixtures
- AI texture cache workflow

The current baseline does not yet include:

- provider-backed AI image generation
- automatic engine import generation
- procedural map generation

## Core Principles

1. Geometry correctness comes from 3D.
2. Camera and lighting remain fixed within a render profile.
3. Output ordering must be deterministic.
4. Metadata must be stable enough for adapters and AI tooling.
5. CLI and file outputs should be stable enough for AI agents to call directly.

## Supported Runtime Baseline

- Blender: 5.1.x primary tested baseline
- Python: 3.11+
- Python dependency install: `requirements.txt`

## Config Schema Baseline

This is the current repository-level config contract.

### Required keys

- `tileset_name`
- `output_root`
- `export_collections`
- `camera_name`

### Optional keys

- `projection_mode`
- `output_mode`
- `render_profile`
- `render_profiles`
- `default_rotation_mode`
- `render_resolution.width`
- `render_resolution.height`
- `atlas.columns`
- `atlas.padding`

Current supported `projection_mode` values:

- `isometric`
- `square`

Current supported `output_mode` values:

- `png`
- `atlas`
- `both`

Current render-profile direction in baseline:

- config may select `render_profile`
- config may define reusable `render_profiles`
- the selected profile may resolve camera + projection + render resolution

Planned next expansion:

- `output_mode`
- render/profile settings that can cover both square and isometric production

## Metadata Schema Baseline

The pipeline produces:

- `manifest.json` after render
- `tileset.json` after atlas assembly

### Manifest entry fields

- `id`
- `name`
- `source_object`
- `category`
- `projection_mode`
- `tile_shape`
- `render_profile`
- `anchor_type`
- `footprint_width`
- `footprint_height`
- `height_class`
- `tags`
- `source_collection`
- `material_variant`
- `render_preset`
- `rotation`
- `file`
- `file_name`
- `width`
- `height`

### Atlas entry fields

Each atlas entry includes all manifest fields plus:

- `atlas_index`
- `atlas_column`
- `atlas_row`
- `atlas_x`
- `atlas_y`

### Planned next expansion

- `render_profile`
- `material_slots`
- `texture_pack_status`

## Output Products

The repository should treat these as first-class outputs:

- individual PNG renders
- atlas PNG
- metadata manifests
- AI texture request/pack metadata
- future engine-adapter outputs

Atlas output is important, but it is not the only intended product.

## Asset Naming

Required rule:

- exported object names must start with a zero-padded numeric prefix

Format:

- `<order>_<category>_<name>`

Examples:

- `001_floor_plain`
- `101_wall_straight`
- `201_stair_up`
- `301_prop_switch`

## Atlas Stability Policy

Atlas order is determined only by:

1. configured export collection scan result
2. filtered eligible mesh objects
3. lexical sort by full object name
4. per-object rotation expansion in fixed order

### Stability rules

- object names are the stable ordering key
- numeric prefixes are required
- renaming an object changes atlas order and is a breaking content change
- adding a new object can shift later atlas indices if its sort position is earlier

### Recommended numeric ranges

- `001-099`: floor
- `101-199`: wall
- `201-299`: stair
- `301-399`: prop

## Render Cell Policy

- one render = one output cell
- all cells share one identical size within a render profile
- current cell size equals `render_resolution`
- no trim-to-content in the baseline flow
- transparent background is the default render behavior

## Sample Fixture Contract

The repository should keep minimal sample fixtures for regression.

Current baseline fixture:

- one isometric sample scene

Planned next fixture:

- square config + square camera path on the shared sample scene, with its own regression baseline

## AI-Agent Callable Interface

The primary operational surface is the CLI plus stable file layout.

Design direction:

- commands should avoid interactive prompts
- outputs should remain machine-readable
- intermediate artifacts should have predictable paths
- higher-level orchestration commands are preferred when practical

## Git and Output Policy

Ignored by default:

- `output/`
- `texture_cache/`
- Python cache files
- Blender backup files such as `.blend1`

Committed as regression baseline:

- sample fixture scenes
- sample golden images
- normalized baseline metadata

## Related Design Documents

- `docs/REPO_PLAN.md`
- `docs/BLENDER_WORKFLOW.md`
- `docs/SAMPLE_SCENE.md`
- `docs/ADAPTERS.md`
- `docs/AI_TEXTURE_BOUNDARY.md`
- `docs/AI_TEXTURE_WORKFLOW.md`
