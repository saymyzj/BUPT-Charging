#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-$ROOT/backend/venv/bin/python}"

if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="${PYTHON:-python3}"
fi

"$PYTHON_BIN" "$ROOT/scripts/reset_dev_db.py" --touch-hmr "$@"
npm --prefix "$ROOT/frontend" run build
