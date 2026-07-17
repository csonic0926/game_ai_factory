# AI caller landing — gameplay_factory

Use this factory when the missing question is not “what happens next?” but
“how does the player personally experience it?”

Phase 0 is a manual document workflow. Do not create a CLI, step machine, or
skill until real project traces have tested the contracts across at least two
or three beats.

The manual invocation must identify the operation and either name the game
repo or be launched from it:

```text
factory: <FACTORY_REPO>/gameplay
operation: onboard | author_trace | segment_trace | reception_review
game_repo: <explicit path, or CURRENT_GIT_ROOT>
project_id: <required only for registry.local.md lookup>
```

## Resolve the target game repo

Resolve `<GAME_REPO>` before reading inputs or creating outputs:

1. use the explicit game-repo path in the invocation, when supplied;
2. otherwise use the current working directory's Git root;
3. only for an explicit `project_id`, optionally consult the ignored
   `../adapters/registry.local.md` machine-local phonebook.

Then set `<GAMEPLAY_ROOT>` to the fixed game-owned location
`<GAME_REPO>/design/gameplay`. Reject the call if that resolution falls inside
the factory repo. Never scan sibling directories or rely on a committed
absolute developer path.

## Onboard a game repo

For an explicit onboarding request, create only these game-owned paths:

```text
<GAME_REPO>/design/gameplay/adapter/
<GAME_REPO>/design/gameplay/state/
```

Seed the two adapter answer sheets from `../adapters/_template/` and the blank
grammar state from `../templates/GAMEPLAY_GRAMMAR_STATE.md`. Never overwrite
an existing answer or state file. Fill and version them in the game repo.
Create `traces/`, `beat_packets/`, and `qa/` only when their first real
artifact is produced. No onboarding output may land under this factory.

## Preconditions

Resolve and read the project adapter per
[`PROJECT_ADAPTER_CONTRACT.md`](PROJECT_ADAPTER_CONTRACT.md). Continue only
when all of these are available:

- story anchors expressed as required state deltas plus causal constraints;
- current runtime/world/player-knowledge state;
- a filled `PROJECT_GAMEPLAY_PROFILE.md`;
- a filled `PRODUCTION_ADAPTER.md`;
- current `GAMEPLAY_GRAMMAR_STATE.md`, or a newly initialized blank state for
  the project's first trace.

If no adapter resolves, or an answer is missing, report
`BLOCKED_BY_ADAPTER`. Do not infer verbs, camera behavior, HUD behavior,
budget, or runtime schemas from a story document. Initialization is allowed
only when onboarding was explicitly requested; an ordinary production call
must not silently replace or regenerate an incomplete adapter.

## Manual Phase 0 workflow

### 1. Establish the input ledger

Record the exact story-anchor source, current-state source, adapter path, and
grammar-state version in the trace header. Separate:

- observable/player state;
- derived design state and player-knowledge ledger;
- decision/allocation state such as budget and selected delivery mechanisms;
- external production/runtime state.

A draft trace does not mutate story canon or runtime state.
Repo-relative adapter paths are resolved against the already validated
`<GAME_REPO>` Git root.

### 2. Roll out the Intended Player continuously

Use the blank
[`PLAYABLE_WALKTHROUGH_TRACE.md`](../templates/PLAYABLE_WALKTHROUGH_TRACE.md)
and the
[`trace contract`](PLAYABLE_WALKTHROUGH_TRACE_CONTRACT.md). Write through the
whole requested span in player time before deciding beat packets. Preserve
control handoffs, immediate feedback, recent verbs, pacing, what the player
knows, and what they are waiting to learn.

The trace is the canonical production source after approval.

### 3. Annotate deltas, delivery, and proof

For every runtime, world, player-knowledge, or proposed player-affect delta:

1. state the before/after change;
2. choose `caused_by_player`, `witnessed_by_player`, or `offstage` delivery;
3. attach exact runtime validation or a reception contract;
4. emit `unresolved_delta` when the adapter or budget cannot support it.

The artifact must contain both continuous player-time prose and structured
moments. Whether authors draft prose first or structure first remains an open
Phase 0 question; do not hard-code an authoring order.

### 4. Segment the finished trace

Apply the boundary signals in
[`PLAYABLE_BEAT_PACKET_CONTRACT.md`](PLAYABLE_BEAT_PACKET_CONTRACT.md): player
intent, core verb, control mode, player understanding, expectation payoff, and
handoff to a new situation. Compile trace slices into beat packets; never
invent missing gameplay during packet compilation.

### 5. Run a blinded First-time Player session

Use a fresh model/session. A facilitator reveals the trace's
`visible_and_known` values one moment at a time and nothing else. Do not send
the story anchors, canonical action, enumerated available actions, response,
deltas, design intent, packet, or future moments.

At each reveal, ask the verifier to record:

- what it believes the immediate objective is;
- what action it would try next and why;
- what it may have missed or misread;
- whether it believes it has control;
- what feedback it expects.

Compare that report with the canonical trace outside the verifier session.
The first meaningful divergence is a reception finding; do not feed the
canonical answer back and call the continuation independent. Revise the
canonical trace, regenerate the blind projection, and rerun with another
fresh session. The allowed drift neighborhood is intentionally not fixed in
v0 and must be calibrated by the pilot.

### 6. Human review and production handoff

Record USER rejections as evidence for the future “feels like playing” rubric;
do not manufacture that rubric from factory opinion. Human approval remains
the Phase 0 gate. Only approved Intended Player trace slices compile into
production-facing beat packets.

Production uses each packet's runtime contract plus the resolved
`PRODUCTION_ADAPTER.md`. Asset and sound orders may then route to the sibling
factories. Reception-contract checks supplement, but never replace, a human
playtest of the runtime result.

## Canonical game-repo outputs

Under the resolved `<GAMEPLAY_ROOT>`:

```text
adapter/
  PROJECT_GAMEPLAY_PROFILE.md
  PRODUCTION_ADAPTER.md
state/
  GAMEPLAY_GRAMMAR_STATE.md
traces/<trace_id>/
  PLAYABLE_WALKTHROUGH_TRACE.md
  FIRST_TIME_PLAYER_INPUT.md
  FIRST_TIME_PLAYER_REPORT.md
beat_packets/<packet_id>.md
qa/<trace_id>_RECEPTION_REVIEW.md
```

`FIRST_TIME_PLAYER_INPUT.md` is a mechanically/manual-derived sequential
projection containing only `visible_and_known` values. It is stored for audit,
but should be revealed progressively rather than handed to the verifier as a
complete future timeline.
