#!/usr/bin/env bash
# convert_to_webp.sh — Convert PNG/JPG images to WebP using ffmpeg
#
# Usage:
#   ./scripts/convert_to_webp.sh                    # convert img/ in place
#   ./scripts/convert_to_webp.sh img/               # explicit directory
#   ./scripts/convert_to_webp.sh img/photo.png      # single file
#   ./scripts/convert_to_webp.sh img/ --dry-run     # preview only
#   ./scripts/convert_to_webp.sh img/ --keep        # keep originals (default deletes)
#   ./scripts/convert_to_webp.sh img/ --quality 90  # quality 1-100 (default 85)
#   ./scripts/convert_to_webp.sh img/ --max-width 1600

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
TARGET="${1:-img}"
QUALITY=85
MAX_WIDTH=1400
DELETE_ORIGINALS=true
DRY_RUN=false

# ── Parse flags ───────────────────────────────────────────────────────────────
shift 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)    DRY_RUN=true ;;
        --keep)       DELETE_ORIGINALS=false ;;
        --quality)    QUALITY="$2"; shift ;;
        --max-width)  MAX_WIDTH="$2"; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# ── Helpers ───────────────────────────────────────────────────────────────────
format_bytes() {
    local bytes=$1
    if (( bytes >= 1048576 )); then
        printf "%.1f MB" "$(echo "scale=1; $bytes/1048576" | bc)"
    else
        printf "%.1f KB" "$(echo "scale=1; $bytes/1024" | bc)"
    fi
}

# ── Collect files ─────────────────────────────────────────────────────────────
if [[ -f "$TARGET" ]]; then
    mapfile -t FILES < <(echo "$TARGET")
else
    mapfile -t FILES < <(find "$TARGET" -maxdepth 1 \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | sort)
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "No PNG/JPG images found in: $TARGET"
    exit 0
fi

echo ""
$DRY_RUN && printf "DRY RUN — " || true
echo "Converting ${#FILES[@]} image(s) → WebP"
echo "  Quality: $QUALITY  |  Max width: ${MAX_WIDTH}px  |  Delete originals: $DELETE_ORIGINALS"
echo ""

TOTAL_ORIG=0
TOTAL_NEW=0
CONVERTED=0
SKIPPED=0

for SRC in "${FILES[@]}"; do
    EXT="${SRC##*.}"
    DEST="${SRC%.*}.webp"

    # Skip if WebP already exists
    if [[ -f "$DEST" ]]; then
        echo "  SKIP  $(basename "$SRC")  (WebP already exists)"
        (( SKIPPED++ )) || true
        continue
    fi

    ORIG_SIZE=$(stat -c%s "$SRC" 2>/dev/null || stat -f%z "$SRC")

    if $DRY_RUN; then
        echo "  WOULD CONVERT  $(basename "$SRC")  ($(format_bytes $ORIG_SIZE))"
        (( TOTAL_ORIG += ORIG_SIZE )) || true
        continue
    fi

    # Build ffmpeg scale filter — only downscale if wider than MAX_WIDTH
    SCALE="scale='if(gt(iw,${MAX_WIDTH}),${MAX_WIDTH},iw)':'if(gt(iw,${MAX_WIDTH}),-1,ih)'"

    ffmpeg -y -i "$SRC" -vf "$SCALE" -q:v "$QUALITY" "$DEST" -loglevel error

    NEW_SIZE=$(stat -c%s "$DEST" 2>/dev/null || stat -f%z "$DEST")
    SAVINGS=$(( ORIG_SIZE - NEW_SIZE ))
    PCT=$(echo "scale=1; $SAVINGS * 100 / $ORIG_SIZE" | bc)

    if (( SAVINGS >= 0 )); then
        SIGN="-"
    else
        SIGN="+"
        PCT="${PCT#-}"
    fi

    echo "  ✓  $(basename "$SRC")"
    echo "     $(format_bytes $ORIG_SIZE) → $(format_bytes $NEW_SIZE)  (${SIGN}${PCT}%)"

    (( TOTAL_ORIG += ORIG_SIZE )) || true
    (( TOTAL_NEW  += NEW_SIZE  )) || true
    (( CONVERTED++             )) || true

    if $DELETE_ORIGINALS; then
        rm "$SRC"
    fi
done

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "──────────────────────────────────────────────────"
if $DRY_RUN; then
    echo "  Would convert: ${#FILES[@]} file(s)  ($(format_bytes $TOTAL_ORIG) total)"
else
    echo "  Converted: $CONVERTED  |  Skipped: $SKIPPED"
    if (( CONVERTED > 0 )); then
        TOTAL_SAVINGS=$(( TOTAL_ORIG - TOTAL_NEW ))
        TOTAL_PCT=$(echo "scale=1; $TOTAL_SAVINGS * 100 / $TOTAL_ORIG" | bc)
        echo "  Before: $(format_bytes $TOTAL_ORIG)  →  After: $(format_bytes $TOTAL_NEW)"
        echo "  Saved:  $(format_bytes $TOTAL_SAVINGS)  (${TOTAL_PCT}% reduction)"
    fi
fi
echo ""
