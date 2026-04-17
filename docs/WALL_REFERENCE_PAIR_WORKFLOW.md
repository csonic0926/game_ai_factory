# Wall Reference Pair Workflow

This document describes the **wall-only** reference-pair workflow.

Use this document when the run is about:

- `left` / `right` wall variants
- `1u` / `2u` wall references
- wall preprocessing gate
- wall mapping
- wall verification

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
   - `step_3_cleanup_pool/`
   - `step_4_gate/`
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
- `s3_cleanup.left.v01_conservative.png`
- `s4_gate.left.json`
- `s5_source.left.json`
- `s6_mapped.left.v01_conservative.png`
- `s7_selected.left.png`
- `deliverable.left.png`

## Background mode

Wall runs are typically debugged in `color_key` mode:

1. raw wall image
2. six cleanup variants
3. preprocessing gate + least-destructive valid candidate pick
4. canonical mapping
5. mapping verification

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

#### Agent-assisted imagegen variant

When wall Step 1 is executed by Codex/imagegen rather than a repo-local provider:

1. set the spec provider to:
   - `provider.mode = "agent_handoff"`
   - `provider.name = "imagegen"`
2. run `prepare-reference-pair`
3. read `request/imagegen_handoff.json`
4. write one raw PNG per variant to:
   - `agent_handoff/step_1_raw/left.png`
   - `agent_handoff/step_1_raw/right.png`
5. run `generate-reference-pair` to ingest those Step 1 outputs and continue with Step 3+

### 3. Validate and gate

```bash
python3 itf.py validate-reference-pair \
  --run-root output/reference_pair_runs/pixel_stone_wall_demo
```

#### Wall preprocessing gate

For wall runs, validation first answers:

> does at least one keyed cleanup candidate leave behind a usable silhouette?

The preprocessing gate evaluates the six Step 3 cleanup candidates directly.

A candidate is considered usable only if it:

- has an opaque silhouette bbox
- does not fill the whole canvas as foreground
- does not fail the **four-corner / exterior-fill background-residue** check

The residue check is intended to:

- start from the four corners / exterior transparent region
- detect leftover key-colored pixels that still cling to the outside background
- avoid penalizing interior image colors that merely resemble the background color

If no keyed candidate is usable:

- wall variant is marked `hard_fail`
- preprocessing gate records failure
- mapping / verification is skipped for that attempt

Preferred step artifacts:

- step 1 raw:
  - `step_1_raw/s1_raw.<variant>.png`
- step 3 cleanup pool:
  - `step_3_cleanup_pool/s3_cleanup.<variant>.vXX_<cleanup>.png`
  - `step_3_cleanup_pool/s3_cleanup.<variant>.json`
- step 4 preprocessing gate:
  - `step_4_gate/s4_gate.<variant>.json`
  - `step_4_gate/s4_gate_pass_example.<variant>.png`
  - `step_4_gate/s4_gate_fail_example.<variant>.png`

The Step 4 gate now also chooses the **least-destructive valid candidate** by fixed cleanup order.

### 4. Canonical mapping

This step writes the mapped wall candidate from the Step 4 chosen cleanup image.

Preferred artifacts:

- `step_6_mapping/s6_mapped.<variant>.vXX_<cleanup>.png`
- `step_6_mapping/s6_mapping.<variant>.json`

Interpretation:

- this is the mapped game-iso wall candidate
- it is **not yet** the final deliverable

### 5. Mapping verification

```bash
python3 itf.py select-reference-pair-variant \
  --run-root output/reference_pair_runs/pixel_stone_wall_demo \
  --variant left
```

Behavior:

- Step 4 already chooses the cleanup candidate
- Step 7 now verifies whether the mapped result is game-iso correct
- no multi-candidate rebound / cutoff selector remains in the wall path

Preferred artifacts:

- `step_7_selection/s7_overlay.<variant>.vXX_<cleanup>.png`
- `step_7_selection/s7_normalized.<variant>.vXX_<cleanup>.png`
- `step_7_selection/s7_selected.<variant>.png`
- `step_7_selection/s7_selection.<variant>.json`
- `deliverables/deliverable.<variant>.png`

Interpretation:

- `final_*` failures mean cleanup succeeded, but the mapped result still missed the canonical wall target

## Triage order

When a wall run looks wrong, inspect in this order:

1. `artifact_status.json`
2. `step_4_gate/`
3. `step_6_mapping/`
4. `step_7_selection/`
5. `deliverables/`

If step 4 fails, debug key-color cleanup first.  
Do **not** start from mapping.
