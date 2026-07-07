# STEP 10 — Sync Twin + Frame

## Purpose

Close the chapter's canon loop: write the chapter's new canon back into the
story-world database（每章回寫）, and run any adapter-defined sync so
project-specific frames serve the latest chapter state. New canon born in a
chapter must not stay buried in that chapter's artifacts.

## Read inputs from

Read these inputs before syncing:

- `<STORY_ROOT>/qa/reports/` — the chapter's passed QA reports
- the chapter artifacts of this stem: event graph, chapter source, landed
  runtime files (from STEP 7)
- `<STORY_ROOT>/story_world/` — the current database state (query with
  `<FACTORY>/scripts/twin_db.py --root <STORY_ROOT> search/get/list` to
  check what already exists before adding)
- `adapters/<project_id>/SYNC_SPEC.md`, when the adapter has one

## Save output to

Write one sync log to:

- `<STORY_ROOT>/state/frames/<artifact_stem>_sync_log_<yyyymmdd>.md`

Plus the write-back manifest used (keep it next to the sync log):

- `<STORY_ROOT>/state/frames/<artifact_stem>_writeback_<yyyymmdd>.json`

## Skill use

- No skill required for this step.

## Task

### Part A — twin write-back (runs whenever `<STORY_ROOT>/story_world/` exists)

1. Collect the chapter's NEW canon: entities that stuck (characters,
   places, objects, rituals), ruling-grade facts later chapters must not
   contradict, and relations between them. What does NOT qualify: prose,
   staging choices, one-off scene dressing. Check first that a candidate is
   actually new (query the db); prefer `update-entity` over duplication
   when a chapter deepened an existing entity.
2. Write the write-back manifest (shape documented in
   `<FACTORY>/modules/twin-db/README.md`), then apply it:

```bash
python3 <FACTORY>/scripts/twin_db.py --root <STORY_ROOT> writeback \
  --chapter <ARTIFACT_STEM> --manifest <manifest_path>
python3 <FACTORY>/scripts/twin_db.py --root <STORY_ROOT> validate
```

3. `validate` must exit clean; a validation error blocks this step.

If `<STORY_ROOT>/story_world/` does not exist (no world package was ever
built), record `NO TWIN DB` in the sync log and skip Part A.

### Part B — adapter sync (runs only when the adapter has `SYNC_SPEC.md`)

Follow the adapter's `SYNC_SPEC.md` exactly — it defines (or points to) the
project's own sync commands and frame targets (rpg-1's spec points to the
authoritative STEP 10 file in its game repo, which carries the
`make twin-check` + frame-rebuild command sequence). Missing spec ⇒ record
`SKIPPED_BY_PROFILE` for Part B; that is not a failure.

## Block definitions

### `SYNC LOG`

State, in a short readable log: the manifest applied and its record count,
the validate result, the adapter sync commands run (or the skip reason),
and the refreshed frame targets.

### `EXPECTED RESULT`

The story-world database contains the chapter's new canon with
`chapter:<ARTIFACT_STEM>` provenance and validates clean; any
adapter-defined frames align with the latest chapter landing.
