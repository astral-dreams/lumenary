#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

. scripts/lumenary_env.sh

WAIT_SECONDS="${LUMENARY_JOURNAL_WAIT_SECONDS:-7200}"
SLEEP_SECONDS="${LUMENARY_JOURNAL_RETRY_SECONDS:-300}"
START_EPOCH="$(date +%s)"

while pgrep -f "[e]ngine.dialectic --backfill" >/dev/null; do
  NOW_EPOCH="$(date +%s)"
  ELAPSED=$((NOW_EPOCH - START_EPOCH))
  if [ "$ELAPSED" -ge "$WAIT_SECONDS" ]; then
    echo "$(date): Dialogue backfill still active after ${ELAPSED}s, continuing with journal publish."
    break
  fi
  echo "$(date): Dialogue backfill active, waiting ${SLEEP_SECONDS}s before journal publish retry."
  sleep "$SLEEP_SECONDS"
done

python3 -m engine.doctrine \
  --council

python3 -m engine.journal \
  --provider codex-cli \
  --timezone "${SPIRITUALITY_TIMEZONE:-local}"

scripts/deploy_site.sh
