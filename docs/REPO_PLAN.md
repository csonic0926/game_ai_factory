# Repository Plan

## Purpose

This document captures the planning work that should follow when moving `isometric_tile_factory` into its own Codex project and repository.

The main goal is to prevent tool design decisions from being mixed back into a game project.

This file is intentionally focused on:

- repository setup
- missing planning items
- implementation phases
- validation needs
- future adapter boundaries

## Immediate Direction

This tool should move forward as its own standalone repository.

It should not continue evolving inside a game repository.

## Repository Boundary

### The new repository should contain

- generic Blender automation
- generic atlas and metadata tooling
- generic documentation
- example scenes and example configs
- optional engine adapters that remain clearly separated

### The new repository should not contain

- project-specific game code
- project-specific gameplay metadata
- project-specific art assets unless clearly marked as examples
- direct assumptions about one engine scene structure

## Recommended Repository Name

Suggested names:

- `isometric_tile_factory`
- `isometric-render-factory`
- `blender-isometric-tile-factory`

Current working name:

- `isometric_tile_factory`

## Required Planning Still Missing

These items should be resolved early in the new repository.

### 1. Blender Version Support Policy

Status:

- converged in `docs/SPEC.md`
- primary tested baseline is Blender 5.1.x

Define:

- minimum supported Blender version
- primary tested Blender version
- whether API compatibility with older versions matters

Recommended first pass:

- support one primary Blender version only
- add compatibility later if needed

### 2. Python Tooling Policy

Status:

- converged in `docs/SPEC.md`
- dependency file landed as `requirements.txt`

Define:

- minimum Python version
- dependency installation method
- whether a virtual environment is recommended

Recommended first pass:

- Python 3.11+
- dependencies in `requirements.txt`

### 3. Config Schema v1

Status:

- converged in `docs/SPEC.md`

The config needs a real schema, not just example fields.

Define:

- required keys
- optional keys
- default values
- validation errors

Missing fields to consider:

- light preset name
- transparent background toggle
- manifest output path
- per-category output folders
- naming conflict policy
- atlas packing options

### 4. Metadata Schema v1

Status:

- expanded in executable form in `pipeline/validation.py` and `blender/scripts/render_tiles.py`
- documented in `docs/SPEC.md`

The metadata contract should be stabilized early.

Current fields are not enough for future engine adapters.

Missing candidate fields:

- `anchor_type`
- `footprint_width`
- `footprint_height`
- `height_class`
- `tags`
- `source_collection`
- `material_variant`
- `render_preset`

### 5. Atlas Stability Policy

Status:

- converged in `docs/SPEC.md`

This is critical.

Define:

- what determines output order
- whether ordering is strictly name-based
- whether new assets are allowed to shift old atlas indices
- whether reserved numeric ranges are recommended

Strong recommendation:

- atlas order is driven by deterministic object naming
- numeric prefixes are required

### 6. Sample Factory Scene Plan

Status:

- converged in `docs/SAMPLE_SCENE.md`

The repository needs a minimal sample Blender scene for validation.

Minimum sample assets:

- one floor tile
- one wall tile
- one stair tile
- one prop
- camera rig
- light rig
- reference guides

### 7. Validation Rules

Status:

- converged in executable form via `pipeline/validation.py`
- Blender scene checks landed in `blender/scripts/validate_scene.py`

The repository needs validation tooling for authoring errors.

Candidate checks:

- duplicate object names
- unsupported object types in export collections
- missing camera
- missing collections
- invalid `rotation_mode`
- non-deterministic ordering
- missing render output folders
- missing material slots if required by policy

### 8. Render Output Policy

Status:

- converged in `docs/SPEC.md`

Define:

- fixed canvas size vs trim-to-content
- transparent padding policy
- whether crop is allowed
- whether all atlas cells must share one exact size

### 9. Material and AI Hook Boundary

Status:

- boundary documented in `docs/AI_TEXTURE_BOUNDARY.md`

Even if AI integration is not part of v1, the repository should reserve a place for it.

Need to define:

- material slot naming conventions
- texture input folder conventions
- generated texture cache policy
- variant naming conventions

### 10. Engine Adapter Boundary

Status:

- boundary documented in `docs/ADAPTERS.md`
- future adapter folder reserved as `adapters/`

Keep core pipeline engine-agnostic.

Need to define:

- core metadata contract
- adapter extension points
- where Godot-specific files should live

Recommended structure:

- core pipeline in root modules
- engine adapters in `adapters/`

### 11. CLI Shape

Status:

- converged in executable form via `itf.py`

The repository should define a proper CLI shape instead of only raw scripts.

Target commands:

- `render`
- `build-atlas`
- `validate`
- `inspect-manifest`

### 12. Git and Output Policy

Status:

- converged in `docs/SPEC.md`
- `.gitignore` added
- sample regression baseline landed under `examples/golden/sample_factory`

Define what should be committed.

Need decisions for:

- should `output/` be gitignored
- should sample renders be committed
- should example atlas files be committed
- should generated metadata snapshots be committed

Strong recommendation:

- generated output is ignored by default
- keep only tiny sample outputs if needed for docs

## Recommended Phase Plan

## Phase 0: Repository Bootstrap

Goal:

- create independent repository
- copy current skeleton
- define runtime versions
- add basic README and contribution notes

Tasks:

- initialize repo
- add `.gitignore`
- add `requirements.txt`
- add license choice
- add `docs/REPO_PLAN.md`
- add `docs/SPEC.md`
- add `docs/BLENDER_WORKFLOW.md`

## Phase 1: Stable Core Contracts

Goal:

- define the repository's long-lived interfaces

Tasks:

- formalize config schema
- formalize metadata schema
- formalize naming rules
- formalize atlas ordering policy
- formalize output folder policy

Deliverables:

- `docs/CONFIG_SCHEMA.md`
- `docs/METADATA_SCHEMA.md`
- `docs/ATLAS_POLICY.md`

## Phase 2: Blender Export Validation

Goal:

- make Blender export reliable enough for repeated use

Tasks:

- improve `render_tiles.py`
- support object custom properties cleanly
- validate collections and camera existence
- emit better errors
- add dry-run manifest inspection

Deliverables:

- stronger render script
- validation script

## Phase 3: Sample Factory Scene

Goal:

- prove the workflow in a minimal but complete way

Tasks:

- create sample `.blend`
- create minimal export collections
- create minimal assets
- confirm render output matches docs

Deliverables:

- sample scene
- sample manifest
- sample atlas

## Phase 4: Atlas and Metadata Hardening

Goal:

- make atlas generation stable and adapter-ready

Tasks:

- improve atlas builder
- support padding options
- support deterministic manifest consumption
- emit `tileset.json`
- document output guarantees

## Phase 5: Engine Adapter Layer

Goal:

- add optional adapters without polluting the core

Possible adapters:

- Godot
- Tiled
- generic JSON consumer

Important rule:

- adapters should consume metadata
- adapters should not redefine core render rules

## Phase 6: AI Material and Texture Hooks

Goal:

- connect image generation to a stable geometry pipeline

Possible tasks:

- texture import conventions
- material variant presets
- generated texture cache handling
- optional prompt-to-texture helper docs

This phase should happen after the core render and atlas flow is stable.

## Repository File Plan

Recommended additions for the new repository:

- `README.md`
- `requirements.txt`
- `.gitignore`
- `docs/SPEC.md`
- `docs/BLENDER_WORKFLOW.md`
- `docs/REPO_PLAN.md`
- `docs/CONFIG_SCHEMA.md`
- `docs/METADATA_SCHEMA.md`
- `docs/ATLAS_POLICY.md`
- `blender/scripts/render_tiles.py`
- `pipeline/build_atlas.py`
- `pipeline/validate_factory.py`
- `examples/config.json`
- `examples/sample_manifest.json`

## Risks To Watch

### Risk 1: Camera Drift

If camera settings are changed casually, output stops being consistent.

Mitigation:

- validate camera name and type
- document camera lock policy

### Risk 2: Atlas Index Drift

If ordering is not fully deterministic, engine-side references become fragile.

Mitigation:

- require numeric prefixes
- sort strictly by name

### Risk 3: Asset Anchoring Drift

If artists place meshes inconsistently, props will no longer align.

Mitigation:

- document origin rules
- add validation checks later

### Risk 4: Overcoupling To Godot

If the repository starts assuming Godot internals too early, it stops being reusable.

Mitigation:

- keep Godot import as a separate adapter

### Risk 5: AI Scope Creep

If AI texture generation is treated as part of the core too early, the base pipeline may stay unstable.

Mitigation:

- stabilize geometry/render/atlas first
- integrate AI after the core is dependable

## New Codex Project Handoff Checklist

When opening the new Codex project, start with this checklist:

- confirm repository root and name
- confirm Blender version
- confirm Python version
- decide whether `output/` is ignored
- copy current docs and scripts
- define config schema v1
- define metadata schema v1
- define atlas ordering policy
- decide sample scene scope
- decide whether adapters are in-scope for v1

## Recommended First Task In The New Project

The best first task is:

- formalize config and metadata schemas before adding more rendering features

That keeps the repository from drifting into ad hoc scripting.

## Recommended Second Task In The New Project

- build and validate a minimal sample Blender factory scene

That will expose the real gaps faster than adding more code in the abstract.
