# Floor Reference Pair Workflow

Use this document for:

- `full` / `half` floor runs
- floor full↔half transform mode
- floor validation / final selection

## Canonical references

- `/Users/hunglingki/git_projects/tools/isometric_tile_factory/examples/workflow_references/floor_height_pair/floor_full_k_scaled.png`
- `/Users/hunglingki/git_projects/tools/isometric_tile_factory/examples/workflow_references/floor_height_pair/floor_half_k_scaled.png`

## Main commands

Prepare:

```bash
python3 itf.py prepare-reference-pair \
  --spec /absolute/path/to/spec.json
```

Generate:

```bash
python3 itf.py generate-reference-pair \
  --spec /absolute/path/to/spec.json
```

Validate:

```bash
python3 itf.py validate-reference-pair \
  --run-root /absolute/path/to/run_root
```

Select final variant:

```bash
python3 itf.py select-reference-pair-variant \
  --run-root /absolute/path/to/run_root \
  --variant full
```

## Floor workflow shape

Typical floor run:

1. prepare references and request files
2. generate raw output
3. emit cleanup candidates when color key is used
4. validate against canonical floor geometry
5. select the final mapped output

## Transform mode

Use transform mode only when converting an already-approved floor tile into the opposite height.

Example:

```json
{
  "variants": ["full"],
  "conversion": {
    "mode": "transform",
    "source_variant": "half",
    "source_image": "/absolute/path/to/deliverables/deliverable.half.png"
  }
}
```

Use it for:

- `half -> full`
- `full -> half`

Do not use it for same-height restyling.

## Run triage

Start with:

- `artifact_status.json`

Then inspect:

1. `step_1_raw/`
2. `step_3_cleanup_pool/`
3. `step_7_selection/`
4. `deliverables/`
