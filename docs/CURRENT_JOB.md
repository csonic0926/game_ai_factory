# CURRENT_JOB.md

## Job

Shift the tile factory from raw-render-driven final placement toward **game-facing 2D canonical placement rules**, starting with walls.

## Current understanding

- The factory should not use world/map coordinates directly.
- Left/right wall naming is defined by which **top edge of the floor tile** the wall attaches to:
  - `left wall` = top-left edge
  - `right wall` = top-right edge
- For factory purposes, this should be expressed as pure 2D rules:
  - canvas size
  - opaque half
  - contact edge
  - body polygon
  - height extension rule
- Raw Blender renders are not canonical truth for final placement.
- `1 tile unit = 128 x 128`.
- `wall 2u` final canvas should be `128 x 256`.

## Active plan

1. Rewrite canonical spec into pure 2D factory language.
   - Avoid world-coordinate framing.
   - Keep only factory-usable geometry and placement fields.
2. Correct left/right wall semantics.
   - left wall = top-left edge, body in left half, right half transparent
   - right wall = top-right edge, body in right half, left half transparent
3. Make final fitter use canonical targets instead of raw render bbox.
4. Limit current implementation scope to walls first.
5. Verify 1u/2u wall final outputs for:
   - correct canvas size
   - correct occupied half
   - mostly transparent opposite half
   - reasonable contact-edge placement

## Progress so far

- Added `examples/workflow_references/canonical_tile_spec.json`.
- Started wiring `pipeline/variant_selector.py` to read canonical wall targets.
- `wall 2u` final export now uses `128 x 256` canvas.
- Reframed the canonical spec toward pure 2D factory fields (`attach_edge`, `opaque_half`, `transparent_half`, `height_units`).
- Added a wall-specific fitter path that maps the source wall alpha bbox into the canonical wall bbox before polygon/half masking.
- Wall final alpha is now driven directly by the canonical polygon + half mask instead of the raw source alpha silhouette.
- Current left-2u test now lands at canonical size/bbox (`128x256`, bbox near `0,0,65,225`).
- Confirmed the wall generation helper had left/right reference images swapped for Gemini input (`rot0` vs `rot90`) and corrected the mapping in `itf.py`.
- Remaining issue: validate left/right naming and contact-edge semantics, then run the same fitter path on the right-wall case.

## Newly confirmed pipeline diagnosis

- The failed candle-wall run exposed a **spec-path problem**, not just a generation-quality problem.
- The direct/generated spec used for that run did **not** preserve wall height as a structured field in `variant_profiles`.
  - The selector later inferred canonical target from free text and fell back to `wall_left_1u` / `wall_right_1u`.
- The failing run specs also had a **reference handedness mapping error**:
  - original 2u dual-variant spec mapped left/right refs opposite to intended handedness
  - later right-only retry pointed to the same `rot90` reference as the left retry
- Resulting consequence chain:
  1. requested `2u` job degraded to `1u` canonical fitting
  2. left/right semantic conditioning degraded because both sides could point at left-like reference input
  3. validator could still report `pass` on the wrong semantics because it validated against the same wrong reference mapping
  4. final fitter could hide some raw-generation geometry errors by imposing canonical alpha after resize

## Immediate interpretation

- Current blocker is not “Gemini is bad at walls” in isolation.
- The factory pipeline is currently too dependent on:
  - prose-only height cues
  - correct external spec assembly
  - reference integrity that is not preflight-asserted
- Before any future wall regeneration is trusted, diagnose the request/spec/selector chain first, then generator quality second.

## Completed fixes

- `itf.py` wall spec builder now emits structured wall metadata per variant:
  - `wall_side`
  - `height_units`
  - `reference_rotation`
- `pipeline/reference_pair_workflow.py` now:
  - preserves that wall metadata in normalized spec/request payloads
  - rejects wall specs that omit structured `height_units`
  - rejects wall refs whose rotation contradicts handedness (`left -> rot90`, `right -> rot0`)
  - rejects left/right wall pairs that resolve to the same underlying image content
  - injects stronger wall-side + height instructions into the generator prompt
- `pipeline/variant_selector.py` now derives `wall_left_1u/2u` and `wall_right_1u/2u` from structured wall metadata first, so 2u no longer silently falls back to 1u when prose is incomplete.
- Updated example wall spec to match the repo wall-reference convention and include structured wall metadata.

## Newly confirmed after rerun

- The rerun at `/tmp/imt_reference_pair_runs/stone_wall_candle_2u_pair_20260410` used a manually authored spec that still swapped handedness:
  - `left -> 102_wall_straight_2u_rot0.png`
  - `right -> 102_wall_straight_2u_rot90.png`
  - and also declared `reference_rotation` values that matched that swapped mapping
- This showed one remaining hole in the previous fix:
  - loader was trusting `reference_rotation` from the spec
  - it should instead enforce canonical handedness (`left -> rot90`, `right -> rot0`) and reject contradictory declared metadata
- Another confirmed issue: wall selector was still scoring candidates against the **raw reference silhouette**, while wall final output is canonicalized.
  - Result: left raw 2u could be visually acceptable, and final fitted output could be correct 2u, but selection still rejected it due to raw wall-thickness silhouette drift.
  - Fix direction: canonicalize the reference mask too, then score canonicalized wall output vs canonicalized wall target.

## Additional completed fixes

- `pipeline/reference_pair_workflow.py` now rejects specs whose declared `reference_rotation` contradicts canonical left/right wall handedness.
- `pipeline/variant_selector.py` now scores wall candidates against the **canonical fitted reference mask** instead of the raw wall reference silhouette.
- Re-running selector on the rerun root now produces:
  - `final/selected_left.png`
  - `final/selected_right.png`
  - both as `128x256` wall outputs instead of null selection.

## Newly completed for issue 4

- Replaced the old wall finalizer behavior that overwrote alpha with the canonical wall mask.
  - That old path could create fake opaque black regions inside the final wall where Gemini had painted nothing.
- Tried a piecewise triangular deform first, but discarded it after visual review because it introduced colored seam artifacts.
- Wall final export now uses a **continuous 5-point wall warp** instead:
  - preserve painted wall thickness
  - align the wall face to canonical game-iso anchors
  - align outer top/bottom thickness toward the required game-iso edges
  - avoid synthetic black opacity and avoid triangle seam lines
- Current source-anchor contract:
  - left wall:
    - `face_top = (x=0,min_y)`
    - `apex = center_x on face_top row`
    - `top_outer = rightmost pixel on face_top row`
    - `bottom_outer = rightmost pixel on face_bottom row`
    - `face_bottom = (x=0,max_y)`
  - right wall mirrors the same logic from the right edge / leftmost outer points
- Current target geometry:
  - left wall anchors:
    - `face_top (0,32)`
    - `apex (64,0)`
    - `top_outer (127,32)`
    - `bottom_outer (64,255)`
    - `face_bottom (0,225)`
  - right wall mirrors that:
    - `face_top (127,32)`
    - `apex (64,0)`
    - `top_outer (0,32)`
    - `bottom_outer (64,255)`
    - `face_bottom (127,225)`
- Implementation detail:
  - final warp is done with **mean value coordinates** over the 5-point source/destination wall polygon, which keeps the deform continuous.
  - outer thickness points are no longer hard-mapped to fixed corners first; the pipeline now:
    1. solves a 3-point affine from `face_top / face_bottom / apex`
    2. maps `top_outer / bottom_outer` through that affine
    3. projects those two outer points **vertically** onto the target top/bottom iso edges
- Wall selection scoring still evaluates **wall-face coverage inside the canonical polygon** rather than the full thick silhouette.
- Re-ran selector on the current successful 2u candle-wall runs after switching to the continuous warp:
  - left run: `classic_dungeon_stone_wall_candlelight_2u_left_retry_20260411`
  - right run: `classic_dungeon_stone_wall_candlelight_2u_20260411`
  - both remain selectable and produce final outputs successfully.

## Next implementation focus

- Refactor the canonical spec wording/fields to be explicitly 2D-factory-oriented.
- Add wall-specific fitter behavior:
  - enforce occupied half
  - enforce contact-edge landing
  - avoid using raw reference bbox as final truth
  - verify the same behavior on right-wall generation and on future re-generated walls

## Trial update

- Tried the six-point wall hexagon mapping path instead of the previous face-only affine fallback.
- Current wall final export now warps source wall pixels through a derived six-point wall polygon and then reapplies the canonical polygon/half rules.
- Smoke tests on the golden wall references now land cleanly in:
  - `wall_left_1u` -> bbox `(0, 0, 65, 97)`
  - `wall_right_1u` -> bbox `(64, 0, 128, 97)`
  - `wall_left_2u` -> bbox `(0, 0, 65, 225)`
  - `wall_right_2u` -> bbox `(64, 0, 128, 225)`
- This is good enough to treat the six-point mapping as a successful trial for now; next refinement can be about whether the hexagon should be tuned further, not whether the approach is viable.

## April 11 rollback note

- The attempt to add outer-thickness constrained deform drifted away from game-iso correctness.
- Rolled wall final export back to the simpler **3-point face affine map** for now:
  - source anchors from `_wall_source_face_anchors()`
  - target anchors from `_wall_target_face_anchors()`
- Next work should start from this simpler face-first baseline instead of the 5-point / outer-edge variants.

## April 15 — perspective skew finalization

- Replaced the mean-value-coordinate warp with a **4-point perspective transform** for wall final export.
- Approach:
  1. Fit four edge lines (face, top, bottom, outer) to the source alpha mask via least-squares.
  2. Intersect the four lines to find four body corners — works even when a corner falls outside the source canvas (pure math, no pixel detection needed for off-canvas points).
  3. Solve an 8-coefficient homography mapping source corners → canonical body polygon.
  4. Apply PIL `Image.PERSPECTIVE` transform (runs in C, no seam artifacts).
  5. Clip to the 4-point body polygon + opaque-half rule.
- Edge detection notes:
  - Face and outer edges: scan leftmost/rightmost opaque pixels per row in the middle 60 % of vertical range.
  - Top edge: scan topmost pixel per column in the face-side 55 % of columns.
  - Bottom edge: skip 25 % of columns near the face to avoid the wall-base taper region.
- Tested on both left and right 2u walls:
  - Left wall: top slope −0.505, bottom slope −0.528 (target −0.500). IoU 0.941 vs reference.
  - Right wall: renders correctly; low IoU is Gemini generation quality, not the transform.
- Also fixed the polygon mask: the old 6-point `_wall_canonical_polygon` hexagon was broken for right walls. Now uses the 4-point body polygon directly for masking.
