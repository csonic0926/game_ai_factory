# Module — world-rules-editor

Interactive module for creating and revising a game's two sovereignty files.
USER holds the pen; the AI is a scribe and a mirror, never an author of
record.

## The files it manages

- `<STORY_ROOT>/state/WORLD_RULES.md` — what is TRUE in the world: ontology,
  foundational laws, currency, decided-terms table, tone red lines.
  Template: `../../core/schemas/templates/WORLD_RULES.template.md`.
- `<STORY_ROOT>/state/NARRATIVE_DELIVERY.md` — how the game speaks: the
  explicitness dial, channel weighting, dialogue density.
  Template: `../../core/schemas/templates/NARRATIVE_DELIVERY.template.md`.

Sovereignty rule (same as the legacy WORKFLOW_CORE_VARIABLES rule, unchanged
in strength): AI workflows READ these files; only this module may WRITE
them, and only with the USER's explicit approval of the exact wording.

## Operations

1. **bootstrap** — copy the two templates into a game's `<STORY_ROOT>/state/`
   (also done by `scripts/init_story_root.sh`).
2. **revise** — the USER states a ruling in conversation; the module drafts
   the entry IN PLACE (right section, right file — world truth vs delivery),
   shows the exact diff, and writes only after the USER approves the wording.
   Entries the AI drafted but the USER has not line-item confirmed are marked
   【建議】or【草案待 USER 確認】so later readers know their weight.
3. **migrate** — split a legacy `WORKFLOW_CORE_VARIABLES.md` into the two
   files: sort every clause into world truth / delivery / production
   discipline (production clauses point to the factory core + adapter
   `STYLE_GUIDE.md` instead of moving into a sovereignty file), keep each
   clause's original USER-ruling date, and leave a pointer table at the old
   path. Reference migration: vinci_world, 2026-07-07.

## What does NOT belong in these files

- Production discipline (handoff rules, style lint, review procedure) —
  factory core and adapter `STYLE_GUIDE.md`.
- Facts derivable from the game repo or the twin database.
- Per-run direction answers — those go to `<STORY_ROOT>/state/briefs/`;
  offer promotion into a sovereignty file only when a ruling is durable,
  and only with explicit USER approval.
