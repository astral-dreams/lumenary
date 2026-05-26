#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

echo "$(date): Overnight parallel research tick."

python3 -m engine.parallel_research \
  --stop-at "${SPIRITUALITY_STOP_AT:-2026-05-26T07:00:00-07:00}" \
  --launchagent-plist "${SPIRITUALITY_LAUNCHAGENT_PLIST:-/Users/johnforrester/Library/LaunchAgents/com.lumenary.overnight-parallel.plist}" \
  --unload-after-stop \
  --focus "${SPIRITUALITY_FOCUS:-Generate a new original cross-tradition finding for The Lumenary. Use source grounding, engage prior Codex and Claude findings, follow docs/writing-style.md, and do not use em dashes.}"

echo "$(date): Overnight parallel research tick complete."
