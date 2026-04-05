# Reference Pair Workflow

This workflow uses two canonical render references:

- `examples/workflow_references/floor_height_pair/floor_full.png`
- `examples/workflow_references/floor_height_pair/floor_half.png`

The references constrain **shape and camera**, while the prompt controls **style and surface detail**.

The workflow now supports two background modes:

- `transparent` — ask Gemini/Nano Banana for native transparency
- `color_key` — ask for a flat chroma-key background such as `#FF00FF`, remove it locally, then run geometry validation on the keyed PNG

By default, the workflow still generates a matched `full` + `half` pair, but the spec can now request only one variant:

- `"variants": ["half"]`
- `"variants": ["full"]`
- `"variants": ["full", "half"]` (default)

## Commands

### 1. Prepare a run

```bash
python3 itf.py prepare-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json
```

This creates:

- copied references under `refs/`
- `refs/reference_pair_sheet.png`
- `request/request.json`
- one or more prompt files such as `request/prompt_half.txt`

If `background.mode` is `color_key`, the prompt will explicitly request the configured flat background color.

Use these files if you want to send the prompts/images to Gemini manually.

### 2. Auto-generate and validate

Mock smoke test:

```bash
python3 itf.py generate-reference-pair \
  --spec examples/reference_pair_workflow/pixel_grass_demo.spec.json
```

Real Gemini run:

1. set `provider.name` to `nano_banana` or `nano_banana_pro`
2. ensure `GEMINI_API_KEY` is available in the process env or repo `.env`
3. run the same command

Note: the local Nano Banana wrapper accepts one image input.

- pair runs use one vertical reference sheet:
  - upper reference = full-height
  - lower reference = half-height
- single-variant runs use only that variant's canonical reference image, so you do not burn tokens on the unused height

### 3. Validate returned images

After Gemini returns images, save them to the prepared run directory:

- `generated/generated_full.png` when `full` was requested
- `generated/generated_half.png` when `half` was requested

If the run uses `background.mode = "color_key"`, the validator will first create keyed copies under `processed/` and then run silhouette checks against those processed PNGs.

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

## Validation outputs

Selection behavior notes:
- cleanup variants are evaluated in their fixed order (`01_conservative` -> `06_aggressive_plus`)
- if a later variant's score rebounds by more than 10 points versus the previous variant, that variant and all later variants are treated as invalid (`blocked_by_score_rebound_gt_10`)
- half-height variants use a looser shoulder inset tolerance than full-height variants because the shorter silhouette amplifies the same pixel drift


The validator writes:

- `validation/validation.json`
- `validation/overlay_<variant>.png` for each requested variant
- `validation/diff_<variant>.png` for each requested variant

## What validation checks

Per image:

- transparent-background silhouette presence after optional color-key removal
- silhouette IoU vs reference
- bbox drift vs reference
- likely full-canvas background fill

Pair-level:

- half/full height ratio remains close to the reference pair when both variants were requested

## Status meanings

- `pass`: shape is aligned enough for use
- `soft_fail`: usable for review, but geometry drift exists
- `hard_fail`: likely wrong framing / wrong silhouette / broken transparency
