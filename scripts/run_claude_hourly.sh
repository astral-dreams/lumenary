#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

. scripts/lumenary_env.sh

notify() {
  local title="$1"
  local body="$2"

  echo "$(date): ${title}: ${body}"

  osascript \
    -e 'on run argv' \
    -e 'display notification (item 2 of argv) with title (item 1 of argv) subtitle "Lumenary"' \
    -e 'end run' \
    "$title" \
    "$body" 2>/dev/null || true
}

current_direction() {
  python3 - <<'PY'
from pathlib import Path

path = Path("state/next_directions.md")
if not path.exists():
    print("Cross-tradition observation in progress")
    raise SystemExit

lines = []
for raw in path.read_text().splitlines():
    text = raw.strip()
    if not text or text.startswith("#"):
        continue
    if text.startswith("- "):
        text = text[2:].strip()
    lines.append(text)

priority = [
    line for line in lines
    if "next" in line.lower() or "priority" in line.lower() or "source-grounded" in line.lower()
]
choice = (priority or lines or ["Cross-tradition observation in progress"])[0]
print(choice[:180])
PY
}

latest_idea_field() {
  local field="$1"
  python3 - "$field" <<'PY'
import json
import sys
from pathlib import Path

field = sys.argv[1]
path = Path("hypotheses/ideas.jsonl")
value = ""

if path.exists():
    for raw in path.read_text().splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        value = str(record.get(field) or value)

print(value)
PY
}

trap 'notify "Run failed" "Check runs/claude-hourly.stderr.log for details."' ERR

HOUR=$(date +%H)
HOUR_NUMBER=$((10#$HOUR))

if [ "$HOUR_NUMBER" -lt 7 ] || [ "$HOUR_NUMBER" -ge 17 ]; then
  echo "$(date): Outside research window (7am-5pm ${LUMENARY_ACTIVE_TIMEZONE:-local}), skipping."
  exit 0
fi

notify "Research starting" "Pulling latest and beginning a new observation..."
git pull origin main --ff-only 2>/dev/null || true

DIRECTION="$(current_direction)"
notify "Researching" "$DIRECTION"

DEFAULT_FOCUS="Generate an original cross-tradition observation. Read Codex latest work and engage with it. Use web search for real sources. Follow the writing style guide in docs/writing-style.md. Do not use em dashes."
BEFORE_ID="$(latest_idea_field idea_id)"

python3 -m engine.run \
  --provider claude-code \
  --agent claude \
  --model opus \
  --focus "${SPIRITUALITY_FOCUS:-$DEFAULT_FOCUS}"

AFTER_ID="$(latest_idea_field idea_id)"
TITLE="$(latest_idea_field title)"
if [ -z "$TITLE" ]; then
  TITLE="new observation"
fi

if [ -n "$AFTER_ID" ] && [ "$AFTER_ID" != "$BEFORE_ID" ]; then
  notify "New finding" "$TITLE"
else
  notify "New finding" "No new title detected. Check the run log."
fi

bash scripts/deploy_site.sh 2>&1 | tail -3

git add -A
git commit -m "Research run $(date +%H:%M)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>" 2>/dev/null || true

git push origin main 2>/dev/null || true

notify "Run complete" "Published: $TITLE"
