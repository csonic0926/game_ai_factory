# LANDING SPEC — rpg-1

Status: AVAILABLE (pointer spec)

The authoritative landing mechanics for rpg-1 are maintained in the user's
skill `rpg-1-runtime-csv-landing`
(`~/.claude/skills/rpg-1-runtime-csv-landing/SKILL.md`). Workers on chapter
STEP 7/7.5 (and 19/19.5) MUST read that skill file and follow it verbatim.

Contract answers (summary; the skill file wins on any conflict):

1. **Target files**: `settings/event.csv`, `settings/event_timelines.csv`,
   `settings/world_map_node.csv`, `locales/locales.csv`; chapter-entry wiring
   via `settings/misc.csv` + `settings/chapter_intro_entries.csv`.
2. **Id & key grammar**: per the skill (event id patterns, `story.*` /
   `choice.*` / `world_map.*` locale keys).
3. **Granularity**: one click per timeline row.
4. **Choice & routing**: choice columns on timeline rows; `battle_id` is a
   cross-branch contract (same fight ⇒ same id; variants split ids).
5. **Locale landing**: zh-TW authored; en/ja natural lines landed with it.
6. **Integrity**: the skill's integrity checklist + `scripts/validate_settings.py`
   in the game repo.
7. **Battle hooks**: `type=BATTLE` events referencing `battles.csv`;
   win/lose routing per `win_event_id`/`lose_event_id`.
