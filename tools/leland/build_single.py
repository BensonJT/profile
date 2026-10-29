"""
Stitch the four AI Builder pages into ONE self-contained HTML file for the Leland course site.

Why: Leland hosts a single .html file (in an <iframe srcdoc>, sanitized, frames blocked). The profile site keeps
four pages; this script turns them back into one page. Edit the pages, then run this to regenerate the upload.

Pages, in order: ai-builder.html (hub), ai-builder-projects.html, ai-builder-evaluation.html,
ai-builder-level1.html. Each page marks its parts with HTML comments:
    <!-- leland:drop-start ... --> ... <!-- leland:drop-end -->   left out of the bundle (sub-nav, page heads,
                                                                   the hub's portfolio cards, repeated contact)
    <!-- leland:content-start --> ... <!-- leland:content-end -->  a sub-page's sections, copied into the bundle
    <!-- leland:insert ... -->                                     where those sections go in the hub

What it does:
  A. Stitches: the hub without its drop blocks, with each sub-page's content inserted at the marker.
  B. Nav: the profile nav becomes an in-page section nav; links between the four pages become #anchors;
     links to other profile pages become absolute https://bensonjt.github.io/profile/ URLs.
  1. <link rel="stylesheet" href="css/x.css">  ->  <style> ...css... </style>
  2. url("../fonts/X.woff2") inside that CSS   ->  base64 data URI (font embedded)
  3. <script src="js/x.js" defer></script>     ->  <script> ...js... </script>
  4. <img src="img/x.webp">, favicon           ->  base64 data URIs
  5. Drops the font <link rel="preload"> tags (nothing left to preload)
  6. Every deck a data-deck link points at (my-presentation.html, ai-value-presentation.html)  ->
     Leland blocks frames, so each deck is split into its CSS (rescoped for a shadow root) and its
     slides, stored as base64 JSON keyed by file name on the deck <dialog>, and deck_inline.js
     (bundle only) draws the clicked one in the dialog. Each link becomes "#<deck name>" with a
     data-deck-key. The site keeps the iframe window from builder.js unchanged.
  7. Links marked data-site-only (the deck's PDF download) are dropped: Leland's sandbox blocks
     downloads. The build stops if any link to a local .pdf is left.
  8. Leland's sandbox (allow-scripts only) blocks links to other sites, so outside_links.js (bundle only)
     catches a click on any http(s) link and shows the address in a dialog with a Copy button.
  C. Checks: every #anchor in the bundle has a target, and no relative link is left. The build stops otherwise.

Usage (from anywhere):
    python3 tools/leland/build_single.py [--out PATH]
Output: the Leland upload in the vault, keystone/ai-builder/dist/ai-builder-single.html, when that folder exists
(Jeff publishes from there); otherwise dist/ai-builder-single.html here (git-ignored).
"""

import argparse
import base64
import json
import mimetypes
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # the profile repo
HERE = Path(__file__).resolve().parent
HUB = "ai-builder.html"
SUBPAGES = ["ai-builder-projects.html", "ai-builder-evaluation.html", "ai-builder-level1.html"]
# A link to a sub-page with no #anchor lands at the top of that page's first section
PAGE_ANCHOR = {HUB: "top", "ai-builder-projects.html": "projects", "ai-builder-evaluation.html": "evaluation",
               "ai-builder-level1.html": "builds"}
SITE = "https://bensonjt.github.io/profile/"
VAULT_OUT = Path("/mnt/c/Users/Jeffrey Benson/Documents/keystone/ai-builder/dist/ai-builder-single.html")
DEFAULT_OUT = VAULT_OUT if VAULT_OUT.parent.exists() else ROOT / "dist" / "ai-builder-single.html"
BUNDLE_NAV = [("#about", "About"), ("#focus", "Focus"), ("#projects", "Projects"), ("#evaluation", "Evaluation"),
              ("#builds", "Builds"), ("#contact", "Contact")]

# mimetypes doesn't know these on every system, so register them explicitly
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")


def data_uri(path: Path) -> str:
    """Read a file and return it as a base64 data: URI the browser can use inline."""
    if not path.exists():
        sys.exit(f"Missing file referenced by the page: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def drop_blocks(html: str) -> str:
    html, n = re.subn(r"[ \t]*<!-- leland:drop-start.*?<!-- leland:drop-end -->\n?", "", html, flags=re.S)
    if "leland:drop-start" in html or "leland:drop-end" in html:
        sys.exit("Unbalanced leland:drop markers")
    return html


def stitch() -> str:
    """A: the hub with every sub-page's marked content inserted at the marker."""
    hub = drop_blocks((ROOT / HUB).read_text(encoding="utf-8"))
    parts = []
    for name in SUBPAGES:
        page = (ROOT / name).read_text(encoding="utf-8")
        m = re.search(r"<!-- leland:content-start -->\n(.*?)[ \t]*<!-- leland:content-end -->", page, re.S)
        if not m:
            sys.exit(f"{name} has no leland:content-start/end markers")
        parts.append(drop_blocks(m.group(1)))
    marker = re.search(r"[ \t]*<!-- leland:insert[^>]*-->\n", hub)
    if not marker:
        sys.exit(f"{HUB} has no leland:insert marker")
    return hub[: marker.start()] + "\n".join(parts) + hub[marker.end():]


def bundle_nav(html: str) -> str:
    """B: the profile nav becomes the one-page section nav."""
    def links(indent: str) -> str:
        return "\n".join(f'{indent}<a href="{href}">{label}</a>' for href, label in BUNDLE_NAV)

    html, a = re.subn(r'(<div class="nav__links">\n)(.*?)(\n\s*</div>)',
                      lambda m: m.group(1) + links("                        ") + m.group(3), html, count=1, flags=re.S)
    html, b = re.subn(r'(<div class="nav__drawer"[^>]*>\n)(.*?)(\n\s*</div>)',
                      lambda m: m.group(1) + links("                    ") + m.group(3), html, count=1, flags=re.S)
    if not (a and b):
        sys.exit("Nav markup changed; cannot build the bundle's section nav")
    return html


def rewrite_links(html: str) -> str:
    """B: links between the four pages become #anchors; other relative page links become absolute."""
    pages = [HUB] + SUBPAGES

    def page_link(m):
        name, anchor = m.group(1), m.group(2)
        if name in pages:
            return f'href="#{anchor or PAGE_ANCHOR[name]}"'
        if name == "index.html":
            return f'href="{SITE}{"#" + anchor if anchor else ""}"'
        return f'href="{SITE}{name}{"#" + anchor if anchor else ""}"'

    html = re.sub(r'href="([\w.-]+\.html)(?:#([\w-]+))?"(?!\s+data-deck\b)', page_link, html)
    # the résumé PDF and other site files that are not inlined later
    html = re.sub(r'href="(Jeffrey_Benson_Resume\.pdf)"', rf'href="{SITE}\1"', html)
    return html


def inline_css(match: re.Match) -> str:
    """Replace a stylesheet <link> with a <style> block, embedding its fonts."""
    css_path = ROOT / match.group(1)
    css = css_path.read_text(encoding="utf-8")
    # url("../fonts/X.woff2") is relative to the CSS file's own folder
    css = re.sub(
        r'url\("?([^")]+)"?\)',
        lambda m: f'url("{data_uri((css_path.parent / m.group(1)).resolve())}")'
        if not m.group(1).startswith(("data:", "http"))
        else m.group(0),
        css,
    )
    return f"<style>\n/* inlined from {match.group(1)} */\n{css}\n</style>"


def inline_js(match: re.Match) -> str:
    """Replace <script src=...> with the script's contents. The scripts sit at the
    end of <body>, so dropping 'defer' doesn't change when they run."""
    js = (ROOT / match.group(1)).read_text(encoding="utf-8")
    return f"<script>\n/* inlined from {match.group(1)} */\n{js}\n</script>"


# The deck's own CSS assumes it owns the page. Each rewrite below must apply, or the deck
# generator changed and this conversion needs a look (the build stops instead of shipping a broken deck).
DECK_CSS_REWRITES = [
    (":root{", ":host{"),
    ("html,body{height:100%}", ":host{display:block}"),
    ("\nbody{", "\n.deck-body{position:absolute;inset:0;"),
    (".stage{position:fixed;", ".stage{position:absolute;"),
    (".notes{position:fixed;", ".notes{position:absolute;"),
    (".hint{position:fixed;", ".hint{position:absolute;"),
    ("height:24vh", "height:32%"),
    (".show-notes .", ".deck-body.show-notes ."),
]


DECK_LINK = re.compile(r'href="([\w-]+\.html)"(\s+data-deck\b)')


def deck_parts(name: str) -> dict:
    """One deck file -> its CSS (rescoped for a shadow root) and its slide markup."""
    deck = ROOT / name
    if not deck.exists():
        sys.exit(f"Missing file referenced by the page: {deck}")
    src = deck.read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
    css = re.sub(r"@font-face\{[^}]*\}\n?", "", css)  # the page's site.css already loads the same faces
    for old, new in DECK_CSS_REWRITES:
        if old not in css:
            sys.exit(f"Deck CSS changed in {name}; cannot rescope it for Leland (missing {old!r})")
        css = css.replace(old, new)
    return {"css": css, "html": re.search(r"<body>(.*?)<script>", src, re.S).group(1)}


def inline_deck(html: str) -> str:
    """Store every linked deck (CSS + slides, keyed by file name) on the dialog for deck_inline.js,
    point each link at its key, and add that script."""
    decks = {name: deck_parts(name) for name in dict.fromkeys(m.group(1) for m in DECK_LINK.finditer(html))}
    payload = base64.b64encode(json.dumps(decks).encode("utf-8")).decode("ascii")
    html = DECK_LINK.sub(lambda m: f'href="#{Path(m.group(1)).stem}" data-deck-key="{m.group(1)}"{m.group(2)}', html)
    html = html.replace("data-deck-sheet", f'data-deck-sheet data-deck-inline-b64="{payload}"', 1)
    runtime = (HERE / "deck_inline.js").read_text(encoding="utf-8")
    return html.replace("</body>", f"<script>\n/* inlined from tools/leland/deck_inline.js */\n{runtime}\n</script>\n</body>", 1)


def check_links(html: str) -> None:
    """C: every #anchor has a target and no relative link is left (Leland cannot resolve one)."""
    ids = set(re.findall(r'\sid="([\w-]+)"', html))
    bad = []
    for tag in re.findall(r"<(?:a|link)\b[^>]*>", html):
        m = re.search(r'\shref="([^"]*)"', tag)
        if not m or m.group(1).startswith(("http://", "https://", "mailto:", "data:")):
            continue
        href = m.group(1)
        # a deck link's "#name" is a key deck_inline.js reads, not an element id
        if href.startswith("#") and (href[1:] in ids or href == "#top" or "data-deck-key" in tag):
            continue
        bad.append(href)
    if bad:
        sys.exit(f"Broken or relative links in the bundle: {sorted(set(bad))}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    out = ap.parse_args().out

    html = stitch()                                                                   # A
    html = bundle_nav(html)                                                           # B
    html = html.replace('<a class="nav__brand" href="index.html">', f'<a class="nav__brand" href="{SITE}">', 1)
    html = rewrite_links(html)
    html = html.replace("How I evaluate it &rarr;", "How I evaluate it &darr;")  # same page again in the bundle
    html = re.sub(r"\s*<!-- leland:[^>]*-->", "", html)

    html = re.sub(r'\s*<link rel="preload"[^>]*>', "", html)                       # 5
    html = re.sub(r'<link rel="stylesheet" href="([^"]+)"\s*/?>', inline_css, html)  # 1 + 2
    html = re.sub(r'<script src="([^"]+)"[^>]*></script>', inline_js, html)          # 3
    html = re.sub(                                                                    # 4: favicon
        r'(<link rel="icon" href=")([^"]+)(")',
        lambda m: m.group(1) + data_uri(ROOT / m.group(2)) + m.group(3),
        html,
    )
    html = re.sub(                                                                    # 4: images
        r'(<img[^>]*\ssrc=")(?!data:|https?:)([^"]+)(")',
        lambda m: m.group(1) + data_uri(ROOT / m.group(2)) + m.group(3),
        html,
    )

    if DECK_LINK.search(html):                                                      # 6: the decks
        html = inline_deck(html)

    # 7: links marked data-site-only (the PDF download) need files or permissions Leland's sandbox lacks
    html = re.sub(r"\s*<!--[^>]*data-site-only[^>]*-->", "", html)
    html = re.sub(r"\s*<a\b[^>]*\bdata-site-only\b[^>]*>.*?</a\s*>", "", html, flags=re.S)
    if re.search(r'href="[^"#:]+\.pdf"', html):
        sys.exit("A link to a local PDF is in the bundle; mark it data-site-only (Leland blocks downloads).")

    # Leland's publisher strips <iframe> tags (seen 2026-10-24); frames must be created by script instead
    if re.search(r"<iframe", html, re.I):
        sys.exit("An <iframe> tag is in the page; Leland removes it. Create the frame in JS (see builder.js).")

    # 8: outside links do nothing in Leland's sandbox; show their address to copy instead
    helper = (HERE / "outside_links.js").read_text(encoding="utf-8")
    html = html.replace("</body>", f"<script>\n/* inlined from tools/leland/outside_links.js */\n{helper}\n</script>\n</body>", 1)

    check_links(html)                                                                 # C

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
