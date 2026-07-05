# Branch Implementation Overlay

Purpose:

- define the extra branch-specific requirements that apply when a reused trunk step is used for branch implementation
- keep branch work traceable back to the accepted trunk and the accepted branch point

## Read inputs from

Read this overlay together with the trunk step file being reused for the current branch task.

Use the matching branch artifacts named by that step, such as the accepted trunk source, branch expansion, or branch handoff files, when the step needs them.

## Task

Apply the branch requirements below whenever a trunk step is reused for a branch.

### Reused `STEP 1` / `STEP 1.5`

Record:

- the source trunk
- the accepted branch point
- the branch direction being implemented
- the inherited knowledge, memory, and pressure from the accepted trunk state
- the first branch-specific divergence from trunk expectation

The branch preflight should state how this branch inherits from the trunk and how it departs from it.

### Reused `STEP 2` / `STEP 2.5`

Select a line that is a real divergence from the accepted trunk branch point.

State why this line should be implemented as a branch instead of falling back into trunk behavior.

Keep the chosen branch line distinct from the trunk line in later-state consequence.

### Reused `STEP 3` / `STEP 3.5`

Keep the branch inside the trunk chapter's declared time frame unless the branch explicitly crosses that boundary.

State how the branch bends away from the trunk path.

Make the branch spine meaningfully different from a cosmetic rewrite of the trunk spine.

### Reused `STEP 4` / `STEP 4.5`

Record the following in the branch source:

- source trunk id
- source branch point id
- branch id or branch direction id
- inherited assumptions
- branch-specific divergence note

Keep the branch source traceable back to the accepted trunk and the accepted branch design.

### Reused `STEP 11` / `STEP 11.5`

Treat the result as branch implementation completion.

State outcomes that reflect branch-specific carry-over.

Confirm that the branch now fits cleanly into later chapter transition work.

## Required output wording

When a reused trunk step reaches completion, use branch-completion wording that states:

- one accepted branch implementation is now integrated

Use this wording instead of trunk-completion wording that describes the stable chapter trunk ending.
