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
