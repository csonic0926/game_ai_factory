# Gameplay Project Adapter Contract v0

## Ownership model

Gameplay Factory core is project-agnostic. The factory owns this contract and
blank answer sheets. Each game repo owns the filled answers describing that
game's current capabilities and versions them with the code/data they describe.

The three layers are:

1. **Factory core** — trace/delta/packet contracts, budgets, continuity and
   blinding invariants. It contains no project verbs or engine facts.
2. **Project gameplay adapter** — `PROJECT_GAMEPLAY_PROFILE.md`: verbs,
   systems, presentation modes, control semantics, rhythm axes, feedback and
   per-beat budget/capacity.
3. **Production adapter** — `PRODUCTION_ADAPTER.md`: runtime files/schemas,
   trigger/control/camera/dialogue/objective mappings, asset/sound/code hooks,
   and validation commands.

## Canonical adapter location

The filled answers live in the game repo:

```text
<GAMEPLAY_ROOT>/adapter/            # fixed: <GAME_REPO>/design/gameplay/adapter/
  PROJECT_GAMEPLAY_PROFILE.md       # required
  PRODUCTION_ADAPTER.md             # required
```

Factory-owned blank sheets remain in `gameplay/adapters/_template/`.

## Runtime roots and portable paths

`<GAME_REPO>` and `<GAMEPLAY_ROOT>` are runtime values, not machine paths
stored in a filled adapter:

1. Resolve `<GAME_REPO>` as an absolute Git root for the active call.
2. Resolve `<GAMEPLAY_ROOT>` at the fixed portable location
   `<GAME_REPO>/design/gameplay`.
3. Reject the resolution if it is inside the factory
   repo.

All versioned paths to game-owned files should be relative to `<GAME_REPO>`.
Absolute paths may exist only in an ignored machine-local registry or in
ephemeral run state. This lets any clone or fork use the same filled adapter.

## Game-repo and adapter resolution order

An AI caller must resolve the target game repo in this exact order:

1. game-repo path explicitly stated in the invocation;
2. the current working directory's Git root;
3. `gameplay/adapters/registry.local.md`, only when the invocation supplies an
   exact `<PROJECT_ID>` and the machine-local file exists.

The caller then resolves the adapter only at `<GAMEPLAY_ROOT>/adapter/` and
reads both required files before authoring a trace. The optional local
registry maps project ids to game-repo roots; it is a convenience pointer, not
authority and never a copy of the answers. Its tracked format is documented in
`gameplay/adapters/registry.example.md`.

There is no factory-local project adapter fallback. Scanning sibling folders,
inferring a game from another factory's registry, or committing developer
paths are contract defects.

If no adapter resolves, or any required section is `TBD`, blank, inconsistent,
or points to a missing file, stop with `BLOCKED_BY_ADAPTER`. Do not borrow a
story adapter or inspect engine code and silently turn inference into contract.

## Required project profile answers

`PROJECT_GAMEPLAY_PROFILE.md` defines:

| Answer | Contract |
| --- | --- |
| `<PROJECT_ID>` | Stable exact id; may be used by the optional local registry. |
| `<STORY_ANCHOR_SOURCE>` | Authoritative story-anchor location/interface; game-owned paths are relative to `<GAME_REPO>`, not copied summaries. |
| `<CURRENT_STATE_SOURCE>` | Authoritative runtime/world/current-progress source; game-owned paths are relative to `<GAME_REPO>`. |
| `<PRIMARY_LOCALE>` | Authoring language for prose artifacts. |
| Player verbs | Exhaustive currently supported verbs relevant to design, with preconditions and result/feedback. |
| Systems and spaces | Player-facing systems and traversal/interaction constraints. |
| Presentation modes | Supported free play, dialogue, AVG, cutscene, combat, overlays, etc.; unsupported modes explicit. |
| Control model | Legal owners, takeover/return cues, input-lock semantics. |
| Camera/HUD/reception capabilities | What can frame, hide, focus, notify, and confirm. |
| Gameplay grammar | Project-defined rhythm axes, repetition rules, expectations, completion and handoff conventions. |
| Budget/capacity | Per-beat limits for time, complexity, content, assets, engineering, and any other project cost. |
| Human review | Who approves traces/packets and where rejection evidence is recorded. |

Project-specific verbs or budget numbers anywhere in factory core are a
contract defect.

## Required production adapter answers

`PRODUCTION_ADAPTER.md` defines:

1. target runtime files and authoritative schemas;
2. id/key grammar and reference rules;
3. mappings for triggers, control ownership, camera, presentation/dialogue,
   objectives, state transitions, and completion feedback;
4. how runtime/world deltas are asserted and validated;
5. which reception conditions have runtime-observable proxies, without
   claiming those proxies prove human understanding;
6. asset, sound, localization, and code integration surfaces;
7. exact integrity, headless, screenshot, or playtest commands when available;
8. unsupported capabilities and escalation owner.

Missing capabilities are stated as `NOT_AVAILABLE`; authors must skip them or
emit an unresolved delta, never improvise.

## Canonical game-owned layout

```text
<GAMEPLAY_ROOT>/
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

The gameplay grammar state is derived/statistical design state, not runtime
truth. Runtime/world sources stay authoritative for execution state. Player
knowledge stays its own ledger and advances only through trace-supported
delivery.

## Story / gameplay / production boundary (v0)

- **Story Factory owns** what happens, canon/causality, character meaning, and
  approved story text/staging constraints.
- **Gameplay Factory owns** the continuous player-time experience around those
  anchors: intent, supported action, control choreography, delivery choice,
  reception conditions, pacing continuity, and packet contracts.
- **Production owns** encoding an approved packet through declared engine/data
  capabilities and returning validation evidence.

`story/core/craft/cutscene-staging.md` remains responsible for converting an
already approved story staging plan into the target cutscene document. It does
not decide the surrounding playable walkthrough, when control should be
returned, whether HUD/objective layers interfere, or how the cutscene hands
off to the next player action; those are gameplay packet responsibilities.

When story staging and a gameplay reception/control requirement conflict,
neither side silently overrides the other. Record an `unresolved_delta` and
route the specific capability or story-revision need to its owner. This v0
boundary preserves O5 as a pilot-review question for ambiguous edge cases
without leaving current ownership undefined.

## Onboarding and first pilot

Select the game repo explicitly or by running from its Git working tree.
Create `<GAMEPLAY_ROOT>/adapter/` from the two blank answer sheets and
`<GAMEPLAY_ROOT>/state/GAMEPLAY_GRAMMAR_STATE.md` from the blank state
template. Never overwrite an existing file. Fill and version all answers in
the game repo.

The Phase 0 pilot is the game explicitly named by the caller; it is never
selected by committed factory state. A developer who needs project-id routing
from the factory directory may create ignored
`gameplay/adapters/registry.local.md` using `registry.example.md` as the
format. Factory documents must not preselect or infer a pilot project.
