# AI Caller Landing — gameplay_factory

You are an AI agent producing and independently checking a concrete gameplay
experience from design authority through actual runtime evidence.

## Start here

1. Read `docs/PROJECT_ADAPTER_CONTRACT.md`.
2. Resolve the target game repo: explicit path -> current Git root -> ignored
   local registry for an explicit project id. Never scan sibling repos.
3. Set `<GAMEPLAY_ROOT>` to `<GAME_REPO>/design/gameplay`; reject any output
   inside this factory or outside the game repo.
4. Read all three game-owned answers under `<GAMEPLAY_ROOT>/adapter/`:
   `PROJECT_GAMEPLAY_PROFILE.md`, `PRODUCTION_ADAPTER.md`, and
   `OBSERVATION_ADAPTER.md`. Missing/incomplete answers mean
   `BLOCKED_BY_ADAPTER`.
5. Read `docs/AI_CALLER_LANDING.md` and follow the manual production loop.
   There is no creative step machine or gameplay skill yet; `reader.py` only
   validates and reconstructs actual evidence.

## Hard rules

- **Quantity demand before authoring.** Author and freshly review a Span
  Quant Sheet — span boundaries, cadence contract, and an
  implementation-blind playable-content inventory with derived floors —
  before any Beat Sheet. Only `PASS_QUANT_REVIEW` may proceed to authoring.
- **Cadence is the demand.** The factory's canonical beat is one new
  meaningful choice arriving every 3–5 seconds (max arrival gap 5000 ms). A
  project changes tempo only through an explicit USER ruling in its Gameplay
  Profile; never infer a beat. Total span duration is free — a choice may
  stay open for hours — provided new choices keep arriving on the beat
  inside it. Arrivals hold the tempo, resolutions do not.
- **A meaningful choice is the unit.** One unit = information -> guess ->
  commitment -> consequence -> later-emotion influence. Every counted unit
  answers three questions: which later emotion it influences and how; what
  information lets the player guess; whether a basic guess survives when
  every hint is missed. No guess, no unit — a certain-outcome click never
  counts.
- **Consequences carry the next hints.** Each choice's observable
  consequence must deliver the hint material for the next choice. A span is
  threaded by one desire line; sub-events take their emotional sign relative
  to it.
- **Walking while guessing is engagement.** Traversal with a live guess (a
  search) is anticipation dwell inside an open choice; only commute with
  nothing to guess counts against the arrival gap. Never shrink a search to
  satisfy a gap bound.
- **Sufficiency never comes from the implementation.** Reading game code or
  counting existing content to decide what is enough lets supply define
  demand and passes every thin span. The quant author answers from player
  expectation for the genre/situation/cadence and attests implementation
  blindness; dwell and arrival-rate claims are challenged at quant review so
  six clicks are never called five minutes.
- **Beat Sheet authority.** Create or resolve an exact-version Gameplay
  Experience Beat Sheet against the approved Span Quant Sheet, with its
  mandatory exact-span Quantitative Experience Budget restating the approved
  quant floors, before realization. A sheet may tighten a floor but never
  loosen one without a new quant version. USER rulings and AI assumptions
  remain separate.
- **Fresh review gates.** Author and reviewer use file-only handoffs. A
  reviewer judges PASS/FAIL and never repairs/passes its own input.
- **Walkthrough first, segment second.** Realize one continuous player-time
  trace, then derive packet boundaries from player-state/intent/control/payoff
  changes.
- **Complete engagement, not forced choices.** Decision, mastery, discovery,
  expression, and payoff/recovery have different completeness rules. Do not
  add fake alternatives.
- **Non-gameplay does not self-promote.** Teleporter input, dialogue advance,
  raw inputs, straight locomotion, objective arrival, passive state change,
  control return, or presentation do not independently count as gameplay.
- **Decision proof is consequence proof.** A decision requires at least two
  contemporaneously reachable alternatives and controlled/equivalent evidence
  of distinct observable response/carry-forward consequences. Labels or input
  differences alone do not count.
- **Causal carry-forward.** A world response must generate the next player
  situation/intent/open question; unrelated objective re-issuance is not a
  gameplay chain.
- **Exact lineage.** Beat Sheets bind the exact Span Quant Sheet
  version/checksum; walkthroughs, packets, observation plans, runs, and
  acceptance bind the exact Beat Sheet version/checksum. Changed authority at
  any level makes downstream artifacts `STALE`.
- **Instrumentation ships with gameplay.** Every packet has an observation
  contract. Missing logging/capture hooks prevent production completion.
- **Fail closed before production.** A required kernel with no evidence path
  is `BLOCKED_BY_OBSERVABILITY`.
- **Keep evidence partitions separate.** Raw events, derived timeline, blind
  interpretation, and acceptance comparison are different artifacts. Raw logs
  never claim understanding, feeling, fun, or meaningfulness.
- **Paper prefilter is not runtime acceptance.** Design-authored
  `visible_and_known` can prefilter reception only. Runtime blind input comes
  solely from actual build evidence through `reader.py`/an equivalent reader.
- **Blind the runtime reader.** No Beat Sheet/trace/packet/code, semantic
  design ids, canonical action, available-action enumeration, hidden/future
  state, or implementation notes.
- **Counterfactual honesty.** One golden path cannot prove alternatives or
  failure adjustment. Use controlled branch/failure/performance probes.
- **Factory pass is not fun.** `PASS_FACTORY_CONFORMANCE` remains separate
  from `HUMAN_PLAYTEST_ACCEPTED`.
- **Quantitative gate before segment claims.** Run `measure-budget` before
  packet compilation and again on fresh production evidence before acceptance.
  Only `PASS_EXPERIENCE_BUDGET` may proceed; `NO_GAMEPLAY`, failure, or
  inconclusive evidence cannot be called a gameplay segment.
- **Adapters are authority.** Core never invents game verbs, systems, engine
  hooks, event names, budgets, or capture capabilities.
- **Artifacts land in the game repo.** Factory owns only contracts, blanks,
  schemas, and reader code.
- **Paths stay portable.** Persist game-repo-relative paths; absolute paths are
  active-run values only.

## Core contracts

- `docs/GAMEPLAY_EXPERIENCE_BEAT_SHEET_CONTRACT.md`
- `docs/PLAYABLE_WALKTHROUGH_TRACE_CONTRACT.md`
- `docs/PLAYABLE_BEAT_PACKET_CONTRACT.md`
- `docs/RUNTIME_OBSERVATION_AND_ACCEPTANCE_CONTRACT.md`
- `docs/PROJECT_ADAPTER_CONTRACT.md`
- `docs/OBSERVATION_READER.md`
