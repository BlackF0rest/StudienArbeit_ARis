#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BACKEND_DIR="$REPO_ROOT/Software/Backend"
REPORT_DIR="$REPO_ROOT/Software/QA/reports"
GATE_TIMEOUT_SECONDS="${GATE_TIMEOUT_SECONDS:-180}"
READY_TIMEOUT_SECONDS="${READY_TIMEOUT_SECONDS:-30}"

BACKEND_PID=""
BACKEND_PORT="${BACKEND_PORT:-5010}"

cleanup() {
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

mkdir -p "$REPORT_DIR"

echo "[1/5] Starting backend on port $BACKEND_PORT"
(
  cd "$BACKEND_DIR"
  HOST=127.0.0.1 PORT="$BACKEND_PORT" DB_PATH="$REPORT_DIR/codex_backend_${BACKEND_PORT}.db" PYTHONUNBUFFERED=1 python run.py
) >"$REPORT_DIR/codex_backend.log" 2>&1 &
BACKEND_PID=$!

echo "[2/5] Waiting for /api/status"
READY_DEADLINE=$((SECONDS + READY_TIMEOUT_SECONDS))
until curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/status" >/dev/null 2>&1; do
  if (( SECONDS >= READY_DEADLINE )); then
    echo "Backend readiness timeout after ${READY_TIMEOUT_SECONDS}s"
    exit 1
  fi
  sleep 1
done

echo "[3/5] Running acceptance gate (timeout ${GATE_TIMEOUT_SECONDS}s)"
set +e
QA_BACKEND_BASE_URL="http://127.0.0.1:${BACKEND_PORT}" \
  timeout "${GATE_TIMEOUT_SECONDS}"s \
  python "$REPO_ROOT/Software/QA/scripts/run_acceptance_gate.py"
GATE_EXIT=$?
set -e

if [[ $GATE_EXIT -eq 124 ]]; then
  echo "Acceptance gate timed out"
  exit 1
fi

echo "[4/5] Acceptance criteria table"
python - <<'PY' "$REPORT_DIR/latest.json"
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print("Criterion  Severity  Status")
print("---------  --------  ------")
for row in report["criteria"]:
    print(f"{row['id']:<9}  {row['severity']:<8}  {row['status']}")
PY

echo "[5/5] Stopping backend"

if [[ $GATE_EXIT -ne 0 ]]; then
  echo "Acceptance gate FAILED (exit ${GATE_EXIT})"
  exit "$GATE_EXIT"
fi

echo "Acceptance gate PASSED"
