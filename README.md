# isometric_tile_factory

Generic Blender-based tile and prop rendering pipeline for agentic workflows.

License: MIT

This tool is meant to:

1. let vibe-coding AI or local users generate tile assets through stable CLI contracts
2. support both isometric and regular square tile production over time
3. produce atlas outputs, individual PNG outputs, or both
4. keep geometry shape stable through Blender-based 3D rendering
5. prepare texture-generation and engine-adapter workflows around one core metadata contract

This repository is intentionally project-agnostic.

## Structure

- `docs/` design and workflow notes
- `adapters/` future engine-specific integration boundary
- `blender/scripts/` Blender automation scripts
- `pipeline/` atlas and metadata tooling
- `output/` generated files
- `examples/` sample config files

## Key design docs

- `docs/SPEC.md`
- `docs/BLENDER_WORKFLOW.md`
- `docs/SAMPLE_SCENE.md`
- `docs/ADAPTERS.md`
- `docs/AI_TEXTURE_BOUNDARY.md`
- `docs/AI_TEXTURE_WORKFLOW.md`

## CLI

Primary repo CLI:

```bash
python3 itf.py --help
```

Commands:

- `validate`
- `render`
- `build-atlas`
- `inspect-manifest`
- `create-sample-scene`
- `sample-regression`
- `smoke-sample`
- `smoke-sample-square`
- `smoke-sample-all`
- `init-ai-textures`
- `create-demo-ai-textures`
- `sync-ai-textures`
- `validate-ai-textures`
- `inspect-ai-textures`

## Runtime

- Blender 5.1.x as the primary tested baseline
- Python 3.11+

Install Python dependency:

```bash
python3 -m pip install -r requirements.txt
```

## First commands

Validate config:

```bash
python3 itf.py validate --config examples/config.json
```

Validate square config:

```bash
python3 itf.py validate --config examples/config.square.json
```

Validate Blender scene structure:

```bash
python3 itf.py validate --scene your_scene.blend --config examples/config.json
```

Validate the strict sample fixture contract:

```bash
python3 itf.py validate --scene examples/sample_factory.blend --config examples/config.json --sample-scene
```

Render from Blender:

```bash
python3 itf.py render --scene your_scene.blend --config examples/config.json
```

If config `output_mode` is `atlas` or `both`, `render` now auto-builds the atlas after PNG render.

Render the square sample path:

```bash
python3 itf.py render --scene examples/sample_factory.blend --config examples/config.square.json
```

Build atlas:

```bash
python3 itf.py build-atlas --manifest output/metadata/manifest.json --out output/atlas/tileset.png
```

Validate manifest:

```bash
python3 itf.py validate --manifest output/metadata/manifest.json
```

Inspect manifest:

```bash
python3 itf.py inspect-manifest --manifest output/metadata/manifest.json
```

Create the sample scene fixture:

```bash
python3 itf.py create-sample-scene
```

Then validate it:

```bash
python3 itf.py validate --scene examples/sample_factory.blend --config examples/config.json --sample-scene
```

Update the committed sample baseline from current output:

```bash
python3 itf.py sample-regression --update
```

Verify current output against the committed baseline:

```bash
python3 itf.py sample-regression
```

Run the full sample smoke/regression flow:

```bash
python3 itf.py smoke-sample
```

Run the square sample smoke/regression flow:

```bash
python3 itf.py smoke-sample-square
```

Run both sample smoke/regression flows:

```bash
python3 itf.py smoke-sample-all
```

Run the full flow and refresh the baseline:

```bash
python3 itf.py smoke-sample --update-baseline
```

## AI texture-ready local workflow

Initialize cache layout from a manifest:

```bash
python3 itf.py init-ai-textures --manifest output/metadata/manifest.json
```

Create demo textures so the full local flow can run end-to-end:

```bash
python3 itf.py create-demo-ai-textures --manifest output/metadata/manifest.json
```

Sync cache state:

```bash
python3 itf.py sync-ai-textures --manifest output/metadata/manifest.json
```

Validate cache contents:

```bash
python3 itf.py validate-ai-textures --manifest output/metadata/manifest.json
```

Inspect cache summary:

```bash
python3 itf.py inspect-ai-textures --manifest output/metadata/manifest.json
```

## Status

Working baseline with:

- isometric + square projection configs
- `output_mode` support: `png`, `atlas`, `both`
- `render_profile` / `render_profiles` config support
- projection-aware manifest metadata
- committed sample baselines for both sample outputs
