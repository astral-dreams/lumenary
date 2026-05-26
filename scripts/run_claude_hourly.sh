#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

# Auto-detect system timezone so it follows you when traveling
SYSTEM_TZ=$(readlink /etc/localtime | sed 's|.*/zoneinfo/||')

echo "$(date): Claude hourly scheduler starting (timezone: ${SYSTEM_TZ})..."

git pull origin main --ff-only 2>/dev/null || true

python3 -m engine.scheduler \
  --provider claude-code \
  --agent claude \
  --model opus \
  --cadence hourly-day \
  --timezone "${SYSTEM_TZ}" \
  --active-start-hour 8 \
  --end-hour 17 \
  --publish-after-run \
  --journal-after-window \
  --deploy-script scripts/deploy_site.sh \
  --iterations 0 \
  --focus "${SPIRITUALITY_FOCUS:-Generate an original cross-tradition observation. Read CodeX's latest work and engage with it. Use web search for real sources. Follow the writing style guide in docs/writing-style.md.}"
