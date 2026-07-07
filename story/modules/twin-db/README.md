# Module — twin-db

The story-world database. What used to be a one-shot package
(`DIGITAL_TWIN_PACKAGE.md` + frozen JSON, produced once by WORLD STEP 5 and
never maintained) is now a LIVE database with a maintained access path:
entities (people, places, objects, laws, rituals), grouped seed records,
stable facts, and relations — queryable, editable, growing with every
chapter.

## Storage

Unchanged and git-versioned, under `<STORY_ROOT>/story_world/`:

- `seed_entities.json` — canonical entities (`{id, name, type, summary, why_included}`)
- `seeds/*.json` — grouped seed records per world layer (geography,
  institutions, logistics, rules, facts, relations)
- `changelog.jsonl` — append-only mutation log, written by the tool
- `DIGITAL_TWIN_PACKAGE.md` — the human-readable package overview (WORLD
  STEP 5 output; still the right first read for a fresh worker)

## The tool

`scripts/twin_db.py` (python3, no dependencies):

```
twin_db.py --root <STORY_ROOT> list [--type place]
twin_db.py --root <STORY_ROOT> get <id>
twin_db.py --root <STORY_ROOT> search <keyword> [--limit N]
twin_db.py --root <STORY_ROOT> add-entity / update-entity
twin_db.py --root <STORY_ROOT> add-fact / add-relation
twin_db.py --root <STORY_ROOT> add-record / update-record   # any seeds list
twin_db.py --root <STORY_ROOT> writeback --chapter <STEM> --manifest <file>
twin_db.py --root <STORY_ROOT> validate
```

Every mutation appends a changelog line; `--chapter <STEM>` stamps new
records with `source: chapter:<STEM>`. `validate` hard-fails on duplicate
ids / broken JSON and warns on dangling relation references.

## Querying is a standard worker action

Dispatches give workers the query entry (`twin_db.py --root <STORY_ROOT>
search/get`) instead of copying world facts through handoff files. Handoff
files still carry the WHY and the constraints in rich prose (anti-compression
rules unchanged) — but world facts are looked up at the source, not
transcribed. Chapter STEP 1 (preflight) and any craft that needs world state
query the db directly.

## Per-chapter write-back（每章回寫）

New canon born in a chapter — a new character who stuck, a new location, a
new ruling-grade fact — no longer stays buried in that chapter's artifacts.
At chapter close (CHAPTER STEP 10):

1. The step worker collects the chapter's new canon into a write-back
   manifest (JSON: `entities` / `facts` / `relations` / `records`).
2. `twin_db.py writeback --chapter <STEM> --manifest <file>` applies it with
   provenance stamps.
3. `twin_db.py validate` must pass afterwards; the sync log records the
   manifest and the validate result.

What qualifies for write-back: facts that later chapters must not
contradict. What does not: prose, staging choices, one-off scene dressing.
When in doubt, the STEP 10.5 gate adjudicates.

## Ownership boundary

- WORLD STEP 5 still builds the INITIAL package from the world baselines.
- After that, this module owns the data's life: revision passes of STEP 5
  must respect chapter-written records (merge, never blind-regenerate —
  `changelog.jsonl` shows what chapters added).
- USER sovereignty files (`state/WORLD_RULES.md`) outrank the db: on
  conflict, fix the db.
