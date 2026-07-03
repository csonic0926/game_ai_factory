# Cutscene Staging

*Turns an approved scene (dialogue + prose beats) into a **playable cutscene document** for the target game's cutscene runtime — the bridge that lets the story factory PRODUCE cutscenes, not just text. Use in CHAPTER STEP 7 (runtime landing) when the target surface is a scripted cutscene (per the adapter's `LANDING_SPEC` cutscene surface).*

This craft is **generic**. The concrete document format, beat vocabulary, mark
conventions, and where the file lands are defined by the **target game**, via
`adapters/<project_id>/LANDING_SPEC.md` (the cutscene surface) — read it first
and obey it. This doc teaches the *staging discipline* that applies to any such
runtime.

## Inputs

- The approved runtime-draft scene (STEP 6 output) in `<PRIMARY_LOCALE>`.
- World + character + knowledge context (`<STORY_ROOT>/state/…`, `<KNOWLEDGE_ROOT>`).
- The adapter's cutscene surface in `LANDING_SPEC.md`: document path, schema
  location, beat vocabulary, mark/actor conventions, locale-key rules, integrity checks.
- `<STORY_ROOT>/state/WORKFLOW_CORE_VARIABLES.md` — obey its constraints
  (for Vinci World: the **信任媒介 / TRUST_TRANSLATION_MAP** rule and the
  no-real-tech-words rule are highest priority).

## Output

- One cutscene **document** (data, e.g. `.cutscene.json`) at the path the
  LANDING_SPEC names.
- The scene's **dialogue as locale keys** in every shipped locale (same
  EN-source key discipline as any other landing) — the document references keys,
  never inline strings.

## Staging discipline (the craft)

Read the scene as a director, not a typist. Produce the document in this order:

1. **Cast the actors.** Who is on screen? Map each to an actor entry (bind the
   player; spawn NPCs). Only stage who the beat needs — hide the rest.
2. **Name the marks, not the coordinates.** Every position an actor stands at or
   the camera looks at becomes a **named mark**, authored once. Never scatter raw
   tile/pixel coordinates through the timeline — that is exactly the pain this
   system removes. Reuse existing scene landmarks where the canon has them.
3. **Frame by intent.** Choose camera focus semantically — "on the speaker", "the
   midpoint between the two", "frame both" — and let the runtime resolve the math.
   Only pin a raw position when the shot genuinely demands one.
4. **Block the movement.** Turn stage directions into `walk` / `face` beats.
   Decide what blocks the timeline vs. what runs alongside it (`parallel`).
5. **Land the dialogue.** Each spoken line is a `say` beat referencing a locale
   key. Keep lines short enough for the game's dialogue box (see LANDING_SPEC).
   A line that triggers an action (a choice, an exchange) carries the action.
6. **Punctuate with expression.** Use `emote` beats (bubble + emoji) for reactions
   — this is the cutscene expression layer in place of per-character pose art.
   Run an emote alongside a line via `parallel` when the reaction lands during
   speech.
7. **Cue the sound.** Add `sfx` beats where the scene needs a cue (impact, door,
   item-get, whoosh). Produce the actual clips with **game_ai_factory/sound**
   (ElevenLabs → de-silence → drop-in) and reference the landed asset path.
8. **Compose set-pieces from FX.** Reuse named FX (e.g. `item_exchange`) the
   runtime provides; do not hand-script animation in the document.
9. **End on a transition** if the scene changes scene/room; otherwise end cleanly.

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
- The scene, played, matches the approved STEP 6 intent (no invented beats that
  contradict the draft).
