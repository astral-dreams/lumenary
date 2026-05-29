#!/usr/bin/env bash

LUMENARY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PATH="/Users/johnforrester/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"

set -a
for env_file in "$LUMENARY_ROOT/.env" "$LUMENARY_ROOT/.env.local"; do
  if [ -f "$env_file" ]; then
    # shellcheck disable=SC1090
    . "$env_file"
  fi
done
set +a

# The active schedule follows the user's travel plan explicitly instead of
# depending on launchd's calendar timezone cache.
if [ -z "${SPIRITUALITY_TIMEZONE:-}" ] || [ "${SPIRITUALITY_TIMEZONE:-}" = "local" ]; then
  LUMENARY_TIMEZONE_SWITCH_DATE="${LUMENARY_TIMEZONE_SWITCH_DATE:-2026-06-12}"
  LUMENARY_TIMEZONE_BEFORE_SWITCH="${LUMENARY_TIMEZONE_BEFORE_SWITCH:-Europe/Zagreb}"
  LUMENARY_TIMEZONE_AFTER_SWITCH="${LUMENARY_TIMEZONE_AFTER_SWITCH:-America/Los_Angeles}"
  LUMENARY_TIMEZONE_TODAY="$(TZ="$LUMENARY_TIMEZONE_BEFORE_SWITCH" date +%F)"

  if [[ "$LUMENARY_TIMEZONE_TODAY" < "$LUMENARY_TIMEZONE_SWITCH_DATE" ]]; then
    export SPIRITUALITY_TIMEZONE="$LUMENARY_TIMEZONE_BEFORE_SWITCH"
  else
    export SPIRITUALITY_TIMEZONE="$LUMENARY_TIMEZONE_AFTER_SWITCH"
  fi
fi

export LUMENARY_ACTIVE_TIMEZONE="$SPIRITUALITY_TIMEZONE"
export TZ="$SPIRITUALITY_TIMEZONE"

# Do not import Cloudflare credentials from unrelated projects. The Lumenary
# Pages project lives under forrester.author@gmail.com, while older local
# projects may contain tokens scoped to other accounts. Use this project's
# .env/.env.local or Wrangler's authenticated user config.
