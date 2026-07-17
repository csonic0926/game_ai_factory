# Cross-repo factory request — audit：GLOSSARY.csv 是否被正確視為專有用詞的唯一 source

## Request metadata

- Status: done（2026-07-17 factory 全庫審計完成，見文末 completion report）
- Date: 2026-07-17
- Source repo: vinci_world (game repo, factory caller)
- Source repo path: /Users/hunglingki/git_projects/web_projects/vinci_world
- Request owner: USER（2026-07-17 定案：terms 單一家——glossary CSV 為
  專有用詞唯一 source；並指示「請 factory check 一下是否正確地把 glossary
  視為唯一的專有用詞 source」）
- Factory target area: 全庫審計——docs (PROJECT_PROFILE_CONTRACT) |
  core/steps | core/craft | skills/game-story-factory | scripts | README/AGENTS
- Priority: high（權威模型剛翻新，殘留的舊表述會讓 worker 讀到兩個互相
  矛盾的詞權威）

## User-facing need

TRILINGUAL_GLOSSARY_CSV_REQUEST（同目錄，status: done）落地時的權威模型是
**兩個家**：`WORLD_RULES.md` §用詞表為源、glossary 為營運投影、「衝突時
主權表贏」。2026-07-17 USER 進一步定案改為**單一家**：

> **`<STORY_ROOT>/adapter/GLOSSARY.csv` 是專有用詞（proprietary terms）的
> 唯一正典 source。** 主權不再靠「詞條住在 USER 親筆檔裡」保障，改靠
> 程序規則：工具只能新增 `pending` 行；`canon`／`banned` 的升格與變更
> 只能由 USER 拍板，每筆帶 provenance。USER 親筆檔（WORLD_RULES 一類）
> 保留的是**用詞哲學**（不發明詞彙、技術詞紀律的因果），不再承載詞條。

Game repo 側已完成遷移（2026-07-17，USER 令代筆）：WORLD_RULES §用詞表
換成路標＋哲學；seeds `fact_terms` 改指 CSV；STYLE_GUIDE §2 白名單降格為
「lint 放行清單、非詞表」。

本需求＝請 factory 側做一次**全庫審計**：找出並修正所有仍把詞權威指向
glossary 以外之處的表述。

## Factory-side change requested（audit 清單）

1. **契約**（`docs/PROJECT_PROFILE_CONTRACT.md`）：上一案寫入的
   「WORLD_RULES 是源、衝突時主權表贏」條款改為單一家表述——glossary 為
   唯一詞 source；sovereignty＝USER-only 狀態變更；主權檔載哲學不載詞條。
   缺席行為不變（無 glossary＝NOT_AVAILABLE、legacy 專案照舊）。
2. **步驟與工藝文件**（STEP 6/6.5/7/8/8.5、`dialogue-runway`、
   `quoted-dialogue`、`spoken-fluency`、craft README）：grep 所有指向
   「主權詞表／WORLD_RULES 用詞表／decided terms 表」的讀取指示與衝突
   裁決語句，統一改指 glossary；「主權檔只讀」的紀律不變（它仍是哲學與
   世界真實的權威，只是不再是詞條的家）。
3. **Orchestrator**（`skills/game-story-factory/SKILL.md`）：同上 sweep；
   特別檢查 dispatch recipe 與 chapter hard bindings 裡的詞權威表述。
4. **Checker**（`scripts/glossary_check.py`）：確認沒有任何邏輯假設存在
   第二個詞 source（例如回退去讀主權表）；缺 glossary 時的 NOT_AVAILABLE
   行為維持。
5. **殘留表述掃描**：story/README.md、AGENTS.md、
   `requirement_from_other_repo/TRILINGUAL_GLOSSARY_CSV_REQUEST.md` 以外
   的說明文件——凡描述詞權威的句子一律對齊單一家模型（歷史檔案如
   completion notes 屬紀錄，不改寫，但可加一行「權威模型已於本案更新」
   的指標）。
6. **報告**：列出審計掃過的檔案清單、每處修正的 before/after 一行、
   以及「確認無第二權威殘留」的 grep 證據（例如「衝突時主權表贏」
  「WORLD_RULES §用詞表」在 factory 庫內的殘留筆數＝0 或僅存於歷史紀錄）。

## References and source context

- 前案：`TRILINGUAL_GLOSSARY_CSV_REQUEST.md`（done；其中「主權表是源」
  條款即本案要翻新的對象）
- Game repo 已遷移的三處（審計時可對照）：
  `<GAME_REPO>/design/story/state/WORLD_RULES.md`（§用詞哲學＋路標，
  USER 令代筆、待覆核）、`<GAME_REPO>/design/story/story_world/seeds/facts.json`
  （`fact_terms`）、`<GAME_REPO>/design/story/adapter/STYLE_GUIDE.md` §2
- 現行 glossary：`<GAME_REPO>/design/story/adapter/GLOSSARY.csv`
  （2026-07-17 已含 USER 第一輪拍板全量：實物、傳送、分身、收藏品、
  SBT、rip 等）

## Acceptance criteria

- [x] 契約的權威模型條款改為單一家（glossary 唯一 source＋USER-only
      升格＋主權檔載哲學）。
- [x] step／craft／SKILL.md 全 sweep：無任何指示讓 worker 把 WORLD_RULES
      （或其他檔）當詞條權威讀取；「主權檔只讀」紀律保留。
- [x] checker 無第二 source 假設；NOT_AVAILABLE 行為不變。
- [x] 審計報告：檔案清單＋逐處 before/after＋殘留筆數證據。
- [x] rpg-1 等 legacy 專案（無 glossary）行為零變動。

## Non-goals / do-not-change

- 不動 game repo 側任何檔案（已由 caller 遷移完成）。
- 不放寬「工具只能新增 pending、升格僅 USER」的程序主權。
- 不改歷史紀錄類文件的既有內文（completion notes 等），只加指標。
- 不在本案內處理 vinci_world 的 shipped 遷移批（模樣／這一側／渡系／
  slip→SBT 等，另案）。


## Completion report（factory 側全庫審計，2026-07-17）

### 掃描範圍與檔案清單

以 `rg --files story` 的 120 個檔案為全集（114 Markdown、3 Python、
1 shell、1 CSV、1 JSON）掃描 term authority／glossary／WORLD_RULES／
decided terms／用詞表等表述；再逐一閱讀所有命中的生產契約、step、craft、
orchestrator、template、module、script 與 README/AGENTS 上下文。

本案有內容修正的檔案：

1. `docs/PROJECT_PROFILE_CONTRACT.md`
2. `skills/game-story-factory/SKILL.md`
3. `README.md`
4. `adapters/_template/PROJECT_PROFILE.md`
5. `core/schemas/templates/WORLD_RULES.template.md`
6. `core/schemas/templates/WORKFLOW_CORE_VARIABLES.template.md`
7. `modules/world-rules-editor/README.md`
8. `core/steps/chapter/STEP_6_RUNTIME_DRAFT.md`
9. `core/steps/chapter/STEP_6_5_RUNTIME_DRAFT_REVIEW.md`
10. `core/steps/chapter/STEP_7_RUNTIME_LANDING.md`
11. `core/steps/chapter/STEP_8_QUOTED_DIALOGUE_REVISION.md`
12. `core/steps/chapter/STEP_8_5_QUOTED_DIALOGUE_REVISION_REVIEW.md`
13. `core/craft/README.md`
14. `core/craft/dialogue-runway.md`
15. `core/craft/quoted-dialogue.md`
16. `core/craft/spoken-fluency.md`
17. `scripts/glossary_check.py`
18. `requirement_from_other_repo/TRILINGUAL_GLOSSARY_CSV_REQUEST.md`
19. 本檔（status、acceptance checklist、completion report）

明確逐檔檢查而無需改動者包括 `AGENTS.md`、
`adapters/_template/GLOSSARY.csv`、`scripts/init_story_root.sh`、
`scripts/style_lint.py`、`scripts/twin_db.py`、chapter 其餘 step、craft 其餘
文件、其餘 module README 與 `core/schemas/templates/character.template.json`；
它們沒有把別的檔案宣告成專有用詞權威。歷史 request 既有內文不改寫。

### 每處修正 before → after

| 檔案 | before → after（一行） |
|---|---|
| `docs/PROJECT_PROFILE_CONTRACT.md` | `WORLD_RULES` 詞表是源、glossary 是營運投影、衝突時前者勝 → glossary 是專有用詞唯一正典 source；主權改由 USER-only 狀態變更＋provenance 保證，WORLD_RULES 只管世界真實與用詞哲學。 |
| `skills/game-story-factory/SKILL.md` | resolution/dispatch 把 WORLD_RULES 的 decided terms 與 glossary 衝突裁決一併交給 worker → WORLD_RULES 只在世界真實領域最高，glossary 單獨統轄詞條，禁止從 sovereignty/style/locale/twin 建第二詞表。 |
| `README.md` | glossary 是 operational termbase → glossary 存在時是 proprietary terms 的 sole canonical source。 |
| `adapters/_template/PROJECT_PROFILE.md` | present 只表示 registered terms bind dialogue → present 明定為 sole canonical proprietary-term source。 |
| `WORLD_RULES.template.md` | 內建 `## 用詞表（decided terms）` 三欄表 → 改成「用詞哲學與 glossary 路標」，詞條／三語／語域／禁詞／狀態／provenance 只住 glossary。 |
| `WORKFLOW_CORE_VARIABLES.template.md` | WORLD_RULES 範圍仍含 decided terms → 改為 terminology philosophy，並路標 proprietary-term entries 只住 glossary。 |
| `modules/world-rules-editor/README.md` | editor 管 decided-terms table → editor 只管用詞哲學，明列 glossary 詞條不屬 sovereignty files。 |
| `STEP_6_RUNTIME_DRAFT.md` | 只禁止從 shipped locale 造替代 termbase → 明定 glossary 唯一 source，並禁止 WORLD_RULES／STYLE_GUIDE／locale／其他 artifact 競爭。 |
| `STEP_6_5_RUNTIME_DRAFT_REVIEW.md` | world-term 升格後提醒同步 WORLD_RULES → USER-only 改 glossary 狀態並記 provenance；禁止鏡像到第二詞表。 |
| `STEP_7_RUNTIME_LANDING.md` | 只禁止從 locale prose 重建翻譯 → 明定 glossary 唯一 source，禁止其他 canon/style/locale artifact 覆寫。 |
| `STEP_8_QUOTED_DIALOGUE_REVISION.md` | 只禁止從 shipped locale 猜 en/ko → 明定 glossary 唯一 source，禁止其他 artifact 推斷或覆寫。 |
| `STEP_8_5_QUOTED_DIALOGUE_REVISION_REVIEW.md` | WORLD_RULES 衝突時勝且升格要同步它 → USER-only glossary 狀態變更＋provenance，禁止 mirror/第二詞表。 |
| `core/craft/README.md` | catalog 無跨 craft 的詞權威規則 → 新增 quoted/proprietary term craft 一律接 glossary sole source；缺席仍 NOT_AVAILABLE。 |
| `dialogue-runway.md` | 只禁止 locale reverse-engineering → glossary sole source；sovereignty/style-lint/locale 都不可造或覆寫詞條。 |
| `quoted-dialogue.md` | USER-only 升格但 WORLD_RULES 衝突時勝 → USER-only glossary 狀態變更＋provenance，禁止第二詞表。 |
| `spoken-fluency.md` | freeze list 泛稱 decided terms、缺 glossary 沿用手挑 → glossary available 時抽取只可來自 glossary；無 glossary 的 legacy 手挑行為明確保留。 |
| `scripts/glossary_check.py` | checker 行為雖已只讀 glossary，但未明載 authority boundary → docstring 固定 glossary 是唯一 term source、沒有 WORLD_RULES/style/locale-prose fallback。 |
| `TRILINGUAL_GLOSSARY_CSV_REQUEST.md` | 歷史 completion note 仍記錄雙源模型而無時效提示 → 不改歷史內文，只在檔首加 superseded 指標指向本案。 |

### 殘留掃描證據

排除 `requirement_from_other_repo/` 的生產文件後，以舊模型專屬片語掃描：

```bash
rg -n -i \
  '(sovereignty term list|operational projection|WORLD_RULES\.md wins every conflict|world-term promotion.*WORLD_RULES|decided-terms table|## 用詞表|主權表贏|主權表是源)' \
  story --glob '!**/requirement_from_other_repo/*.md'
```

結果：**0 matches**。全庫不排歷史檔時，舊模型敘述只留在
`TRILINGUAL_GLOSSARY_CSV_REQUEST.md`（已加 superseded 指標）及本案的問題／
驗收／報告紀錄；沒有任何生產契約或 worker 指示殘留第二權威。

正向掃描可在 contract、orchestrator、README、templates、steps、crafts、
module 與 checker 找到 `sole canonical`／`sole source of truth`，各 consumer
均指向 `<ADAPTER>/GLOSSARY.csv`。

### Checker、NOT_AVAILABLE、legacy 驗證

- `python3 -m py_compile scripts/glossary_check.py`：PASS。
- 兩列最小 glossary fixture（canon＋banned）＋對白 artifact：
  `RESULT: PASS errors=0 warnings=0`。
- `--glossary` 指向不存在檔案：exit 2＋`GLOSSARY ERROR`，證明 checker 不會
  回退讀 WORLD_RULES、STYLE_GUIDE 或 locale prose；orchestrator 在能力缺席時
  仍直接標 `NOT_AVAILABLE` 並跳過 glossary-only checks。
- `adapters/rpg-1/GLOSSARY.csv` 仍不存在；legacy resolution/behavior 未改。
- `init_story_root.sh` 臨時 bootstrap：會播種 header-only `GLOSSARY.csv`，
  新 `WORLD_RULES.md` 不再含 decided-terms table，只含 glossary 路標。
- `git diff --check -- story`：PASS；未修改 vinci_world game repo，未建立
  backup branch/file，測試產生的 `__pycache__` 已移除。
