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

import_cloudflare_keys() {
  local env_file="$1"
  if [ ! -f "$env_file" ]; then
    return 0
  fi

  while IFS= read -r line; do
    case "$line" in
      CLOUDFLARE_API_TOKEN=*|CLOUDFLARE_ACCOUNT_ID=*|CLOUDFLARE_ZONE_ID=*)
        export "$line"
        ;;
    esac
  done < "$env_file"
}

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  import_cloudflare_keys "/Users/johnforrester/mightybot-marketing/.env"
fi

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  import_cloudflare_keys "/Users/johnforrester/village-game/server/.env.live"
fi
