# isometric_tile_factory

Blender-first isometric tile factory for isometric floor and wall tile production.

The repository has two primary workflows:

1. **Reference generation from Blender**
   - render canonical reference images
   - define the target camera and silhouette
   - provide stable geometric input for downstream image generation
2. **Gemini/Nano Banana tile generation**
   - send the canonical references to the model
   - receive styled tile images
   - remove chroma-key backgrounds when configured
   - validate generated geometry against the canonical references
   - select a normalized final export

## Main workflow

Use the reference-pair workflow when the objective is to generate final tile art from Gemini/Nano Banana while preserving the Blender-defined geometry.

Primary commands:

- `prepare-reference-pair`
- `generate-reference-pair`
- `validate-reference-pair`
- `select-reference-pair-variant`

See:

- `docs/REFERENCE_PAIR_WORKFLOW.md` — workflow index / router
- `docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md` — floor-only workflow
- `docs/WALL_REFERENCE_PAIR_WORKFLOW.md` — wall-only workflow
- `docs/BLENDER_WORKFLOW.md`
- `docs/SAMPLE_SCENE.md`

### Diagnostic artifact convention

Reference-pair runs now keep both:

- legacy runtime folders for compatibility:
  - `generated/`
  - `processed/`
  - `validation/`
  - `selection/`
  - `final/`
- step-oriented diagnostic folders for review:
  - `step_1_raw/`
  - `step_2_keyed_default/`
  - `step_3_cleanup_pool/`
  - `step_4_gate/`
  - `step_5_source/`
  - `step_6_mapping/`
  - `step_7_selection/`
  - `deliverables/`

Start run triage with:

- `artifact_status.json`
- then the corresponding `step_*` folder

Preferred artifact naming:

- PNG: `s<step>_<kind>.<variant>[.vXX_<cleanup_name>].png`
- JSON: `s<step>_<kind>.<variant>.json`

Examples:

- `s1_raw.left.png`
- `s2_keyed_default.left.png`
- `s3_cleanup.left.v01_conservative.png`
- `s4_gate.left.json`
- `s6_mapped.left.v01_conservative.png`
- `s7_selected.left.png`
- `deliverable.left.png`

## Core CLI

```bash
python3 itf.py --help
```

Available commands:

- `validate`
- `render`
- `build-atlas`
- `inspect-manifest`
- `create-sample-scene`
- `sample-regression`
- `smoke-sample`
- `prepare-reference-pair`
- `generate-reference-pair`
- `generate-wall-reference-pair`
- `validate-reference-pair`

## Runtime

- Blender 4.5.x LTS on macOS Apple Silicon is the current stable baseline
- Python 3.11+

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Canonical sample scene

Stable fixture:

- `examples/sample_factory.blend`

Canonical floor reference pair:

- `001_floor_plain` = full-height reference
- `002_floor_half` = half-height reference

Current sample reference-pair specs point at manually corrected scaled references:

- `examples/workflow_references/floor_height_pair/floor_full_k_scaled.png`
- `examples/workflow_references/floor_height_pair/floor_half_k_scaled.png`

This allows the Gemini-generation workflow to use artist-adjusted framing instead of the raw Blender render when needed.

Canonical wall reference pair example:

- `examples/golden/sample_factory/images/101_wall_straight_rot0.png`
- `examples/golden/sample_factory/images/101_wall_straight_rot90.png`

Canonical handedness mapping for 1u walls:

- `left wall` -> `101_wall_straight_rot90.png`
- `right wall` -> `101_wall_straight_rot0.png`

Canonical 2-unit wall reference pair example:

- `examples/golden/sample_factory/images/102_wall_straight_2u_rot0.png`
- `examples/golden/sample_factory/images/102_wall_straight_2u_rot90.png`

Canonical handedness mapping for 2u walls:

- `left wall` -> `102_wall_straight_2u_rot90.png`
- `right wall` -> `102_wall_straight_2u_rot0.png`

## Low-level Blender commands

Validate the sample scene:

```bash
python3 itf.py validate \
  --scene examples/sample_factory.blend \
  --config examples/config.json \
  --sample-scene
```

Render the sample scene:

```bash
python3 itf.py render --scene examples/sample_factory.blend --config examples/config.json
```

## Reference-pair workflow

Floor and wall workflow docs are now intentionally split.

Use:

- `docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md` for:
  - `full` / `half` floor runs
  - transform mode
  - floor validation / selection
- `docs/WALL_REFERENCE_PAIR_WORKFLOW.md` for:
  - `left` / `right` wall runs
  - wall preprocessing gate
  - wall source eligibility
  - wall mapping / selection

Keep `docs/REFERENCE_PAIR_WORKFLOW.md` as the shared router / index only.

### Common reference-pair commands

```bash
python3 itf.py prepare-reference-pair --spec /absolute/path/to/spec.json
python3 itf.py generate-reference-pair --spec /absolute/path/to/spec.json
python3 itf.py validate-reference-pair --run-root /absolute/path/to/run_root
python3 itf.py select-reference-pair-variant --run-root /absolute/path/to/run_root --variant full
```

Wall helper:

```bash
python3 itf.py generate-wall-reference-pair
python3 itf.py generate-wall-reference-pair --height 2
python3 itf.py generate-wall-reference-pair --height 2 --variant left
python3 itf.py generate-wall-reference-pair --variant right
```

### Shared prompt rule

Reference images are the geometry source of truth.

Prefer structured prompt parts:

- `prompt_parts.style`
- `prompt_parts.material`
- `prompt_parts.decoration`
- `prompt_parts.negative_constraints[]`

Avoid geometry prose that restates canonical structure already encoded by the references.

### Shared provider note

For a real Gemini/Nano Banana run:

1. set `provider.name` to `nano_banana` or `nano_banana_pro`
2. provide `GEMINI_API_KEY` in process env or this repo's `.env`
3. run the same `generate-reference-pair` command

If this factory is called from another repo, export the caller repo's key into the current process env before invoking `itf.py`.

### Shared diagnostics

Use `artifact_status.json` first, then inspect the matching `step_*` folder.

Primary step-oriented folders:

- `step_1_raw/`
- `step_2_keyed_default/`
- `step_3_cleanup_pool/`
- `step_4_gate/` when the workflow has that step
- `step_5_source/` when the workflow has that step
- `step_6_mapping/` when the workflow has that step
- `step_7_selection/`
- `deliverables/`

## Regression

Refresh the committed baseline:

```bash
python3 itf.py sample-regression --update
```

Verify current output against the baseline:

```bash
python3 itf.py sample-regression
```

Run the sample smoke flow:

```bash
python3 itf.py smoke-sample
```

## Direction

This repository is intentionally no longer organized around:

- AI texture cache orchestration
- square-mode product surfaces
- generic external orchestration contracts

It is organized around:

- Blender-generated canonical references
- Gemini-driven tile generation
- reference-based geometric validation
