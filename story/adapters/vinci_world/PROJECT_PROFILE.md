# PROJECT PROFILE — vinci_world

Vinci World (web, PIXI.js client + Bun server).

> TOKEN HYGIENE: the ONLY canon name in this project is the world name
> **Vinci World**. Legacy tokens appearing in filesystem paths or git remotes
> (`doodi`, `renaiss`, `demo`) are historical repo names — they are NOT world
> canon and must never appear in story artifacts.

## Required

- `<PROJECT_ID>`: vinci_world
- `<WORLD_NAME>`: Vinci World (FIXED by user — the only settled name)
- `<GAME_REPO>`: /Users/hunglingki/git_projects/web_projects/vinci_world
- `<STORY_ROOT>`: /Users/hunglingki/git_projects/web_projects/vinci_world/design/story
- `<PRIMARY_LOCALE>`: zh-TW            # story authored in zh-TW (user preference; edit if wrong)
- `<SHIPPED_LOCALES>`: en, zh-TW, ko
  - NOTE: the game's i18n system is EN-source key catalogs (en is the catalog
    source of truth; zh-TW and ko must key-match). Landing must therefore emit
    EN catalog entries even though authoring is zh-TW.
- `<RUNTIME_SHAPE>`: web client with i18n key catalogs (EN-source, data-i18n
  DOM + t() render-time); NO story/event runtime exists yet — story runtime
  (dialogue/event system) is future work.

## Optional

- `<BATTLE_SYSTEM>`: NOT_AVAILABLE (mini-games/card tabletop exist but no
  story-driven battle system)
- `<TWIN_ROOT>`: NOT_AVAILABLE
- `<KNOWLEDGE_ROOT>`: <STORY_ROOT>/knowledge

## Sovereignty files (USER-authored, tools read-only)

- `<STORY_ROOT>/state/WORLD_RULES.md` — what is TRUE in the world
- `<STORY_ROOT>/state/NARRATIVE_DELIVERY.md` — how the game speaks
- Legacy `<STORY_ROOT>/state/WORKFLOW_CORE_VARIABLES.md` is now a pointer to
  the two files above (split 2026-07-07).

## Adapter files

- `LANDING_SPEC.md`: AVAILABLE (v0.2 — onboarding locale keys + scripted
  cutscenes as `.cutscene.json`). Chapter scenes that are NOT scripted
  cutscenes (free-roam / interactive gameplay) remain BLOCKED_BY_PROFILE
  until a general event runtime exists.
- `SYNC_SPEC.md`: NOT_AVAILABLE
- `DELIVERY_CHANNELS.md`: AVAILABLE (7 channels declared 2026-07-07; consumed
  by the delivery-planner module)
- `STYLE_GUIDE.md`: AVAILABLE (v1.0 — 富文本交接、禁造詞；binds ALL
  artifacts under `<STORY_ROOT>`, design docs included)
