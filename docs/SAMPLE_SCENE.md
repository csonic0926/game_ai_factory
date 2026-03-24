# Sample Scene Plan v1

## Purpose

This file defines the minimal Blender sample scene that the repository should maintain as its baseline fixture.

The sample scene exists to validate the factory contract, not to show a content library.

## Scene File Intent

Recommended path once added:

- `examples/sample_factory.blend`

The file should be small, fast to render, and safe to commit.

## Required Top-Level Collections

- `Factory_Rig`
- `Factory_Reference`
- `Export_Floor`
- `Export_Walls`
- `Export_Stairs`
- `Export_Props`
- `Disabled_Archive`

## Required Rig Contents

### `Factory_Rig`

- `IsoCamera`
- `SquareCamera`
- `KeyLight`
- `FillLight`
- optional `RimLight`

### `Factory_Reference`

- `Guide_Tile_1x1`
- `Guide_Tile_2x1`
- `Guide_Height_1`
- `OriginMarker`

Reference guides must not render.

## Required Export Objects

### `Export_Floor`

- `001_floor_plain`

### `Export_Walls`

- `101_wall_straight`

### `Export_Stairs`

- `201_stair_up`

### `Export_Props`

- `301_prop_switch`

## Required Object Rules

- all export objects are mesh objects
- all export objects sit on `Z = 0`
- all export objects follow the shared anchor rule
- all export objects use deterministic names
- each export object is one export unit

## Rotation Policy for Sample Scene

Use this minimal setup:

- `001_floor_plain`: `rotation_mode=none`
- `101_wall_straight`: `rotation_mode=rotate_90`
- `201_stair_up`: `rotation_mode=rotate_90`
- `301_prop_switch`: `rotation_mode=rotate_360`

This gives the sample enough coverage to test variant generation without making the fixture large.

## Validation Expectations

The sample scene should be enough to verify:

- camera lookup
- collection lookup
- deterministic object ordering
- category inference
- rotation expansion
- manifest generation
- atlas generation

Recommended validation command:

```bash
blender -b examples/sample_factory.blend -P blender/scripts/validate_scene.py -- --config examples/config.json --sample-scene=true
```

Square-path validation command:

```bash
blender -b examples/sample_factory.blend -P blender/scripts/validate_scene.py -- --config examples/config.square.json --sample-scene=true
```

Recommended generation command:

```bash
python3 itf.py create-sample-scene
```

## Out of Scope

The sample scene should not include:

- project-specific gameplay metadata
- engine-specific scene setup
- large texture libraries
- advanced shader experiments
- multiple art styles in one file
