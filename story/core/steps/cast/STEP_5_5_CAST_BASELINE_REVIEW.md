# STEP 5.5 — Cast Baseline Acceptance

## Purpose

Review the saved cast baseline and decide whether it is ready for the next chapter-creation phase.

## Read inputs from

- `<STORY_ROOT>/state/cast_management/CAST_SCOPE.md`
- `<STORY_ROOT>/state/cast_management/CAST_AUDIT.md`
- `<STORY_ROOT>/state/cast_management/CAST_MISSING_AND_OVERLAP.md`
- `<STORY_ROOT>/state/cast_management/CAST_REBALANCE.md`
- `<STORY_ROOT>/state/cast_management/CAST_ACTION_REQUESTS.md`
- `<STORY_ROOT>/state/cast_management/CAST_QA.md`
- `<STORY_ROOT>/state/cast_management/CAST_CHARACTER_LIST.md`
- packaged characters under `<STORY_ROOT>/state/characters/`, when they exist

## Save output to

- `<STORY_ROOT>/state/cast_management/CAST_BASELINE_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check whether the saved cast baseline is complete, internally consistent, and ready to hand off to later workflows.

## Acceptance criteria

### Cast baseline coverage

This step passes when:

- `CAST_SCOPE.md`, `CAST_AUDIT.md`, `CAST_MISSING_AND_OVERLAP.md`, `CAST_REBALANCE.md`, `CAST_ACTION_REQUESTS.md`, `CAST_QA.md`, and `CAST_CHARACTER_LIST.md` all exist
- each artifact can be read as part of the same cast pass, with no missing required baseline file
- the baseline summary does not depend on guessing which cast step came last

### QA result

This step passes when:

- `CAST_QA.md` records a `PASS`
- the QA record names no unresolved blocker for the current cast scope
- the QA record does not leave the next cast action ambiguous

### Workflow readiness

This step passes when:

- no blocking character creation request remains for the current scope
- the current cast is sufficient for the next chapter-creation phase
- the review can point to a clear next workflow state without extra interpretation

## Required stop condition

- write a short note that says `STEP 5.5 PASS` or `STEP 5.5 FAIL`
- on `FAIL`, state the blocker clearly
