# Knowledge Stage JSON

*Creates and maintains per-stage player-knowledge JSON files under `<STORY_ROOT>/knowledge/` (INTRO/PROLOGUE/CHAPTER_ONE, etc.) with a stable schema, links to the runtime locale keys, and minimal diffs.*

## Scope

Use this doc when you need to:
- Add a new stage file under `<STORY_ROOT>/knowledge/` (e.g. `PROLOGUE.json`, `CHAPTER_ONE.json`).
- Update an existing stage’s knowledge without rewriting unrelated content.
- Keep a clean mapping between “what the player should know” and the exact runtime locale keys where that knowledge is introduced (locale data lands via the adapter `LANDING_SPEC.md`).

Do **not** use this doc for:
- Writing story prose or timelines (use the chapter/story workflows).
- Editing `<STORY_ROOT>/state/*` world state directly (use the snapshot/state docs).

## Folder + naming

- Folder: `<STORY_ROOT>/knowledge/` (or `<KNOWLEDGE_ROOT>` if the project profile overrides it)
- File names: `INTRO.json`, `PROLOGUE.json`, `CHAPTER_ONE.json`, etc.
- Stage id inside file must match the filename stem (e.g. `INTRO`).

## JSON schema (stable)

Each stage JSON must be an object with:
- `stage_id` (String)
- `version` (int, start at 1)
- `source_locales_keys` (Array[String]) — exact locale keys that introduce this stage’s info (keys live in the runtime locale data defined by the adapter `LANDING_SPEC.md`)
- `knowledge_atoms` (Array[Object]) — high-level “player knows X” records (not prose)
  - `id` (String, snake_case, stable)
  - one short, high-level statement field per shipped locale, keyed by locale code — one field for each of `<SHIPPED_LOCALES>` (example for a zh-TW/en/ja project: `zh`, `en`, `ja` fields, e.g. `zh: 知道魔教`)
- `notes` (Array[String]) — implementation notes, cross-links, TODOs

### knowledge_atoms rules (MANDATORY)

- Keep statements **high-level** and audit-friendly (examples from a wuxia project, `<PRIMARY_LOCALE>` = zh-TW):
  - ✅ “知道魔教”
  - ✅ “知道魔教教主是封家失蹤的下任家主”
  - ✅ “知道簡家與封家是血仇”
  - ❌ Do not restate full intro/story prose lines.
- One atom = one concept; avoid packing multiple independent facts unless they are inseparable.
- Keep `id` stable once created; only update the text if needed.

## Update rules

- Minimal diffs: only change entries that are required by the user’s request.
- Do not reorder arrays unless necessary for correctness.
- When you add new `source_locales_keys`, verify those keys exist in the runtime locale data (per the adapter `LANDING_SPEC.md`).
- If a stage is introduced by multiple surfaces (intro text + story timeline), include all relevant keys.

## Workflow

1) Identify stage file and desired knowledge delta.
2) Update `source_locales_keys` first (so provenance is clear).
3) Update `player_knowledge.must_know` statements to match the introduced keys.
4) Update `entities` lists only if new facts introduce new named entities.
5) Sanity-check: stage facts do not leak future spoilers unless explicitly allowed.

## Reference implementation: event-timeline CSV runtime (rpg-1 heritage)

> Original rpg-1 mappings, kept as a worked example only. Real projects follow
> their adapter `LANDING_SPEC.md` instead.

- `source_locales_keys` pointed at exact keys in `locales/locales.csv`.
- `knowledge_atoms` carried exactly three statement fields: `zh` (繁中, primary), `en`, `ja`.
