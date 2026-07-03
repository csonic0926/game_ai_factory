# Game ISO Mapping Review Plan

## Status

Prepared for handoff to Codex app because the current CLI session showed output-text corruption during review.

## Goal

Review and redesign the wall game-iso mapping path so the post-Step-3 workflow matches the actual product rule:

1. Step 3 emits 6 cleanup candidates.
2. Step 4 picks the least-destructive valid cleanup candidate.
3. Step 6 maps that chosen candidate into canonical game-iso wall placement.
4. Step 7 verifies mapping correctness.

The key product priority is **mapping correctness**, not enforcing a fixed generated wall thickness.

## Findings captured so far

- Current wall mapping entry points are in `pipeline/variant_selector.py`:
  - `select_variant_pool()`
  - `score_candidate()`
  - `render_final_output()`
  - `_render_wall_output()`
- Current wall path already maps **only one chosen cleanup candidate**.
- Current wall mapper is a **backbone-first 6-point warp**:
  - `_derive_wall_source_polygon()` extracts a 6-point source polygon.
  - `_warp_rgba_polygon()` warps the full RGBA plane using mean value coordinates.
  - `_apply_polygon_mask()` and `_apply_opaque_half_rule()` finalize the canonical wall body.
- The current 6 source points are not all directly observed:
  - observed: `face_bottom`, `face_top`, `apex`, `top_outer`, `bottom_outer`
  - derived: one affine-projected geometry point
  - practical shape: **3 backbone points + 2 outer-edge points + 1 derived point**
- Current verification still depends on mask-shape thresholds:
  - `normalized_iou`
  - `anchor_error`
  - width / height scale ratio
  - shoulder / mid inset
  - bottom tip drift
- This may conflict with the product rule that wall thickness variation is acceptable as long as game-iso mapping is correct.

## Next review steps

1. Summarize current mapping failure surfaces.
2. Separate:
   - true mapping errors
   - over-strict shape/thickness verification errors
3. Infer the intended acceptance contract for walls:
   - skew / anchor / contact-edge correctness matters most
   - thickness variation should be tolerated unless it breaks mapping semantics
4. Propose a revised Step 6 / Step 7 contract.
5. Implement and validate the redesign.

## Likely redesign direction

### Step 6

Keep Step 6 focused on:
- mapping the chosen cleanup candidate into canonical game-iso placement
- preserving painted wall thickness
- using a continuous full-plane RGBA warp

### Step 7

Reduce Step 7 to mapping verification, with checks biased toward:
- side correctness
- contact-edge correctness
- top edge / backbone alignment
- anchor placement
- bottom tip placement

Potentially relax or remove checks that mainly punish thickness variance:
- effective width too small
- shoulder inset too large
- mid inset too large

only keep them if they are truly required to detect mapping failure rather than harmless stylistic thickness variance.

## Handoff note

Because the CLI output became unreliable, continue this review from Codex app using this file plus:
- `docs/REPO_MEMORY.md`
- `docs/CURRENT_JOB.md`
- `pipeline/variant_selector.py`
- `pipeline/reference_pair_workflow.py`
