# STEP 9.5 — QA Acceptance

## Purpose

Check the saved story QA and prose QA reports and record a pass or fail result for the chapter.

## Read inputs from

- `<STORY_ROOT>/qa/reports/<stage>_story_r<round>_<yyyymmdd>.md`
- `<STORY_ROOT>/qa/reports/<stage>_prose_r<round>_<yyyymmdd>.md`

## Save output to

- `<STORY_ROOT>/qa/reports/<artifact_stem>_qa_acceptance_<yyyymmdd>.md`

## Skill use

- No skill required for this step.

## Task

Review both QA reports and write one short acceptance note that says `STEP 9.5 PASS` or `STEP 9.5 FAIL`.

## Acceptance criteria

Pass only when all of these are true:

- story QA has been run
- prose QA has been run
- both reports are saved
- neither checklist has a blocker failure
- both results are `pass`

## Required stop condition

- write a short acceptance note that says `STEP 9.5 PASS` when the reports pass
- write `STEP 9.5 FAIL` when either report fails
