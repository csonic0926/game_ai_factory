# LANDING SPEC — vinci_world

Status: AVAILABLE (scoped v0.1 — onboarding surface only)

Vinci World has no general story/event runtime yet. This spec covers the ONE
landing surface that exists today: the new-user onboarding flow. Chapter-scale
work beyond this surface is still BLOCKED_BY_PROFILE.

## Surface 1: new-user onboarding (AVG intro + estate cutscene)

### 1. Target files

- `<GAME_REPO>/client/locales/en.json` (catalog SOURCE of truth)
- `<GAME_REPO>/client/locales/zh-TW.json`
- `<GAME_REPO>/client/locales/ko.json`
All three must stay key-identical. Landing = editing VALUES of existing keys
only. Adding/removing keys requires code changes (declarative arrays in
`client/src/intro/avg.ts` `WELCOME_KEYS` and `client/src/cutscene.ts`
`DIALOGUE_LINES`) — treat as out of scope unless the order explicitly says so.

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

## Landing log

Record every landing under
`<STORY_ROOT>/runtime_scene_drafts/<stem>_LANDING_LOG.md` (keys touched,
term renderings chosen per locale, checks run).
