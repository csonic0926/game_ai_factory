# Craft library

Reusable writing-technique docs. Each is **self-contained** (no step/pipeline
coupling): it consumes only resolved profile variables (`<PRIMARY_LOCALE>`,
`<SHIPPED_LOCALES>`, `<STORY_ROOT>`, `<KNOWLEDGE_ROOT>`, `<BATTLE_SYSTEM>`, …)
plus the input artifacts you hand it.

Two ways to use a craft (see the orchestrator `SKILL.md`):

1. **Inside a step machine** — a step file names the craft it requires and the
   step worker reads it (e.g. CHAPTER STEP 8/8.5 → `quoted-dialogue`).
2. **Independent craft mode** — `/game-story-factory <project_id> craft <craft-name> [task / target files]`.
   Resolution runs first, then ONE fresh worker is dispatched with the craft doc
   as its only source of truth + resolved vars + input/target files + output path.
   No `.5` gate; the worker self-checks against the craft doc. Never edits
   the sovereignty files (`WORLD_RULES.md`, `NARRATIVE_DELIVERY.md`, or a
   legacy `WORKFLOW_CORE_VARIABLES.md`).

## Catalog

| craft-name | purpose | typical input | output |
| --- | --- | --- | --- |
| `story-logic-ledger` | causality-first ledger (stakes, constraints, info distribution, beat reasons, trigger, aftermath deltas) **before** writing a scene/fight | scene intent + world/character state | logic ledger doc for the scene |
| `character-memory-ledger` | keep "who knows what" consistent; per-character memory ledger + deltas after a scene | scene text + involved characters | memory ledgers + memory deltas |
| `quoted-dialogue` | rewrite **only** quoted spoken lines to sound like real speech under pressure, one clear pragmatic function, aligned across locales | scene/lines with quoted dialogue | revised quoted lines (all locales) |
| `character-context` | load characters and emit context cards for writing / battle design | characters JSON | per-character context cards |
| `antagonist-pressure-design` | pressure matrix for pursuers/antagonists (objectives, beliefs, constraints, evidence + escalation ladder, failure mode) | antagonist concept + world/pressure | antagonist pressure matrix |
| `choice-aftermath-writing` | design + write the branch that follows a specific choice (pacing-first) | the choice + current state | aftermath scene + landing notes |
| `knowledge-stage-json` | create/maintain per-stage player-knowledge JSON with stable schema + locale links + minimal diffs | stage id + locale keys | `<KNOWLEDGE_ROOT>` stage JSON |
| `world-state-snapshot` | maintain open-story world state (arcs, factions, character memory, snapshots) + deltas | current state + latest scene | snapshot update + deltas |
| `rest-moment-progression` | design a "rest/town" moment giving limited actions to improve readiness, then route it | story moment + available systems | rest-moment design + routing |
| `story-attributes` | design + land attribute/skill checks in events (success line / fail-forward / costs) | event + attribute system (`<BATTLE_SYSTEM>`) | check design + field mapping |
| `cutscene-staging` | turn an approved STEP 6.7 staging plan into a playable cutscene document for the target game's runtime (CHAPTER STEP 7 landing) | approved STEP 6.7 staging plan + STEP 6 draft + adapter `LANDING_SPEC` cutscene surface | `.cutscene.json` document + dialogue locale keys |
| `dialogue-runway` | pave a 4–7 line conversation runway to a USER-set destination line (creative KPI) so it lands earned, as an invitation | scene constraints + KPI line + arrival emotion | 3 annotated candidate runways (USER cuts) |

Applicability is project-dependent: `story-attributes` / `rest-moment-progression`
assume an RPG-ish system (`<BATTLE_SYSTEM>` present); `knowledge-stage-json`
assumes `<KNOWLEDGE_ROOT>` is set in the adapter profile. A craft whose required
variable is `NOT_AVAILABLE` for the project should report that and stop, not
guess.
