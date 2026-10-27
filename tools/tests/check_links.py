"""
Check every local link and asset reference on the site: each href/src that points at a file in this repo must
exist, and each #anchor must name an id on its target page. External URLs are not fetched.

Why: the AI Builder pages link to each other and to Systems by #anchor (2026-10-27), and 30+ pages share one
nav, so a renamed id or a moved file breaks links nobody clicks until a reader does.

Usage (from the profile repo):
    npm run test:links   (or: python3 tools/tests/check_links.py)
Exit code 0 = every link resolves; 1 = the broken ones are listed.
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
# Pages a reader can reach. first/, proto/ and slides/ are separate demos with their own links.
PAGES = sorted(p for p in ROOT.glob("*.html"))
REF = re.compile(r'\s(?:href|src)="([^"]+)"')
SKIP = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:")


def ids(path: Path, cache: dict) -> set:
    if path not in cache:
        cache[path] = set(re.findall(r'\sid="([^"]+)"', path.read_text(encoding="utf-8", errors="ignore")))
    return cache[path]


def main() -> int:
    cache, bad = {}, []
    for page in PAGES:
        html = page.read_text(encoding="utf-8", errors="ignore")
        html = re.sub(r"<!--.*?-->", "", html, flags=re.S)  # commented-out markup is not a link
        for ref in REF.findall(html):
            if ref.startswith(SKIP) or ref == "#":
                continue
            target, _, anchor = unquote(ref).partition("#")
            file = (page.parent / target) if target else page
            if not file.exists():
                bad.append(f"{page.name}: {ref} (no such file)")
                continue
            if anchor and file.suffix == ".html" and anchor not in ids(file, cache):
                bad.append(f"{page.name}: {ref} (no id {anchor!r})")
    for line in bad:
        print("BROKEN", line)
    print(f"{len(PAGES)} pages checked, {len(bad)} broken")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
