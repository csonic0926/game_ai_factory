# PROJECT PROFILE — <project_id>

Contract: see `../../docs/PROJECT_PROFILE_CONTRACT.md`.

## Required

- `<PROJECT_ID>`: <project_id>
- `<WORLD_NAME>`: not fixed — see world baseline   # canon world name; never inferred from paths
- `<GAME_REPO>`: /absolute/path/to/game/repo
- `<STORY_ROOT>`: <GAME_REPO>/design/story
- `<PRIMARY_LOCALE>`: zh-TW            # language story text is AUTHORED in
- `<SHIPPED_LOCALES>`: zh-TW, en       # ordered list the game ships
- `<RUNTIME_SHAPE>`: one line describing what the game runtime consumes

## Optional (declare NOT_AVAILABLE explicitly if absent)

- `<BATTLE_SYSTEM>`: NOT_AVAILABLE
- `<TWIN_ROOT>`: NOT_AVAILABLE
- `<KNOWLEDGE_ROOT>`: <STORY_ROOT>/knowledge

## Adapter files

- `LANDING_SPEC.md`: NOT_AVAILABLE     # flip when written — unblocks chapter STEP 7
- `VISUAL_GRAMMAR.md`: NOT_AVAILABLE   # flip when written — unblocks chapter STEP 6.7
- `SYNC_SPEC.md`: NOT_AVAILABLE        # chapter STEP 10 skips when absent
- `STYLE_GUIDE.md`: NOT_AVAILABLE
- `GLOSSARY.csv`: NOT_AVAILABLE        # optional; present = sole canonical proprietary-term source
