#!/bin/sh
set -eu

next_host="${NEXT_HOST:-127.0.0.1}"
next_port="${NEXT_PORT:-3000}"
api_host="${API_HOST:-0.0.0.0}"
api_port="${PORT:-8000}"

export NEXT_INTERNAL_ORIGIN="${NEXT_INTERNAL_ORIGIN:-http://${next_host}:${next_port}}"
export INTERNAL_API_ORIGIN="${INTERNAL_API_ORIGIN:-http://127.0.0.1:${api_port}}"

(
  cd /app/frontend
  HOSTNAME="$next_host" PORT="$next_port" node server.js
) &
web_pid=$!

shutdown() {
  kill "${api_pid:-}" "$web_pid" 2>/dev/null || true
  wait "${api_pid:-}" "$web_pid" 2>/dev/null || true
}

trap shutdown INT TERM EXIT

python -c "import os, time, urllib.request
url = os.environ['NEXT_INTERNAL_ORIGIN']
for _ in range(50):
    try:
        urllib.request.urlopen(url, timeout=1)
        break
    except Exception:
        time.sleep(0.1)
else:
    raise SystemExit('Next.js server did not become ready')"

uvicorn src.main:app \
  --host "$api_host" \
  --port "$api_port" \
  --workers "${WEB_CONCURRENCY:-2}" &
api_pid=$!

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
