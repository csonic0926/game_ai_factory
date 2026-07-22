# Gameplay Factory implementation status

This status is deliberately narrower than the umbrella proposal's completion
criteria. Contracts and synthetic tool tests are not a production pilot.

## Implemented in factory core

- Case 3 objective-gameplay front end: explicit blank/foreign/factory-native
  case boundary, primary-progression-first object model, script-first Step 1,
  and one-artifact Step 2 contract;
- dependency-free `prepare.py context` ownership guard and material compiler:
  stable project model + small objective frontier merge, exact repo evidence
  tokens, locale CSV lookup, runtime objective selection /
  completion proof, action/reward validation, compact context rendering, and
  the distinct `READY_FOR_HOW_DESIGN`, `READY_FOR_NEW_GAMEPLAY_DESIGN`, and
  `BLOCKED_BY_MATERIAL` states;
- blank `GAMEPLAY_DESIGN_MODEL.json`, `NEXT_GAMEPLAY_UNIT_INPUT.json`, and
  `OBJECTIVE_GAMEPLAY.md` templates plus machine-readable schemas and
  adversarial preparation tests;
- model-independent Case 3 production planning: the factory user may choose a
  Plan Mode or ordinary model, while both persist the same SHA-bound
  `PRODUCTION_PLAN_MANIFEST.json` plus `N` Markdown change-unit plans;
- dependency-free `plan.py validate` checks exact objective-row coverage,
  source hash freshness, required plan sections/metadata, portable ownership,
  existing repo evidence, plan dependency cycles, ready/blocked consistency,
  and exclusive planned-path ownership;
- production-plan schemas/templates and adversarial tests, plus one real IMT
  sample compiling the nine-row objective into two non-overlapping plans;
- automatic Step 4 caller handoff: a normal high-level gameplay-production
  request treats `READY_FOR_EXECUTION` as intermediate, requires the original
  caller/orchestrator to execute the persisted plans without a second user
  prompt, and reserves plan-only stopping for explicit requests;

- quant-first demand ordering: Span Quant Sheet template/module (span
  boundaries -> cadence contract -> implementation-blind playable-content
  inventory -> derived floors), fresh quant review gate, and
  Beat-Sheet-satisfies-quant design review checks;
- choice-cadence demand semantics: the meaningful-choice unit (information
  -> guess -> commitment -> consequence -> later-emotion influence) with
  three-question qualification, the factory canonical beat (3–5 s arrivals,
  5000 ms max gap, explicit-USER-override only), generator/one-shot
  inventory with a cadence sustainability walk, the chain rule
  (consequences deliver the next choice's hints), desire-line emotional
  signs, and the search-vs-commute traversal distinction — enforced at
  paper gates (quant review + design review);
- v1 Gameplay Experience Beat Sheet authority/authoring/review contract;
- exact version/checksum lineage into walkthroughs, packets, observation
  plans, runtime evidence, and acceptance;
- revised walkthrough and four-layer packet contracts/templates;
- separate Project Gameplay, Production, and Observation Adapter contracts;
- canonical raw evidence, observation-mapping, and kernel-selector schemas;
- dependency-free reference reader for validation, normalization, timeline
  reconstruction/latency, runtime blind projection, evidence viewing, and
  acceptance-comparison input;
- quantitative exact-span gate with runtime-owned run/session selection,
  non-gameplay-only chain rejection, non-inflating content counts, and
  presentation-adjusted effective control measurement;
- optional fail-closed `ordered_sequences` acceptance matching for distinct
  same-run intermediate events between positive phase boundaries;
- fail-closed integrity and contamination checks;
- manual fresh design/realization/packet/landing/runtime acceptance review
  templates;
- unit tests using synthetic evidence.

## Not yet proven or complete

- the compact Case 3 Step 1/Step 2/Step 3 format now has one real-project
  design and planning sample, but its planning token cost and implementation
  usefulness are not proven until production executes the persisted plans;
- Case 1 idea discovery and Case 2 foreign-repo onboarding/refactoring are not
  implemented by this workflow;

- no real game-owned Beat Sheet -> implementation -> actual build evidence
  pilot has been supplied or run from this factory task;
- no real project Observation Adapter normalizer is validated;
- no `LIVE_BLIND_RUN` plus `CONTROLLED_BRANCH_PROBE` evidence set exists here;
- no deliberate implementation/reception mismatch has yet demonstrated correct
  failure routing;
- no second project/gameplay shape has demonstrated portability;
- no human playtest has accepted enjoyment/commercial value;
- no real span has driven the quant-first tower (quant sheet -> Beat Sheet ->
  implementation) end to end, so sufficiency-assessment quality is untuned;
  calibration levers (instruction tuning; an optional independent code-view
  subagent producing a supply-side gameplay report) are deferred to the tune
  phase;
- runtime cadence measurement does not exist: `reader.py` and the budget
  schema still measure the duration/control/gap ontology, and choice-arrival
  events are not yet an Observation Adapter concept. The quant cadence is
  enforced on paper only; the budget JSON's gap caps act as crude
  arrival-gap proxies until the tune phase defines arrival measurement;
- the creative step machine/`.5` worker automation remains intentionally
  deferred until pilot formats stabilize.

Therefore the factory request remains **in progress**. The reference reader is
an MVP implementation candidate, not evidence that Phase 1 or cross-project
closure has passed.
