#!/usr/bin/env python3
"""Stamp partials/cta.html into every page between <!-- CTA:START --> and <!-- CTA:END -->.

Edit the call to action in partials/cta.html only. This runs from githooks/pre-commit.
A page without markers gets them inserted just above its footer; an older closing band
(the green section right above the footer that says "Hiring for..." or "Let's find where...")
is replaced. Usage: python3 scripts/sync-cta.py [--check]
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"privacy.html", "terms.html", "resume.html", "7-zip.html", "ai-value-presentation.html",
        "forester-presentation.html", "grading-presentation.html", "my-presentation.html"}
START, END = "<!-- CTA:START -->", "<!-- CTA:END -->"
FOOTER = re.compile(r'\n([ \t]*)<footer class="(?:on-ink foot|page-footer)')
OLD_CLOSE = re.compile(r'\n[ \t]*(?:<!-- [^\n]*CLOSE[^\n]*-->\s*)?<section class="on-olive section">(?:(?!<section).)*?'
                       r'(?:Hiring for|Let&rsquo;s find where)(?:(?!<section).)*?</section>\s*$', re.S)


def block(indent):
    body = (ROOT / "partials/cta.html").read_text(encoding="utf-8").rstrip("\n").split("\n")
    body = [l for l in body if not l.startswith("<!--") and not l.startswith("     between")]
    return "\n".join([indent + START] + [(indent + l) if l else l for l in body] + [indent + END])


def sync(text):
    m = FOOTER.search(text)
    if not m:
        return text
    indent = m.group(1)
    if START in text:
        return re.sub(re.escape(START) + ".*?" + re.escape(END), lambda _: block(indent).lstrip(), text, flags=re.S)
    head, tail = text[:m.start()], text[m.start():]
    head = OLD_CLOSE.sub("", head)
    return head + "\n\n" + block(indent) + "\n" + tail


def main():
    check = "--check" in sys.argv
    stale = []
    for p in sorted(ROOT.glob("*.html")):
        if p.name in SKIP:
            continue
        old = p.read_text(encoding="utf-8")
        new = sync(old)
        if new != old:
            stale.append(p.name)
            if not check:
                p.write_text(new, encoding="utf-8")
    print(("stale: " if check else "sync-cta: updated ") + (", ".join(stale) if stale else "nothing"))
    sys.exit(1 if check and stale else 0)


if __name__ == "__main__":
    main()
