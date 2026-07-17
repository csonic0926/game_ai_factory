# Gameplay adapter local-registry example

Gameplay adapters and all generated artifacts live in their game repos. The
factory does not commit registrations for individual games.

Calls should normally provide the game-repo path explicitly or run from the
game repo so its Git root can be resolved. For machine-local convenience,
copy only the entry format below into the ignored file
`registry.local.md`:

```text
- <project_id> → /absolute/path/to/game/repo/
```

The value is the game-repo root, not the adapter directory. The caller derives
the fixed `design/gameplay/adapter/` location from that root. Never commit
`registry.local.md` or add a real project path to this example.
