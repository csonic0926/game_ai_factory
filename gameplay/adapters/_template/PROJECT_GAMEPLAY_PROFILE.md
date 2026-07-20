# Project Gameplay Profile — blank answer sheet

Replace every `TBD`. This filled file belongs in the game repo at
`<GAMEPLAY_ROOT>/adapter/PROJECT_GAMEPLAY_PROFILE.md`.

## Identity and authoritative inputs

- `<PROJECT_ID>`: TBD
- `<STORY_ANCHOR_SOURCE>`: TBD_REPO_RELATIVE_PATH_OR_INTERFACE
- `<CURRENT_STATE_SOURCE>`: TBD_REPO_RELATIVE_PATH_OR_INTERFACE
- `<PRIMARY_LOCALE>`: TBD
- Target game mode/platform assumptions: TBD

`<GAME_REPO>` is the active call's resolved Git root and `<GAMEPLAY_ROOT>` is
the fixed `<GAME_REPO>/design/gameplay`; neither is stored here. Keep
game-owned paths relative to the Git root and do not commit a developer's
absolute filesystem path.

Explain how an author selects the exact story-anchor range and current-state
snapshot without copying a stale summary:

TBD

## Player frames, core fantasy, and sovereignty

- Declared player frames (first-time/returning/expert/etc.): TBD
- What each frame already knows/can do/wants: TBD
- Allowed mistakes/navigation drift/risk/attention assumptions: TBD
- Core player fantasy/desires this gameplay serves: TBD
- Gameplay sovereignty/player-control red lines: TBD

## Player verbs

List only implemented or production-approved verbs. Add rows as needed.

| Verb id | Player intent served | Input/selection | Preconditions | Immediate response | Resulting state | Typical cost | Unsupported cases |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Systems and playable spaces

Describe relevant movement, interaction, combat/minigame, inventory,
progression, failure/retry, and navigation systems. Mark absent systems
`NOT_AVAILABLE`.

TBD

## Engagement and challenge generators

Describe how this project supports decision, execution/mastery,
discovery/interpretation, expression/social, and payoff/recovery. For each,
name meaningful alternatives or skill dimensions, feedback/adjustment,
evidence/hypothesis changes, world recognition, and failure/retry conventions.
Mark unsupported modes `NOT_AVAILABLE`.

TBD

## Presentation modes

| Mode id | What player sees/hears | Control owner | Entry cue | Exit/return cue | HUD behavior | Supported limits |
| --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Explicitly list unsupported presentation modes/operations:

TBD

## Control model

- Legal `control_owner` values: TBD
- Input-lock semantics: TBD
- Takeover signalling: TBD
- Return-of-control signalling: TBD
- Shared/partial-control rules or `NOT_AVAILABLE`: TBD

## Camera, HUD, objective, and reception capabilities

- Camera framing/focus operations: TBD
- HUD layers and hide/show rules: TBD
- Objective presentation/update/completion order: TBD
- Dialogue/AVG/cutscene presentation constraints: TBD
- Completion feedback channels: TBD
- Accessibility or readability constraints: TBD

## Gameplay grammar

- Choice-cadence override: `NONE | <USER-ruling ref/date + target range and
  max arrival gap ms>` — the factory's canonical beat is one new meaningful
  choice every 3–5 seconds (max arrival gap 5000 ms); only an explicit USER
  ruling recorded here changes it, and the factory never infers a tempo.
- Project-defined rhythm axes and legal values: TBD
- Recent-verb repetition limits/preferences: TBD
- Player expectation/payoff conventions: TBD
- Completion-feedback conventions: TBD
- Beat-to-beat handoff conventions: TBD
- Initial grammar-state source or initialization rule: TBD

## Budget and capacity

Give explicit per-beat or per-segment limits. Use `NOT_AVAILABLE` only for a
capability that cannot be used; do not leave a limit blank.

| Cost axis | Limit | Measurement | Escalation owner |
| --- | --- | --- | --- |
| Player time | TBD | TBD | TBD |
| Interaction complexity | TBD | TBD | TBD |
| New assets | TBD | TBD | TBD |
| New sound | TBD | TBD | TBD |
| Engineering/data work | TBD | TBD | TBD |
| Player attention/readability | TBD | TBD | TBD |

## Human review and evidence

- Trace/packet approval owner: TBD
- Where USER rejections are recorded: TBD_PATH
- Where USER gameplay rulings/Beat Sheet approvals are recorded: TBD_PATH
- Human playtest gate and evidence path: TBD
