#!/usr/bin/env bash
# Render tools/li-card.html to img/li-cards/<NAME>.png at 1200x627.
# Usage:  NAME=itam tools/render-card.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8902}"
NAME="${NAME:-card}"
OUT="$ROOT/img/li-cards/$NAME.png"
cd "$ROOT"
python3 -m http.server "$PORT" >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true' EXIT
sleep 1
google-chrome --headless --disable-gpu --hide-scrollbars \
  --force-device-scale-factor="${SCALE:-1}" --window-size=1200,627 \
  --screenshot="$OUT" "http://localhost:$PORT/tools/li-card.html?card=$NAME" >/dev/null 2>&1
echo "wrote $OUT"
