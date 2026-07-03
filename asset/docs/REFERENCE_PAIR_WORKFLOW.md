# Reference Pair Workflow

This file is the **router**.

Use:

- `/Users/hunglingki/git_projects/tools/game_ai_factory/asset/docs/FLOOR_REFERENCE_PAIR_WORKFLOW.md` for `full` / `half` floor runs
- `/Users/hunglingki/git_projects/tools/game_ai_factory/asset/docs/WALL_REFERENCE_PAIR_WORKFLOW.md` for `left` / `right` wall runs

## Shared commands

```bash
python3 itf.py prepare-reference-pair --spec /absolute/path/to/spec.json
python3 itf.py generate-reference-pair --spec /absolute/path/to/spec.json
python3 itf.py validate-reference-pair --run-root /absolute/path/to/run_root
python3 itf.py select-reference-pair-variant --run-root /absolute/path/to/run_root --variant full
```

Wall helper:

```bash
python3 itf.py generate-wall-reference-pair
python3 itf.py generate-wall-reference-pair --provider agent_handoff --model gpt-image-2
```

## GPT Image provider priority

For a Codex-agent caller, prefer `agent_handoff` for GPT Image:

```json
"provider": { "name": "agent_handoff", "mode": "agent_handoff", "agent_tool": "imagegen" },
"model": { "name": "gpt-image-2" }
```

Preparation writes `request/imagegen_handoff.json`. Each task in that packet
declares:

- `codex_prompt_text`
- `codex_exec_prompt_text`
- `codex_exec_shell_command`
- `edit_target_image`
- `output_path`

Run one task per Codex/imagegen session. The task must call
`image_gen.imagegen`, must not hand-draw with code, must persist the actual
returned bytes to `output_path`, and must verify with `ls -la`.

The expected raw handoff path is:

```text
<run_root>/agent_handoff/step_1_raw/<variant>.png
```

After all requested handoff PNGs exist, resume with:

```bash
python3 itf.py generate-reference-pair --spec /absolute/path/to/spec.json
```

Use `cliproxyapi + gpt-image-2` as the fallback for non-agent/headless callers
that cannot do the Codex handoff.

## Shared run triage

Start with:

- `artifact_status.json`

Then inspect the relevant step folder:

- `step_1_raw/`
- `step_3_cleanup_pool/`
- `step_4_gate/` when that step exists
- `step_6_mapping/` when that step exists
- `step_7_selection/`
- `deliverables/`
