---
name: game-story-factory
description: Project-agnostic story creation orchestrator. Use when any game project needs world/character/cast/chapter story production. Resolves a project adapter under game_story_factory/adapters/, then routes one fresh worker per step through the factory's step files with .5 review gates.
---

# Game Story Factory Orchestrator

Factory repo: `/Users/hunglingki/git_projects/tools/game_ai_factory/story`
(referred to below as `<FACTORY>`).

One skill orchestrates all four workflows: WORLD, CHARACTER, CAST, CHAPTER.
Everything project-specific comes from an adapter — never hardcode game paths.

## Invocation

`/game-story-factory <project_id> [world|character|cast|chapter] [start|resume|revise ...]`

If `<project_id>` is omitted, infer it from the current working repo by
matching `<GAME_REPO>` across `<FACTORY>/adapters/*/PROJECT_PROFILE.md`;
if no adapter matches, offer to create one from `adapters/_template/`.

## Resolution (always first)

1. Read `<FACTORY>/adapters/<project_id>/PROJECT_PROFILE.md`.
   Resolve `<GAME_REPO>`, `<STORY_ROOT>`, `<PRIMARY_LOCALE>`, `<SHIPPED_LOCALES>`,
   `<RUNTIME_SHAPE>` and optional variables. Contract:
   `<FACTORY>/docs/PROJECT_PROFILE_CONTRACT.md`.
2. Ensure `<STORY_ROOT>` exists with the canonical layout
   (bootstrap: `<FACTORY>/scripts/init_story_root.sh <STORY_ROOT>`).
3. Ensure `<STORY_ROOT>/state/WORKFLOW_CORE_VARIABLES.md` exists; if missing,
   copy `<FACTORY>/core/schemas/templates/WORKFLOW_CORE_VARIABLES.template.md`.
   That file is USER-authored: read it, never edit it silently.

## Core orchestration rules (proven, inherited from the rpg-1 system)

- Treat each `STEP n` and `STEP n.5` as separate worker tasks.
- One fresh worker per step: give it only (a) the step file path,
  (b) the resolved profile variables it needs, (c) the input artifacts to read,
  (d) the output path to write. The step file is the worker's source of truth.
- File-based handoff only. Determine the next step from saved artifacts +
  matching review artifacts, never from conversation memory.
- Review (`.5`) steps only PASS/FAIL with reasons; they never fix content.
  FAIL ⇒ route back to the matching integer step; keep the failed review as
  the blocker record. PASS ⇒ next step.
- Substitute `<STORY_ROOT>`, `<PRIMARY_LOCALE>`, `<SHIPPED_LOCALES>`,
  `<PROJECT_ID>`, `<TWIN_ROOT>`, `<KNOWLEDGE_ROOT>`, `<BATTLE_SYSTEM>` in the
  worker prompt when dispatching (workers must never guess them).

## Step machines

Step files live under `<FACTORY>/core/steps/`.

**WORLD** — `core/steps/world/` STEP 0→6.5
(concept → rules → geography → institutions → objects/movement → twin
packaging → consistency QA). Complete at STEP 6.5 PASS.
Artifacts: `<STORY_ROOT>/state/world_baselines/`, `<STORY_ROOT>/story_world/`.

**CHARACTER** — `core/steps/character/` STEP 0→5.5, ONE character per run
(concept → world position → behavior/voice → knowledge/relations → packaging
→ QA). Before STEP 0, read `<STORY_ROOT>/state/cast_management/CAST_ACTION_REQUESTS.md`
if present — a named `CREATE_CHARACTER_REQUEST` overrides freeform invention.
Schema: `core/schemas/CHARACTER_SCHEMA.md`; template
`core/schemas/templates/character.template.json`.
Artifacts: `<STORY_ROOT>/state/character_baselines/`, `<STORY_ROOT>/state/characters/`.

**CAST** — `core/steps/cast/` STEP 0→5.5
(scope → audit → missing/overlap → relationship/pressure rebalance → action
requests → sufficiency QA). Artifacts: `<STORY_ROOT>/state/cast_management/`.

**CHAPTER** — `core/steps/chapter/`
Phase A trunk STEP 1→11.5: preflight → story line discovery → day spine →
chapter source → event graph → runtime draft (`<PRIMARY_LOCALE>`) → runtime
landing → quoted dialogue revision → story/prose QA → sync → outcomes/handoff.
Phase B STEP 12/12.5: open-story branch expansion/acceptance.
Phase C STEP 13→22.5: branch implementation = trunk files 1–11.5 minus STEP 10,
plus `BRANCH_IMPLEMENTATION_OVERLAY.md`, with a branch `<ARTIFACT_STEM>`.

Chapter hard bindings:
- STEP 7/7.5 (and 19/19.5) REQUIRE `adapters/<project_id>/LANDING_SPEC.md`;
  missing/NOT_AVAILABLE ⇒ stop at approved STEP 6 draft, report BLOCKED_BY_PROFILE.
- STEP 8/8.5 workers MUST use `core/craft/quoted-dialogue.md`.
- STEP 10 follows `adapters/<project_id>/SYNC_SPEC.md`; missing ⇒ SKIPPED_BY_PROFILE.

## Master loop

`WORLD → CHARACTER (one) → CAST → CHARACTER (next requested) → CAST → …
→ CAST_PASS → CHAPTER (repeat per chapter/branch)`

## Craft library

Writing-technique docs in `<FACTORY>/core/craft/` (story-logic-ledger,
character-memory-ledger, quoted-dialogue, antagonist-pressure-design,
choice-aftermath-writing, character-context, knowledge-stage-json,
world-state-snapshot, rest-moment-progression, story-attributes).
Step files name the craft docs they require; pass those paths to workers.
