#!/usr/bin/env python3
"""Draw the Requirements Fit Analyzer process map (fit-analyzer-map.html).

One data source below draws every figure twice (wide, and tall for narrow screens) and writes the numbered notes
under it, so a marker and its note cannot drift apart. The script rewrites the blocks between
<!-- fitmap:NAME --> and <!-- /fitmap:NAME --> in the page and leaves everything else alone.

    python3 tools/fitmap/build_fitmap.py && npx prettier --write fit-analyzer-map.html

Public page: describe what each step does, never a file, script or table name (build plan section 11.2).
Node kinds: d = script (deterministic), j = AI judgment, p = me.
"""

import re
import sys
from html import escape
from pathlib import Path

PAGE = Path(__file__).resolve().parents[2] / "fit-analyzer-map.html"


def e(s):
    return escape(s, quote=True)


# ---------- data: the top-level cycle ----------
PHASES = [
    dict(n=1, title="Find", sub=("job boards,", "posting text"), actors="dp", href="#nightly",
         lead="Find.",
         note="Every night a script pulls each employer’s own job board and fetches the full text of every new "
              "posting. I choose which employers are on the list."),
    dict(n=2, title="Judge", sub=("rules, models,", "AI review"), actors="dj", href="#nightly",
         lead="Judge.",
         note="Rules, trained models and a small embedding model score each posting. Two AI judges read the "
              "Required block of the shortlist."),
    dict(n=3, title="Validate", sub=("every judge", "is scored"), actors="dp", href="#validate",
         lead="Validate.",
         note="Every judge is scored against my own blind grades and keeps only the role its score earned."),
    dict(n=4, title="Decide", sub=("build, pass,", "hold, grade"), actors="dp", href="#decide",
         lead="Decide.",
         note="I make the calls: build, pass or hold. Grades I give before seeing any machine score become the "
              "answer key the judges are scored on."),
    dict(n=5, title="Build", sub=("select, check,", "export"), actors="djp", href="#build",
         lead="Build.",
         note="AI selects verified statements, word for word, from a database of my work and drafts the letter. "
              "Scripts check every fact and phrase, then build the Word files. I edit and send."),
    dict(n=6, title="Learn", sub=("retrain, voice,", "record"), actors="djp", href="#learn",
         lead="Learn.",
         note="My calls retrain the models through a gate. A script finds every edit I make to a sent document "
              "and AI explains why, so the voice guide and the record of my work both improve."),
    dict(n=7, title="Publish", sub=("reports, charts,", "presentation"), actors="dp", href="#nightly",
         lead="Publish.",
         note="A snapshot of each night rebuilds the reports, charts and presentation. I review anything new "
              "before it goes public."),
]
RING_GATES = ("retraining gate", "judge bars", "repeatability bars", "statement guards", "verb check",
              "document check")

# ---------- data: the nightly run ----------
# side: ("in", lines) = I feed this step; ("out", lines) = this step hands work to me; cap = a short caption.
NIGHTLY_LANES = [
    ("PREPARE", "before the pull", [1, 2, 3]),
    ("FIND", "phase 1", [4, 5]),
    ("JUDGE", "phase 2", [6, 7, 8, 9, 10]),
    ("PUBLISH", "phase 7", [11, 12, 13]),
]
NIGHTLY = {
    1: dict(kind="d", label=("Wake on", "schedule"), lead="Wake on schedule.",
            note="I pick the start time. A scheduled task wakes the laptop five minutes before it, so a sleeping "
                 "machine still runs, and the pre-flight checks run twice: when I confirm and when it starts."),
    2: dict(kind="d", label=("Apply my", "calls"), side=("in", ("My calls", "from the day")),
            lead="Apply my calls.",
            note="The build, pass and hold calls and the grades I entered during the day wait in a queue. They "
                 "are applied first, so tonight’s scores already know them."),
    3: dict(kind="d", label=("Retrain the", "models"), cap="when due", gate=True, lead="Retrain the models.",
            note="When a retrain is due, the fit models train again on my latest calls and grades. A new model "
                 "replaces the old one only if it clears the gate: a shuffled-label check for leaks, accuracy no "
                 "worse than the last model that passed, and no drop in labels. A model that fails is discarded, "
                 "and every attempt is logged."),
    4: dict(kind="d", label=("Pull every", "job board"), lead="Pull every job board.",
            note="A script pulls each employer’s own job board, the same data its careers page shows. New postings "
                 "are added and returning ones reopened. A posting is closed only when a clean, complete pull no "
                 "longer lists it, and nothing is deleted, so every posting keeps its full history."),
    5: dict(kind="d", label=("Fetch the", "posting text"), lead="Fetch the posting text.",
            note="The full text of each new posting is fetched, along with a share of the older ones still "
                 "missing it. A posting fetched again keeps the grade it already has."),
    6: dict(kind="d", label=("Screen by", "rules"), gate=True, lead="Screen by rules.",
            note="Rules screen each posting on function, level, location, clearance and discipline. Every verdict "
                 "keeps its reasons, so when a rule changes, the postings it screened out can be reopened."),
    7: dict(kind="d", label=("Score with", "trained models"), lead="Score with trained models.",
            note="Small trained models score fit on my three lenses: process, technical and applied AI. The best "
                 "of the three sets the rank. Two more score the Required block and the closest matches, and "
                 "their scores are shown beside the rank."),
    8: dict(kind="d", label=("Match requirements", "to my record"), cap="explains the rank",
            lead="Match requirements to my record.",
            note="A small embedding model that runs on the laptop matches each requirement in the posting to the "
                 "piece of my record that answers it, and marks it strong, partial or a gap. As a ranker it "
                 "scored 0.669 against the trained models’ 0.955, so its job is to explain the rank."),
    9: dict(kind="j", label=("AI review of", "the shortlist"), side=("out", ("Grey cases", "come to me")),
            lead="AI review of the shortlist.",
            note="Jev, TypeSafe AI’s model for fast typed decisions, reads the Required block of each posting on "
                 "the shortlist. A clear fail is demoted. A fail that rests only on grey lines comes to me to "
                 "check. A posting I have already ruled on is never judged again: my call outranks Jev’s."),
    10: dict(kind="j", label=("Second read of", "the demotions"), cap="evidence only",
             lead="Second read of the demotions.",
             note="Gemma, a second AI judge, reads only Jev’s demotions. It never passed its accuracy bar in "
                  "eight rounds, so its read is shown as evidence beside each demotion and decides nothing."),
    11: dict(kind="d", label=("Apply my", "calls again"), side=("in", ("Calls made", "during the run")),
             lead="Apply my calls again.",
             note="Calls I made while the run was going are applied before the snapshot, so nothing I decided "
                  "waits a day."),
    12: dict(kind="d", label=("Snapshot", "the night"), lead="Snapshot the night.",
             note="One snapshot copies the night’s results into the reporting database in a single swap, so a "
                  "report never reads a half-finished night."),
    13: dict(kind="d", label=("Rebuild reports", "and charts"), lead="Rebuild reports and charts.",
             note="Forty-five seconds later the reports, charts, workbook and presentation rebuild from the "
                  "snapshot, and my application tracker refreshes. If nothing changed, nothing rebuilds. The "
                  "public charts show only industries and percentages."),
}


# ---------- drawing helpers ----------
def defs(p):
    return (
        "<defs>"
        f'<marker id="{p}-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#2c2e2f" /></marker>'
        f'<marker id="{p}-m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#c27b58" /></marker>'
        f'<marker id="{p}-f" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#4a4b45" /></marker>'
        "</defs>"
    )


def arrow(p, d, kind=""):
    cls = {"": "fm-ar", "fb": "fm-ar fm-ar--fb", "me": "fm-ar fm-ar--me"}[kind]
    m = {"": "a", "fb": "f", "me": "m"}[kind]
    return f'<path class="{cls}" d="{d}" marker-end="url(#{p}-{m})" />'


def text(x, y, lines, cls, lh, anchor="middle"):
    """A block of lines centred vertically on y."""
    y0 = y - (len(lines) - 1) * lh / 2
    spans = "".join(f'<tspan x="{x:g}" y="{y0 + i * lh:g}">{e(s)}</tspan>' for i, s in enumerate(lines))
    return f'<text class="{cls}" text-anchor="{anchor}" dominant-baseline="central">{spans}</text>'


def num(x, y, n):
    return (f'<circle class="fm-num" cx="{x:g}" cy="{y:g}" r="14" />'
            f'<text class="fm-t-num" x="{x:g}" y="{y:g}" text-anchor="middle" dominant-baseline="central">{n}</text>')


def person(cx, cy, s=1.0):
    """A small person glyph centred on (cx, cy)."""
    return (f'<g class="fm-glyph"><circle cx="{cx:g}" cy="{cy - 5 * s:g}" r="{4.2 * s:g}" />'
            f'<path d="M{cx - 7.5 * s:g},{cy + 8 * s:g} a{7.5 * s:g},{7.5 * s:g} 0 0 1 {15 * s:g},0 z" /></g>')


def gate(x, y, vertical_arrow=False):
    """A bar across the arrow at (x, y), with a check mark beside it."""
    if vertical_arrow:
        return (f'<g class="fm-gate"><line x1="{x - 12:g}" y1="{y:g}" x2="{x + 12:g}" y2="{y:g}" />'
                f'<path d="M{x + 17:g},{y - 1:g} l4,4 l8,-9" /></g>')
    return (f'<g class="fm-gate"><line x1="{x:g}" y1="{y - 12:g}" x2="{x:g}" y2="{y + 12:g}" />'
            f'<path d="M{x - 6:g},{y - 21:g} l4,4 l8,-9" /></g>')


def box(x, y, w, h, kind, lines, n=None, lh=18, cls="fm-t-node"):
    rx = {"d": 0, "j": h / 2, "p": 7}[kind]
    k = {"d": "det", "j": "judg", "p": "person"}[kind]
    out = f'<g class="fm-n fm-n--{k}"><rect class="fm-box" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx:g}" />'
    if kind == "p":
        out += person(x + 17, y + h / 2)
        out += text(x + 17 + (w - 17) / 2 + 2, y + h / 2, lines, cls, lh)
    else:
        out += text(x + w / 2, y + h / 2, lines, cls, lh)
    if n is not None:
        out += num(x + (9 if kind == "j" else 0), y + (3 if kind == "j" else 0), n)
    return out + "</g>"


def marks(cx, y, actors):
    """The row of small marks that says who works in a phase (script, AI judgment, me)."""
    widths = {"d": 12, "j": 22, "p": 14}
    total = sum(widths[a] for a in actors) + 10 * (len(actors) - 1)
    x, out = cx - total / 2, []
    for a in actors:
        if a == "d":
            out.append(f'<rect class="fm-mark--d" x="{x:g}" y="{y - 6:g}" width="12" height="12" />')
        elif a == "j":
            out.append(f'<rect class="fm-mark--j" x="{x:g}" y="{y - 6:g}" width="22" height="12" rx="6" />')
        else:
            out.append(person(x + 7, y, 0.8))
        x += widths[a] + 10
    return '<g aria-hidden="true">' + "".join(out) + "</g>"


def phase(p, x, y, w, h, sub_lines, wide):
    label = f"Phase {p['n']}, {p['title']}: {' '.join(p['sub'])}. Open its detail."
    cx = x + w / 2
    out = (f'<a class="fm-link" href="{p["href"]}" aria-label="{e(label)}"><g class="fm-n fm-phase">'
           f'<rect class="fm-box" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="3" />')
    if wide:
        out += text(cx, y + 34, [p["title"]], "fm-t-title", 0)
        out += text(cx, y + 68, sub_lines, "fm-t-sub", 17)
        out += marks(cx, y + h - 13, p["actors"])
    else:
        out += text(cx, y + 28, [p["title"]], "fm-t-title", 0)
        out += text(cx, y + 54, sub_lines, "fm-t-sub", 17)
        out += marks(cx, y + h - 13, p["actors"])
    return out + num(x, y, p["n"]) + "</g></a>"


def svg_open(pid, vw, vh, title, desc, role_img=True):
    role = ' role="img"' if role_img else ""
    return (f'<svg class="fm-svg" viewBox="0 0 {vw} {vh}"{role} aria-labelledby="{pid}-t {pid}-d">'
            f'<title id="{pid}-t">{e(title)}</title><desc id="{pid}-d">{e(desc)}</desc>{defs(pid)}')


TOP_TITLE = "The Requirements Fit Analyzer: seven phases in one loop"
TOP_DESC = ("Find, Judge, Validate, Decide, Build and Learn run in order; Publish follows Learn and feeds the next "
            "night's Find. Dashed feedback arrows run back: blind grades from Decide to Validate, edits and "
            "statements from Learn to Build, and calls that retrain the models from Learn to Judge. A guardrail "
            "ring of deterministic gates surrounds every phase.")


# ---------- the top-level cycle ----------
def top_wide():
    p = "tw"
    W, H = 1200, 560
    xs, y, w, h = [48 + i * 188 for i in range(6)], 232, 158, 110
    out = [svg_open(p, W, H, TOP_TITLE, TOP_DESC, role_img=False)]
    out.append('<rect class="fm-ring" x="8" y="8" width="1184" height="544" rx="36" />')
    for tx in (120, 300, 900, 1080):
        out.append(f'<line class="fm-tick" x1="{tx}" y1="1" x2="{tx}" y2="15" />')
        out.append(f'<line class="fm-tick" x1="{tx}" y1="545" x2="{tx}" y2="559" />')
    for ty in (180, 380):
        out.append(f'<line class="fm-tick" x1="1" y1="{ty}" x2="15" y2="{ty}" />')
        out.append(f'<line class="fm-tick" x1="1185" y1="{ty}" x2="1199" y2="{ty}" />')
    out.append('<text x="600" y="516" text-anchor="middle" dominant-baseline="central">'
               '<tspan class="fm-t-ring">THE GUARDRAIL RING</tspan>'
               f'<tspan class="fm-t-gates" dx="14">{e(" · ".join(RING_GATES))}</tspan></text>')
    # the loop: Learn -> Publish -> the next night's Find
    out.append(arrow(p, "M1067,230 V105 H715"))
    out.append(arrow(p, "M490,105 H127 V229"))
    out.append(text(300, 89, ["the next night"], "fm-t-fb", 0))
    for i in range(5):
        out.append(arrow(p, f"M{xs[i] + w},{y + h / 2:g} H{xs[i + 1] - 2}"))
    # feedback, dashed, routed back along the bottom
    out.append(arrow(p, "M680,342 V376 H514 V346", "fb"))
    out.append(text(597, 394, ["blind grades"], "fm-t-fb", 0))
    out.append(arrow(p, "M1056,342 V376 H890 V346", "fb"))
    out.append(text(973, 394, ["edits, statements"], "fm-t-fb", 0))
    out.append(arrow(p, "M1078,342 V440 H315 V346", "fb"))
    out.append(text(691, 458, ["my calls retrain the models"], "fm-t-fb", 0))
    for i, ph in enumerate(PHASES[:6]):
        out.append(phase(ph, xs[i], y, w, h, ph["sub"], True))
    out.append(phase(PHASES[6], 490, 50, 223, 110, PHASES[6]["sub"], True))
    return "".join(out) + "</svg>"


def top_tall():
    p = "tt"
    W, H = 440, 960
    x, w, h = 90, 250, 86
    ys = [56 + i * 116 for i in range(7)]
    out = [svg_open(p, W, H, TOP_TITLE, TOP_DESC, role_img=False)]
    out.append('<rect class="fm-ring" x="6" y="6" width="428" height="948" rx="30" />')
    out.append(text(220, 32, ["THE GUARDRAIL RING"], "fm-t-ring", 0))
    g = RING_GATES
    out.append(text(220, 902, [f"{g[0]} · {g[1]}", f"{g[2]} · {g[3]}", f"{g[4]} · {g[5]}"], "fm-t-gates", 22))
    for i in range(6):
        out.append(arrow(p, f"M215,{ys[i] + h} V{ys[i + 1] - 2}"))
    out.append(arrow(p, f"M340,{ys[6] + h / 2:g} H400 V{ys[0] + h / 2:g} H342"))
    out.append(arrow(p, f"M90,{ys[3] + 43} H66 V{ys[2] + 43} H88", "fb"))
    out.append(arrow(p, f"M90,{ys[5] + 43} H50 V{ys[4] + 43} H88", "fb"))
    out.append(arrow(p, f"M90,{ys[5] + 58} H30 V{ys[1] + 43} H88", "fb"))
    for i, ph in enumerate(PHASES):
        out.append(phase(ph, x, ys[i], w, h, [" ".join(ph["sub"])], False))
    return "".join(out) + "</svg>"


# ---------- the nightly run ----------
NIGHTLY_TITLE = "The nightly run, step by step"
NIGHTLY_DESC = ("Thirteen numbered steps in four lanes. Prepare: wake on schedule, apply my calls from the day, "
                "retrain the models when due behind a gate. Find: pull every job board, fetch the posting text. "
                "Judge: screen by rules behind a gate, score with trained models, match requirements to my "
                "record, AI review of the shortlist with grey cases sent to me, a second AI read of the "
                "demotions as evidence only. Publish: apply calls made during the run, snapshot the night, "
                "rebuild reports and charts.")


def nightly_wide():
    p = "nw"
    W, H = 1200, 660
    w, h = 165, 66
    out = [svg_open(p, W, H, NIGHTLY_TITLE, NIGHTLY_DESC)]
    pos = {}
    for li, (name, sub, steps) in enumerate(NIGHTLY_LANES):
        top = 10 + li * 165
        if li:
            out.append(f'<line class="fm-sep" x1="16" y1="{top}" x2="1184" y2="{top}" />')
        out.append(text(24, top + 96, [name], "fm-t-lane", 0, "start"))
        out.append(text(24, top + 116, [sub], "fm-t-lanesub", 0, "start"))
        for ci, n in enumerate(steps):
            pos[n] = (175 + ci * 210, top + 70, top)
    order = [n for _, _, steps in NIGHTLY_LANES for n in steps]
    for a, b in zip(order, order[1:]):
        ax, ay, atop = pos[a]
        bx, by, btop = pos[b]
        mid_a, mid_b = ay + h / 2, by + h / 2
        if atop == btop:
            out.append(arrow(p, f"M{ax + w},{mid_a:g} H{bx - 2}"))
            if NIGHTLY[a].get("gate"):
                out.append(gate(ax + w + 22.5, mid_a))
        else:
            xr = ax + w
            out.append(arrow(p, f"M{xr},{mid_a:g} H{xr + 20} V{atop + 157} H150 V{mid_b:g} H{bx - 2}"))
            if NIGHTLY[a].get("gate"):
                out.append(gate(xr + 10, mid_a))
    for n, (x, y, top) in pos.items():
        s = NIGHTLY[n]
        cx = x + w / 2
        if "side" in s:
            way, lines = s["side"]
            out.append(box(x, top + 12, w, 36, "p", lines, lh=14, cls="fm-t-chip"))
            if way == "in":
                out.append(arrow(p, f"M{cx:g},{top + 48} V{y - 2}", "me"))
            else:
                out.append(arrow(p, f"M{cx:g},{y} V{top + 50}", "me"))
        elif "cap" in s:
            out.append(text(cx, top + 44, [s["cap"]], "fm-t-cap", 0))
        out.append(box(x, y, w, h, s["kind"], s["label"], n))
    return "".join(out) + "</svg>"


def nightly_tall():
    p = "nt"
    W = 440
    x, w, h, gap = 24, 240, 58, 30
    cx = x + w / 2
    body, y, prev = [], 10, None
    for li, (name, sub, steps) in enumerate(NIGHTLY_LANES):
        if li:
            body.append(f'<line class="fm-sep" x1="16" y1="{y}" x2="424" y2="{y}" />')
        body.append(f'<text class="fm-t-lane" x="424" y="{y + 20}" text-anchor="end">{e(name)}'
                    f'<tspan class="fm-t-lanesub" dx="8">{e(sub)}</tspan></text>')
        y += 36
        for n in steps:
            s = NIGHTLY[n]
            if prev is not None:
                body.append(arrow(p, f"M{cx:g},{prev[1]} V{y - 2}"))
                if NIGHTLY[prev[0]].get("gate"):
                    body.append(gate(cx, prev[1] + 13, vertical_arrow=True))
            mid = y + h / 2
            if "side" in s:
                way, lines = s["side"]
                body.append(box(288, mid - 23, 140, 46, "p", lines, lh=15, cls="fm-t-chip"))
                body.append(arrow(p, f"M288,{mid:g} H{x + w + 2}" if way == "in" else f"M{x + w},{mid:g} H286", "me"))
            elif "cap" in s:
                body.append(text(358, mid, [s["cap"]], "fm-t-cap", 0))
            body.append(box(x, y, w, h, s["kind"], s["label"], n))
            prev = (n, y + h)
            y += h + gap
        y += 26 - gap
    H = y + 4
    return svg_open(p, W, H, NIGHTLY_TITLE, NIGHTLY_DESC) + "".join(body) + "</svg>"


# ---------- notes and page assembly ----------
def notes(items, cls="fm-notes"):
    lis = "".join(f'<li><strong>{e(lead)}</strong> {e(note)}</li>' for lead, note in items)
    return f'<ol class="{cls}">{lis}</ol>'


def figure(name, wide, tall):
    return (f'<figure class="fm-fig fm-fig--wide" data-fm-fig="{name}">{wide}</figure>'
            f'<figure class="fm-fig fm-fig--tall" data-fm-fig="{name}">{tall}</figure>')


def blocks():
    order = [n for _, _, steps in NIGHTLY_LANES for n in steps]
    assert order == sorted(NIGHTLY) == list(range(1, len(NIGHTLY) + 1)), "nightly numbers must run 1..N in order"
    return {
        "top-fig": figure("top", top_wide(), top_tall()),
        "top-notes": notes([(p["lead"], p["note"]) for p in PHASES], "fm-notes fm-notes--cols"),
        "nightly-fig": figure("nightly", nightly_wide(), nightly_tall()),
        "nightly-notes": notes([(NIGHTLY[n]["lead"], NIGHTLY[n]["note"]) for n in order], "fm-notes fm-notes--cols"),
    }


def main():
    page = PAGE.read_text(encoding="utf-8")
    for name, html in blocks().items():
        pat = re.compile(rf"(<!-- fitmap:{name} -->)(.*?)(<!-- /fitmap:{name} -->)", re.S)
        if not pat.search(page):
            sys.exit(f"marker <!-- fitmap:{name} --> not found in {PAGE.name}")
        page = pat.sub(lambda m: m.group(1) + html + m.group(3), page)
    PAGE.write_text(page, encoding="utf-8")
    print(f"wrote {PAGE.name}: {', '.join(blocks())}")


if __name__ == "__main__":
    main()
