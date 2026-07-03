# STEP 4.5 — Objects and Movement Review

## Purpose

Review the saved logistics baseline and decide whether it is concrete enough to reuse.

## Read inputs from

- `<STORY_ROOT>/state/world_baselines/WORLD_LOGISTICS.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_GEOGRAPHY.md`
- `<STORY_ROOT>/state/world_baselines/WORLD_INSTITUTIONS.md`

## Save output to

- `<STORY_ROOT>/state/world_baselines/WORLD_LOGISTICS_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check the saved logistics baseline against the criteria below and write one review result block.

## Acceptance criteria

### Common objects

This step passes when ordinary objects, goods, tools, or documents are named concretely, their normal locations and uses are clear, and no later step would need to invent a new object layer to describe them.

### Service flows

This step passes when each common service names its provider, user, and delivery or request path, and the payment or routing logic can be imagined in ordinary use.

### Movement logic

This step passes when the baseline shows how people, goods, messages, or authority move, what normally limits that movement, and what route or transfer pattern applies.

### Transfer points

This step passes when each transfer point is specific, the handoff there is named, and the point can be used as a delay site, pressure site, or bottleneck without extra invention.

## Required stop condition

### `REVIEW RESULT`

- `STEP 4.5 PASS` or `STEP 4.5 FAIL`
- If `FAIL`, add one short `BLOCKER:` line that names the concrete missing piece
