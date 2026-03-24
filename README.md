# isometric_tile_factory

Generic Blender-based isometric tile and prop rendering pipeline.

This tool is meant to:

1. batch render isometric tiles and props from Blender
2. keep output ordering stable
3. assemble atlas sheets
4. export metadata for engine adapters such as Godot

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

Run the full flow and refresh the baseline:

```bash
python3 itf.py smoke-sample --update-baseline
```

## Status

Prototype skeleton.
