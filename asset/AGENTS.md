# AGENTS.md

## Memory policy

- Keep `AGENTS.md` short.
- `AGENTS.md` should define **how repo memory is stored and maintained**, not hold a growing list of project facts.
- Store durable workflow notes, render caveats, and reference-PNG rules in:
  - `docs/REPO_MEMORY.md`
- Store the active implementation brief / evolving task state in:
  - `docs/CURRENT_JOB.md`

## Read / write rules

- Before changing render workflow, reference PNG workflow, or sample scene assumptions, read:
  - `docs/REPO_MEMORY.md`
- When continuing an in-flight implementation, read:
  - `docs/CURRENT_JOB.md`
- When discovering a new durable gotcha or rule, write it to:
  - `docs/REPO_MEMORY.md`
- When the current task plan, assumptions, or partial progress changes, update:
  - `docs/CURRENT_JOB.md`
- If a new note conflicts with an old one, resolve the conflict by **rewriting the memory file coherently** instead of stacking contradictory bullets.
- Before ending a session with unfinished workflow review / implementation, write the latest decisions and next-step state into:
  - `docs/REPO_MEMORY.md`
  - `docs/CURRENT_JOB.md`
- Keep memory notes practical and repo-specific:
  - known failure modes
  - framing / occupancy rules
  - canonical-vs-corrected reference distinctions
  - debug checklists

## Cross-repo requirement intake

- If another repo only needs to call existing factory tools, start with:
  - `docs/AI_CALLER_LANDING.md`
- Store requests from other repos in:
  - `requirement_from_other_repo/`
- Other-repo Codex agents should follow:
  - `requirement_from_other_repo/README.md`
  - `requirement_from_other_repo/REQUEST_TEMPLATE.md`
- Factory-side Codex should treat each request file as the source of truth, then update specs/code/docs as needed.
- After handling a request, append a short factory response to that request file and update `docs/CURRENT_JOB.md`.

## Stable repo rules

- Prefer keeping sample export objects in one stable scene: `examples/sample_factory.blend`.
- Avoid splitting full/half floor samples into separate `.blend` files unless there is a Blender-level limitation we cannot work around.
- For floor height variants, prefer:
  - one canonical sample object/setup in the main sample scene
  - per-run object filtering and/or height override in the render pipeline
- Existing code already supports floor height override in `blender/scripts/render_tiles.py` via `ITF_FLOOR_HEIGHT`.
