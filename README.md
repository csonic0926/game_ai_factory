# isometric_tile_factory

Blender-first isometric tile factory for isometric floor-tile production.

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

Stable fixture:

- `examples/sample_factory.blend`

Canonical floor reference pair:

- `001_floor_plain` = full-height reference
- `002_floor_half` = half-height reference

Current sample reference-pair specs point at manually corrected scaled references:

- `examples/workflow_references/floor_height_pair/floor_full_k_scaled.png`
- `examples/workflow_references/floor_height_pair/floor_half_k_scaled.png`

This allows the Gemini-generation workflow to use artist-adjusted framing instead of the raw Blender render when needed.

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

### 1. Prepare

Create a run directory with copied references, prompt files, and request metadata:

```bash
python3 itf.py prepare-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json
```

### 2. Generate

Generate requested variants from the spec:

```bash
python3 itf.py generate-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json
```

The sample specs demonstrate `background.mode = "color_key"` with a two-color chroma-key policy:

- Gemini must choose between `#FF00FF` and `#00FF00`
- the choice is driven by the **top surface / upper silhouette / ground material colors**, not by the lower side walls
- green-dominant top surfaces such as grass should prefer `#FF00FF`

The generation workflow then:

1. removes the selected key color locally
2. emits six cleanup variants
3. runs geometry validation
4. preserves the variant pool for later selection

Provider outputs do not need to match the reference canvas size exactly. If Gemini/Nano Banana returns a larger image such as `1024x1024` while the canonical reference is `256x256`, validation aligns the generated image to the reference canvas before silhouette checks. Canvas mismatch alone is not treated as a hard failure.

For a real Gemini/Nano Banana run:

1. set `provider.name` to `nano_banana` or `nano_banana_pro`
2. provide `GEMINI_API_KEY` in process env or repo `.env`
3. run the same `generate-reference-pair` command

### 3. Validate

Re-run validation for an existing prepared/generated run:

```bash
python3 itf.py validate-reference-pair \
  --run-root output/reference_pair_runs/pixel_grass_demo
```

### 4. Select final output

Score cleanup variants and export the normalized final tile:

```bash
python3 itf.py select-reference-pair-variant \
  --run-root output/reference_pair_runs/pixel_grass_demo \
  --variant full
```

The final export includes a post-scale edge safeguard. After scaling, the selector checks key left-edge pixels such as `(0,32)` and `(0,33)` and applies a small corrective nudge when needed.

Cleanup variants are scored by normalized silhouette similarity. The selector blocks any later cleanup step whose score rebounds by more than 10 points versus the previous step, because increasingly aggressive cleanup should not geometrically recover. Half-height tiles use a slightly looser shoulder inset tolerance than full-height tiles.

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
