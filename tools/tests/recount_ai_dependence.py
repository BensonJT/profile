"""
Re-count how much of each system's code calls a language model, for the AI evaluation section.

Why: the page says "10 of 973 modules call a language model (measured October 27, 2026)". Those counts go
stale as the code changes, so this re-measures them the same way keystone `ai-builder/briefs/deterministic-by-default-brief.md`
and `ai-builder/briefs/abide-evaluations-brief.md` did, and says when the page is out of date. Read-only: it runs
`git ls-files` and reads files; no git pull, no network, no model call.

How it counts (same rules as the briefs):
  - A source module is a tracked code file, with tests, generated code, example files, dead code and build-loop
    tooling left out (see SKIP below). SQL is left out.
  - A module "calls a model" if it makes the request itself. Which modules do was decided by reading each grep
    hit by hand on 2026-10-20 (KNOWN_MODEL below). A grep can't make that call reliably, so instead the script
    greps every module for model words and prints any hit that is not already classified, for a person to read.
    Classify it in KNOWN_MODEL or NOT_A_CALL, then re-run.

Usage (from the profile repo, in WSL on the Vostro, where the repos live):
    npm run test:figures   (or: python3 tools/tests/recount_ai_dependence.py)
Exit code 0 = the page's figures still match; 1 = a figure changed or a grep hit needs a person's review.
"""
import re
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
VAULT = Path("/mnt/c/Users/Jeffrey Benson/Documents/keystone")  # the vault (Benson Academy scripts live there)

# What the page says now (update these when the page is updated). "lm" = language-model modules.
PAGE = {"Meridian": (243, 3), "Forester": (470, 0), "Job Search": (73, 4), "AdoptiScope": (42, 0),
        "Sheets Decomposer": (13, 0), "Benson Academy": (132, 3)}
PAGE_TOTAL = (973, 10)

CODE = {".py", ".sh", ".ts", ".tsx", ".js", ".mjs"}
SKIP = re.compile(
    r"(^|/)(tests?|__tests__|e2e|generated|superseded|ralph|node_modules|\.venv)/"
    r"|(^|/)test_[^/]*\.py$|\.test\.tsx?$|\.spec\.ts$|(^|/)conftest\.py$|\.example\.py$|(^|/)types/api\.ts$"
)
MODEL_WORDS = re.compile(
    r"openai|anthropic|genai|generativeai|generativelanguage|ollama|groq|gemini|gemma|typesafe|\bjev\b"
    r"|sentence_transformers|CrossEncoder|fastembed|faster_whisper|whisper|kokoro|/v1/messages|chat/completions",
    re.I)

# Hand-classified 2026-10-20 (briefs). Paths are relative to each source root.
KNOWN_MODEL = {
    "Meridian": {"scripts/llm_provider.py", "scripts/score_news.py", "scripts/one_time/score_reference_set.py"},
    "Job Search": {"backend/finder/jev.py", "backend/finder/judge2.py", "backend/finder/jev_cli.py",
                   "backend/finder/jev_gate.py"},
    "Benson Academy": {"scripts/narrate.py", "scripts/podcast_episode.py", "scripts/podcast_trial.py"},
}
# Embedding models (local) and speech-to-text checkers: model code, but not a language model writing text.
KNOWN_OTHER_MODEL = {
    "Job Search": {"embed.py", "coverage.py", "required_embed.py", "evidence.py", "retrain.py"},
    "Benson Academy": {"transcribe.py", "check_audio.py", "check_audio_medium.py", "audit_medium.py",
                       "section_video.py", "cut_phrase.py", "draft_voice.py", "find_span.py"},
}
# Grep hits read by hand and found not to make a model call (prompt modules, launchers, readers, prose).
# The first names in each set come from the briefs; the rest were read when this script first ran (2026-10-20):
# they name a model in prose or config, ping a free models-list endpoint (no tokens), read a prompt version, or
# import a helper or a setup check from a model module without calling the model.
NOT_A_CALL = {
    "Meridian": {"news_scoring.py", "cron_news_lane.sh", "smoke_check.py",
                 "api_credits.py", "derive_news_events.py", "doctor.py", "compare_reference_scores.py",
                 "pipeline_log.py", "run_batch.sh", "components.py", "theme.py", "alerts.py"},
    "Job Search": {"pipeline.py", "finder.py", "judge.py", "jev_questions.py", "jev_types.py", "jev_eval.py",
                   "store.py", "blind_sheet.py", "report.py", "requirements.py", "setup_check.py", "launch.sh",
                   "eightfold_worksite_backfill.py", "fact_sheet_sync.py", "gold_redo.sh", "lookup.py",
                   "mcp_lookup_server.py",
                   # read 2026-10-27: a status reader, the snapshot that imports it, and the sweep launcher's --llm-top flag
                   "jev_status.py", "pg_snapshot.py", "sweep_ats.py"},
    "Benson Academy": {"gen_deck.py", "mdx_to_narration.py", "lesson_slides.py", "check_lesson.py", "robots.ts",
                       "Presentation.tsx", "audio_audit_status.py", "split_bsb_tables.py",
                       "tts_budget.py"},  # 2026-10-27: builds the client and paces requests; callers make them,
}


def tracked(repo, *paths):
    out = subprocess.run(["git", "-C", str(repo), "ls-files", *paths], capture_output=True, text=True, check=True)
    return [line for line in out.stdout.splitlines() if line]


def code_files(repo, paths=(), extra=(), skip_more=None):
    """Tracked code files under repo (optionally only `paths`), as (root, relative path) pairs."""
    files = []
    for f in tracked(repo, *paths):
        if SKIP.search(f) or (skip_more and skip_more.search(f)):
            continue
        if Path(f).suffix in CODE or f in extra:
            files.append((Path(repo), f))
    return files


def systems():
    """Each system's source modules, following the briefs' scope rules."""
    abide_vault = [(VAULT, f) for _, f in code_files(VAULT, ["Personal/Projects/abide/"])]
    faith = [(VAULT, f) for _, f in code_files(VAULT, ["Personal/Projects/faith-online/"])]
    # the app repo's scripts, the one root script and the site source; tool configs (web/*.config.*) are not modules
    abide_repo = code_files(HOME / "code/abide", ["scripts/", "web/scripts/", "web/src/", "fix_lesson.py"])
    transcriber = [(HOME / "scripts", "transcribe.py")] if (HOME / "scripts/transcribe.py").exists() else []
    return {
        "Meridian": code_files(HOME / "meridian", skip_more=re.compile(r"^docs/|^ralph/")),
        "Forester": code_files(HOME / "forester", skip_more=re.compile(r"(^|/)loop\.sh$|^skills/")),
        "Job Search": code_files(HOME / "jobsearch"),
        "AdoptiScope": code_files(HOME / "first", extra={"first", "githooks/pre-commit"}),
        "Sheets Decomposer": code_files(HOME / "code/sheets_decomposer", extra={"sd"}),
        "Benson Academy": abide_vault + faith + abide_repo + transcriber,
    }


def lines(root, f):
    try:
        return (root / f).read_text(encoding="utf-8", errors="ignore").count("\n")
    except OSError:
        return 0


def main():
    stale = False
    rows, tot_m, tot_lm, tot_l, tot_lml = [], 0, 0, 0, 0
    for name, files in systems().items():
        known = KNOWN_MODEL.get(name, set())
        other = KNOWN_OTHER_MODEL.get(name, set())
        quiet = NOT_A_CALL.get(name, set())
        lm = [(r, f) for r, f in files if f in known or any(f.endswith("/" + k) for k in known)]
        n_lines = sum(lines(r, f) for r, f in files)
        lm_lines = sum(lines(r, f) for r, f in lm)
        rows.append((name, len(files), len(lm), n_lines, lm_lines))
        tot_m, tot_lm, tot_l, tot_lml = tot_m + len(files), tot_lm + len(lm), tot_l + n_lines, tot_lml + lm_lines
        for r, f in files:  # unclassified grep hits need a person to read them
            base = Path(f).name
            if (r, f) in lm or base in other or base in quiet:
                continue
            if MODEL_WORDS.search((r / f).read_text(encoding="utf-8", errors="ignore")):
                print(f"REVIEW  {name}: {f} mentions a model; classify it in KNOWN_MODEL or NOT_A_CALL")
                stale = True
        missing = [k for k in known if not any(f == k or f.endswith("/" + k) for _, f in files)]
        for k in missing:
            print(f"REVIEW  {name}: known model module {k} not found (moved or deleted?)")
            stale = True

    print(f"\n{'System':<18} {'modules':>8} {'call LM':>8} {'share of lines':>15}   page says")
    for name, m, lm, n_l, lm_l in rows:
        page = PAGE[name]
        flag = "" if (m, lm) == page else f"   CHANGED (page: {page[1]} of {page[0]})"
        stale |= bool(flag)
        print(f"{name:<18} {m:>8} {lm:>8} {100 * lm_l / max(n_l, 1):>14.1f}%   {page[1]} of {page[0]}{flag}")
    flag = "" if (tot_m, tot_lm) == PAGE_TOTAL else "   CHANGED"
    stale |= bool(flag)
    print(f"{'All six':<18} {tot_m:>8} {tot_lm:>8} {100 * tot_lml / max(tot_l, 1):>14.1f}%   "
          f"{PAGE_TOTAL[1]} of {PAGE_TOTAL[0]}{flag}")
    print("\nPage figures still match." if not stale else
          "\nUpdate the page (and PAGE above), or classify the REVIEW lines, before republishing.")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
