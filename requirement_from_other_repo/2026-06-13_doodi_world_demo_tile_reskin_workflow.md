# Cross-repo factory request

## Request metadata

- Status: done
- Date: 2026-06-13
- Source repo: doodi_world_demo (Vinci-World)
- Source repo path: /Users/hunglingki/git_projects/web_projects/doodi_world_demo
- Request owner / Codex context: scene base/overlay tile restyle (v4 Octopath look)
- Factory target area: other (new tile re-skin workflow)
- Priority: normal

## User-facing need

We restyled a scene's ground tiles (grass base + road/sand/water/fence autotile
overlays) into a new art style. The proven method is to re-skin EXISTING,
geometrically-correct tiles (not regenerate geometry), because seamless tiling
and autotile connectivity must be preserved. We want this method available as a
factory workflow callable from other repos. Generating geometrically-correct
tile sets from scratch is a separate, later request.

## Factory-side change requested

Add a `tile_reskin_workflow_v1` workflow: take a directory of existing tile
variants + target materials, produce re-skinned tiles whose geometry/edges are
unchanged.

## Asset / workflow details

- Workflow name: tile_reskin_workflow_v1
- Variants: any autotile family (road/sand 13, water 25, fence 10, base 1–N)
- Target tile size: 64 (configurable)
- Background/transparency: overlays are opaque squares; alpha preserved as-is
- Provider/model: mock | cliproxyapi(gpt-image-2) | gemini_cli
- Region classifiers: green/blue/sandy/foam/brown/gray/else, with keep + luma

## References and source context

- doodi reskin scripts (the hand-built originals this ports):
  - `scripts/sprite_style_regen/make_grass_tiles.py`-equivalent (`.js`) seamless cut
  - `scripts/sprite_style_regen/reskin_overlay_final.js` (sand/water)
  - `scripts/sprite_style_regen/reskin_road_fromorig.js` (man-made road)
  - `scripts/sprite_style_regen/reskin_fence.js` (3D fence)
- doodi skill: `.claude/skills/scene-tile-regen/skill.md`

## Acceptance criteria

- [x] Deliverable PNGs exist at the expected paths.
- [x] Existing wall/floor/prop/reference-pair behavior unchanged.
- [x] Runs offline with `--provider mock`.
- [x] Real re-skin matches the hand-built doodi output.

## Factory response (2026-06-13)

Status: **done**.

Changed files:
- `pipeline/tile_reskin_workflow.py` (new module)
- `itf.py` (+`prepare-tile-reskin`, `+generate-tile-reskin`, imports, dispatch)
- `docs/TILE_RESKIN_WORKFLOW.md` (new doc)
- `README.md` (workflow section + docs list)
- `examples/tile_reskin_workflow/{village_road.mock,village_road,village_sand,village_water,village_fence}.spec.json`
- `docs/REPO_MEMORY.md`, `docs/CURRENT_JOB.md`

Commands:
```
python3 itf.py generate-tile-reskin --spec examples/tile_reskin_workflow/village_road.mock.spec.json
python3 itf.py generate-tile-reskin --spec examples/tile_reskin_workflow/village_road.spec.json
```

Verified: mock road (13), real road/sand/water/fence (13/13/25/10) from the
target repo's git-HEAD originals; assembled corner/edge/center previews confirm
connectivity, straight man-made road boundary, natural sand/water fringes, and
fence rails — matching the source-repo hand-built result.

Notes / blockers:
- Geometry generation (correct-from-scratch tile sets) intentionally NOT
  included; add a sibling workflow when needed.
- Other repos call this by writing a `tile_reskin_workflow_v1` spec (see doc)
  pointing `source_tiles.dir` at their pristine tiles and supplying material
  fields or `generate` prompts.
