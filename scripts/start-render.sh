#!/bin/sh
set -eu

api_host="${API_HOST:-127.0.0.1}"
api_port="${API_PORT:-8001}"
public_port="${PORT:-8000}"

export HOSTNAME="${HOSTNAME:-0.0.0.0}"
export PORT="$public_port"
export INTERNAL_API_ORIGIN="${INTERNAL_API_ORIGIN:-http://${api_host}:${api_port}}"

uvicorn src.main:app \
  --host "$api_host" \
  --port "$api_port" \
  --workers "${WEB_CONCURRENCY:-2}" &
api_pid=$!

cd /app/frontend
node server.js &
web_pid=$!

shutdown() {
  kill "$api_pid" "$web_pid" 2>/dev/null || true
  wait "$api_pid" "$web_pid" 2>/dev/null || true
}

trap shutdown INT TERM EXIT

while true; do
  if ! kill -0 "$api_pid" 2>/dev/null; then
    wait "$api_pid"
    exit $?
  fi

  if ! kill -0 "$web_pid" 2>/dev/null; then
    wait "$web_pid"
    exit $?
  fi

  sleep 2
done
