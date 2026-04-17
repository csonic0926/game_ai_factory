# REPO_MEMORY.md

## Render visibility gotcha

- In Blender, **collection `hide_render` can effectively override object-level renderability** for this pipeline.
- So if an object has `hide_render = false` but its parent collection has `hide_render = true`, the object still will not show up in render/export.
- When debugging "object exists but did not render", check **collection render flags first**, then object flags.

## Floor reference PNG memory

- For floor reference PNG work, distinguish clearly between:
  - `floor_full_k.png` = raw Blender rendering result
  - `floor_full_k_scaled.png` = manually scaled version that actually fits in-game iso framing
- Current known issue: **raw Blender render framing is not automatically “game iso correct.”**
- So a render being geometrically valid in Blender does **not** mean it is ready to become the final workflow reference PNG.

## Floor framing rule

- When discussing floor full vs half, remember: **the meaningful difference is only Z/height**.
  - Do not let the workflow get distracted by treating full and half as separate framing problems.
  - First lock the correct **full-height framing / occupancy / game-iso fit**.
  - Then derive half-height from the same camera/framing logic.
- Current working interpretation:
  - `floor_full_k.png` is a render of a too-regular cube-like base.
  - `floor_full_k_scaled.png` is closer to the intended game-iso footprint.
  - The correction is not just “make it bigger”; it behaves like widening the tile along the **screen-horizontal top-face diagonal** so the base becomes a **rhombic prism**, not a perfect cube.
- Current working number:
  - the manual correction was about **+15.3% widening** along that diagonal
  - use this as a starting geometry target, then verify by render
- Approved current direction:
  - widening the **other** top-face diagonal produced the correct visual direction
  - keep full / half floor on that same diagonal rule
  - walls should inherit the same game-iso floor-plane basis
- Preferred fix direction:
  - change the **3D base mesh** so Blender renders closer to the desired game-iso footprint directly
  - do not rely on 2D post-scale as the long-term canonical solution

## Reference PNG rules

- When creating reference PNGs, optimize for **game-facing silhouette fit**, not for “neutral Blender render.”
- For final export placement, prefer **game-facing 2D canonical tile rules** over raw render bbox matching.
- Treat reference PNG creation as a **two-stage problem**:
  1. render stable geometry from Blender
  2. verify that the result matches **game iso occupancy/framing**
- If a raw render looks too small, too centered, or otherwise unlike the in-game iso footprint, do **not** assume it is acceptable just because the camera is technically isometric.
- For floors, use `floor_full_k_scaled.png` as proof that **post-render scaling/fitting may be required**.
- Better long-term goal for floors:
  - make the Blender floor base itself produce a render close to `floor_full_k_scaled.png`
  - then reuse that fitted base logic for walls
- Wall note:
  - after adopting the game-iso floor-plane basis, wall left/right variants should be treated as **mirror counterparts**, not as the same biased mesh rotated 90 degrees
- Wall height variants should reuse the same floor-plane basis and handedness rule.
  - adding a 2-unit-high wall should only change wall height/Z
  - do not change the approved wall footprint logic when creating taller variants
- For walls and future references, target the same principle:
  - the object should occupy the canvas at a game-appropriate scale
  - the silhouette should read like in-game iso art, not like a distant Blender preview
  - “reference correctness” includes **screen occupancy**, not only angle and proportions
- If there is a disagreement between:
  - raw Blender render fidelity
  - downstream game iso fit
  choose **game iso fit** for the workflow reference PNG.

## Canonical target rule

- Treat raw Blender renders as upstream inputs, not final placement truth.
- Final tile fitting should target a **2D canonical placement spec** (canvas, contact edge, occupied side/polygon), especially for walls.
- Wall left/right naming should be preserved as a factory-facing handedness rule and should not be inferred from visual centering.

## Reference-pair retry loop

- For wall and floor reference-pair jobs, treat generation as a **closed loop**, not a single provider call.
- The intended delivery contract is:
  1. generate raw output
  2. validate
  3. produce `final/selected_<variant>.png` deliverables
  4. validate the delivered outputs
  5. retry generation if delivery still fails
- Preserve per-attempt artifacts under `run_root/attempts/attempt_XX/` so failed retries remain debuggable instead of being overwritten in place.
- A raw validation pass is not enough by itself; the run should still leave a concrete final handoff artifact for each variant.

## Wall pipeline gotchas

- For wall jobs, **height and handedness must exist as structured fields all the way through the pipeline**.
  - If a direct/generated spec keeps height only in the run name or prose prompt, downstream selection can silently fall back to `1u`.
  - Wall specs should carry `variant_profiles.<side>.height_units` and `wall_side`; request payloads preserve these inside `wall_profile`.
  - Selector inference should use structured wall metadata first and only use prose as legacy fallback.
- **Reference-pair correctness is a hard dependency for wall validation.**
  - If left/right reference PNGs are swapped or duplicated, the generator will learn the wrong handedness and the validator may still pass because it is comparing against the wrong reference.
  - A passing wall validation is only meaningful if the request's `references.left/right` mapping was first verified.
  - Current sample-factory convention is:
    - `left wall -> rot90`
    - `right wall -> rot0`
  - Wall spec loading should reject opposite rotation mapping and reject left/right references that resolve to the same image content.
- The current wall fitter can make output alpha look canonically placed even when the source generation geometry is wrong, because the final alpha is replaced by the canonical polygon/half mask.
  - Therefore, for wall debugging, inspect both:
    1. raw/generated geometry
    2. final fitted output
  - Do not treat a plausible final silhouette alone as proof that generation semantics were correct.
- For **wall selection**, score against the **canonical fitted wall mask**, not the raw reference silhouette.
  - Raw wall references contain thickness / bevel / side-face silhouette details that are useful for generation guidance but too unstable as selector truth.
  - If selection compares final wall output against the raw reference silhouette, a geometrically acceptable 2u wall can be rejected with false `normalized_iou` / `anchor_error` failures.
  - Wall validation can still inspect raw-vs-reference drift, but wall selection should compare canonicalized reference vs canonicalized candidate.
- Wall final export should **preserve Gemini-painted thickness**.
  - Do not overwrite wall alpha with the canonical polygon mask; that creates fake opaque black fill where the model never painted content.
  - Do not use seam-prone piecewise triangle warps for final wall export; they can introduce colored stitching artifacts.
  - A working wall strategy is to warp source pixels through a **derived six-point wall hexagon** and then apply the canonical polygon + half rules afterward.
  - This lets the final placement use game-iso geometry directly without requiring a green fill or any other temporary painted backing.
  - The wall warp must act on the **full RGBA image plane**, not only on opaque/colored pixels.
    - Transparent pixels are part of the source coordinate domain.
    - Derived wall structure points may legitimately land in transparent space or outside the painted silhouette.
    - Final output should come from continuous image warping + RGBA resampling, not from dragging only visible pixels toward wall endpoints.
  - Current wall deform contract uses a **derived six-point wall hexagon** for both source and target.
    - source extraction uses the wall-side edge, top-tip apex, outer top edge, outer bottom edge, and a lower inner point.
    - the same semantic ordering is used for the canonical target so selection and final output stay aligned.
  - The implementation currently uses **mean value coordinates** over that 6-point polygon so the deform stays continuous and preserves thickness without triangle seam lines.
  - After deform, score wall geometry on the **canonical fitted wall mask** rather than the raw source silhouette.

## Artifact naming / diagnostics rule

- Keep legacy runtime folders for compatibility, but treat the **step-oriented folders** as the primary diagnostic interface for wall workflow review:
  - `step_1_raw/`
  - `step_3_cleanup_pool/`
  - `step_4_gate/`
  - `step_6_mapping/`
  - `step_7_selection/`
  - `deliverables/`
- Prefer reviewing `artifact_status.json` first when triaging a run.
- Prefer `s<step>_<kind>...` artifact names over ambiguous names like bare `final` when adding new diagnostic outputs.

## Step 0 review checkpoint

- Current working conclusion for wall workflow review:
  - Step 0 is allowed to stay **deterministic and safety-oriented**.
  - Most of Step 0 complexity is acceptable because it protects Step 1 generation:
    - input/schema validation
    - wall handedness / height / reference integrity checks
    - generation-input routing
    - request snapshot materialization
- The main Step 0 area that still looks suspicious is **Gemini prompt assembly structure**.
- Do **not** rewrite Step 0 preflight logic first.
- Instead:
  1. review the actual Gemini generation step and decide the correct prompt contract there
  2. then come back and decide whether Step 0 prompt-building should be simplified or rewritten

## Step 1 / Step 3 boundary rule

- Current repo-side review decision:
  - treat **Step 1 as raw generation only**
  - treat **Step 3 as deterministic six-candidate cleanup emission only**
- Do not let Step 1 silently perform keying inside the provider-generation loop.
- For wall workflow review:
  - if color keying artifacts appear, discuss them as Step 3 artifacts
  - do not attribute keyed outputs back to Step 1
- Post-Step-3 wall direction:
  - Step 4 = cleanup validation + least-destructive valid candidate pick
  - Step 6 = game-iso mapping of the chosen candidate
  - Step 7 = mapping verification, not multi-candidate winner selection
- Step 4 background-residue rule should bias toward **four-corner / exterior-fill detection** rather than only scanning the top boundary.
  - Goal: catch leftover outside background color
  - Avoid over-penalizing interior painted colors that merely resemble the chroma-key color

## Wall Step 1 prompt contract

- Current wall-generation direction:
  - let the **reference PNG** carry wall geometry, handedness, and height semantics
  - do **not** spend extra prompt budget restating 1u / 2u height in prose
  - do **not** let wall `role_text` or wall style text smuggle height wording back into the prompt
  - do **not** compose `refs/reference_pair_sheet.png` for wall pair runs
- Wall Step 1 should send Gemini only:
  - one side-specific wall reference PNG (`refs/left.png` or `refs/right.png`)
  - a short prompt that emphasizes:
    - exact geometry lock from the reference image
    - no extra scene / props / text
    - chroma-key background rules
    - style direction
    - negative constraints
- Prefer keeping wall prompt text short so more attention stays on:
  - the supplied reference image
  - the actual wall rendering
  - the background-color restriction

## Agent-assisted wall Step 1 contract

- Wall Step 0 may now emit an **agent_handoff** contract for Codex-side image generation.
- This is **not** a normal repo-local provider call.
  - use `provider.mode = "agent_handoff"`
  - use `provider.name = "imagegen"`
  - Step 0 writes `request/imagegen_handoff.json`
- The external Codex/imagegen side owns **Step 1 raw generation only**:
  - read prompt + reference image(s) from the handoff packet
  - write one PNG per variant to `agent_handoff/step_1_raw/<variant>.png`
  - do not perform Step 3 cleanup / selection there
- After those raw PNGs are staged, the factory resumes with `generate-reference-pair` and ingests them into the normal Step 3+ workflow.

## Why this matters

- Split `.blend` files made debugging harder because collection visibility state became part of the failure mode.
- A single sample scene is easier to validate, easier to diff mentally, and less likely to drift.
- The floor workflow already showed that manual post-scale was needed to match the actual game look.
- This means the repo must preserve the distinction between:
  - raw canonical render input
  - corrected reference PNG actually used by downstream generation

## Debug checklist

1. Check requested export collections in config.
2. Check collection `hide_render` on the target collection.
3. Check object `hide_render` on the mesh object.
4. Check object name matches `export_objects` filter.
5. Re-run validation/render against `examples/sample_factory.blend` before assuming geometry is wrong.
6. If the render exists but feels wrong, ask:
   - is this just a raw render?
   - or is this supposed to be the final workflow reference PNG?
7. For floor references, compare against the known corrected asset:
   - `examples/workflow_references/floor_height_pair/floor_full_k_scaled.png`
8. Do not collapse “render succeeded” and “reference is game-ready” into the same conclusion.
