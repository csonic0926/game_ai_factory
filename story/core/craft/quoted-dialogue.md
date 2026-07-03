# Quoted Dialogue

*Rewrites only quoted spoken lines so they sound like people speaking in the current setting and pressure, with one clear pragmatic function and the same intent across `<PRIMARY_LOCALE>` and all `<SHIPPED_LOCALES>`. Use when a quoted line sounds written, archaic, authored, or over-expository.*

Use this doc when:

- a quoted line inside `「…」` or `"..."` sounds too literary, too archaic, too authored, or too unlike speech
- a line needs sharper speaker identity
- a line is carrying too much exposition
- a line needs `<PRIMARY_LOCALE>` / `<SHIPPED_LOCALES>` alignment at the spoken-action level

This doc handles **quoted dialogue only**.
It should not rewrite narration outside quotation marks.

## Goal

Write dialogue that sounds like:

- a person speaking now
- in this situation
- under this pressure
- in this world

The line should perform one clear social action on-screen.

## Core principle

Dialogue is not a lore paragraph and not an author verdict.

Quoted speech should primarily do one of these:

- ask
- answer
- warn
- push
- refuse
- confirm
- redirect
- test the other person

## Hard rules

### 1) Speakable first

- If a human actor could not say it naturally in one breath or two short breaths, rewrite it.
- Prefer spoken rhythm over elegant sentence architecture.
- Do not let the line read like a written notice.
- Do not over-optimize into clipped slogan-like lines either.
- Spoken language can have a small lead-in, a turn, or a trailing push if it still sounds natural.

### 2) No built-in archaic flavor

- Do not default to old-timey, classical, or faux-wuxia phrasing.
- Do not add period flavor unless the world, faction, education level, or speaker role specifically supports it.
- Neutral spoken `<PRIMARY_LOCALE>` is the baseline.

Examples to avoid by default (example for a zh-TW/en/ja project — Chinese-specific archaic markers):

- `若……`
- `且……`
- `休要……`
- `速去……`
- overly compressed threat or command structures that sound stylized rather than spoken

### 3) One dominant pragmatic move per line

- One line should mainly do one thing.
- A small follow-through phrase is fine if it sounds like natural speech.
- If the speaker must warn and instruct, either make one clearly primary or split into two quoted lines.
- Do not make every line so function-pure that it stops sounding like someone talking.

### 4) Do not hide narration inside dialogue

Avoid lines whose real job is:

- explaining backstory
- summarizing the plot
- naming the theme
- translating scene logic for the player

If the line is only there to explain the scene, move that work back to narration or scene structure.

### 5) Match the speaker, not the template

The line should reflect:

- speaker role
- education level
- social position
- urgency
- relationship to the listener

Do not use one generic "dramatic dialogue" template for everyone.

### 5.5) Spoken ease matters

- Leave room for hesitation, emphasis, irritation, or habit when those belong to the speaker.
- Not every line needs to sound neat.
- A slightly messy spoken line is often better than a perfectly balanced written line.

### 6) World flavor comes from the world, not from automatic stylization

If the setting is:

- magic academy
- wuxia city
- industrial district
- frontier settlement

the dialogue should pick up concrete vocabulary from that setting.
But the line should still sound like speech, not genre cosplay.

### 7) Reader knowledge and character knowledge are separate

- A speaker may know more than the reader.
- Let the line preserve that asymmetry when needed.
- Do not over-explain just to make the line self-sufficient.

### 8) First appearance dialogue should help place the speaker

If this is the audience's first meaningful exposure to the speaker:

- the line should help the reader place what kind of person this is
- but do not turn the line into self-introduction boilerplate

## Dialogue design workflow

For each quoted line:

1. identify the speaker
2. identify the listener
3. identify the immediate pressure
4. identify the line's main pragmatic move
5. write the shortest natural spoken line that performs that move
6. align `<PRIMARY_LOCALE>` and all `<SHIPPED_LOCALES>` to the same move and force

Do not confuse "shortest" with "most compressed."
If the shortest version sounds stiff, allow a slightly looser spoken version.

## Natural spoken baseline (example for a zh-TW primary locale — Chinese language craft)

Default baseline for zh:

- modern readable spoken Chinese
- concise but not clipped into fragments
- direct enough to sound spoken
- no decorative ancientness unless justified by character/world input
- allow light spoken looseness when it improves human rhythm

Prefer lines that sound like a person opening their mouth in the moment,
not like a subtitle writer trying to sound efficient.

Over lines that feel artificially old or theatrical.

## Checks for "too archaic"

Rewrite if the line feels like:

- a costume drama subtitle
- a proclamation
- a proverb
- an author-crafted "period" line rather than something someone would actually say here

## Multi-language alignment

- `<PRIMARY_LOCALE>` and all `<SHIPPED_LOCALES>` must preserve the same pragmatic move
- do not let one language become more explanatory than the others
- do not make `<PRIMARY_LOCALE>` overly stylized while the other locales stay plain (e.g., for a zh-TW/en/ja project: do not make zh overly stylized while en/ja stay plain)

## Self-check before output

- Does this sound spoken, not written?
- Is the line doing one clear social action?
- Is it too neat or too compressed to sound human?
- Is it too archaic for the current world and speaker?
- Did it smuggle narration or plot explanation into speech?
- Could a different speaker say this unchanged? If yes, sharpen the voice.
- Do `<PRIMARY_LOCALE>` and all `<SHIPPED_LOCALES>` still perform the same move?

If any answer is bad, rewrite the line.
