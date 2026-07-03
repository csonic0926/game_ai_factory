# STEP 10 — Sync Twin + Frame

## Purpose

Refresh the twin and story frame after runtime landing so they serve the latest chapter state.

## Read inputs from

Read these inputs before syncing:

- `<STORY_ROOT>/qa/reports/<stage>_story_r<round>_<yyyymmdd>.md`
- `<STORY_ROOT>/qa/reports/<stage>_prose_r<round>_<yyyymmdd>.md`
- the touched CSV / locale files from STEP 7
- `<STORY_ROOT>/qa/reports/<artifact_stem>_qa_acceptance_<yyyymmdd>.md`

## Save output to

Write one sync log to:

- `<STORY_ROOT>/state/frames/<artifact_stem>_sync_log_<yyyymmdd>.md`

## Skill use

- No skill required for this step.

## Task

Run the sync commands, refresh the frame targets, and record what changed in the sync log.

## Required output format or exact commands

Use this exact command sequence after runtime CSV or locale changes:

```bash
make twin-check
python3 scripts/build_story_logic_frame.py --trace <STORY_ROOT>/state/branch_traces/example_branch_trace.json
python3 scripts/story_query_with_frame.py keyword --trace <STORY_ROOT>/state/branch_traces/example_branch_trace.json --query "黃家 巡夜" --limit 5
python3 scripts/story_query_with_frame.py belief --trace <STORY_ROOT>/state/branch_traces/example_branch_trace.json --character-id ch_player --query "中立" --limit 5
```

Record these items in the sync log:

- the exact trace file used
- the commands run
- the refreshed frame targets

## Block definitions

### `SYNC LOG`

State the trace, commands, and refreshed targets in a short, readable log.

### `EXPECTED RESULT`

The twin and story frame should align with the latest chapter landing and stop serving replaced runtime rows.
