# STEP 4.5 — Cast Action Request Acceptance

## Purpose

Review the saved cast action requests and decide whether they are ready to drive the next cast-management step.

## Read inputs from

- `<STORY_ROOT>/state/cast_management/CAST_ACTION_REQUESTS.md`
- `<STORY_ROOT>/state/cast_management/CAST_REBALANCE.md`
- `<STORY_ROOT>/state/cast_management/CAST_MISSING_AND_OVERLAP.md`

## Save output to

- `<STORY_ROOT>/state/cast_management/CAST_ACTION_REQUESTS_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check whether the saved cast action requests name a clear next action, a clear target, and a clear reason for that action.

## Acceptance criteria

### Request types

This step passes when:

- each request uses one explicit type: `CREATE_CHARACTER_REQUEST`, `REVISE_CHARACTER_REQUEST`, `RELATION_REBALANCE_REQUEST`, or `CAST_PASS`
- each request can be read without guessing which workflow move it belongs to

### Request clarity

This step passes when:

- each request names the target role or target character
- each request states why the request exists
- each request states which cast gap, overlap, or imbalance it resolves

### Workflow routing

This step passes when:

- the request set points to one clear next move for the cast workflow
- the next move is readable as create, revise, rebalance, or `CAST_PASS`
- no request leaves the next workflow step ambiguous

## Required stop condition

- write a short note that says `STEP 4.5 PASS` or `STEP 4.5 FAIL`
- on `FAIL`, name the specific request or missing detail that blocks routing
