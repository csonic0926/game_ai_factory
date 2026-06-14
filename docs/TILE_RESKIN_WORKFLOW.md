# Tile Re-skin Workflow (`tile_reskin_workflow_v1`)

Re-texture an **existing, geometrically-correct tile set** into a new material
look without regenerating geometry. This covers the *"we already have a tile set
whose shapes and autotile edges connect — re-skin it into a new style"* half of
tile work. Generating geometrically-correct tile sets from scratch is **out of
scope** for this workflow (a future workflow will own that).

## Why re-skin instead of regenerate

Ground tiles have two hard constraints that make per-tile from-scratch
regeneration wrong:

1. **Seamless tiling** — a base tile must repeat without seams or a lighting
   hotspot. A directional light or any brightness gradient becomes a visible
   repeating pattern across the map.
2. **Autotile connectivity** — overlay variants (center / edge / corner /
   inner-corner) are opaque squares whose painted boundary lines up with their
   neighbours; the autotile resolver picks the variant. Regenerating each
   variant's *shape* breaks that boundary match.

The fix: generate ONE flat material per surface, cut a seamless tile from it,
then re-texture each existing tile **in place**, using the original tile's own
colour regions as the mask. Geometry is never touched, so seamlessness and
connectivity are preserved by construction.

## Commands

```bash
python3 itf.py prepare-tile-reskin  --spec examples/tile_reskin_workflow/village_road.spec.json
python3 itf.py generate-tile-reskin --spec examples/tile_reskin_workflow/village_road.spec.json
# overrides:
python3 itf.py generate-tile-reskin --spec <spec> --provider mock        # no network, flat-colour fields
python3 itf.py generate-tile-reskin --spec <spec> --out output/tile_reskin_runs/my_run
```

## Run layout

```
<output_root>/<run_id>/
  request/request.json
  step_1_field/<material>_field.png        # flat material field (generated or copied)
  step_2_material/<material>_tile.png       # seamless tile cut from the field
  step_2_material/_proof_<material>.png     # 3x3 tiling proof — eyeball for seams
  step_3_reskin/<variant>.png               # re-skinned tiles
  deliverables/<variant>.png                # final, copy these into the game repo
  deliverables/manifest.json
  artifact_status.json
  logs/generate.json
```

## Spec

```json
{
  "schema_version": "tile_reskin_workflow_v1",
  "run_id": "village_road",
  "output_root": "../../output/tile_reskin_runs",
  "provider": { "name": "gpt_image", "mode": "direct" },
  "model": { "name": "gpt-image-2" },
  "tile_size": 64,
  "source_tiles": {
    "dir": "/abs/path/to/overlay",
    "prefix": "road"
  },
  "materials": [
    { "id": "grass", "field": "/abs/grass_field.png" },
    { "id": "road",  "generate": { "prompt": "flat-lit cobblestone …", "size": "1024x1024", "color_ref": "/abs/orig_road.png" } }
  ],
  "reskin": {
    "regions": [
      { "match": "green", "material": "grass", "soft": true },
      { "match": "else",  "material": "road",  "modulate_luma": true }
    ]
  }
}
```

### `source_tiles`
- `dir` — directory of the geometrically-correct source PNGs (use the
  pristine originals, e.g. extracted from the target repo's git HEAD, not a
  previous re-skin).
- `variants` (list) **or** `prefix` (string). `prefix: "road"` matches
  `road.png` + `road_*.png`.

### `materials[]` — one entry per surface, identified by `id`
Provide ONE of:
- `generate: { prompt, size, color_ref?, mock_color? }` — generate a flat field
  via the provider. The prompt MUST stress flat even lighting (no directional
  light / shadow / vignette / hotspot) and full-bleed object-free coverage, and
  should pass the original tile as `color_ref` so the model doesn't drift warm.
- `field: <png>` — an already-generated flat field; the workflow cuts the
  seamless tile from it.
- `tile: <png>` — an already-seamless tile; used as-is (just resized).

### `reskin.regions[]` — evaluated to classify each original pixel
Each region: `match` + (`material` or `keep: true`), plus `modulate_luma` and
`soft`. The list MUST end with a `{ "match": "else", … }` catch-all.

Named classifiers: `green`, `blue`, `sandy`, `foam`, `brown`, `gray`, `dark`,
`cream`, `light`, `else`. `dark` (max channel < 60) is how you KEEP structural
black on interior wall tiles; `cream` matches warm low-sat plaster/parchment.

`match` may also be an **HSV-range object** for any surface the named set
doesn't cover: `{ "hue": [90,150], "sat": [0.2,1], "val": [0.3,1] }` (any subset
of hue/sat/val; hue may wrap when min > max).

- `material` — fill matched pixels with that material's seamless tile.
- `keep: true` — keep the original pixels (e.g. water foam).
- `modulate_luma: true` — multiply the material by `origLuma / regionMeanLuma`,
  so curbs, 3D posts/rails, and shading shapes survive the re-texture.
- `soft: true` (default for `green`) — soft-blend by classifier strength for a
  clean anti-aliased fringe; otherwise a hard threshold is used.

Region order matters: earlier regions overlay later ones; `foam` (keep) goes
first, the core surface goes in the `else` slot.

## Family recipes (validated on doodi village standard)

| Family | regions |
|--------|---------|
| road (man-made; straight edges already drawn in the original) | `green→grass(soft)`, `else→road(luma)` |
| sand (natural; organic grass fringe in the original) | `green→grass(soft)`, `else→sand` |
| water (foam + grass bank + sand shore) | `foam→keep`, `sandy→sand(luma)`, `green→grass(soft)`, `brown→grass(luma)`, `else→water` |
| fence (3D posts/rails on grass) | `green→grass(soft)`, `else→wood(luma)` |
| house floor (interior stone) | `else→floor` |
| house walls (plaster panel + wood frame + structural black) | `dark→keep`, `cream→plaster`, `else→wood(luma)` |

Always open `step_2_material/_proof_*` (seam check) and assemble a
corner/edge/center block from `deliverables/` (connectivity check) before
shipping.

## Notes
- Pure Pillow; tiles are small so per-pixel Python is fine. Fields are cropped
  before the seamless seal so the 1024² pass stays cheap.
- Seamless seal knobs: `seal_band` (default 0.25 — narrow, keeps texture) and
  `crop_frac` (default 0.2 — small crop, less downscale blur).
- `--provider mock` produces flat-colour fields (with a faint checker) so the
  full pipeline runs offline for tests.
