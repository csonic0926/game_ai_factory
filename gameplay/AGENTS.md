# AI Caller Landing — gameplay_factory

You are an AI agent translating approved story anchors into a continuous,
player-time gameplay design for a game.

## Start here

1. Read `docs/PROJECT_ADAPTER_CONTRACT.md`.
2. Resolve the target game repo in this order: an explicit game-repo path in
   the invocation → the current working directory's Git root → the optional,
   ignored `adapters/registry.local.md` entry for an explicit `project_id`.
   Never discover a game by scanning sibling directories or from a committed
   developer path.
3. Set `<GAMEPLAY_ROOT>` to `<GAME_REPO>/design/gameplay`, validate that it is
   inside the game repo and outside this factory repo, and resolve the adapter only at
   `<GAMEPLAY_ROOT>/adapter/`.
4. Read both resolved answer files: `PROJECT_GAMEPLAY_PROFILE.md` and
   `PRODUCTION_ADAPTER.md`. A missing or incomplete answer file means
   `BLOCKED_BY_ADAPTER`; do not invent project capabilities.
5. Read `docs/AI_CALLER_LANDING.md`, then use the document-first Phase 0
   workflow. There is intentionally no skill, step machine, or CLI yet.

## Hard rules

- **Walkthrough first.** Author one continuous Playable Walkthrough Trace in
  player time. Do not fill gaps between pairs of story beats independently.
- **Segment second.** Beat boundaries emerge from player-state delta detection
  after the trace exists; do not outline packets first.
- **Keep evidence partitions separate.** `visible_and_known` records only what
  is actually available to the player. `design_intent` and design annotations
  must never leak into it.
- **Blind the verifier.** A fresh First-time Player session receives only the
  sequential `visible_and_known` projection. It must not receive the canonical
  action, available-action enumeration, deltas, anchors, or design intent.
- **Compile only the intended trace.** The Intended Player trace is canonical.
  The First-time Player report diagnoses reception failures; it is never an
  alternate production source.
- **Adapters are authority.** Verbs, systems, presentation modes, rhythm axes,
  budgets, engine mappings, and validation commands come from the resolved
  game-owned adapter. None belong in factory core.
- **Artifacts land in the game repo.** Traces, verifier projections/reports,
  beat packets, grammar state, and filled adapter answers live under the
  project's `<GAMEPLAY_ROOT>`, never under this factory.
- **Paths are portable.** Persist game-repo-relative paths in filled adapters.
  Resolve absolute paths only for the active run; never write a developer's
  home-directory or drive-specific path into versioned factory files.
- **Fail closed on ownership.** Before any write, resolve the destination and
  reject it if it is outside `<GAME_REPO>` or inside the factory repo.
- **Human playtest remains final.** The simulated First-time Player is only a
  paper-stage prefilter.
- If a required delta cannot be delivered within declared capabilities or
  budget, emit `unresolved_delta`; do not silently change the story anchor or
  pretend the runtime can prove player understanding.

## Contract files

- `docs/PLAYABLE_WALKTHROUGH_TRACE_CONTRACT.md`
- `docs/PLAYABLE_BEAT_PACKET_CONTRACT.md`
- `docs/PROJECT_ADAPTER_CONTRACT.md`
