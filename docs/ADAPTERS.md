# Engine Adapter Boundary v1

## Purpose

This file defines how engine-specific integration should attach to the core pipeline without changing the core contract.

The repository should keep rendering, manifest generation, atlas building, and metadata normalization engine-agnostic.

## Core Output Contract

The core pipeline owns:

- Blender scene validation
- render PNG generation
- `manifest.json`
- atlas PNG generation
- `tileset.json`

The core metadata fields are:

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
- transform anchor or footprint values into engine coordinates
- write engine-side helper files

An engine adapter must not:

- redefine Blender naming policy
- redefine atlas ordering policy
- mutate the core manifest schema in-place
- require game-specific logic inside the core pipeline

## Recommended Repository Layout

Future engine-specific code should live under:

- `adapters/`

Suggested structure:

- `adapters/godot/`
- `adapters/<engine_name>/`

## Extension Mechanism

The adapter input should be:

- `manifest.json`
- `tileset.json`
- atlas PNG

The adapter output should be written outside the core metadata files, for example:

- engine import manifests
- engine resource files
- engine sample scenes

## Stability Rule

Core metadata names should change slowly.

If a future adapter needs more information, prefer:

1. adding a new optional core metadata field
2. versioning the adapter output

Do not overload existing field meanings per engine.
