#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../backend"

VENV_NAME="blueguard"
VENV_DIR="$PWD/$VENV_NAME"
VENV_PY="$VENV_DIR/bin/python"
REQ_HASH_FILE="$VENV_DIR/.requirements.sha256"

ALLOWED_PY="3.12"

echo "[Backend] Working directory: $PWD"
echo "[Backend] Virtual env directory: $VENV_DIR"

pick_python_for_venv() {
  if command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    local py_ver
    py_ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [[ "$py_ver" == "$ALLOWED_PY" ]]; then
      echo "python3"
      return 0
    fi
  fi

  if command -v python >/dev/null 2>&1; then
    local py_ver
    py_ver="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [[ "$py_ver" == "$ALLOWED_PY" ]]; then
      echo "python"
      return 0
    fi
  fi

  return 1
}

ensure_venv() {
  if [[ -x "$VENV_PY" ]]; then
    echo "[Backend] Reusing existing virtual environment: $VENV_NAME"
    return 0
  fi

  local selected_py
  if ! selected_py="$(pick_python_for_venv)"; then
    echo "[Backend][ERROR] No compatible Python found."
    echo "[Backend] Please install Python $ALLOWED_PY first."
    return 1
  fi

  echo "[Backend] Creating virtual environment $VENV_NAME using $selected_py ..."
  "$selected_py" -m venv "$VENV_DIR"
}

calc_requirements_hash() {
  sha256sum requirements.txt | awk '{print $1}'
}

ensure_venv

if [[ ! -x "$VENV_PY" ]]; then
  echo "[Backend][ERROR] Virtual environment python executable was not found."
  echo "[Backend] Tried: $VENV_PY"
  exit 1
fi

REQ_HASH="$(calc_requirements_hash)"
LAST_REQ_HASH=""
if [[ -f "$REQ_HASH_FILE" ]]; then
  LAST_REQ_HASH="$(cat "$REQ_HASH_FILE")"
fi

if [[ "$REQ_HASH" == "$LAST_REQ_HASH" ]]; then
  echo "[Backend] requirements.txt unchanged. Skipping dependency install."
else
  echo "[Backend] requirements.txt changed or first run. Installing dependencies..."
  "$VENV_PY" -m pip install --upgrade pip
  "$VENV_PY" -m pip install -r requirements.txt
  echo "$REQ_HASH" > "$REQ_HASH_FILE"
fi

echo "[Backend] Starting FastAPI on http://localhost:8000 ..."
exec "$VENV_PY" -m uvicorn main:app --reload --port 8000 --host 0.0.0.0
