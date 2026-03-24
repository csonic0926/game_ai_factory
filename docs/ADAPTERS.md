# Engine Adapter Boundary

## Purpose

This file defines how engine-specific integration should attach to the repository without changing the core contract.

The core pipeline should remain engine-agnostic.

## Core Pipeline Owns

- Blender scene validation
- render PNG generation
- `manifest.json`
- AI texture request/pack metadata
- atlas PNG generation
- `tileset.json`

## Core Metadata Contract

The adapter-facing metadata currently includes:

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

## Adapter Responsibilities

An engine adapter may:

- map core metadata into engine import formats
- create engine-specific atlas or tileset resources
- consume AI texture pack state if needed
- transform anchor or footprint values into engine coordinates
- write engine-side helper files

An engine adapter must not:

- redefine Blender naming policy
- redefine atlas ordering policy
- mutate the core manifest schema in-place
- require game-specific logic inside the core pipeline

## Recommended Layout

Future engine-specific code should live under:

- `adapters/`

Suggested structure:

- `adapters/godot/`
- `adapters/<engine_name>/`

## Adapter Inputs

Primary inputs:

- `manifest.json`
- `tileset.json`
- atlas PNG

Optional future inputs:

- AI texture cache metadata

## Stability Rule

Core metadata meanings should change slowly.

If a future adapter needs more information, prefer:

1. adding a new core metadata field
2. versioning adapter output

Do not overload existing field meanings per engine.
