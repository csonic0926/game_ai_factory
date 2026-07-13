# Story Factory — 流程缺陷清單（ENTRY_LANDING 驗證跑，2026-07-07）

> 來源：以隔離 sub-agent 跑 CHAPTER pipeline（STEP 1–6＋各 .5，STEP 7 依約停關卡）
> 生產 vinci_world `ENTRY_LANDING` beat sheet 第 1–4 拍。這輪的目的就是驗證
> 生產流程是否理想；設計鏈（STEP 1–6）本身健康，以下是暴露出來的三個缺陷，
> 由重到輕。前兩個是 factory core 的結構問題（要在 tools/game_ai_factory 修），
> 第三個是本輪已臨時補救、但根因仍在 core。

---

## BUG 1（高）— 上游改動不會使下游 artifact 失效：beat sheet 改了，delivery plan 沒被擋

**現象**：`ENTRY_LANDING_BEAT_SHEET.md` 經過多次 USER 改定（第 1、2 拍換人、
新增第 3.5 拍），但 `ENTRY_LANDING_DELIVERY_PLAN.md` 停在改定前的舊拍，且缺
第 3.5 拍。STEP 2（assignment 模式）把 delivery plan 當 binding input 讀——
若沒人察覺，STEP 2 會照**過時的**渠道分配往下走，整條鏈長在錯的地基上。

**根因**：`beat-sheet-dialogue`（產 beat sheet）與 `delivery-planner`（產 delivery
plan）兩個模組之間，沒有「上游更新 → 下游失效」的連動機制。delivery plan 不
記錄它是根據 beat sheet 的哪一版產的，pipeline 也不比對兩者是否同步。

**建議修法**（擇一或並用）：
1. **版本印記 + 前置檢查**：delivery plan 的 header 記錄「based on beat sheet
   修訂記錄的最後一條日期／雜湊」。STEP 1（preflight）或 STEP 2 開頭比對
   beat sheet 現行版本與 delivery plan 記錄的版本；不一致即 FAIL，要求先
   重跑 delivery-planner，不得靜默沿用。
2. **beat sheet 的修訂協定加一條**：任何 beat 改定後，同一次 interactive
   session 內必須連帶重跑 delivery-planner（或至少標記 delivery plan STALE）。
   寫進 `modules/beat-sheet-dialogue/README.md` 的 Phase 3 與 Revision 段。
3. **delivery-planner 的 README 補「輸入版本綁定」小節**：明列它綁的是哪一版
   beat sheet，並要求輸出 header 落章此綁定。

**落點檔案**：`core/steps/chapter/STEP_1_CHAPTER_PREFLIGHT.md`（加同步檢查）、
`core/steps/chapter/STEP_2_STORY_LINE_DISCOVERY.md`（讀 delivery plan 前先驗
版本）、`modules/beat-sheet-dialogue/README.md`、`modules/delivery-planner/README.md`。

---

## BUG 2（高）— 落地面存在性驗得太晚：到 STEP 7 才撞牆

**現象**：ENTRY_LANDING 第 1–4 拍需要「渡船場景」與「重做的碼頭場景」，但目標
runtime 的 `CutsceneScene` 只有 village/town_hall/house。設計鏈 STEP 1–6 完全
不受影響、照常產出漂亮的劇本，一路到 STEP 7 落地才發現一大半 BLOCKED_BY_PROFILE。
等於「beat sheet 可以定案一條現行 runtime 完全承接不了的走廊，而工廠要到最後
一步才知道」。

**根因**：STEP 1 preflight 沒有把「這條 beat sheet 需要的落地面／runtime 能力
是否存在」列為必查項。落地面存在性只在 STEP 7 才隱含地被撞出來。

**建議修法**：STEP 1 preflight 新增一項必查——**落地面盤點**。對照 beat sheet
（或其 delivery plan）需要的場景／渠道／runtime 能力，逐項標「現成／需工程新建
（engineering dependency）／後備方案」。凡有「需工程新建」項，preflight 產出
一張明確的工程相依清單，並在報告裡標這條 beat sheet 是「設計可跑、落地待工程」，
讓 USER 在投入 STEP 2–6 前就知道落地缺口，而不是產完劇本才發現不能上。
（注意：這不阻擋設計鏈——設計本來就該能先於工程跑；只是把缺口前移到看得見。）

**落點檔案**：`core/steps/chapter/STEP_1_CHAPTER_PREFLIGHT.md`、
`core/steps/chapter/STEP_1_5_PREFLIGHT_REVIEW.md`（審查閘加驗這張清單存在）。
渠道清單的權威在 adapter `DELIVERY_CHANNELS.md`＋目標 runtime 的實際 enum，
preflight 應被指示去讀這兩者、不得憑空假設場景存在。

---

## BUG 3（中）— beat 改寫時「情感 → 渠道」重新指派容易被漏

**現象**：第 1 拍由「同航的人（聊天）」改定為「船上放開控制、玩家自己走到船頭」，
情感核心從「聽別人說」變成「自己移動」——渠道也應從 NPC 對話改成任務/自走。
舊 delivery plan 沒跟著改，仍掛在 NPC 對話。本輪重核已改正，但這類「改了畫面
卻沒改渠道」的漏，目前沒有機制擋。

**根因**：與 BUG 1 同源（模組不連動），但更細一層：即使有人記得重跑
delivery-planner，也需要一條明確準則提醒「畫面的情感一變，主渠道要重新判定，
不能沿用舊渠道」。

**建議修法**：`modules/delivery-planner/README.md` 加一條判定準則——**渠道由該拍
的情感交付方式決定，不由畫面題材決定**；重核既有 delivery plan 時，逐拍重問
「這一拍的情感是靠誰交付（玩家自己動作／某人開口／場景擺設／物件文字）」，
答案變了就換渠道。可附本例（自己走 vs 聽人說）作判例。

**落點檔案**：`modules/delivery-planner/README.md`。

---

## 附：本輪未觸及、但相鄰的兩個既有機制（非 bug，供修 core 時一併看）

- STEP 7 的 USER 劇本放行硬關卡（LANDING_SPEC Surface 2）運作正常——auto 模式
  正確停在此、只產草稿不落 game repo。無需改。
- dialogue-runway craft 正確回報 BLOCKED_ON_USER_CUT、不代選——分工乾淨。無需改。

## 相關產物路徑（在 vinci_world repo，供交叉參照）

- beat sheet：`design/story/beat_sheets/ENTRY_LANDING_BEAT_SHEET.md`
- delivery plan（已補救到第三版）：`design/story/state/chapter_sources/ENTRY_LANDING_DELIVERY_PLAN.md`
- 本輪 pipeline 產物：`design/story/state/chapter_sources/ENTRY_LANDING_*`、
  `design/story/chapter_event_graphs/ENTRY_LANDING.md`、
  `design/story/runtime_scene_drafts/ENTRY_LANDING_zh.md`、
  `.../ENTRY_LANDING_BEAT2_DIALOGUE_RUNWAYS.md`、`.../ENTRY_LANDING_LANDING.md`
