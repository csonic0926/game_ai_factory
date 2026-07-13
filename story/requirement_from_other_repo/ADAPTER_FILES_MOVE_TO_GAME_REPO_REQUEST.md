# Cross-repo factory request — adapter answer-files move to the game repo

## Request metadata

- Status: done（2026-07-13 factory 側實作完成，見文末 completion notes）
- Date: 2026-07-13
- Source repo: vinci_world (game repo, factory caller)
- Source repo path: /Users/hunglingki/git_projects/web_projects/vinci_world
- Request owner: USER（結構性決定，2026-07-13 對話定案方向）
- Factory target area: docs (PROJECT_PROFILE_CONTRACT) | skills/game-story-factory | adapters resolution | story/AGENTS.md
- Priority: normal（在下一次 chapter/entry 生產開跑前完成即可）

## User-facing need

Adapter 的五個「答卷檔」（PROJECT_PROFILE / VISUAL_GRAMMAR / LANDING_SPEC /
DELIVERY_CHANNELS / STYLE_GUIDE）描述的是**遊戲 repo 的程式能力**（client 拍得
出什麼、核准文字落進哪些 runtime 檔、i18n key 文法），卻住在 factory repo 的
`story/adapters/<project_id>/`。實證問題（2026-07 兩件）：

1. **失同步**：game repo 上線 sky-dive intro（commit c8c501dc/7f1d54d8）後，
   factory 側 `LANDING_SPEC.md` 停在 v0.2 白幕版多日，直到人工對齊（2026-07-13）。
   遊戲的 commit 無法原子性地帶上自己的 adapter 更新。
2. **無主檔**：`adapters/vinci_world/VISUAL_GRAMMAR.md` 自 2026-07-08 存在卻
   一直 untracked——兩個 repo 都不覺得這檔是自己的。

USER 定案方向：**factory 出題（契約），game repo 交卷（答案檔），答案跟被
描述的程式住在一起、隨遊戲版本化。** factory 才知道自己要什麼——所以契約
（欄位、格式、驗收）仍歸 factory；填好的檔案歸各遊戲。

## Factory-side change requested

1. **契約文件改版**（`story/docs/PROJECT_PROFILE_CONTRACT.md`）：
   - 宣告答卷檔的正典位置改為 `<GAME_REPO>/design/story/adapter/`
     （即 `<STORY_ROOT>/adapter/`；名稱可由 factory 定案，但必須是固定約定路徑）。
   - 契約本身（必答欄位、LANDING_SPEC 七問、VISUAL_GRAMMAR 應含章節）與
     `adapters/_template/`（空白答卷）留在 factory。
2. **解析順序**（`story/AGENTS.md` §Start here 第 2 條 +
   `skills/game-story-factory/SKILL.md` 的 profile 解析規則）改為：
   1. 呼叫時明示的 adapter 路徑（若有）
   2. `story/adapters/registry.md` 電話簿（一行一專案：`<project_id> → <絕對路徑>`）
   3. cwd 約定：session 工作目錄若為遊戲 repo，找 `./design/story/adapter/`
   4. **fallback：舊位置 `story/adapters/<project_id>/`**（未遷移專案照跑，
      rpg-1 不動）
3. **新增 `story/adapters/registry.md`**，首筆登記
   `vinci_world → /Users/hunglingki/git_projects/web_projects/vinci_world/design/story/adapter/`。
4. **遷移 vinci_world**：`story/adapters/vinci_world/` 五檔搬到上述 game repo
   路徑（git mv 保歷史；注意 `VISUAL_GRAMMAR.md` 目前 untracked，需先入庫或
   直接在 game repo 首次入庫）；原資料夾留一個 `MOVED.md` pointer 防舊引用。
5. **同步修訂引用**：`story/README.md`（Factory positioning／Layout）、
   `AI_CALLER_LANDING.md`（若提及 adapters 路徑）、
   `scripts/init_story_root.sh`（bootstrap 時應一併建立 `<STORY_ROOT>/adapter/`
   並從 `_template/` 複製空白答卷）。

## References and source context

- `story/docs/PROJECT_PROFILE_CONTRACT.md`（現行契約）
- `story/README.md` §Factory positioning（現行三權分立表述）
- `story/adapters/vinci_world/`（現行五檔，2026-07-13 已更新到 LANDING_SPEC
  v0.3 / VISUAL_GRAMMAR v0.2——遷移時搬「更新後」的版本）
- 失同步案例：vinci_world commits c8c501dc、7f1d54d8（sky-dive intro）與
  LANDING_SPEC v0.2→v0.3 的時間差
- 佐證模式：本 umbrella `asset/requirement_from_other_repo/REQUEST_TEMPLATE.md`
  （factory 出題、caller 交卷的既有先例）

## Acceptance criteria

- [x] PROJECT_PROFILE_CONTRACT.md 宣告新正典位置＋解析順序（含 legacy fallback）。
- [x] `story/adapters/registry.md` 存在且含 vinci_world 一筆。
- [x] vinci_world 五檔在 `<GAME_REPO>/design/story/adapter/` 且內容為 2026-07-13
      更新後版本；factory 舊資料夾只剩 pointer。
- [x] 以 vinci_world 跑一次 profile 解析 dry-run（任一 step 的 orchestrator
      前置），worker prompt 內的變數全部解析自新位置。
- [x] rpg-1 未遷移、經 fallback 照常解析（不改其任何檔案）。
- [x] `_template/` 仍在 factory 且被 CONTRACT 引用為「空白答卷」。

## Non-goals / do-not-change

- 不動 `core/` step 檔與 `.5` 閘（`<STORY_ROOT>` canonical layout 不變；
  `adapter/` 是它底下新增的一個子目錄）。
- 不動產出物歸屬（artifacts 本來就 version with the game）。
- 不動 sovereignty 規則（WORLD_RULES / NARRATIVE_DELIVERY 仍為 USER-authored、
  tools read-only）。
- 不在本案內遷移 rpg-1（fallback 支撐；日後另案）。

## Factory completion notes (2026-07-13)

- 契約：`docs/PROJECT_PROFILE_CONTRACT.md` 新增「Canonical adapter location」
  （`<STORY_ROOT>/adapter/`，答卷檔列表含 DELIVERY_CHANNELS.md 與
  style_lint_config.json）與「Adapter resolution order」四段解析順序；
  canonical STORY_ROOT layout 補上 `adapter/` 子目錄。
- 解析順序落到兩處入口：`story/AGENTS.md` §Start here 第 2 條、
  `skills/game-story-factory/SKILL.md` Resolution 第 1 條（引入 `<ADAPTER>`
  變數；文內三處 `adapters/<project_id>/` 硬路徑同步改為 `<ADAPTER>/`；
  skill description 一併更新）。
- `adapters/registry.md` 建立，首筆 vinci_world。
- 遷移：六檔（五答卷＋`style_lint_config.json`）以 working-tree 版本複製到
  game repo 並 `diff -r` 逐檔驗證一致後，factory 側 `git rm` 五個 tracked 檔
  ＋移除 untracked 的 VISUAL_GRAMMAR.md；舊資料夾只剩 `MOVED.md` pointer。
  跨 repo 無法以 git mv 保歷史——factory 歷史保留在本 repo git log，
  game repo 為首次入庫。
- 引用同步：`story/README.md`（positioning／Layout／Onboarding）、
  `scripts/init_story_root.sh`（bootstrap 建立 `<STORY_ROOT>/adapter/` 並從
  `_template/` 播種，絕不覆寫既有答卷；已於 mktemp 目錄實測）。
  umbrella `AI_CALLER_LANDING.md` 未寫死 adapters 路徑，免改。
- Dry-run：registry 查得 vinci_world → 新位置解析出全部七個必答變數，
  五檔＋lint config 可讀；rpg-1 無 registry 登記（`^- rpg-1 ` 0 筆）、
  `adapters/rpg-1/PROJECT_PROFILE.md` 經 fallback 照常解析，檔案零變動。
  工廠內 `adapters/vinci_world` 殘留引用 0 筆（本需求單除外）。
- 兩個 repo 的變更均未 commit，留待 USER 檢視後入庫（game repo 側
  `design/story/adapter/` 六檔為 untracked 新檔，與進行中的 staged
  archive 作業互不干擾）。
