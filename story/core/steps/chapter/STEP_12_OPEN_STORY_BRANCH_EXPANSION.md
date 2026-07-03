# STEP 12 — Open Story Branch Expansion

## Purpose

Turn one accepted trunk chapter into concrete branch directions that can support later branch implementation.

## Read inputs from

Read these saved artifacts:

- `<STORY_ROOT>/state/outcomes/<stage>/<artifact_stem>_handoff.md`
- the accepted trunk chapter source, graph, and runtime artifacts for the branch point

## Save output to

Write one branch expansion design file to:

- `<STORY_ROOT>/state/chapter_sources/<artifact_stem>_BRANCH_EXPANSION.md`

## Skill use

- No skill required for this step.

## Task

Design branch directions from one concrete branch point in the accepted trunk.

Write branch directions that:

- start from concrete player actions the player can take now
- stay tied to the current scene's actual people, places, objects, routines, timing, and pressure
- produce distinct later consequences instead of alternate wording for the same outcome
- stay traceable back to the exact trunk branch point
- define both writing-side state change and runtime-facing projection

## Branch design standard

For each branch option, make these points explicit:

1. what the player physically does
2. who sees, helps, blocks, or remembers the action
3. what future state changes because of it
4. what later scene becomes possible, harder, costlier, or more exposed

Build the branch from a forcing function that exists on-screen at the branch point.

Ground each option in concrete world supports such as:

- a specific location or route
- naturally present people
- ordinary objects or documents
- routine or institutional process
- time-of-day pressure

## State consequence standard

For each branch option, define:

- `axes_delta`: at least 2 writing-side axis changes, or 1 strong axis change plus 1 strong runtime projection
- `runtime_projection`: what the player will later feel in runtime
- `delayed_hook`: 1 hook that can be read later by tags, routing, access, pressure, memory, or cost

Runtime projection can include:

- tag added or removed
- gold or health change
- route access or route pressure
- who remembers the player
- whether a later path becomes cleaner, dirtier, safer, or more exposed

## Runtime state projection standard

When a branch writes runtime state, use the project's runtime-state tools:

- numeric stats
- event tags
- routed success / fail-forward outcomes

Typical runtime state shapes:

- `choice_N_add_tags`
- `choice_N_remove_tags`
- `choice_N_effect_stat`
- `choice_N_effect_amount`
- `choice_N_event_id`
- `choice_N_fail_event_id`

If a branch causes a battle later, keep `battle_id` consistent with the actual battle facts that branch implies.

## Required output blocks

Always output these blocks:

- `CANDIDATE BEAT CHECK`
- `BRANCH TABLE`
- `DISTINCTNESS PROOF`
- `FOLLOW-UP SCENE SEEDS`

## Block definitions

### `CANDIDATE BEAT CHECK`

State:

- `candidate_branch_beat`
- `why_this_beat_can_split`

The chosen beat should be a real on-screen moment where the player must choose now.

### `BRANCH TABLE`

List 2-4 branch options.

For each option, include:

- `player_action`
- `immediate_beat`
- `grounding`
- `axes_delta`
- `runtime_projection`
- `delayed_hook`

### `DISTINCTNESS PROOF`

For each option, state why it is not replaceable by the other options.

The proof should show that the option changes future leverage, access, exposure, cost, or memory in a distinct way.

### `FOLLOW-UP SCENE SEEDS`

For each option, include:

- 1 immediate next-scene concept
- 1 later pay-off concept
