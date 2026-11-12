#!/usr/bin/env bash
# Recomputes the published article count from articles.html (unique article-*.html links)
# and syncs every live reference to it:
#   index.html     "<N> articles on how operating improvement actually happens." and "All <N> →"
#   articles.html  "<N> articles on how operating improvement gets done"
# Usage:
#   scripts/update-article-count.sh           sync the counts (the pre-commit hook runs this)
#   scripts/update-article-count.sh --check   change nothing; exit 1 if any count is stale (npm test runs this)
# Enable the hook once per clone: git config core.hooksPath githooks
set -euo pipefail

cd "$(dirname "$0")/.."

count=$(grep -oE 'href="article-[a-z0-9-]+\.html"' articles.html | sort -u | wc -l | tr -d ' ')
files=$(ls article-*.html | wc -l | tr -d ' ')

if [ -z "$count" ] || [ "$count" -eq 0 ]; then
    echo "update-article-count: refusing to write a zero/empty count, check articles.html" >&2
    exit 1
fi
if [ "$count" -ne "$files" ]; then
    echo "update-article-count: WARNING articles.html links ${count} articles but ${files} article-*.html files exist (a draft not yet on the Notebook?)" >&2
fi

patterns=(
    "index.html|(<h2>)([0-9]+)( articles on how operating improvement actually happens\.</h2>)"
    "index.html|(<a class=\"link-more\" href=\"articles\.html\">All )([0-9]+)( &rarr;</a>)"
    "articles.html|(<p class=\"deck\">)([0-9]+)( articles on how operating improvement gets done)"
)

if [ "${1:-}" = "--check" ]; then
    stale=0
    for entry in "${patterns[@]}"; do
        file=${entry%%|*}
        re=${entry#*|}
        found=$(sed -nE "s#.*${re}.*#\\2#p" "$file" | head -1)
        if [ -z "$found" ]; then
            echo "FAIL article count: pattern not found in ${file}: ${re}" >&2
            stale=1
        elif [ "$found" != "$count" ]; then
            echo "FAIL article count: ${file} says ${found}, articles.html links ${count} (run scripts/update-article-count.sh)" >&2
            stale=1
        fi
    done
    [ "$stale" -eq 0 ] && echo "PASS article count: ${count} everywhere"
    exit "$stale"
fi

for entry in "${patterns[@]}"; do
    file=${entry%%|*}
    re=${entry#*|}
    sed -i -E "s#${re}#\\1${count}\\3#" "$file"
done

echo "update-article-count: index.html and articles.html synced to ${count} articles"
