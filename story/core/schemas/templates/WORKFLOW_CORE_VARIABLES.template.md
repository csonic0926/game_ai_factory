# Workflow Core Variables — SUPERSEDED (2026-07-07)

This template is retired. The single user-authored control file mixed three
kinds of sovereignty, so it was split (see the umbrella repo's
`STORY_REBUILD_PLAN.md`, section 三):

| was in this file | now lives at | sovereignty |
|---|---|---|
| what is TRUE in the world (ontology, laws, currency, terminology philosophy, tone red lines) | `<STORY_ROOT>/state/WORLD_RULES.md` — template: `WORLD_RULES.template.md` | USER-authored, tools read-only; proprietary-term entries live only in adapter `GLOSSARY.csv` when available |
| how the game SPEAKS (explicitness dial, channel weighting, dialogue density) | `<STORY_ROOT>/state/NARRATIVE_DELIVERY.md` — template: `NARRATIVE_DELIVERY.template.md` | USER-authored, tools read-only |
| production discipline (style, language, handoff anti-compression, review procedure) | factory core (`SKILL.md`, `core/`) + adapter `STYLE_GUIDE.md` | factory-maintained |

Rules for existing projects:

- A project whose `<STORY_ROOT>/state/WORKFLOW_CORE_VARIABLES.md` still exists
  as a full legacy file (e.g. rpg-1) keeps working: workers read it as before.
- A migrated project keeps a pointer at the old path naming the two new files;
  workers follow the pointer.
- `init_story_root.sh` no longer creates this file; it creates the two new
  sovereignty files from their templates.
