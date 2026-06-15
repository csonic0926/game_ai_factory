# AI caller landing

This is the first stop for an AI agent working in another repo that wants to
use `game_asset_factory`.

## Decide the path

| Caller need | Do this |
| --- | --- |
| Use an existing factory workflow and get PNG deliverables | Call the CLI from this repo with a spec file. |
| Re-skin an existing geometrically-correct tile/autotile set | Use `tile_reskin_workflow_v1`. |
| Generate engineering-validated prop/object sprites | Use `prop_asset_workflow_v1`. |
| Generate/validate floor or wall reference-pair tiles | Use `reference_pair_workflow_v1` or the wall helper. |
| Need the factory to add a capability, schema field, validator, adapter, or example | File a request in `requirement_from_other_repo/` using `REQUEST_TEMPLATE.md`. |

Do not file a cross-repo request if the existing CLI/specs already satisfy the
job. File a request only when the factory itself must change.

## Basic calling contract

Run commands from the factory repo:

```bash
cd /Users/hunglingki/git_projects/tools/game_asset_factory
python3 -m pip install -r requirements.txt
python3 itf.py --help
```

Use absolute paths in specs when the source repo and factory repo differ. Keep
source-repo output expectations in the spec when supported, for example
`target_project_folder` in prop specs.

For a safe offline smoke test, prefer `provider.name = "mock"` or the workflow's
`--provider mock` override. For real generation, use the provider/model contract
documented in `README.md`.

## Common workflows

### Prop/object assets

Use this when the target repo needs transparent game sprites with validated
canvas, anchor, alpha, manifest, and handoff metadata.

```bash
python3 itf.py generate-prop-assets \
  --spec examples/prop_asset_workflow/flame_relay_brazier_pair.spec.json

python3 itf.py validate-prop-assets \
  --run-root output/prop_asset_runs/imt_flame_relay_brazier_pair
```

Real provider examples:

```bash
python3 itf.py generate-prop-assets \
  --spec examples/prop_asset_workflow/flame_relay_brazier_pair.gpt_image.spec.json \
  --provider gpt_image

python3 itf.py generate-prop-assets \
  --spec examples/prop_asset_workflow/flame_relay_brazier_pair.gemini_pro.spec.json \
  --provider gemini_cli \
  --model nano-banana-pro
```

Inspect:

- `deliverables/*.png`
- `deliverables/prop_asset_manifest.json`
- `deliverables/validation_summary.json`
- `deliverables/preview_sheet.png`
- `deliverables/imt_prop_handoff.json` when present

Read more: [`docs/PROP_ASSET_WORKFLOW.md`](PROP_ASSET_WORKFLOW.md).

### Tile re-skin

Use this when the target repo already has geometrically-correct tiles/autotiles
and only needs a new material look while preserving connectivity.

```bash
python3 itf.py prepare-tile-reskin \
  --spec examples/tile_reskin_workflow/village_road.spec.json

python3 itf.py generate-tile-reskin \
  --spec examples/tile_reskin_workflow/village_road.spec.json

python3 itf.py generate-tile-reskin \
  --spec examples/tile_reskin_workflow/village_road.spec.json \
  --provider mock
```

Inspect the run's `deliverables/` folder and `artifact_status.json`.

Read more: [`docs/TILE_RESKIN_WORKFLOW.md`](TILE_RESKIN_WORKFLOW.md).

### Reference-pair floor/wall tiles

Use this when the target repo needs reference-guided floor or wall tile
generation and geometry validation.

```bash
python3 itf.py prepare-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json

python3 itf.py generate-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json

python3 itf.py validate-reference-pair \
  --run-root /absolute/path/to/run_root

python3 itf.py select-reference-pair-variant \
  --run-root /absolute/path/to/run_root \
  --variant full
```

Wall helper:

```bash
python3 itf.py generate-wall-reference-pair --height 2
python3 itf.py generate-wall-reference-pair --height 2 --variant left
python3 itf.py generate-wall-reference-pair --provider gemini_cli --model nano-banana-pro
python3 itf.py generate-wall-reference-pair --provider cliproxyapi --model gpt-image-2
```

Inspect:

- `artifact_status.json`
- `step_1_raw/`
- `step_3_cleanup_pool/`
- `step_4_gate/`
- `step_6_mapping/`
- `step_7_selection/`
- `deliverables/`

Read more:

- [`docs/REFERENCE_PAIR_WORKFLOW.md`](REFERENCE_PAIR_WORKFLOW.md)
- [`docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md`](FLOOR_REFERENCE_PAIR_WORKFLOW.md)
- [`docs/WALL_REFERENCE_PAIR_WORKFLOW.md`](WALL_REFERENCE_PAIR_WORKFLOW.md)

## When the existing tools are not enough

Create one request file in:

```text
requirement_from_other_repo/
```

Use:

- [`requirement_from_other_repo/README.md`](../requirement_from_other_repo/README.md)
- [`requirement_from_other_repo/REQUEST_TEMPLATE.md`](../requirement_from_other_repo/REQUEST_TEMPLATE.md)

The request should include the source repo, target workflow, exact deliverables,
canvas/anchor/transparency rules, provider/model constraints, references, and
pass/fail criteria.

After the factory handles it, the factory-side agent appends status, changed
files, commands, outputs, and blockers to that same request file.

## Minimal source-repo agent checklist

1. Identify whether the job is prop, tile re-skin, reference-pair tile, or a new
   factory capability.
2. If existing, create or reuse a spec and call `python3 itf.py ...` from the
   factory repo.
3. Start review from `artifact_status.json`, then inspect `deliverables/`.
4. Copy or import only validated deliverables into the source repo.
5. If blocked by missing factory behavior, file a request under
   `requirement_from_other_repo/` instead of making ad hoc source-repo guesses.
