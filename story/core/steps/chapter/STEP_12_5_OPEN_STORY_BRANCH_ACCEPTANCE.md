# STEP 12.5 — Open Story Branch Acceptance

## Purpose

Review the saved branch expansion and decide whether it passes.

## Read inputs from

- `<STORY_ROOT>/state/chapter_sources/<artifact_stem>_BRANCH_EXPANSION.md`

## Save output to

- `<STORY_ROOT>/state/chapter_sources/<artifact_stem>_BRANCH_ACCEPTANCE.md`

## Skill use

- No skill required for this step.

## Task

Check whether the saved branch expansion is complete, concrete, and consistent with the STEP 11 branch-expansion contract.

## Acceptance criteria

### Candidate beat

This step passes when:

- the branch expansion identifies one concrete branch beat
- the chosen beat is a real on-screen moment where the player must choose now
- the beat can plausibly split into multiple actions without leaving the trunk scene logic

### Branch table

This step passes when:

- the branch table gives 2-4 branch options
- each option is a concrete player action
- each option includes immediate beat, grounding, axes delta, runtime projection, and delayed hook
- each option stays traceable to the same branch point

### Grounding

This step passes when:

- each option is grounded in concrete world supports
- the grounding names real scene supports such as location, people, objects, routines, process, or time-of-day pressure
- the branch reads like something that can happen only at this scene and branch point

### State consequences

This step passes when:

- each option changes writing-side state in a meaningful way
- each option defines a runtime-facing projection the player can later feel
- each option adds one delayed hook that can be read later by tags, routing, access, pressure, memory, or cost
- runtime-state projections use valid project shapes such as stats, event tags, or routed outcomes

### Distinctness

This step passes when:

- each option changes future leverage, access, exposure, cost, memory, or pressure in a distinct way
- the options are not replaceable by wording-only variation
- the branch produces real divergence from the trunk

### Follow-up scene seeds

This step passes when:

- each option includes one immediate next-scene concept
- each option includes one later pay-off concept
- the follow-up seeds match the branch option's stated grounding and state consequences

## Required stop condition

- write a short note that says `STEP 12.5 PASS` or `STEP 12.5 FAIL`
- on `FAIL`, state the blocker clearly
