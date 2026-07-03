# STEP 0.5 — Cast Scope Acceptance

## Purpose

Review the saved cast scope and decide whether it is ready for cast audit work.

## Read inputs from

- `<STORY_ROOT>/state/cast_management/CAST_SCOPE.md`
- packaged characters under `<STORY_ROOT>/state/characters/`, when they exist
- cast-management artifacts under `<STORY_ROOT>/state/cast_management/`, when they exist

## Save output to

- `<STORY_ROOT>/state/cast_management/CAST_SCOPE_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Read `CAST_SCOPE.md` and judge the saved scope on four concrete points:

- the cast purpose is explicit
- the scale target is concrete
- the scope level is named
- the required story functions are usable for later audit work

## Acceptance criteria

### Cast purpose

This step passes when:

- the cast purpose is explicit
- the stated purpose names a usable cast-management target

### Scale target

This step passes when:

- the current scale target gives a practical ensemble size or scale
- the target can guide later audit and sufficiency checks without guesswork

### Scope level

This step passes when:

- the scope level is stated as chapter, arc, or baseline world-stage support
- later steps can use that level directly without inferring it

### Required story functions

This step passes when:

- the needed story functions are listed clearly
- the functions are specific enough to support missing-role and overlap checks

## Required stop condition

- write one short note that says `STEP 0.5 PASS` or `STEP 0.5 FAIL`
- on `FAIL`, name the specific blocker in one line
