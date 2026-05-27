#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"

mkdir -p runs/map-refresh

STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="runs/map-refresh/${STAMP}.log"

WAIT_SECONDS="${LUMENARY_MAP_WAIT_SECONDS:-7200}"
SLEEP_SECONDS="${LUMENARY_MAP_RETRY_SECONDS:-300}"
START_EPOCH="$(date +%s)"

while pgrep -f "[e]ngine.dialectic --backfill" >/dev/null; do
  NOW_EPOCH="$(date +%s)"
  ELAPSED=$((NOW_EPOCH - START_EPOCH))
  if [ "$ELAPSED" -ge "$WAIT_SECONDS" ]; then
    echo "$(date): Dialogue backfill still active after ${ELAPSED}s, continuing with living map refresh." | tee -a "$LOG"
    break
  fi
  echo "$(date): Dialogue backfill active, waiting ${SLEEP_SECONDS}s before living map refresh retry." | tee -a "$LOG"
  sleep "$SLEEP_SECONDS"
done

{
  echo "$(date): Starting living map refresh."
  echo "$(date): Validating map source files."

  test -s publication/growth/growth.jsonl
  test -s hypotheses/ideas.jsonl
  test -s graph/concept-graph.seed.json
  test -s sources/sources_index.jsonl

  echo "$(date): Backfilling missing reader-facing finding copy and validating existing copy."
  python3 -m engine.distill --backfill --provider offline
  python3 -m engine.distill --validate-store

  echo "$(date): Building site so all three living SVG maps are regenerated."
  npm run build

  echo "$(date): Checking generated Map page."
  grep -q "The Lumenary's Knowledge Map" dist/map/index.html
  grep -q "The Lumenary's Method Map" dist/map/index.html
  grep -q ">Research Map<" dist/map/index.html
  grep -q "living knowledge graph" dist/map/index.html

  echo "$(date): Deploying refreshed living maps."
  npx wrangler pages deploy dist --project-name thelumenary --branch main

  echo "$(date): Living map refresh complete."
} 2>&1 | tee "$LOG"
