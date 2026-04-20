# Reference Pair Workflow

This file is the **router**.

Use:

- `/Users/hunglingki/git_projects/tools/isometric_tile_factory/docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md` for `full` / `half` floor runs
- `/Users/hunglingki/git_projects/tools/isometric_tile_factory/docs/WALL_REFERENCE_PAIR_WORKFLOW.md` for `left` / `right` wall runs

## Shared commands

```bash
python3 itf.py prepare-reference-pair --spec /absolute/path/to/spec.json
python3 itf.py generate-reference-pair --spec /absolute/path/to/spec.json
python3 itf.py validate-reference-pair --run-root /absolute/path/to/run_root
python3 itf.py select-reference-pair-variant --run-root /absolute/path/to/run_root --variant full
```

Wall helper:

```bash
python3 itf.py generate-wall-reference-pair
```

## Shared run triage

Start with:

- `artifact_status.json`

Then inspect the relevant step folder:

- `step_1_raw/`
- `step_3_cleanup_pool/`
- `step_4_gate/` when that step exists
- `step_6_mapping/` when that step exists
- `step_7_selection/`
- `deliverables/`
