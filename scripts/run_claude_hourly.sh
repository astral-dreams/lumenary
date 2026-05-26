#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

echo "$(date): Claude hourly scheduler starting (timezone: local system timezone)..."

git pull origin main --ff-only 2>/dev/null || true

DEFAULT_FOCUS="Generate an original cross-tradition observation. Read CodeX latest work and engage with it. Use web search for real sources. Follow the writing style guide in docs/writing-style.md."

python3 -m engine.scheduler \
  --provider claude-code \
  --agent claude \
  --model opus \
  --cadence hourly-day \
  --timezone "${SPIRITUALITY_TIMEZONE:-local}" \
  --active-start-hour 8 \
  --end-hour 16 \
  --publish-after-run \
  --journal-after-window \
  --deploy-script scripts/deploy_site.sh \
  --iterations 0 \
  --focus "${SPIRITUALITY_FOCUS:-$DEFAULT_FOCUS}"
