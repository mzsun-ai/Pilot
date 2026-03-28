#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PORT="${PILOT_WEB_PORT:-8765}"

if command -v ss >/dev/null 2>&1; then
  if ss -tln 2>/dev/null | grep -q ":${PORT}"; then
    echo "Pilot: port ${PORT} already in use. Stop old server: fuser -k ${PORT}/tcp" >&2
    exit 1
  fi
elif (echo >/dev/tcp/127.0.0.1/"${PORT}") 2>/dev/null; then
  echo "Pilot: port ${PORT} in use." >&2
  exit 1
fi

if command -v conda >/dev/null 2>&1; then
  exec conda run -n Pilot --no-capture-output uvicorn web.app:app --host 0.0.0.0 --port "${PORT}"
fi
exec uvicorn web.app:app --host 0.0.0.0 --port "${PORT}"
