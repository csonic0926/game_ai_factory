# Sample Scene

## Purpose

`examples/sample_factory.blend` is the canonical Blender fixture for this repo.

It exists to provide:

- stable render references
- stable camera + silhouette geometry
- a small validation target for the CLI

## Required top-level collections

- `Factory_Rig`
- `Factory_Reference`
- `Export_Floor`
- `Export_Walls`
- `Export_Stairs`
- `Export_Props`
- `Disabled_Archive`

## Required rig contents

Inside `Factory_Rig`:

- `IsoCamera`
- `KeyLight`
- `FillLight`
- optional `RimLight`

Inside `Factory_Reference`:

- `Guide_Tile_1x1`
- `Guide_Tile_2x1`
- `Guide_Height_1`
- `OriginMarker`

These reference helpers must not render.

## Required sample export objects

- `001_floor_plain`
- `002_floor_half`
- `101_wall_straight`
- `102_wall_straight_2u`
- `201_stair_up`
- `301_prop_switch`

The two floor objects are especially important because they define the canonical full/half pair used by the floor reference-pair workflow.

See:

- `docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md`

## Validation command

```bash
python3 itf.py validate \
  --scene examples/sample_factory.blend \
  --config examples/config.json \
  --sample-scene
```

## Rule

Prefer keeping floor reference variants in this one shared scene instead of splitting them across multiple `.blend` files.
