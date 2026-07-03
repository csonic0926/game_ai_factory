# Story Attributes（western RPG 標準：屬性/技能/判定）

*以傳統 western RPG（D&D/CRPG）標準，設計並落地「屬性/技能/衍生值」在故事事件中的判定、代價、成功線/失敗線（fail-forward）；choice 條件欄位與 stats/flags 的實際編碼，依 adapter 的 `LANDING_SPEC.md` 落地。*

用在：你要做「故事選項會吃條件、會改變角色狀態/資源/屬性」，並遵循傳統 western RPG 的設計邏輯：
- 判定是 **核心屬性 → 衍生值 → 技能/特質 → 狀態/資源 → 關係與世界狀態** 疊加。
- **fail-forward**：失敗不是結束，而是換一種可玩的下文（受傷、破財、被記住、耗時、引來追兵…）。

專案現況（numeric stats、旗標系統、timeline choice 欄位的實際形態）依 adapter 的 `LANDING_SPEC.md` 與 `<BATTLE_SYSTEM>`（如有）確認後再落地。

這份 skill 提供兩種落地：
- **A. 相容模式**：專案已有核心屬性 numeric stats；技能/狀態/世界旗標先用 tags。
- **B. 完整模式（後續擴充）**：補齊 derived stats（stamina/mana/resistance）與技能 rank，讓判定更像 D&D/CRPG。

---

## 1) Western RPG 的事件判定標準（寫事件一律照這套）

### 1.1 檢定類型
- **DC 檢定**：`d20 + Skill + Attribute_mod + situational` vs `DC`
- **對抗檢定**：你 `d20 + Skill` vs 對手 `d20 + Skill`（或對手被動值）
- **資源換結果**：不骰（或失敗可補救），用 `gold/time/item/HP` 買下結果

### 1.2 DC 分級（內容製作的共同語感）
- `DC 5` 幾乎必成、`10` 容易、`15` 標準、`20` 困難、`25` 極難、`30` 傳說

### 1.3 成功程度（Degrees of success）
至少三段（越像 CRPG 越要有程度差）：
- **成功線**：乾淨、便宜、快、少尾巴（或多情報/更好開局）
- **代價線（fail-forward）**：也能做到，但付出可理解代價（HP/time/gold/tag）
- **壞失敗**（少用）：更大代價或引發戰鬥/追兵，但仍可玩、可回主線

### 1.4 UI 原則：提示風險，不提示算式
不要寫 `敏捷≥12`；要寫「你現在手腳慢半拍，硬闖會見血 / 會被記住」。

---

## 2) 完整屬性清單（Attributes）

### 2.1 核心屬性（6）
- **STR 力量**：推門、扛重物、掙脫束縛、近戰壓制、肉體威嚇
- **DEX 敏捷**：潛行、閃避、開鎖、扒竊、遠程命中、反應
- **CON 體質**：抗毒病、耐力、長途行動、撐刑、抗寒熱
- **INT 智力**：解謎、機關/工程、推理、知識理解、制定計畫
- **PER/WIS 感知**：察覺、追蹤、洞察、直覺、抗誘惑/精神干擾
- **CHA 魅力**：說服、交涉、欺瞞、表演、領導、收買人心

### 2.2 幸運（LUCK，可選但推薦）
- 用途：重擲/保底、壞結果偏移、暴擊/掉落/“意外”結果的微調
- 原則：不能取代技能；只用來「把壞失敗拉回代價線」或「讓成功線更好」

---

## 3) 衍生數值（Derived stats）與戰鬥用途（標準）

### 3.1 建議衍生值
- **HP / Wounds（生命/受傷）**：戰鬥生存；劇情代價首選
- **Stamina / Fatigue（體力/疲勞）**：追逐、翻越、連續行動；劇情=趕路代價
- **Mana/Qi（法力/內力）**：特殊能力資源；劇情=“硬撐”換結果
- **Accuracy / Evasion / Initiative（命中/閃避/先攻）**：戰鬥核心；劇情=射擊、追逐、反伏擊
- **Carry/Encumbrance（負重）**：帶走證物/財寶/傷患；劇情=撤離壓力
- **Resistances（抗性：毒/火/寒/電/精神）**：戰鬥與劇情（毒霧、恐懼、拷問）

### 3.2 Attributes → 戰鬥連動（你在設計上必須能說得出口）
- STR：近戰輸出、擒抱/破防
- DEX：命中、閃避、先攻
- CON：HP 上限、抗性、倒地門檻
- INT：弱點利用、技能效率、法術理論（依系統）
- PER/WIS：偵測伏擊、抗控場、反制欺瞞
- CHA：士氣、招降、同伴協同（可選）
- LUCK：暴擊/觸發率、壞結果偏移（可選）

---

## 4) 技能（Skills）清單（CRPG 常用，事件好寫）

技能是事件判定的主角；屬性主要提供加成或替代判定。

### 4.1 探索/犯罪
- Athletics（運動，STR/CON）
- Acrobatics（雜技，DEX）
- Stealth（潛行，DEX）
- Lockpicking（開鎖，DEX/INT）
- Traps（拆陷阱，PER/INT）
- Sleight of Hand（巧手，DEX）

### 4.2 社交/心理
- Persuasion（說服，CHA）
- Intimidation（威嚇，STR/CHA）
- Deception（欺瞞，CHA）
- Insight（洞察，PER/WIS）
- Streetwise（江湖/人脈，CHA/PER）

### 4.3 知識/專業
- Investigation（調查，INT/PER）
- Medicine（醫療，INT/WIS）
- Engineering（工程，INT）
- Arcana（奧術，INT）
- History（歷史，INT）
- Nature（自然，INT/WIS）
- Religion（宗教，INT/WIS）

### 4.4 生存/戰場
- Survival（生存/追蹤，WIS/PER）
- Perception（察覺，PER）
- Tactics（戰術，可選，INT/WIS）

### 4.5 技能等級（標準語感）
建議 rank 0–5（或 0–10）。rank 的典型用途：
- 解鎖「更乾淨的成功線」
- 同樣結果更省資源（更少 HP/time/gold）
- 提供額外情報（預警、弱點、看破）

---

## 5) 狀態（Status）與世界旗標（Flags）（事件成敗的常見真因）

### 5.1 Status（建議標準）
- 疲勞/飢餓/口渴/失眠：同一行動變貴、甚至改走代價線
- 中毒/流血/骨折/感染：特定行動高風險或不可用
- 恐懼/憤怒/沮喪：社交/理性判定受影響，或觸發衝動選項

### 5.2 Flags（世界狀態）
- 勢力聲望、同伴信任、是否被通緝、是否公開身份、是否拿到關鍵證據
- 原則：Flags 的權重通常應高於骰子（這才像 CRPG）

---

## 6) 落地（把 western RPG 標準映射到專案資料）

### 6.1 相容模式
- 將核心屬性（6+1）與 HP/金錢等衍生值，對應到專案既有的 numeric stats（實際對應表依 adapter 的 `LANDING_SPEC.md`）。
- 技能、狀態、世界旗標仍建議先用 tags 表達：
  - `trait.noble`、`background.thief`
  - `status.fatigued`、`status.bleeding`
  - `skill.lockpicking`（二元：有/沒有）
  - 勢力聲望/通緝之類的世界旗標（example：`faction.blackclad.rep_hostile`、`wanted.city_jianghu`）

事件設計照 western RPG：用 **成功線/代價線路由**，而不是用 disabled 卡死玩家。

### 6.2 完整模式（補齊 Skills/Derived）
若要真正做到「技能 rank + DC + 對抗 + 程度差」，你需要把 Attributes/Skills/Derived 變成可比較的 numeric stats（或新增技能系統）。

最低限度做法（延續目前架構；實際要改哪些 runtime 檔案、驗證腳本與 UI 翻譯 key，依 adapter 的 `LANDING_SPEC.md`）：
- 擴充 runtime 支援的 stat keys（attributes/derived/skills）
- 同步更新驗證工具的合法 stat 清單
- UI 顯示補齊翻譯 key

建議兩期上線：
- 一期：Attributes（6+1）數值化；skills 先用 tags 解鎖
- 二期：skills 做成 numeric rank + derived（stamina/mana/resistance），細做 DC/對抗/程度差

---

## 7) Choice 條件與效果欄位（依 adapter 落地）

事件列與選項需要能表達以下能力；實際欄位名與編碼，依 adapter 的 `LANDING_SPEC.md`。

### 7.1 每列事件的「被動效果」（揭露該列時自動套用）
- stat 變動（stat key + value）
- 效果顯示文案 key（不填會退回顯示 `+3 STAT` 類機械字串）

### 7.2 每個選項的「需求、代價線、效果、旗標」
每個選項需支援：
- required / forbidden tags
- required stat（stat key + 門檻值）
- fail-forward 代價線路由（失敗時導向的事件 id）
- 立即 stat 效果（按下選項立即變動）
- add / remove tags
- battle 觸發 id

---

## 8) 事件模板（western RPG 標準寫法）

### 8.1 同一個選項：成功線 vs 代價線（標準 fail-forward）
- 需求：選項的 required 條件（tags / stat 門檻）
- 成功線：選項的主路由事件
- 代價線：選項的 fail-forward 路由事件
- 代價落點：`health/gold`（或 stamina/mana）+ add tags（被記住/通緝/關係惡化）

### 8.2 加值選項（可消失，不影響主線）
只有加值選項才允許「不滿足就 disabled」；主線必要選項一律走 fail-forward。

---

## 9) 檢核表（寫完必看）
- 每個需要屬性的主線選項是否都有 fail-forward 代價線路由？
- 代價線是否能回到主線壓力鍋（不是死胡同）？
- 每個代價是否有敘事理由（玩家覺得公平）？
- 效果顯示文案 key 是否存在於 runtime locale 資料？

---

## 10) 驗證工具
依 adapter `LANDING_SPEC.md` 的 integrity checklist 執行機械驗證：
- stat key / value 的合法性
- 選項 required / effect 欄位的合法性

---

## Reference implementation: event-timeline CSV runtime (rpg-1 heritage)

> 以下是本文件原始 rpg-1 版本的具體落地細節，僅作為 worked example 保留。
> 真實專案一律依各自 adapter 的 `LANDING_SPEC.md` 落地。

### 專案現況（rpg-1）
- Numeric stats：`strength`, `intelligence`, `agility`, `constitution`, `perception`, `charisma`, `luck`, `health`, `gold`（`gd/Globals.gd`）
- Tags：`Globals.event_tags`（字串旗標）
- Story timeline：`settings/event_timelines.csv`（choice 支援需求/代價線/效果/旗標/戰鬥）

### 6.1 相容模式的屬性對應
- `strength` ≈ STR
- `agility` ≈ DEX
- `intelligence` ≈ INT
- `constitution` ≈ CON
- `perception` ≈ PER/WIS
- `charisma` ≈ CHA
- `luck` ≈ LUCK
- `health` ≈ HP（衍生值）
- `gold` ≈ 金錢資源

### 6.2 完整模式的最低限度做法
- 在 `gd/Globals.gd` 擴充支援的 stat keys（attributes/derived/skills）
- 同步更新 `scripts/validate_settings.py` 的 `SUPPORTED_STATS`
- UI 顯示補齊翻譯 key（例如 `STAT_CON`、`STAT_CHA`、`STAT_LUCK`）

### 7) CSV 欄位（settings/event_timelines.csv）

每列事件的「被動效果」（揭露該列時自動套用）：
- `stat_key` / `stat_value`
- `effect_display_key`（不填會退回顯示 `+3 STAT` 類機械字串）

每個選項的「需求、代價線、效果、旗標」，對 `choice_1` ~ `choice_4`：
- `choice_N_required_tags` / `choice_N_forbidden_tags`（用 `;` 分隔）
- `choice_N_required_stat_key` / `choice_N_required_stat_value`
- `choice_N_fail_event_id`（fail-forward 代價線）
- `choice_N_effect_stat` / `choice_N_effect_amount`（按下選項立即變動）
- `choice_N_add_tags` / `choice_N_remove_tags`
- `choice_N_battle_id`

註：rpg-1 的 CSV loader 不支援引號與逗號 escaping，所以 tag 清單用 `;` 分隔，欄位內不要放逗號。

### 8.1 事件模板的欄位對應
- 需求：`choice_N_required_*`
- 成功線：`choice_N_event_id`
- 代價線：`choice_N_fail_event_id`

### 9) 檢核
- `effect_display_key` 是否存在於 `locales/locales.csv`？

### 10) 驗證工具
跑：`python3 scripts/validate_settings.py`
- 會檢查 `stat_key/stat_value` 與 `choice_N_required_stat_*` / `choice_N_effect_*` 的合法性。
