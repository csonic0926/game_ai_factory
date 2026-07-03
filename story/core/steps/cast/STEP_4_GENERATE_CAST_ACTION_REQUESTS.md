# STEP 4 — Generate Cast Action Requests

## Purpose

Turn the saved cast findings into explicit workflow requests and a clear next cast action.

## Read inputs from

- `<STORY_ROOT>/state/cast_management/CAST_SCOPE.md`
- `<STORY_ROOT>/state/cast_management/CAST_AUDIT.md`
- `<STORY_ROOT>/state/cast_management/CAST_MISSING_AND_OVERLAP.md`
- `<STORY_ROOT>/state/cast_management/CAST_REBALANCE.md`

## Save output to

- `<STORY_ROOT>/state/cast_management/CAST_ACTION_REQUESTS.md`
- `<STORY_ROOT>/state/cast_management/CHARACTER_CREATION_PROGRESS.md`

## Skill use

- No skill required for this step.

## Task

Turn the current cast findings into a small set of explicit cast-management requests that a fresh workflow step can act on immediately.

Use only these request types:

- `CREATE_CHARACTER_REQUEST`
- `REVISE_CHARACTER_REQUEST`
- `RELATION_REBALANCE_REQUEST`
- `CAST_PASS`

Write each request so it names one concrete next action and the exact cast need it serves.

For each request, include:

- the target role or target character
- why the request is needed
- what cast problem it solves
- why this request belongs in the current priority order

## Required output blocks

### `REQUEST LIST`

List the requests in priority order.

For each request, state:

- the request type
- the target role or target character
- the cast need or deficiency that drives the request
- the problem the request resolves
- the reason it comes before or after the other requests

### `NEXT ACTION`

State the single next cast move that should happen first.

If the cast is already sufficient, write `CAST_PASS`.

### `PROGRESS NOTE`

Update `CHARACTER_CREATION_PROGRESS.md` with the current cast-request status in a short, readable form.

## Required output checks

The request set should:

- make the next cast action clear
- translate cast findings into actionable workflow work
- allow the cast to move into character creation, character revision, relation rebalance, or `CAST_PASS`
