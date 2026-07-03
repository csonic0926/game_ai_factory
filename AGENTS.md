# AGENTS — game_ai_factory

You are an AI agent driving game production. This repo is an **umbrella** over
three factories: `asset/`, `story/`, `sound/`.

1. Read [`AI_CALLER_LANDING.md`](AI_CALLER_LANDING.md) and route to a factory.
2. Each factory has its own `AGENTS.md` / landing + calling contract — obey it.
3. Factory outputs land in the **game repo**, never under this umbrella.
4. Factory-side changes (new workflow/provider/stage/schema) go in the relevant
   sub-factory via normal commits; keep each factory's contract stable for callers.

Sub-factory entry points:
- `asset/` → `asset/AGENTS.md`, `asset/docs/AI_CALLER_LANDING.md`, `asset/itf.py`
- `story/` → `story/AGENTS.md`, skill `game-story-factory`
- `sound/` → `sound/docs/AI_CALLER_LANDING.md`, `sound/sfx.py`
