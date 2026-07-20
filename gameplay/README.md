# Gameplay Factory

Gameplay Factory owns a closed production-conformance loop:

```text
versioned Span Quant Sheet (span -> cadence -> playable-content demand)
  -> versioned Gameplay Experience Beat Sheet (supply satisfies demand)
  -> continuous player-time walkthrough
  -> production packets + observation contracts
  -> caller implementation + instrumentation
  -> actual runtime logs/captures
  -> canonical observed timeline + blinded runtime reading
  -> fresh conformance acceptance or routed failure
```

Quantity is decided first: the quant sheet fixes the span, adopts the
factory's canonical cadence (one new meaningful choice every 3–5 seconds
unless a project USER ruling overrides it), and inventories the generators
and one-shots that can hold that beat — implementation-blind, from player
expectation, so supply never defines demand. Total duration is free when the
beat holds. A Beat Sheet may only be authored against approved quant floors.

Its factory verdict asks whether an implementation preserved an approved
experience. It does not promise that every player feels the same thing, prove
that a structure is fun, or replace human playtesting.

## Current implementation status

The factory owns the v1 contracts, blank game-owned answer/artifact templates,
canonical raw evidence schemas, and dependency-free reference reader. The
creative workflow remains manual while real project pilots calibrate it; there
is no gameplay skill or creative step machine yet.

`reader.py` can validate raw evidence, normalize through a project mapping,
reconstruct player time/latency, build a sequential runtime-blind projection,
prepare kernel evidence refs, and measure the quant-derived, sheet-bound
quantitative budget against an invocation-selected runtime run/session. Its objective budget
status is not a factory/human acceptance verdict. It does not implement game
instrumentation, play the build, or interpret player psychology.

The full factory request is not complete until real game-owned pilots prove
the loop, including a deliberate mismatch and a second gameplay shape.
See [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md) for the
explicit implemented/unproven boundary.

## Layout

```text
AGENTS.md                         hard caller rules
docs/AI_CALLER_LANDING.md        manual end-to-end workflow
docs/*_CONTRACT.md               authority/trace/packet/adapter/evidence contracts
docs/OBSERVATION_READER.md       reader formats and commands
modules/span-quant/              manual quant-demand authoring/review module
modules/experience-beat-sheet/   manual authoring/review module
adapters/_template/              three blank game-owned adapter answers
schemas/                         canonical evidence/mapping/kernel JSON schemas
templates/                       blank game-owned artifacts
reader.py                        runtime evidence reference tool
tests/                            factory reader tests only
```

## Ownership boundary

- **Factory repo:** project-agnostic questions, contracts, schemas, tools,
  invariants, and blank templates.
- **Game repo:** filled adapters, Beat Sheets, walkthroughs, packets,
  observation plans, implementation mappings, logs/captures, timelines, blind
  reports, acceptance reports, grammar state, and experience lessons.

AI callers start at [`docs/AI_CALLER_LANDING.md`](docs/AI_CALLER_LANDING.md).
