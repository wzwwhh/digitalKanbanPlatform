#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
BACKEND_LOG="$PID_DIR/backend.log"
FRONTEND_LOG="$PID_DIR/frontend.log"

mkdir -p "$PID_DIR"

stop_pid() {
  local pid_file="$1"
  local name="$2"

  if [[ ! -f "$pid_file" ]]; then
    return 0
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -z "${pid:-}" ]]; then
    rm -f "$pid_file"
    return 0
  fi

  if kill -0 "$pid" 2>/dev/null; then
    echo "Stopping $name (PID: $pid)..."
    pkill -TERM -P "$pid" 2>/dev/null || true
    kill -TERM "$pid" 2>/dev/null || true

    for _ in {1..30}; do
      if ! kill -0 "$pid" 2>/dev/null; then
        break
      fi
      sleep 1
    done

    if kill -0 "$pid" 2>/dev/null; then
      echo "$name did not exit after TERM, forcing kill..."
      pkill -KILL -P "$pid" 2>/dev/null || true
      kill -KILL "$pid" 2>/dev/null || true
    fi
  fi

  rm -f "$pid_file"
}

stop_pid "$BACKEND_PID_FILE" "backend"
stop_pid "$FRONTEND_PID_FILE" "frontend"

cd "$ROOT_DIR/backend"
python -m uvicorn app.main:app --reload >"$BACKEND_LOG" 2>&1 &
backend_pid=$!
echo "$backend_pid" >"$BACKEND_PID_FILE"
echo "Backend started: PID $backend_pid"

cd "$ROOT_DIR/frontend"
npm run dev >"$FRONTEND_LOG" 2>&1 &
frontend_pid=$!
echo "$frontend_pid" >"$FRONTEND_PID_FILE"
echo "Frontend started: PID $frontend_pid"

echo ""
echo "Services started."
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo "Logs are in: $PID_DIR"
echo "To stop them, run: ./stop.sh"
