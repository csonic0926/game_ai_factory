#!/usr/bin/env bash
# Bootstrap the canonical <STORY_ROOT> layout for a game project.
# Usage: init_story_root.sh /absolute/path/to/game/design/story
set -euo pipefail
FACTORY="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="${1:?usage: init_story_root.sh <STORY_ROOT>}"

mkdir -p "$ROOT"/state/{world_baselines,character_baselines,characters,cast_management,chapter_sources,briefs} \
         "$ROOT"/{chapter_event_graphs,runtime_scene_drafts,qa/reports,knowledge,story_world,templates,outcomes}

# Sovereignty files (USER-authored, tools read-only). The legacy single file
# WORKFLOW_CORE_VARIABLES.md was split into these two (2026-07-07); a legacy
# project that still has the old file keeps it — we never overwrite it.
WORLD_RULES="$ROOT/state/WORLD_RULES.md"
if [ ! -f "$WORLD_RULES" ]; then
  cp "$FACTORY/core/schemas/templates/WORLD_RULES.template.md" "$WORLD_RULES"
  echo "created $WORLD_RULES (USER-authored — what is TRUE in the world)"
fi
NARRATIVE_DELIVERY="$ROOT/state/NARRATIVE_DELIVERY.md"
if [ ! -f "$NARRATIVE_DELIVERY" ]; then
  cp "$FACTORY/core/schemas/templates/NARRATIVE_DELIVERY.template.md" "$NARRATIVE_DELIVERY"
  echo "created $NARRATIVE_DELIVERY (USER-authored — how the game speaks)"
fi

mkdir -p "$ROOT/beat_sheets"

for t in "$FACTORY"/core/schemas/templates/*.md; do
  base="$(basename "$t")"
  case "$base" in
    WORKFLOW_CORE_VARIABLES.template.md|WORLD_RULES.template.md|NARRATIVE_DELIVERY.template.md) continue ;;
  esac
  [ -f "$ROOT/templates/$base" ] || cp "$t" "$ROOT/templates/$base"
done

echo "STORY_ROOT ready: $ROOT"
