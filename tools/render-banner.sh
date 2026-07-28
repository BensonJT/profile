#!/usr/bin/env bash
# Render the LinkedIn banner to img/linkedin-banner.png at exactly 1584x396.
#
# Served over http rather than file:// so the woff2 faces load without needing
# --allow-file-access-from-files. Re-run this after any edit to
# tools/linkedin-banner.html, and after the custom domain lands so the URL line
# can be updated in one place.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8901}"
SCALE="${SCALE:-1}" # SCALE=2 renders 3168x792 for a sharper upload
OUT="${OUT:-$ROOT/img/linkedin-banner.png}"

cd "$ROOT"
python3 -m http.server "$PORT" >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true' EXIT
sleep 1

google-chrome \
    --headless \
    --disable-gpu \
    --hide-scrollbars \
    --default-background-color=00000000 \
    --force-device-scale-factor="$SCALE" \
    --window-size=1584,396 \
    --screenshot="$OUT" \
    "http://localhost:$PORT/tools/linkedin-banner.html" \
    >/dev/null 2>&1

echo "wrote $OUT"
