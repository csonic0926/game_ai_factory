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

## Adapter files

- `LANDING_SPEC.md`: AVAILABLE (scoped v0.1 — onboarding locale-key surface
  only). Chapter-scale work beyond that surface remains BLOCKED_BY_PROFILE
  until a general story runtime exists.
- `SYNC_SPEC.md`: NOT_AVAILABLE
- `STYLE_GUIDE.md`: NOT_AVAILABLE
