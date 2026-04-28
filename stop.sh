#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

stop_pid() {
  local pid_file="$1"
  local name="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$name is not running (no pid file)."
    return 0
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [[ -z "${pid:-}" ]]; then
    rm -f "$pid_file"
    echo "$name pid file was empty."
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

    if kill -0 "$pid" 2>/dev/null; then
      echo "Warning: $name may still be running."
    else
      echo "$name stopped."
    fi
  else
    echo "$name was not running."
  fi

  rm -f "$pid_file"
}

stop_pid "$BACKEND_PID_FILE" "backend"
stop_pid "$FRONTEND_PID_FILE" "frontend"

rmdir "$PID_DIR" 2>/dev/null || true

echo "All done."
