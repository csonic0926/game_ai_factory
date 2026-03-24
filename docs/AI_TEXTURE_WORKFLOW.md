# AI Texture Workflow v1

## Purpose

This file describes the executable local workflow for AI-texture-ready cache management.

It does not call any external image model yet.

Instead, it defines the request, cache, sync, validate, and inspect flow that a generator can plug into later.

## Directory Layout

Recommended cache root:

- `texture_cache/`

Per asset and variant:

- `texture_cache/<source_object>/<variant>/request.json`
- `texture_cache/<source_object>/<variant>/pack.json`
- `texture_cache/<source_object>/<variant>/textures/`

## Material Slots

Supported slots:

- `base_color`
- `normal`
- `orm`
- `emissive`

Default contract:

- required: `base_color`
- optional: `normal`, `orm`, `emissive`

## End-to-End Flow

### 1. Initialize requests from a render manifest

```bash
python3 itf.py init-ai-textures --manifest output/metadata/manifest.json
```

This creates per-asset request files and cache folders.

### 2. Generate or place textures

For now you can use the demo generator:

```bash
python3 itf.py create-demo-ai-textures --manifest output/metadata/manifest.json
```

Later an external AI generator should write selected files into:

- `textures/base_color.png`
- `textures/normal.png`
- `textures/orm.png`
- `textures/emissive.png`

### 3. Sync pack metadata

```bash
python3 itf.py sync-ai-textures --manifest output/metadata/manifest.json
```

This writes `pack.json` and marks each asset as:

- `draft`
- `partial`
- `ready`

### 4. Validate cache contents

```bash
python3 itf.py validate-ai-textures --manifest output/metadata/manifest.json
```

### 5. Inspect workflow summary

```bash
python3 itf.py inspect-ai-textures --manifest output/metadata/manifest.json
```

## Status Meaning

- `draft`: no required textures exist yet
- `partial`: some textures exist, but required slots are still missing
- `ready`: all required slots are present

## Boundary

This workflow manages texture requests and cache state only.

It does not yet:

- generate prompts automatically from a model
- call an external AI service
- bind textures back into Blender materials automatically

Those integrations should attach on top of this cache contract later.
