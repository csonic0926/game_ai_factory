# Floor Reference Pair Workflow

This document describes the **floor-only** reference-pair workflow.

Use this document when the run is about:

- `full` / `half` floor variants
- floor full↔half transform mode
- floor cleanup / validation / selection

For wall runs, use `docs/WALL_REFERENCE_PAIR_WORKFLOW.md`.

## Scope

Canonical floor references:

- `examples/workflow_references/floor_height_pair/floor_full_k_scaled.png`
- `examples/workflow_references/floor_height_pair/floor_half_k_scaled.png`

Floor runs typically use:

- `"variants": ["full", "half"]`
- or a single target variant such as `"variants": ["full"]`

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
   - `step_7_selection/`
   - `deliverables/`

Start review with:

- `artifact_status.json`
- then the matching `step_*` folder

Preferred artifact naming:

- PNG: `s<step>_<kind>.<variant>[.vXX_<cleanup_name>].png`
- JSON: `s<step>_<kind>.<variant>.json`

Examples:

- `s1_raw.full.png`
- `s3_cleanup.full.v01_conservative.png`
- `s7_selected.full.png`
- `deliverable.full.png`

## Background modes

The floor workflow supports:

- `transparent`
- `color_key`

When `background.mode = "color_key"`:

1. the raw floor image is generated
2. six cleanup variants are emitted
3. validation may read one fixed cleanup candidate as its baseline keyed image, but that choice is outside Step 3 itself
4. validation / selection compare those results against the canonical floor geometry

## Workflow stages

### 1. Prepare

```bash
python3 itf.py prepare-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json
```

This prepares:

- copied references under `refs/`
- `refs/reference_pair_sheet.png` for the full/half pair
- `request/request.json`
- prompt files such as `request/prompt_full.txt`

### 2. Generate

```bash
python3 itf.py generate-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json
```

Behavior:

- pair runs use one vertical reference sheet
  - upper reference = full
  - lower reference = half
- single-variant runs send only that variant's reference image
- transform mode sends:
  - image 1 = existing source floor tile
  - image 2 = target canonical floor reference

### 3. Validate

```bash
python3 itf.py validate-reference-pair \
  --run-root output/reference_pair_runs/pixel_grass_demo
```

Validation checks:

- canvas alignment to reference size when needed
- transparent-background silhouette presence
- silhouette IoU vs reference
- bbox drift vs reference
- for `full + half` runs: pair-height relationship

Preferred diagnostic artifacts:

- step 1 raw:
  - `step_1_raw/s1_raw.<variant>.png`
- step 3 cleanup pool:
  - `step_3_cleanup_pool/s3_cleanup.<variant>.vXX_<cleanup>.png`
  - `step_3_cleanup_pool/s3_cleanup.<variant>.json`
- validation layer:
  - `validation/validation.json`
  - `validation/overlay_<variant>.png`
  - `validation/diff_<variant>.png`

### 4. Select final cleanup variant

```bash
python3 itf.py select-reference-pair-variant \
  --run-root output/reference_pair_runs/pixel_grass_demo \
  --variant full
```

Selection behavior:

- cleanup variants are evaluated in fixed order:
  - `01_conservative`
  - `02_conservative_plus`
  - `03_balanced`
  - `04_balanced_plus`
  - `05_aggressive`
  - `06_aggressive_plus`
- if score rebounds by more than 10 points, later candidates are blocked

Preferred selection artifacts:

- `step_7_selection/s7_overlay.<variant>.vXX_<cleanup>.png`
- `step_7_selection/s7_normalized.<variant>.vXX_<cleanup>.png`
- `step_7_selection/s7_selected.<variant>.png`
- `step_7_selection/s7_selection.<variant>.json`
- `deliverables/deliverable.<variant>.png`

## Transform mode

Use transform mode when converting an already-approved floor tile into the opposite height.

Example:

```json
{
  "variants": ["full"],
  "conversion": {
    "mode": "transform",
    "source_variant": "half",
    "source_image": "/absolute/path/to/deliverables/deliverable.half.png"
  }
}
```

This mode is intended for:

- `half -> full`
- `full -> half`

It is **not** the identity-preserving path for same-height restyles.

## Status meanings

- `pass`
- `soft_fail`
- `hard_fail`
