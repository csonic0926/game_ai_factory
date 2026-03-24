# Blender Workflow v1

## Purpose

This document defines how a Blender scene should be organized so it can work as a stable isometric asset factory.

The goal is not to build a beautiful presentation scene.
The goal is to build a repeatable production scene for batch rendering tiles and props.

## Core Rule

Treat the Blender file as a factory, not as a one-off render setup.

That means:

- fixed camera
- fixed light rig
- fixed anchor rules
- fixed naming rules
- deterministic output order

## Collection Layout

Recommended top-level collections:

- `Factory_Rig`
- `Factory_Reference`
- `Export_Floor`
- `Export_Walls`
- `Export_Stairs`
- `Export_Props`
- `Disabled_Archive`

### `Factory_Rig`

Contains:

- `IsoCamera`
- key light
- fill light
- optional rim light
- optional helper empties

### `Factory_Reference`

Contains non-render reference helpers:

- tile footprint guides
- height guides
- origin marker
- measurement helpers

Do not export objects from this collection.

### `Export_*`

Contains the actual assets to render.

Each object in these collections should be one export unit.

### `Disabled_Archive`

Contains old or experimental objects that should not be rendered.

## Camera Rules

Use a single fixed camera:

- name: `IsoCamera`
- type: `Orthographic`

The camera transform must remain fixed for the whole tileset.

Do not move the camera to fit individual assets.
Move and align the assets instead.

## Lighting Rules

Use one shared light rig for all exports.

Recommended structure:

- `KeyLight`
- `FillLight`
- optional `RimLight`

Lighting should be:

- readable
- soft enough for atlas use
- stable across all renders

Avoid:

- dramatic shadows
- per-object lighting tweaks
- strong environment color casts

## Origin and Grounding Rules

Every export object must follow the same grounding convention.

### Required rule

The object's ground contact should align with world origin.

In practice:

- the object sits on `Z = 0`
- the intended anchor is centered around `(0, 0, 0)`

### Examples

#### Floor tile

- tile base lies on `Z = 0`
- tile center aligns to origin

#### Wall

- wall base touches `Z = 0`
- wall footprint aligns to the tile guide

#### Prop

- the part that touches the floor aligns to origin
- do not offset by eye just to look nice in one shot

## Footprint Guides

Place reusable guides in `Factory_Reference`.

Recommended guides:

- `Guide_Tile_1x1`
- `Guide_Tile_2x1`
- `Guide_Tile_2x2`
- `Guide_Height_1`
- `Guide_Height_Half`

These guides help verify:

- footprint width
- footprint height
- wall placement
- stair alignment
- large prop bounds

They should not be part of the final render output.

## Naming Rules

Each export object should use:

`<order>_<category>_<name>`

Examples:

- `001_floor_plain`
- `002_floor_cracked`
- `101_wall_straight`
- `102_wall_corner_inner`
- `201_stair_up`
- `301_prop_switch`

Why:

- output order is stable
- atlas order is stable
- metadata remains deterministic

Recommended reserved ranges:

- `001-099` floor
- `101-199` wall
- `201-299` stair
- `301-399` prop

Leave gaps inside each range so new assets can be inserted later without renaming everything.

## Custom Properties

Recommended object custom properties:

### `rotation_mode`

Supported values:

- `none`
- `rotate_90`
- `rotate_360`

### `category`

Examples:

- `floor`
- `wall`
- `stair`
- `prop`

### `anchor_type`

Examples:

- `tile_center`
- `floor_contact`
- `wall_base`

For v1, only `rotation_mode` is required by the script.
The others are recommended for future metadata expansion.

Supported `rotation_mode` values for v1:

- `none`
- `rotate_90`
- `rotate_360`

Variant output order is always:

- `rot0`
- `rot90`
- `rot180`
- `rot270`

## Export Unit Rule

One object should represent one exported asset.

Good:

- one floor tile = one object
- one stair tile = one object
- one switch prop = one object

Avoid:

- grouping many unrelated assets into one mesh and expecting the script to split them

## Minimal Sample Scene

The repository sample scene should stay intentionally small.

Required export objects:

- `001_floor_plain`
- `101_wall_straight`
- `201_stair_up`
- `301_prop_switch`

Required non-export rig contents:

- `IsoCamera`
- `KeyLight`
- `FillLight`
- optional `RimLight`
- `Guide_Tile_1x1`
- `Guide_Height_1`

The sample scene is for regression checking, not for showing artistic range.

## Material Rules

Prefer a stable material slot structure.

Example material roles:

- `MAT_Base`
- `MAT_Detail`
- `MAT_Metal`
- `MAT_Glow`
- `MAT_Decal`

This makes later AI texture replacement easier.

Avoid random one-off material naming per object.

## Resolution Rules

Choose one default output resolution for a tileset run.

Examples:

- `256 x 256`
- `512 x 512`

Keep it consistent across all objects in the batch.

## Structural vs Prop Assets

It helps to think in two groups:

### Structural assets

- floor
- wall
- stair
- cliff
- gate frame

These must strictly obey footprint and anchor rules.

### Hero props

- switch
- chest
- shrine
- crystal
- statue

These can be more visually expressive, but must still obey the floor contact rule.

## Recommended Minimum Test Set

Before scaling up, validate the workflow with five objects:

- `001_floor_plain`
- `101_wall_straight`
- `102_wall_corner_inner`
- `201_stair_up`
- `301_prop_switch`

If these render correctly and consistently, the workflow is viable.

## Validation Checklist

For each new asset, verify:

- is the ground contact correct?
- is the footprint within the intended guide?
- does rotation keep the object centered?
- does lighting match the rest of the batch?
- does the exported order stay stable?
- does the name follow the naming rule?

## Recommended Human Workflow

1. Put the object in the correct `Export_*` collection.
2. Align it to the origin and ground plane.
3. Set its object name.
4. Set `rotation_mode`.
5. Assign standard materials.
6. Run batch render.
7. Review the exported png, manifest, and atlas.

## Future Extensions

Later versions can add:

- automatic anchor validation
- footprint metadata
- material variant swapping
- AI texture injection
- engine adapters such as Godot import helpers
