# requirement_from_other_repo

This folder is the intake contract for other repositories that need `game_asset_factory` to add or update asset-generation functionality.

If another repo only needs to call existing factory tools, start with
[`docs/AI_CALLER_LANDING.md`](../docs/AI_CALLER_LANDING.md) instead of creating
a request here.

## Who should use this

Use this when another repo's Codex needs factory-side work, for example:

- new prop / object asset families
- new tile, wall, or floor workflow variants
- new provider/model constraints
- new output handoff metadata for a target game repo
- validation or cleanup changes required by another repo's asset pipeline

## Source-repo Codex workflow

1. Read this README and `REQUEST_TEMPLATE.md`.
2. Create one request Markdown file in this folder, named:
   - `YYYY-MM-DD_<source_repo>_<short_topic>.md`
3. Fill the template with concrete engineering requirements, not only art taste.
4. Include or link any required reference images / specs / target repo files.
5. Do not change factory implementation code from the source repo unless the user explicitly asks for a cross-repo patch.
6. Ask the factory Codex to read the request file and update `game_asset_factory` accordingly.

## Factory Codex workflow

When acting inside `game_asset_factory`:

1. Read the incoming request file first.
2. Read `docs/REPO_MEMORY.md` and `docs/CURRENT_JOB.md` before changing workflow behavior.
3. Decide whether the request is:
   - supported by existing CLI/specs,
   - a new spec/example only,
   - or a factory feature change.
4. Preserve existing floor/wall/prop behavior unless the request explicitly targets it.
5. Implement the smallest factory-side change that satisfies the request.
6. Run relevant validation/tests or explain why they were not run.
7. Update the request file with a short factory response: status, changed files, commands, outputs, and blockers.
8. Update `docs/CURRENT_JOB.md`; update `docs/REPO_MEMORY.md` only for durable gotchas or rules.

## Good request shape

A good request answers:

- Which repo is asking?
- What asset/workflow is needed?
- What exact deliverables should the factory produce?
- What target canvas, anchor, transparency, folder, and metadata rules apply?
- Which provider/model should be used or avoided?
- What should count as pass/fail?
- What existing files or screenshots should be treated as references?

If a request only says "make it look better," factory Codex should ask for missing acceptance criteria before changing behavior.
