# Production Adapter — blank answer sheet

Replace every `TBD`; mark unsupported capability `NOT_AVAILABLE`. This filled
game-owned file belongs at
`<GAMEPLAY_ROOT>/adapter/PRODUCTION_ADAPTER.md`.

## Identity and version

- Project id: TBD
- Adapter version/date: TBD
- Supported build/content revisions: TBD

## Runtime surfaces and schemas

| Surface | Target file(s) | Authoritative schema/docs | Producer/owner |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

## Id, key, reference, and ordering grammar

- Runtime ids: TBD
- Localization keys: TBD
- Cross-file references: TBD
- Timeline/event ordering: TBD
- Beat Sheet/beat/packet provenance fields or landing log: TBD

## Gameplay-to-runtime mappings

Name exact fields/nodes/APIs, failure behavior, and unsupported cases.

- Entry triggers: TBD
- Player input and resolved actions: TBD
- Control owners/input locks: TBD
- Camera framing/focus: TBD
- HUD/layer visibility: TBD
- Dialogue/AVG/cutscene presentation: TBD
- Objective show/update/complete: TBD
- Runtime/world transitions: TBD
- Failure/recovery/reset/checkpoint: TBD
- Completion/reward/feedback order: TBD
- Exit handoff/scene transition: TBD

## Delta validation

| Delta kind | Assertion/evidence | Exact validation command/check | Limits |
| --- | --- | --- | --- |
| runtime_delta | TBD | TBD | TBD |
| world_delta | TBD | TBD | TBD |

Mechanical validation cannot prove human attention, understanding, or feeling.

## Instrumentation landing surfaces

The Observation Adapter owns evidence semantics. This section owns where its
required hooks land in production.

- Logger/event-bus integration points: TBD
- Control/camera/HUD/presentation probes: TBD
- State before/delta/after hooks: TBD
- Capture triggers and storage hooks: TBD
- Session/build/save/seed provenance injection: TBD
- Flush/append-only guarantees: TBD
- Instrumentation validation command: TBD

Missing required hooks mean production is not complete.

## Asset, sound, story, localization, and code hooks

- Asset paths/order format + provenance: TBD
- Sound paths/order format + provenance: TBD
- Story/localization workflow + provenance: TBD
- Game code/data ownership: TBD
- Sibling factory handoff rules: TBD

## Validation and playtest

- Schema/integrity checks: TBD
- Build/headless/runtime tests: TBD
- Launch/checkpoint commands: TBD
- Screenshot/video/audio capture checks: TBD
- Human playtest procedure/evidence: TBD

## Unsupported capabilities and escalation

| Capability | Status/reason | Required capability/design revision | Owner |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |
