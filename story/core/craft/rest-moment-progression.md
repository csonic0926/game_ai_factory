# Rest Moment Progression

*Designs “rest/town” story moments that give the player a limited number of actions to improve combat readiness (shop/training/skills/gear/positioning), and implements those moments via event timelines and routing landed through the adapter `LANDING_SPEC.md`.*

Use this doc when the user wants progression to come from **short, intentional downtime moments** (e.g. “rest in town for five days / five actions”), and accepts that some fights are unwinnable if the player refuses to prepare.

## Design goals

- Teach the player: **prepare before fights** (gear, skills, positioning), not “grind stats forever”.
- Make preparation carry **opportunity cost**: only N actions; can’t buy/train everything.
- Treat failure as a valid outcome: “這就是江湖” is a supported outcome (example flavor from a wuxia project).

## Files

Land all timeline, event, and locale changes via the adapter `LANDING_SPEC.md`. The data you will typically touch:

- the event timeline data (the sequence; options; routes)
- the routed event data (story/battle; recruit fields)
- the locale data (all player-facing text via keys)

Typical progression content data you might also touch:
- item/shop data (shop inventory comes from here if implemented)
- skill data (if you implement skill acquisition) — see `<BATTLE_SYSTEM>` if declared

## Workflow

### Step 1) Define the rest moment contract

Write down:

- `N` actions (e.g. 5)
- Allowed actions (examples):
  - Shop: buy/upgrade weapon or armor
  - Training: improve a constrained base stat (still respecting narrative caps)
  - Technique: unlock a skill or improve a skill multiplier/range access
  - Recon: preview the next battle’s enemy “signature”
  - Position drill: remind/teach slot-index positioning before battle

### Step 2) Make actions teach the combat pillars

Every action should reinforce at least one combat pillar:

- Gear-first: shop/upgrade meaningfully changes success odds.
- Skill range: training/technique teaches row/column value (not just “+damage”).
- Positioning: give explicit prompts to adjust slots before the next fight.

### Step 3) Implement as a repeatable pattern in timelines

Pattern suggestion (data-friendly, minimal code):

1. A timeline step that sets the scene (resting in town).
2. A looped choice node with options representing actions.
3. Each choice routes to a short sub-timeline (1–3 lines) applying its effects.
4. After each action, decrement remaining actions (state) and return to the choice node.
5. When actions reach 0, route to the next story/battle event.

If you don’t yet have a generic “counter” system in data, implement a simpler first version:

- Create `N` separate “day” nodes in the event timeline data (day1..dayN),
  each offering choices, routing to day+1 after a choice resolves.

### Step 4) Keep player-facing text in locales

All UI strings must be translation keys (no hard-coded strings in code):

- Add timeline lines/options to the locale data via the adapter `LANDING_SPEC.md`
- Use key patterns consistent with the project’s existing content (key grammar per the adapter `LANDING_SPEC.md`)

## Guardrails

- Solve difficulty through preparation tradeoffs, not base stat inflation.
- Prefer giving the player **gear and information** over raw stat boosts.
- If a player refuses preparation, allow a loss outcome and make the cause legible.

## Output format (what to propose/implement)

- Rest moment spec: N actions + option list
- For each option: pillar taught + concrete effect
- Timeline structure: main timeline id + day nodes or loop design
- Localization keys to add

## Reference implementation: event-timeline CSV runtime (rpg-1 heritage)

> Original rpg-1 file mappings, kept as a worked example only. Real projects
> follow their adapter `LANDING_SPEC.md` instead.

- `settings/event_timelines.csv` (the sequence; options; routes) — “day” nodes live here in the simple first version
- `settings/event.csv` (routed events; story/battle; recruit fields)
- `locales/locales.csv` (all player-facing text via keys) — use `story_telling.*` style keys consistent with existing content
- `settings/items.csv` (shop inventory comes from here if implemented)
- `settings/skills.csv` / `settings/character_skills.csv` (if you implement skill acquisition)
