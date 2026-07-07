# STORY 部門重建計畫（REBUILD PLAN）

> 位置說明：本檔放在 game_ai_factory 傘級目錄，因為這是「AI 工廠重建 story 部門」
> 的計畫，不是 story 部門內部的一次修補。
>
> 緣起：2026-07-06～07-07 與 USER 在 vinci_world 上重做 world entry / landing 的
> 創作過程，暴露出現有 story factory 的結構性缺陷。這份計畫由那次過程的逐步
> 發現寫成；每一節先講「發現了什麼」，再講「因此要改什麼」。
>
> 狀態：USER 已核可方向（2026-07-07）。動工順序見文末。

---

## 一、診斷：有系統、沒故事

現有管線（WORLD → CHARACTER → CAST → CHAPTER，每步配 .5 審查閘）的上游輸入
只有三樣：世界基線（digital twin）、WORKFLOW_CORE_VARIABLES（USER 定案）、
adapter 落地規格。這三樣分別回答「世界怎麼運作」「哪些紅線不能碰」「怎麼落到
遊戲裡」。**「這個故事要傳播什麼情感」在任何一份輸入裡都沒有位置。**

審查閘全部是往上游驗真：語意保真、canon 一致、形式合格。驗真的前提是上游有
一個「真」可以對——當最上游沒有情感目標，閘能保證的就只是「精緻地不出錯」。
vinci_world CH1 是證據：canon 全對、工藝合格，但抽掉整章，玩家心裡沒有哪一點
不可逆地變了。

## 二、創作過程中定下的地基（vinci_world 的判例，方法論通用）

以下五條是那次對談逐步砍出來的結論。前三條是**通用方法論**，進 factory core；
後兩條是 vinci_world 的世界定案，進該 adapter 與遊戲 repo 的主權檔。

1. **情感是核心，token 分兩種。**能「傳播」情感的 token，說出口對方胸口先動
   一下（例：「媽媽大掃除把整盒卡丟了」「零用錢只夠買一包，在店門口站了很久
   才拆」）；只能「承載」情感的 token 要先解釋才有感覺（例：slab、行會、
   pop report、樂園）。創作與交接一律用前者定調，後者降級為家具。
2. **地方敘事（迪士尼 A 面）。**故事優先被「住」，其次才被「講」：場景、儀式、
   地標、貨流方向都是敘事渠道，對白排在它們後面。入場那段路（停車場→專車→
   門→隧道→大街→街尾城堡）是完整的敘事結構：手續全部辦在路之外，路上
   每一節只做「進入異世界」一件事。
3. **感覺一致性（迪士尼 C 面）。**每個接觸點交付同一種感覺，跨章、跨場景
   不斷線。這是驗收線，不是形容詞。
4. **（vinci_world 定案）取得是社交的，收藏是私人的。**Vinci World 是「取得
   收藏」的地方；收藏本身住在個人房間（現階段不展開）。「一個人天天與藏品
   獨處」不是可用的情感（USER 判定：那是連環殺手摸戰利品）。情感全部長在
   人與人之間，收藏品是電線。
5. **（vinci_world 定案）壓住取得、只建期望。**入場走廊從頭到尾一次都不釋放
   「取得」：貨與人同船、封條完好護送、佈告只寫箱數不寫內容、到貨鈴響的是
   「封著的東西就緒」。第一次「打開」必須是玩家自己的第一抽。期望建立的
   完整度，就是第一抽情感強度的上限。

## 三、主權檔拆分：WORKFLOW_CORE_VARIABLES 一分為三

現在那份檔混了三種東西，拆成：

| 新檔 | 內容 | 主權 |
|---|---|---|
| **世界規則**（WORLD_RULES，每遊戲一份） | 世界裡什麼是真的：本體論、投影法則、貨幣、用詞表、基調紅線 | USER 親筆，工具唯讀 |
| **敘事方針**（NARRATIVE_DELIVERY，每遊戲一份） | 這個遊戲怎麼說話：直說／不說人話的刻度（黑魂式 vs 動森式）、各渠道的側重比例、對白密度 | USER 親筆，工具唯讀 |
| **生產規則**（留在 factory core / adapter） | 文風紀律、語言、交接反壓縮規則、審查程序 | factory 維護 |

敘事方針單獨成檔的理由：它既不是世界事實（黑魂的世界觀不要求它不說話），
也不是生產流程（它是每個遊戲的藝術決定）。

## 四、Digital twin 升格為故事世界 database

現況是一次性打包的成品（DIGITAL_TWIN_PACKAGE.md + seed_entities.json），
沒有維護工具。改為：

- 有 CRUD 工具的活資料庫：實體（人、地、物、規則、儀式）可查、可改、可加。
- **每章回寫**：章節產出的新 canon（新角色、新地點、新判例）落章時寫回庫，
  不再散在各章 artifacts 裡等人翻。
- 查詢是工人的標準動作：dispatch 時給查詢入口，不再靠交接檔轉抄世界設定。

## 五、新增最上游 artifact：情感 beat sheet

每章一份新 md（放遊戲 repo 的 STORY_ROOT），內容是**有序的畫面拍點＋情感曲線**。
以 vinci_world 的 entry/landing 為第一個範本：

- 每個 beat 是一個能傳播情感的畫面（「同船的人聊自己想找什麼，有人的
  want list 摺得又舊又軟」），不是抽象指令（「建立期望」）。
- 曲線標明哪裡壓、哪裡放（例：上船→同航→護送→佈告→到貨鈴，壓到頂，
  gacha 第一抽開閘）。
- 一份 beat sheet 算一個章節單位，內含多個 scene。
- 章節管線的 STEP 2 從「就地發現故事線」改成「從 beat sheet 領任務」。

**beat sheet 的產生方式是對談，自動化不了。**流程固定為：AI 攤田（同海拔、
一條一個具體畫面、不推導不歸納）→ USER 砍與定 → 收斂成 beat sheet。這要
建成 factory 的一個 interactive 模組（skill），與 headless 管線分開。

## 六、新增管線步驟：投放規劃（game 特化的核心）

story factory 是 game 特化的，不是小說／電影劇本工廠。beat sheet 定稿後，
新增一步「投放規劃」：

- 輸入：beat sheet ＋ 敘事方針。
- 輸出：每個 beat 走哪個渠道——cutscene／任務遊玩（A 點到 B 點）／NPC 閒聊
  ／item 說明／場景與道具本身／佈告欄／成就文案。
- 渠道清單由 adapter 宣告（每個遊戲不一樣；vinci_world 現有：cutscene 文件、
  mission 系統、NPC 對話、item 文案、場景佈置、佈告欄、成就）。
- 敘事方針決定側重：黑魂式會把大部分 beat 塞給 item 說明與場景，動森式
  塞給 NPC 對話。
- 判例：vinci_world CH1 把純過場重切成「過場＋六段任務」，就是手工做了
  這一步——之後由這一步在落地前做掉。

## 七、模組化總圖

現有 step 管線降級為模組之一。重建後的 story 部門：

```
story/
  modules/
    world-rules-editor/     # 世界規則＋敘事方針的建立與修訂（interactive，USER 主權）
    twin-db/                # 故事世界 database ＋ CRUD 工具＋每章回寫
    beat-sheet-dialogue/    # 攤田→砍→收斂 的對談工具（interactive）
    delivery-planner/       # 投放規劃：beat → 渠道
    step-pipelines/         # 現有 WORLD/CHARACTER/CAST/CHAPTER step 機（headless）
  adapters/                 # 每遊戲：渠道清單、落地規格、主權檔位置
```

各模組獨立可呼叫（今天就已經需要單獨修 WORKFLOW_CORE_VARIABLES 和 twin 而
無工具可用）。審查閘保留，並新增一道**情感驗收**：這個產出把 beat sheet 的
哪一拍傳出去了？曲線的壓與放有沒有走樣？

## 八、動工順序

1. USER 定稿 vinci_world 的「世界規則」與「敘事方針」開頭幾句（本體論改寫：
   取得是社交的、收藏是私人的；Vinci World 是取得收藏的地方）。
2. 拆檔：WORKFLOW_CORE_VARIABLES → 世界規則／敘事方針／生產規則三份，
   舊檔留 pointer。
3. 建 beat-sheet-dialogue 模組，把 vinci_world entry/landing 的 1-9 收成
   第一份正式 beat sheet。
4. 建 delivery-planner，拿 landing beat sheet 試跑（船、封箱、Momo、到貨鈴
   ——哪些是場景、哪些是 cutscene、哪些是 NPC 閒聊）。
5. twin-db 工具化。
6. step-pipelines 接新上游（STEP 2 改領任務制），舊 rpg-1 判例照舊可跑。
7. 第一個完整案子：vinci_world 碼頭 landing scene 重做（渡口＝世界正門）。

## 九、施工記錄（2026-07-07，第 1–6 步已動工完成）

- 第 1 步：本體論改寫的開頭幾句已依本計畫記錄落款進
  `vinci_world/design/story/state/WORLD_RULES.md`，標「USER 核可方向、
  親筆定稿待覆核」——USER 過目改定即可。
- 第 2 步：拆檔完成。vinci_world 端三份歸位、舊檔改 pointer；factory 端
  templates／init 腳本／SKILL／contract 全部改讀新主權檔，rpg-1 legacy
  路徑保留。
- 第 3 步：`story/modules/beat-sheet-dialogue/` 建成；第一份 beat sheet 收在
  `vinci_world/design/story/beat_sheets/ENTRY_LANDING_BEAT_SHEET.md`。
  **注意**：原對談的 1-9 清單初收時沒有落盤，beat sheet 曾依本計畫記錄的
  定案轉述收成；2026-07-07 稍後由持有對談原文的一方補登為十拍定稿（恢復
  「你來找什麼」「跟著箱子走」「街上全是猜」三拍；Momo 見證封條升入骨幹；
  初版「貨箱分流走另一條路」與定案相反，已修正為「人與貨同向」），
  投放規劃隨之重核為第二版。
- 第 4 步：`story/modules/delivery-planner/` 建成；渠道清單
  `adapters/vinci_world/DELIVERY_CHANNELS.md`（七渠道）；試跑產出
  `vinci_world/design/story/state/chapter_sources/ENTRY_LANDING_DELIVERY_PLAN.md`
  （佈告欄渠道 BLOCKED_BY_RUNTIME，留後備方案；三個開放項待 USER）。
- 第 5 步：`story/scripts/twin_db.py` 建成（list/get/search/add/update/
  writeback/validate＋changelog），對 vinci_world 實資料驗證通過
  （159 個 record id，0 錯 0 警告）。
- 第 6 步：chapter STEP 1/2/2.5/3/6.5/9/10/10.5 接新上游——STEP 2 雙模式
  （領任務制／無 beat sheet 走舊 discovery）、6.5 與 9 加情感驗收、
  STEP 10 改為「twin 回寫（Part A）＋adapter sync（Part B）」；
  world STEP 5 revision 改 merge-not-regenerate。rpg-1 照舊可跑。
- 第 7 步未動工（等 USER 砍定 beat sheet 草案拍與三個投放開放項）。
