# Gameplay Factory

The Gameplay Factory translates required story/world changes into the way a
player experiences them over continuous play time:

```text
story anchors + current state + project adapters + gameplay grammar state
  -> Intended Player continuous walkthrough
  -> delta-driven beat segmentation + blinded First-time Player check
  -> playable beat packets for production
```

Phase 0 is deliberately **document-first and manual**. The factory currently
owns contracts, blank answer sheets, and artifact templates—not a CLI, skill,
or step machine. Filled adapters and all produced traces/packets live in the
game repo under `<GAMEPLAY_ROOT>`.

AI callers start at [`docs/AI_CALLER_LANDING.md`](docs/AI_CALLER_LANDING.md).

## Layout

```text
AGENTS.md                         caller rules
docs/AI_CALLER_LANDING.md        manual Phase 0 workflow
docs/*_CONTRACT.md               trace, packet, and adapter contracts
adapters/registry.example.md     optional local phonebook format (no projects)
adapters/registry.local.md       ignored machine-local project routing
adapters/_template/              blank project + production answer sheets
templates/                       blank game-owned artifact shapes
```

## Ownership boundary

- **Factory repo:** project-agnostic questions, schemas, invariants, and blank
  templates.
- **Game repo:** project answers, story-anchor inputs, walkthroughs, packets,
  reports, grammar state, and production mappings.

The caller receives the game repo explicitly or resolves it from the current
Git working tree. Versioned adapter paths are relative to that root. A local
registry is only a convenience for calls launched from the factory directory;
it is ignored and is never project authority.
