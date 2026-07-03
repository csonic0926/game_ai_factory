# Wall Reference Pair Workflow

Use this document for:

- `left` / `right` wall runs
- `1u` / `2u` wall references
- wall preprocessing gate
- wall mapping and verification

## Canonical references

- `1u left -> /Users/hunglingki/git_projects/tools/game_asset_factory/examples/golden/sample_factory/images/101_wall_straight_rot90.png`
- `1u right -> /Users/hunglingki/git_projects/tools/game_asset_factory/examples/golden/sample_factory/images/101_wall_straight_rot0.png`
- `2u left -> /Users/hunglingki/git_projects/tools/game_asset_factory/examples/golden/sample_factory/images/102_wall_straight_2u_rot90.png`
- `2u right -> /Users/hunglingki/git_projects/tools/game_asset_factory/examples/golden/sample_factory/images/102_wall_straight_2u_rot0.png`

Canonical handedness:

- `left wall -> rot90`
- `right wall -> rot0`

## Main helper command

```bash
python3 itf.py generate-wall-reference-pair
python3 itf.py generate-wall-reference-pair --height 2
python3 itf.py generate-wall-reference-pair --height 2 --variant left
python3 itf.py generate-wall-reference-pair --variant right
python3 itf.py generate-wall-reference-pair --provider agent_handoff --model gpt-image-2
python3 itf.py generate-wall-reference-pair --provider cliproxyapi --model gpt-image-2
python3 itf.py generate-wall-reference-pair --provider cliproxyapi --model gpt-image-2 --ensure-proxy
python3 itf.py generate-wall-reference-pair --provider gemini_cli --model nano-banana-2
```

Provider notes:

- canonical public contract is:
  - `provider.name = agent_handoff`, `provider.mode = agent_handoff`, `model.name = gpt-image-2` for Codex-agent GPT Image handoff
  - `provider.name = cliproxyapi`, `provider.mode = direct`, `model.name = gpt-image-2` for non-agent/headless fallback
  - `provider.name = gemini_cli`, `model.name = nano-banana-2` or `nano-banana-pro`
- legacy aliases remain accepted for compatibility:
  - `gpt_image_2` / direct `imagegen`
  - `nano_banana`
  - `nano_banana_pro`
  - `imagegen_handoff`
- direct fallback GPT Image runs require local `cliproxyapi`; if
  `curl -s -m4 http://127.0.0.1:8317/v1/models` has no response, start
  `/opt/homebrew/bin/cliproxyapi --config ~/.cli-proxy-api/config.yaml` or pass
  `--ensure-proxy` instead of switching providers.

## Codex agent handoff path

Use this as the normal GPT Image path when the caller is a Codex-capable agent:

```bash
python3 itf.py generate-wall-reference-pair \
  --height 2 \
  --provider agent_handoff \
  --model gpt-image-2 \
  --spec-out /tmp/wall_handoff.spec.json \
  --output-root /tmp/game_asset_factory_handoff_runs
```

The helper stops after preparation and prints `request/imagegen_handoff.json`.
For each variant task:

1. Run the task's `codex_exec_shell_command`, or manually call
   `image_gen.imagegen` with `codex_exec_prompt_text`.
2. Do not hand-draw with code.
3. Persist the actual returned image bytes to the task's `output_path`.
4. Verify with `ls -la <output_path>`.

Use one Codex/imagegen session per variant. Expected paths:

```text
<run_root>/agent_handoff/step_1_raw/left.png
<run_root>/agent_handoff/step_1_raw/right.png
```

Then resume the factory:

```bash
python3 itf.py generate-reference-pair --spec /tmp/wall_handoff.spec.json
```

## Main workflow commands

Prepare:

```bash
python3 itf.py prepare-reference-pair \
  --spec /absolute/path/to/spec.json
```

Generate:

```bash
python3 itf.py generate-reference-pair \
  --spec /absolute/path/to/spec.json
```

Validate:

```bash
python3 itf.py validate-reference-pair \
  --run-root /absolute/path/to/run_root
```

Verify mapped final output:

```bash
python3 itf.py select-reference-pair-variant \
  --run-root /absolute/path/to/run_root \
  --variant left
```

## Wall prompt rule

Wall geometry should come from:

- the supplied canonical wall reference image
- structured wall metadata

Prompt text should focus on:

- style
- material
- decoration
- negative constraints

Do not restate wall geometry in prose unless truly necessary.

## Wall workflow shape

Typical wall run:

1. prepare per-variant wall references
2. generate raw output
3. emit cleanup candidates
4. run preprocessing gate and choose the least-destructive valid cleanup
5. map the chosen wall into canonical game-iso placement
6. verify the mapped result

## Preprocessing gate

Before wall mapping, validation must confirm that at least one cleanup candidate leaves a usable wall silhouette.

A usable candidate must:

- have an opaque silhouette bbox
- not fill the whole canvas as foreground
- not fail exterior background-residue checks

If no cleanup candidate is usable, stop at the gate and debug cleanup first.

## Run triage

Start with:

- `artifact_status.json`

Then inspect:

1. `step_4_gate/`
2. `step_6_mapping/`
3. `step_7_selection/`
4. `deliverables/`

If Step 4 fails, debug cleanup first.
