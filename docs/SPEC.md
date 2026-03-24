# isometric_tile_factory v1

## Goal

Create a generic pipeline that renders Blender tiles and props into 2D isometric assets with stable output ordering.

## Scope

v1 includes:

- fixed orthographic camera workflow
- collection and object based batch render
- rotation variants
- manifest export
- atlas assembly
- metadata export

v1 does not include:

- AI image generation
- automatic Godot TileSet import
- background removal
- procedural map generation

## Core Principles

1. Geometry correctness comes from 3D.
2. Camera and lighting remain fixed.
3. Output ordering must be deterministic.
4. Metadata must be stable enough for engine adapters.

## Supported Runtime Baseline

- Blender: 5.1.x primary tested baseline for v1
- Python: 3.11+
- Python dependency install: `requirements.txt`

Version compatibility outside the primary tested setup is not part of the v1 contract.

## Config Schema v1

This is the repository-level config contract to stabilize first.

### Required keys

- `tileset_name`: string
- `output_root`: string
- `export_collections`: array of strings
- `camera_name`: string

### Optional keys

- `default_rotation_mode`: string, default `none`
- `render_resolution.width`: integer, default `256`
- `render_resolution.height`: integer, default `256`
- `atlas.columns`: integer, default `8`
- `atlas.padding`: integer, default `0`

### Removed from v1 contract

These fields are intentionally not part of the stable v1 schema:

- `rotation_step_degrees`
- `atlas.tile_width`
- `atlas.tile_height`

Reason:

- rotation variants are controlled by object `rotation_mode`
- atlas cell size is derived from rendered image size
- v1 uses one fixed render canvas for all atlas cells

### Canonical example

```json
{
  "tileset_name": "example_tileset",
  "output_root": "output",
  "export_collections": [
    "Export_Floor",
    "Export_Walls",
    "Export_Stairs",
    "Export_Props"
  ],
  "camera_name": "IsoCamera",
  "default_rotation_mode": "none",
  "render_resolution": {
    "width": 256,
    "height": 256
  },
  "atlas": {
    "columns": 8,
    "padding": 0
  }
}
```

### Validation rules

- missing required keys: hard error
- unknown top-level keys: warning for now, hard error after validator lands
- empty `export_collections`: hard error
- non-positive render width or height: hard error
- non-positive atlas columns: hard error
- negative atlas padding: hard error
- unsupported `default_rotation_mode`: hard error

## Metadata Schema v1

The pipeline produces:

- `manifest.json` after render
- `tileset.json` after atlas assembly

### `manifest.json`

Top-level fields:

- `tileset_name`
- `entries`

Each manifest entry includes:

- `id`
- `name`
- `source_object`
- `category`
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

### `tileset.json`

Top-level fields:

- `tileset_name`
- `atlas_path`
- `tile_width`
- `tile_height`
- `columns`
- `rows`
- `padding`
- `entries`

Each atlas entry includes all manifest fields plus:

- `atlas_index`
- `atlas_column`
- `atlas_row`
- `atlas_x`
- `atlas_y`

## Asset Naming

Recommended object naming:

- `001_floor_plain`
- `002_floor_cracked`
- `101_wall_straight`
- `102_wall_corner_inner`
- `201_stair_up`
- `301_prop_switch`

Recommended suffixes for generated variants:

- `_rot0`
- `_rot90`
- `_rot180`
- `_rot270`

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

This is a strict v1 policy.

### Ordering source

Atlas order is determined only by:

1. the configured export collection scan result
2. filtered eligible mesh objects
3. final lexical sort by full object name
4. per-object rotation expansion in fixed order

### Stability rules

- object names are the stable ordering key
- numeric prefixes are required
- renaming an object changes atlas order and is a breaking content change
- adding a new object can shift later atlas indices if its sort position is earlier
- therefore, numeric order ranges should be left with gaps for future insertion

### Recommended numeric ranges

- `001-099`: floor
- `101-199`: wall
- `201-299`: stair
- `301-399`: prop
- `900-999`: temporary or test objects, not for committed sample outputs

### Rotation expansion rule

Generated variants always append after the base object in this order:

- `rot0`
- `rot90`
- `rot180`
- `rot270`

The allowed subset is controlled by `rotation_mode`:

- `none` -> `rot0`
- `rotate_90` -> `rot0`, `rot90`
- `rotate_360` -> `rot0`, `rot90`, `rot180`, `rot270`

### Atlas cell policy

- one render = one atlas cell
- all cells share one identical size
- cell size equals `render_resolution`
- no trim-to-content in v1
- no per-entry crop in v1
- transparent background is the default render behavior
- atlas padding is uniform between cells

## Git and Output Policy

Generated runtime output is not part of the default committed working set.

Ignored by default:

- `output/`
- Python cache files
- Blender backup files such as `.blend1`

Committed as the regression baseline:

- `examples/sample_factory.blend`
- `examples/golden/sample_factory/images/*.png`
- `examples/golden/sample_factory/metadata/*.json`
- `examples/golden/sample_factory/baseline_summary.json`

Regression flow:

1. generate sample scene
2. render sample outputs
3. build atlas
4. update or verify the committed sample baseline

Commands:

```bash
python3 itf.py create-sample-scene
python3 itf.py render --scene examples/sample_factory.blend --config examples/config.json
python3 itf.py build-atlas --manifest output/metadata/manifest.json --out output/atlas/tileset.png
python3 itf.py sample-regression
```

One-command smoke check:

```bash
python3 itf.py smoke-sample
```

## Sample Factory Scene Contract

The repository should keep one minimal sample factory scene as a validation fixture.

Required contents:

- `IsoCamera`
- one fixed light rig
- `Factory_Reference` collection
- `Export_Floor` collection with one floor tile
- `Export_Walls` collection with one wall tile
- `Export_Stairs` collection with one stair tile
- `Export_Props` collection with one prop

Required sample asset names:

- `001_floor_plain`
- `101_wall_straight`
- `201_stair_up`
- `301_prop_switch`

Purpose of the sample scene:

- verify naming and ordering rules
- verify anchor and grounding rules
- verify render output shape
- verify manifest and atlas metadata
- serve as the smallest regression fixture for the repo

## Blender Expectations

The Blender scene should contain:

- a fixed orthographic isometric camera
- a fixed light rig
- exportable objects grouped by collection
- objects centered around a common anchor rule

### Recommended metadata-bearing custom properties

Objects may define:

- `rotation_mode`
- `anchor_type`
- `footprint_width`
- `footprint_height`
- `height_class`
- `tags`
- `material_variant`
- `render_preset`

## Pipeline Stages

1. Read config.
2. Find export collections.
3. Enumerate eligible objects.
4. Render each object and each required rotation.
5. Write `manifest.json`.
6. Assemble atlas.
7. Write atlas metadata.

## Engine Adapter Boundary

This tool should remain engine-agnostic.

Any Godot-specific import logic should live in a later adapter layer.

See:

- `docs/ADAPTERS.md`

## AI Texture Boundary

AI texture work is outside the current v1 render contract.

See:

- `docs/AI_TEXTURE_BOUNDARY.md`
