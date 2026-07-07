# AI Caller Landing — game_story_factory

You are an AI agent (Claude Code or Codex) driving story production for a game.

## Start here

1. Read `docs/PROJECT_PROFILE_CONTRACT.md` — the adapter contract.
2. Resolve the project: `adapters/<project_id>/PROJECT_PROFILE.md`.
   No adapter? Copy `adapters/_template/` and fill it (ask the user for
   `<STORY_ROOT>` and locales; do not guess `LANDING_SPEC.md`).
3. Orchestrate via `skills/game-story-factory/SKILL.md` — it defines the four
   step machines (world / character / cast / chapter), the step-selection rule,
   and the worker-handoff rule.

## Hard rules

- One fresh worker per `STEP n` / `STEP n.5`; pass it only the step file path,
  resolved profile variables, input artifact paths, output path.
- Never edit the sovereignty files `state/WORLD_RULES.md` /
  `state/NARRATIVE_DELIVERY.md` (user-authored; legacy projects:
  `WORKFLOW_CORE_VARIABLES.md`). Only the world-rules-editor module writes
  them, with explicit USER approval.
- Never hardcode a game path in `core/` — if a step needs a project path that
  the contract cannot express, that is a factory bug: fix the contract, not the step.
- Chapter STEP 7 without a usable `LANDING_SPEC.md` ⇒ BLOCKED_BY_PROFILE
  (stop at the approved STEP 6 draft; tell the user what the spec must define).
- Review steps output PASS/FAIL + reasons only.

## Cross-repo requests

Factory-side changes (new step, contract extension, new craft doc) belong in
this repo via normal commits. Game-side artifacts always land under the game
repo's `<STORY_ROOT>` — never under `core/` or `adapters/`.
