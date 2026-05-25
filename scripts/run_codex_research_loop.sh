#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

python3 -m engine.scheduler \
  --provider codex-cli \
  --search \
  --interval-minutes "${SPIRITUALITY_INTERVAL_MINUTES:-120}" \
  --focus "${SPIRITUALITY_FOCUS:-Generate original cross-tradition ideas with rigorous epistemic labeling.}"
