# Cross-repo factory request

## Request metadata

- Status: completed
- Date: 2026-06-17
- Source repo: simplest_infinity_magic_tower (Infinity Magic Tower / IMT)
- Source repo path: /Users/hunglingki/git_projects/Godot/simplest_infinity_magic_tower
- Request owner / Codex context: dungeon master-render → tile decomposition; was choosing a provider for fresh tile/scene generation
- Factory target area: provider routing + docs (GPT Image / cliproxyapi)
- Priority: normal

## The bug (what's wrong)

The factory makes an agent reasonably (but wrongly) conclude that **GPT Image is
unavailable on this machine**, so it silently falls back to Gemini for every
fresh generation. That conclusion is wrong: GPT Image IS fully set up here — the
factory just gives no signal of that and no guidance to enable it.

### Why an agent concludes "GPT Image unavailable"

- GPT Image (`gpt-image-2`) is reachable **only** through the `cliproxyapi`
  provider. See `pipeline/reference_pair_workflow.py`:
  - `CLI_PROXY_DEFAULT_BASE_URL = "http://127.0.0.1:8317/v1"`
  - `CLI_PROXY_DEFAULT_API_KEY = "local-dev-image-key"`
  - `CLI_PROXY_DEFAULT_MODEL = "gpt-image-2"`
  - aliases `gpt_image_2` / `imagegen` → `cliproxyapi`
- If the local proxy is not running, a GPT Image run fails with a connection
  error to `127.0.0.1:8317`. Nothing in the failure path says the proxy is
  installed/configured, or how to start it. The orchestrator skill even says
  "don't treat `GET /` as capability truth" — which pushes the agent toward
  "assume unavailable" rather than "start the proxy".

### Reality on this machine (verified 2026-06-17)

- `cliproxyapi` binary is installed: `/opt/homebrew/bin/cliproxyapi`
- Config present: `~/.cli-proxy-api/config.yaml` (host 127.0.0.1, port 8317,
  api-key `local-dev-image-key`)
- Upstream auth present: `~/.cli-proxy-api/codex-*.json` (Codex/ChatGPT
  plus/team/pro accounts) — i.e. GPT Image is served via Codex accounts through
  the proxy.
- The ONLY missing piece is that the proxy process was not running
  (`curl http://127.0.0.1:8317/v1/models` → no response; nothing listening on
  8317).

So GPT Image is a one-command-away capability, not an unavailable one.

## Factory-side change requested

Pick any subset; the goal is that an agent never silently downgrades to Gemini
when GPT Image is actually available.

1. **Preflight + actionable error.** Before a cliproxyapi run, probe
   `GET {base_url}/models` (or `/v1/images/...`). If unreachable, fail with a
   message like:
   `cli-proxy not running. Start it: cliproxyapi --config ~/.cli-proxy-api/config.yaml (binary at /opt/homebrew/bin/cliproxyapi), then retry.`
   instead of a raw connection error.
2. **Optional auto-start hook.** A `--ensure-proxy` flag (or env opt-in) that
   starts cliproxyapi if 8317 isn't listening, waits for health, then proceeds.
3. **README/docs.** State plainly that GPT Image runs through a LOCAL cli-proxy
   that is installed + configured here, and must be running. Include the start
   command and the health-check URL. Right now the docs read as if a local proxy
   is an obscure prerequisite rather than the configured default path.

## Secondary smell found while tracing this (worth a look, not the main ask)

The Gemini path hardcodes `--key=company` when shelling out to nano_banana
(`reference_pair_workflow.py` ~line 1461), while
`credentials.py:build_gemini_provider_env` overwrites BOTH `GEMINI_KEY_COMPANY`
and `GEMINI_KEY_PERSONAL` with the single resolved `GEMINI_API_KEY`. Net effect:
runs log `API Key: 公司 (Company)` while actually using whatever `GEMINI_API_KEY`
resolves to (on this machine the *personal* key, because the company key's free
tier is exhausted / limit 0). It works, but the company/personal distinction is
a no-op and the log line is misleading. Consider either honoring a real
key-selection or dropping the `--key=company` hardcode and the label.

## Repro / evidence commands

```bash
ls /opt/homebrew/bin/cliproxyapi            # binary present
cat ~/.cli-proxy-api/config.yaml            # host/port/api-key configured
ls ~/.cli-proxy-api/codex-*.json            # upstream Codex auth present
curl -s -m4 -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8317/v1/models  # 000 when proxy down
```


## Factory response — 2026-06-17

Status: completed.

Changed:

- Added a `cliproxyapi` preflight that checks `GET {base_url}/models` before GPT Image requests.
- Replaced raw connection-refused failures with an actionable error that says to start `/opt/homebrew/bin/cliproxyapi --config ~/.cli-proxy-api/config.yaml` and includes the health-check URL.
- Added an opt-in auto-start hook:
  - `--ensure-proxy` for `generate-reference-pair` and `generate-wall-reference-pair`
  - `CLI_PROXY_API_ENSURE=1` for any workflow using the shared provider wrapper.
- Documented the local GPT Image / `cliproxyapi` setup in README and workflow docs so agents should start the proxy instead of silently downgrading to Gemini.
- Added provider tests for `/v1/models` preflight and actionable down-proxy errors.

Changed files:

- `pipeline/reference_pair_workflow.py`
- `itf.py`
- `tests/test_reference_pair_workflow_provider.py`
- `README.md`
- `docs/SPEC.md`
- `docs/AI_CALLER_LANDING.md`
- `docs/WALL_REFERENCE_PAIR_WORKFLOW.md`
- `docs/PROP_ASSET_WORKFLOW.md`
- `docs/TILE_RESKIN_WORKFLOW.md`
- `docs/REPO_MEMORY.md`
- `docs/CURRENT_JOB.md`
- `requirement_from_other_repo/2026-06-17_imt_gpt_image_cliproxy_availability.md`

Validation:

```bash
python3 -m unittest tests.test_reference_pair_workflow_provider -v
python3 -m unittest tests.test_prop_asset_workflow tests.test_reference_pair_workflow_provider tests.test_variant_selector_floor_mapping tests.test_variant_selector_wall_validation -v
python3 -m py_compile pipeline/reference_pair_workflow.py itf.py pipeline/prop_asset_workflow.py pipeline/tile_reskin_workflow.py
```

Also tried `python3 -m unittest discover -s tests -v`; it reached the existing `tests/test_tile_reskin_workflow.py` pytest dependency and failed because `pytest` is not installed in this environment.

Notes / not changed:

- Did not start the proxy or run a paid/real GPT Image generation during this factory-side patch.
- The Gemini `--key=company` label/key-selection smell was left as a separate follow-up because the main GPT Image availability failure is now covered.
