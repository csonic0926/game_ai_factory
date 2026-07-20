# Observation Adapter — blank answer sheet

Replace every `TBD`. Mark unavailable evidence `NOT_OBSERVABLE`. This filled
game-owned answer belongs at
`<GAMEPLAY_ROOT>/adapter/OBSERVATION_ADAPTER.md`.

## Identity and version

- Project id: TBD
- Adapter version/date: TBD
- Supported build/content revisions: TBD
- Machine-readable mapping path, repo-relative, or `NOT_AVAILABLE`: TBD
- Source log schema/version: TBD

## Instrumentation and reproducible launch

- Instrumentation enable/build steps: TBD
- Exact launch/test commands: TBD
- Session/run id generation: TBD
- Save/checkpoint/seed preparation: TBD
- Locale/input/platform/viewport capture: TBD
- Shutdown/flush guarantees: TBD

## Raw log and capture ownership

- Raw log location/pattern: TBD
- Screenshot location/pattern: TBD
- Video/audio/state snapshot location/pattern: TBD
- Append-only/order guarantee: TBD
- Retention and redaction rules: TBD
- Private provenance mapping location: TBD

All persisted project paths are relative to `<GAME_REPO>`. Raw evidence must
not contain design intent, semantic beat/sheet ids, or player-psychology
claims.

## Event and state mapping

| Canonical concern | Project event/source | Fields and order semantics | Observable or hidden | Limits |
| --- | --- | --- | --- | --- |
| Raw player input | TBD | TBD | TBD | TBD |
| Resolved gameplay action | TBD | TBD | TBD | TBD |
| Control owner/input enabled | TBD | TBD | TBD | TBD |
| Camera/viewport | TBD | TBD | TBD | TBD |
| HUD/modal/dialogue/objective | TBD | TBD | TBD | TBD |
| Audio/VFX/animation cue | TBD | TBD | TBD | TBD |
| World/runtime before-delta-after | TBD | TBD | TBD | TBD |
| Completion/reward/feedback order | TBD | TBD | TBD | TBD |
| Position/spatial relation | TBD | TBD | TBD | TBD |
| Captures/state snapshots | TBD | TBD | TBD | TBD |
| Exact span boundary markers | TBD | TBD | TBD | TBD |
| Player-control interval start/end | TBD | TBD | TBD | TBD |
| Presentation interval start/end | TBD | TBD | TBD | TBD |
| Traversal-only interval start/end | TBD | TBD | TBD | TBD |

## Clocks, correlation, and latency

- Monotonic clock source/unit: TBD
- Sequence/frame ordering: TBD
- Cue/action/response correlation ids: TBD
- Known clock skew/performance caveats: TBD

## Evidence-mode support

| Mode | Launch/checkpoint procedure | What it can prove | Limits |
| --- | --- | --- | --- |
| LIVE_BLIND_RUN | TBD | TBD | TBD |
| RECORDED_RUN | TBD | TBD | TBD |
| CONTROLLED_BRANCH_PROBE | TBD | TBD | TBD |
| STATIC_RUNTIME_ASSERTION | TBD | TBD | TBD |

## Blind projection exclusions

- Hidden runtime fields: TBD
- Design/provenance fields kept private: TBD
- Public context safe to reveal: TBD
- Capture redactions: TBD

## Observability matrix

List known kernels or capability classes. `NOT_OBSERVABLE` is a production
blocker, not a request for the reviewer to infer.

| Kernel/capability | Cue evidence | Attempt evidence | Response evidence | Carry-forward evidence | Branch/failure evidence | Status/gap owner |
| --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Validation and integrity

- Raw schema validation command: TBD
- Normalization command: TBD
- Timeline/blind-projection command: TBD
- Quantitative budget path and `measure-budget` command, including separate
  runtime-owned `--run-id` / `--session-id` arguments: TBD
- Reviewed acceptance-kernel measurement and non-gameplay selector ownership: TBD
- Capture-reference validation: TBD
- Expected integrity report location: TBD

## Unsupported evidence and escalation

| Missing evidence path | Why | Required instrumentation/plan revision | Owner |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |
