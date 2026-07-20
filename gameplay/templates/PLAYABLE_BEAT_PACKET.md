# Playable Beat Packet — `<PACKET_ID>`

- **Packet status:** `DRAFT | PRODUCTION_READY | BLOCKED_BY_OBSERVABILITY | STALE`

## Source experience authority

- Beat Sheet path/id/version token/checksum/status:
- Source Beat Sheet beat ids:
- Acceptance kernel ids:
- Fresh design-review PASS ref:
- Quantitative Experience Budget path/id:
- Exact-span budget gate result/ref: `PASS_EXPERIENCE_BUDGET`

## Source trace

- Trace id/version:
- First/last moment:
- Realization-review PASS ref:
- Candidate boundary signals:
- Merge rationale, if any:

## Entry state

- Runtime:
- World:
- Player knowledge:
- Grammar (recent verbs/rhythm/expectations/budget):

## 1. Experience contract

- Intended experience:
- Pacing function (adapter-defined):
- Primary/secondary engagement modes:
- Concrete player work:
- Agency/challenge source:
- Commitment and pressure:
- Observable world response:
- Intended player change (qualified):
- Carry-forward:
- Failure/misread/recovery and acceptable drift:
- Red lines:

## 2. Player-action contract

- Immediate intent:
- Visible and known:
- Core verb (adapter-declared):
- Ordered action/attempt arc:
- Ordered game responses:
- Knowledge landing (before -> after + evidence):
- Control arc:

## 3. Runtime contract

- Entry trigger:
- Control takeover/return:
- Camera framing:
- Presentation/HUD state:
- Dialogue/objective/completion order:
- State transitions:
- Completion feedback:
- Exit handoff:
- Production Adapter mapping refs:
- Runtime validation:

### Reception contract

- [ ] Required information is perceptible.
- [ ] Camera frames the relevant object/event.
- [ ] HUD/presentation layers do not interfere.
- [ ] Control takeover/return is signaled and ordered.
- [ ] Dialogue/objective/state/feedback order is explicit.
- [ ] Paper blind finding is linked as prefilter only.
- [ ] Runtime blind reading and human playtest remain required.

## 4. Observation contract

- Observation Adapter path/version:
- Observation plan path/status:
- Raw log/capture destination pattern:
- Instrumentation code/data hooks and owners:
- Enable/launch/flush/validation/reader commands:
- Blind projection exclusions:

| Kernel | Cue evidence | Action/attempt | World response + latency | Carry-forward | Evidence mode | Captures | Probe requirement |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

| Kernel | Ordered sequence id | After phase | Before phase | Ordered intermediate evidence |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

### Observability fail-closed check

- [ ] Every kernel has cue -> attempt -> response -> carry-forward evidence.
- [ ] Every declared ordered sequence has distinct same-run evidence strictly
      between its selected positive phases.
- [ ] Alternatives/failure/performance claims have controlled-probe coverage.
- [ ] Instrumentation ships with gameplay implementation.
- [ ] No raw/blind field asserts mental state or design intent.
- [ ] Missing evidence paths set `BLOCKED_BY_OBSERVABILITY`.

## Delta -> Delivery -> Proof

## Budget and dependencies

- Exact start/end boundary allocation:
- Duration/control/presentation/traversal threshold allocation:
- Counted gameplay measurement/kernel refs:
- Counted decision controlled/equivalent branch-consequence refs:
- Explicit non-gameplay-only activity exclusions:

## Unresolved deltas / observability blockers

## Exit state

- Runtime:
- World:
- Player knowledge:
- Approved grammar update:

## Fresh packet review

- Reviewer/session:
- Result: `PASS_PACKET_REVIEW | FAIL_PACKET_REVIEW`
- Quantitative gate verified `PASS_EXPERIENCE_BUDGET`: yes | no
- First invalid transformation boundary:
- Reviewer made no source edits: yes | no
