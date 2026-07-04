# Project Profile Contract (Adapter Contract)

The factory's step files are **project-agnostic**. Everything project-specific
lives in one adapter directory:

```
adapters/<project_id>/
  PROJECT_PROFILE.md    # required — resolves all <VARIABLES> used by core steps
  LANDING_SPEC.md       # required for chapter production — how approved text becomes runnable game data
  SYNC_SPEC.md          # optional — post-landing sync duties (digital twin, frames, exports)
  STYLE_GUIDE.md        # optional — narration/prose style rules for this game
```

An orchestrator (Claude or Codex) MUST resolve the profile before dispatching
any step worker, and MUST pass the resolved values into the worker prompt.

## Variables every PROJECT_PROFILE.md must define

| Variable | Meaning |
|---|---|
| `<PROJECT_ID>` | adapter directory name, stable id |
| `<WORLD_NAME>` | the canon name of the game world, exactly as it may appear in story artifacts. Mark `FIXED` if user-settled, or `not fixed — see world baseline`. Workers MUST take the world's name from this field only — never infer it from repo paths, git remotes, or `<PROJECT_ID>` (those may carry legacy tokens that are NOT canon) |
| `<GAME_REPO>` | absolute path to the game repository |
| `<STORY_ROOT>` | absolute path where all story artifacts live (inside the game repo, so story versions with the game) |
| `<PRIMARY_LOCALE>` | the locale story text is AUTHORED in (source of truth) |
| `<SHIPPED_LOCALES>` | full ordered locale list the game ships |
| `<RUNTIME_SHAPE>` | one line: what the game runtime consumes (e.g. "event CSV + locales CSV", "Godot dialogue JSON", "web JSON + i18n key catalogs") |

Optional variables (declare explicitly as `NOT_AVAILABLE` if absent — workers
must treat a missing optional capability as a hard skip, never improvise):

| Variable | Meaning |
|---|---|
| `<BATTLE_SYSTEM>` | pointer to combat data docs if the game has battles |
| `<TWIN_ROOT>` | digital-twin/world-mirror root if the project keeps one |
| `<KNOWLEDGE_ROOT>` | player-knowledge stage files root (default `<STORY_ROOT>/knowledge/`) |

## Canonical STORY_ROOT layout (factory-owned, same for every project)

```
<STORY_ROOT>/
  state/
    WORKFLOW_CORE_VARIABLES.md      # USER-authored creative rules (never AI-edited)
    world_baselines/                # WORLD_* artifacts
    character_baselines/            # per-character step artifacts + reviews
    characters/                     # packaged ch_<id>.json + index.json
    cast_management/                # CAST_* artifacts + CAST_ACTION_REQUESTS.md
    chapter_sources/                # preflight / story line / day spine / source JSON
    briefs/                         # ask-mode direction briefs (<workflow>_<stem>_BRIEF.md)
  chapter_event_graphs/
  runtime_scene_drafts/
  qa/reports/
  knowledge/
  story_world/                      # digital-twin packaging output (world STEP 5)
  outcomes/<stage>/
```

Core step files reference paths ONLY under this layout (as `<STORY_ROOT>/...`)
or through the three spec files below. If a step file needs any other
project path, that is a factory bug.

## LANDING_SPEC.md — the landing contract

Chapter STEP 7 (and branch STEP 19) delegate ALL runtime knowledge here.
A landing spec must answer, concretely, for its game:

1. **Target files** — exact runtime files approved scene text lands into.
2. **Id & key grammar** — event ids, locale key patterns, naming rules.
3. **Granularity rules** — e.g. one click/advance per row/node; how choices split.
4. **Choice & routing encoding** — how options, conditions, and jumps are written.
5. **Locale landing** — how `<PRIMARY_LOCALE>` text and other locales are stored;
   what placeholder discipline applies before translation passes.
6. **Integrity checklist** — mechanical checks (dangling ids, orphan keys,
   unreachable nodes) and how to run them (script commands if any).
7. **Battle/minigame hooks** — how gameplay triggers are referenced from story
   data, or `NOT_AVAILABLE`.

If `LANDING_SPEC.md` is missing or marked `NOT_AVAILABLE`, chapter production
stops at STEP 6 (approved runtime draft) and reports that landing is blocked.
World / character / cast workflows never need a landing spec.

## SYNC_SPEC.md — the post-landing sync contract

Chapter STEP 10 delegates here (twin sync, frame/export regeneration, asset
hooks). Missing spec ⇒ STEP 10 is recorded as `SKIPPED_BY_PROFILE` and the
workflow proceeds to STEP 11.

## Authority rules (inherited from the rpg-1 system, kept)

- `WORKFLOW_CORE_VARIABLES.md` is user-authored; AI reads, never edits.
- One step at a time; every STEP n has a STEP n.5 review gate that can FAIL.
- File-based handoff only — a fresh worker must be able to resume from disk.
- Review steps never fix content; they only PASS/FAIL with reasons.
- Handoff artifacts are token-RICH working memory, never compressed
  summaries (USER ruling 2026-07-04): full natural prose in
  `<PRIMARY_LOCALE>`; no invented shorthand/labels — expand inherited ones
  back into plain language; workers over-read upstream sources rather than
  trust summaries; review gates verify meaning fidelity, not label counts.
  If `STYLE_GUIDE.md` exists it binds ALL `<STORY_ROOT>` artifacts.
