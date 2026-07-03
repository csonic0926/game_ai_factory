# STEP 1.5 — Cast Audit Acceptance

## Purpose

Review the saved cast audit and decide whether it is ready for missing-role and rebalance work.

## Read inputs from

- `<STORY_ROOT>/state/cast_management/CAST_AUDIT.md`
- `<STORY_ROOT>/state/cast_management/CAST_SCOPE.md`
- packaged characters under `<STORY_ROOT>/state/characters/`, when they exist

## Save output to

- `<STORY_ROOT>/state/cast_management/CAST_AUDIT_REVIEW.md`

## Skill use

- No skill required for this step.

## Task

Check the saved cast audit against the scope and the packaged character set, then decide whether the audit is complete enough to use as the next cast-management input.

## Acceptance criteria

### Current cast

This step passes when:

- the audit names the current cast members that matter for this cast pass
- the audit gives a clear, readable snapshot of who currently exists

### Role coverage

This step passes when:

- the audit names the roles or story functions each current character covers
- the audit makes it easy to compare coverage against the scope

### Gaps

This step passes when:

- the audit states the important missing functions, relations, or pressures
- the gap notes are specific enough to feed the next cast action request

### Overlaps

This step passes when:

- the audit identifies the main overlap points
- the overlap notes explain which characters are too similar in function, pressure, or relation shape

## Required stop condition

- write one short result note that says `STEP 1.5 PASS` or `STEP 1.5 FAIL`
- on `FAIL`, name the single blocker that prevents the audit from being usable
