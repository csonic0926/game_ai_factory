# Project Profile Contract (Adapter Contract)

The factory's step files are **project-agnostic**. Everything project-specific
lives in one adapter directory. Ownership split: the factory owns the
**contract** (this file, plus the blank answer sheets in `adapters/_template/`);
each game repo owns its **filled-in answers** — the adapter files describe that
game's runtime and staging capabilities, so they live with the code they
describe and version with the game.

## Canonical adapter location

The canonical home of a project's adapter is inside the game repo:

```
<STORY_ROOT>/adapter/     # i.e. <GAME_REPO>/design/story/adapter/
  PROJECT_PROFILE.md      # required — resolves all <VARIABLES> used by core steps
  VISUAL_GRAMMAR.md       # required for chapter staging — how approved text can actually be staged/shot
  LANDING_SPEC.md         # required for chapter runtime landing — how approved staging becomes runnable game data
  DELIVERY_CHANNELS.md    # declared delivery channels — read by chapter STEP 1 preflight
  SYNC_SPEC.md            # optional — post-landing sync duties (digital twin, frames, exports)
  STYLE_GUIDE.md          # optional — narration/prose style rules for this game
  style_lint_config.json  # optional — machine-checkable STYLE_GUIDE rules for review gates
```

## Adapter resolution order

An orchestrator (Claude or Codex) MUST resolve the adapter directory in this
order, MUST resolve the profile before dispatching any step worker, and MUST
pass the resolved values into the worker prompt:

1. An adapter path stated explicitly in the invocation, if any.
2. `adapters/registry.md` in the factory — the phonebook, one line per
   migrated project: `<project_id> → <absolute adapter path>`.
3. cwd convention: when the session's working directory is a game repo,
   look for `./design/story/adapter/`.
4. **Legacy fallback:** the factory-local `adapters/<project_id>/`.
   Unmigrated projects (e.g. rpg-1) keep resolving here unchanged.

`adapters/_template/` (the blank answer sheets) stays in the factory;
`scripts/init_story_root.sh` copies it into `<STORY_ROOT>/adapter/` when
onboarding a new game.

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
  adapter/                            # the project's filled-in adapter — canonical location (see above)
  state/
    WORLD_RULES.md                  # USER-authored: what is TRUE in the world (never AI-edited)
    NARRATIVE_DELIVERY.md           # USER-authored: how the game speaks (never AI-edited)
    WORKFLOW_CORE_VARIABLES.md      # legacy single file — full on unmigrated projects, pointer after migration
    world_baselines/                # WORLD_* artifacts
    character_baselines/            # per-character step artifacts + reviews
    characters/                     # packaged ch_<id>.json + index.json
    cast_management/                # CAST_* artifacts + CAST_ACTION_REQUESTS.md
    chapter_sources/                # preflight / story line / chapter spine / source JSON
    briefs/                         # ask-mode direction briefs (<workflow>_<stem>_BRIEF.md)
  beat_sheets/                      # per-chapter emotional beat sheets (beat-sheet-dialogue module)
  chapter_event_graphs/
  runtime_scene_drafts/
  qa/reports/
  knowledge/
  story_world/                      # the story-world database (world STEP 5 builds it; twin-db module maintains it)
  outcomes/<stage>/
```

Core step files reference paths ONLY under this layout (as `<STORY_ROOT>/...`)
or through the adapter files below. If a step file needs any other project
path, that is a factory bug.

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
stops before STEP 7 and reports that landing is blocked. When
`VISUAL_GRAMMAR.md` exists, the pipeline may still produce an approved staging
plan; it must not write runtime data without the landing spec.
World / character / cast workflows never need a landing spec.

## VISUAL_GRAMMAR.md — the staging / shooting contract

Chapter STEP 6.7 (and the branch implementation's reused STEP 6.7) delegate
the "can this engine actually show this?" question here. A visual grammar must
answer, concretely, for its game:

1. **View** — fixed or changeable viewpoint, map/screen grammar, and what a
   "shot" means in this game.
2. **Camera whitelist** — allowed camera operations (focus, pan, zoom,
   follow, fade, cut, letterbox, etc.) and unsupported operations.
3. **Actor performance** — how characters move, face, emote, speak, animate,
   and what they cannot perform.
4. **Cannot list** — cinematic / spatial / performance language the engine
   cannot currently shoot, such as close-ups, cut/reverse-shot, moving
   vehicles, background scroll, montage, or detailed gesture, when applicable.
5. **Native pacing** — what "stay", "speak", player movement, pauses,
   dialogue, and environmental holds feel like in this game.
6. **Presentation primitives** — concrete cutscene, player-operation,
   environment, text, sound, and transition primitives that STEP 6.7 may use
   and STEP 7 can mechanically map into runtime data.

If `VISUAL_GRAMMAR.md` is missing or marked `NOT_AVAILABLE`, chapter production
stops at STEP 6.7 and reports `BLOCKED_BY_PROFILE`. STEP 6 remains
medium-independent; STEP 6.5 must not reject a draft merely because it uses a
cinematic image that the visual grammar will later restage.

### LANDING_SPEC.md vs VISUAL_GRAMMAR.md

These two adapter files are complementary and must not replace each other:

- `LANDING_SPEC.md` declares **landing surfaces**: which runtime files, ids,
  locale keys, schemas, routing rules, and integrity checks receive story data.
- `VISUAL_GRAMMAR.md` declares **how to stage or shoot** a beat: camera, actor
  performance, forbidden presentation, native pacing, and the allowed
  operation primitives.

STEP 6.7 reads `VISUAL_GRAMMAR.md` to produce the staging plan. STEP 7 reads
`LANDING_SPEC.md` plus the approved staging plan to write runtime files.

## SYNC_SPEC.md — the post-landing sync contract

Chapter STEP 10 Part B delegates here (project-specific frame/export
regeneration, asset hooks). Missing spec ⇒ Part B is recorded as
`SKIPPED_BY_PROFILE` and the workflow proceeds to STEP 11. STEP 10 Part A —
the twin write-back via `scripts/twin_db.py` — is factory-owned and runs
whenever `<STORY_ROOT>/story_world/` exists, spec or no spec.

## Authority rules (inherited from the rpg-1 system, kept)

- The sovereignty files (`WORLD_RULES.md`, `NARRATIVE_DELIVERY.md`; legacy:
  `WORKFLOW_CORE_VARIABLES.md`) are user-authored; AI reads, never edits.
- One step at a time; every STEP n has a STEP n.5 review gate that can FAIL.
- File-based handoff only — a fresh worker must be able to resume from disk.
- Review steps never fix content; they only PASS/FAIL with reasons.
- Handoff artifacts are token-RICH working memory, never compressed
  summaries (USER ruling 2026-07-04): full natural prose in
  `<PRIMARY_LOCALE>`; no invented shorthand/labels — expand inherited ones
  back into plain language; workers over-read upstream sources rather than
  trust summaries; review gates verify meaning fidelity, not label counts.
  If `STYLE_GUIDE.md` exists it binds ALL `<STORY_ROOT>` artifacts.
