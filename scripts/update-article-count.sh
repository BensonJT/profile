#!/usr/bin/env bash
# Recomputes the published article count from articles.html and syncs
# every reference to it in index.html. Safe to run manually; also wired
# as the pre-commit hook (see githooks/pre-commit).
set -euo pipefail

cd "$(dirname "$0")/.."

count=$(grep -oE 'href="article-[a-z0-9-]+\.html"' articles.html | sort -u | wc -l | tr -d ' ')

if [ -z "$count" ] || [ "$count" -eq 0 ]; then
    echo "update-article-count: refusing to write a zero/empty count, check articles.html" >&2
    exit 1
fi

sed -i -E \
    -e "s/(<h2>)[0-9]+( articles on how operating improvement actually happens\.<\/h2>)/\1${count}\2/" \
    -e "s/(<a class=\"link-more\" href=\"articles\.html\">All )[0-9]+( &rarr;<\/a>)/\1${count}\2/" \
    index.html

echo "update-article-count: index.html synced to ${count} articles"
