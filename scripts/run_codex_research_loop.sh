#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

python3 -m engine.scheduler \
  --provider codex-cli \
  --search \
  --cadence "${SPIRITUALITY_CADENCE:-hourly-day}" \
  --interval-minutes "${SPIRITUALITY_INTERVAL_MINUTES:-60}" \
  --timezone "${SPIRITUALITY_TIMEZONE:-America/Los_Angeles}" \
  --active-start-hour "${SPIRITUALITY_RESEARCH_START_HOUR:-8}" \
  --end-hour "${SPIRITUALITY_RESEARCH_END_HOUR:-17}" \
  --publish-after-run \
  --journal-after-window \
  --deploy-script "${SPIRITUALITY_DEPLOY_SCRIPT:-scripts/deploy_site.sh}" \
  --focus "${SPIRITUALITY_FOCUS:-Generate original cross-tradition ideas with rigorous epistemic labeling.}"
