# Runtime Observation and Acceptance Contract v1

## Purpose

Gameplay experience is produced during runtime interaction. Code existence,
state tests, screenshots, or a design-derived paper projection cannot by
themselves prove that the approved experience survived implementation.

Every production-ready Playable Beat Packet therefore includes an observation
contract. Gameplay implementation and instrumentation are two deliverables of
the same production job:

```text
no observable acceptance evidence
  -> no production-ready packet
  -> no factory-conformance PASS
```

## Formal objects and causal partitions

For a source Beat Sheet version `B`, walkthrough `T`, packet set `P`, build
`I`, raw evidence `E`, Observation Adapter `A_o`, and blinded reading `H`:

```text
C = normalize(E, A_o)                 # canonical event stream
L = reconstruct_player_time(C)        # derived observable timeline
Q = sequential_blind_projection(L)    # no design/future/hidden state
V = compare(B, T, P, L, H)            # acceptance verdict
```

Keep these state classes separate:

- **authority/decision state:** `B`, `T`, `P`, production/observation plans;
- **external execution state:** build, save, seed, session, input/platform;
- **raw observable evidence:** append-only runtime events and captures;
- **derived observable state:** `C` and `L`;
- **experience interpretation:** `H` and the final acceptance comparison.

Allowed arrows: runtime creates raw evidence; the adapter normalizes it; the
blind reader interprets sequential observable evidence; the acceptance
reviewer compares authority and observation chains.

Forbidden arrows:

- design intent, beat ids, or expected actions into raw evidence or blind
  input;
- implementation-author explanation into observed runtime truth;
- future events or hidden state into a blind-reader turn;
- blind-reader interpretation back into raw/derived observations;
- one recorded golden path into claims about untested alternatives;
- a logger field asserting understanding, emotion, fun, or meaningfulness.

## Evidence layers

### 1. Raw runtime evidence

Raw evidence preserves engine order and contains no design interpretation.
The canonical manifest and event schemas are:

- `../schemas/raw_manifest.schema.json`
- `../schemas/raw_event.schema.json`

Minimum coverage includes:

- session/run id, build/content revision, save/checkpoint, seed, locale, input
  mode, platform, viewport/window mode, and relevant performance context;
- monotonic timestamp and comparable sequence/frame ordering;
- scene/map/encounter context;
- raw player input and resolved gameplay action as different event kinds;
- control owner, movement enabled, cutscene/dialogue/modal state;
- relevant state before/delta/after;
- camera/viewport and key cue/actor/UI presentation state;
- objective/dialogue/feedback/reward/audio/VFX ordering;
- screenshot/video/audio/state-snapshot references;
- neutral runtime ids. Private design/provenance mappings remain outside blind
  data.

The logger must not write fields such as `player_understood`,
`player_forecast`, `felt_fun`, `emotion`, `meaningful_alternative`, or semantic
beat/sheet ids. The reference validator fails closed on prohibited field
names, missing provenance, bad ordering, and unresolved capture refs.

When an acceptance kernel contains a negative/absence check, the manifest may
declare an explicit complete observation window:

```json
{
  "observation_window": {
    "start_sequence": 100,
    "end_sequence": 140,
    "coverage_status": "COMPLETE",
    "coverage_basis": "adapter-declared shutdown/flush marker and contiguous logger sequence"
  }
}
```

The reference reader verifies that every integer sequence in the declared
range is present. This declaration is optional for positive evidence, but
without a complete window covering the selected phase interval, no-match is
`INCONCLUSIVE_COVERAGE`, never proof of absence. A found forbidden match is
reported as `VIOLATION_MATCH_FOUND` even when wider absence coverage is
incomplete.

### 2. Derived observable timeline

The Factory reader normalizes engine-specific events using the game-owned
Observation Adapter and reconstructs player time. It may state what appeared,
whether control was available, when input occurred, how the world responded,
and measured cue/action/feedback latency. It may not state what the player
understood or felt.

Every normalized event keeps raw evidence references. Derived results never
overwrite raw logs.

### 3. Experience interpretation

A fresh runtime player/reader records the immediate purpose, next attempted
action and reason, perceived alternatives, expected feedback, confidence,
misread, and model update from a live build or sequential blind projection.
These are QA observations, not runtime facts.

## Evidence modes and coverage

- `LIVE_BLIND_RUN` — a fresh agent/human controls the build; supports action
  formation and reception evidence.
- `RECORDED_RUN` — an existing run; supports only the observed path.
- `CONTROLLED_BRANCH_PROBE` — same checkpoint/seed or declared equivalent,
  testing alternatives, failure/recovery, or performance outcomes.
- `STATIC_RUNTIME_ASSERTION` — mechanical state/reference evidence only.

The raw manifest declares one mode. Acceptance may combine multiple sessions.
A decision kernel needs branch evidence for alternatives; a mastery kernel
whose meaning includes failure adjustment needs differentiated outcomes.
Controlled branch evidence is grouped only by explicit probe group, requires
the same build/content/checkpoint/seed/locale/input/platform/display and
performance context, at least two labels, one complete causal chain per label,
and distinct observed response/carry-forward consequences. Different labels
or different inputs with otherwise identical response/carry evidence are not
distinct branches. Decision proof must support at least two contemporaneously
reachable alternatives from the controlled baseline; a chain merely labelled
`decision` never counts.

Pressing a teleporter, advancing dialogue, raw button/input counts, straight
locomotion, reaching an objective trigger, and passive state changes do not
independently count as gameplay evidence. A span containing presentation,
input, control return, movement, and arrival but no complete reviewed
engagement chain is `NO_GAMEPLAY`.

Every acceptance kernel whose `required_evidence_modes` contains
`CONTROLLED_BRANCH_PROBE` must also declare a non-empty unique
`controlled_probe_group_ids` list. Values are exact raw-manifest
`probe_group.group_id` bindings; selector overlap never infers applicability.
Only declared groups are evaluated for that kernel, and every declared group
must be present and complete. A missing group, a missing branch chain, an
incomparable environment, or identical observed signatures remains
`INCOMPLETE`. Undeclared groups are omitted even when they match generic
selectors. A kernel that does not require `CONTROLLED_BRANCH_PROBE` must not
declare the binding field and reports no branch-probe groups.

## Acceptance-kernel ordered sequences

The four positive selectors remain `cue -> action_or_attempt ->
world_response -> carry_forward`. When required runtime behavior has ordered
intermediate events that those four boundaries cannot prove, the kernel may
declare `ordered_sequences`:

```json
{
  "sequence_id": "cache-reopen-proof",
  "after_phase": "world_response",
  "before_phase": "carry_forward",
  "matches": [
    { "match": { "observable": { "cache": { "result": "shown" } } } },
    { "match": { "observable": { "cache": { "close": 1 } } } },
    { "match": { "event_kind": "control", "observable": { "owner": "player" } } },
    { "match": { "observable": { "cache": { "reopen": true } } } },
    { "match": { "event_kind": "capture", "observable": { "cache": { "snapshot": "reopened" } } } },
    { "match": { "observable": { "cache": { "close": 2 } } } }
  ]
}
```

Boundary phases must increase in positive-phase order. Every match binds one
strictly ordered, distinct event in the same run/session and strictly inside
the selected phase boundaries. Extra events are allowed; cross-run filling,
boundary-event reuse, and one-event/multiple-step reuse are forbidden. A
positive phase chain is acceptance-ready only if all declared sequences can
be satisfied jointly. Branch completeness and negative-check windows operate
only on those sequence-qualified chains. Missing, outside-window, reordered,
or reuse-dependent steps remain incomplete and expose evidence candidates;
they never degrade into positive-chain-only completion.

`ordered_sequences` is optional. A v1 kernel that omits it retains the prior
four-phase behavior.

## Observation Adapter responsibilities

The game-owned `OBSERVATION_ADAPTER.md` declares:

- instrumentation enablement and reproducible launch procedure;
- raw log/capture locations and source schema/version;
- declarative or executable mapping to canonical event fields;
- checkpoint/save/seed setup and evidence-mode support;
- control, camera, HUD, audio, spatial, state, and capture sources;
- clock/order semantics and correlation ids;
- private provenance handling and blind-field exclusions;
- acceptance kernels currently `NOT_OBSERVABLE`.

The optional machine-readable mapping follows
`../schemas/observation_mapping.schema.json`. Factory core does not hard-code
engine scenes, nodes, files, verbs, or event names.

## Production observation contract

Each packet must name:

- acceptance kernel(s) and exact Beat Sheet binding;
- raw event kinds and fields that will carry cue, attempt, response, and
  carry-forward evidence;
- every required ordered intermediate sequence, its phase boundaries, and the
  event/capture fields that prove each step;
- required captures and capture timing;
- correlation/order/latency requirements;
- evidence modes and branch/failure probes;
- instrumentation landing locations and validation commands;
- redaction/blinding rules;
- known gaps and their blocker status.

If any required chain has no reliable evidence path, mark the packet
`BLOCKED_BY_OBSERVABILITY` before production. A generic test or screenshot
command is not an observation contract.

## Reference reader capability

`../reader.py` provides a dependency-free reference interface:

1. `validate` — validate manifest, events, order, forbidden fields, refs, and
   provenance;
2. `normalize` — map project events into a canonical event stream;
3. `reconstruct` — produce a chronological JSON/Markdown timeline and
   cue/action/response latency measurements;
4. `blind-project` — strip future/hidden/design data into facilitator-revealed
   payloads;
5. `prepare-acceptance` — attach auditable phase and ordered-sequence evidence
   refs, plus fail-closed incomplete reasons, without deciding PASS/FAIL;
6. `measure-budget` — measure exact-span duration, player-control ratio,
   presentation/traversal gaps, complete kernel chains, controlled decision
   consequences, and configured content counts against the game-owned
   Quantitative Experience Budget;
7. `run` — execute the full readback sequence and emit an integrity report.

The quantitative gate emits exactly one objective status:
`PASS_EXPERIENCE_BUDGET`, `FAIL_EXPERIENCE_BUDGET`, `NO_GAMEPLAY`, or
`INCONCLUSIVE_EVIDENCE`, with measured values, threshold comparisons, and
source evidence refs. It cannot infer fun, meaningfulness, understanding, or
psychology and cannot emit `PASS_FACTORY_CONFORMANCE`. Raw event labels never
self-certify counts: configured measurement ids bind reviewed acceptance
kernels, and temporal measures bind paired selectors over a complete exact
observation window.

The Beat-Sheet-owned budget contains boundary selectors but no runtime run or
session id. Measurement invocation selects the runtime-owned run/session. The
reported control ratio is gameplay-capable control time: presentation-only
overlap is subtracted even when dialogue advance remains available. One chain
may count as a complete gameplay beat plus at most one distinct content quota.
A chain whose action, response, and carry evidence are all classified by the
non-gameplay selectors is disqualified rather than self-certifying gameplay.

See `OBSERVATION_READER.md` for commands and format boundaries. Reader output
belongs under the game repo's `design/gameplay/runtime_evidence/<run_id>/`,
never under this factory.

## Blinded runtime reading

A fresh blind reader receives only sequential runtime observations. It must
not receive Beat Sheet/trace/packet/code, semantic design ids, canonical
action, future frames, hidden state, action enumeration, or implementation
notes. Each reveal records an answer before the next reveal.

The paper-stage First-time Player projection remains a useful design
reception prefilter, but its source is design-authored `visible_and_known`.
Runtime blind input must come only from actual runtime evidence through the
reader. The two reports are not interchangeable.

## Acceptance reviewer

Only the fresh acceptance reviewer receives both chains:

```text
Authority: approved Beat Sheet -> walkthrough -> packets
Observation: build -> raw/captures -> timeline -> blind report
```

It evaluates each acceptance kernel, allowed drift, curve/control/order, and
red-line check. It does not require the observed action sequence to equal a
golden path. It points to evidence or identifies the first transformation
boundary where meaning was lost. It never fixes design or implementation in
the same pass.

Runtime acceptance must read a fresh exact-span quantitative result first.
Only `PASS_EXPERIENCE_BUDGET` may proceed to production acceptance; a span with
any other quantitative status cannot be called a gameplay segment or receive
factory conformance.

Allowed verdicts:

- `PASS_FACTORY_CONFORMANCE`
- `FAIL_IMPLEMENTATION_FIDELITY`
- `FAIL_RECEPTION`
- `FAIL_DESIGN`
- `BLOCKED_BY_ADAPTER`
- `BLOCKED_BY_OBSERVABILITY`
- `INCONCLUSIVE_EVIDENCE`

Every factory pass also records human status, normally
`PENDING_HUMAN_PLAYTEST`. Only a USER/human process may mark
`HUMAN_PLAYTEST_ACCEPTED`; factory conformance never implies enjoyment.

## Integrity fail-closed rule

Missing captures, unresolved refs, clock/order errors, mixed sessions/builds,
prohibited interpretation fields, missing branch coverage, or contaminated
blind input produce `INCONCLUSIVE_EVIDENCE` or the specific blocker. They
never degrade to warnings followed by PASS.
