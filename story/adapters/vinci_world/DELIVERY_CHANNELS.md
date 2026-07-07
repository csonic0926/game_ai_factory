# DELIVERY CHANNELS — vinci_world

Channels declared per the 2026-07-07 rebuild plan (§六), grounded in what
the web client actually runs today. Consumed by the delivery-planner module.

| channel | what it is | status | carries well | carries badly |
|---|---|---|---|---|
| cutscene 文件 | scripted `.cutscene.json` documents played by the client cutscene runtime (`LANDING_SPEC.md` surface 2) | AVAILABLE | staged moments where framing and timing matter: thresholds, rituals, the chapter peak | long stretches of travel (CH1 precedent: pure cutscene ran too long and was re-cut) |
| mission 系統（任務遊玩） | the player walks A point to B point themselves; small played segments (introduced by the CH1 re-cut, 2026-07-05) | AVAILABLE (per CH1 landing; mission definitions live in the game repo) | the player's own pacing and posture: running on the first day, slowing down on the walk home; entering a place with their own feet | precise staging; simultaneous crowd choreography |
| NPC 對話 | villagers speaking to (or near) the player | AVAILABLE inside cutscenes (`say` beats); free-roam ambient dialogue runtime NOT yet available | one line of feel next to a lived picture; directions and everyday warmth (the game's surface is Animal-Crossing-leaning) | explanation of world laws — the underside is never spoken (NARRATIVE_DELIVERY dial) |
| item 文案 | locale-key copy attached to objects the player holds or inspects (e.g. the slip/憑證) | AVAILABLE (i18n key catalogs, EN-source) | quiet second-read depth; what an object means to its owner | time-ordered beats; anything the player must not miss |
| 場景佈置（場景與道具本身） | the scene and its props: where things are, what people are doing, which way goods move | AVAILABLE (needs per-scene art/layout work in the game repo) | place-first beats: sealed crates riding the same boat, crowd around a notice board — visible, never explained | anything requiring interiority; precise verbal content |
| 佈告欄 | the in-world notice board with readable postings | PLANNED (board exists as scenery; readable-posting runtime missing) | the "box count, never contents" hold beat — official, terse, public | warmth; personal voice |
| 成就文案 | achievement titles/descriptions (the achievement system is canon) | AVAILABLE (locale keys) | naming a milestone AFTER it happened (first crossing, first turn) | building anticipation — an achievement fires as release, it cannot hold |
