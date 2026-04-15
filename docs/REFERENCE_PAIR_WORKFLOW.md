# Reference Pair Workflow

This document describes the Gemini/Nano Banana generation workflow that consumes canonical Blender references and produces validated tile PNGs.

The workflow uses canonical render references keyed by variant name.

The default floor example uses:

- `examples/workflow_references/floor_height_pair/floor_full.png`
- `examples/workflow_references/floor_height_pair/floor_half.png`

The references define **geometry and camera**. The prompt controls **style and surface detail**.

## Background modes

The workflow supports two background modes:

- `transparent` — ask Gemini/Nano Banana for native transparency
- `color_key` — ask for a flat chroma-key background such as `#FF00FF`, remove it locally, then validate the keyed PNG

By default, the floor workflow generates a matched `full` + `half` pair, but the spec may request only one variant:

- `"variants": ["half"]`
- `"variants": ["full"]`
- `"variants": ["full", "half"]` (default)

The same machinery can also be used with non-floor pairs such as:

- `"variants": ["left", "right"]`
- `reference_pair.left`
- `reference_pair.right`
- `variant_profiles.left/right`

For walls, the repo now also exposes a high-level helper command:

```bash
python3 itf.py generate-wall-reference-pair
python3 itf.py generate-wall-reference-pair --height 2
python3 itf.py generate-wall-reference-pair --height 2 --variant left
python3 itf.py generate-wall-reference-pair --variant right
```

Behavior:

- defaults to both `left` + `right`
- `--height 1` uses `101_wall_straight`
- `--height 2` uses `102_wall_straight_2u`
- single-side generation is controlled by repeating `--variant`
- canonical handedness is:
  - `left wall -> rot90`
  - `right wall -> rot0`

So the canonical wall references are:

- `1u left -> examples/golden/sample_factory/images/101_wall_straight_rot90.png`
- `1u right -> examples/golden/sample_factory/images/101_wall_straight_rot0.png`
- `2u left -> examples/golden/sample_factory/images/102_wall_straight_2u_rot90.png`
- `2u right -> examples/golden/sample_factory/images/102_wall_straight_2u_rot0.png`

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

If the spec uses arbitrary variants like `left` / `right`, those names are preserved through the whole run:

- `generated/generated_left.png`
- `generated/generated_right.png`
- `validation/overlay_left.png`
- `validation/overlay_right.png`

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

#### Wall iso-skew finalization

For wall variants, the selector applies a **perspective skew** step that aligns the Gemini-generated wall to exact game-iso geometry:

1. **Edge detection** — fits four lines (face, top, bottom, outer) to the source alpha mask using least-squares
2. **Corner extraction** — intersects the four lines to find the four body corners; line extension handles corners that fall outside the source canvas
3. **Perspective transform** — solves an 8-coefficient homography mapping the detected source corners to the canonical body polygon from the tile spec
4. **Clipping** — masks the result to the 4-point body polygon and enforces the opaque-half rule

This replaces the earlier mean-value-coordinate warp approach. The perspective transform runs in C (via PIL) and produces cleaner results without triangle seam artifacts.

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
