# Story department — modules

The story department is a set of independently callable modules (rebuild of
2026-07-07, plan: umbrella repo `STORY_REBUILD_PLAN.md`). The old step
pipeline is one module among five, no longer the whole department.

| module | mode | what it does |
|---|---|---|
| [`world-rules-editor/`](world-rules-editor/README.md) | interactive (USER sovereignty) | create & revise a game's `WORLD_RULES.md` + `NARRATIVE_DELIVERY.md`; migrate a legacy `WORKFLOW_CORE_VARIABLES.md` |
| [`twin-db/`](twin-db/README.md) | tool + procedure | the story-world database: query/CRUD over `<STORY_ROOT>/story_world/`, plus the per-chapter write-back |
| [`beat-sheet-dialogue/`](beat-sheet-dialogue/README.md) | interactive (cannot be automated) | 攤田 → USER cuts & rules → converge into a chapter's emotional beat sheet |
| [`delivery-planner/`](delivery-planner/README.md) | headless-able | assign each beat of a finished beat sheet to a delivery channel, weighted by `NARRATIVE_DELIVERY.md`, and stamp the exact beat-sheet version it used |
| [`step-pipelines/`](step-pipelines/README.md) | headless | the proven WORLD / CHARACTER / CAST / CHAPTER step machines (files stay at `../core/steps/`) |

Production flow for a chapter, end to end:

```
sovereignty files ──┐
                    ├─ beat-sheet-dialogue ─→ beat sheet (per chapter, in <STORY_ROOT>/beat_sheets/)
twin-db (query) ────┘            │
                                 ▼
                       delivery-planner ─→ delivery plan (beat → channel,
                       bound to one beat-sheet version)
                                 │
                                 ▼
                  step-pipelines CHAPTER (STEP 2 takes assignments
                  from the beat sheet instead of discovering lines)
                                 │
                                 ▼
                  landing → twin-db write-back (new canon returns to the db)
```

Review gates are kept everywhere they existed, plus one new line in chapter
gates: **emotional acceptance** — which beat of the beat sheet did this
output transmit, and did the curve's holds and releases survive?
(Foundations: `../core/NARRATIVE_FOUNDATIONS.md`.)

Adapters (`../adapters/<project_id>/`) own per-game knowledge: the delivery
channel list (`DELIVERY_CHANNELS.md`), landing specs, style guide, and the
location of the sovereignty files.
