# Cross-repo factory request — CORRECTION

## Request metadata

- Status: completed
- Date: 2026-06-17
- Source repo: simplest_infinity_magic_tower (Infinity Magic Tower / IMT)
- Source repo path: /Users/hunglingki/git_projects/Godot/simplest_infinity_magic_tower
- Corrects: `2026-06-17_imt_gpt_image_cliproxy_availability.md` (already actioned)
- Factory target area: GPT Image provider priority + docs + orchestrator skill guidance
- Priority: normal

## Why this correction

My previous note set the **wrong priority**, and the factory fix that followed
optimized the wrong path. That note treated "GPT Image is unavailable" as a
cli-proxy problem and asked for cli-proxy preflight + `--ensure-proxy`
auto-start. Those changes are fine as a *fallback*, but they made the
**indirect, server-requiring** path look like the answer.

The user clarifies the intended priority: on this setup the first-class GPT
Image route is **direct Codex GPT image generation** — i.e. the orchestrating
Codex agent generates the image itself with its native image tool. No local
proxy server should need to be started for the normal path.

## The correct priority

1. **Primary: `agent_handoff` (direct Codex imagegen).** The factory already
   models this (`reference_pair_workflow.py` ~1085–1208): agent_handoff mode does
   not call a provider; it prepares the imagegen handoff task + output paths, and
   an external Codex agent writes the Step 1 raw PNGs, then the run continues.
   The `codex` CLI is installed (`/opt/homebrew/bin/codex`, native image
   support). This is the most direct path: the agent that's already running the
   factory produces the image — no extra server, no extra process to babysit.
2. **Fallback: `cliproxyapi` (direct HTTP to local proxy).** Keep this for
   non-agent / headless automation callers that can't do an agent handoff. The
   preflight + `--ensure-proxy` work from the prior fix belongs here — as the
   fallback's ergonomics, not the headline.

## Factory-side change requested

1. **Flip the recommended default in docs + orchestrator skill.** Provider
   selection guidance currently leads with "fresh GPT Image gen → cliproxyapi +
   gpt-image-2". For a Codex-agent caller (the normal case here) it should lead
   with **agent_handoff (imagegen)** and present cliproxyapi as the fallback for
   non-agent callers. Update: `README.md`, `docs/AI_CALLER_LANDING.md`,
   `docs/SPEC.md`, the wall/prop/reference-pair workflow docs, and
   `docs/REPO_MEMORY.md`.
2. **Make the handoff path frictionless to choose.** Ensure there's a clear,
   documented one-liner for "generate via agent_handoff": which command prepares
   the handoff task, exactly which paths the agent must write, and which command
   resumes. If a convenience flag (e.g. `--provider agent_handoff` end-to-end
   with a clear "now produce these N images at these paths" manifest) isn't
   already obvious, surface it.
3. **Do not regress the cli-proxy fallback.** Leave the preflight/auto-start in
   place; just reframe it as fallback.

## Not changing / out of scope

- The cli-proxy preflight + `--ensure-proxy` already shipped — keep it.
- The Gemini `--key=company` smell — still a separate follow-up.

## Verified mechanism (2026-06-17) — confirmed working

Direct Codex GPT image gen works headlessly via the `codex` CLI's built-in
`image_gen.imagegen` tool, using the already-stored Codex OAuth auth
(`~/.codex/auth.json`; tokens id/access/refresh + account_id). No cli-proxy, no
platform API key. Even a non-Codex caller (e.g. a Claude session) can drive it by
shelling out to `codex exec`.

Working invocation (one image per session):

```bash
cd /tmp && codex exec --skip-git-repo-check --sandbox workspace-write \
  "Call the image_gen.imagegen model tool to generate <PROMPT>. Then take the \
actual image bytes the tool returns and WRITE them to disk at <ABS_OUT.png> \
(decode base64 / copy the tool's output file as needed). After writing, run \
'ls -la <ABS_OUT.png>' and report the absolute path and byte size. Do NOT \
hand-draw with code. If you cannot persist, say exactly CANNOT_PERSIST." < /dev/null
```

Gotchas learned the hard way (encode these into the agent_handoff contract/docs):

- **Must say "use image_gen.imagegen, do NOT hand-draw with code."** Without it,
  Codex satisfies "make an image" by writing SVG/PIL code → a flat ~5 KB vector,
  not a real gpt-image render (~1–1.5 MB).
- **Must explicitly tell it to persist the returned bytes to a path and verify
  with `ls`.** The tool returns the image into the conversation; Codex does not
  auto-write it to an arbitrary path. "decode base64 / copy the tool's output
  file" + a verify step is what made it land on disk.
- **One image per `codex exec` session.** A single session asked for 3 images
  returned `CANNOT_PERSIST` for all three; one-image-per-session each succeeded.
- `--skip-git-repo-check` (or run inside a trusted git dir) and `< /dev/null`
  (so it doesn't block reading stdin) are both required for headless runs.
- `--sandbox workspace-write` so it can write the output file.

So the factory's `agent_handoff` step should hand the Codex agent: (1) the prompt,
(2) the exact output path, (3) an instruction to use `image_gen.imagegen` + persist
bytes + verify, and process ONE variant per handoff call.

## Note to the IMT side (self-reminder)

For IMT, generate masters/tiles via the verified `codex exec` + `image_gen.imagegen`
path above (one image per session). cliproxyapi stays a fallback only.


## Factory response — 2026-06-17

Status: completed.

Changed:

- Reframed GPT Image guidance so Codex-agent callers use `agent_handoff` / native `image_gen.imagegen` as the primary path.
- Kept `cliproxyapi + gpt-image-2` preflight and `--ensure-proxy` as the non-agent/headless fallback path.
- Made `request/imagegen_handoff.json` more explicit and executable:
  - each task now includes `codex_exec_prompt_text`
  - each task now includes `codex_exec_shell_command`
  - the contract says one variant per session, use `image_gen.imagegen`, do not hand-draw with code, persist actual returned bytes to `output_path`, and verify with `ls -la`.
- Updated docs to show the handoff one-liner, raw output paths, and resume command.
- Updated the IMT tile orchestrator skill guidance to prefer `agent_handoff` for fresh floor/wall GPT Image generation from Codex-capable agents.

Changed files:

- `pipeline/reference_pair_workflow.py`
- `tests/test_reference_pair_workflow_provider.py`
- `README.md`
- `docs/AI_CALLER_LANDING.md`
- `docs/SPEC.md`
- `docs/REFERENCE_PAIR_WORKFLOW.md`
- `docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md`
- `docs/WALL_REFERENCE_PAIR_WORKFLOW.md`
- `docs/PROP_ASSET_WORKFLOW.md`
- `docs/TILE_RESKIN_WORKFLOW.md`
- `docs/REPO_MEMORY.md`
- `docs/CURRENT_JOB.md`
- `/Users/hunglingki/.claude/skills/imt-generate-tiles-orchestrator/SKILL.md`
- `requirement_from_other_repo/2026-06-17_imt_gpt_image_direct_codex_priority_CORRECTION.md`

Validation:

```bash
python3 -m unittest tests.test_reference_pair_workflow_provider -v
python3 -m unittest tests.test_prop_asset_workflow tests.test_reference_pair_workflow_provider tests.test_variant_selector_floor_mapping tests.test_variant_selector_wall_validation -v
python3 -m py_compile pipeline/reference_pair_workflow.py itf.py pipeline/prop_asset_workflow.py pipeline/tile_reskin_workflow.py
```

Notes / not changed:

- Did not run real image generation or `codex exec`; this patch updates the factory contract/docs and tests the generated handoff packet shape.
- Prop and tile-reskin workflows still do not implement `agent_handoff`; their docs now call that out instead of presenting `cliproxyapi` as the global GPT Image default.
- The Gemini `--key=company` smell remains a separate follow-up.
