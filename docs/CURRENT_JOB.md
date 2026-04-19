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

## Newly completed for retry closed loop

- `generate_reference_pair()` now supports a bounded end-to-end retry loop (`max_attempts`, default 3).
- The loop now treats **wall + floor** jobs as selector-capable closed-loop runs when their variants are supported by `variant_selector`.
- Per attempt, the workflow now does:
  1. provider generation
  2. raw validation
  3. selector/finalization when needed
  4. final validation on delivered outputs
  5. retry if the delivery still fails
- Successful raw validation now still writes deliverable outputs to `final/selected_<variant>.png`, so even already-good runs produce a final handoff artifact.
- Attempt snapshots are preserved under `run_root/attempts/attempt_XX/` with generated / processed / validation / selection / final artifacts for debugging.
- CLI now exposes `--max-attempts` on both `generate-reference-pair` and `generate-wall-reference-pair`, and returns non-zero when the closed loop still fails after exhausting attempts.

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

## April 15 — wall prompt builder correction

- Confirmed the Gemini prompt problem for wall runs was in the **factory prompt builder**, not in the external skill/spec alone.
- Previous wall prompt assembly over-explained geometry in prose (`attach to top-left edge`, `leave opposite half empty`, `do not mirror`) even though the wall reference image/sheet already carried that structure.
- Updated `pipeline/reference_pair_workflow.py` so wall prompts now:
  - treat the supplied wall reference as the **exact geometry lock**
  - explicitly freeze silhouette / handedness / occupied side / contact edge / proportions to the reference
  - move prose emphasis toward **height preservation + surface/style direction**
  - reduce tile-system-style geometric narration that was acting as model noise
- Floor prompt behavior remains unchanged; the prompt-builder correction is wall-specific.

## April 15 — structured external prompt parts

- Tightened the external prompt contract so callers can pass:
  - `prompt_parts.style`
  - `prompt_parts.material`
  - `prompt_parts.decoration`
  - `prompt_parts.negative_constraints[]`
- Goal:
  - keep external inputs short and concrete
  - let the factory add the longer prompt scaffolding
  - reduce overfit / contradictory geometry prose from external repos or skills
- For wall variants:
  - `variant_profiles.<variant>.geometry_guidance` is now ignored by prompt assembly
  - geometry is taken from the reference lock plus structured wall metadata (`wall_side`, `height_units`, `reference_rotation`)
- Legacy `prompt` and `negative_prompt` are still accepted and normalized into `prompt_parts` for backward compatibility, but README now documents `prompt_parts` as the preferred contract.

## April 15 — wall reference input correction

- Confirmed a remaining factory mistake: wall pair runs were still sending the shared `reference_pair_sheet.png` to Gemini for both left and right variants.
- This is wrong for walls because left/right are not a height pair; each wall variant must receive its own canonical reference image:
  - left task -> `rot90`
  - right task -> `rot0`
- Updated `prepare_reference_pair_run()` so:
  - floor dual-variant runs can still use the shared pair sheet
  - wall variants now always use their own per-variant reference image as the generation input, even when both variants are requested in one run
- The pair sheet can still be created as a debug artifact, but wall generation no longer depends on it.

## April 15 — preprocessing gate before wall mapping

- Confirmed another workflow bug from the failed rerun: a wall image could fail to produce any usable keyed silhouette after chroma-key preprocessing, but the pipeline still continued into geometry mapping / selector scoring.
- Added a wall-specific preprocessing gate in `validate_reference_pair_run()`:
  - inspect the keyed default output plus all emitted color-key variants
  - require at least one candidate that:
    - has an opaque silhouette bbox
    - does not still fill the whole canvas
    - does not fail top-boundary key-color contamination
- If no usable keyed silhouette variant exists:
  - mark that wall variant as `hard_fail`
  - replace the failure reason with a preprocessing-gate failure
  - skip selector/mapping in the closed-loop retry path for that attempt
- This makes the retry loop distinguish:
  - **workflow/preprocessing failure** (no clean退地 result)
  - vs **generation geometry failure** after a usable silhouette exists

## April 15 — wall selector green-fringe fix

- Confirmed another downstream workflow bug while inspecting `selection/.../*.final.png`:
  - wall selector finals could still show opaque green fringe / fill even when the processed keyed candidates no longer had visible green background
  - root cause was the wall perspective warp sampling straight RGBA during `Image.PERSPECTIVE`, which let chroma-key edge RGB bleed back into opaque pixels
- Fixed `pipeline/variant_selector.py` so wall perspective warp now:
  - premultiplies RGBA before the perspective transform
  - un-premultiplies after the transform
- Result:
  - selector `final.png` artifacts are no longer expected to show large opaque `#00FF00` carry-through when the processed keyed inputs are already clean

## April 15 — selector semantics split into source vs final

- Continued the workflow cleanup by making selector/debug semantics explicitly two-stage:
  - `source_*` = source eligibility problems before trusting the candidate as a clean wall source
  - `final_*` = post-map game-iso fit problems after canonical wall mapping
- Updated `pipeline/variant_selector.py` fail-reason naming accordingly.
- Updated README + the wall workflow documentation so the documented wall workflow now reads:
  - preprocessing gate
  - source eligibility
  - map back to canonical game iso
  - final-fit selector

## April 15 — selector implementation workflow refactor

- Brought selector implementation closer to the documented staged workflow instead of only renaming fail reasons.
- `select_variant_pool()` now evaluates wall candidates in explicit stages:
  1. source eligibility
  2. mapped game-iso candidate generation
  3. final-fit validation
  4. winner selection
- Source-stage failures no longer conceptually mix with final-fit failures in one undifferentiated bucket.
- Score rebound / cutoff logic now operates on source-pass candidates only, so obviously invalid source candidates do not distort later final-fit selection behavior.

## Next section plan — wall canonical game-iso mapper redesign

### Goal

Replace the current wall **4-point perspective body warp** with a wall-specific **backbone-first 6-point game-iso mapping** that can align both:

- the wall back / face plane
- the wall body thickness / outer extension

The key reason is that wall sources do **not** fill the full canonical iso wall body the way floors fill their base. Some structurally important target points live in:

- transparent image space
- or even outside the source PNG bounds

So a direct visible-corners-only warp is not a reliable contract for walls.

### Newly clarified mapping requirement before implementation

The 6-point wall mapper must transform the **entire RGBA image plane**, including transparent pixels.

This must **not** be implemented as:

- moving only non-transparent / colored pixels
- stretching the visible painted silhouette to reach the 6 target points
- treating transparent space as ignorable empty area

Instead, wall mapping must be treated as:

- a continuous image-space warp over the full source canvas
- with RGBA sampled consistently from the source plane
- where derived structure points may legitimately lie in transparent space or outside the source bounds

This clarification matters because several wall target structure points are geometric support points, not guaranteed visible painted corners.

### Current limitation to replace

Current live implementation in `pipeline/variant_selector.py`:

- detects 4 visible wall-body corners from the source alpha
- maps those 4 corners directly to the canonical wall body
- clips to the canonical wall polygon / opaque half

Observed weakness:

- can roughly align the visible face plane
- does **not** sufficiently constrain wall thickness / wall-body extension
- likely causes final-fit failures such as:
  - width too small
  - anchor drift
  - shoulder alignment mismatch

### Proposed new mapping contract

#### Stage 1 — detect 3 backbone points from the source

Use only points that are structurally stable and visually present in the source:

- `face_top`
- `face_bottom`
- `apex` / top ridge pivot

Purpose:

- establish the wall back / face backbone in game-iso space first
- avoid trusting weakly observed thickness corners too early

#### Stage 2 — perform backbone alignment

Use those 3 backbone points to align the wall back to canonical game-iso orientation.

This is not yet the final wall-body mapping; it is the calibration step that defines the wall’s local game-iso frame.

#### Stage 3 — derive the additional 3 structure points

After backbone alignment, derive the remaining wall-body points by extension rules rather than by raw visible-corner detection.

Expected examples:

- upper outer thickness point
- lower outer thickness point
- lower inner / contact-side extension point

Important:

- these points may lie in transparent source space
- they may lie outside the source PNG bounds
- that is acceptable because they are geometric structure points, not necessarily visible painted pixels

#### Stage 4 — build a 6-point source/target correspondence

Form the full wall mapping from:

- 3 detected backbone points
- 3 derived extension points

and map them to the canonical 6-point wall game-iso target.

#### Stage 5 — warp and finalize

After 6-point mapping:

- warp source pixels into canonical game-iso wall geometry
- then apply:
  - canonical polygon rule
  - opaque-half rule
  - contact-edge expectations

### Intended outcome

After this redesign, selector final-fit validation should judge a wall candidate that has:

- correct wall back alignment
- correct wall thickness / extension placement
- more faithful canonical game-iso body occupancy

rather than only a roughly aligned face plane.

### Implementation targets for the next section

- `pipeline/variant_selector.py`
  - replace or branch from `_render_wall_output(...)`
  - add explicit backbone-point detection helper(s)
  - add derived extension-point construction helper(s)
  - replace direct 4-corner body warp with 6-point wall mapping
- keep selector staging as already refactored:
  - preprocessing gate
  - source eligibility
  - map to canonical game iso
  - final-fit validation
  - winner selection

### Validation checklist for the next section

For the existing problematic left-wall candidates, verify whether the new mapper improves:

- final effective width
- final anchor error
- shoulder placement
- bottom-tip placement
- overall visual agreement with canonical wall body

Primary regression target:

- `output/reference_pair_runs/classic_dungeon_stone_wall_match_floor_2u_rerun_20260415_1`

## April 15 — backbone-first 6-point mapper implementation

- Replaced the wall finalizer’s **4-point perspective body warp** with a **backbone-first 6-point wall mapper** in `pipeline/variant_selector.py`.
- New implementation shape:
  1. detect 3 visible backbone points from the source wall:
     - `face_bottom`
     - `face_top`
     - `apex`
  2. solve a backbone affine between source and canonical target
  3. derive the remaining 3 source structure points by mapping the canonical outer/contact points back through that affine
  4. run a full-plane **RGBA inverse warp** over the source canvas using the 6-point wall polygon
  5. finalize with canonical polygon + opaque-half masking
- Important contract now enforced in code:
  - the wall warp samples the **full RGBA plane**, including transparent source pixels
  - derived source points are allowed to land outside the source PNG bounds
  - output is produced by continuous warp + RGBA resampling, not by relocating only opaque pixels

## April 16 — artifact naming / step diagnostics pass

- Started a repo-side artifact contract pass **without changing step 5 / step 6 algorithms**.
- Goal was limited to:
  1. make PNG / JSON names self-describing by step
  2. make it faster to see which step failed
- New step-oriented output folders now exist under each run root:
  - `step_1_raw/`
  - `step_3_cleanup_pool/`
  - `step_4_gate/`
  - `step_6_mapping/`
  - `step_7_selection/`
  - `deliverables/`
- New canonical artifact names follow the `s<step>_<kind>.<variant>[.vXX_*].png/json` pattern.
  - examples:
    - `s1_raw.left.png`
    - `s3_cleanup.left.v01_conservative.png`
    - `s4_gate.left.json`
    - `s6_mapped.left.v01_conservative.png`
    - `s7_selected.left.png`
    - `deliverable.left.png`
- Added run-level `artifact_status.json` so a reviewer can quickly scan per-variant step status without opening every folder first.
- Legacy folders (`generated/`, `processed/`, `selection/`, `final/`) are still written for compatibility; the new step folders are diagnostic aliases, not algorithm changes.

## April 16 — Step 0 review checkpoint

- Current review conclusion:
  - wall Step 0 is mostly acceptable as a deterministic safety boundary for Step 1
  - keep its preflight responsibilities for now:
    - spec/schema validation
    - wall handedness / height / reference integrity enforcement
    - generation-input routing
    - request snapshot writing
- The main Step 0 area still under suspicion is the **Gemini prompt assembly structure**, not the existence of Step 0 itself.
- Decision:
  - do **not** refactor Step 0 first
  - continue the workflow review until the Gemini generation step
  - decide the proper prompt contract there first
  - only then return to Step 0 and judge whether prompt-building should be simplified

## April 16 — Step 1 split completed

- Completed the first boundary-cleanup pass around wall Step 1 **without changing keying algorithms**.
- New intended execution boundary:
  - Step 1 = raw generation only
- Implementation change in `pipeline/reference_pair_workflow.py`:
  - `generate_reference_pair()` no longer runs `apply_color_key_to_image(...)` directly inside the provider-generation loop
- Review consequence:
  - future Step 1 discussion should treat color keying as out-of-scope for Step 1
  - next cleanup target after Step 1 review is the keyed cleanup stage boundary

## April 17 — wall Step 1 prompt simplification

- Simplified wall prompt generation in `pipeline/reference_pair_workflow.py`.
- New wall prompt contract:
  - one side-specific reference image per variant (`refs/left.png` / `refs/right.png`)
  - short prompt centered on:
    - exact geometry lock from the supplied reference image
    - no extra scene / props / text
    - chroma-key background rule
    - style direction
    - negative constraints
- Removed wall-only prompt clutter that was competing for attention:
  - no extra 1u / 2u prose reminders
  - no 1u / 2u wording inside wall `role_text`
  - no 1u / 2u wording inside wall style prompt text
  - no extra wall reinterpretation sentences
  - no outline-specific block
  - no `Reference intent` / `Extra notes` tail for wall Step 1
- Wall pair runs no longer compose `refs/reference_pair_sheet.png`.
  - prepare now leaves `reference_sheet = null` for wall pair runs
  - `generation_inputs.left/right` point directly to `refs/left.png` / `refs/right.png`
- Verified with a prepare-only 2u wall check:
  - 2u wall Step 1 still uses the correct 2u reference PNGs
  - but the generated prompt text no longer mentions `two-tile-high`, `2u`, or any other height wording
  - height is now carried only by the supplied reference image and structured metadata, not by Gemini-facing prose

## Next review target

- Step 1 prompt / reference contract is now intentionally simplified and should be treated as the current baseline.
- Next step for the wall workflow review:
  - inspect the keyed cleanup stage
  - decide whether default keyed output deserves its own processing step
  - keep Step 5 / Step 6 redesign deferred until keyed cleanup semantics are clearer

## April 17 — agent-assisted imagegen wall Step 1

- Added a new wall execution path for Codex-side image generation without treating imagegen as a normal in-repo provider call.
- Spec / Step 0 changes:
  - `provider.mode = "agent_handoff"` is now supported
  - `provider.name = "imagegen"` is the current allowed handoff backend
  - prepare writes `request/imagegen_handoff.json`
  - request metadata now preserves per-variant handoff raw output paths
- Step 1 behavior:
  - `generate-reference-pair` can now ingest externally staged raw PNGs from:
    - `agent_handoff/step_1_raw/left.png`
    - `agent_handoff/step_1_raw/right.png`
  - after ingest, the existing Step 3+ wall workflow continues unchanged
- April 17 follow-up decision:
  - removed Step 2 as an independent processing step
  - validation now uses the default candidate emitted by Step 3 cleanup-pool generation as the baseline keyed image
  - the repo now treats cleanup/keying as one Step 3 stage rather than a Step 2 + Step 3 split
- April 17 Step 3 simplification:
  - Step 3 is now defined as **deterministic six-candidate cleanup emission only**
  - Step 3 no longer writes a baseline keyed output of its own
  - Step 3 no longer exports `selected_variant` semantics
  - wall preprocessing gate now inspects the six Step 3 candidates directly
  - any choice to read one candidate as a validation baseline now belongs to validation logic, not to Step 3 itself
- April 17 post-Step-3 wall simplification:
  - Step 4 now merges gate + pick:
    - check cleanup residue / silhouette viability
    - choose the least-destructive valid candidate by fixed cleanup order
  - removed Step 5 as a distinct wall step
  - Step 6 now maps only the chosen cleanup candidate
  - Step 7 now verifies the mapped result instead of running multi-candidate rebound / cutoff selection
- April 17 Step 4 tightening:
  - tightened wall residue detection toward **four-corner / exterior-fill background residue**
  - intent is to catch leftover outside background color while avoiding false positives from interior colors that only look similar to the key color
- Current practical test status:
  - prepared a 2u left/right wall run with `provider=imagegen`
  - staged simulated Step 1 raw outputs into the handoff paths
  - verified `generate-reference-pair` resumed successfully and produced final deliverables
  - test run root:
    - `/private/tmp/itf_imagegen_test_runs/wall_2u_imagegen_test`
- Important boundary:
  - this makes imagegen usable when another Codex skill/agent is orchestrating the repo
  - it does **not** make imagegen a normal standalone provider API for non-Codex execution

## April 18 — game iso mapping review handoff

- Prepared `docs/GAME_ISO_MAPPING_PLAN.md` as the handoff plan for the next wall game-iso mapping review pass.
- Reason for handoff: current CLI session showed output-text corruption during findings review, so continue from Codex app.
- Immediate next work:
  1. summarize mapping failure surfaces
  2. separate true mapping errors from over-strict thickness/shape verification
  3. redesign Step 6 / Step 7 acceptance around mapping correctness first


## April 19 — Step 7 edge-direction validation

- Implemented the Step 6 / Step 7 contract split inside `pipeline/variant_selector.py`:
  - Step 6 remains the single wall mapping step.
  - Step 7 now validates the mapped wall by fitted edge-direction semantics instead of thickness-driven mask thresholds.
- Added wall edge validation for:
  - face edge
  - top edge
  - outer edge
  - bottom edge
- Wall pass/fail now uses:
  - approximate angle agreement with canonical wall-body edges
  - face-edge attachment-side offset guard to reject mirrored/shifted outputs
- Legacy `normalized_iou` / `anchor_error` / anchor payloads are still emitted as diagnostics, but they no longer gate wall acceptance.
- Added regression tests in `tests/test_variant_selector_wall_validation.py` covering:
  - thicker-but-aligned pass case
  - mirrored fail case
  - slumped-top fail case
  - real wall reference mapping smoke passes for left/right 1u/2u

## April 19 — 2u stone wall Codex imagegen run

- Ran a 2u left/right wall job through the agent-handoff path:
  - spec: `examples/reference_pair_workflow/stone_wall_2u_imagegen_20260419_200320.generated.spec.json`
  - run root: `output/reference_pair_runs/stone_wall_2u_imagegen_20260419_200320`
- Direct Codex imagegen Step 1 attempts produced stone-wall art, but did not preserve the narrow canonical wall silhouette and used noisy chroma backgrounds.
  - The first raw handoff outputs were preserved under:
    - `agent_handoff/imagegen_raw_attempts/left.imagegen_raw_original.png`
    - `agent_handoff/imagegen_raw_attempts/right.imagegen_raw_original.png`
- To complete the factory run, created geometry-locked handoff composites:
  - extracted imagegen stone texture
  - composited it into the canonical left/right reference alpha/silhouette
  - used a flat `#FF00FF` background
  - staged those as `agent_handoff/step_1_raw/left.png` and `agent_handoff/step_1_raw/right.png`
- Factory Step 3+ completed and produced deliverables:
  - `deliverables/deliverable.left.png`
  - `deliverables/deliverable.right.png`
- Artifact status shows Step 4 / Step 6 / Step 7 passing for both sides.
- The outer `generate-reference-pair` result still reports `ok=false` because final validation compares 128x256 wall deliverables back against the original 256x256 reference render bbox and records soft bbox failures; the wall-specific Step 7 edge-direction verification passes.
- Follow-up issue discovered:
  - a pure imagegen raw attempt with no usable cleanup candidate triggered an AttributeError in `validate_reference_pair_run()` instead of returning a clean gate failure.
  - Fix target: guard `preprocessing_gate.get("chosen_candidate")` when it is `None`.

## April 19 — imagegen handoff path-contract fix

- Updated the imagegen handoff packet so it no longer relies on ambiguous `reference_images` paths alone.
- `request/imagegen_handoff.json` tasks now include:
  - `codex_imagegen_mode = "edit"`
  - `edit_target_image`
  - `codex_prompt_text`
  - an explicit `contract.codex_execution_protocol`
- The intended Codex-side operator flow is now:
  1. load `edit_target_image` with `view_image`
  2. invoke built-in imagegen in edit mode using `codex_prompt_text`
  3. copy the selected generated PNG from `$CODEX_HOME/generated_images/...` to the task `output_path`
- Prepared a new 2u left/right run with the enlarged golden references:
  - spec: `examples/reference_pair_workflow/stone_wall_2u_imagegen_refbig_20260419_211306.generated.spec.json`
  - run root: `output/reference_pair_runs/stone_wall_2u_imagegen_refbig_20260419_211306`
- Observed result from the first updated left edit attempt:
  - the enlarged reference + edit-style prompt still did not reliably preserve the exact narrow wall geometry.
  - Conclusion: the path-contract issue is fixed in the repo handoff, but pure imagegen geometry-lock remains unresolved.

## April 19 — return to Gemini/Nano Banana for 2u wall

- Confirmed repo `.env` contains `GEMINI_API_KEY`; credential resolver can read it via repo `.env` fallback.
- Tried `nano_banana` first:
  - run id: `stone_wall_2u_gemini_20260419_212327`
  - provider failed before image output with a fetch failure / remote side closed.
- Retried with `nano_banana_pro`:
  - spec: `examples/reference_pair_workflow/stone_wall_2u_gemini_pro_20260419_212444.generated.spec.json`
  - run root: `output/reference_pair_runs/stone_wall_2u_gemini_pro_20260419_212444`
  - raw generation succeeded for both left and right.
- Raw Gemini Pro outputs are much closer to the intended 2u wall geometry than imagegen:
  - `generated/generated_left.raw.png`
  - `generated/generated_right.raw.png`
- Factory Step 4 / Step 6 / Step 7 all pass and deliverables are written:
  - `deliverables/deliverable.left.png`
  - `deliverables/deliverable.right.png`
- However, visual review shows the final deliverables are heavily zoomed/cropped after wall mapping; the raw provider outputs look more usable than the mapped deliverables.
- Follow-up focus should be on Step 6 wall mapping/fitting behavior with the newly enlarged 2u references, not provider prompt quality first.

## April 19 — Step 6 six-point mapping/debug pass

- Reworked Step 6 to follow the requested six-point wall mapping contract more literally:
  - source points `p0/p1/p2` are the detected real points
  - source points `p3/p4/p5` are virtual points derived by affine extension from the target game-iso six-point polygon
  - the final mask is now the target six-point polygon, not the old 4-point body polygon
  - removed the post-warp `opaque_half` clipping from wall Step 6
- Added Step 6 debug PNG/JSON outputs:
  - real 3-point source markup
  - virtual 3-point + extension-line source markup
  - target game-iso six-point polygon markup
  - mapped full six-polygon output
  - raw geometry JSON
- Reran selector on the Gemini Pro 2u wall run:
  - `output/reference_pair_runs/stone_wall_2u_gemini_pro_20260419_212444`
- Step 6 debug artifacts now exist under:
  - `step_6_mapping/s6_debug.left.v_keyed.01_conservative.*`
  - `step_6_mapping/s6_debug.right.v_keyed.01_conservative.*`
- The new mapped outputs are no longer clipped to exactly half-width:
  - left bbox changed to roughly `(0, 0, 88, 224)`
  - right bbox changed to roughly `(42, 0, 128, 224)`
- Remaining visual issue:
  - the mapping still crops/warps too aggressively compared with the raw Gemini output.
  - The new debug PNGs make the likely next bug visible: the derived virtual source polygon and extension-line choice need review/tuning, especially how the visible wall thickness maps into the full six-point target.

## April 19 — Step 6 real-point correction

- User clarified the first Step 6 bug is the red real-point detection, not the provider prompt.
- Updated `pipeline/variant_selector.py` so Step 6 real points now use the face-axis opaque column:
  - left wall: extreme face axis = minimum opaque x
  - right wall: mirrored face axis = maximum opaque x
  - `p0` = min y opaque pixel on that axis
  - `p1` = max y opaque pixel on that axis
  - `p2` remains the top-row apex and was already considered correct
- The six-point warp keeps the stored target polygon winding internally (`[p1, p0, p2, ...]`) so the existing polygon order remains non-self-crossing while the debug labels show the user-defined p0/p1.
- Reran selector for the Gemini Pro 2u run:
  - left passes Step 7, bbox now roughly `0..76 x 0..223`
  - right currently fails narrowly on bottom-edge angle (`12.124°` vs `12°` threshold), but the requested p0/p1 red-point correction is in place.

## April 20 — Step 6 virtual-point correction

- User clarified the next Step 6 bug is the three virtual points.
- Updated `pipeline/variant_selector.py` so virtual points are no longer affine-derived from all old target vertices.
- Current virtual-source construction:
  - `p2_prime` = topmost opaque pixel on the outer x column (`max x` for left wall, mirrored `min x` for right wall)
  - thickness magnitude = `|p0p2|` (chosen because the user repeated `p0p2` in the p5 rule, despite one conflicting `p1p2` mention)
  - `p3 = p2 + unit(p2_prime - p2) * |p0p2|`
  - `inner_bottom_support` still comes from the previous affine support calculation; user said inner bottom itself was correct
  - `p4 = inner_bottom_support + (p3 - p2)`
  - `p5 = p1 + (p3 - p2)` and is now the outer-bottom point
- The target six-point polygon used by Step 6 now also replaces the old inner-bottom sixth vertex with the derived outer-bottom target:
  - left p5 target = `[63, 256]`
  - right p5 target = `[63, 256]`
  - old inner-bottom target `[64, 192]` is kept as support/debug data, not as final p5
- Reran selector on the Gemini Pro 2u run after this correction:
  - left/right both regenerate Step 6 debug PNG/JSON artifacts
  - both currently fail Step 7 bottom-edge-angle by the strict validator, but the virtual point construction requested by the user is now reflected in the debug artifacts

## April 20 — Step 6 robust edge-band point detection

- User noted the left side was correct only for the current cleanup result and the same keying/edge erosion risk applies to all four structural source points: `p0`, `p1`, `p2`, and `p2_prime`.
- Updated `pipeline/variant_selector.py` so Step 6 no longer depends on a single exact extreme x column / top row:
  - `p0`/`p1` are found in a narrow face-side tolerance band (`2–4px` depending on image size), choosing the topmost/bottommost opaque pixel and preferring the actual outermost side pixel on ties.
  - `p2_prime` is found in a mirrored outer-side tolerance band with the same tie preference.
  - `p2` apex is now chosen from the first few top rows by preferring the narrowest top-band span, which preserves the current apex when clean but tolerates small top-edge gaps.
- Reran selector on the Gemini Pro 2u run:
  - left points stay essentially aligned with the previously approved geometry (`p0` shifted from `[271,204]` to `[273,203]` due to the robust band picking the topmost band pixel).
  - right `p0` is corrected upward to `[740,203]` instead of the previous bad `[743,348]`.
  - Step 7 still fails after the geometry change (`left` bottom-edge angle, `right` top-edge angle), so next work should review the target/checking interpretation rather than reverting the robust source-point logic.

## April 20 — Step 6 point naming cleanup

- User clarified the previous "outer top" interpretation was wrong: current `p0..p5`, intermediate `p2_prime`, and `inner_bottom` are correct.
- Renamed Step 6 geometry/debug labels to the user's point vocabulary:
  - real points: `p0`, `p1`, `p2`
  - virtual mapped points: `p3`, `p4`, `p5`
  - support/intermediate points: `p2_prime`, `inner_bottom`
- Added the still-unhandled top-plane point to debug/JSON only:
  - source label: `top_plane_apex_opposite_unmapped`
  - target label: `top_plane_apex_opposite_unmapped = [64,64]`
  - source construction currently recorded as `p0 + (p3 - p2)` following the user's "from p0, same parallel line" description
- This new top-plane point is not yet included in the warp/control polygon; it is exposed for the next geometry fix.

## April 20 — Step 6 apex-opposite warp control

- User confirmed the currently exposed point set is correct and identified the remaining visible issue: the top-plane point opposite the apex is drifting in the final mapped image.
- Updated Step 6 rendering so `top_plane_apex_opposite` is no longer debug-only:
  - source point = `p0 + (p3 - p2)`
  - target point = `[64,64]`
  - final wall warp now uses a star triangulation around this interior control point instead of only boundary mean-value coordinates.
- The existing six boundary points remain the final polygon/mask boundary; `top_plane_apex_opposite` is an interior warp constraint.
- Reran the Gemini Pro 2u left/right selectors and regenerated Step 6 debug PNG/JSON outputs.

## April 20 — Step 6 source geometry verification overlay

- User clarified that the requested point overlay should not mark target points; it should rerun the Step 6 source-side point finding on the conservative candidate itself.
- Added a new Step 6 debug artifact for each candidate:
  - `*.01b_source_detected_geometry_points.png`
- This image overlays the conservative source image with the detected source geometry points:
  - red: `p0`, `p1`, `p2`
  - blue: `p3`, `p4`, `p5`
  - orange: support points `p2_prime`, `inner_bottom`
  - magenta: `top_plane_apex_opposite`
- Reran the Gemini Pro 2u selectors and generated left/right 01b overlays under `step_6_mapping/`.

## April 20 — Step 6 mapped-output geometry re-detection

- User corrected the geometry verification target: the point overlay should rerun point detection on the already warped mapped output (`04_mapped_full_6_polygon.png`), not on the conservative source image.
- Added a new Step 6 artifact:
  - `*.04b_mapped_detected_geometry_points.png`
- This artifact runs `_wall_mapping_geometry()` on the mapped PNG and overlays the re-detected mapped geometry points on that mapped image.
- The re-detected mapped geometry is also written into each candidate `geometry.json` under `mapped_detected_geometry`.
- Current re-detected mapped values on the Gemini Pro 2u run are close to target, e.g. apex-opposite lands near `[64,62]` left and `[63.8,61.6]` right.

## April 20 — Step 6 piecewise mesh warp fix

- User correctly identified the issue as an algorithm bug, not a validator problem: mapped `inner_bottom` must land inside solid wall pixels.
- Root cause: the previous warp constrained only the six boundary points plus `top_plane_apex_opposite`; `inner_bottom` remained an unconstrained interior support point, so scale/content could drift while boundary geometry looked close.
- Fixed `_render_wall_output()` to use a named piecewise-affine triangle mesh with both interior support points constrained:
  - boundary: `p0..p5`
  - interior controls: `top_plane_apex_opposite`, `inner_bottom`
  - triangles: top plane, left/right middle quads, and lower quads around the two interior controls
- Reran the Gemini Pro 2u selectors.
- Current mapped-output alpha check at re-detected `inner_bottom` and `top_plane_apex_opposite`:
  - left inner bottom: center alpha 255, 9x9 coverage 1.0
  - left apex opposite: center alpha 255, 9x9 coverage 1.0
  - right inner bottom: center alpha 255, 9x9 coverage 1.0
  - right apex opposite: center alpha 255, 9x9 coverage 1.0
- Left now passes Step 7; right still has a Step 7 `wall_top_edge_angle_mismatch`, likely a separate validation/edge-fitting tolerance issue after the warp algorithm fix.

## April 20 — experimental PS Distort / plane-based wall mapper

- User suggested the manual Photoshop operation is closer to Distort than mesh warp.
- Added an experimental Step 6 plane-distort path without replacing the current deliverable:
  - `*.04c_plane_distort_mapped.png`
  - `*.04d_plane_distort_detected_geometry_points.png`
- The experiment treats the wall as an iso rectangular tile with three planes:
  - `top = p0, p2, p2_prime, p0_prime`
  - `left/front = p0, p0_prime, p1_prime, p1`
  - `right/side = p0_prime, p2_prime, n, p1_prime`
- New derived source points:
  - `p0_prime = p0 + (p2_prime - p2)`
  - `p1_prime = p1 + (p2_prime - p2)`
  - `n` = lowest solid pixel along the `p2_prime` x column
- Target `p2_prime` is calculated by scaling source `|p2p2_prime|` into game iso using the source/target p0-p1 scale and the target p2->p3 direction; target `p0_prime`, `p1_prime`, and `n` are derived from that.
- Current experimental outputs look promising and visibly more like a per-plane PS Distort result, but this path is debug-only for now.

## April 20 — plane-distort promoted to official Step 6 mapper

- Cleaned up the Step 6 implementation after visual approval of the PS Distort-style approach.
- Promoted the per-plane mapper from debug-only `04c` to the official wall output path:
  - official `04_mapped_full_6_polygon.png` / final selected output now use the three-plane Distort mapper
  - removed the obsolete mesh-warp path from `_render_wall_output()`
  - retained mapped-output re-detection as `04b_mapped_detected_geometry_points.png`
- Re-ran the Gemini Pro 2u left/right selectors:
  - left: passes Step 7, selected `v_keyed.01_conservative`
  - right: passes Step 7, selected `v_keyed.01_conservative`
- Verification before commit:
  - `python3 -m py_compile pipeline/variant_selector.py pipeline/reference_pair_workflow.py`
  - `python3 -m unittest tests/test_variant_selector_wall_validation.py`
