# Cross-repo factory request — Gameplay Factory：從玩法創作到實際遊玩驗收

## Request metadata

- Status: in_progress（v1 contract／reader foundation 已按 reframing 落地；真實 runtime pilots、mismatch rejection、cross-project proof 待完成）
- Original date: 2026-07-17
- Reframed: 2026-07-19
- Source repo: umbrella-level requirement
- Request owner: USER
- Factory target: `gameplay/`
- Priority: high

> 本文件取代這份 proposal 先前以 Walkthrough Trace／Decision Loop 為中心的架構。
> 舊內容只可作歷史背景，不是新的實作權威。已存在的 contract、template 和
> Phase 0 產物必須逐項重新對照本文件；名稱相同不代表語義已符合。

---

## 一、真正要建立的產品

Gameplay Factory 不是：

- 替兩個 story beats 之間填入移動、戰鬥和互動；
- 生成一份看起來像 walkthrough 的文件；
- 把 gameplay specification 交給 coding AI 後便宣布完成；
- 在實作後跑幾個測試、截幾張圖，再由同一個 AI 自稱驗收通過。

它必須提供一個閉合的 production loop：

```text
Gameplay Experience authoring
    ↓
continuous player-time realization
    ↓
production packets + observability requirements
    ↓
caller AI implements code / data / story / asset / sound
    ↓
actual gameplay is logged and reconstructed in player time
    ↓
fresh, information-isolated acceptance compares intended experience
against observed runtime experience
    ↓
PASS, or route the failure to the correct upstream step
```

Factory 的完整 deliverable 不是「玩法文件」，而是：

1. 一份有權威、有版本的原初 gameplay experience design；
2. 可供 production 實作的連續玩法與 beat packets；
3. production 同時落地的 gameplay observation／logging 能力；
4. Factory 自己能讀回的 runtime evidence；
5. 對「實際遊玩是否兌現原初設計」作出的獨立驗收。

少了第 3–5 項，Factory 只是 design generator，不是 production factory。

---

## 二、正確驗收從哪裏來

AI 不會因為換上 `reviewer` 角色就突然擁有正確判斷。正確性必須由 artifact
authority、information partition 和 review structure 共同建立。

Story Factory 的有效先例是：

- USER-ruled Emotional Beat Sheet 是最高語義來源；
- 下游 artifact 綁定該來源的確切版本；
- 每次轉譯後由 fresh review worker 驗收，reviewer 只判 PASS／FAIL，不修稿；
- 驗收問的是原定 beat 是否在下游真正 TRANSMIT，而不是關鍵詞或檔案是否存在；
- 最終 QA 回到 landed artifacts，按玩家順序逐 beat 指出由哪個 channel 承載。

Gameplay Factory 必須沿用同一原理，但 gameplay 比 story 多一個不可省略的
條件：玩家經驗是在 runtime interaction 中生成，不能只從 design 文件或 code
推斷。因此最終驗收必須同時持有兩條彼此獨立的證據鏈：

```text
Authority chain:
approved Gameplay Experience Beat Sheet
→ approved walkthrough
→ approved beat packets / production contract

Observation chain:
actual build
→ raw gameplay log + captures
→ normalized Observed Gameplay Trace
→ blinded runtime-player reading
```

最後的 acceptance reviewer 比較兩條鏈的語義是否相符。它不能把 implementation
作者的解釋、code comment、design intent 或 golden-path 答案餵給 blind reader。

現有 `FIRST_TIME_PLAYER_INPUT` 從 design trace 的 `visible_and_known` 投影而來，
仍然有價值，但只可稱為 **paper-stage design reception prefilter**。它能揭露設計
文件自己是否提供足夠 cue，不能證明實作真的把 cue 放進畫面。Runtime acceptance
所使用的 blind input 必須由 actual build evidence 經 Factory reader 產生，兩者
不可共用來源或用同一份 report 代替。

### Factory 可以和不可以聲稱甚麼

Factory 可以聲稱：

- implementation 是否忠於指定版本的 gameplay design；
- 原定 cue、agency、challenge、response、learning／model update 和 handoff
  是否在實際遊玩證據中出現；
- 玩家是否獲得公平、清楚、沒有被 UI／camera／control order 破壞的接收條件；
- 一段設計是否退化成只可服從 objective 的 compliance chain。

Factory 不可以聲稱：

- 每一個真人必然感受到指定情緒；
- 結構合格便等於「好玩」；
- 一次 golden-path run 證明所有玩家與所有分支都成立。

Factory verdict 應明確區分 `FACTORY_CONFORMANCE_PASS` 和
`HUMAN_PLAYTEST_ACCEPTED`。前者不可冒充後者。

---

## 三、最高語義來源：Gameplay Experience Beat Sheet

### 3.1 定位

Factory 必須新增正式的 **Gameplay Experience Beat Sheet** contract、template、
authoring guidance 和 review gate。

它是 gameplay production 的最高語義來源，地位等同 Story Factory 的
Emotional Beat Sheet。Walkthrough Trace 不再是最高來源；它只是 Beat Sheet
在連續玩家時間中的第一個 realization。任何 trace、packet、production plan、
runtime acceptance 都必須綁定 Beat Sheet 的確切版本。

Beat Sheet 回答：

> 玩家在這一段實際需要注意甚麼、想甚麼、做甚麼、承擔甚麼、學會甚麼，
> 以及為甚麼這個 experience 只有放在這裏才成立。

它不回答具體 engine API、scene path、CSV row 或 asset filename；那些屬於
production adapters 與下游 realization。

### 3.2 Sheet-level 強制規格

每份合格 Beat Sheet 必須包含：

1. **Identity and scope**
   - stable sheet id；
   - 從哪個可辨識的 player situation 開始，到哪個 situation 結束；
   - story anchors、world/player state、gameplay sovereignty／profile 等來源；
   - target game mode／platform assumptions。

2. **Authority and version evidence**
   - revision date、plain-language change record、stable version token／checksum；
   - status：`USER_APPROVED`、`AI_DRAFT_FOR_REVIEW` 或 `STALE`；
   - USER 已敲定的 ruling 與 AI 自行假設的內容必須分開。

3. **Target player frame**
   - 玩家在進入這段前已知道甚麼、熟練甚麼、正想完成甚麼；
   - 這是 first-time、returning、expert 或其他 adapter-declared player frame；
   - 允許的失誤、迷路、風險胃口和注意力假設。

4. **Ordered experience curve**
   - ordered beats；
   - 每拍的 `build | hold | release | recovery | rest` curve mark；
   - 全段的主要 tension／curiosity／mastery／expression arc；
   - 哪些 open loops 在段尾仍然保留。

5. **Rulings and red lines**
   - 不可被 production 改寫的 player-facing meaning；
   - 不可變成的失敗形態，例如「只跟 objective marker 走」、「cutscene 代替
     玩家親手完成」、「reward popup 提早洩掉 hold」。

### 3.3 Per-beat 強制規格

每一拍必須在同一個抽象高度，用具體的玩家時間來寫，並包含以下欄位：

1. **Concrete player situation**
   - 玩家此刻實際看見、聽見、控制和承受的局面；
   - 禁止只寫「探索」、「建立期待」、「有生存感」等抽象指令。

2. **Live player purpose or question**
   - 玩家當下想完成、確認、避免、試驗或表達甚麼；
   - 必須能由先前 runtime evidence 長出，不可只由作者在欄位中宣告。

3. **Why this beat works here**
   - 需要哪些既有知識、資源壓力、技能、關係或未解問題；
   - 說明若提前一拍或延後一拍，experience 會失去甚麼。

4. **Primary engagement mode**
   - 至少標一個主要模式：`decision`、`execution/mastery`、
     `discovery/interpretation`、`expression/social`、`payoff/recovery`；
   - 可組合，但不可用一串標籤代替具體內容。

5. **Player work**
   - 玩家真正需要投入的認知、空間、感官、節奏、策略、操作、記憶、表達或
     社交工作；
   - 若玩家不需要投入任何工作，必須明示這是 payoff／recovery／rest，並指出
     它正在兌現哪個上游 loop 及其 duration budget。

6. **Agency／challenge source**
   - 這一拍憑甚麼不是單純服從；
   - decision beat：列出玩家當時可知、可做、結果不同且沒有被明顯支配的
     meaningful alternatives；
   - execution/mastery beat：列出需要讀取的 pattern、可改善的 skill dimension、
     failure feedback 和再次調整的機會；
   - discovery/interpretation beat：列出未解問題、可取得的證據和可被更新的
     hypothesis；
   - expression/social beat：列出可表達的偏好／姿態，以及世界如何辨認並回應；
   - payoff/recovery beat：列出被兌現的上游 commitment，禁止憑空派 reward。

7. **Commitment and pressure**
   - 玩家投入了甚麼：時間、位置、資源、暴露、機會成本、節奏準確度、關係
     立場或注意力；
   - 若 commitment 為零，說明這一拍仍成立的理由。

8. **Observable world response**
   - 世界如何回答玩家；
   - 哪些 camera、HUD、sound、animation、dialogue、state change 或 spatial
     consequence 讓回答可被接收；
   - response 不可只是一個「完成」回執。

9. **Intended player change**
   - 這一拍希望令玩家在 knowledge、skill、strategy、desire、confidence、
     relationship reading 或 future expectation 上發生甚麼變化；
   - 這是 intended delta，不得寫成「玩家一定感到／一定明白」。

10. **Carry-forward**
    - 上一項變化如何生成下一個 player intent、選擇傾向或 open question；
    - 下一拍不得只靠系統重新簽發一張無關 objective。

11. **Failure／misread／recovery**
    - 玩家漏看 cue、選錯、操作失敗或形成另一個合理理解時，遊戲如何回應；
    - 指明 acceptable drift、fail-forward 或 reset boundary。

12. **Acceptance kernel**
    - production 完成後，必須在 actual observed gameplay 中看見哪些最小證據鏈，
      才能說這一拍仍然存在；
    - 必須包含 cue presentation → player action／attempt → world response →
      carry-forward 的可觀察落點；
    - 對不可直接觀察的理解／情緒，只能規定公平接收條件與 blind-reader 判斷，
      不得要求 logger 直接聲稱玩家心理狀態。

### 3.4 Type-specific completeness rule

不是每拍都要有 explicit choice；節奏輸入、瞄準、搜索、表達、等待 payoff 都可
以不同方式構成 gameplay。因此 Factory 不得把「兩個選項」硬塞進每個 moment。

但每拍必須滿足其 primary engagement mode 的完整性。若一拍沒有 decision、
沒有 mastery demand、沒有 discovery、沒有 expression，也沒有兌現任何既有
loop，它便不是 gameplay beat；應合併、刪除、改成 presentation beat，或退回
設計層重做。

### 3.5 Beat Sheet review gate

Fresh reviewer 只做 PASS／FAIL，不直接修 sheet。至少檢查：

- 每拍是否由具體 player situation 而非抽象設計語句構成；
- purpose 是否由玩家可取得的證據形成；
- engagement mode 是否真的有相應 work／agency／challenge；
- response 是否會改變後續遊玩，而不是 completion receipt；
- carry-forward 是否形成 intent chain；
- curve 的 build／hold／release 是否有因果次序；
- acceptance kernel 是否可由 runtime observation 支持；
- AI 假設與 USER ruling 是否分開，版本是否可追溯。

一個欄位填滿但語義空洞的 sheet 必須 FAIL。Checklist completeness 不是品質證明。

---

## 四、AI 與 USER 敲定內容的非強制指引

Beat Sheet contract 是強制；以下 dialogue guidance 是建議，不是問卷。AI 只應
挑選當前最能改變整段設計的 3–5 個問題，不得每次機械地逐題詢問。

建議優先與 USER 敲定：

- 玩家離開這一段後，最值得記住或向別人描述的是哪一個親手經歷？
- 這一段的滿足主要來自判斷正確、操作變熟、發現未知、表達偏好，還是被世界
  回應？
- 哪個結果必須由玩家賺回來，不能用對白、cutscene 或 popup 直接送出？
- 玩家應該在哪裏猶豫；猶豫來自未知、代價、技巧，還是價值取捨？
- 失敗應該讓玩家覺得「我下次知道怎樣改」，還是讓世界／角色關係轉向？
- novice 和 experienced player 在這一拍應該做出甚麼不同的閱讀或行動？
- 哪些路段刻意是日常、喘息或享受 presentation；它可以維持多久才不會變成
  跑腿？
- 玩家控制權與作者安排的 timing 在哪裏交界？哪一部分被奪走便會破壞 experience？
- 有沒有一個看似合理但不應被遊戲默認的替代行動？世界應如何誠實回應它？
- 這一拍服務哪類玩家慾望；它是否符合本 project 的核心 fantasy／commercial
  purpose？

Live session 可把 USER 確認的答案即時寫入 Beat Sheet；headless／auto run 可
自行作出最佳判斷，但必須標為 `AI_DRAFT_FOR_REVIEW`，記錄 assumptions 和 open
items。未經 USER ruling 的 sheet 可以接受 implementation-conformance 驗收，
但 Factory 不得宣稱它代表 USER 已接受的 gameplay direction。

---

## 五、從 Beat Sheet 到 production：沿用 Story Factory 的 step discipline

Gameplay Factory 應採用整數創作 step + `.5` fresh review gate、file-based
handoff、reviewer 不修內容、FAIL 回到對應上游 step 的結構。具體 step number
可在實作時調整，但責任順序不可顛倒。

### A. Source and preflight

1. 建立／解析 Gameplay Experience Beat Sheet；
2. 綁定 exact version，讀取 current runtime/world/player-knowledge state；
3. 解析 project gameplay、production、observation adapters；
4. 若某個 acceptance kernel 無法觀察，必須在 production 前報
   `BLOCKED_BY_OBSERVABILITY`，不可等實作完成後才發現無法驗收。

### B. Continuous realization

1. Intended Player 按 Beat Sheet 連續 rollout 整段 player time；
2. 先保持連續遊玩質地，再 annotation state、control、knowledge、engagement
   loop 和 delta；
3. Walkthrough 必須綁定 Beat Sheet version；
4. fresh reviewer 驗證 continuity、no-lookahead、agency／challenge、curve 和
   beat coverage；
5. paper-stage First-time Player 只讀 design projection 的 observable fields，
   作為 pre-production reception prefilter，而不是 runtime acceptance。

### C. Packet compilation

1. 從 approved walkthrough 切出 Playable Beat Packets；
2. packet 同時包含 experience contract、player-action contract、runtime contract
   和 **observation contract**；
3. packet 不得發明 walkthrough 中不存在的 gameplay；
4. packet 必須回指 Beat Sheet beat 和 version；
5. packet review 檢查 production 是否能在不改寫 experience 的情況下落地。

### D. Production and landing

1. caller AI 依 packet 實作 game code／data；
2. story、asset、sound factory orders 必須保留 packet／beat provenance；
3. gameplay implementation 和 observation instrumentation 是同一個 production
   job 的兩個 deliverables；
4. 缺 logging／capture hook 的 beat 不可標記 production complete；
5. landing review 驗證 runtime mapping 與 instrumentation mapping，不能只測
   happy-path state delta。

### E. Runtime observation and acceptance

1. 用 actual build 產生 raw evidence；
2. Factory reader 把 project-specific evidence normalize 成 canonical Observed
   Gameplay Trace；
3. fresh blinded runtime-player session 只讀 sequential runtime observations，
   不讀 Beat Sheet、walkthrough、packet、code 或 design intent；
4. acceptance reviewer 才同時讀 authority chain 與 observation chain，逐 beat
   判斷原初 experience 是否在 runtime 存活；
5. reviewer 只 PASS／FAIL／INCONCLUSIVE，不能在同一 pass 修 implementation
   或重寫原 design；
6. final human playtest 維持為 subjective enjoyment 的最高 gate。

---

## 六、Observation／Reading subsystem 是 Factory 的必需產品

### 6.1 原則：先設計可讀性，再實作 gameplay

Factory 不能在 production 後才問「怎樣知道玩家剛才經歷了甚麼」。每個 Beat
Packet 在交付 production 時必須帶 observation contract；Production Adapter
必須回答如何捕捉；Factory 必須擁有把捕捉結果讀回 canonical experience
timeline 的工具。

這是 **design for observability**：

```text
No observable acceptance evidence
→ no production-ready packet
→ no factory PASS
```

### 6.2 三種 evidence 必須分開

1. **Raw runtime evidence**
   - actual input、action、trigger、state delta、control owner、camera／HUD／modal
     state、objective／dialogue order、audio／visual cue emission、position、timing；
   - screenshots、video frame refs、audio refs、state dump 等 capture artifacts；
   - append-only、保留原始順序，不含 design interpretation。

2. **Derived observable timeline**
   - Factory reader 依 Observation Adapter 把 engine-specific events normalize 成
     玩家時間中的事件；
   - 可指出畫面上出現了甚麼、控制是否可用、輸入何時發生、回應延遲多久；
   - 不可直接寫「玩家明白了」、「玩家覺得緊張」、「這是 meaningful choice」。

3. **Experience interpretation**
   - blinded runtime player／human report 對 timeline 或 live build 作出的目的、
     forecast、alternative、confidence、misread、update 判斷；
   - 這是 QA evidence，不回寫成 raw runtime truth。

把三層混在同一 log，會讓 implementation 自己宣告自己達成了設計，驗收失效。

### 6.3 Canonical raw log 最低語義覆蓋

Factory 應定義 project-agnostic log schema。實際欄名可在 schema design step
定案，但最低必須覆蓋：

- session／run id、build／content revision、save／seed／locale／input mode、platform、
  viewport／window mode 和 relevant performance context；
- monotonic timestamp 及可比較的 frame／sequence order；
- scene／map／encounter context；
- player input 和已解析的 gameplay action（兩者分開）；
- control owner、movement enabled、cutscene／dialogue／modal state；
- relevant runtime／world state before、delta、after；
- camera transform／viewport，以及關鍵 cue／actor／UI presentation state；
- objective、dialogue、feedback、reward、audio／VFX emission order；
- screenshot／video／audio／state snapshot references；
- neutral runtime ids 與 private provenance mapping。

Raw logger 不可寫入 `player_forecast`、`player_understood`、`felt_fun`、
`meaningful_alternative=true` 等心理或評價欄位。那些只能由 blind reading 和
acceptance comparison 產生。

### 6.4 Factory 必須提供的 reading-tool capabilities

Factory foundation 只有 contract/template 不算完成。至少要有可重複調用的
工具介面完成：

1. **schema validation** — 檢查 log version、順序、required fields、artifact
   refs、session/build provenance；
2. **normalization** — 用 Observation Adapter 把 project log 轉成 canonical
   event stream；
3. **timeline reconstruction** — 依玩家時間組合 input、control、presentation、
   world response 和 state change，並能計算 cue／input／feedback 的時間距離；
4. **sequential blind projection** — 移除未來資訊、design ids／intent、hidden
   state，只逐步揭示玩家當刻可取得的 runtime evidence；
5. **evidence viewer／reader output** — 生成 AI 和人可閱讀的 timeline，能連回
   screenshot／video／audio／state evidence；
6. **acceptance comparison input** — 對每個 Beat Sheet acceptance kernel 提供
   可審計 evidence refs，但不預先替 reviewer 下結論；
7. **integrity report** — 缺資料、時鐘錯序、capture 遺失或無法重建時輸出
   `INCONCLUSIVE_EVIDENCE`，絕不可默認 PASS。

工具可以先由一個 reference implementation 開始；adapter 負責 project-specific
capture 和 mapping。Factory core 不得硬編某引擎的 scene、node、CSV 或 event
名稱。

### 6.5 Live run、recorded run 與 counterfactual coverage

一條錄好的 golden path 只能證明該路徑曾發生，不能證明 alternatives 真實、
可見和有不同後果。Observation subsystem 必須標示證據模式：

- `LIVE_BLIND_RUN`：fresh agent／human 實際控制 build；可驗 reception 和 action
  formation；
- `RECORDED_RUN`：讀既有 playthrough；可驗 observed path，不能單獨證明未選
  alternatives；
- `CONTROLLED_BRANCH_PROBE`：從同一 checkpoint／seed 測試 declared
  alternatives、failure、recovery 或不同 performance outcome；
- `STATIC_RUNTIME_ASSERTION`：只證明 mechanical state／reference integrity。

Decision beat 的 meaningful alternatives 至少需要 branch probe 或等價 runtime
evidence。Execution/mastery beat 若其 experience 依賴失敗後調整，至少要有能
區分 miss／partial／success 的 evidence。不能用一次順利完成的 run 證明整個
experience contract。

---

## 七、Adapters 與 ownership

Factory 出題與工具；project answers、logs、traces、captures 和 reports 全部
version／存放在 game repo。建議分成三個 project-owned answer surfaces：

1. **Project Gameplay Profile**
   - player verbs、systems、engagement／decision generators、rhythm axes、budgets、
     player frames、failure conventions、presentation capabilities。

2. **Production Adapter**
   - gameplay packet 如何落到 code／data／scene／asset／sound；
   - exact runtime validation、test／launch commands、state mappings。

3. **Observation Adapter**
   - 如何啟用 instrumentation；
   - raw log／capture locations 和 schema mapping；
   - 如何啟動可重現 session、checkpoint／seed／save；
   - camera／HUD／control／audio／spatial evidence 如何取得；
   - 哪些 acceptance kernels 暫時 `NOT_OBSERVABLE`。

若實作上選擇把 Observation Adapter 作為 `PRODUCTION_ADAPTER.md` 的 mandatory
section，亦可；但語義、ownership 和 completeness 必須獨立，不能用「已有測試
command」代替 observation contract。

Factory-owned：contract、blank templates、canonical log schema、reader tools、
step/review instructions。

Game-owned：filled adapters、Beat Sheets、walkthroughs、packets、raw logs、
captures、Observed Gameplay Traces、blind reports、acceptance reports、grammar／
experience state。

---

## 八、Runtime acceptance standard

### 8.1 Information-isolated roles

即使由同一個 foundation model 執行，以下角色亦必須使用 fresh context 和
file-only handoff：

1. **Experience author** — 產生／修訂 Beat Sheet；
2. **Realization author** — 寫 walkthrough／packets；
3. **Implementation caller** — 實作 runtime 和 instrumentation；
4. **Blind runtime player／reader** — 只見 actual sequential observations；
5. **Acceptance reviewer** — 讀鎖定的 design authority 與 blind observed report，
   只判定，不修內容。

Blind reader 不可看 Beat Sheet 名稱、moment／beat semantic ids、canonical action、
future frames、available-action enumeration、design intent、code 或 implementation
notes。Acceptance reviewer 不可把作者辯解當作 runtime evidence。

### 8.2 不比較唯一腳本，驗證 experience invariants

Factory 不應要求 observed run 與 Intended Player golden path 逐 action 相同。
合格 gameplay 容許合理 drift、不同路線、不同 performance 和 expression。

驗收單位是 Beat Sheet 的 acceptance kernel：

- 所需 cue／problem 是否在正確時間可取得；
- 玩家是否真的需要投入指定 work；
- declared agency／challenge source 是否在 runtime 成立；
- commitment 是否有實際 effect；
- world response 是否可辨識、及時並改變後續局面；
- intended player change 是否有公平接收條件，blind report 是否支持或合理偏離；
- carry-forward 是否由上一拍結果生成；
- curve、control ownership 和 presentation order 是否存活；
- red lines 是否被觸犯。

### 8.3 Verdicts and routing

- `PASS_FACTORY_CONFORMANCE` — 所需 evidence 完整，原初 experience 在允許 drift
  內由 runtime 兌現；仍標記 human playtest status。
- `FAIL_IMPLEMENTATION_FIDELITY` — approved design 有要求，runtime 沒有實現或
  被 code/data mapping 改寫；回 caller implementation。
- `FAIL_RECEPTION` — capability 存在，但 camera／HUD／control／cue／feedback
  令 blind player 無法形成原定 experience；回 presentation／level／UI／content。
- `FAIL_DESIGN` — implementation 忠於 source，但 source 本身沒有有效 player
  work、agency／challenge、response 或 carry-forward；回 Beat Sheet。
- `BLOCKED_BY_ADAPTER` — project capability／mapping 未交卷。
- `BLOCKED_BY_OBSERVABILITY` — 需要的 experience 無可靠 evidence path；回
  observation／production planning。
- `INCONCLUSIVE_EVIDENCE` — run／log／capture 不完整或污染；重跑，不得降級 PASS。
- `PENDING_HUMAN_PLAYTEST` — factory conformance 可通過，但 enjoyment／commercial
  value 尚未由 USER／真人確認。

每次 FAIL 必須指出第一個失去語義的 transformation boundary，而不是列出一堆
相鄰症狀。Review artifact 保留作 blocker record；修正後用 fresh reviewer 重跑。

---

## 九、Canonical artifact chain

建議的 game-owned artifacts：

```text
design/gameplay/
  adapter/
    PROJECT_GAMEPLAY_PROFILE.md
    PRODUCTION_ADAPTER.md
    OBSERVATION_ADAPTER.md          # 或 Production Adapter 的獨立 mandatory section
  experience_beat_sheets/
    <sheet_id>.md
  walkthroughs/<trace_id>/
    PLAYABLE_WALKTHROUGH_TRACE.md
    PAPER_BLIND_INPUT.md
    PAPER_BLIND_REPORT.md
  beat_packets/
    <packet_id>.md
  observation_plans/
    <packet_or_span_id>.md
  runtime_evidence/<run_id>/
    RAW_MANIFEST.md
    <project-native logs and captures>
    CANONICAL_EVENT_STREAM.*
    OBSERVED_GAMEPLAY_TRACE.md
    RUNTIME_BLIND_INPUT.md
    RUNTIME_BLIND_REPORT.md
  qa/
    <span_id>_DESIGN_REVIEW.md
    <span_id>_LANDING_REVIEW.md
    <span_id>_RUNTIME_ACCEPTANCE.md
  state/
    GAMEPLAY_GRAMMAR_STATE.md
    EXPERIENCE_LESSONS.md
```

確切檔名可在 contract 實作時調整，但 authority、observation 和 acceptance 三條
artifact lineage 不可混為一份自我證明文件。

---

## 十、Implementation phases

### Phase 0 — Contract correction and manual proof

- 新增 Gameplay Experience Beat Sheet contract／template／review；
- 讓現有 walkthrough／packet contract 改為綁定 Beat Sheet version；
- 新增 observation contract 和 adapter answer surface；
- 以一段真實 gameplay span 手工完成：Beat Sheet → walkthrough → packets →
  implementation mapping → actual evidence → manual normalized readback → acceptance；
- 用 pilot 修正 schema，而不是由 factory opinion 宣布穩定。

### Phase 1 — Reading-tool minimum viable implementation

- canonical log schema validator；
- 一個 project adapter 的 normalizer；
- timeline reconstruction；
- blind projection builder；
- evidence integrity report；
- 以至少一個 `LIVE_BLIND_RUN` 和一個 `CONTROLLED_BRANCH_PROBE` 驗證。

### Phase 2 — Story-like step machine

- 把已穩定的 manual workflow 固化成 step／`.5` review gates；
- one fresh worker per creative／review step；
- file-based resume、version binding、FAIL routing、honesty loop；
- 不把尚未經 pilot 證明的格式過早硬編進 CLI。

### Phase 3 — Cross-project proof

- 至少第二個 project／不同 gameplay shape 使用同一 core reader contract；
- engine-specific logging 只出現在 Observation Adapter／project integration；
- 驗證 decision、mastery／execution、discovery 中至少兩種不同 engagement mode，
  避免 factory 只適用於 objective／choice-heavy gameplay。

Document-first 仍可作格式探索策略，但「只有文件、沒有 reader」不再是 Factory
完成狀態。

---

## 十一、Acceptance criteria for this factory request

### Authority and authoring

- [ ] Gameplay Experience Beat Sheet contract、template、authoring module 和 fresh
      review gate 已落地。
- [ ] 強制規格與非強制 AI↔USER dialogue guidance 清楚分開。
- [ ] Sheet 有 version／authority status；walkthrough、packet、runtime acceptance
      全部綁定 exact sheet version。
- [ ] Auto mode 的 AI assumptions 不會被標成 USER ruling。

### Production and observability

- [ ] 每個 production packet 必須包含 observation contract；不可觀察的 packet
      fail closed。
- [ ] Project／Production／Observation adapter contracts 和 blank answer sheets
      完成，answers 留在 game repo。
- [ ] Canonical raw gameplay log schema 定義完成，禁止心理／評價欄位污染 raw log。
- [ ] Factory reader 能 validate、normalize、reconstruct timeline、build blind
      projection 和報 evidence integrity。
- [ ] Actual runtime run 的 evidence 可追溯到 build、save／seed、session 和 captures。

### Correct acceptance

- [ ] Blind runtime reader 的輸入只來自 actual runtime observation，不來自 design
      trace 的 `visible_and_known` 自述。
- [ ] Fresh acceptance reviewer 能逐 Beat Sheet acceptance kernel 指向實際 evidence，
      並在缺證時輸出 INCONCLUSIVE／BLOCKED，而不是猜 PASS。
- [ ] Alternatives、failure／recovery 或 performance-dependent experience 有
      counterfactual／controlled probe coverage；不以單一 golden path 代替。
- [ ] Verdict 能正確路由 design、implementation、reception、adapter、observability
      和 evidence failure。
- [ ] Factory pass 與 human playtest acceptance 明確分開。

### Workflow proof

- [ ] 一個真實 project span 完成完整 loop：Beat Sheet → design → implementation
      → runtime logging/readback → factory acceptance → failure routing／rerun。
- [ ] 至少一個故意植入的 reception 或 implementation mismatch 被 Factory 正確
      拒絕，證明 review 不是只會通過自己的產物。
- [ ] 第二個不同 gameplay shape 的 project／pilot 證明 core contract 可移植。
- [ ] 既有 story／asset／sound factory 行為未被 gameplay core 硬耦合或改寫。

只有以上 closure 通過，Gameplay Factory 才可標記 complete。

---

## 十二、Non-goals and hard invariants

- 不把 gameplay 縮窄成 explicit decision；操作、搜索、節奏、表達和 recovery
  都可成立，但必須有對應 engagement completeness。
- 不要求每個 moment 都有 alternatives；這會產生假選擇。
- 不把 objective completion、reward popup 或 state delta 當成 experience 已被
  接收的證明。
- 不從 code existence 推斷 player experience；actual runtime observation 必需。
- 不讓 raw logger 寫心理結論。
- 不讓 blind verifier 看到 design intent 或未來資料。
- 不把 verifier 的 alternate path 自動升格為 canonical design；它是 finding。
- 不讓 review worker 一邊修內容一邊替自己 PASS。
- 不把 project verbs、systems、engine hooks 或 log event names 寫死在 factory core。
- 不取代 human playtest；Factory 的責任是令人類收到的是被正確實作的原設計，
  並將結構性失敗提早、可追溯地暴露。

---

## References inside this umbrella

- `story/core/NARRATIVE_FOUNDATIONS.md`
- `story/modules/beat-sheet-dialogue/README.md`
- `story/modules/delivery-planner/README.md`
- `story/core/steps/chapter/STEP_6_75_STAGING_REVIEW.md`
- `story/core/steps/chapter/STEP_7_5_LANDING_INTEGRITY_REVIEW.md`
- `story/core/steps/chapter/STEP_9_STORY_AND_PROSE_QA.md`
- `gameplay/docs/PLAYABLE_WALKTHROUGH_TRACE_CONTRACT.md`（需按本 proposal 修訂）
- `gameplay/docs/PLAYABLE_BEAT_PACKET_CONTRACT.md`（需按本 proposal 修訂）
- `gameplay/docs/PROJECT_ADAPTER_CONTRACT.md`（需新增 observation ownership）

## Factory response

2026-07-19 factory-side foundation 已按本次 reframing 修正：Gameplay Experience
Beat Sheet authority／template／authoring review、exact-version lineage、四層 Beat
Packet、獨立 Observation Adapter、raw evidence schemas、runtime blind／acceptance
contracts，以及可 validate／normalize／reconstruct／blind-project／prepare
acceptance evidence 的 reference reader 已落地；詳見
`gameplay/docs/IMPLEMENTATION_STATUS.md`。

本 request **仍未完成**。本次 umbrella invocation 沒有指定可合法解析的 game repo
或 project id，因此按 adapter ownership／no-sibling-scanning 規則，Factory 沒有
虛構 Phase 0／1 pilot。尚欠：一個真實 span 的 actual build loop、實際
`LIVE_BLIND_RUN` + `CONTROLLED_BRANCH_PROBE`、故意 mismatch rejection、第二種
gameplay shape／project portability proof，以及其後才可穩定的 creative step
machine。Factory 不會以 synthetic reader tests 代替這些 closure evidence。
