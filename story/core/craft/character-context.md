# Character Context Cards

*Loads character JSON from `<STORY_ROOT>/state/characters/` and outputs character context cards (with hard boundaries) for writing and battle design. Use mid-reasoning whenever dialogue, actions, or battle constraints must align with a character's voice, taboos, and limits.*

目的：在創作或戰鬥設計的「思考中途」快速讀取 `<STORY_ROOT>/state/characters/` 底下的角色人設 JSON（`ch_*.json`，不含 `*.memory.json`），輸出可直接貼進上層推理的角色卡（含硬邊界）。

## 何時使用

- 你正在寫任何角色對白/行動，但需要先對齊該角色的 `voice/taboos/core`。
- 你正在設計戰鬥或事件條件，需要把角色的 `limits/pressure_points/hooks` 轉成設計約束。
- 使用者只給了角色名、外號、或不確定 ID，需要先解析成角色檔案。

## 輸入（盡量最少）

請先向使用者取得（若已提供則略過）：

- `characters`: Array[String]（角色 `id` / `name` / `aliases` 任一皆可）
- `mode`: `"writer"` | `"battle"` | `"both"`（預設 `"writer"`）
- `scene_hint`: String（可選；一句話即可；預設空字串）

## 資料來源

優先讀取：

- `<STORY_ROOT>/state/characters/index.json` 的 `name_or_alias_to_id` 映射（若存在）
- 再讀取對應的 `<STORY_ROOT>/state/characters/ch_<id>.json`

若 `<STORY_ROOT>/state/characters/index.json` 不存在或查無結果：

- 以 `<STORY_ROOT>/state/characters/ch_*.json` 掃描 `id/name/aliases` 嘗試匹配（需排除 `*.memory.json`）
- 若仍不確定，回傳 `needs_clarification`，列出候選（不得猜測）

## 輸出格式（給上層技能拼裝）

請輸出一個 JSON 物件（不是角色檔本體），固定欄位如下：

```json
{
  "resolved": [
    {
      "input": "",
      "id": "",
      "path": "",
      "confidence": "high|medium|low",
      "notes": ""
    }
  ],
  "writer_card": [
    {
      "id": "",
      "identity": { "public_face": "", "private_truth": "", "social_mask": "" },
      "core": { "drives": [], "fears": [], "values_ordered": [], "nonnegotiables": [] },
      "voice": {
        "tone": "",
        "speech_clarity": "",
        "sentence_length": "",
        "default_posture": "",
        "preferred_speech_acts": [],
        "avoidances": []
      },
      "hard_constraints": {
        "nonnegotiables": [],
        "avoidances": []
      },
      "baseline_relationships": [],
      "hooks": [],
      "pressure_points": [],
      "secrets": [],
      "assumptions": []
    }
  ],
  "battle_card": [
    {
      "id": "",
      "capabilities": { "combat": "", "resources": "", "limits": [] },
      "design_constraints": [],
      "pressure_points": []
    }
  ],
  "needs_clarification": [
    { "input": "", "candidates": [], "question": "" }
  ],
  "scene_hint_used": ""
}
```

### `writer_card` 的規則

- 只摘錄角色 JSON 的原始內容；不得擅自補設定。
- 任何推導或補齊一律放在 `assumptions`，且要保留其「可被推翻」性。
- `hard_constraints` 必須直接對應 `core.nonnegotiables` 與 `voice.avoidances`（不可省略）。
- `secrets` 只保留「觸發條件」與「曝光風險」，不要替劇情下結論。

### `battle_card` 的規則

- 只從 `capabilities`、`pressure_points`、`core.nonnegotiables`、`voice.avoidances` 轉成「設計約束」。
- `design_constraints` 用可檢查的句子描述（例如：不得安排其在眾目睽睽下長篇自述；不得設計成戀戰型 AI）。
- 不產生具體數值；若需要數值，回到上層戰鬥設計流程處理。

## 注意事項

- 若使用者給的是 runtime locale key（例如 `scholar_girl_option_2`；實際存放位置見 adapter `LANDING_SPEC.md`），本流程只負責角色卡，不負責查 key 的內容；應要求使用者貼出文本或由上層先解析文本再決定要讀哪個角色。
- 若 `scene_hint` 為空，輸出仍必須完整（至少 `hard_constraints/hooks/pressure_points`）。
