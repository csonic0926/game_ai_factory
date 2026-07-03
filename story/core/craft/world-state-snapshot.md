# World State Snapshot

*Maintains open-story world state: reads/writes the writing-only JSON under `<STORY_ROOT>/state/` (arcs, factions, character memory, snapshots) and produces consistent snapshot updates + deltas.*

Use this doc when you need to:
- Turn vague story intent into a **state snapshot** that can drive branching
- Update the snapshot after a choice (state deltas + new hooks)
- Keep arc axes, faction pressure, and character memory consistent

## Data locations (repo)

- Arc + axes: `<STORY_ROOT>/state/arcs/*.json`
- Factions: `<STORY_ROOT>/state/factions/*.json`
- Character memory: `<STORY_ROOT>/state/characters/*.memory.json`
- Snapshots: `<STORY_ROOT>/state/snapshots/*.json`

*Note: field suffixes `_zh` in this schema denote text authored in `<PRIMARY_LOCALE>` (the `_zh` naming is an example from a zh-TW primary-locale project); substitute your project's primary-locale suffix.*

## Hard rules

1) Snapshot axes are 0–5 integers.
2) Every choice must change **at least 2 axes**.
3) Every choice must add **exactly 1 delayed hook** (a future payoff question/problem).
4) Any non-trivial inference must be written into `assumptions_zh`.

## Output format (always)

### 1) Snapshot (current)
- Echo the current `axes` line in one sentence.
- List present factions/characters.

### 2) Proposed choice outcomes (2–4 options)
For each option:
- `axes_delta`: a map of axis -> +1/-1/0 (only changed axes)
- `new_hook_zh`: one delayed hook
- `evidence_anchors_zh`: 1–2 on-screen anchors that justify the delta
- `memory_deltas`: per involved character (know/assume/misread one-liners)

### 3) Updated snapshot (pick one)
If the user picks an option, output the updated snapshot JSON patch:
- new `axes` values
- appended `open_hooks_zh`
- appended `assumptions_zh` (if any)

## Safety checks

- If an option changes only 1 axis: reject and revise.
- If a hook is immediate (resolves in the same scene): reject and rewrite.
- If a delta contradicts a faction constraint: revise the option.
