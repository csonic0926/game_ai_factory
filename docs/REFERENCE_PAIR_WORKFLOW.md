# Reference Pair Workflow

This document describes the Gemini/Nano Banana generation workflow that consumes canonical Blender references and produces validated tile PNGs.

The workflow uses two canonical render references:

- `examples/workflow_references/floor_height_pair/floor_full.png`
- `examples/workflow_references/floor_height_pair/floor_half.png`

The references define **geometry and camera**. The prompt controls **style and surface detail**.

## Background modes

The workflow supports two background modes:

- `transparent` — ask Gemini/Nano Banana for native transparency
- `color_key` — ask for a flat chroma-key background such as `#FF00FF`, remove it locally, then validate the keyed PNG

By default, the workflow generates a matched `full` + `half` pair, but the spec may request only one variant:

- `"variants": ["half"]`
- `"variants": ["full"]`
- `"variants": ["full", "half"]` (default)

The workflow also supports **height conversion edit mode**:

- input an existing `half` tile and transform it into `full`
- input an existing `full` tile and transform it into `half`

In this mode, Gemini/Nano Banana should **edit the supplied tile**, not invent a new tile family. The source tile and target geometry reference are sent as separate images, not as one combined sheet.

## Workflow stages

### 1. Prepare a run

```bash
python3 itf.py prepare-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json
```

This command creates:

- copied references under `refs/`
- `refs/reference_pair_sheet.png`
- `request/request.json`
- one or more prompt files such as `request/prompt_half.txt`

If `conversion.mode = "transform"`, prepare also copies the source tile into the run and records two separate generation inputs:

- first image = source tile to preserve
- second image = target-height canonical geometry reference

If `background.mode` is `color_key`, the prompt will explicitly request the configured flat background color.

Use these artifacts when the prompt or image request will be submitted manually.

### 2. Generate

Mock smoke test:

```bash
python3 itf.py generate-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json
```

Real Gemini run:

1. set `provider.name` to `nano_banana` or `nano_banana_pro`
2. ensure `GEMINI_API_KEY` is available in the process env or repo `.env`
3. run the same command

Note: the local Nano Banana wrapper accepts repeated `--image=...` arguments and forwards them as separate image parts to Gemini.

Reference input behavior:

- pair runs use one vertical reference sheet
  - upper reference = full-height
  - lower reference = half-height
- single-variant runs use only that variant's canonical reference image, so the unused height is not sent to the model
- conversion runs use two separate image inputs
  - first image = source tile that must be transformed
  - second image = target-height canonical reference
  - prompt explicitly says to preserve source identity and only change height/geometry

`generate-reference-pair` performs generation and immediate validation for the requested variants. It does not select the final cleanup variant export.

### 3. Validate generated images

To validate an existing run, save provider outputs to the prepared run directory:

- `generated/generated_full.png` when `full` was requested
- `generated/generated_half.png` when `half` was requested

If the run uses `background.mode = "color_key"`, validation first creates keyed copies under `processed/` and then runs silhouette checks against those processed PNGs.

If the generated image canvas does not match the canonical reference size—for example, Gemini returns `1024x1024` while the reference is `256x256`—validation first aligns the generated image to the reference canvas and then evaluates silhouette geometry. Canvas mismatch alone is not a hard failure.

Then run:

```bash
python3 itf.py validate-reference-pair \
  --run-root output/reference_pair_runs/pixel_grass_demo
```

Or validate arbitrary files against the prepared run:

```bash
python3 itf.py validate-reference-pair \
  --run-root output/reference_pair_runs/pixel_grass_demo \
  --full-image /absolute/path/to/full.png \
  --half-image /absolute/path/to/half.png
```

### 4. Select the final cleanup variant

```bash
python3 itf.py select-reference-pair-variant \
  --run-root output/reference_pair_runs/pixel_grass_demo \
  --variant full
```

This command scores cleanup variants against normalized reference geometry and exports the selected final tile under `final/`.

Selection behavior:

- cleanup variants are evaluated in fixed order: `01_conservative` -> `06_aggressive_plus`
- if a later variant's score rebounds by more than 10 points versus the previous variant, that variant and all later variants are treated as invalid
- half-height variants use a looser shoulder inset tolerance than full-height variants because the shorter silhouette amplifies the same pixel drift

## Validation outputs

The validator writes:

- `validation/validation.json`
- `validation/overlay_<variant>.png` for each requested variant
- `validation/diff_<variant>.png` for each requested variant

When canvas alignment is applied, `validation.json` records it under `canvas_alignment` for the affected variant.

## Validation checks

Per image, validation checks:

- canvas alignment to reference size before geometry checks when provider output size differs
- transparent-background silhouette presence after optional color-key removal
- silhouette IoU vs reference
- bbox drift vs reference
- likely full-canvas background fill

At pair level, validation checks:

- half/full height ratio remains close to the reference pair when both variants were requested

## Status meanings

- `pass`: shape is aligned enough for use
- `soft_fail`: usable for review, but geometry drift exists
- `hard_fail`: likely wrong framing / wrong silhouette / broken transparency
