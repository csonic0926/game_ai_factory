# Cutscene Staging

*Turns an approved STEP 6.7 staging plan into a **playable cutscene document**
for the target game's cutscene runtime. Use in CHAPTER STEP 7 (runtime
landing) when the target surface is a scripted cutscene (per the adapter's
`LANDING_SPEC` cutscene surface).*

This craft is **generic**. The concrete document format, beat vocabulary, mark
conventions, and where the file lands are defined by the **target game**, via
`adapters/<project_id>/LANDING_SPEC.md` (the cutscene surface) — read it first
and obey it. The creative staging decision has already happened in STEP 6.7 via
`VISUAL_GRAMMAR.md`; this doc is now the document-conversion discipline that
keeps the landing faithful to that approved plan.

## Inputs

- The approved staging plan (STEP 6.7 output) and `STEP 6.75 PASS` review.
- The approved runtime-draft scene (STEP 6 output) in `<PRIMARY_LOCALE>` for
  wording / meaning reference.
- World + character + knowledge context (`<STORY_ROOT>/state/…`, `<KNOWLEDGE_ROOT>`).
- The adapter's cutscene surface in `LANDING_SPEC.md`: document path, schema
  location, beat vocabulary, mark/actor conventions, locale-key rules, integrity checks.
- The sovereignty files `<STORY_ROOT>/state/WORLD_RULES.md` and
  `<STORY_ROOT>/state/NARRATIVE_DELIVERY.md` (or the legacy
  `WORKFLOW_CORE_VARIABLES.md` where the project has not migrated) — obey
  their constraints (for Vinci World: the **信任媒介 / TRUST_TRANSLATION_MAP**
  rule and the no-real-tech-words rule are highest priority).

## Output

- One cutscene **document** (data, e.g. `.cutscene.json`) at the path the
  LANDING_SPEC names.
- The scene's **dialogue as locale keys** in every shipped locale (same
  EN-source key discipline as any other landing) — the document references keys,
  never inline strings.

## Staging discipline (the craft)

Read the staging plan as binding. Produce the document in this order:

1. **Cast the approved actors.** Map each staged actor to an actor entry (bind
   the player; spawn NPCs). Do not add actors not required by the staging plan.
2. **Name the approved marks, not the coordinates.** Every position an actor
   stands at or the camera looks at becomes a **named mark**, authored once.
   Never scatter raw tile/pixel coordinates through the timeline. Reuse existing
   scene landmarks where the canon has them.
3. **Frame by approved intent.** Use the camera focus, midpoint, frame, zoom,
   follow, fade, and wait operations already listed in the staging plan. Do not
   invent close-ups, wide shots, cuts, or new camera grammar in STEP 7.
4. **Block the approved movement.** Convert staged `walk` / `face` operations
   into runtime beats. Preserve whether movement blocks the timeline or runs
   alongside it (`parallel`) unless the staging plan explicitly leaves that
   open.
5. **Land the approved dialogue.** Each spoken line is a `say` beat referencing a locale
   key. Keep lines short enough for the game's dialogue box (see LANDING_SPEC).
   A line that triggers an action (a choice, an exchange) carries the action.
6. **Punctuate with approved expression.** Use `emote` beats from the staging
   plan. Do not add extra emoji to simulate animation.
7. **Cue approved sound.** Add `sfx` beats named by the staging plan. Produce
   missing clips with **game_ai_factory/sound** (ElevenLabs → de-silence →
   drop-in) and reference the landed asset path.
8. **Compose approved set-pieces from FX.** Reuse named FX the runtime provides;
   do not hand-script animation in the document.
9. **End on the approved transition** if the scene changes scene/room;
   otherwise end cleanly.

If the staging plan is underspecified, impossible to translate, or appears to
need a different camera / actor / pacing decision, stop and route back to
STEP 6.7. Do not fix the design in this craft.

## Trust & canon gates (Vinci World)

- Everything the `TRUST_TRANSLATION_MAP` ruler demands still applies at the
  cutscene layer — a scripted moment is where first-30-min trust is won or lost.
  Ask of each beat: which felt-trust does it deliver / which distrust reflex does
  it risk?
- No real-tech words (blockchain/NFT/上鏈/token/SBT) in any dialogue key.
- Use the decided in-world terms; keep the surface warm, the mystery curiosity-driven.

## Review (STEP 7.5 integrity)

- Document parses; every referenced actor / mark / FX id / locale key resolves.
- Locale key sets identical across all shipped locales; no forbidden real-tech words.
- `walk` targets are reachable; the timeline ends in a transition or a clean stop.
- The scene, played, matches the approved STEP 6.7 staging plan and preserves
  the approved STEP 6 intent (no invented beats that contradict the plan or
  draft).
