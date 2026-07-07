# STEP 9 — Story + Prose QA

## Purpose

Run final chapter story QA and prose QA on the latest landed chapter artifacts, then save both reports.

## Read inputs from

Read the latest chapter artifacts relevant to QA:

- `<STORY_ROOT>/chapter_event_graphs/<ARTIFACT_STEM>.md`
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_LANDING.md`
- touched CSV / locale files for landed runtime review
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_zh.md` when the pre-landing prose draft is needed for comparison
- `<STORY_ROOT>/runtime_scene_drafts/<ARTIFACT_STEM>_LANDING_REVIEW.md` for the landing status being reviewed
- `<STORY_ROOT>/beat_sheets/<ARTIFACT_STEM>_BEAT_SHEET.md`, when it exists —
  the emotional-acceptance source for the whole chapter

## Save output to

Write QA reports to:

- `<STORY_ROOT>/qa/reports/<stage>_story_r<round>_<yyyymmdd>.md`
- `<STORY_ROOT>/qa/reports/<stage>_prose_r<round>_<yyyymmdd>.md`

Use `<STORY_ROOT>/qa/templates/review_report.md` for each report.

## Skill use

- No skill required for this step.

## Task

1. Run story QA with `<STORY_ROOT>/qa/story_quality_checklist.md`.
2. Run prose QA with `<STORY_ROOT>/qa/prose_quality_checklist.md`.
3. Run the final chapter locale audit across the graph, the target runtime files, and the locale storage defined by the adapter `LANDING_SPEC.md`.
4. Save one report for each run.
5. Keep the branch identifier in `<stage>` or in the report body when the chapter belongs to a branch-specific artifact stem.
6. If either QA run finds a blocker, revise the relevant upstream chapter artifacts and rerun both QA checks after the revision batch.

## Required run sequence

- Run story QA first.
- Run prose QA second.
- During these checks, audit the landed chapter for final locale integrity and chapter-level consistency.
- Re-run both checks after each revision batch until both reports pass.

## Final audit scope

Check these chapter-local files together:

- `<STORY_ROOT>/chapter_event_graphs/<ARTIFACT_STEM>.md`
- the target runtime files and locale storage defined by the adapter `LANDING_SPEC.md`

Keep the audit chapter-local unless a reference truly crosses chapters.

## Required final audit checks

### CSV shape and key existence

Verify:

- locale rows have the correct number of columns
- every timeline, world-map, and event locale key exists
- no duplicate keys or ids were introduced for the chapter

### Orphaned locale keys

Flag chapter-local locale keys that exist in the locale storage but are not referenced by any target runtime file defined by the adapter `LANDING_SPEC.md`.

### Knowledge-order leaks

Compare the graph reveal order against runtime access order.

Flag cases where:

- a world-map description reveals a fact before the reveal scene
- a choice button names a person, item, or location before the player has that knowledge
- a shared route description assumes stronger branch knowledge than the minimum shared knowledge

### Shared-node neutrality

For any shared FLOW, STORY, or world-map node reached by multiple routes:

- inspect each incoming route
- identify the minimum knowledge common to all of them
- make sure the shared node text only assumes that common layer

### Graph-to-runtime contract drift

Flag cases where landed runtime no longer matches the graph-level promise, such as:

- wrong speaker
- wrong location
- shifted consequence
- missing payoff or setup that breaks route logic
- player decision text that no longer matches the routed event

### Route and button integrity

Check:

- choice button wording matches the routed event
- no disabled or missing branch is still advertised in locale copy
- no button implies one destination while routing to another

### Naming consistency

Check chapter-local consistency for:

- named NPCs
- place names
- object labels
- household or shop references

### Emotional acceptance（情感驗收）— whole chapter

Applies whenever the chapter has a beat sheet; without one, state
`NO BEAT SHEET — emotional acceptance not applicable` in the story QA
report.

Across the LANDED chapter (all delivery channels together — cutscenes,
played segments, scenery, copy):

- account for every beat: which landed artifact transmits it, through which
  channel; a beat with no landing anywhere is a blocker
- verify each beat still TRANSMITS after landing: the landed form works as
  a concrete picture, not as an explanation of one
  (`core/NARRATIVE_FOUNDATIONS.md` #1)
- walk the chapter in player order and verify the curve: every HOLD (壓)
  still holds through its whole stretch, the single RELEASE (放) lands
  where the beat sheet put it, and nothing that landed later (an
  achievement pop, a reward toast, a stray line) releases inside a hold
- verify feel-consistency across channels: every touchpoint of the chapter
  delivers the same feel (`core/NARRATIVE_FOUNDATIONS.md` #3) — a channel
  whose tone breaks the chapter's feel is a finding even when its content
  is technically correct

## Required output format

- One saved story QA report.
- One saved prose QA report.
- Each report uses the shared review report template.
- Findings should be ordered by severity and include affected files plus minimal fix direction when needed.
- If no findings are found, say so explicitly and mention residual risks.

## Scope boundary

- This step judges story quality, prose quality, and final chapter locale consistency.
- This step does not replace mechanical landing integrity checks.
- If STEP 6 is still `draft_only`, the QA reports may review design artifacts, but the chapter is not yet playable or landed in runtime data.
