#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-manual}"
NEO4J_WAIT_MAX="${2:-45}"

is_port_listening() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn | awk '{print $4}' | grep -qE ":${port}$"
  else
    netstat -ltn 2>/dev/null | awk '{print $4}' | grep -qE ":${port}$"
  fi
}

resolve_neo4j_cmd() {
  if command -v neo4j >/dev/null 2>&1; then
    echo "neo4j"
    return 0
  fi

  if [[ -n "${NEO4J_HOME:-}" && -x "${NEO4J_HOME}/bin/neo4j" ]]; then
    echo "${NEO4J_HOME}/bin/neo4j"
    return 0
  fi

  return 1
}

if is_port_listening 7687; then
  echo "[OK] Neo4j is already running on port 7687."
  exit 0
fi

if ! NEO4J_CMD="$(resolve_neo4j_cmd)"; then
  if [[ "$MODE" == "auto" ]]; then
    echo "[WARN] Neo4j launcher not found."
    echo "[WARN] Continuing startup. QA graph features may be degraded."
    exit 0
  fi
  echo "[ERROR] Cannot find Neo4j launcher (neo4j)."
  echo "[INFO] Please set NEO4J_HOME or add Neo4j bin directory to PATH."
  exit 1
fi

if [[ "$MODE" == "auto" ]]; then
  echo "[WARN] Neo4j is not listening on port 7687."
  echo "[*] Attempting to start Neo4j service..."
  "$NEO4J_CMD" start >/dev/null 2>&1 || true

  echo "[*] Waiting for Neo4j port 7687..."
  for ((i=1; i<=NEO4J_WAIT_MAX; i++)); do
    if is_port_listening 7687; then
      echo "[OK] Neo4j is now listening on port 7687."
      exit 0
    fi
    sleep 1
  done

  echo "[WARN] Neo4j did not become ready within ${NEO4J_WAIT_MAX} seconds."
  echo "[WARN] Continuing startup. QA graph features may be degraded."
  exit 0
fi

echo "Starting Neo4j in console mode..."
exec "$NEO4J_CMD" console
