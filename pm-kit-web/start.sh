#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/.pm-kit-web.pid"
ACTION="${1:-start}"

_find_product_yaml() {
  local yaml="${PM_KIT_PRODUCT_YAML:-}"
  if [ -n "$yaml" ]; then
    echo "$yaml"
    return
  fi
  for candidate in "$SCRIPT_DIR/../product.yaml" "$SCRIPT_DIR/../../product.yaml" "$(pwd)/product.yaml"; do
    if [ -f "$candidate" ]; then
      echo "$candidate"
      return
    fi
  done
}

_get_port() {
  echo "${PM_KIT_PORT:-8770}"
}

_is_running() {
  if [ -f "$PID_FILE" ]; then
    local pid
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
    rm -f "$PID_FILE"
  fi
  return 1
}

do_stop() {
  if _is_running; then
    local pid
    pid=$(cat "$PID_FILE")
    echo "[PM Kit Web] Stopping process $pid on port $(_get_port)..."
    kill "$pid" 2>/dev/null || true
    local waited=0
    while kill -0 "$pid" 2>/dev/null && [ $waited -lt 10 ]; do
      sleep 1
      waited=$((waited + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
      echo "[PM Kit Web] Force killing $pid..."
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    echo "[PM Kit Web] Stopped."
  else
    local port
    port=$(_get_port)
    local pids
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
      echo "[PM Kit Web] No PID file but port $port is occupied. Killing: $pids"
      echo "$pids" | xargs kill 2>/dev/null || true
      echo "[PM Kit Web] Stopped."
    else
      echo "[PM Kit Web] Not running."
    fi
  fi
}

do_start() {
  if _is_running; then
    echo "[PM Kit Web] Already running (PID $(cat "$PID_FILE")). Use '$0 restart' to restart."
    exit 0
  fi

  local product_yaml
  product_yaml=$(_find_product_yaml)

  if [ -n "$product_yaml" ]; then
    export PM_KIT_PRODUCT_YAML="$product_yaml"
    echo "[PM Kit Web] Using product config: $product_yaml"
  else
    echo "[PM Kit Web] Warning: No product.yaml found. Set PM_KIT_PRODUCT_YAML env var."
  fi

  local port
  port=$(_get_port)

  local pids
  pids=$(lsof -ti :"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "[PM Kit Web] Port $port is occupied by: $pids"
    echo "[PM Kit Web] Use '$0 stop' or '$0 restart' first."
    exit 1
  fi

  echo "[PM Kit Web] Starting on http://localhost:$port"

  cd "$SCRIPT_DIR"
  nohup python3 -m server.main > "$SCRIPT_DIR/.pm-kit-web.log" 2>&1 &
  local pid=$!
  echo "$pid" > "$PID_FILE"

  local waited=0
  while ! curl -s "http://localhost:$port/api/health" > /dev/null 2>&1; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "[PM Kit Web] Failed to start. Check $SCRIPT_DIR/.pm-kit-web.log"
      rm -f "$PID_FILE"
      exit 1
    fi
    if [ $waited -ge 15 ]; then
      echo "[PM Kit Web] Timeout waiting for startup. Check $SCRIPT_DIR/.pm-kit-web.log"
      exit 1
    fi
    sleep 1
    waited=$((waited + 1))
  done

  echo "[PM Kit Web] Ready at http://localhost:$port (PID $pid)"
}

do_restart() {
  echo "[PM Kit Web] Restarting..."
  do_stop
  do_start
}

do_status() {
  if _is_running; then
    local pid
    pid=$(cat "$PID_FILE")
    echo "[PM Kit Web] Running (PID $pid) on port $(_get_port)"
  else
    echo "[PM Kit Web] Not running."
  fi
}

case "$ACTION" in
  start)   do_start ;;
  stop)    do_stop ;;
  restart) do_restart ;;
  status)  do_status ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    echo ""
    echo "Commands:"
    echo "  start    Start PM Kit Web (default)"
    echo "  stop     Stop PM Kit Web"
    echo "  restart  Stop then start"
    echo "  status   Check if running"
    echo ""
    echo "Environment variables:"
    echo "  PM_KIT_PRODUCT_YAML  Path to product.yaml (auto-detected if unset)"
    echo "  PM_KIT_PORT          Port number (default: 8770)"
    exit 1
    ;;
esac
