# DELIVERY CHANNELS — <project_id>

The delivery channels this game offers for story beats, consumed by the
delivery-planner module (`modules/delivery-planner/`). The planner uses this
list for rough channel intent; STEP 6.7 later reads `VISUAL_GRAMMAR.md` to
decide exact cutscene / player-operation binding. Every game's list is
different — declare only channels this game actually has or has concretely
planned, and be honest about runtime status: the planner uses `status` to mark
what lands now versus what waits.

For each channel state:

- **what it is** (one plain sentence);
- **status**: `AVAILABLE` (lands now — name the landing surface in
  `LANDING_SPEC.md`) / `PLANNED` (design exists, runtime missing — name
  what's missing) / `NOT_AVAILABLE`;
- **carries well / carries badly**: what kind of beat this channel is good
  and bad at (e.g. a reward pop-up cannot carry a HOLD beat).

| channel | what it is | status | carries well | carries badly |
|---|---|---|---|---|
| （declare per game） | | | | |
