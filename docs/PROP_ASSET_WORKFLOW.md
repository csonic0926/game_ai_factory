# Prop Asset Workflow

Use this document for engineering-spec-driven isometric object/prop assets.

First vertical slice:

- IMT dungeon prototype `flame_relay_brazier`
- `imt_flame_target_brazier_unlit`
- `imt_flame_source_brazier_active`

Additional IMT prop order:

- `field_cooking_campfire_pot`
- `imt_field_cooking_pot_unlit`
- `imt_field_cooking_pot_active`
- handoff target folder: `img/generated/field_cooking_campfire_pot/`

## Main commands

Prepare:

```bash
python3 itf.py prepare-prop-assets \
  --spec /absolute/path/to/prop.spec.json
```

Generate + validate + deliver:

```bash
python3 itf.py generate-prop-assets \
  --spec /absolute/path/to/prop.spec.json
```

Validate an existing prepared run:

```bash
python3 itf.py validate-prop-assets \
  --run-root /absolute/path/to/run_root
```

Example smoke run:

```bash
python3 itf.py generate-prop-assets \
  --spec examples/prop_asset_workflow/flame_relay_brazier_pair.spec.json
```

Real provider run, same flame relay pair:

```bash
python3 itf.py generate-prop-assets \
  --spec examples/prop_asset_workflow/flame_relay_brazier_pair.gpt_image.spec.json

python3 itf.py generate-prop-assets \
  --spec examples/prop_asset_workflow/flame_relay_brazier_pair.cliproxyapi.spec.json

python3 itf.py generate-prop-assets \
  --spec examples/prop_asset_workflow/flame_relay_brazier_pair.gemini_pro.spec.json

python3 itf.py generate-prop-assets \
  --spec examples/prop_asset_workflow/field_cooking_campfire_pot.gpt_image.spec.json \
  --provider gpt_image
```

GPT Image color-key CLI override:

```bash
python3 itf.py generate-prop-assets \
  --spec examples/prop_asset_workflow/flame_relay_brazier_pair.gpt_image.spec.json \
  --provider gpt_image \
  --out output/prop_asset_runs/imt_flame_relay_brazier_pair_gpt_image

python3 itf.py validate-prop-assets \
  --run output/prop_asset_runs/imt_flame_relay_brazier_pair_gpt_image
```

When overriding providers from a mock spec, the CLI also chooses the matching
default model unless `--model` is supplied:

- `--provider gpt_image` / `cliproxyapi` -> `gpt-image-2`
- `--provider gemini_cli` / `nano_banana` -> `nano-banana-2`
- `--provider nano_banana_pro` -> `nano-banana-pro`

Note: `gpt-image-2` rejects native transparent background (`Transparent background is not supported for this model.`). The GPT Image prop path therefore uses a flat chroma-key source background and deterministic cleanup scoring; `--transparent-background true` is intentionally rejected.

The direct provider contract is:

```json
"provider": { "name": "cliproxyapi", "mode": "direct" },
"model": { "name": "gpt-image-2" }
```

`gpt_image`/CLIProxyAPI edit states are sent as JSON data-URL edit payloads.
This avoids the local proxy build failure mode where `/v1/images/edits`
exists but rejects multipart bridging with `request Content-Type isn't
multipart/form-data`.

`gemini_cli` direct mode is also accepted with `nano-banana-2` or
`nano-banana-pro`; base states receive a small engineering guide image, and
`edit_from` states receive the already-cleaned source state as the reference
image.

GPT Image prop contract:

```json
"provider": { "name": "gpt_image", "mode": "gpt_image_prop_color_key" },
"model": { "name": "gpt-image-2" },
"background": {
  "mode": "color_key",
  "prompt_color": "#FF00FF",
  "fallback_colors": ["#00FF00"],
  "tolerance": 24
}
```

This path prompts GPT Image for one centered prop on a perfectly flat chroma-key background. It does not assume native alpha. It exports all cleanup candidates, scores them against the raw image, selects the best engineering candidate, then validates the transparent PNG.

## Generation canvas

Prop callers should describe the **final engineering canvas** only:

```json
"canvas": { "width": 128, "height": 256 }
```

The workflow now derives a provider-neutral source canvas from that final canvas:

```json
"generation_canvas": {
  "strategy": "derive_from_final_canvas",
  "target_long_edge": 1024,
  "preserve_aspect_ratio": true
}
```

If omitted, the same block is used by default. For a final `128x256` prop, the factory derives:

```json
{
  "final_canvas": { "width": 128, "height": 256 },
  "derived_aspect_ratio": "1:2",
  "derived_size": { "width": 512, "height": 1024 }
}
```

Provider adapters then convert that into provider-specific generation args:

- GPT Image / CLIProxyAPI:
  - derives a legal GPT Image size and records any fallback, e.g. `1024x1536`
- Gemini / Nano Banana:
  - derives the closest supported `aspect_ratio` and `image_size`, e.g. `9:16` + `1K`

The source image is allowed to be high-resolution; the workflow still cleans, scores, and normalizes the selected result back onto the final engineering canvas.

## Workflow shape

1. read `prop_asset_workflow_v1` spec
2. prepare prompts and request snapshot
3. generate one PNG per state
4. if `background.mode=color_key`: emit cleanup candidates into `step_3_cleanup_pool/`
5. score cleanup candidates by comparing raw pixels with each cleaned PNG (`prop_cleanup_score.{asset_id}.json`)
6. normalize the selected candidate onto the requested prop canvas
7. run prop engineering validator
8. write deliverables only when validation passes

Each generated state writes a provider request snapshot under:

```text
request/provider_request_{asset_id}.json
request/provider_requests.json
```

For `source_active` / `edit_from`, the request snapshot must show the cleaned
`target_unlit` PNG in `reference_images`.

Each request snapshot now also records:

- `generation_canvas`
- `adapter_decision`
- `provider_generation_args`

So debug review can see:

1. the caller's final canvas
2. the factory-derived source aspect ratio / size hint
3. the actual provider-facing conversion

## Validator scope

The first validator checks engineering usability only:

- PNG mode is RGBA
- canvas is exactly `128x256`
- alpha channel exists
- top corner alpha means are near zero; bottom corners remain diagnostic only
- opaque pixel ratio is within configured bounds
- bbox width/height are within configured bounds
- transparent background is clean after cleanup
- opaque bbox does not touch top/left/right canvas edges
- object bottom is close to bottom-center anchor `(64,255)`
- object x center is close to `64`
- likely baked-in floor diamond is rejected
- likely text/watermark corner marks are rejected
- paired states have similar bbox size, center, and bottom anchor

It does **not** grade artistic quality.

## Deliverables

A successful run writes:

```text
deliverables/
  imt_flame_source_brazier_active.png
  imt_flame_target_brazier_unlit.png
  prop_asset_manifest.json
  imt_prop_handoff.json
  validation_summary.json
  preview_sheet.png
```

When `atlas.enabled=true`, it also writes:

```text
  prop_asset_atlas.png
  prop_asset_atlas_metadata.json
```

The atlas metadata includes `asset_id`, atlas rect, anchor, and footprint fields intended to be easy for IMT `TileAssetRegistry`-style ingestion.

`imt_prop_handoff.json` is the IMT handoff contract. Paths inside it are relative
to `deliverables/`, `asset_id` values are stable, and each asset records:

- `file`
- `atlas_rect`
- `anchor`
- `footprint`
- `validation_status`

If the spec includes `target_project_folder`, it is copied into
`imt_prop_handoff.json` for IMT-side import tooling.

For GPT Image color-key runs, the handoff keeps the existing IMT-facing shape and includes:

- `generation_provider: "gpt_image"`
- `background_mode: "color_key"`
- `alpha_validated: true` after cleanup + validation pass

## Agent handoff status

`prop_asset_workflow_v1` currently supports mock and direct providers only.
`agent_handoff` is intentionally not supported yet.

Preparing an `agent_handoff` spec writes `request/prop_agent_handoff.json` as an
explicit unsupported packet for debugging, but `generate-prop-assets` will still
return an error before generation.

## Boundary rule

This workflow is separate from `reference_pair_workflow_v1`. Do not route prop/object validation through the wall selector or mutate floor/wall canonical placement rules for prop needs.
