# Gameplay Observation Plan — `<PACKET_OR_SPAN_ID>`

## Authority and production binding

- Beat Sheet path/id/version/checksum:
- Walkthrough path/version:
- Packet ids/versions:
- Production Adapter version:
- Observation Adapter version:
- Build/content target:
- Plan status: `READY | BLOCKED_BY_OBSERVABILITY | STALE`

## Kernel evidence matrix

| Kernel | Cue evidence | Action/attempt evidence | World response + latency | Carry-forward evidence | Mode/session | Captures | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

## Required ordered intermediate sequences

Omit entries when the four positive phases are sufficient.

| Kernel | Stable sequence id | After phase | Before phase | Ordered event matches and evidence hooks |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Instrumentation landing

- Code/data hooks and owners:
- Raw event/capture locations:
- Correlation/order rules:
- Enable/launch/flush commands:
- Integrity validation command:

## Run matrix

| Run label | Evidence mode | Checkpoint/save/seed | Branch/outcome | Fresh player/reader | Required artifacts |
| --- | --- | --- | --- | --- | --- |
|  | LIVE_BLIND_RUN |  |  |  |  |
|  | CONTROLLED_BRANCH_PROBE |  |  |  |  |

## Blinding and private provenance

- Raw fields excluded from blind input:
- Semantic/design ids kept only in private comparison mapping:
- Capture redactions:
- File-only handoff boundary:

## Pre-production fail-closed check

- [ ] Every kernel has cue → attempt → response → carry-forward evidence.
- [ ] Every declared ordered sequence has distinct same-run event evidence
      strictly inside its phase boundaries.
- [ ] Alternatives/failure/performance claims have the required probe mode.
- [ ] Instrumentation is part of the production job.
- [ ] Captures and refs can be validated.
- [ ] Blind projection contains no design, hidden, or future data.
- [ ] Every gap is `BLOCKED_BY_OBSERVABILITY`; none is deferred silently.
