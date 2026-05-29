#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

. scripts/lumenary_env.sh

if [ "${LUMENARY_JOURNAL_SCHEDULED:-0}" = "1" ]; then
  TODAY="$(date +%F)"
  STAMP_FILE="state/journal_last_run_date"
  HOUR="$(date +%H)"
  MINUTE="$(date +%M)"
  NOW_MINUTES=$((10#$HOUR * 60 + 10#$MINUTE))
  START_MINUTES=$((17 * 60 + 15))

  if [ "$NOW_MINUTES" -lt "$START_MINUTES" ]; then
    echo "$(date): Journal schedule guard: before 17:15 ${LUMENARY_ACTIVE_TIMEZONE:-local}, skipping."
    exit 0
  fi

  if [ -f "$STAMP_FILE" ] && [ "$(cat "$STAMP_FILE")" = "$TODAY" ]; then
    echo "$(date): Journal schedule guard: journal already ran for $TODAY ${LUMENARY_ACTIVE_TIMEZONE:-local}, skipping."
    exit 0
  fi
fi

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

if [ "${LUMENARY_JOURNAL_SCHEDULED:-0}" = "1" ]; then
  mkdir -p state
  date +%F > state/journal_last_run_date
fi
