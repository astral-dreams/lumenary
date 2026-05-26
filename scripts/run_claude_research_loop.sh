#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

python3 -m engine.scheduler \
  --provider claude-code \
  --agent claude \
  --interval-minutes "${SPIRITUALITY_INTERVAL_MINUTES:-120}" \
  --focus "${SPIRITUALITY_FOCUS:-Generate original cross-tradition ideas. Read CodeX observations and engage with them; agree, disagree, extend, or challenge. Use web search for real sources.}"
