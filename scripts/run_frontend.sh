#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../frontend"

echo "[Frontend] Working directory: $PWD"
if [[ ! -d node_modules ]]; then
  echo "[Frontend] Installing dependencies..."
  npm install
else
  echo "[Frontend] node_modules exists, skipping npm install."
fi

echo "[Frontend] Starting Vite on http://localhost:5173 ..."
exec npm run dev -- --host 0.0.0.0 --port 5173
