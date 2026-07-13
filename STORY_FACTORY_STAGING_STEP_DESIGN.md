# Story Factory — 新增「實拍設計」step ＋ 攝影文法 adapter 檔（設計規格）

> 來源：vinci_world ENTRY_LANDING 驗證跑（2026-07-07/08）暴露的根本問題——
> 工廠 STEP 6 產出的是電影文法劇本（海面往後退、兩船並行全景、特寫、切鏡），
> 而目標引擎只會平面 iso ＋ 平移縮放，且角色無動畫、只用表情符號回應。
> 「劇本拍不出來、節奏不對」（USER 2026-07-08）。
>
> USER 定的修法：**STEP 6 維持「按 beat 出劇本、與媒介無關」；新增一個 step
> 把劇本落實成這台引擎實際拍得出來的呈現，並在同一步決定哪拍是 cutscene、
> 哪拍是玩家操作。** 這份是該 step ＋ 其讀的 adapter 能力檔的設計規格。
> 實作落在 `tools/game_ai_factory/story`。

---

## 一、問題定位：工廠缺「攝影文法」這層輸入

STEP 6 憑 beat sheet 的畫面（散文）寫劇本，但沒有任何輸入告訴它目標引擎能
拍什麼。於是它用通用電影文法寫，理所當然地叫出「兩船並行的推軌全景」——
一個 iso tile 引擎根本說不出的句子。這跟先前兩個 bug 同源（落地面存在性、
渠道同步），但更底層：**不是場景不存在，是引擎的攝影語言與劇本的語言不同種。**

節奏同理：STEP 6 把大部分拍派給對話框 say-beat（＝「講」的節奏），但
「壓住取得、只建期望」這種走廊要的是「住」的節奏（玩家自走、環境定格、
字極少）。沒有「原生節奏」這層輸入，工廠會預設電影/小說的敘事節奏。

## 二、新 adapter 檔：`adapters/<project_id>/VISUAL_GRAMMAR.md`

宣告目標引擎的**實拍能力與節奏**，與 `DELIVERY_CHANNELS.md` 同級、由 adapter
維護。必含欄位：

- **視角（view）**：例 vinci_world＝JRPG 俯視 tile map，單一固定 iso 角度，
  不可換鏡位。
- **相機能力（camera）**：可做的相機操作**白名單**。vinci_world＝平移（pan）、
  標準縮放（zoom，canvas scale）、對某格/某角色/兩點中點聚焦、跟隨、
  淡入淡出、上下黑條。**無**切鏡、景別（特寫/全景）、鏡位切換、推軌。
- **角色表演（actor）**：vinci_world＝逐格走、四向面朝、表情符號泡泡；
  **無逐幀動畫**——所有情緒回應只能靠表情符號＋面朝＋走位，不能靠表情/
  肢體演出。
- **絕對禁區（cannot）**：明列引擎做不到的手法，讓 STEP 6/實拍步能自檢。
  vinci_world＝移動載具、並行運動的物件、背景捲動、特寫、蒙太奇/切鏡、
  任何「鏡頭運動」以外的電影手法。
- **原生節奏（native pacing）**：一拍在這遊戲裡感覺多長、哪種節奏是「住」、
  哪種是「講」。vinci_world＝對話框逐句＝講（省用）；玩家自走＋環境定格＝
  住（主力）；表情符號一次一個情緒點。
- **可用呈現原語（primitives）**：對照 runtime 實際 API——cutscene say/walk/
  face/camera/fade/emote/sfx/transition beats、mission（ReachTile/EnterScene）、
  NPC ambient chat、item text、scene layout、achievement copy。

## 三、新 step：「實拍設計 / Staging & Realization」

位置：**STEP 6 之後、STEP 7 落地之前**（建議編號 STEP 6.7，配 6.75 審查閘；
或明確重切 6→7 邊界，見§五）。輸入、動作、輸出如下。

**輸入**：
1. STEP 6 放行的劇本稿（散文，與媒介無關）。
2. `VISUAL_GRAMMAR.md`（本設計新增）。
3. delivery-planner 的每拍**渠道意向**（粗粒度：這拍是說的/環境的/玩家移動的）。
4. beat sheet（回查每拍的情感與「憑什麼到位」）。

**動作（逐拍/逐場景）**：
1. **判 cutscene vs 玩家操作**——這是 USER 點名要在這步做的決定。準則：
   情感靠「玩家自己動作」交付的拍＝玩家操作段（走、走到、親手）；靠
   「被安排好的畫面/群體調度/時間控制」交付的拍＝cutscene。此判定會**細化
   或推翻** delivery-planner 的粗意向，因為這步才看得到實際能拍什麼。
2. **設計實拍**——把該拍的畫面翻成 `VISUAL_GRAMMAR` 白名單內的具體操作序列：
   哪個相機操作、聚焦哪格、縮放到多少、誰走到哪格、誰面朝哪、哪個情緒用
   表情符號、環境靠什麼定格。**只准用白名單原語**。
3. **撞禁區即回報**——劇本某拍要的呈現若落在 `cannot`，標兩種出路之一：
   (a) **restage**：在現有文法內重新調度該拍的等價畫面（例：「船在動的航程」→
   「靜態船場景＋抵達用場景切換」；「兩船並行」→「已並排靠泊的一塊區域」）；
   (b) **engineering dependency**：值得為它擴引擎——明列所需 runtime 能力，
   交遊戲 repo。不得靜默沿用拍不出的鏡頭。
4. **節奏校準**——依 `native pacing` 檢查全段：對話框是否用過頭（該「住」的
   段落被寫成一句句「講」）；把可轉成「玩家自走＋環境」的段落轉過去。

**輸出**：一份**實拍設計稿（staging plan）**，逐拍記：
- cutscene / 玩家操作（binding 決定，附理由）；
- 實拍操作序列（白名單原語，可直接餵 STEP 7 落地，近乎機械轉譯）；
- 撞禁區項的 restage 方案或工程相依；
- 節奏標記（住/講、預估拍長）。

**審查閘（6.75）**：只驗——每個呈現操作都在 `VISUAL_GRAMMAR` 白名單內
（引擎拍得出來）；cutscene/操作的判定守準則；情感驗收（實拍有沒有把該拍
的「憑什麼到位」拍出來，壓/放有沒有走樣）；撞禁區項有沒有明確出路。
FAIL 路回 STEP 6.7，不在閘內改。

## 四、STEP 7 落地隨之瘦身

STEP 7（cutscene-staging craft）從「讀散文劇本、自己想像成鏡頭與站位」降為
**機械轉譯**：讀實拍設計稿的白名單操作序列，直接產 `.cutscene.json` beats／
mission 定義／NPC 行／locale keys。它不再重新推導畫面——推導在 6.7 做完了。
這消掉「散文被描述一次、又被重新想像一次」的漂移點。

## 五、與現有結構的接縫（實作時決定）

- delivery-planner 保留為 beat-sheet 級的**粗渠道意向**；**cutscene vs 玩家
  操作的 binding 決定移入實拍設計步**（看得到攝影文法才判得準）。兩者不衝突：
  planner 給意向，staging 落地並可推翻。
- 現有 `core/craft/cutscene-staging.md` 的定位改為「STEP 7 落地的機械轉譯
  工具」，實拍**設計**上移到新步。
- preflight（STEP 1，已加落地面盤點）順帶讀 `VISUAL_GRAMMAR`：beat sheet 若
  整段依賴引擎 `cannot` 的手法，preflight 就先警示，不必等到實拍設計步才撞。

## 六、落點檔案清單（給實作）

- 新增 `adapters/vinci_world/VISUAL_GRAMMAR.md`（內容見§二，vinci 值已在本檔列出）。
- adapter 契約 `docs/PROJECT_PROFILE_CONTRACT.md`：登記 `VISUAL_GRAMMAR.md` 為
  adapter 必備檔（缺＝實拍設計步 BLOCKED）。
- 新增 `core/steps/chapter/STEP_6_7_STAGING_REALIZATION.md` ＋
  `STEP_6_75_STAGING_REVIEW.md`（內容見§三）。
- `core/steps/chapter/STEP_7_RUNTIME_LANDING.md`：改為讀實拍設計稿、機械轉譯（§四）。
- `core/steps/chapter/STEP_1_CHAPTER_PREFLIGHT.md`：加讀 `VISUAL_GRAMMAR` 的
  整段可拍性預警（§五）。
- `modules/delivery-planner/README.md`：註明 cutscene/操作 binding 決定移交
  實拍設計步（§五）。
- `skills/game-story-factory/SKILL.md`：章節管線步序加入 STEP 6.7；chapter
  hard bindings 加「實拍設計步 REQUIRES `VISUAL_GRAMMAR.md`」。

## 六之補、完整性缺口（double-check 後補；實作務必涵蓋）

以下三項在初稿漏了或講得不夠死，對照 factory 現有結構補上：

1. **Phase C 分支階段要鏡像這一步（真缺口）。** 章節管線有 Phase C（STEP
   13→22.5，分支落地＝重用 trunk 檔 1–11.5 minus STEP 10 ＋
   `BRANCH_IMPLEMENTATION_OVERLAY.md`）。該 overlay 是「每個重用的 trunk step
   一個小節」（現有 `Reused STEP 1` / `Reused STEP 2` …）。新增 STEP 6.7 後，
   overlay **必須加一節 `Reused STEP 6.7`**（分支的實拍設計：分支場景可能引入
   trunk 沒有的呈現需求，同樣要過 `VISUAL_GRAMMAR` 白名單、同樣在此判分支拍的
   cutscene/操作）。SKILL.md 的 Phase C 描述「trunk files 1–11.5」範圍已自然
   涵蓋 6.7，但 overlay 的對應小節要手動補。落點：
   `core/steps/chapter/BRANCH_IMPLEMENTATION_OVERLAY.md`。

2. **STEP 6.5 審查閘的範圍要講死（小補）。** STEP 6.5（`STEP_6_5_RUNTIME_DRAFT_
   REVIEW.md`）審的是劇本的**情感與內容**，**不審可拍性**——可拍性是 6.75 的
   事。要在 6.5 加一句：劇本用了電影文法（如「兩船並行全景」）**不構成 FAIL**，
   因為 STEP 6 本就與媒介無關；6.5 若拿引擎拍不出來當理由退稿，就是把兩步的
   分工搞混了。落點：`core/steps/chapter/STEP_6_5_RUNTIME_DRAFT_REVIEW.md`。

3. **`VISUAL_GRAMMAR` 與 `LANDING_SPEC` 的分工要點明（小補）。** 兩者互補、
   不重疊：`LANDING_SPEC.md` 宣告**落地面**（哪種 surface、locale key 規格、
   放行硬關卡）；`VISUAL_GRAMMAR.md` 宣告**怎麼拍**（相機/角色/禁區/節奏）。
   實拍設計步讀 `VISUAL_GRAMMAR`；STEP 7 落地讀 `LANDING_SPEC`（產哪種文件）
   ＋實拍設計稿（拍什麼）。contract 登記兩檔都是 adapter 必備。落點：
   `docs/PROJECT_PROFILE_CONTRACT.md`。

## 七、對 ENTRY_LANDING 現稿的即時意義

現稿（`runtime_scene_drafts/ENTRY_LANDING_zh.md`）是 STEP 6 產物、與媒介無關，
**留著不廢**——它是實拍設計步的合法輸入。實拍設計步跑起來後，會對它做的事：
E00「海面往後退」→ restage 成靜態船場景；E03「兩船並行全景」→ restage 成
已並排靠泊的一塊區域；把對話框過重的段落（E02/E05）與玩家自走段（E01/E06）
的節奏重配；並逐拍落 cutscene/操作 binding。這步做完，才輪到 STEP 7 產真正
上得了這台引擎的 cutscene 文件。
