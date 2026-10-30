#!/usr/bin/env python3
"""Check the Requirements Fit Analyzer process map (fit-analyzer-map.html). Exit 1 on any FAIL.

1. Markers and notes: in every figure (wide and tall), the numbered circles run 1..N and the notes list below it
   has exactly N items, so no marker lacks a note and no note lacks a marker.
2. Public language: the visible text, alt text and labels name no file, script, table or path, no private
   track, no pay, and no counts of employers, boards or applications.
3. Voice (advisory): if VOICE_CHECK points at the voice checker, run it on the page and print what it finds.

    python3 tools/fitmap/check_fitmap.py
"""

import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parents[2] / "fit-analyzer-map.html"

BANNED = [
    (r"\b[\w-]+\.(py|sh|sql|md|csv|duckdb|json|toml|parquet|ps1)\b", "a file name"),
    (r"~/|/home/|/mnt/|[A-Z]:\\", "a path"),
    (r"\b[a-z]+_[a-z0-9_]+\b", "a snake_case identifier (script, table or column name)"),
    (r"\bbridge\b", "the private bridge track"),
    (r"\$\s?\d|\bsalary\b|\bpay band\b", "pay"),
    (r"\b\d[\d,]*\+?\s+(employers?|boards?|applications?|companies)\b", "a count of employers, boards or applications"),
    (r"\b(Top_Jobs|Jobs_Found|launch|finder|sweep_ats|pg_snapshot|trk)\b", "a private script or report name"),
]


class Text(HTMLParser):
    """Visible text plus alt, aria-label and title attributes; skips scripts and styles."""

    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        for k, v in attrs:
            if k in ("alt", "aria-label", "title") and v:
                self.parts.append(v)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())


def check_markers(html):
    fails = []
    for name in sorted(set(re.findall(r'data-fm-fig="([\w-]+)"', html))):
        m = re.search(rf"<!-- fitmap:{name}-notes -->(.*?)<!-- /fitmap:{name}-notes -->", html, re.S)
        if not m:
            fails.append(f"{name}: no notes block")
            continue
        n_notes = len(re.findall(r"<li\b", m.group(1)))
        for fig in re.findall(rf'<figure[^>]*data-fm-fig="{name}"[^>]*>(.*?)</figure>', html, re.S):
            nums = [int(x) for x in re.findall(r'class="fm-t-num"[^>]*>\s*(\d+)\s*<', fig)]
            if sorted(nums) != list(range(1, n_notes + 1)):
                fails.append(f"{name}: markers {sorted(nums)} vs {n_notes} notes")
    return fails


def check_language(html):
    page = Text()
    page.feed(html)
    text = "\n".join(page.parts)
    fails = []
    for pat, what in BANNED:
        for m in re.finditer(pat, text, re.I if what in ("pay", "the private bridge track") else 0):
            fails.append(f"public language: {what}: {m.group(0)!r}")
    return fails


def main():
    html = PAGE.read_text(encoding="utf-8")
    fails = check_markers(html) + check_language(html)
    figs = len(set(re.findall(r'data-fm-fig="([\w-]+)"', html)))
    print(f"fit-analyzer-map: {figs} figures checked, {len(fails)} FAIL")
    for f in fails:
        print("  FAIL", f)
    voice = os.environ.get("VOICE_CHECK")
    if voice and Path(voice).exists():
        r = subprocess.run([sys.executable, voice, "--html", str(PAGE)], capture_output=True, text=True)
        print("  voice check (advisory):")
        for line in (r.stdout or r.stderr).splitlines():
            print("   ", line)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
