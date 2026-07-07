# Module — step-pipelines

The proven WORLD / CHARACTER / CAST / CHAPTER step machines with `.5` review
gates. Demoted from "the whole story department" to one module among five
(2026-07-07 rebuild); the files themselves stay where they always were so no
dispatch path breaks:

- step files: `../../core/steps/{world,character,cast,chapter}/`
- orchestrator: `../../skills/game-story-factory/SKILL.md`
- schemas & templates: `../../core/schemas/`
- craft library: `../../core/craft/`

What the rebuild changed inside the machines:

- CHAPTER STEP 1/2/2.5 now run in **assignment mode** when the chapter has a
  beat sheet (`<STORY_ROOT>/beat_sheets/`) — STEP 2 takes its task from the
  beat sheet (+ delivery plan when present) instead of discovering story
  lines on the spot. With no beat sheet (e.g. rpg-1 back catalog), the
  legacy discovery mode runs unchanged.
- Chapter review gates carry an **emotional acceptance** line: which beat of
  the beat sheet did this output transmit; did the curve's holds and
  releases survive? (`../../core/NARRATIVE_FOUNDATIONS.md`)
- CHAPTER STEP 10 writes new canon back into the twin database
  (`../twin-db/README.md`) in addition to any adapter `SYNC_SPEC.md` sync.
- Workers read the sovereignty files `WORLD_RULES.md` +
  `NARRATIVE_DELIVERY.md` (legacy projects: `WORKFLOW_CORE_VARIABLES.md`).
