# Wall Reference Pair Workflow

This document describes the **wall-only** reference-pair workflow.

Use this document when the run is about:

- `left` / `right` wall variants
- `1u` / `2u` wall references
- wall preprocessing gate
- wall source eligibility
- wall mapping
- wall selection

For floor runs, use `docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md`.

## Scope

Canonical wall references:

- `1u left -> examples/golden/sample_factory/images/101_wall_straight_rot90.png`
- `1u right -> examples/golden/sample_factory/images/101_wall_straight_rot0.png`
- `2u left -> examples/golden/sample_factory/images/102_wall_straight_2u_rot90.png`
- `2u right -> examples/golden/sample_factory/images/102_wall_straight_2u_rot0.png`

Canonical handedness:

- `left wall -> rot90`
- `right wall -> rot0`

## Diagnostic artifact contract

Each run keeps both:

1. legacy runtime folders for compatibility
   - `generated/`
   - `processed/`
   - `validation/`
   - `selection/`
   - `final/`
2. step-oriented diagnostic folders for review
   - `step_1_raw/`
   - `step_2_keyed_default/`
   - `step_3_cleanup_pool/`
   - `step_4_gate/`
   - `step_5_source/`
   - `step_6_mapping/`
   - `step_7_selection/`
   - `deliverables/`

Start review with:

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
- `s5_source.left.json`
- `s6_mapped.left.v01_conservative.png`
- `s7_selected.left.png`
- `deliverable.left.png`

## Background mode

Wall runs are typically debugged in `color_key` mode:

1. raw wall image
2. keyed default output
3. six cleanup variants
4. preprocessing gate
5. source eligibility
6. canonical mapping
7. final-fit selection

## Helper command

```bash
python3 itf.py generate-wall-reference-pair
python3 itf.py generate-wall-reference-pair --height 2
python3 itf.py generate-wall-reference-pair --height 2 --variant left
python3 itf.py generate-wall-reference-pair --variant right
```

Rules:

- defaults to both `left + right`
- `--height 1` uses `101_wall_straight`
- `--height 2` uses `102_wall_straight_2u`
- omit `--variant` for both sides
- `--variant left` or `--variant right` for one side

## Prompt contract

For wall specs, geometry should come from:

- the supplied canonical wall reference image
- structured wall metadata:
  - `selector_profile = "wall"`
  - `wall_side`
  - `height_units`
  - `reference_rotation`

Keep prompt parts focused on:

- style
- material
- decoration
- negative constraints

Avoid restating:

- handedness
- occupied half
- contact edge
- mirror rules

## Workflow stages

### 1. Prepare

```bash
python3 itf.py prepare-reference-pair \
  --spec examples/reference_pair_workflow/pixel_stone_wall_demo.spec.json
```

Wall-specific behavior:

- left/right names are preserved end-to-end
- wall runs do **not** use the shared pair sheet as the generation input
- each wall variant uses its own canonical reference image

### 2. Generate

```bash
python3 itf.py generate-reference-pair \
  --spec examples/reference_pair_workflow/pixel_stone_wall_demo.spec.json
```

The wall pair sheet may still be written as a debug artifact, but generation should use the per-variant canonical wall reference.

### 3. Validate and gate

```bash
python3 itf.py validate-reference-pair \
  --run-root output/reference_pair_runs/pixel_stone_wall_demo
```

#### Wall preprocessing gate

For wall runs, validation first answers:

> does at least one keyed cleanup candidate leave behind a usable silhouette?

A candidate is considered usable only if it:

- has an opaque silhouette bbox
- does not fill the whole canvas as foreground
- does not fail top-boundary key-color contamination checks

If no keyed candidate is usable:

- wall variant is marked `hard_fail`
- preprocessing gate records failure
- selector / mapping is skipped for that attempt

Preferred step artifacts:

- step 1 raw:
  - `step_1_raw/s1_raw.<variant>.png`
- step 2 keyed default:
  - `step_2_keyed_default/s2_keyed_default.<variant>.png`
  - `step_2_keyed_default/s2_keyed_default.<variant>.json`
- step 3 cleanup pool:
  - `step_3_cleanup_pool/s3_cleanup.<variant>.vXX_<cleanup>.png`
  - `step_3_cleanup_pool/s3_cleanup.<variant>.json`
- step 4 preprocessing gate:
  - `step_4_gate/s4_gate.<variant>.json`
  - `step_4_gate/s4_gate_pass_example.<variant>.png`
  - `step_4_gate/s4_gate_fail_example.<variant>.png`

### 4. Source eligibility

This step answers:

> which gated candidates are still trustworthy enough as wall sources?

Preferred artifacts:

- `step_5_source/s5_source.<variant>.json`
- `step_5_source/s5_source.<variant>.vXX_<cleanup>.png`

Interpretation:

- `source_*` failures mean the keyed candidate itself was not a good enough source

### 5. Canonical mapping

This step writes the mapped wall candidate that later selection will score.

Preferred artifacts:

- `step_6_mapping/s6_mapped.<variant>.vXX_<cleanup>.png`
- `step_6_mapping/s6_mapping.<variant>.json`

Interpretation:

- this is the mapped game-iso wall candidate
- it is **not yet** the final deliverable

### 6. Final-fit selection

```bash
python3 itf.py select-reference-pair-variant \
  --run-root output/reference_pair_runs/pixel_stone_wall_demo \
  --variant left
```

Selection behavior:

- cleanup variants are evaluated in fixed order
- score rebound can block later candidates
- selection should be interpreted only after preprocessing gate has passed

Preferred artifacts:

- `step_7_selection/s7_overlay.<variant>.vXX_<cleanup>.png`
- `step_7_selection/s7_normalized.<variant>.vXX_<cleanup>.png`
- `step_7_selection/s7_selected.<variant>.png`
- `step_7_selection/s7_selection.<variant>.json`
- `deliverables/deliverable.<variant>.png`

Interpretation:

- `final_*` failures mean preprocessing/source survived, but the mapped result still missed the canonical wall target

## Triage order

When a wall run looks wrong, inspect in this order:

1. `artifact_status.json`
2. `step_4_gate/`
3. `step_5_source/`
4. `step_6_mapping/`
5. `step_7_selection/`
6. `deliverables/`

If step 4 fails, debug key-color cleanup first.  
Do **not** start from mapping.
