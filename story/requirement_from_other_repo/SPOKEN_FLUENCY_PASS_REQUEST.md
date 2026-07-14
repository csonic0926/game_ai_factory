# Cross-repo factory request — 對白唸稿潤句工序（spoken-fluency pass）

## Request metadata

- Status: done（2026-07-13 factory 側實作完成，見文末 completion notes）
- Date: 2026-07-13
- Source repo: vinci_world (game repo, factory caller)
- Source repo path: /Users/hunglingki/git_projects/web_projects/vinci_world
- Request owner: USER（2026-07-13 對白產線實測後的裁定）
- Factory target area: core/craft（新工藝文件）| core/steps/chapter STEP 6/8 與各 .5 閘 | craft catalog README
- Priority: high（下一次對白生產前必須到位——沒有它，產出的台詞不能直接用）

## User-facing need

2026-07-13 以 vinci_world 做了一次對白產線實測（craft mode：`dialogue-runway`
＋`quoted-dialogue`，各一個 fresh worker，正常走完自檢）。USER 對成品的
裁定原話：

> Story factory 的產出唯一問題就是文句不流暢。就算生成英文的，也是非常
> 古怪的句子。但 beat、情感、身份等等確實是正確的。以語言學的角度講，
> 是文法不對——factory 產出的句子文法是有問題的。

USER 判例（實測產物 `GATE_KPI_DIALOGUE_RUNWAYS_SKYDIVE.md` 候選三第 1 句）：

- Factory 原句：「到了到了，就是這裡！你站的這條門廊在雲海上頭——後面是
  彼端，腳邊這口井望下去，就是村子。」
- USER 改句：「到了到了，就是這裡！這條門廊是在雲海上——後面是彼端。
  你從腳邊這口井往下望，就是我們的村子。」

病灶診斷：worker 在同一個 context 裡連續做設計推理（beat 職責、語用功能、
紅線自查），寫台詞時把**設計註記的壓縮句法**帶進了引號——主語與介詞省略
到只有書面才允許的程度（「腳邊這口井望下去」少了「你從……往」）、名詞前
疊關係子句（「你站的這條門廊」）、動詞搭配錯位（另一實測樣本把「亮出」
接上「喜歡」——亮出只能接實物）。而現有的品質關卡沒有一道抓得到它：
`.5` 閘驗的是**意義忠實度**（回上游比對語義）、style lint 查的是禁詞與
造標籤——沒有任何一步把句子當「話」唸一遍。beat／情感／身份正確恰好
證明約束收斂在運作；文法失守是因為**語言層從來不是任何 worker 的唯一
任務**。

## Factory-side change requested

1. **新增工藝文件 `core/craft/spoken-fluency.md`**（名稱可由 factory 定案，
   但必須是白話可讀的名字）。工藝定義：
   - 輸入：一份含引號台詞的 artifact（STEP 6 劇本、STEP 8 修訂稿、
     `dialogue-runway`／`quoted-dialogue` 產物皆可）＋該專案 adapter 的
     `STYLE_GUIDE.md`。
   - 工作：**只改句法，凍結其他一切**——beat 結構、語用功能、資訊內容、
     角色聲線特徵（語尾詞、口頭禪、句短句長的性格差）、紅線用詞全部
     不許動；逐句出聲唸（唸稿測試），把「設計註記腔」的句子改寫成
     該語言母語者嘴巴講得出來的話。改寫的最小單位是句，不是詞——
     必要時拆句、還原主語與介詞、換慣用動詞搭配。
   - 範圍：`<PRIMARY_LOCALE>` 與 `<SHIPPED_LOCALES>` 全部適用——en/ko
     的產出同樣要過各自語言的母語文法直覺，不是只修中文。
   - 每處改動在產物裡留一行對照（原句 → 改句＋一句改動理由），供閘門
     驗「意義沒被改掉」。
   - vinci_world 的答卷檔已備好可引用的規則錨：
     `<GAME_REPO>/design/story/adapter/STYLE_GUIDE.md` §4.1
     「對白口語文法（USER 判例 2026-07-13）」——五條從判例導出的自查
     規則（主語介詞不省、修飾子句限一層、一句一焦點、動詞搭配走慣用、
     唸稿是寫的人的步驟）。工藝文件應要求 worker 讀 adapter STYLE_GUIDE
     的對應章節；無此章節的專案以工藝文件內建的通用規則為準。
2. **接線（架構要求：獨立 fresh worker）**：凡產出引號台詞的步驟，其
   產物在進 `.5` 閘之前必須過一次本工藝，且**由一個獨立的 fresh worker
   執行**——不得讓原創作 worker 自己順手潤（病灶正是同一個 context 裡
   設計推理污染語言直覺；理由同「review 閘必須是獨立 worker」的既有
   架構原則）。落點：
   - chapter STEP 6（runtime draft）與 STEP 8（quoted dialogue revision）
     的步驟文件加上這一道；
   - craft mode 的 `dialogue-runway`、`quoted-dialogue` 在 README 註明
     「產物建議串接 spoken-fluency 後再交 USER」；
   - 對應 `.5` 閘（6.5、8.5）的檢核清單加一條：抽三句出聲唸，唸得出
     設計註記腔即 FAIL 回整數步。
3. **craft catalog README 更新**：新工藝入表（purpose／typical input／
   output）。

## References and source context

- 實測產物（病例＋病灶樣本）：
  `<GAME_REPO>/design/story/runtime_scene_drafts/GATE_KPI_DIALOGUE_RUNWAYS_SKYDIVE.md`
  `<GAME_REPO>/design/story/runtime_scene_drafts/ENTRY_SKYDIVE_NEW_LINES_TRILINGUAL.md`
- 規則錨（答卷側，已落地 2026-07-13）：
  `<GAME_REPO>/design/story/adapter/STYLE_GUIDE.md` §4.1
- 相關既有條款：STYLE_GUIDE §4「禁 LLM 腔」（病徵清單＋土法唸稿檢測，
  2026-07-04）——本請求把它從 reviewer 的病徵對照升級為一道**獨立工序**。
- 架構先例：`.5` 閘只判 PASS/FAIL 不改內容、一步一 fresh worker
  （SKILL.md core orchestration rules）。

## Acceptance criteria

- [x] `core/craft/spoken-fluency.md`（或 factory 定名）存在，定義輸入／
      凍結範圍／唸稿程序／對照輸出，三語適用。
- [x] chapter STEP 6、STEP 8 步驟文件明文要求產物過本工藝（獨立 worker），
      6.5／8.5 閘檢核清單含出聲唸抽查。
- [x] craft README catalog 入表；`dialogue-runway`／`quoted-dialogue` 條目
      註明建議串接。
- [x] 以 vinci_world 實測產物任一候選跑一次本工藝 dry-run：beat／語用／
      聲線零改動、句法改動有對照行、成品過 STYLE_GUIDE §4.1 五條自查。
- [x] 不動 sovereignty 規則（工藝不碰 WORLD_RULES / NARRATIVE_DELIVERY）。

## Non-goals / do-not-change

- 不改 `.5` 閘「只判不改」的性質——潤句是工序（整數步側），不是閘。
- 不把本工藝做成自動 lint／腳本——文法直覺是語言模型的活，lint 只管
  禁詞（既有 style_lint 不變）。
- 不在本案內回頭重潤已上線的對白（vinci_world shipped 台詞由 game repo
  自行處置）。

## Completion notes（factory 側，2026-07-13）

實作落點（工藝定名維持 `spoken-fluency`，中文名「唸稿潤句」）：

1. **`core/craft/spoken-fluency.md` 已建立**。內含：獨立 fresh worker 的
   架構要求（明文寫進工藝文件本身，不只靠接線）；凍結清單（beat 結構、
   語用功能、資訊內容、聲線特徵、canon 用詞、引號外敘述、落地檔的
   routing/id）；逐句唸稿程序（改寫最小單位是句）；五條通用口語文法
   規則（從 USER 判例導出，project-agnostic；專案 STYLE_GUIDE 的口語
   文法章節存在時優先並可加嚴）；三語各依母語直覺；對照行輸出格式
   （原句 → 改句＋一行文法理由）；honesty loop（結尾點名一兩處最沒把握
   的改寫，交下一道閘裁決）。USER 判例原句／改句全文收錄為錨。
2. **接線完成（獨立 worker 明文化三處）**：
   - `STEP_6_RUNTIME_DRAFT.md`／`STEP_8_QUOTED_DIALOGUE_REVISION.md` 各加
     「Spoken-fluency pass (required before STEP 6.5/8.5)」一節——存檔後、
     進 `.5` 閘前，由 orchestrator 另派一個 fresh worker 執行，原創作
     worker 不得自潤。log 落點：STEP 6 → `<ARTIFACT_STEM>_FLUENCY.md`；
     STEP 8 → `<ARTIFACT_STEM>_DIALOGUE_REVISION_FLUENCY.md`。
   - `STEP_6_5`／`STEP_8_5` 閘各加「Spoken fluency（唸稿抽查）」驗收段：
     驗 fluency log 存在且有對照行；抽三句出聲唸（8.5 跨語言抽），唸出
     設計註記腔即 FAIL 回整數步；用對照行 spot-check 意義／beat／語用／
     聲線未被改動。
   - `skills/game-story-factory/SKILL.md` chapter hard bindings 加一條
     （orchestrator 是派工的人，只改步驟文件它看不到），內容同上。
   - 分支線 STEP 13–22.5 重用 trunk 步驟檔，自動繼承本工序。
3. **craft catalog README 已入表**；`dialogue-runway`、`quoted-dialogue`
   兩條目的 output 欄加註「chain `spoken-fluency`（separate fresh worker）
   before handing to USER」。
4. **Dry-run 已跑（驗收第 4 條）**：獨立 fresh worker 對
   `GATE_KPI_DIALOGUE_RUNWAYS_SKYDIVE.md` 候選三執行本工藝，非破壞式
   輸出至同目錄 `GATE_KPI_DIALOGUE_RUNWAYS_SKYDIVE_SPOKEN_FLUENCY_DRYRUN.md`
   （原檔未動）。結果：zh 五句唸五句、改四句留一句（USER 指定的 KPI 終點
   句凍結未動）；第 1 句 worker 自行收斂到與 USER 判例改句逐字相同——
   工藝文件本身足以讓乾淨的腦袋重現 USER 的改法；凍結清單五項全過、
   §4.1 五條自查全過；honesty loop 點名兩處交閘裁決（「立起來→安頓好」
   的畫面略平、「此刻→現在」屬詞彙修不是嚴格句法修）。候選三無 en/ko
   句，dry-run 檔內已明記規則 5 無材料、未擅自造譯文。
5. **Sovereignty 未動**（驗收第 5 條）：工藝文件明文禁編輯 WORLD_RULES /
   NARRATIVE_DELIVERY；dry-run worker 僅讀取。

驗收清單五條全勾。範圍外備忘（不在本案動）：`choice-aftermath-writing`
等其他會產引號台詞的 craft 未強制接線，僅靠 README 的 chaining 慣例；
若下次實測再現同病，可比照 STEP 6/8 明文化。

**追記（2026-07-13 晚，USER 裁定後的層級修正）**：completion notes 第 1 條
「USER 判例原句／改句全文收錄為錨」已修正——專案內容不得住在 factory 側
的通用工藝文件裡。`spoken-fluency.md` 的判例錨改為：規則內嵌例句全部換成
中性構造例；「USER precedent (the anchor)」一節改為「The project exemplar
library (the anchor)」——判例庫的唯一住所是各專案 adapter（vinci_world＝
STYLE_GUIDE §4.1.1），worker 動工前讀整庫。同時寫入教義：**判例是教學不是
欽定**——worker 自行導出改句，判例原句命中時結果逐字相同是機制在運作；
產物不得把品質層改句標成「owner 欽定句」，欽定只存在於創作層（beat sheet
鎖定的終點句一類）。
