#!/usr/bin/env bash
set -euo pipefail

cd /Users/johnforrester/spirituality

python3 -m engine.journal \
  --provider codex-cli \
  --timezone "${SPIRITUALITY_TIMEZONE:-America/Los_Angeles}"

scripts/deploy_site.sh
