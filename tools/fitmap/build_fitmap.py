#!/usr/bin/env python3
"""Draw the Requirements Fit Analyzer process map (fit-analyzer-map.html).

One data source below draws every figure twice (wide, and tall for narrow screens) and writes the numbered notes
under it, so a marker and its note cannot drift apart. The script rewrites the blocks between
<!-- fitmap:NAME --> and <!-- /fitmap:NAME --> in the page, writes the mini diagram other pages link from
(img/fit-analyzer-map-mini.svg), and leaves everything else alone.

    python3 tools/fitmap/build_fitmap.py && npx prettier --write fit-analyzer-map.html

Public page: describe what each step does, never a file, script or table name. Each note can end with a
technical aside (`tech`), shown in parentheses for technical readers; the plain sentence comes first.
Node kinds: d = script (deterministic), j = AI judgment, p = me, r = a role or outcome.
"""

import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "fit-analyzer-map.html"
MINI = ROOT / "img" / "fit-analyzer-map-mini.svg"


def e(s):
    return escape(s, quote=True)


# ══════════ data: the top-level cycle ══════════
PHASES = [
    dict(n=1, title="Find", sub=("job boards,", "posting text"), actors="dp", href="#nightly", lead="Find.",
         note="Every night a script pulls each employer’s own job board and fetches the full text of every new "
              "posting. I choose which employers are on the list.",
         tech="employers’ own hiring-system feeds across 13 platforms, stored in DuckDB"),
    dict(n=2, title="Judge", sub=("rules, models,", "AI review"), actors="dj", href="#nightly", lead="Judge.",
         note="Rules, trained models and a small embedding model score each posting. Two AI judges read the "
              "Required block of the shortlist.",
         tech="rule engine; TF-IDF with logistic regression; BGE sentence embeddings; TypeSafe Jev and Gemma 4"),
    dict(n=3, title="Validate", sub=("every judge", "is scored"), actors="dp", href="#validate", lead="Validate.",
         note="Every judge is scored against my own blind grades and keeps only the role its score earned.",
         tech="employer-grouped cross-validated AUC; catch and agreement rates; measurement system analysis"),
    dict(n=4, title="Decide", sub=("build, pass,", "hold, grade"), actors="dp", href="#decide", lead="Decide.",
         note="I make the calls: build, pass or hold. Grades I give before seeing any machine score become the "
              "answer key the judges are scored on."),
    dict(n=5, title="Build", sub=("select, check,", "export"), actors="djp", href="#build", lead="Build.",
         note="AI selects verified statements, word for word, from a database of my work and drafts the letter. "
              "Scripts check every fact and phrase, then build the Word files. I edit and send.",
         tech="spaCy keyword extraction; Claude with written skills; python-docx export and its exact reverse"),
    dict(n=6, title="Learn", sub=("retrain, voice,", "record"), actors="djp", href="#learn", lead="Learn.",
         note="My calls retrain the models through a gate. A script finds every edit I make to a sent document "
              "and AI explains why, so the voice guide and the record of my work both improve.",
         tech="gated retraining; word-level document diff"),
    dict(n=7, title="Publish", sub=("reports, charts,", "presentation"), actors="dp", href="#nightly",
         lead="Publish.",
         note="A snapshot of each night rebuilds the reports, charts and presentation. I review anything new "
              "before it goes public.",
         tech="PostgreSQL reporting views; SVG charts; an HTML deck"),
]
RING_GATES = ("retraining gate", "judge bars", "repeatability bars", "statement guards", "verb check",
              "document check")

# ══════════ data: the nightly run (a snake of lanes) ══════════
# side: ("in", lines) = I feed this step; ("out", lines) = it hands work to me. cap = a short caption.
# gate = a gate on the arrow out of the step. loop = (step, label): a dashed fix-and-retry arrow back.
NIGHTLY_LANES = [
    ("PREPARE", "before the pull", [1, 2, 3]),
    ("FIND", "phase 1", [4, 5]),
    ("JUDGE", "phase 2", [6, 7, 8, 9, 10]),
    ("PUBLISH", "phase 7", [11, 12, 13]),
]
NIGHTLY = {
    1: dict(kind="d", label=("Wake on", "schedule"), lead="Wake on schedule.",
            note="I pick the start time. A scheduled task wakes the laptop five minutes before it, so a sleeping "
                 "machine still runs, and the pre-flight checks run twice: when I confirm and when it starts.",
            tech="a Windows scheduled task with wake-to-run, since a sleeping laptop never fires cron"),
    2: dict(kind="d", label=("Apply my", "calls"), side=("in", ("My calls", "from the day")),
            lead="Apply my calls.",
            note="The build, pass and hold calls and the grades I entered during the day wait in a queue. They "
                 "are applied first, so tonight’s scores already know them."),
    3: dict(kind="d", label=("Retrain the", "models"), cap="when due", gate=True, lead="Retrain the models.",
            note="When a retrain is due, the fit models train again on my latest calls and grades. A new model "
                 "replaces the old one only if it clears the gate: a shuffled-label check for leaks, accuracy no "
                 "worse than the last model that passed, and no drop in labels. A model that fails is discarded, "
                 "and every attempt is logged.",
            tech="shuffled-label AUC must land between 0.40 and 0.60; employer-grouped AUC at least the last "
                 "promoted run’s minus 0.02; labels at least 95% of the last run’s"),
    4: dict(kind="d", label=("Pull every", "job board"), lead="Pull every job board.",
            note="A script pulls each employer’s own job board, the same data its careers page shows. New postings "
                 "are added and returning ones reopened. A posting is closed only when a clean, complete pull no "
                 "longer lists it, and nothing is deleted, so every posting keeps its full history.",
            tech="one adapter per hiring-system platform, run in parallel"),
    5: dict(kind="d", label=("Fetch the", "posting text"), lead="Fetch the posting text.",
            note="The full text of each new posting is fetched, along with a share of the older ones still "
                 "missing it. A posting fetched again keeps the grade it already has."),
    6: dict(kind="d", label=("Screen by", "rules"), gate=True, lead="Screen by rules.",
            note="Rules screen each posting on function, level, location, clearance and discipline. Every verdict "
                 "keeps its reasons, so when a rule changes, the postings it screened out can be reopened."),
    7: dict(kind="d", label=("Score with", "trained models"), lead="Score with trained models.",
            note="Small trained models score fit on my three lenses: process, technical and applied AI. The best "
                 "of the three sets the rank. Two more score the Required block and the closest matches, and "
                 "their scores are shown beside the rank.",
            tech="TF-IDF on words and word pairs with class-balanced logistic regression, one model per lens; "
                 "employer-grouped held-out AUC about 0.955. The Required score adds a stacked logistic "
                 "regression over TF-IDF, a BGE-base embedding of the Required block and a per-line roll-up"),
    8: dict(kind="d", label=("Match requirements", "to my record"), cap="explains the rank",
            lead="Match requirements to my record.",
            note="A small embedding model that runs on the laptop matches each requirement in the posting to the "
                 "piece of my record that answers it, and marks it strong, partial or a gap. As a ranker it "
                 "scored 0.669 against the trained models’ 0.955, so its job is to explain the rank.",
            tech="BAAI bge-small-en-v1.5 sentence embeddings, cosine similarity, run locally"),
    9: dict(kind="j", label=("AI review of", "the shortlist"), side=("out", ("Grey cases", "come to me")),
            lead="AI review of the shortlist.",
            note="Jev, TypeSafe AI’s model for fast typed decisions, reads the Required block of each posting on "
                 "the shortlist. A clear fail is demoted. A fail that rests only on grey lines comes to me to "
                 "check. A posting I have already ruled on is never judged again: my call outranks Jev’s.",
            tech="typed outputs, one pinned model version; scored on the gold set at 91% catch and 93% agreement"),
    10: dict(kind="j", label=("Second read of", "the demotions"), cap="evidence only",
             lead="Second read of the demotions.",
             note="Gemma, a second AI judge, reads only Jev’s demotions. It never passed its accuracy bar in "
                  "eight rounds, so its read is shown as evidence beside each demotion and decides nothing.",
             tech="Gemma 4 through Google AI Studio; bars of 70% catch and 85% agreement"),
    11: dict(kind="d", label=("Apply my", "calls again"), side=("in", ("Calls made", "during the run")),
             lead="Apply my calls again.",
             note="Calls I made while the run was going are applied before the snapshot, so nothing I decided "
                  "waits a day."),
    12: dict(kind="d", label=("Snapshot", "the night"), lead="Snapshot the night.",
             note="One snapshot copies the night’s results into the reporting database in a single swap, so a "
                  "report never reads a half-finished night.",
             tech="DuckDB to PostgreSQL in one transaction"),
    13: dict(kind="d", label=("Rebuild reports", "and charts"), lead="Rebuild reports and charts.",
             note="Forty-five seconds later the reports, charts, workbook and presentation rebuild from the "
                  "snapshot, and my application tracker refreshes. If nothing changed, nothing rebuilds. The "
                  "public charts show only industries and percentages.",
             tech="SQL reporting views feed SVG charts, an Excel workbook and an HTML deck"),
}

# ══════════ data: the application build (a snake of lanes) ══════════
BUILD_LANES = [
    ("PREPARE", "the posting in", [1, 2, 3, 4]),
    ("DRAFT", "select, then check", [5, 6, 7, 8]),
    ("WORD FILES", "build, edit, send", [9, 10, 11, 12]),
    ("MY EDITS", "learn from them", [13, 14, 15, 16, 17]),
]
BUILD = {
    1: dict(kind="p", label=("I choose", "to build"), lead="I choose to build.",
            note="A role from the reports gets a build only when I choose it. A duplicate check runs first, then the "
                 "application gets its own folder and a line in my tracker."),
    2: dict(kind="d", label=("Capture the", "posting"), lead="Capture the posting.",
            note="The posting text is saved word for word, so the draft is written against what the employer "
                 "actually asked for, even after the posting comes down."),
    3: dict(kind="j", label=("Sort the", "keywords"), lead="Sort the keywords.",
            note="The posting’s keywords are sorted into required, preferred and context, so the draft can be "
                 "checked for coverage later. A language library finds the candidates and an AI model sorts "
                 "them.",
            tech="spaCy, then Gemma 4, with Groq and then a Claude subagent as fallbacks"),
    4: dict(kind="j", label=("Read the", "requirements"), side=("out", ("Questions", "for me")),
            lead="Read the requirements.",
            note="Claude reads the requirements against my background and the rules on what I may claim, notes "
                 "where I fit and where I don’t, and asks me anything it can’t settle from the record.",
            tech="Claude with written skills, my voice guide and a guardrails file"),
    5: dict(kind="j", label=("Select", "statements"), cap="word for word", lead="Select statements.",
            note="Claude picks 14 to 16 statements from the database of verified statements about my work. Each "
                 "is used word for word, and a script looks up each one’s guards: what it must never be used to "
                 "claim, and which statements it may not appear beside.",
            tech="202 statements, each tagged by project, problem solved and lens"),
    6: dict(kind="j", label=("Draft the resume", "and letter"), lead="Draft the resume and letter.",
            note="Claude writes the summary and the cover letter in my voice, and lists every statement it cut "
                 "and why. The facts come only from the selected statements."),
    7: dict(kind="d", label=("Check", "coverage"), lead="Check coverage.",
            note="A script measures how much of the posting’s keyword list the draft covers. Covering most of it "
                 "is the target; chasing every last keyword makes worse writing, so the check stops there.",
            tech="65 to 75% is the target band"),
    8: dict(kind="d", label=("Quality", "check"), gate=True, loop=(6, "fail: fix the draft, check again"),
            lead="Quality check.",
            note="A script checks everything with one right answer: every figure against the statement it came "
                 "from, company names and dates against the record, standing bans on certain figures, layout "
                 "rules, the letter’s parts, and my voice. One failure stops the build until it is fixed.",
            tech="a voice checker counts the phrasing habits of AI-written text, measured against my own "
                 "pre-AI writing"),
    9: dict(kind="d", label=("Build the", "Word files"), lead="Build the Word files.",
            note="Scripts turn the checked draft into a resume on my template, fitted to two pages, and a "
                 "one-page letter that matches it.",
            tech="python-docx; Word itself counts the pages"),
    10: dict(kind="d", label=("Check the", "Word files"), gate=True, lead="Check the Word files.",
             note="The same check runs on the Word files, and the letter must read back identical to its draft."),
    11: dict(kind="p", label=("I edit", "and send"), lead="I edit and send.",
             note="I read both documents, edit them in Word, save the PDFs and send the application."),
    12: dict(kind="d", label=("Record", "the send"), lead="Record the send.",
             note="The tracker records the application, and the PDFs move off the laptop to cloud storage."),
    13: dict(kind="d", label=("Find every", "edit"), cap="every edit", lead="Find every edit.",
             note="A script compares the documents I sent with the drafts and records every change, down to a "
                  "single word. A script never misses a one-word cut.",
             tech="a word-level diff of the sent Word files against the drafts"),
    14: dict(kind="j", label=("Explain", "each edit"), lead="Explain each edit.",
             note="Claude writes why I made each change. Meaning is a judgment, so this step is AI, and it feeds "
                  "the voice guide."),
    15: dict(kind="d", label=("Read the Word", "files back"), lead="Read the Word files back.",
             note="Scripts turn my sent Word files back into the draft format, exactly, so the record of the "
                  "application matches what I actually sent.",
             tech="exact inverses of the export, tested lossless on 36 of 40 earlier letters, the rest off only "
                  "by trailing spaces"),
    16: dict(kind="d", label=("Check", "again"), gate=True, lead="Check again.",
             note="The quality check runs once more. A failure here is usually an edit I made on purpose, so it "
                  "is reported to me and never “fixed.”"),
    17: dict(kind="p", label=("New statements:", "I decide"), lead="New statements: I decide.",
             note="Edits that changed a statement come to me as candidates. I decide in the database itself "
                  "whether the master statement changes; tailored wording never leaks back on its own."),
}

# ══════════ data: judges and validation ══════════
VALIDATE = [
    # (id, kind, judge label, role label, passed?, lead, note, tech)
    ("key", "p", ("My blind grades", "the answer key"), None, None, "My blind grades.",
     "Grades I give a posting before I see any machine score. Only these count as the answer key, and every "
     "judge below is scored against them.",
     "the gold set: blind rows that include a Required-fit call"),
    ("rules", "d", ("Rules", "keep their reasons"), ("Screen: candidate,", "review or reject"), True, "Rules.",
     "Rules on function, level, location, clearance and discipline. Each verdict keeps its reasons, so a rule "
     "that screens out a good posting can be found and changed.", None),
    ("models", "d", ("Trained models", "AUC 0.955"), ("Sets the rank",), True, "Trained models.",
     "Small models trained on my own calls and grades, one per lens. They rank well on employers they never saw "
     "in training, and a retrain replaces them only if it passes the gate.",
     "TF-IDF with logistic regression; AUC measured on held-out employers; retrain gate with a shuffled-label "
     "leak check"),
    ("embed", "d", ("Embedding model", "AUC 0.669"), ("Explains the rank",), False, "Embedding model.",
     "Matching requirements to my record by meaning looked like the obvious ranker. Its scores bunched too "
     "tightly to rank, so it failed that bar and kept the job of explaining the rank.",
     "bge-small sentence embeddings, cosine similarity"),
    ("gemma", "j", ("Gemma", "never passed"), ("Evidence only",), False, "Gemma.",
     "A second AI judge for the Required block. It missed its bar in eight rounds, so it decides nothing and "
     "its read is shown beside Jev’s demotions.",
     "Gemma 4; bars of 70% catch (the share of my fails it also catches) and 85% agreement"),
    ("jev", "j", ("Jev", "91% catch · 93% agree"), ("Demotes a clear fail;", "grey cases to me"), True, "Jev.",
     "TypeSafe AI’s typed-decision model passed the Required bar and a repeatability study, so it may demote a "
     "clear fail. It missed the calibration bar, so it acts only on its yes-or-no call and hands grey cases to "
     "me.",
     "measurement system analysis: lens agreement at least 0.70, repeat flips at most 2% (it scored 1.6%), "
     "median change at most 0.03, prompt injection caught 4 of 5 times; calibration ECE bar 0.10, missed"),
    ("me", "p", ("Me, re-grading", "55 of 72 unchanged"), ("Stays the", "answer key"), True, "Me.",
     "I am a gauge too. Between my first pass on one blind sheet and my final grades, 55 of 72 grades stayed "
     "the same, which tells me how firm the answer key is.",
     "test-retest repeatability of the human grader"),
]

# ══════════ data: the feedback loop (free layout) ══════════
DECIDE_NODES = {
    "app": dict(kind="p", label=("My calls in the app", "build, pass, hold"), n=1, lead="My calls in the app.",
                note="In a small app I mark a posting build, pass or hold, with a reason and any requirement I "
                     "don’t meet. An ordinary pass teaches the models. A pass for reasons outside the work, such as location, does not.",
                tech="a Python desktop app writing to a PostgreSQL queue"),
    "grades": dict(kind="p", label=("Grades only", "lens, overall, Required"), n=2, lead="Grades only.",
                   note="I can grade a posting without deciding on it: a grade on each lens, an overall grade, and "
                        "whether I meet the Required block. Given blind, these become answer-key rows."),
    "sheet": dict(kind="p", label=("Blind grading", "sheets"), n=3, lead="Blind grading sheets.",
                  note="Batches of postings I grade with every machine score hidden. Some include decoys, to "
                       "measure the AI judges directly. They go straight to the answer key."),
    "queue": dict(kind="d", label=("Decision", "queue"), n=4, lead="Decision queue.",
                  note="Everything I enter waits in one queue, so nothing I decide during the day is lost while "
                       "the pipeline is busy."),
    "apply": dict(kind="d", label=("Applied before", "the run"), n=5, lead="Applied before the run.",
                  note="The queue is applied at the start of each run and again just before the snapshot. A "
                       "grade that conflicts with an earlier blind or seen call of mine is refused, so blind and "
                       "seen grades never mix in the answer key."),
    "labels": dict(kind="d", label=("Training labels", "to the retrain gate"), n=6, lead="Training labels.",
                   note="Decisions and lens grades become the labels the next retrain learns from. A build on a "
                        "posting Jev demoted is a human overrule: Jev never judges it again, and it becomes a "
                        "ruling Jev is scored on."),
    "gold": dict(kind="d", label=("The answer key", "to judge scoring"), n=7, lead="The answer key.",
                 note="Blind grades with a Required call join the gold set every judge is scored against."),
    "status": dict(kind="p", label=("Status, notes,", "contacts"), n=8, lead="Status, notes, contacts.",
                   note="Beside the calls, the tracker keeps where each application stands, my notes and the "
                        "people involved. I update it from the app or a command line."),
    "inbox": dict(kind="d", label=("Email", "watcher"), cap="hourly", n=9, lead="Email watcher.",
                  note="Every hour a script reads job email, such as confirmations and rejections, and updates "
                       "the tracker."),
    "tracker": dict(kind="d", label=("Tracker", "database"), n=10, lead="Tracker database.",
                    note="One database stores the tracker, the record of my work and the nightly snapshot.",
                    tech="PostgreSQL"),
    "views": dict(kind="d", label=("Tracker sheet,", "focus report"), n=11, lead="Tracker sheet and reports.",
                  note="A read-only sheet and my daily focus report refresh from it, so I never keep two lists."),
}
DECIDE_EDGES = [("app", "queue"), ("grades", "queue"), ("queue", "apply"), ("apply", "labels"), ("apply", "gold"),
                ("sheet", "gold"), ("status", "tracker"), ("inbox", "tracker"), ("tracker", "views")]
DECIDE_WIDE = dict(W=1200, H=560, nodes={
    "app": (30, 40, 230, 62), "grades": (30, 130, 230, 62), "sheet": (30, 220, 230, 62),
    "queue": (340, 130, 200, 62), "apply": (610, 130, 200, 62),
    "labels": (890, 60, 270, 62), "gold": (890, 200, 270, 62),
    "status": (30, 400, 230, 62), "inbox": (340, 470, 200, 62),
    "tracker": (610, 400, 200, 62), "views": (890, 400, 270, 62),
}, paths={("sheet", "gold"): "M260,251 H300 V300 H1025 V264", ("status", "tracker"): "M260,431 H608",
          ("inbox", "tracker"): "M540,501 H575 V431"},
    extra=[("sep", 16, 350, 1184), ("lane", 30, 378, "THE TRACKER, BESIDE IT")])
DECIDE_TALL = dict(W=440, H=724, nodes={
    "app": (24, 10, 190, 62), "grades": (226, 10, 190, 62),
    "queue": (24, 112, 190, 56), "sheet": (226, 112, 190, 56),
    "apply": (24, 208, 190, 56),
    "labels": (24, 304, 190, 62), "gold": (226, 304, 190, 62),
    "status": (24, 460, 190, 56), "inbox": (226, 460, 190, 56),
    "tracker": (120, 556, 200, 56), "views": (120, 652, 200, 56),
}, paths={("grades", "queue"): "M321,72 V92 H119 V110", ("apply", "gold"): "M214,236 H321 V302",
          ("sheet", "gold"): "M321,168 V302", ("status", "tracker"): "M119,516 V536 H220 V554",
          ("inbox", "tracker"): "M321,516 V536 H220 V554"},
    extra=[("sep", 16, 396, 424), ("lane", 24, 418, "THE TRACKER, BESIDE IT")])

# ══════════ data: the learning loops ══════════
# Each loop: four steps, clockwise from the signal I give. gate = index of the step a gate guards.
LOOPS = [
    dict(n=1, title="Models", sub="the next night", gate=2, steps=[
        ("p", ("My calls and", "lens grades")), ("d", ("Retrain the", "fit models")),
        ("d", ("Promote", "or discard")), ("d", ("The rank", "improves"))],
         lead="Models.",
         note="My build and pass calls and lens grades become labels. The models retrain, and a new model replaces "
              "the old one only if it beats it under the same gate, so a bad retrain can never demote a good model.",
         tech="labels per lens; shuffled-label leak check; employer-grouped AUC; every run ledgered"),
    dict(n=2, title="Judges", sub="the next scoring night", gate=2, steps=[
        ("p", ("My blind", "grades")), ("d", ("Score every", "judge")),
        ("d", ("Keep the role", "it earned")), ("j", ("Judges act only", "where they pass"))],
         lead="Judges.",
         note="Each new blind grade, and each time I overrule a demotion, adds to the answer key. On scoring "
              "nights every AI judge is scored again, and a judge keeps only the role its bar allows. A newer "
              "model version takes the same test before the pipeline moves to it.",
         tech="catch and agreement bars; repeatability, injection and calibration studies; results ledgered"),
    dict(n=3, title="Voice", sub="the next draft", gate=None, steps=[
        ("p", ("My edits to", "sent documents")), ("d", ("Find every", "edit")),
        ("j", ("Explain", "each edit")), ("j", ("Update the", "voice guide"))],
         lead="Voice.",
         note="Every edit I make to a sent resume or letter is found by script and explained by AI. After about "
              "five applications the voice guide is re-derived from the explained edits, and any habit that can be "
              "counted goes into the voice checker, so drafts drift less from how I write.",
         tech="word-level diff; an edits corpus; countable tics move into the deterministic checker"),
    dict(n=4, title="Statements", sub="the next build", gate=2, steps=[
        ("p", ("My edits and", "new background")), ("d", ("List the", "candidates")),
        ("p", ("I decide in", "the database")), ("d", ("The record", "improves"))],
         lead="Statements.",
         note="When an edit changes a statement, or a build surfaces background the record lacks, it becomes a "
              "candidate. Only I change a master statement, in the database itself, so tailored wording never "
              "leaks back into the record on its own.",
         tech="lint views check length, references, first person, tags and opening-verb variety"),
]


# ══════════ drawing helpers ══════════
def defs(p):
    out = "<defs>"
    for k, colour in (("a", "#2c2e2f"), ("m", "#c27b58"), ("f", "#4a4b45")):
        out += (f'<marker id="{p}-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{colour}" /></marker>')
    return out + "</defs>"


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


def gate(x, y, vertical_arrow=False, ok=True):
    """A bar across the arrow at (x, y), with a check mark (passed) or a cross (failed its bar) beside it."""
    if vertical_arrow:
        bar, mx, my = f'x1="{x - 12:g}" y1="{y:g}" x2="{x + 12:g}" y2="{y:g}"', x + 17, y - 1
    else:
        bar, mx, my = f'x1="{x:g}" y1="{y - 12:g}" x2="{x:g}" y2="{y + 12:g}"', x - 6, y - 21
    mark = (f'<path d="M{mx:g},{my:g} l4,4 l8,-9" />' if ok else
            f'<path class="fm-gate__x" d="M{mx:g},{my - 6:g} l9,9 m0,-9 l-9,9" />')
    return f'<g class="fm-gate"><line {bar} />{mark}</g>'


def box(x, y, w, h, kind, lines, n=None, lh=18, cls="fm-t-node"):
    rx = {"d": 0, "j": h / 2, "p": 7, "r": 3}[kind]
    k = {"d": "det", "j": "judg", "p": "person", "r": "role"}[kind]
    out = (f'<g class="fm-n fm-n--{k}"><rect class="fm-box" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
           f'rx="{rx:g}" />')
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


def svg_open(pid, vw, vh, title, desc, role_img=True):
    role = ' role="img"' if role_img else ""
    return (f'<svg class="fm-svg" viewBox="0 0 {vw:g} {vh:g}"{role} aria-labelledby="{pid}-t {pid}-d">'
            f'<title id="{pid}-t">{e(title)}</title><desc id="{pid}-d">{e(desc)}</desc>{defs(pid)}')


def route(a, b):
    """An orthogonal path from box a to box b (each x, y, w, h)."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    if ax + aw <= bx:
        sy, ty = ay + ah / 2, by + bh / 2
        if abs(sy - ty) < 1:
            return f"M{ax + aw:g},{sy:g} H{bx - 2:g}"
        mx = (ax + aw + bx) / 2
        return f"M{ax + aw:g},{sy:g} H{mx:g} V{ty:g} H{bx - 2:g}"
    sx, tx = ax + aw / 2, bx + bw / 2
    if ay + ah <= by:
        if abs(sx - tx) < 1:
            return f"M{sx:g},{ay + ah:g} V{by - 2:g}"
        my = (ay + ah + by) / 2
        return f"M{sx:g},{ay + ah:g} V{my:g} H{tx:g} V{by - 2:g}"
    raise ValueError(f"no automatic route from {a} to {b}; give a path")


# ══════════ the top-level cycle ══════════
TOP_TITLE = "The Requirements Fit Analyzer: seven phases in one loop"
TOP_DESC = ("Find, Judge, Validate, Decide, Build and Learn run in order; Publish follows Learn and feeds the next "
            "night's Find. Dashed feedback arrows run back: blind grades from Decide to Validate, edits and "
            "statements from Learn to Build, and calls that retrain the models from Learn to Judge. A guardrail "
            "ring of deterministic gates surrounds every phase.")


def phase(p, x, y, w, h, sub_lines, wide, mini=False):
    cx = x + w / 2
    if mini:
        out = (f'<g class="fm-n fm-phase"><rect class="fm-box" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
               f'rx="3" />' + text(cx, y + h / 2, [p["title"]], "fm-t-title", 0))
        return out + num(x, y, p["n"]) + "</g>"
    label = f"Phase {p['n']}, {p['title']}: {' '.join(p['sub'])}. Open its detail."
    out = (f'<a class="fm-link" href="{p["href"]}" aria-label="{e(label)}"><g class="fm-n fm-phase">'
           f'<rect class="fm-box" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="3" />')
    out += text(cx, y + (34 if wide else 28), [p["title"]], "fm-t-title", 0)
    out += text(cx, y + (68 if wide else 54), sub_lines, "fm-t-sub", 17)
    out += marks(cx, y + h - 13, p["actors"])
    return out + num(x, y, p["n"]) + "</g></a>"


def top_wide(mini=False):
    p = "tw" if not mini else "mini"
    xs, y, w, h = [48 + i * 188 for i in range(6)], 232, 158, 110
    if mini:
        y, h = 250, 80
    out = [svg_open(p, 1200, 560, TOP_TITLE, TOP_DESC, role_img=mini)]
    out.append('<rect class="fm-ring" x="8" y="8" width="1184" height="544" rx="36" />')
    for tx in (120, 300, 900, 1080):
        out.append(f'<line class="fm-tick" x1="{tx}" y1="1" x2="{tx}" y2="15" />')
        out.append(f'<line class="fm-tick" x1="{tx}" y1="545" x2="{tx}" y2="559" />')
    for ty in (180, 380):
        out.append(f'<line class="fm-tick" x1="1" y1="{ty}" x2="15" y2="{ty}" />')
        out.append(f'<line class="fm-tick" x1="1185" y1="{ty}" x2="1199" y2="{ty}" />')
    if mini:
        out.append(text(600, 500, ["THE GUARDRAIL RING"], "fm-t-ring", 0))
    else:
        out.append('<text x="600" y="516" text-anchor="middle" dominant-baseline="central">'
                   '<tspan class="fm-t-ring">THE GUARDRAIL RING</tspan>'
                   f'<tspan class="fm-t-gates" dx="14">{e(" · ".join(RING_GATES))}</tspan></text>')
    bottom = y + h
    # the loop: Learn -> Publish -> the next night's Find
    out.append(arrow(p, f"M1067,{y - 2} V105 H715"))
    out.append(arrow(p, f"M490,105 H127 V{y - 1}"))
    for i in range(5):
        out.append(arrow(p, f"M{xs[i] + w},{y + h / 2:g} H{xs[i + 1] - 2}"))
    # feedback, dashed, routed back along the bottom
    out.append(arrow(p, f"M680,{bottom} V{bottom + 34} H514 V{bottom + 4}", "fb"))
    out.append(arrow(p, f"M1056,{bottom} V{bottom + 34} H890 V{bottom + 4}", "fb"))
    out.append(arrow(p, f"M1078,{bottom} V{bottom + 98} H315 V{bottom + 4}", "fb"))
    if not mini:
        out.append(text(300, 89, ["the next night"], "fm-t-fb", 0))
        out.append(text(597, 394, ["blind grades"], "fm-t-fb", 0))
        out.append(text(973, 394, ["edits, statements"], "fm-t-fb", 0))
        out.append(text(691, 458, ["my calls retrain the models"], "fm-t-fb", 0))
    for i, ph in enumerate(PHASES[:6]):
        out.append(phase(ph, xs[i], y, w, h, ph["sub"], True, mini))
    out.append(phase(PHASES[6], 490, 50, 223, 110, PHASES[6]["sub"], True, mini))
    return "".join(out) + "</svg>"


def top_tall():
    p = "tt"
    x, w, h = 90, 250, 86
    ys = [56 + i * 116 for i in range(7)]
    out = [svg_open(p, 440, 960, TOP_TITLE, TOP_DESC, role_img=False)]
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


MINI_STYLE = (
    "<style>"
    ".fm-ring{fill:none;stroke:#3b4b35;stroke-width:2}.fm-tick{stroke:#3b4b35;stroke-width:2}"
    ".fm-box{fill:#f0ead6;stroke:#7c7a71;stroke-width:1.5}"
    ".fm-ar{fill:none;stroke:#2c2e2f;stroke-width:2}.fm-ar--fb{stroke:#4a4b45;stroke-dasharray:7 6}"
    ".fm-num{fill:#bfa36f}"
    "text{font-family:'Iowan Old Style',Georgia,serif;fill:#2c2e2f}"
    ".fm-t-title{font-size:36px}"
    ".fm-t-num{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;font-size:14px;font-weight:700;fill:#161914}"
    ".fm-t-ring{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;font-size:22px;font-weight:600;"
    "letter-spacing:.16em;fill:#3b4b35}"
    "</style>"
)


def mini_svg():
    """The small static diagram other pages link from (an <img>, so styles are inline and fonts fall back)."""
    s = top_wide(mini=True).replace('class="fm-svg" ', 'xmlns="http://www.w3.org/2000/svg" ', 1)
    s = s.replace("<defs>", MINI_STYLE + "<defs>", 1)
    return s.replace("<svg ", '<svg width="1200" height="560" ', 1) + "\n"


# ══════════ snakes: the nightly run and the application build ══════════
def snake_wide(p, lanes, steps, title, desc):
    w, h = 165, 66
    out, pos = [], {}
    for li, (name, sub, ns) in enumerate(lanes):
        top = 10 + li * 165
        if li:
            out.append(f'<line class="fm-sep" x1="16" y1="{top}" x2="1184" y2="{top}" />')
        out.append(text(24, top + 96, [name], "fm-t-lane", 0, "start"))
        out.append(text(24, top + 116, [sub], "fm-t-lanesub", 0, "start"))
        for ci, n in enumerate(ns):
            pos[n] = (175 + ci * 210, top + 70, top)
    order = [n for _, _, ns in lanes for n in ns]
    for a, b in zip(order, order[1:]):
        ax, ay, atop = pos[a]
        bx, by, btop = pos[b]
        mid_a, mid_b = ay + h / 2, by + h / 2
        if atop == btop:
            out.append(arrow(p, f"M{ax + w},{mid_a:g} H{bx - 2}"))
            if steps[a].get("gate"):
                out.append(gate(ax + w + 22.5, mid_a))
        else:
            xr = ax + w
            out.append(arrow(p, f"M{xr},{mid_a:g} H{xr + 20} V{atop + 157} H150 V{mid_b:g} H{bx - 2}"))
            if steps[a].get("gate"):
                out.append(gate(xr + 10, mid_a))
    for n, (x, y, top) in pos.items():
        s = steps[n]
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
        if "loop" in s:
            back, label = s["loop"]
            bx = pos[back][0] + w / 2
            out.append(arrow(p, f"M{cx:g},{y} V{top + 34} H{bx:g} V{y - 2}", "fb"))
            out.append(text((cx + bx) / 2, top + 22, [label], "fm-t-fb", 0))
        out.append(box(x, y, w, h, s["kind"], s["label"], n))
    H = 10 + len(lanes) * 165 - 15
    return svg_open(p, 1200, H, title, desc) + "".join(out) + "</svg>"


def snake_tall(p, lanes, steps, title, desc):
    x, w, h, gap = 24, 240, 58, 30
    cx = x + w / 2
    body, y, prev, ys = [], 10, None, {}
    for li, (name, sub, ns) in enumerate(lanes):
        if li:
            body.append(f'<line class="fm-sep" x1="16" y1="{y}" x2="424" y2="{y}" />')
        body.append(f'<text class="fm-t-lane" x="424" y="{y + 20}" text-anchor="end">{e(name)}'
                    f'<tspan class="fm-t-lanesub" dx="8">{e(sub)}</tspan></text>')
        y += 36
        for n in ns:
            s = steps[n]
            if prev is not None:
                body.append(arrow(p, f"M{cx:g},{prev[1]} V{y - 2}"))
                if steps[prev[0]].get("gate"):
                    body.append(gate(cx, prev[1] + 13, vertical_arrow=True))
            mid = y + h / 2
            ys[n] = mid
            if "side" in s:
                way, lines = s["side"]
                body.append(box(288, mid - 23, 140, 46, "p", lines, lh=15, cls="fm-t-chip"))
                body.append(arrow(p, f"M288,{mid:g} H{x + w + 2}" if way == "in" else f"M{x + w},{mid:g} H286", "me"))
            elif "cap" in s:
                body.append(text(358, mid, [s["cap"]], "fm-t-cap", 0))
            if "loop" in s:
                body.append(arrow(p, f"M{x},{mid:g} H6 V{ys[s['loop'][0]]:g} H{x - 2}", "fb"))
            body.append(box(x, y, w, h, s["kind"], s["label"], n))
            prev = (n, y + h)
            y += h + gap
        y += 26 - gap
    return svg_open(p, 440, y + 4, title, desc) + "".join(body) + "</svg>"


NIGHTLY_TITLE = "The nightly run, step by step"
NIGHTLY_DESC = ("Thirteen numbered steps in four lanes. Prepare: wake on schedule, apply my calls from the day, "
                "retrain the models when due behind a gate. Find: pull every job board, fetch the posting text. "
                "Judge: screen by rules behind a gate, score with trained models, match requirements to my "
                "record, AI review of the shortlist with grey cases sent to me, a second AI read of the "
                "demotions as evidence only. Publish: apply calls made during the run, snapshot the night, "
                "rebuild reports and charts.")
BUILD_TITLE = "The application build, from posting to sent documents and back"
BUILD_DESC = ("Seventeen numbered steps in four lanes. Prepare: I choose to build, the posting is captured, "
              "keywords sorted, requirements read with questions for me. Draft: statements selected word for word, "
              "resume and letter drafted, coverage checked, then a quality check that sends a failure back to the "
              "draft. Word files: built, checked, edited and sent by me, the send recorded. My edits: every edit "
              "found, each explained, the Word files read back into the draft, checked again, and new statement "
              "candidates decided by me.")


# ══════════ judges and validation ══════════
VAL_TITLE = "Every judge scored against my blind grades"
VAL_DESC = ("My blind grades are the answer key. Six judges are scored against it, each through a gate to the role "
            "it earned: rules screen; trained models (AUC 0.955) set the rank; the embedding model (AUC 0.669) "
            "failed as a ranker and explains the rank; Gemma never passed and is evidence only; Jev (91% catch, "
            "93% agreement) demotes a clear fail and sends grey cases to me; my own re-grades (55 of 72 "
            "unchanged) keep me as the answer key.")


def validate_wide():
    p = "vw"
    out = [svg_open(p, 1200, 580, VAL_TITLE, VAL_DESC)]
    key = VALIDATE[0]
    kb = (30, 255, 220, 70)
    for i, (vid, kind, label, role, ok, *_rest) in enumerate(VALIDATE[1:]):
        y = 40 + i * 90
        jb = (340, y, 250, 60)
        out.append(arrow(p, route(kb, jb)))
        out.append(arrow(p, f"M590,{y + 30} H818"))
        out.append(gate(704, y + 30, ok=ok))
        out.append(box(*jb, kind, label, i + 2, lh=19))
        out.append(box(820, y, 330, 60, "r", role, lh=19))
    out.append(text(704, 14, ["each judge’s bar"], "fm-t-cap", 0))
    out.append(text(985, 14, ["the role it earned"], "fm-t-cap", 0))
    out.append(box(*kb, key[1], key[2], 1, lh=19))
    return "".join(out) + "</svg>"


def validate_tall():
    p = "vt"
    out = [svg_open(p, 440, 600, VAL_TITLE, VAL_DESC)]
    key = VALIDATE[0]
    out.append(box(24, 10, 392, 56, key[1], key[2], 1, lh=18))
    for i, (vid, kind, label, role, ok, *_rest) in enumerate(VALIDATE[1:]):
        y = 100 + i * 84
        out.append(arrow(p, f"M10,66 V{y + 29} H46" if i == 0 else f"M10,{y - 55} V{y + 29} H46"))
        out.append(arrow(p, f"M213,{y + 29} H255"))
        out.append(gate(234, y + 29, ok=ok))
        out.append(box(48, y, 165, 58, kind, label, i + 2, lh=17, cls="fm-t-node fm-t-node--sm"))
        out.append(box(257, y, 159, 58, "r", role, lh=17, cls="fm-t-node fm-t-node--sm"))
    return "".join(out) + "</svg>"


# ══════════ free layouts: the feedback loop ══════════
DECIDE_TITLE = "How my calls and grades flow into the next night"
DECIDE_DESC = ("My calls in the app and grades-only entries go to a decision queue, applied before the run, which "
               "produces training labels for the retrain gate and answer-key rows for judge scoring. Blind grading "
               "sheets go straight to the answer key. Beside it, the tracker: my status updates and an hourly email "
               "watcher feed the tracker database, which refreshes a tracker sheet and the focus report.")


def free(p, layout, nodes, edges, title, desc, small=False):
    W, H, pos, paths = layout["W"], layout["H"], layout["nodes"], layout["paths"]
    out = [svg_open(p, W, H, title, desc)]
    for item in layout.get("extra", []):
        if item[0] == "sep":
            out.append(f'<line class="fm-sep" x1="{item[1]}" y1="{item[2]}" x2="{item[3]}" y2="{item[2]}" />')
        else:
            out.append(text(item[1], item[2], [item[3]], "fm-t-lane", 0, item[4] if len(item) > 4 else "start"))
    for a, b in edges:
        out.append(arrow(p, paths.get((a, b)) or route(pos[a], pos[b])))
    cls = "fm-t-node fm-t-node--sm" if small else "fm-t-node"
    for k, s in nodes.items():
        x, y, w, h = pos[k]
        if "cap" in s:
            out.append(text(x + w / 2, y - 12, [s["cap"]], "fm-t-cap", 0))
        out.append(box(x, y, w, h, s["kind"], s["label"], s.get("n"), lh=18, cls=cls))
    return "".join(out) + "</svg>"


# ══════════ the learning loops ══════════
LEARN_TITLE = "Four loops that learn from me"
LEARN_DESC = ("Four cycles, each starting from something I give. Models: my calls and lens grades, retrain, promote "
              "or discard behind a gate, the rank improves. Judges: my blind grades, every judge scored, each keeps "
              "the role it earned, judges act only where they pass. Voice: my edits, every edit found, each "
              "explained, the voice guide updated. Statements: my edits and new background, candidates listed, I "
              "decide in the database, the record improves.")

# clockwise slot order around a loop's box, starting at the corner nearest the centre of the figure
INNER_START = {0: "c", 1: "d", 2: "b", 3: "a"}
CLOCKWISE = "abcd"


def loop_box(p, lp, qx, qy, qw, qh, start, nw=160, nh=58, sm=False):
    inset = 22
    slot = {"a": (qx + inset, qy + 50), "b": (qx + qw - inset - nw, qy + 50),
            "c": (qx + qw - inset - nw, qy + qh - 30 - nh), "d": (qx + inset, qy + qh - 30 - nh)}
    order = [CLOCKWISE[(CLOCKWISE.index(start) + i) % 4] for i in range(4)]
    out = [f'<rect class="fm-quad" x="{qx}" y="{qy}" width="{qw}" height="{qh}" rx="20" />']
    cls = "fm-t-node fm-t-node--sm" if sm else "fm-t-node"
    boxes = [(slot[s][0], slot[s][1], nw, nh) for s in order]
    for i in range(4):
        a, b = boxes[i], boxes[(i + 1) % 4]
        ax, ay, _, _ = a
        bx, by, _, _ = b
        if ay == by:  # along the top or bottom
            y = ay + nh / 2
            d = f"M{ax + nw:g},{y:g} H{bx - 2:g}" if bx > ax else f"M{ax:g},{y:g} H{bx + nw + 2:g}"
            gx, gy, vert = (ax + nw + bx) / 2 if bx > ax else (bx + nw + ax) / 2, y, False
        else:  # down or up a side
            x = ax + nw / 2
            d = f"M{x:g},{ay + nh:g} V{by - 2:g}" if by > ay else f"M{x:g},{ay:g} V{by + nh + 2:g}"
            gx, gy, vert = x, (ay + nh + by) / 2 if by > ay else (by + nh + ay) / 2, True
        out.append(arrow(p, d, "fb" if i == 3 else ""))
        if lp["gate"] is not None and i + 1 == lp["gate"]:
            out.append(gate(gx, gy, vertical_arrow=vert))
    for (kind, label), b in zip(lp["steps"], boxes):
        out.append(box(*b, kind, label, lh=17, cls=cls))
    cx, cy = qx + qw / 2, qy + qh / 2 - 4
    out.append(text(cx + 12, cy - 10, [lp["title"]], "fm-t-title", 0))
    out.append(num(cx - 12 - len(lp["title"]) * 6.5, cy - 10, lp["n"]))
    out.append(text(cx, cy + 18, [lp["sub"]], "fm-t-cap", 0))
    return "".join(out)


def learn_wide():
    p = "lw"
    out = [svg_open(p, 1200, 600, LEARN_TITLE, LEARN_DESC)]
    quads = [(10, 10), (610, 10), (10, 310), (610, 310)]
    for i, (lp, (qx, qy)) in enumerate(zip(LOOPS, quads)):
        out.append(loop_box(p, lp, qx, qy, 580, 280, INNER_START[i]))
    out.append('<circle class="fm-hub" cx="600" cy="300" r="40" />')
    out.append(person(600, 292, 1.6))
    out.append(text(600, 322, ["me"], "fm-t-cap", 0))
    return "".join(out) + "</svg>"


def learn_tall():
    p = "lt"
    out = [svg_open(p, 440, 1130, LEARN_TITLE, LEARN_DESC)]
    for i, lp in enumerate(LOOPS):
        out.append(loop_box(p, lp, 6, 6 + i * 280, 428, 268, "a", nw=176, nh=56, sm=True))
    return "".join(out) + "</svg>"


# ══════════ notes and page assembly ══════════
def note_li(lead, note, tech=None):
    t = f' <span class="fm-tech">({e(tech)})</span>' if tech else ""
    return f"<li><strong>{e(lead)}</strong> {e(note)}{t}</li>"


def notes(items, cls="fm-notes fm-notes--cols"):
    return f'<ol class="{cls}">' + "".join(note_li(*it) for it in items) + "</ol>"


def figure(name, wide, tall):
    return (f'<figure class="fm-fig fm-fig--wide" data-fm-fig="{name}">{wide}</figure>'
            f'<figure class="fm-fig fm-fig--tall" data-fm-fig="{name}">{tall}</figure>')


def lane_order(lanes, steps):
    order = [n for _, _, ns in lanes for n in ns]
    assert order == sorted(steps) == list(range(1, len(steps) + 1)), "steps must run 1..N in lane order"
    return order


def blocks():
    n_order = lane_order(NIGHTLY_LANES, NIGHTLY)
    b_order = lane_order(BUILD_LANES, BUILD)
    d_nodes = sorted(DECIDE_NODES.values(), key=lambda s: s["n"])
    assert [s["n"] for s in d_nodes] == list(range(1, len(d_nodes) + 1))
    return {
        "top-fig": figure("top", top_wide(), top_tall()),
        "top-notes": notes([(p["lead"], p["note"], p.get("tech")) for p in PHASES]),
        "nightly-fig": figure("nightly",
                              snake_wide("nw", NIGHTLY_LANES, NIGHTLY, NIGHTLY_TITLE, NIGHTLY_DESC),
                              snake_tall("nt", NIGHTLY_LANES, NIGHTLY, NIGHTLY_TITLE, NIGHTLY_DESC)),
        "nightly-notes": notes([(NIGHTLY[n]["lead"], NIGHTLY[n]["note"], NIGHTLY[n].get("tech")) for n in n_order]),
        "validate-fig": figure("validate", validate_wide(), validate_tall()),
        "validate-notes": notes([(v[5], v[6], v[7]) for v in VALIDATE]),
        "decide-fig": figure("decide",
                             free("dw", DECIDE_WIDE, DECIDE_NODES, DECIDE_EDGES, DECIDE_TITLE, DECIDE_DESC),
                             free("dt", DECIDE_TALL, DECIDE_NODES, DECIDE_EDGES, DECIDE_TITLE, DECIDE_DESC, True)),
        "decide-notes": notes([(s["lead"], s["note"], s.get("tech")) for s in d_nodes]),
        "build-fig": figure("build", snake_wide("bw", BUILD_LANES, BUILD, BUILD_TITLE, BUILD_DESC),
                            snake_tall("bt", BUILD_LANES, BUILD, BUILD_TITLE, BUILD_DESC)),
        "build-notes": notes([(BUILD[n]["lead"], BUILD[n]["note"], BUILD[n].get("tech")) for n in b_order]),
        "learn-fig": figure("learn", learn_wide(), learn_tall()),
        "learn-notes": notes([(lp["lead"], lp["note"], lp.get("tech")) for lp in LOOPS], "fm-notes"),
    }


def main():
    page = PAGE.read_text(encoding="utf-8")
    built = blocks()
    for name, html in built.items():
        pat = re.compile(rf"(<!-- fitmap:{name} -->)(.*?)(<!-- /fitmap:{name} -->)", re.S)
        if not pat.search(page):
            sys.exit(f"marker <!-- fitmap:{name} --> not found in {PAGE.name}")
        page = pat.sub(lambda m: m.group(1) + html + m.group(3), page)
    PAGE.write_text(page, encoding="utf-8")
    MINI.write_text(mini_svg(), encoding="utf-8")
    print(f"wrote {PAGE.name} ({', '.join(built)}) and {MINI.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
