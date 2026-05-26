#!/usr/bin/env bash
set -euo pipefail

export PATH="/Users/johnforrester/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

cd /Users/johnforrester/spirituality

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
for raw in path.read_text(encoding="utf-8").splitlines():
    text = raw.strip()
    if not text or text.startswith("#"):
        continue
    if text.startswith("- "):
        text = text[2:].strip()
    lines.append(text)

priority = [
    line for line in lines
    if "next" in line.lower()
    or "priority" in line.lower()
    or "source-grounded" in line.lower()
]
choice = (priority or lines or ["Cross-tradition observation in progress"])[0]
print(choice[:180])
PY
}

pause_until() {
  python3 - <<'PY'
from datetime import datetime
from pathlib import Path

path = Path("state/research_pause_until")
if not path.exists():
    raise SystemExit(0)

value = path.read_text(encoding="utf-8").strip()
try:
    pause_until = datetime.fromisoformat(value)
except ValueError:
    path.unlink(missing_ok=True)
    raise SystemExit(0)

now = datetime.now(pause_until.tzinfo).astimezone()
if now < pause_until:
    print(value)
    raise SystemExit(2)

path.unlink(missing_ok=True)
raise SystemExit(0)
PY
}

latest_agent_titles() {
  python3 - <<'PY'
import json
from pathlib import Path

path = Path("hypotheses/ideas.jsonl")
records = []
if path.exists():
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

parts = []
for agent in ("codex", "claude"):
    agent_records = [item for item in records if item.get("agent") == agent]
    if not agent_records:
        continue
    agent_records.sort(key=lambda item: item.get("created_at", ""))
    title = str(agent_records[-1].get("title") or "new observation")
    parts.append(f"{agent.capitalize()}: {title}")

print("; ".join(parts)[:240] or "new observation")
PY
}

trap 'notify "Run failed" "Check runs/parallel-research.stderr.log and runs/parallel-*.stderr.log."' ERR

HOUR=$(date +%H)

if [ "$HOUR" -lt 7 ] || [ "$HOUR" -ge 17 ]; then
  echo "$(date): Outside research window (7am-5pm), skipping."
  exit 0
fi

set +e
PAUSE_UNTIL="$(pause_until)"
PAUSE_STATUS=$?
set -e
if [ "$PAUSE_STATUS" -eq 2 ]; then
  notify "Research paused" "Skipping this run until ${PAUSE_UNTIL}."
  exit 0
fi

notify "Research starting" "Pulling latest and beginning a new observation..."

DIRECTION="$(current_direction)"
notify "Researching" "$DIRECTION"

DEFAULT_FOCUS="Generate original cross-tradition observations. Codex and Claude should engage each other's latest work, close-read primary texts against each other, hunt anomalies that could break the model, make falsifiable predictions, use real sources, follow docs/writing-style.md, improve the method of observation, and avoid em dashes."

python3 -m engine.parallel_research \
  --focus "${SPIRITUALITY_FOCUS:-$DEFAULT_FOCUS}" \
  --launchagent-plist "${SPIRITUALITY_LAUNCHAGENT_PLIST:-/Users/johnforrester/Library/LaunchAgents/com.lumenary.research.plist}"

TITLES="$(latest_agent_titles)"
notify "New finding" "$TITLES"
notify "Run complete" "Published: $TITLES"
