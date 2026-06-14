# REPO_MEMORY.md

## Cross-repo requirement intake

- Canonical intake folder for requirements from other repos is `requirement_from_other_repo/`.
- Other-repo Codex agents should create one dated Markdown request file there using `REQUEST_TEMPLATE.md`.
- Factory-side Codex should treat the request file as the source of truth, implement the smallest factory-side change that satisfies it, and append a short factory response to the same request file.
- Older notes that mention `requirement_from_others/` are historical; use the singular `requirement_from_other_repo/` for new requests.

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

## Wall 2u target-height correction

- Corrected wall Step 6 target contract: **2u wall mapping uses a `128 x 192` target canvas**, not `128 x 256`.
- Source-side Gemini/raw cleanup point extraction can remain unchanged when it is already correct.
- The fix is on the **target mapping points only**:
  - for the old 2u target coordinates, keep points at `y <= 64` unchanged
  - for target points with `y > 64`, subtract `64` from `y`
- Keep `top_plane_apex_opposite = (64, 64)` unchanged; it is exactly the boundary between unchanged and shifted target rows.

## Wall Step 7 edge-sampling note

- A visually correct mapped wall can still fail Step 7 if bottom-edge sampling picks an isolated thickness/taper outlier instead of the main contact-edge run.
- Current fix:
  - keep top/bottom sampling mirror-symmetric for left/right walls
  - after raw top/bottom edge extraction, keep the **largest consistent per-column edge run**
  - this prevents a single stray endpoint sample from skewing the fitted angle
- Use this before loosening wall angle thresholds; the failure mode is often sampling contamination, not wrong wall geometry.

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
- Step 7 wall acceptance should validate the **mapped output silhouette** as a game-iso wall, not re-check the Step 6 transform math.
  - Primary pass/fail signal is now whether the delivered wall's visible edges follow the expected game-iso edge directions.
  - Treat alignment as **angle/slope agreement**, not full-edge coincidence.
  - Keep thickness-sensitive mask/anchor metrics only as diagnostics for wall runs.
  - Keep one attachment-side position guard: the wall face edge should still land near the canonical attached side so mirrored outputs do not pass on angle alone.

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

## Prop asset workflow boundary

- Prop/object asset work should be added as a separate workflow/schema instead of stretching `reference_pair_workflow_v1`.
- Preserve existing floor/wall reference-pair behavior; new prop code should be additive and should not change wall/floor selector thresholds, canonical wall/floor targets, or reference-pair prompt assembly.
- For the first prop vertical slice, optimize for **engineering handoff correctness**:
  - fixed RGBA canvas
  - clean transparent background
  - bottom-center anchor
  - bbox margins / center / bottom-contact checks
  - no baked-in floor tile
  - no text/watermark
  - pair consistency across state variants
- Use the step-oriented artifact style for prop diagnostics too, but do not force wall-only Step 6 mapping semantics onto props.
- For real-provider prop runs:
  - keep `mock` and `direct` providers additive; do not route prop generation through reference-pair selector/finalizer.
  - `edit_from` prop states must use the already-cleaned/normalized source asset PNG as the reference image.
  - write provider request snapshots under `request/provider_request_{asset_id}.json` and `request/provider_requests.json`.
  - preserve raw provider output in `step_1_raw/` and cleanup candidates in `step_3_cleanup_pool/`.
  - provider outputs may arrive as 1024px opaque-background images; prop cleanup now samples corner background colors and then normalizes the cleaned object onto the requested prop canvas.
  - bottom-corner opaque pixels are valid for prop legs/bases; text/watermark heuristics should focus on top-corner marks unless a future case proves otherwise.
  - broad brazier bowls can trip floor-diamond heuristics if the threshold is too low; use both side-floor occupancy and near-anchor span, and keep true floor tiles rejected by full-width span.
  - `imt_prop_handoff.json` is the IMT-facing contract; paths inside it should be relative to `deliverables/`.
- For GPT Image prop runs:
  - `gpt-image-2` rejects native transparent background, so do **not** use `gpt_image_transparent_prop` for this model.
  - use `provider.name = "gpt_image"`, `provider.mode = "gpt_image_prop_color_key"`, `model.name = "gpt-image-2"`, and `background.mode = "color_key"`.
  - prompt for a flat solid `#FF00FF` background, with `#00FF00` as fallback; do not ask the model to output alpha.
  - Step 3 should keep every cleanup candidate and write `prop_cleanup_score.<asset_id>.json`.
  - Cleanup selection should compare the raw image to each cleaned candidate: reward removal of border-connected key background, reward preservation of non-background object pixels/RGB, and penalize retained key fringe or object deletion.
  - The selected cleanup candidate is then normalized, validated, and handed off to IMT; the validator remains pass/fail and should not become the candidate selector.
  - Treat `canvas` as the **final deliverable canvas**, not the provider source canvas.
  - Prop specs may include `generation_canvas`, but the default is already:
    - `strategy = derive_from_final_canvas`
    - `target_long_edge = 1024`
    - `preserve_aspect_ratio = true`
  - Current derived example:
    - final `128x256` -> source hint `512x1024` with aspect ratio `1:2`
  - Provider adapters must record `generation_canvas`, `adapter_decision`, and `provider_generation_args` in request snapshots so debug review can distinguish:
    1. caller final canvas
    2. factory-derived source geometry
    3. actual provider-facing fallback
  - For mock/high-res prop generation, do **not** stretch the final 128x256 sprite to fill the provider canvas.
    - Keep the prop as a smaller bottom-anchored cutout inside the larger source canvas, so normalization/validation behavior stays representative of real provider output.

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

## CLIProxyAPI GPT Image 2 provider

- The repo now exposes a **public provider/model split** for Step 1 execution.
- Canonical external contract:
  - `provider.name = "cliproxyapi"` + `model.name = "gpt-image-2"` for direct local CLIProxyAPI execution
  - `provider.name = "gemini_cli"` + `model.name = "nano-banana-2"` or `nano-banana-pro`
  - `provider.name = "agent_handoff"` + `model.name = "gpt-image-2"` for Codex handoff mode
- Legacy aliases remain accepted but should be treated as compatibility input only:
  - `gpt_image_2`
  - direct `imagegen`
  - `nano_banana`
  - `nano_banana_pro`
  - `imagegen_handoff`
- Direct GPT Image 2 provider resolution order:
  1. `CLI_PROXY_API_BASE_URL` / `CLI_PROXY_API_KEY`
  2. `CLIPROXYAPI_BASE_URL` / `CLIPROXYAPI_API_KEY`
  3. `~/.cli-proxy-api/config.yaml`
  4. fallback defaults `http://127.0.0.1:8317/v1` and `local-dev-image-key`
- Current repo limitation: direct GPT Image 2 backend supports **0 or 1 reference image** per variant in this repo wrapper.
  - single-reference variants use `/images/edits`
  - zero-reference variants use `/images/generations`
  - multi-reference variants should still use Gemini/Nano Banana or a future dedicated mapping layer
- CLIProxyAPI service compatibility note:
  - Homebrew `cliproxyapi 6.9.30` on this machine exposed only text routes even though upstream `main` already had image handlers.
  - Root endpoint advertisement can be stale/incomplete; do **not** treat missing `/v1/images/*` in `GET /` as proof that image routes are unavailable.
  - Real truth is whether `/v1/images/generations` and `/v1/images/edits` return non-404.

## Codex imagegen wall run gotchas

- Codex imagegen can be used for wall Step 1 only through the handoff path; Python still cannot call it directly.
- In the first real 2u wall run, imagegen produced visually useful stone texture but did **not** reliably obey:
  - the exact wall reference silhouette
  - the flat chroma-key background requirement
- When imagegen ignores the silhouette, do not treat that as a Step 6/Step 7 mapping problem first; inspect the raw `agent_handoff/step_1_raw/*.png` and compare it to `refs/<side>.png`.
- If the generated background is noisy/gradient instead of exact `#FF00FF` / `#00FF00`, Step 4 cleanup can fail before mapping.
- A practical manual rescue for this class of test run is:
  1. preserve the raw imagegen attempts under a debug folder
  2. extract imagegen stone texture only
  3. composite that texture into the canonical reference alpha/silhouette with a flat chroma background
  4. stage the geometry-locked composite as the handoff raw PNG
- Treat that rescue as a debug workaround, not as proof that pure imagegen Step 1 is already reliable.
- The handoff packet now includes a Codex-specific edit-mode contract:
  - `edit_target_image`
  - `codex_imagegen_mode = "edit"`
  - `codex_prompt_text`
  - `contract.codex_execution_protocol`
- This fixes the **handoff path ambiguity**: Codex must load the exact local reference image with `view_image` before invoking imagegen because the built-in imagegen tool does not consume arbitrary filesystem paths directly.
- Early test with enlarged 2u references still showed that imagegen may ignore exact silhouette even in edit-style prompting, so the path-contract fix is necessary but not sufficient for geometric correctness.

## Wall Step 6 six-point debug contract

- Step 6 should follow the user-requested wall mapping contract:
  - detect 3 real source points
  - derive 3 virtual source points by extending the source coordinate frame
  - map the resulting 6-point source polygon to the target game-iso 6-point polygon
  - warp the full RGBA plane through that polygon
- Do **not** map to a 6-point polygon and then clip back to the old 4-point body polygon / opaque-half mask; that reintroduces the old "forced half wall" failure.
- Step 6 now writes debug artifacts for each mapped wall candidate:
  - `s6_debug.<variant>.<candidate>.01_source_real_3_points.png`
  - `s6_debug.<variant>.<candidate>.02_source_virtual_3_points_and_extension_lines.png`
  - `s6_debug.<variant>.<candidate>.03_target_game_iso_6_points.png`
  - `s6_debug.<variant>.<candidate>.04_mapped_full_6_polygon.png`
  - `s6_debug.<variant>.<candidate>.geometry.json`
- The virtual-point debug PNG must include extension lines because virtual points may be outside the original source image.

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

## Wall Step 6 real-point rule

- For wall Step 6 debug/mapping, the three red source points must follow the user-defined face-axis rule:
  - `p0` = opaque pixel on the face-axis extreme x column with minimum y
  - `p1` = opaque pixel on the same face-axis extreme x column with maximum y
  - `p2` = apex/top-row ridge point
- For left wall, the face-axis extreme x is minimum opaque x; for right wall, use the mirrored maximum opaque x.
- Do not substitute a ratio-derived shoulder row for `p1`; if `p1` is wrong, the later p1→p2 / virtual-point geometry will be wrong.

## Wall Step 6 virtual-point rule

- Step 6 virtual points should follow the user-defined extension geometry rather than deriving every virtual point from the old six-point target by affine back-projection.
- Required source construction:
  - `p2_prime` = topmost opaque pixel on the outer x column (`max x` for left wall; mirrored `min x` for right wall)
  - use the direction from `p2` through `p2_prime`
  - use `|p0p2|` as the extension magnitude unless the user later resolves the single conflicting `p1p2` wording differently
  - `p3 = p2 + direction * |p0p2|`
  - `inner_bottom` is a support point, not final `p5`
  - `p4 = inner_bottom + (p3 - p2)`
  - `p5 = p1 + (p3 - p2)`; this is the true outer-bottom point
- The target mapping polygon must likewise use the derived outer-bottom target as the sixth mapped point; keep old inner-bottom only as support/debug data.

## Wall Step 6 robust point detection rule

- Do not rely on a single exact extreme x column for Step 6 source points after background removal/keying.
- `p0`, `p1`, `p2`, and `p2_prime` may all need tolerance because edge pixels can be discontinuous or eroded by 1–2 px.
- Use narrow side bands for source structural point detection:
  - face-side band for `p0`/`p1` (`min x..min x+tolerance` for left, mirrored `max x-tolerance..max x` for right)
  - outer-side band for `p2_prime` (`max x-tolerance..max x` for left, mirrored `min x..min x+tolerance` for right)
  - top-row band for `p2`, preferring the narrowest top span to avoid single-row keying damage
- Tie-breaks should prefer the actual side extreme within the band so clean inputs still match the exact-column rule.

## Wall Step 6 point naming convention

- Use the user's point names in Step 6 debug artifacts and geometry JSON:
  - `p0`, `p1`, `p2` = real points
  - `p2_prime` = intermediate direction probe, not a final mapped polygon point
  - `inner_bottom` = support/intermediate point, not `p5`
  - `p3`, `p4`, `p5` = virtual mapped polygon points
- The additional top-plane point opposite the apex should be tracked separately until it is wired into mapping:
  - target game-iso coordinate: `[64,64]`
  - source-side construction: extend from `p0` using the same `p2p3` parallel vector
  - do not call this point `outer top`; that caused ambiguity with `p3`/`p2_prime`.

## Wall Step 6 apex-opposite control point

- The top-plane point opposite the apex is a real warp control point, not just a debug label.
- Source construction: `top_plane_apex_opposite = p0 + (p3 - p2)`.
- Target game-iso coordinate: `[64,64]`.
- Keep the six mapped p0..p5 points as the wall boundary/mask, but include the apex-opposite point as an interior constraint so the top plane does not drift under a boundary-only warp.

## Wall Step 6 source geometry verification artifact

- Step 6 should emit a source-side geometry verification overlay for the chosen cleanup candidate, not only target-point and final mapped outputs.
- Artifact naming: `*.01b_source_detected_geometry_points.png`.
- The overlay should mark detected source geometry on the conservative/source image itself so Step 7 or later validators can verify point detection before blaming the warp.

## Wall Step 6 mapped-output geometry verification artifact

- For Step 6 geometry verification, source-point overlays are not enough.
- Also rerun the point-finding logic on the mapped result (`04_mapped_full_6_polygon.png`) and emit:
  - `*.04b_mapped_detected_geometry_points.png`
- Store the re-detected mapped points in `geometry.json` as `mapped_detected_geometry` so Step 7 can compare actual mapped geometry against target coordinates.

## Wall Step 6 mesh-warp rule

- `inner_bottom` and `top_plane_apex_opposite` are interior warp constraints, not just debug/support labels.
- A boundary-only six-point warp, or a warp that pins only `top_plane_apex_opposite`, can leave `inner_bottom` in transparent space even when p0..p5 look aligned.
- Step 6 wall rendering should use a piecewise-affine triangle mesh over:
  - boundary points `p0..p5`
  - interior points `inner_bottom` and `top_plane_apex_opposite`
- After mapping, re-detect geometry on the mapped PNG and verify that these interior points fall in solid alpha neighborhoods before treating Step 6 as geometrically sound.

## Wall Step 6 plane-distort experiment

- A promising alternative to mesh warp is a Photoshop-Distort-style per-plane mapping.
- Treat a wall as three iso-rectangular faces:
  - top: `p0, p2, p2_prime, p0_prime`
  - front/left face: `p0, p0_prime, p1_prime, p1`
  - side/right face: `p0_prime, p2_prime, n, p1_prime`
- Derive `p0_prime` and `p1_prime` from the source `p2 -> p2_prime` vector; derive `n` by scanning down from `p2_prime`'s x column to the lowest solid pixel.
- Compute target `p2_prime` by scaling the source `|p2p2_prime|` into game iso space along the target `p2 -> p3` direction, then derive target `p0_prime`, `p1_prime`, and `n`.
- Keep this as an experimental debug output until visually approved:
  - `*.04c_plane_distort_mapped.png`
  - `*.04d_plane_distort_detected_geometry_points.png`

## Wall Step 6 official mapper

- The official wall Step 6 mapper is now the per-plane Photoshop-Distort-style mapper, not the whole-wall mesh warp.
- Official mapped output should be written as `04_mapped_full_6_polygon.png`; `04b_mapped_detected_geometry_points.png` should re-detect geometry on that official mapped result.
- Treat old mesh-warp/mean-value approaches as superseded for wall final rendering because they can preserve boundary points while distorting plane scale/content.

## Wall Step 6 four-real-point inference experiment

- A more robust future wall mapper should infer all planes from four structural real points instead of scanning for top/outer derived points that decorations can corrupt.
- Required vectors:
  - `P0P2` = wall width
  - `P1P1'` = wall thickness / shortest line
  - `P0P1` = wall height
- `P1'` should be found from the bottommost opaque source pixels, tie-breaking closest to `P1`.
- Derived source points:
  - `P0' = P0 + (P1' - P1)`
  - `P2' = P2 + (P1' - P1)`
  - `N = P2' + (P1 - P0)`
- Experimental artifacts:
  - `*.04e_four_point_plane_distort_mapped.png`
  - `*.04f_four_point_detected_geometry_points.png`

## Wall Step 6 four-point target thickness rule

- In the four-real-point inference experiment, do **not** map source `P1'` directly to canonical `P5`; that makes the wall as thick as the whole tile.
- Correct target `P1'` rule:
  - measure source thickness `|P1P1'|`
  - scale by wall height ratio `|target P0P1| / |source P0P1|`
  - place along the canonical game-iso thickness direction hinted by `target P1 -> target P5`
- Then derive target `P0'`, `P2'`, and `N` from the resulting target depth vector.

## Wall Step 6 four-point mapper promotion

- The approved official wall Step 6 mapper is the four-real-point plane-distort mapper.
- Official mapped output name remains `04_mapped_full_6_polygon.png`; do not rely on old experimental `04e` names for new runs.
- Core inference:
  - find real `P0`, `P1`, `P2`, and `P1'`
  - `P0P2` = width, `P1P1'` = thickness, `P0P1` = height
  - derive `P0'`, `P2'`, and `N`; do not scan `P2'`/`N` from outer/top pixels because decorations can corrupt them
- Target `P1'` must preserve source wall thickness by scaling `|P1P1'|` into game iso along the canonical thickness direction; never map it directly to full-tile `P5`.

## Floor Step 6 target geometry rule

- Floor Step 6 should use the user's 7-point game-iso target geometry, not bbox-only scaling.
- Full floor target points:
  - `p0 = [0, 32]`
  - `p1 = [0, 96]`
  - `p2 = [64, 0]`
  - `p3 = [128, 32]`
  - `p4 = [128, 96]`
  - `p5 = [64, 128]`
  - `p6 = [64, 64]`
- Half floor target points:
  - `p0 = [0, 64]`
  - `p1 = [0, 96]`
  - `p2 = [64, 32]`
  - `p3 = [128, 64]`
  - `p4 = [128, 96]`
  - `p5 = [64, 128]`
  - `p6 = [64, 96]`
- Face quads for both full and half:
  - `top = [p0, p2, p3, p6]`
  - `left = [p0, p6, p5, p1]`
  - `right = [p6, p3, p4, p5]`
- Source detection should follow the same spirit as wall Step 6: most outer structural points are directly measurable from alpha, while `p6` is the center / inner junction point that may need to be inferred.

## April 26 — prop color-key internal-hole rule

- For prop color-key GPT Image runs, treat requested chroma-key colors as reserved background colors everywhere in the source image, not only along border-connected regions.
- Reason: brazier-like props may have enclosed openings/rings that show the `#FF00FF` background through the object; border-only flood fill leaves those holes opaque.
- Keep this prop-specific behavior separate from existing floor/wall reference-pair cleanup defaults, because wall/floor workflows may still rely on border-connected cleanup semantics.
- Prop cleanup scoring should also classify enclosed key-colored pixels as background so a correctly transparent internal opening is not penalized as deleted object content.

## April 26 — prop validator corner rule refinement

- For bottom-anchored prop assets, do not fail engineering validation solely because the bottom-left/bottom-right 32px corner regions contain alpha.
- Reason: legitimate prop bases, legs, or bottom contact silhouettes can occupy the lower corners after final `128x256` normalization.
- Keep top-corner alpha checks strict to catch opaque canvas backgrounds, UI/text/watermark, and failed background cleanup.
- Keep bottom-corner alpha values in diagnostics, but use baked-floor heuristics and bbox/anchor checks for bottom-region failures.

## Repo name

- Canonical repo/folder name is now `game_asset_factory`.
- Use `/Users/hunglingki/git_projects/tools/game_asset_factory` in new docs, specs, command examples, and local handoff notes.
- Prior public names were `isometric_tile_factory` and then `isometric_asset_factory`; treat old generated run metadata, historical notes, and OS backup filenames with those names as snapshot provenance unless the run/file must be reused after the rename.

## CLIProxyAPI GPT Image edit route note

- Local CLIProxyAPI GPT Image generation may expose `/v1/images/generations` and `/v1/images/edits` even when `GET /` only advertises text routes; do not trust root endpoint advertisement as the image-route capability source.
- For this factory's direct GPT Image edit path, prefer JSON data-URL edit payloads to `/v1/images/edits` instead of multipart uploads.
  - The 2026-06-02 field-cooking run proved `/v1/images/generations` worked, while multipart `/v1/images/edits` failed with `request Content-Type isn't multipart/form-data`.
  - JSON edit payloads with `images: [{ image_url: data:image/png;base64,... }]` succeeded and preserved the `edit_from` prop workflow.

## IMT field-cooking prop order

- The field-cooking campfire-pot order is now represented by:
  - `examples/prop_asset_workflow/field_cooking_campfire_pot.gpt_image.spec.json`
  - asset family `field_cooking_campfire_pot`
  - assets `imt_field_cooking_pot_unlit` and `imt_field_cooking_pot_active`
  - IMT target folder `img/generated/field_cooking_campfire_pot/`
- Verified real GPT Image color-key run:
  - run root `/private/tmp/imt_prop_asset_runs/imt_field_cooking_campfire_pot_gpt_image_20260602`
  - deliverables include the two state PNGs, atlas PNG/metadata, preview sheet, validation summary, manifest, and `imt_prop_handoff.json`
  - validation status `pass`
- The spec's `target_project_folder` should be copied into `imt_prop_handoff.json` so IMT import tooling can know the intended generated-image folder.

## Local CLIProxyAPI service setup

- On 2026-06-02 the default LaunchAgent was still pointing at the Homebrew `cliproxyapi` binary, which returned `404 page not found` for `/v1/images/generations`.
- Switched `/Users/hunglingki/Library/LaunchAgents/homebrew.mxcl.cliproxyapi.plist` to run:
  - `/Users/hunglingki/.local/bin/cliproxyapi-main -config /opt/homebrew/etc/cliproxyapi.conf`
- A backup was written at:
  - `/Users/hunglingki/Library/LaunchAgents/homebrew.mxcl.cliproxyapi.plist.backup.isometric_asset_factory_20260602`
- Route probe after restart:
  - `POST /v1/images/generations` with empty JSON returns HTTP 400 `prompt is required` instead of 404
  - `POST /v1/images/edits` with empty JSON returns HTTP 400 `prompt is required` instead of 404

## Tile re-skin workflow (tile_reskin_workflow_v1)

- Added 2026-06-13. Module `pipeline/tile_reskin_workflow.py`, CLI
  `prepare-tile-reskin` / `generate-tile-reskin`, doc
  `docs/TILE_RESKIN_WORKFLOW.md`, examples in `examples/tile_reskin_workflow/`.
- Scope: re-texture an EXISTING geometrically-correct tile/autotile set into a
  new material look. It does NOT generate tile geometry — that is deliberately a
  separate future workflow.
- Core rule: never re-shape, only re-skin. Geometry/alpha of each source variant
  is preserved, so seamless tiling + autotile connectivity hold by construction.
- Pipeline: flat-lit material FIELD (generated via `generate_with_provider`, or
  supplied) -> seamless tile (toroidal offset + narrow feather, `seal_band`
  default 0.25, `crop_frac` 0.2) -> per-variant re-skin by classifying the
  ORIGINAL pixel colours into regions and remapping to new materials, optionally
  `modulate_luma` to keep curbs/foam/3D shading.
- Region classifiers: green/blue/sandy/foam/brown/gray/else; region list must end
  with an `else` catch-all; `keep:true` preserves original pixels (water foam).
- Validated family recipes (doodi village standard): road `green→grass(soft),
  else→road(luma)`; sand `green→grass(soft), else→sand`; water `foam→keep,
  sandy→sand(luma), green→grass(soft), brown→grass(luma), else→water`; fence
  `green→grass(soft), else→wood(luma)`.
- Pure Pillow (no numpy). `--provider mock` makes flat-colour fields so the full
  pipeline runs offline (used by manual checks/tests).
- Gotcha: feed PRISTINE source tiles (e.g. target repo git-HEAD), not a prior
  re-skin. For man-made surfaces (road) the straight/rounded boundary is ALREADY
  in the original's own green/gray regions — classify those; do not synthesize a
  grass band or borrow another family's organic jagged mask.
