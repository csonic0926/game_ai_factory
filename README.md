# isometric_tile_factory

Blender-first isometric tile factory for **reference-pair generation, validation, and final selection** of floor and wall tiles.

## Use this workflow

For almost all tile-art work, use the **reference-pair workflow**.

Main commands:

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

## Workflow docs

Use these docs as the real workflow entry points:

- `/Users/hunglingki/git_projects/tools/isometric_tile_factory/docs/REFERENCE_PAIR_WORKFLOW.md`
- `/Users/hunglingki/git_projects/tools/isometric_tile_factory/docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md`
- `/Users/hunglingki/git_projects/tools/isometric_tile_factory/docs/WALL_REFERENCE_PAIR_WORKFLOW.md`

## What to inspect first in a run

Start with:

- `artifact_status.json`

Then inspect the relevant step folder:

- `step_1_raw/`
- `step_3_cleanup_pool/`
- `step_4_gate/`
- `step_6_mapping/`
- `step_7_selection/`
- `deliverables/`

## Runtime

- Blender 4.5.x LTS on macOS Apple Silicon
- Python 3.11+

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Other CLI

If needed:

```bash
python3 itf.py --help
```
