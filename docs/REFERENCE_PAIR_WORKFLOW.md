# Reference Pair Workflow

This file is now a **router / index**.

The repository no longer treats floor and wall as one shared workflow document.

Use:

- `docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md` for:
  - `full` / `half` floor runs
  - floor transform mode
  - floor validation / selection
- `docs/WALL_REFERENCE_PAIR_WORKFLOW.md` for:
  - `left` / `right` wall runs
  - wall preprocessing gate
  - wall source eligibility
  - wall mapping / selection

## Shared command surface

The core CLI entry points are still:

- `prepare-reference-pair`
- `generate-reference-pair`
- `validate-reference-pair`
- `select-reference-pair-variant`
- `generate-wall-reference-pair`

## Shared diagnostic convention

Both floor and wall runs use the same high-level artifact convention:

- legacy runtime folders are kept for compatibility:
  - `generated/`
  - `processed/`
  - `validation/`
  - `selection/`
  - `final/`
- step-oriented folders are the preferred diagnostic interface:
  - `step_1_raw/`
  - `step_2_keyed_default/`
  - `step_3_cleanup_pool/`
  - `step_4_gate/` when that step exists for the workflow
  - `step_5_source/` when that step exists for the workflow
  - `step_6_mapping/` when that step exists for the workflow
  - `step_7_selection/`
  - `deliverables/`

Start run review with:

- `artifact_status.json`
- then the workflow-specific document above
