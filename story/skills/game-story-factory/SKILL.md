---
name: game-story-factory
description: Project-agnostic story creation orchestrator. Use when any game project needs world/character/cast/chapter story production. Resolves a project adapter under the factory's adapters/, then routes one fresh worker per step through the factory's step files with .5 review gates; also supports craft mode to invoke a single writing-technique doc independently, without a full step machine.
---

# Game Story Factory Orchestrator

Factory repo: `/Users/hunglingki/git_projects/tools/game_ai_factory/story`
(referred to below as `<FACTORY>`).

One skill orchestrates all four workflows: WORLD, CHARACTER, CAST, CHAPTER.
Everything project-specific comes from an adapter — never hardcode game paths.

## Invocation

`/game-story-factory <project_id> [world|character|cast|chapter] [start|resume|revise ...] [ask|auto]`
`/game-story-factory <project_id> craft <craft-name> [task / target files ...]`  — independent single-craft call
`/game-story-factory <project_id> beatsheet <chapter-stem>` — beat-sheet dialogue (interactive only; `<FACTORY>/modules/beat-sheet-dialogue/`)
`/game-story-factory <project_id> delivery <chapter-stem>` — delivery planning (`<FACTORY>/modules/delivery-planner/`)
`/game-story-factory <project_id> twin <query/mutation>` — story-world db (`<FACTORY>/modules/twin-db/`, tool `scripts/twin_db.py`)
`/game-story-factory <project_id> rules [revise|migrate]` — sovereignty files (interactive only; `<FACTORY>/modules/world-rules-editor/`)

The step pipeline is one module among five (`<FACTORY>/modules/README.md`);
each module is independently callable after Resolution.

If `<project_id>` is omitted, infer it from the current working repo by
matching `<GAME_REPO>` across `<FACTORY>/adapters/*/PROJECT_PROFILE.md`;
if no adapter matches, offer to create one from `adapters/_template/`.

## Interaction modes: ask / auto (USER ruling 2026-07-05)

Two modes govern how the orchestrator handles DIRECTION decisions — the
choices that shape a whole run and that review gates cannot fix afterwards
(a wrong direction produces a well-crafted wrong thing).

**ask — dialogue mode (default for a live human session).**
After Resolution and before dispatching the first step, put the run's 3–5
highest-leverage direction questions to the user in ONE round: each with
2–4 concrete options and a marked recommendation. Then write the answers
into a brief file at `<STORY_ROOT>/state/briefs/<workflow>_<stem>_BRIEF.md`
(rich prose per the handoff rules — the brief is what STEP 0/1 reads as
"the user's brief"). Mid-run, when a worker or gate surfaces a decision it
marks as open-for-USER, ask it right away as a small single question instead
of letting open items pile up to the end. If an answer sounds like a durable
ruling (true beyond this run), offer to write it into the matching
sovereignty file (`WORLD_RULES.md` for world truth, `NARRATIVE_DELIVERY.md`
for how the game speaks) — with the user's explicit approval only, via the
world-rules-editor module.

Direction questions per workflow (guidance, not a fixed form — pick what
actually matters for THIS run):
- WORLD: what the world exists to express; the player's relationship to the
  world; surface tone and how dark the underside may go.
- CHARACTER: what this character must carry for the story; formalize an
  existing canon slot or create freely; how the player should read them at
  first sight; name now or leave open.
- CAST: which stage is locked; ensemble size; any seats the user already
  has firm images for.
- CHAPTER: the player's pulse and posture this chapter (the v1→v2 lesson:
  quiet resident vs excited newcomer); the chapter's time frame (one day?
  one evening? several days? a journey? — the story's needs decide, there
  is no factory default); where the emotional peak should land; how much
  of the mystery budget to spend; any single big judgment call the chapter
  hinges on (e.g. hands-on first pull vs watching); delivery checkpoint
  (script approved first vs run straight through).

**auto — headless mode (REQUIRED for AI callers, cron, pipelines).**
Zero questions. Make the best-judgment call on every direction decision,
record each one in the artifacts with its reasons and a clearly labeled
open-items list (with fallback plans) for later human review. Hard USER
gates from the adapter (e.g. a landing spec's script-approval gate) are NOT
skipped in auto mode — the run stops there and reports, instead of asking.

Mode resolution when unspecified: a live human conversation defaults to
`ask`; a programmatic/headless invocation defaults to `auto`. Craft mode is
`auto` by nature (a single technique application) unless the task itself is
ambiguous enough to need one clarifying question.

## Resolution (always first)

1. Read `<FACTORY>/adapters/<project_id>/PROJECT_PROFILE.md`.
   Resolve `<GAME_REPO>`, `<STORY_ROOT>`, `<PRIMARY_LOCALE>`, `<SHIPPED_LOCALES>`,
   `<RUNTIME_SHAPE>` and optional variables. Contract:
   `<FACTORY>/docs/PROJECT_PROFILE_CONTRACT.md`.
2. Ensure `<STORY_ROOT>` exists with the canonical layout
   (bootstrap: `<FACTORY>/scripts/init_story_root.sh <STORY_ROOT>`).
3. Resolve the sovereignty files (USER-authored: read, never edit silently):
   - `<STORY_ROOT>/state/WORLD_RULES.md` — what is TRUE in the world
     (ontology, laws, currency, decided terms, tone red lines). Highest
     world-truth authority. Do not confuse with
     `state/world_baselines/WORLD_RULES.md`, a factory-produced artifact
     derived downstream of it — on conflict the sovereignty file wins.
   - `<STORY_ROOT>/state/NARRATIVE_DELIVERY.md` — how the game speaks
     (explicitness dial, channel weighting, dialogue density). Primary input
     of the delivery-planner module.
   If missing, copy from `<FACTORY>/core/schemas/templates/`.
   **Legacy:** a project that still carries a full
   `<STORY_ROOT>/state/WORKFLOW_CORE_VARIABLES.md` (e.g. rpg-1) keeps using
   it as before; a migrated project keeps a pointer there — follow it.

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

## Handoff language (anti-compression rules — USER ruling 2026-07-04)

Handoff files are the ONLY channel between workers. They are shared working
memory, NOT summaries. Compressed handoffs breed invented jargon that
eventually poisons story prose — so:

- Write artifacts token-RICH: full natural prose in `<PRIMARY_LOCALE>`.
  Every constraint carried forward states the rule in plain words, its
  source (which file, which ruling), why it exists, and what a violation
  would look like — a short paragraph each, never a coined label.
- NEVER invent shorthand: no code names, no compressed tags, no
  jargon-coinage for constraints, beats, or disciplines. When an upstream
  artifact already coined one, EXPAND it back into plain language when
  carrying it forward and cite the origin; do not propagate the label as
  if it were a term of art.
- Meaning may repeat across artifacts; wording should vary. Rich and
  diverse beats short and cryptic — a downstream worker can skim past
  redundancy, but cannot decompress a label it has never seen defined.
- Dispatch workers to LOOK THINGS UP: name every upstream artifact AND the
  canon files behind it; instruct workers to over-read the sources rather
  than trust any summary (including the orchestrator's own).
- Review gates verify MEANING fidelity against upstream sources. Label
  presence or count-matching alone is never sufficient evidence.
- If the adapter has `STYLE_GUIDE.md`, its language rules bind ALL
  artifacts written under `<STORY_ROOT>` — design documents and reviews
  included, not just story prose.

## Dispatch recipe (what every worker prompt must include — proven 2026-07-04)

Every worker dispatch hands over, explicitly:

1. the step file path (the worker's single source of truth for the task);
2. the resolved profile variables;
3. the sovereignty files `<STORY_ROOT>/state/WORLD_RULES.md` and
   `<STORY_ROOT>/state/NARRATIVE_DELIVERY.md` (or the legacy
   `WORKFLOW_CORE_VARIABLES.md` where the project has not migrated), named
   as the highest authority (read, never edit);
4. the adapter `STYLE_GUIDE.md` when present — with the reminder that it
   governs every word the worker writes, reports included;
5. the upstream artifacts to read AND the canon files they cite, with the
   instruction to over-read the originals rather than trust any summary;
6. one short plain-language paragraph of context: why this step exists
   right now (what changed upstream, what the user asked for, what a
   previous version got wrong). Workers write noticeably better when they
   understand the why, not just the what.

**Honesty loop (required):** creative-step workers END their report by
naming the one or two choices they are least confident about. The
orchestrator passes those named spots into the next review dispatch, and
the review gate must adjudicate each one explicitly (keep, or route back
with reasons) — never leave a flagged doubt to drift downstream to the
user unexamined.

**Lint in the gate:** when the adapter provides `style_lint_config.json`,
review-gate workers run
`python3 <FACTORY>/scripts/style_lint.py --config <adapter>/style_lint_config.json <artifact>`
and adjudicate every hit: citation-form usage (label quoted with source,
meaning expanded nearby) passes; term-of-art usage in prose fails.

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
Phase A trunk STEP 1→11.5: preflight → chapter task (ASSIGNMENT mode from
the chapter's emotional beat sheet when `<STORY_ROOT>/beat_sheets/<stem>_BEAT_SHEET.md`
exists — the beat sheet + delivery plan are the chapter's commissioned task;
legacy DISCOVERY mode only when no beat sheet exists, e.g. the rpg-1 back
catalog) → chapter spine → chapter source → event graph → runtime draft
(`<PRIMARY_LOCALE>`) → runtime landing → quoted dialogue revision →
story/prose QA → sync/write-back → outcomes/handoff.
Phase B STEP 12/12.5: open-story branch expansion/acceptance.
Phase C STEP 13→22.5: branch implementation = trunk files 1–11.5 minus STEP 10,
plus `BRANCH_IMPLEMENTATION_OVERLAY.md`, with a branch `<ARTIFACT_STEM>`.

Chapter hard bindings:
- STEP 2 mode is mechanical: beat sheet exists ⇒ assignment mode; a beat
  sheet with zero USER-ruled beats ⇒ BLOCKED_BY_BEAT_SHEET (report, never
  fall back silently). Producing a missing beat sheet is the interactive
  beat-sheet-dialogue module's job — a headless run cannot invent one.
- Emotional acceptance（情感驗收）: when the chapter has a beat sheet, the
  STEP 6.5 and STEP 9 gates verify which beat each output transmits and
  that the curve's holds and releases survived (`core/NARRATIVE_FOUNDATIONS.md`).
- STEP 7/7.5 (and 19/19.5) REQUIRE `adapters/<project_id>/LANDING_SPEC.md`;
  missing/NOT_AVAILABLE ⇒ stop at approved STEP 6 draft, report BLOCKED_BY_PROFILE.
  When the landing surface is a scripted cutscene, STEP 7 uses
  `core/craft/cutscene-staging.md` to emit the game's cutscene document.
- STEP 8/8.5 workers MUST use `core/craft/quoted-dialogue.md`.
- STEP 10 Part A (twin write-back via `scripts/twin_db.py writeback`) runs
  whenever `<STORY_ROOT>/story_world/` exists; Part B follows
  `adapters/<project_id>/SYNC_SPEC.md`, missing ⇒ SKIPPED_BY_PROFILE.

## Master loop

`WORLD → CHARACTER (one) → CAST → CHARACTER (next requested) → CAST → …
→ CAST_PASS → CHAPTER (repeat per chapter/branch)`

## Craft library & craft mode

Writing-technique docs live in `<FACTORY>/core/craft/`. They are self-contained
(no step/pipeline coupling; they consume only resolved profile variables such as
`<PRIMARY_LOCALE>` / `<SHIPPED_LOCALES>` plus the input artifacts you hand them).
Catalog + per-craft inputs/outputs: `<FACTORY>/core/craft/README.md`.

Two ways to use a craft:

1. **Inside a step machine** — step files name the craft docs they require
   (e.g. CHAPTER STEP 8/8.5 require `quoted-dialogue.md`); pass those paths to the
   step worker.
2. **Independent craft mode** — `/game-story-factory <project_id> craft <craft-name> [task / target files]`.
   Run Resolution first (profile → variables), then dispatch ONE fresh worker with:
   (a) `<FACTORY>/core/craft/<craft-name>.md` as its only source of truth,
   (b) the resolved profile variables it needs,
   (c) the input artifacts / target files named in the task,
   (d) the output path (usually an existing `<STORY_ROOT>` file to revise, or a
   named deliverable).
   **No `.5` gate** — craft mode applies a technique, it is not a pipeline stage;
   the worker self-checks against the craft doc's own criteria. Use it to run one
   technique (revise quoted dialogue, build a knowledge-stage JSON, write a memory
   ledger) without spinning up a full step machine. Craft mode never edits
   the sovereignty files (`WORLD_RULES.md`, `NARRATIVE_DELIVERY.md`, or a
   legacy `WORKFLOW_CORE_VARIABLES.md`).
