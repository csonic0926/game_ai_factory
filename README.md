# game_asset_factory

Blender-first game asset factory for **reference-pair generation, validation, and final selection** of floor/wall tiles, plus engineering-spec validation for prop/object assets.

## Factory positioning

Treat this repo as a **game asset factory** for isometric art workflows:

- caller places an order with a spec
- factory prepares canonical references + prompts
- factory runs generation
- factory validates geometry
- factory emits final handoff PNGs for tiles and prop/object assets

The public order contract is the **reference-pair spec JSON** plus the CLI commands in `/Users/hunglingki/git_projects/tools/game_asset_factory/itf.py`.

## Use this workflow

For almost all tile-art work, use the **reference-pair workflow**.

Main commands:

```bash
python3 itf.py prepare-reference-pair --spec /absolute/path/to/spec.json
python3 itf.py generate-reference-pair --spec /absolute/path/to/spec.json
python3 itf.py validate-reference-pair --run-root /absolute/path/to/run_root
python3 itf.py select-reference-pair-variant --run-root /absolute/path/to/run_root --variant full
```

Tile re-skin (re-texture an EXISTING geometrically-correct tile/autotile set
into a new material look, preserving seamlessness + connectivity):

```bash
python3 itf.py prepare-tile-reskin  --spec examples/tile_reskin_workflow/village_road.spec.json
python3 itf.py generate-tile-reskin --spec examples/tile_reskin_workflow/village_road.spec.json
python3 itf.py generate-tile-reskin --spec <spec> --provider mock   # offline flat-colour fields
```

See `docs/TILE_RESKIN_WORKFLOW.md`. Generating geometrically-correct tile sets
from scratch is not part of this workflow yet.

Wall helper:

```bash
python3 itf.py generate-wall-reference-pair
python3 itf.py generate-wall-reference-pair --height 2
python3 itf.py generate-wall-reference-pair --height 2 --variant left
python3 itf.py generate-wall-reference-pair --variant right
python3 itf.py generate-wall-reference-pair --provider cliproxyapi --model gpt-image-2
python3 itf.py generate-wall-reference-pair --provider gemini_cli --model nano-banana-pro
```

Prop/object vertical slice:

```bash
python3 itf.py generate-prop-assets --spec examples/prop_asset_workflow/flame_relay_brazier_pair.spec.json
python3 itf.py validate-prop-assets --run-root output/prop_asset_runs/imt_flame_relay_brazier_pair
python3 itf.py generate-prop-assets --spec examples/prop_asset_workflow/flame_relay_brazier_pair.gpt_image.spec.json
python3 itf.py generate-prop-assets --spec examples/prop_asset_workflow/flame_relay_brazier_pair.cliproxyapi.spec.json
python3 itf.py generate-prop-assets --spec examples/prop_asset_workflow/flame_relay_brazier_pair.gemini_pro.spec.json
python3 itf.py generate-prop-assets --spec examples/prop_asset_workflow/flame_relay_brazier_pair.gpt_image.spec.json --provider gpt_image --out output/prop_asset_runs/imt_flame_relay_brazier_pair_gpt_image
python3 itf.py generate-prop-assets --spec examples/prop_asset_workflow/flame_relay_brazier_pair.spec.json --provider gemini_cli --model nano-banana-pro
python3 itf.py validate-prop-assets --run output/prop_asset_runs/imt_flame_relay_brazier_pair_gpt_image
python3 itf.py generate-prop-assets --spec examples/prop_asset_workflow/field_cooking_campfire_pot.gpt_image.spec.json --provider gpt_image
```

Prop workflow note: `prop_asset_workflow_v1` currently supports mock and direct
providers only. `agent_handoff` is intentionally not supported yet.

## Public provider/model contract

Use these two fields in specs:

```json
"provider": {
  "name": "cliproxyapi",
  "mode": "direct"
},
"model": {
  "name": "gpt-image-2"
}
```

Canonical provider backends:

- `mock`
- `gemini_cli`
- `cliproxyapi`
- `gpt_image` for prop `gpt_image_prop_color_key` workflow, backed by `cliproxyapi` + `gpt-image-2`
- `agent_handoff`

Current supported models:

- `mock` -> `mock`
- `gemini_cli` -> `nano-banana-2`, `nano-banana-pro`
- `cliproxyapi` -> `gpt-image-2`
- `agent_handoff` -> `gpt-image-2`

For prop assets, direct `cliproxyapi`, `gpt_image`, and `gemini_cli` runs emit request payload
snapshots under `request/provider_request_{asset_id}.json`; `edit_from` states
route the cleaned source-state PNG as the reference image. For local CLIProxyAPI GPT Image edit routes, the factory sends JSON data-URL edit payloads rather than multipart uploads so current proxy builds can bridge through the Responses image tool. GPT Image 2 does not support native transparent background, so the prop path asks for a flat `#FF00FF`/`#00FF00` chroma-key background, emits cleanup candidates, scores them by raw-vs-cleaned pixel preservation/removal, then validates the selected transparent PNG.

Legacy aliases are still accepted and normalized:

- `nano_banana` -> `provider.name=gemini_cli`, `model.name=nano-banana-2`
- `nano_banana_pro` -> `provider.name=gemini_cli`, `model.name=nano-banana-pro`
- `gpt_image_2` or direct `imagegen` -> `provider.name=cliproxyapi`, `model.name=gpt-image-2`
- `imagegen_handoff` -> `provider.name=agent_handoff`, `model.name=gpt-image-2`

For new integrations, prefer the canonical provider/model fields instead of legacy aliases.

## Spec example

```json
{
  "schema_version": "reference_pair_workflow_v1",
  "theme": "pixel dungeon stone wall 2u",
  "run_id": "stone_wall_2u",
  "output_root": "/absolute/path/to/output/reference_pair_runs",
  "variants": ["left", "right"],
  "provider": {
    "name": "cliproxyapi",
    "mode": "direct"
  },
  "model": {
    "name": "gpt-image-2"
  },
  "reference_pair": {
    "left": "/absolute/path/to/left_reference.png",
    "right": "/absolute/path/to/right_reference.png"
  },
  "prompt_parts": {
    "style": "pixel art dungeon wall",
    "material": "aged stone blocks",
    "decoration": "subtle moss and cracks",
    "negative_constraints": [
      "no extra props",
      "no text",
      "no watermark"
    ]
  }
}
```

## Workflow docs

Use these docs as the real workflow entry points:

- `/Users/hunglingki/git_projects/tools/game_asset_factory/docs/TILE_RESKIN_WORKFLOW.md`
- `/Users/hunglingki/git_projects/tools/game_asset_factory/docs/REFERENCE_PAIR_WORKFLOW.md`
- `/Users/hunglingki/git_projects/tools/game_asset_factory/docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md`
- `/Users/hunglingki/git_projects/tools/game_asset_factory/docs/WALL_REFERENCE_PAIR_WORKFLOW.md`
- `/Users/hunglingki/git_projects/tools/game_asset_factory/docs/PROP_ASSET_WORKFLOW.md`

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
