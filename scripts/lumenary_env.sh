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

# Do not import Cloudflare credentials from unrelated projects. The Lumenary
# Pages project lives under forrester.author@gmail.com, while older local
# projects may contain tokens scoped to other accounts. Use this project's
# .env/.env.local or Wrangler's authenticated user config.
