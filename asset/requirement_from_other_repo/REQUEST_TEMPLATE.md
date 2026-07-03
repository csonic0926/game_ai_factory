# Cross-repo factory request

## Request metadata

- Status: new
- Date: YYYY-MM-DD
- Source repo:
- Source repo path:
- Request owner / Codex context:
- Factory target area: prop_asset_workflow | reference_pair_workflow | render_tiles | validation | docs | other
- Priority: normal | urgent

## User-facing need

Describe what the target repo needs in plain language.

## Factory-side change requested

Describe what `game_asset_factory` should add or change.

Examples:

- Add a new prop spec and generate deliverables.
- Add validator support for a new handoff field.
- Add a new workflow option without changing existing wall/floor behavior.

## Asset / workflow details

- Asset family / workflow name:
- Variants or states:
- Target canvas size:
- Anchor / pivot rule:
- Transparency/background rule:
- Target project folder:
- Required metadata fields:
- Provider/model preference:
- Provider/model constraints:

## References and source context

List all files, images, specs, screenshots, or previous outputs that factory Codex should read.

- `path/or/link`
- `path/or/link`

## Acceptance criteria

Factory work is done only if these pass:

- [ ] Deliverable PNGs exist at the expected paths.
- [ ] Output canvas/alpha/anchor rules pass validation.
- [ ] Handoff metadata contains target repo paths and required IDs.
- [ ] Existing unrelated workflows are not changed.
- [ ] Relevant tests or validation commands pass.

Add any repo-specific checks here.

## Non-goals / do-not-change

List behavior that must not be changed.

- Do not rewrite unrelated floor/wall workflows.
- Do not rename existing asset IDs unless requested.

## Factory response

Factory Codex fills this section after handling the request.

- Status: new | in_progress | done | blocked
- Summary:
- Changed files:
- Commands run:
- Outputs / run roots:
- Blockers or follow-up:
