#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

HOUR=$(date +%H)
if [ "$HOUR" -ge 17 ]; then
  echo "$(date): Past 5pm cutoff, skipping."
  exit 0
fi

echo "$(date): Starting hourly Claude research run..."

git pull origin main --ff-only 2>/dev/null || true

python3 -m engine.run \
  --provider claude-code \
  --agent claude \
  --model opus \
  --focus "${SPIRITUALITY_FOCUS:-Generate an original cross-tradition observation. Read CodeX's latest work and engage with it. Use web search for real sources. Follow the writing style guide in docs/writing-style.md.}"

echo "$(date): Research complete. Building and deploying site..."

npm run build
npx wrangler pages deploy dist \
  --project-name thelumenary \
  --branch main \
  --commit-dirty=true

echo "$(date): Committing and pushing..."

git add -A
git commit -m "$(cat <<'COMMIT'
Hourly Claude research run and site publish

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
COMMIT
)" || true

git push origin main || true

echo "$(date): Hourly run complete."
