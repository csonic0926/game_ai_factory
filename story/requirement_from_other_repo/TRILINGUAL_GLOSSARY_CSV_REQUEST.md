# Cross-repo factory request — 三語 glossary CSV＋使用規則（termbase for story production）

> Historical authority model: this completed request records the original
> two-source design. It was superseded on 2026-07-17 by
> `GLOSSARY_SINGLE_SOURCE_AUDIT_REQUEST.md`; `GLOSSARY.csv` is now the sole
> canonical source for proprietary terms.

## Request metadata

- Status: done（2026-07-17 factory＋vinci_world bootstrap 完成，見文末 completion notes）
- Date: 2026-07-17
- Source repo: vinci_world (game repo, factory caller)
- Source repo path: /Users/hunglingki/git_projects/web_projects/vinci_world
- Request owner: USER（2026-07-17 對談定案：「現在 story factory 未有一張
  近似翻譯時常用的 glossary csv，也沒有使用這張 glossary csv 的規則——
  這得做」）
- Factory target area: docs (PROJECT_PROFILE_CONTRACT) | adapters/_template |
  core/craft（spoken-fluency、quoted-dialogue、dialogue-runway）|
  core/steps/chapter（STEP 6/6.5/7/8/8.5）| skills/game-story-factory |
  scripts（新 checker）
- Priority: high（en/ko 對白生產已實際發生漂移風險；淨室派工的保護詞
  目前靠 orchestrator 每次手挑）

## User-facing need

故事產線的用詞管理現況是一個**四層防禦系統**：主權詞表
（`<STORY_ROOT>/state/WORLD_RULES.md` §用詞表，九條，USER 拍板帶出處）→
seeds `fact_terms` 傳播 → `style_lint_config.json` 執法（whitelist／jargon／
code_patterns，管設計行文）→ 判例庫兜底（§4.1.1，實際上已在承載詞級
口味）。它很會凍結和禁止，但有五個實測撞出來的缺口：

1. **沒有入籍程序**：「分身」（USER 口語）、「款」（worker 母語直覺）、
   「這一側 vs 這一邊」（shipped 文本 vs 自然口語）——每個新詞候選都變成
   ad-hoc 旗標掛著等 USER，沒有「提名 → 拍板 → 入表帶出處」的固定路。
2. **單語域**：詞表每個指涉物只登正式詞；對白需要的語域變體（設計叫
   「原件／藏品」、村民嘴裡是「寶貝／心頭好」）與「誰的嘴可以講哪個」
   只隱含在 shipped 台詞裡。
3. **三語對應無家**：彼端＝the far side＝저편、搖＝a turn——這些實質的
   term 決定只活在 shipped locale 字串裡；寫 en/ko 的 worker 得去 locale
   檔逆向工程（2026-07-13 的 quoted-dialogue worker 實際就這樣做），
   換一個 worker 就可能寫出 "the other side"。
4. **小詞無家**：量詞（數化身用「款」）、動詞慣例（gacha 動作用「搖」
   避用「抽」——主權表已登，但 en/ko 的 "a turn" 對應無機器可讀的家）
   現在寄居在判例庫，而判例庫管「怎麼說話」不管「用什麼詞」。
5. **對白層執法靠手工**：淨室重寫派工時保護哪些詞是 orchestrator 每次
   手挑的清單；canon 回驗閘驗詞也是人工比對。

USER 定案方向：**做一張翻譯業 termbase 式的 glossary CSV＋一套「誰在
什麼時候必須讀它」的使用規則。** 沿用既有分工：factory 出題（CSV schema
＋使用規則＝契約），game repo 交卷（填好的 glossary＝答卷檔，住
`<STORY_ROOT>/adapter/`，隨遊戲版本化）；詞的主權不動——canon 狀態的
變更只能來自 USER，主權詞表（WORLD_RULES）與 glossary 衝突時主權表贏。

## Factory-side change requested

### 1. 契約：定義 `GLOSSARY.csv` 為 adapter 答卷檔之一

`docs/PROJECT_PROFILE_CONTRACT.md` 答卷檔清單加入 `GLOSSARY.csv`；
`adapters/_template/` 加空白模板。Schema（欄位名可由 factory 定案，
語義要齊）：

| 欄 | 語義 |
|---|---|
| `term_id` | 穩定鍵（snake_case，供腳本與引用） |
| `zh_TW` | 主形（創作語言） |
| `en` | en 對應（EN-source catalog 的權威拼法） |
| `ko` | ko 對應 |
| `referent` | 指涉什麼，一句白話 |
| `register` | 語域：`formal`（canon 正式詞）／`folk`（街頭講法）／`both` |
| `variant_of` | 語域變體指回正典行的 `term_id`（正典行留空） |
| `speaker_scope` | 誰的嘴：`all`／`villagers`／具名角色 id／`design_only`（只進設計行文不進對白） |
| `dialogue_protected` | `true`＝對白中不得被同義替換（淨室派工的保護詞直接由此欄機械抽取） |
| `status` | `canon`／`pending`（候選待 USER 拍板）／`banned`／`deprecated` |
| `provenance` | 出處（USER 拍板日期／shipped commit／判例編號） |
| `notes` | 量詞、搭配、避用詞等（例：搖——避用「抽/pull/draw」；款——數化身款式） |

格式：UTF-8、逗號分隔、標準 quoting、一行一詞形（變體各自成行）。
機器可讀是硬要求——閘門與派工腳本要直接吃它。

### 2. 使用規則（「誰在什麼時候必須讀它」——落到既有文件）

1. **凡產出引號台詞的步驟與工藝**（chapter STEP 6、STEP 8、
   `dialogue-runway`、`quoted-dialogue`）：動工前讀 glossary；
   `dialogue_protected` 詞照登記形使用；`speaker_scope` 與 `register`
   約束角色嘴裡的變體；en/ko 生產以 glossary 為三語權威對應，
   **不再從 shipped locale 檔逆向工程**。
2. **spoken-fluency 淨室模式**：派工時的保護詞清單改為**從 glossary 機械
   抽取**（該場景語言的 `dialogue_protected=true` 行），取代 orchestrator
   手挑；世界事實仍以人話一句進淨室（淨室不讀 CSV 本體，讀的是抽取後
   的人話清單——語域紀律不變）。
3. **Canon 回驗閘**：對照 glossary 機械 diff——保護詞在場且未被替換、
   `banned` 詞零出現、en/ko 對應與登記一致。
4. **`.5` 閘**：新產物若出現未登記的世界詞彙（新名詞、新量詞慣例、
   新語域變體），不是 FAIL——是要求提名：以 `status=pending` 列入
   glossary（或報告列明候選），留給 USER 拍板。閘門驗「有沒有漏提名」。
5. **入籍協定**：`pending` → `canon`／`banned` 的狀態變更**只能由 USER
   拍板**（answer 檔在 game repo，工具可以新增 pending 行、不可自行
   升格）；升格時 `provenance` 記 USER 拍板日期。若該詞屬世界內用語，
   同步提醒 USER 在主權詞表（WORLD_RULES §用詞表）補一行——主權表是
   源，glossary 是營運投影，衝突時主權表贏。
6. **解析與缺席行為**：glossary 缺席＝`NOT_AVAILABLE`，一切照現行行為
   （rpg-1 等未遷專案零影響）；存在即約束生效。

### 3. Checker 腳本

`scripts/glossary_check.py`（比照 `style_lint.py` 的定位）：輸入 artifact
＋glossary，機械檢查——`banned` 詞出現即報；引號內台詞若含
`dialogue_protected` 詞的常見同義替換（可先做精確詞比對版，同義偵測
留人工）；locale 檔模式下驗 en/ko 對應與 glossary 一致。閘門在
`.5` 檢核清單引用它。

### 4. vinci_world bootstrap（首次交卷，比照 adapter 搬家先例由 factory 側代辦）

在 `<GAME_REPO>/design/story/adapter/GLOSSARY.csv` 建首版：

- **九條主權詞**（WORLD_RULES §用詞表原文照登，provenance 抄決策來源）
  ＋自 shipped locale 檔註冊 en/ko 對應（`client/locales/en.json`／
  `ko.json`——例：彼端＝the far side＝저편；憑證＝slip；搖＝a turn。
  en/ko 對應登記後標 `canon`，但在報告中列明「三語對應為 shipped 事實
  的註冊，USER 未逐條覆核」）。
- **排隊中的候選**以 `status=pending` 入列（全部出自 2026-07-13～17 的
  實測旗標）：分身 vs 模樣（玩家化身的稱呼）、這一側 vs 這一邊、
  款（數化身的量詞）、寶貝／心頭好（原件的街頭語域變體，
  `speaker_scope` 建議 villagers/all 待 USER）、化成 vs 變成（投影的
  動詞搭配）。
- `banned` 行：現實技術詞（區塊鏈、NFT、token、SBT、上鏈——來源
  `design/TRUST_TRANSLATION_MAP.md`）。

## References and source context

- 主權詞表：`<GAME_REPO>/design/story/state/WORLD_RULES.md` §用詞表
  （九條，USER 拍板帶出處；「搖／a turn」條目是入籍格式的最好範本）
- 現行執法：`<GAME_REPO>/design/story/adapter/style_lint_config.json`
  （whitelist／jargon／code_patterns——管設計行文，與本案分工見 Non-goals）
- 三語事實來源：`<GAME_REPO>/client/locales/{en,zh-TW,ko}.json`
- 實測缺口記錄：本 repo `SPOKEN_FLUENCY_PASS_REQUEST.md`（判例庫承載
  詞級口味的現況）；vinci_world `design/story/adapter/STYLE_GUIDE.md`
  §4.1.1 用詞旗標（分身/模樣 pending 的原始記錄）
- 分工先例：`ADAPTER_FILES_MOVE_TO_GAME_REPO_REQUEST.md`（factory 出題、
  game repo 交卷；bootstrap 由 factory 側代辦的先例）

## Acceptance criteria

- [x] CONTRACT 定義 `GLOSSARY.csv` schema＋`_template/` 空白模板；答卷檔
      清單與 canonical STORY_ROOT layout 更新。
- [x] 使用規則落到位：STEP 6/8 步驟文件、`dialogue-runway`／
      `quoted-dialogue`／`spoken-fluency`（淨室保護詞機械抽取）、
      6.5/8.5 閘（未登記詞→提名不 FAIL）、SKILL.md orchestrator 派工
      規則各一段；缺席＝NOT_AVAILABLE 照舊。
- [x] `scripts/glossary_check.py` 存在且以 vinci_world glossary 實跑一次
      （對任一近期對白 artifact）。
- [x] vinci_world `design/story/adapter/GLOSSARY.csv` 首版落地：九條主權
      詞（含 shipped en/ko 註冊）＋五組 pending 候選＋banned 行；CSV 可
      被 checker 解析。
- [x] 主權不動：工具只能新增 `pending` 行；`canon`／`banned` 升格僅 USER；
      WORLD_RULES 衝突時勝出——此三條寫進契約與使用規則。
- [x] rpg-1 未遷專案零影響（無 glossary → 行為不變）。

## Non-goals / do-not-change

- 不合併 `style_lint_config.json`——jargon／code_patterns 管**設計行文
  衛生**，glossary 管**世界語彙**；兩套各司其職（日後 whitelist 是否改由
  glossary 生成，另案）。
- 不回頭改寫任何 shipped locale 字串（登記現狀，不改現狀）。
- 不做同義詞自動偵測的 NLP——checker 先做精確比對，語感層留給閘門
  worker 與 USER 耳朵。
- 不替 USER 裁決任何 pending 行（bootstrap 只列隊，不拍板）。
- 判例庫（STYLE_GUIDE §4.1.1）職責不變——它管句子怎麼說（品質教學），
  glossary 管詞用哪個（詞彙登記）；判例中的詞級結論（如「款」）由
  glossary 承接後，判例本身仍留作語感錨。


## Completion notes（factory 側＋vinci_world bootstrap，2026-07-17）

1. **契約與答卷模板**：`docs/PROJECT_PROFILE_CONTRACT.md` 已把
   `GLOSSARY.csv` 加入 canonical adapter 答卷檔，寫明精確 header、UTF-8
   CSV、一行一詞形、欄位 enum、缺 locale 對應時的行為、六個必讀 consumer、
   缺席＝`NOT_AVAILABLE`。`adapters/_template/GLOSSARY.csv` 是只有 header 的
   空白答卷；`init_story_root.sh` 不需特判，既有 `_template/*` 播種迴圈會自動
   複製，已用臨時 STORY_ROOT 實跑確認。
2. **主權與入籍**：契約、step、craft、orchestrator 均明文固定：
   `WORLD_RULES.md` 是源且衝突時勝；工具只可把新觀察新增為 `pending`；
   pending 升 `canon`／`banned` 與既有 canon/banned 變更只能由 USER 裁決；
   世界詞升格時提醒同步主權詞表。`.5` gate 遇到新名詞／量詞慣例／語域
   變體只要求提名或在 review 點名，不因「新」本身 FAIL，且 gate 不改檔。
3. **接線**：chapter STEP 6／7／8、6.5／8.5，`dialogue-runway`、
   `quoted-dialogue`、`spoken-fluency`、craft catalog，以及
   `skills/game-story-factory/SKILL.md` 全部已接上。淨室 worker 不讀 CSV；
   orchestrator 先機械抽出該語言的 protected/banned 人話清單，canon-aware
   back-check 才讀 CSV、跑 checker、驗 register/speaker scope。
4. **Checker**：新增可執行的 `scripts/glossary_check.py`。它驗 schema／enum／
   variant reference，掃 exact banned/deprecated/pending，支援
   `--extract-cleanroom <LOCALE> <artifact>` 的淨室人話清單、
   `--baseline BEFORE AFTER` 的 protected-term 計數差，以及重複
   `--locale LOCALE=PATH` 的 aligned JSON catalog 比對。它刻意不猜同義詞、
   不用 NLP 猜新世界詞，兩者留給 gate／USER。臨時 fixture 已驗：pass、
   banned＋protected drop fail、三語 aligned locale pass 三路皆符合預期。
5. **vinci_world 首版答卷**：
   `design/story/adapter/GLOSSARY.csv` 共 25 行資料：11 行 canon（主權表九個
   條目；「渡口／渡進／渡回」依一行一詞形拆成三行）、9 行 pending（五組
   候選拆成各詞形）、5 行 banned。`PROJECT_PROFILE.md` 已標 AVAILABLE。
   已有 aligned shipped 證據的對應以 commit 登記（例如投影、收藏家、原件、
   彼端＝the far side＝저편、憑證＝slip＝증표、迎新、搖）；這些三語對應是
   **shipped 事實的營運註冊，USER 未逐條覆核**。點數的 ko 與
   渡口／渡進／渡回的 en/ko 沒有 aligned shipped 用例，刻意留空並讓
   checker 警告；沒有為了填滿表格而替 USER 發明權威翻譯。
6. **實跑**：checker 對近期正式淨室對白 artifact
   `GATE_KPI_DIALOGUE_RUNWAYS_SKYDIVE_CLEANROOM_FINAL.md` 實跑為
   `PASS errors=0`（列出 8 類 pending 用詞命中與 4 個缺 locale mapping
   warning）。全量 locale mode 另如實抓出 15 個**既有**差異／禁詞命中，
   包含舊 `the other side`、語法活用造成的 exact mismatch，以及產品 UI 既有
   SBT/on-chain/token 字樣；依本案 non-goal 沒有回寫任何 shipped locale。
7. **相容性**：`story/adapters/rpg-1/GLOSSARY.csv` 不存在，解析結果為
   `NOT_AVAILABLE`；既有流程與檔案零變動。
