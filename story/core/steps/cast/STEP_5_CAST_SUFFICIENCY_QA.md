# STEP 5 — Cast Sufficiency QA

## Purpose

Check whether the saved cast baseline is sufficient for the current scope and ready for the next chapter-creation phase.

## Read inputs from

- `<STORY_ROOT>/state/cast_management/CAST_SCOPE.md`
- `<STORY_ROOT>/state/cast_management/CAST_AUDIT.md`
- `<STORY_ROOT>/state/cast_management/CAST_MISSING_AND_OVERLAP.md`
- `<STORY_ROOT>/state/cast_management/CAST_REBALANCE.md`
- `<STORY_ROOT>/state/cast_management/CAST_ACTION_REQUESTS.md`
- packaged characters under `<STORY_ROOT>/state/characters/`, when they exist

## Save output to

- `<STORY_ROOT>/state/cast_management/CAST_QA.md`

## Skill use

- No skill required for this step.

## Task

Review the cast-management artifacts and decide whether the current cast can support the current scope without blocking gaps.

Judge the cast by these concrete checks:

- the cast covers the required story functions named in `CAST_SCOPE.md`
- the cast has enough distinct role coverage for the current scope
- the cast has enough distinct pressure coverage for the current scope
- the cast has enough relation coverage for the current scope
- the current cast does not leave a blocking gap in key character types
- the next required cast action is clear in `CAST_ACTION_REQUESTS.md`

## Required output blocks

### `REVIEW SUMMARY`

State one short summary of the QA result and whether the cast is ready or not ready.

### `PASS OR FAIL`

Write `PASS` if the cast is sufficient for the current scope, otherwise write `FAIL`.

### `ISSUES`

List each concrete blocker, gap, or insufficiency.

For each issue, state which cast layer is still lacking.

### `FIXES`

List the specific cast-management change needed to resolve each issue.
