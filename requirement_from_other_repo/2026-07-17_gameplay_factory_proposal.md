# Cross-repo factory request — 新建第四個 sub-factory：`gameplay/`（Gameplay Factory）

## Request metadata

- Status: in_progress（factory foundation complete；portable onboarding 已修正，Phase 0 pilot 待執行）
- Date: 2026-07-17
- Source repo: n/a — umbrella 級結構提案（非單一 game repo 的功能需求）
- Request owner: USER；設計定案來自 2026-07-17 USER × Claude × Codex 三方討論
- Factory target area: umbrella（新 sub-factory，不屬於 asset/story/sound 任何一個）
- Priority: normal

> 放在 umbrella 頂層 intake 的原因：現有三個 `requirement_from_other_repo/`
> 都是 per-factory 的；本 request 是結構級——在 umbrella 下新建一個 factory。
>
> **通用性約束**：Gameplay Factory 與 asset/story/sound 一樣是 project-agnostic
> 的。本文件中出現的任何示例（動詞、delta、trace 段落）皆為討論中的示意，
> 不綁定任何專案；專案內容一律經 project adapter 答卷進入（見 D6）。

## User-facing need（真空診斷）

現時 factory stack 有一個真空層：

| 層 | 回答的問題 | 現狀 |
| --- | --- | --- |
| Story factory | 接下來**發生**甚麼 | 已有（`story/`） |
| **Gameplay factory** | 玩家要**怎樣親手經歷**它 | **真空** |
| Production（asset/sound/game code） | 把已決定的玩法**實作**出來 | 已有 |

一個 story beat（例如「主角沿多年固定路線前往下一個補給點」）不能直接成為
遊戲。中間缺一層翻譯：遠目標→當下目標→玩家動詞→世界回應→意義補完→
下一拍交接。這層翻譯目前在 caller 專案裡由人在對話中 ad hoc 補上——
不被記錄、不可重複、不跨 project。

而 caller 專案的生產經驗顯示，實作後的返工幾乎全部集中在**接收層**：
任務提示看不到、對白放錯 presentation、cutscene 主角出鏡、AVG 沒隱藏
HUD——表面是 UI bug，實質是「這一拍沒有被玩家正確接收到」。
（具體實證案例 version 在各 game repo，依 umbrella 原則不入 factory 文件；
caller 專案可在自己的 adapter 答卷或後續 request 附上。）

Gameplay Factory 要把這層翻譯變成有格式、有驗收、可重複、跨專案通用的
生產工序。

## 核心設計決定（三方討論已定案，factory 實作時不要重開）

### D1 — Walkthrough-first，不是逐對 story beat 填空

Factory 的第一生成物是一條**連續的 Playable Walkthrough Trace**：LLM 沿玩家
實際時間「玩完整段遊戲」。不要逐對處理 Story Beat A→B 填空。

理由：填空是 constraint satisfaction，LLM 會產生局部合理的膠水
（去某處→按互動→看對話），每段成立、整體不像有人在玩。連續 rollout 是
autoregressive model 的本性所長，只有它才會自然照顧：剛打完不應再戰鬥、
連續兩次走路需要換動詞、剛交還控制不能兩秒後再奪走、某個 story anchor
應該延後讓玩家先產生疑問。

Factory 核心能力因此不是 "game design generation"，而是：
**維持玩家視角與時間連續性的長程 rollout**。

### D2 — Beat 由 trace 切割浮現；切割準則 = player-state delta detection

Beat 不是人工在 outline 上切段。以下任一 player-state delta 出現即為候選
beat 邊界：

- 玩家意圖改變
- 核心動詞改變
- 控制模式改變（自由操作 ↔ cutscene/AVG ↔ 戰鬥）
- 新資訊改寫玩家理解
- 一個期待獲得 payoff
- 遊戲把玩家交到下一個局面

### D3 — State delta 四類；player_knowledge_delta 是正式欄位

```
runtime_delta           # 程式可精確驗證的世界/系統狀態變化（樓層、任務階段、flag…）
world_delta             # 敘事世界層面的變化（角色位置、事件推進…）
player_knowledge_delta  # 玩家理解了甚麼新東西
player_affect_delta     # 玩家情緒/節奏感受的轉變
```

前兩類可被程式精確驗證，做 runtime 驗收 metadata。後兩類不可證明玩家
「一定接收到」，改行 **reception contract**（見 D5 的 Proof）：系統證明自己
提供了足夠清晰、公平、互不干擾的接收條件。

`player_knowledge_delta` 必須是 trace moment 的正式欄位，不是設計備註——
否則 factory 會做齊所有 runtime state，卻再次產出「所有 step 都對，但沒有
在玩遊戲的感受」。

State delta 不是主要創作引擎；它的四個崗位：story anchors 的必要限制、
walkthrough 連續性檢查、beat 切割訊號（D2）、runtime 驗收 metadata。

### D4 — 兩個玩家角色：generator / verifier，且 verifier 必須 blinded

1. **Intended Player**（author）：能自然讀懂提示、沿設計預期路線前進，寫出
   golden path。這是 canonical trace——production 只能由它 compile。
2. **First-time Player**（verifier）：重跑 trace，模擬遲疑、漏看 UI、走錯路、
   誤解 affordance，在**紙面階段**暴露接收失敗（任務看不到、鏡頭沒拍到、
   控制權混亂），把這類返工從 implement 後推前到 implement 前。

**硬性規則（blinding）**：verifier 只能讀 trace 中「玩家看得見／知道甚麼」
的欄位，設計意圖一個字都不給。理由：兩個角色都是 LLM、priors 相關，見到
設計意圖就永遠「看得懂」提示，驗證即失效。這條規則反過來決定 trace 格式：
**「設計想怎樣」與「畫面上實際有甚麼」必須是嚴格分開的欄位**。

即使 blinded，simulated player ≠ 真人。人類 playtest 是最終 gate，
First-time Player 只是平價前濾。

### D5 — 最小語義核心：Delta → Delivery → Proof

Gameplay Factory 對每個 delta 的工作：選擇 delivery mechanism
（由玩家親手造成 / 由玩家目擊 / 暗場帶過），並附上 Proof——對
knowledge/affect delta 而言 Proof 即 reception contract：

- 必要資訊玩家是否看得見
- Camera 是否框住關鍵對象
- HUD 是否干擾 presentation
- 控制權何時被接管、何時歸還
- 對白、objective 與完成回饋是否按正確次序出現

某個 delta 在目前系統、budget 或節奏下無法交付時，回傳 constraint failure
（不是「否決權」這種政治結構）：

```
unresolved_delta:
  reason: ...
  required_capability_or_story_revision: ...
```

### D6 — 三層 adapter，沿用 story factory 契約先例

- **Factory core**（project-agnostic）：delta 分解、delivery 選擇、節奏
  ledger、budget、完整性檢查、blinding 規則。
- **Project gameplay adapter**（每專案一份答卷）：這款遊戲有哪些玩家動詞、
  系統、presentation 模式、資產能力、每拍 budget。動詞清單完全屬於答卷，
  factory core 不得內建任何專案的動詞。
- **Production adapter**（每專案一份答卷）：怎樣落地到目標 repo 的引擎與
  資料格式。

契約歸屬照 `story/docs/PROJECT_PROFILE_CONTRACT.md` 與
`ADAPTER_FILES_MOVE_TO_GAME_REPO_REQUEST.md` 的定案先例：**factory 出題
（契約 + 空白答卷模板），答案檔住在 game repo** 的固定
`design/gameplay/adapter/`。Game repo 由呼叫參數或 cwd Git root 解析；只有
從 factory cwd 以 `project_id` 呼叫時，才可使用 ignored 的本機 registry。

### D7 — Document-first：工具由穩定格式長出來

先以手寫文件驗證格式能否承受真實設計，通過兩三個 beat 之後才考慮
step machine / skill / CLI。禁止一開始就起工具。

## Pipeline（目標形態）

```
Story anchors（story factory 產出的必要 state deltas + 因果限制）
＋ 目前世界狀態
＋ Project gameplay adapter（verbs / systems / presentation / budget）
＋ Gameplay grammar state（最近動詞、節奏位置、玩家知識 ledger）
        ↓
LLM 連續 rollout（Intended Player）
        ↓
Playable Walkthrough Trace（moment-level，玩家時間）
        ↓                          ↘
Beat segmentation（D2）            First-time Player blinded 重跑（D4）
        ↓                          ↙ reception failures 回修 trace
Playable Beat Packets
        ↓
Production factories（asset / sound / game code）→ Runtime
        ↓
runtime_delta 驗收 + reception contract 驗收
（unresolved_delta 隨時可回傳 story factory）
```

## Artifact 規格 v0（供 factory 迭代，不是最終版）

### Playable Walkthrough Trace — moment schema

每個 moment 至少含：

```
- player_intent        玩家目前想做甚麼
- visible_and_known    玩家看得見／知道甚麼        ← blinded verifier 唯一可讀來源
- available_actions    玩家有哪些可用動作
- action_taken         玩家實際選了甚麼
- game_response        遊戲如何立即回應
- knowledge_update     玩家因此重新理解了甚麼（player_knowledge_delta 落點）
- control_owner        控制權現在屬於誰
- design_intent        設計想達成甚麼               ← 與上面嚴格分離（D4）
```

書寫形態傾向兩 pass：先 prose rollout（保持模擬質地），再結構化 annotation
（供切割與 compile）——見 Open question O4。

Trace 質地示例（僅示意顆粒度，取自定案討論的一段範例，不綁定專案）：

> AVG 結束，控制權回到玩家。畫面出現「找到前往下一層的傳送門」。玩家沿
> 未走過的通道前進，遠處先看到紫色光源——而不是立即知道那是傳送門。走近、
> 確認可互動、接觸後角色停下，音效光效回應，控制權短暫接管。切換到下一層。
> 玩家尚未移動，AVG 已開始，主角才提到這是自己多年巡迴的舊路。AVG 結束，
> 目標更新。

重點在顆粒度：不是 plot summary（「玩家找到傳送門，前往下一層」），而是
沿玩家實際時間、逐 moment 記錄看見／理解／行動／回應／控制權。

### Playable Beat Packet

1. **Experience beat** — 這一拍要讓玩家感受到甚麼。
2. **Player-action beat** — 玩家看見甚麼、理解甚麼、親手做甚麼、得到甚麼回應。
3. **Runtime contract** — trigger、控制權、camera、dialogue presentation、
   objective、state transition、completion feedback、驗收條件
   （含 reception contract 檢查表，見 D5）。

### Gameplay grammar state（persistent，隨 project 演進，per-project 存放）

最近使用過的動詞（避免連續重複同一互動形態）、目前節奏位置（探索／戰鬥／
休息／其他，節奏軸由 project adapter 定義）、玩家此刻知道甚麼缺甚麼期待
甚麼、每拍允許的複雜度／長度／成本、完成回饋與交接慣例。

## Phase 0 — first job（以呼叫時明示的專案為 pilot，全人手、零工具）

Pilot 專案由 caller 明示 game repo，或由該 game repo 的 cwd Git root 決定；
factory 的 versioned 文件不指定專案。

1. 取該專案 story factory 已產出的下一段 story anchors，手寫一條連續 trace。
2. 用 D2 準則切拍，檢驗 Beat Packet 是否自然跌出來。
3. First-time Player blinded 重跑（另開 fresh session，只餵
   `visible_and_known` 欄位），記錄 reception failures。
4. 把 USER 對 trace 的 reject 反應記錄成「真正玩遊戲」rubric 的首批條目
   （見 O1——這是整個系統的 eval function，只能從人類判斷中採集）。
5. 依結果修訂 artifact 規格；累積兩三個 beat 的先例後，才評估 step machine。

## Acceptance criteria（本 request 完成的定義）

- [x] `gameplay/` sub-factory 目錄建立，含 `AGENTS.md` 與 caller landing 文件。
- [x] Trace / Beat Packet / adapter 三份契約文件 v0 落地（含 D1–D7 的決定，
      標明哪些已定案、哪些是 open question），全部 project-agnostic。
- [x] Adapter 解析規則遵守 ownership boundary（契約在 factory、答案檔在
      game repo；explicit game repo → cwd Git root → ignored local registry）；
      空白答卷模板就緒。
- [ ] Phase 0 以首個登記的 caller 專案走通一次（人手模式），trace 與切割
      結果存檔為首個先例（存於該 game repo，不入 factory）。
- [x] 頂層 `README.md` 與 `AI_CALLER_LANDING.md` 由三 factory 更新為四 factory。
- [x] asset/story/sound 現有行為與契約零改動。

## Open questions（本 request 明確不假裝已解決的位）

- **O1 —「真正玩遊戲」eval rubric**：判斷一條 walkthrough「像不像有人在玩」
  的具體 reject 訊號，目前只存在人類直覺中。經 Phase 0 review 逐步採集，
  不要由 factory 自行發明。
- **O2 — `player_affect_delta` 的正式化程度**：傾向 beat-level intent
  （切割與節奏的目標），而非 per-moment 可證欄位；待 Phase 0 驗證。
- **O3 — First-time Player 的漂移範圍**：模擬多少迷路／誤判（golden path
  鄰域多寬），參數由首次紙面重跑校準。
- **O4 — trace 書寫形態**：prose-first 再 annotation，還是 structured-first。
  傾向前者（兩 pass），待 Phase 0 用真實內容裁決。
- **O5 — 與 story factory 的邊界**：`story/core/craft/cutscene-staging.md`
  目前住在 story 側；Beat Packet 內 presentation 責任誰屬，需在契約 v0 講清。

## Non-goals / do-not-change

- **不是任務填充機**：不是每兩個 story beat 之間都必須塞 gameplay。Factory
  有權判斷：這裡需要完整 gameplay／只需一次小互動／不應打斷劇情／這個
  story beat 應拆開讓一半由玩家造成。
- **不取代人類 playtest**：simulated First-time Player 是前濾，人類 playtest
  是最終 gate。
- **不內建任何專案內容**：動詞、系統、節奏軸、budget 全部經 adapter 答卷
  進入；factory core 出現專案專屬內容即為 bug。
- Phase 0 不建任何 CLI、step machine、skill。
- 不改動 asset / story / sound 三個現有 factory 的行為與契約。
- Factory 產物不落在 umbrella 下——trace、packet、grammar state、adapter
  答案檔全部 version 在各 game repo（沿用本 repo 設計原則）。

## References and source context

- `story/docs/PROJECT_PROFILE_CONTRACT.md` — adapter 契約先例
- `gameplay/adapters/registry.example.md` — ignored 本機電話簿格式
- `story/requirement_from_other_repo/ADAPTER_FILES_MOVE_TO_GAME_REPO_REQUEST.md`
  — 「factory 出題、game repo 交卷」的定案先例
- `story/core/craft/cutscene-staging.md` — O5 邊界問題的相鄰文件
- 各 caller 專案的實證案例（接收層返工紀錄等）由該 game repo 自行提供，
  隨其 adapter 答卷或後續 per-project request 附上。

## Factory response

Factory Codex 處理後填寫。

- Status: blocked
- Summary: Gameplay Factory 的 Phase 0 document-first foundation 已建立；D1–D7、
  O1–O5、Delta → Delivery → Proof、blinded verifier、story/gameplay/production
  邊界與 state/causality invariants 已落到三份 v0 契約。六項 acceptance criteria
  已完成五項；未在沒有 caller 答卷的情況下虛構 pilot。
- Commands run:
  - `sed` / `find` / `grep` / `git status`：閱讀 intake、umbrella landing、story
    adapter 先例與相鄰 cutscene contract，並檢查工作樹。
  - Python document audit：驗證 D1–D7、8 個 moment 必填欄、4 類 delta、6 個
    segmentation signals、blinding exclusions、canonical-source invariant、O1–O5、
    adapter resolution order，及全部本地 Markdown links。
  - `git diff --check`、existing-factory diff guard、backup-artifact guard。
- Changed files:
  - Umbrella: `AGENTS.md`, `README.md`, `AI_CALLER_LANDING.md`。
  - New factory entry: `gameplay/AGENTS.md`, `gameplay/README.md`,
    `gameplay/docs/AI_CALLER_LANDING.md`。
  - Contracts: `gameplay/docs/PLAYABLE_WALKTHROUGH_TRACE_CONTRACT.md`,
    `gameplay/docs/PLAYABLE_BEAT_PACKET_CONTRACT.md`,
    `gameplay/docs/PROJECT_ADAPTER_CONTRACT.md`。
  - Adapter local-routing example/templates: `gameplay/adapters/registry.example.md`,
    `gameplay/adapters/_template/PROJECT_GAMEPLAY_PROFILE.md`,
    `gameplay/adapters/_template/PRODUCTION_ADAPTER.md`。
  - Artifact templates: `gameplay/templates/PLAYABLE_WALKTHROUGH_TRACE.md`,
    `PLAYABLE_BEAT_PACKET.md`, `GAMEPLAY_GRAMMAR_STATE.md`,
    `FIRST_TIME_PLAYER_INPUT.md`, `FIRST_TIME_PLAYER_REPORT.md`,
    `RECEPTION_REVIEW.md`。
  - This intake response.
- Outputs / run roots: none；本案目前只有 factory contracts/templates，沒有把
  project output 寫進 umbrella。
- Blockers or follow-up: factory foundation 不再依賴 committed project
  registration；caller 必須明示 game repo 或從其 cwd 呼叫。首個 game-owned
  gameplay adapter 已可依固定 `design/gameplay/adapter/` 位置解析，但 Phase 0
  trace／切割／blinded rerun 尚未執行，因此本 request 仍未標記 done。D6 仍
  禁止從 Story Factory registry 猜 project 或代填 project capabilities。
  未建立任何 backup artifact。
