#!/usr/bin/env bash
# Biome lint/format runner for the frontend project.
#
# Usage (from the frontend/ directory):
#   ./scripts/lint.sh          # check only
#   ./scripts/lint.sh --fix    # auto-fix formatting and lint issues
#
# Prerequisites:
#   npm install   (installs @biomejs/biome as a devDependency)
#
# Alternatively, run via npx without installing:
#   npx @biomejs/biome check src/
#   npx @biomejs/biome check --write src/

set -euo pipefail
cd "$(dirname "$0")/.."

BIOME="./node_modules/.bin/biome"

if [ ! -x "$BIOME" ]; then
  echo "Biome not found. Run 'npm install' first, or use npx:"
  echo "  npx @biomejs/biome check src/"
  exit 1
fi

if [ "${1:-}" = "--fix" ]; then
  echo "==> Formatting..."
  "$BIOME" format --write src/
  echo "==> Linting with auto-fix..."
  "$BIOME" lint --write src/
  echo "==> Final check..."
  "$BIOME" check src/
else
  echo "==> Running biome check..."
  "$BIOME" check src/
fi
