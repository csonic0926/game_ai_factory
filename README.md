# isometric_tile_factory

Blender-first isometric tile factory focused on one workflow:

1. render canonical tile references from Blender
2. send those references to Gemini/Nano Banana
3. optionally color-key the returned PNGs
4. validate the processed tile PNGs against the Blender-defined silhouettes

## Main workflow

Use the reference-pair workflow when you want Gemini to generate final tile images while preserving the canonical shape/camera from Blender.

High-level commands:

- `prepare-reference-pair`
- `generate-reference-pair`
- `validate-reference-pair`

See:

- `docs/REFERENCE_PAIR_WORKFLOW.md`
- `docs/BLENDER_WORKFLOW.md`
- `docs/SAMPLE_SCENE.md`

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
- `validate-reference-pair`

## Runtime

- Blender 4.5.x LTS on macOS Apple Silicon is the current stable baseline
- Python 3.11+

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Canonical sample scene

The stable fixture is:

- `examples/sample_factory.blend`

Important canonical floor pair:

- `001_floor_plain` = full-height reference
- `002_floor_half` = half-height reference

Current sample reference-pair specs point at the manually corrected scaled references:

- `examples/workflow_references/floor_height_pair/floor_full_k_scaled.png`
- `examples/workflow_references/floor_height_pair/floor_half_k_scaled.png`

This lets the workflow use artist-adjusted framing instead of the raw Blender render when needed.

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

Prepare a run:

```bash
python3 itf.py prepare-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json
```

Auto-generate and validate:

```bash
python3 itf.py generate-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json
```

The sample specs now demonstrate `background.mode = "color_key"` with a two-color chroma-key policy:

- Gemini must choose between `#FF00FF` and `#00FF00`
- the choice is guided by the **top surface / upper silhouette / ground material colors**, not by the lower side walls
- green-dominant top surfaces such as grass should prefer `#FF00FF`

The workflow then removes the chosen key color locally, generates six cleanup variants, runs geometry/edge selection, and exports the selected normalized final tile.

Validate prepared/generated output later:

```bash
python3 itf.py validate-reference-pair \
  --run-root output/reference_pair_runs/pixel_grass_demo
```

Select the best cleanup variant and export the normalized final tile:

```bash
python3 itf.py select-reference-pair-variant \
  --run-root output/reference_pair_runs/pixel_grass_demo \
  --variant full
```

The final export includes a post-scale edge safeguard: after scaling, the selector checks key left-edge pixels such as `(0,32)` and `(0,33)` and applies a small corrective nudge when needed.

Selector note: cleanup variants are still scored by normalized silhouette similarity, but the selector now blocks any later cleanup step whose score rebounds by more than 10 points versus the previous step, because increasingly aggressive cleanup should not geometrically 'recover'. Half-height tiles also use a slightly looser shoulder inset tolerance than full-height tiles.

For a real Gemini/Nano Banana run:

1. set `provider.name` to `nano_banana` or `nano_banana_pro`
2. provide `GEMINI_API_KEY` in process env or repo `.env`
3. run the same `generate-reference-pair` command

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

This repo is intentionally no longer organized around:

- AI texture cache orchestration
- square-mode product surfaces
- generic external orchestration contracts

It is organized around:

- Blender canonical references
- Gemini-driven tile generation
- reference-based validation
