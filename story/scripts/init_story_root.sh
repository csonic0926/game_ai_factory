#!/usr/bin/env bash
# Bootstrap the canonical <STORY_ROOT> layout for a game project.
# Usage: init_story_root.sh /absolute/path/to/game/design/story
set -euo pipefail
FACTORY="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="${1:?usage: init_story_root.sh <STORY_ROOT>}"

mkdir -p "$ROOT"/state/{world_baselines,character_baselines,characters,cast_management,chapter_sources,briefs} \
         "$ROOT"/{chapter_event_graphs,runtime_scene_drafts,qa/reports,knowledge,story_world,templates,outcomes}

CORE_VARS="$ROOT/state/WORKFLOW_CORE_VARIABLES.md"
if [ ! -f "$CORE_VARS" ]; then
  cp "$FACTORY/core/schemas/templates/WORKFLOW_CORE_VARIABLES.template.md" "$CORE_VARS"
  echo "created $CORE_VARS (USER-authored file — fill in your creative rules)"
fi

for t in "$FACTORY"/core/schemas/templates/*.md; do
  base="$(basename "$t")"
  [ "$base" = "WORKFLOW_CORE_VARIABLES.template.md" ] && continue
  [ -f "$ROOT/templates/$base" ] || cp "$t" "$ROOT/templates/$base"
done

echo "STORY_ROOT ready: $ROOT"
