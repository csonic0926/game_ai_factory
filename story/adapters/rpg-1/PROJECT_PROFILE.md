# PROJECT PROFILE — rpg-1

Reference adapter: the game this factory was extracted from. Its story system
predates the factory, but the paths below are contract-equivalent, so factory
workflows can run against it directly.

## Required

- `<PROJECT_ID>`: rpg-1
- `<WORLD_NAME>`: not fixed — see world baseline (`rpg-1` is a repo codename, not world canon)
- `<GAME_REPO>`: /Users/hunglingki/git_projects/Godot/rpg-1
- `<STORY_ROOT>`: /Users/hunglingki/git_projects/Godot/rpg-1/design
  - NOTE (legacy layout): this repo predates the canonical layout. Mapping:
    `<STORY_ROOT>/state/…` = `design/story_logic/state/…`,
    `<STORY_ROOT>/templates/…` = `design/story_logic/templates/…`,
    other roots (`chapter_event_graphs/`, `runtime_scene_drafts/`, `qa/`,
    `knowledge/`, `story_world/`) sit directly under `design/` as canonical.
- `<PRIMARY_LOCALE>`: zh-TW (台式書面語)
- `<SHIPPED_LOCALES>`: zh-TW, en, ja
- `<RUNTIME_SHAPE>`: Godot 4 + CSV runtime (settings/event.csv,
  settings/event_timelines.csv, locales/locales.csv, world_map_node.csv)

## Optional

- `<BATTLE_SYSTEM>`: 4x4 grid battles — enemies.csv / battles.csv /
  battle_layouts.csv / party_loadouts.csv; sim tool `gd/tools/battle_balance_sim.gd`
- `<TWIN_ROOT>`: /Users/hunglingki/git_projects/Godot/rpg-1/design/echeng_twin
- `<KNOWLEDGE_ROOT>`: /Users/hunglingki/git_projects/Godot/rpg-1/design/knowledge

## Adapter files

- `LANDING_SPEC.md`: AVAILABLE (pointer spec — see file)
- `VISUAL_GRAMMAR.md`: NOT_AVAILABLE (adapter predates STEP 6.7; fill before
  running new chapter staging)
- `SYNC_SPEC.md`: AVAILABLE (pointer spec — see file)
- `STYLE_GUIDE.md`: NOT_AVAILABLE as a file; wuxia-DOS narration rules live in
  the user's `wuxia-dos-narration` skill — treat that skill as the style guide.
