# Repository Plan

## Purpose

This document captures the current planning direction for `isometric_tile_factory` as an independent open-source repository.

The main goal is to keep the tool:

- independent from any game project
- callable by vibe-coding AI through stable CLI/file contracts
- focused on tile asset production rather than gameplay logic

## Product Direction

The repository is planned as:

- a Blender-backed tile asset factory
- able to produce either integrated atlas outputs or individual PNG outputs
- eventually able to support both isometric and regular square tiles
- eventually able to support built-in AI texture generation providers
- engine-agnostic at the core, with adapters kept separate

## Repository Boundary

### The repository should contain

- generic Blender automation
- projection-aware render workflows
- atlas and individual-output tooling
- metadata and validation tooling
- AI texture request/cache workflows
- generic documentation
- example scenes and example configs
- optional engine adapters that remain clearly separated

### The repository should not contain

- project-specific game code
- project-specific gameplay metadata
- project-specific art assets unless clearly marked as examples
- direct assumptions about one engine scene structure

## Working Name

Current working name:

- `isometric_tile_factory`

Note:

- the product direction is broader than isometric-only
- in planning terms, `isometric` should now be treated as one future projection mode, not the whole product identity

## Planning Areas

### 1. Runtime Policy

Status:

- baseline documented in `docs/SPEC.md`
- primary tested Blender baseline is 5.1.x
- Python dependency install uses `requirements.txt`

### 2. Config Schema

Status:

- baseline converged in `docs/SPEC.md`

Next planning adjustment:

- add `projection_mode`
- add `output_mode`
- add render/profile concepts that can cover both square and isometric production

### 3. Metadata Schema

Status:

- baseline fields are executable in the current pipeline

Current metadata already includes:

- `anchor_type`
- `footprint_width`
- `footprint_height`
- `height_class`
- `tags`
- `source_collection`
- `material_variant`
- `render_preset`

Next candidate fields:

- `projection_mode`
- `tile_shape`
- `render_profile`
- `material_slots`
- `texture_pack_status`

### 4. Output Model

Status:

- atlas and individual PNG outputs are both part of the intended product direction

Planning rule:

- atlas is one output product, not the only output product

### 5. Sample Fixtures

Status:

- minimal isometric sample fixture exists

Next planning adjustment:

- add a square-tile sample fixture in addition to the current sample

### 6. Validation

Status:

- config validation exists
- manifest validation exists
- Blender scene validation exists
- sample smoke/regression flow exists

Planning direction:

- validation should stay machine-readable and agent-friendly

### 7. AI Texture Product Loop

Status:

- local request/cache/sync/validate workflow exists
- provider-backed generation is not yet implemented

Planning direction:

- users should provide API keys through local `.env`
- the repository should eventually call supported providers directly
- first intended providers are:
  - `nano_banana`
  - `nano_banana_pro`

### 8. Adapter Boundary

Status:

- adapter boundary documented
- adapter folder reserved

Planning direction:

- keep the core pipeline engine-agnostic
- future adapters should consume core outputs, not redefine core semantics

### 9. CLI Shape

Status:

- `itf.py` is the main entrypoint

Planning direction:

- CLI should be designed as an AI-agent callable interface
- JSON/file outputs should remain stable and machine-friendly
- end-to-end orchestration commands are desirable

## Recommended Phase Plan

### Phase 0: Baseline Repository

Goal:

- independent repository
- working sample pipeline
- working smoke/regression flow

Status:

- largely completed

### Phase 1: Multi-Projection Core

Goal:

- support both isometric and regular square tiles
- support atlas output and individual PNG output as first-class products

Tasks:

- add `projection_mode`
- add square sample fixture
- add projection-aware render profiles
- expand regression coverage

### Phase 2: AI Texture Product Loop

Goal:

- complete the texture workflow as a true product feature

Tasks:

- stabilize request/pack schema
- support `.env` provider configuration
- add built-in calls for `nano_banana`
- add built-in calls for `nano_banana_pro`
- bind selected textures back into Blender materials

### Phase 3: Agent-Callable Orchestration

Goal:

- optimize the tool for vibe-coding AI usage

Tasks:

- keep CLI/file IO machine-friendly
- add higher-level orchestration commands
- document contract-first workflows

### Phase 4: Engine Adapters

Goal:

- map the core outputs into engine-specific import formats

Tasks:

- adapter skeletons
- Godot-first adapter path
