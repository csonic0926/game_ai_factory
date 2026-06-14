# Cross-repo factory request — example prop pair

## Request metadata

- Status: example
- Date: 2026-06-03
- Source repo: simplest_infinity_magic_tower
- Source repo path: `/Users/hunglingki/git_projects/.../simplest_infinity_magic_tower`
- Request owner / Codex context: IMT Codex needs new generated prop assets for a gameplay feature.
- Factory target area: prop_asset_workflow
- Priority: normal

## User-facing need

Generate a two-state isometric prop pair that IMT can copy into its `img/generated/...` folder and use in gameplay.

## Factory-side change requested

Add or update a prop spec, run the prop workflow, validate the deliverables, and include IMT-facing handoff metadata.

## Asset / workflow details

- Asset family / workflow name: `example_magic_station`
- Variants or states:
  - `imt_example_magic_station_inactive`
  - `imt_example_magic_station_active`
- Target canvas size: `128x256`
- Anchor / pivot rule: bottom-center anchor at `(64, 255)`
- Transparency/background rule: final PNGs must be RGBA with clean transparent background; no floor tile, frame, text, or watermark.
- Target project folder: `img/generated/example_magic_station/`
- Required metadata fields: asset IDs, relative deliverable paths, atlas rects, anchor, footprint, validation status.
- Provider/model preference: `gpt_image` / `gpt-image-2` via color-key cleanup, unless blocked.
- Provider/model constraints: do not request native transparent background from `gpt-image-2`.

## References and source context

- Source repo scene or gameplay file needing this asset.
- Any existing art direction screenshot.
- Any previous factory run whose style should be reused.

## Acceptance criteria

- [ ] `deliverables/imt_example_magic_station_inactive.png` exists.
- [ ] `deliverables/imt_example_magic_station_active.png` exists.
- [ ] PNGs are `128x256` RGBA with clean alpha.
- [ ] `deliverables/imt_prop_handoff.json` points to `img/generated/example_magic_station/`.
- [ ] `validate-prop-assets` reports pass.
- [ ] Existing wall/floor workflows are untouched.

## Non-goals / do-not-change

- Do not modify IMT code from this factory request.
- Do not change canonical wall/floor placement rules.

## Factory response

- Status: example
- Summary: This is only a template example; no implementation was performed.
- Changed files: none
- Commands run: none
- Outputs / run roots: none
- Blockers or follow-up: Replace this example with a concrete dated request file.
