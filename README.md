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

The sample spec now demonstrates `background.mode = "color_key"`, which asks Gemini for a flat `#FF00FF` background, removes that color locally, and only then runs the geometry checks.

Validate prepared/generated output later:

```bash
python3 itf.py validate-reference-pair \
  --run-root output/reference_pair_runs/pixel_grass_demo
```

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
