# LANDING SPEC — vinci_world

Status: AVAILABLE (v0.2 — onboarding locale keys + scripted cutscenes)

Vinci World now has a **data-driven cutscene runtime** (`client/src/cutscene/`;
see `<GAME_REPO>/docs/CUTSCENE_TOOL_SPEC.md`). This spec covers two landing
surfaces: **Surface 1** — onboarding locale-key values; **Surface 2** — scripted
cutscenes as `.cutscene.json` documents (this is what lifts CHAPTER STEP 7 for
scripted scenes). Chapter scenes that are NOT scripted cutscenes (free-roam /
interactive gameplay) remain BLOCKED_BY_PROFILE until a general event runtime exists.

## Surface 1: new-user onboarding (AVG intro + estate cutscene)

### 1. Target files

- `<GAME_REPO>/client/locales/en.json` (catalog SOURCE of truth)
- `<GAME_REPO>/client/locales/zh-TW.json`
- `<GAME_REPO>/client/locales/ko.json`
All three must stay key-identical. Landing = editing VALUES of existing keys
only. Adding/removing keys requires code changes (`client/src/intro/avg.ts`
`WELCOME_KEYS` for the AVG act; the in-village onboarding cutscene is now a
Surface 2 document — `client/src/cutscene/documents/onboarding.cutscene.json`).

### 2. Key inventory (this surface)

AVG white-screen act (`client/src/intro/avg.ts`):
- `avg.dialogue.welcome`, `avg.dialogue.intro`, `avg.dialogue.pick` (3 typewriter lines, click-to-advance)
- `avg.dialogue.choose` (selection instruction line)
- `avg.confirm` (button)
- `avg.dialogue.seeYou` (parting line)

In-village cutscene (`client/src/cutscene.ts`):
- `cutscene.speaker.estateAgent` (speaker label)
- `cutscene.dialogue.welcome`, `.badgeNotice`, `.badgeExchange`, `.tradeOffer`, `.success`
- `cutscene.exchange`, `cutscene.receiveKey` (buttons)

### 3. Granularity rules

- One key = one typewriter line = one click. Keep lines short (typewriter,
  small dialogue box; aim ≤ ~90 chars zh / ~140 chars en per line).
- `cutscene.dialogue.tradeOffer` carries the ONE interactive beat
  (`action: "exchange"`); exactly one action beat exists — do not move or
  duplicate it. `.success` may contain one `\n`.

### 4. Choice & routing encoding

None. The flow is linear; the only interaction is the exchange button.

### 5. Locale landing

- Author in `<PRIMARY_LOCALE>` zh-TW; en is the catalog source language and
  must read as native copy (not translationese); ko follows.
- All three locales land together in the same change; keys must remain
  identical across files (the i18n system is EN-source key catalogs).

### 6. Integrity checklist

- `node -e "['en','zh-TW','ko'].every(...)"`-style check or jq: all three
  catalogs parse and have identical key sets (at minimum: unchanged key sets).
- Grep changed values for forbidden real-tech words (SBT/NFT/區塊鏈/上鏈/
  blockchain/token) — must be zero.
- Decided world terms used correctly: 投影/收藏家/原件/彼端/點數 (zh);
  their en/ko renderings must be consistent within the surface and recorded
  in the landing log for future reuse.
- Manual smoke: `?force_intro` URL param replays onboarding for verification.

### 7. Battle/minigame hooks

NOT_AVAILABLE.

## Surface 2: scripted cutscenes (.cutscene.json)

Vinci World plays cutscenes from declarative documents via the runtime in
`client/src/cutscene/`. Producing a cutscene = authoring/patching a document +
its dialogue locale keys. Use `core/craft/cutscene-staging.md`.

**USER approval gate (standing rule, 2026-07-04):** the STEP 6 zh-TW draft
must be read and approved by the USER before STEP 7 landing begins on this
surface. No exceptions — the USER is the taste gate for every chapter script.
The draft form is the screenplay format defined in this adapter's
`STYLE_GUIDE.md` §3.

### 1. Target files

- Document: `<GAME_REPO>/client/src/cutscene/documents/<id>.cutscene.json`
- Dialogue keys: the three EN-source locale catalogs (as Surface 1).
- Schema + beat vocabulary (authoritative — read before authoring):
  `<GAME_REPO>/client/src/cutscene/types.ts`, `<GAME_REPO>/docs/CUTSCENE_TOOL_SPEC.md`.

### 2. Document shape

`{ id, scene, config{seed,typewriterMs}, onEnter[], marks{}, actors{}, timeline[] }`
- **marks** = named tile positions `[col,row]`; author once, reference everywhere —
  never scatter raw coordinates through the timeline.
- **actors** = bind `"player"` or spawn an NPC, placed at a mark.
- **timeline** = ordered beats.

### 3. Beat vocabulary

`camera` (focus: tile/mark/actor/midpoint/frame + zoom/ms/follow), `walk`
(await?), `face`, `say` (speaker+text locale keys; optional `action`), `wait`,
`fade`, `emote` (bubble+emoji expression), `sfx` (cue — produce clips with
`game_ai_factory/sound`), `fx` (named set-pieces, e.g. `item_exchange`),
`transition` (enterHouse), `parallel`, `sequence`. Frame by intent, not raw
coordinates; concurrency via `parallel`.

### 4. Choice & routing encoding

A `say` beat may carry `action:{key}` for one interactive button. Branch
SELECTION stays at the factory event-graph level; one document is one linear
staged beat-list.

### 5. Locale landing

Same as Surface 1: dialogue referenced by key, authored zh-TW, en native, ko
follows, all locales land together, key sets identical.

### 6. Integrity checklist

- Document JSON parses; every referenced actor / mark / FX id resolves; every
  `say`/action locale key exists in all three catalogs with identical key sets.
- No forbidden real-tech words (SBT/NFT/區塊鏈/上鏈/blockchain/token) in dialogue.
- Decided world terms correct (投影/收藏家/原件/彼端/點數).
- `walk` targets reachable (walkability); timeline ends in a transition or clean stop.
- Trust ruler passed (WORKFLOW_CORE_VARIABLES 信任媒介 / TRUST_TRANSLATION_MAP).
- Smoke: `?force_intro` (onboarding) or the preview harness for other scenes.

### 7. Battle/minigame hooks

NOT_AVAILABLE.

## Landing log

Record every landing under
`<STORY_ROOT>/runtime_scene_drafts/<stem>_LANDING_LOG.md` (keys touched,
term renderings chosen per locale, checks run).
