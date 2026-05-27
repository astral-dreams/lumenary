#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if pgrep -f "[e]ngine.dialectic --backfill" >/dev/null; then
  echo "$(date): Dialogue backfill active; skipping distillation backfill before deploy."
else
  python3 -m engine.distill --backfill --provider offline
fi
python3 -m engine.distill --validate-store
npm run build
npx wrangler pages deploy dist --project-name thelumenary --branch main
