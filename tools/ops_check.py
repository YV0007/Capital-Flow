"""OPERATIONS.md drift check — does the doc still describe reality?

Usage: python tools/ops_check.py [--json]

OPERATIONS.md is updated WEEKLY, not per-change. That cadence is only safe if the
weekly pass corrects what is actually wrong instead of recalling what changed, so
this script does the recalling. It reads the real payload headers, the real audit
warnings and both repos' commit logs, and prints what no longer matches the doc.

It NEVER writes. Judgement sections (the fact ladder, goals, mandates, rules) are
for a person to change; this only reports on the machine-checkable ones.

Exit code 1 when drift is found, so a scheduled run can flag itself.
"""

import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASH = Path("/Users/macbook/Desktop/BASE/Code/ab-investment")
OPS = ROOT / "OPERATIONS.md"

# Payloads the doc makes claims about: dashboard file -> what §6 says about it.
PAYLOADS = {
    "capitalMap.json": {"contract": None, "cadence": "Weekly"},
    "aiEcosystemNetwork.json": {"contract": "ai-ecosystem-network/2", "cadence": "Monthly"},
    "fundTracker.json": {"contract": "fund-tracker/1", "cadence": "Per filing"},
    "nvidiaEcosystem.json": {"contract": "nvidia-ecosystem/2", "cadence": "Frozen"},
}

# Commits touching these paths almost always change something §6-§9 documents.
WATCHED = [
    "config/", "agents/", "engine/", "tools/", "run_", "RUNBOOK.md", "ARCHITECTURE.md",
    "scripts/", "src/data/", ".claude/skills/",
]


def sh(args, cwd):
    try:
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except Exception:
        return ""


def last_changelog_date(text):
    """Newest date in the §12 changelog — the point the last pass reconciled to."""
    dates = re.findall(r"^- \*\*(\d{4}-\d{2}-\d{2})\*\*", text, re.M)
    return max(dates) if dates else None


def check_payloads(ops_text):
    """Contract, source and fixture flags in the doc vs the delivered files."""
    out = []
    for name, claim in PAYLOADS.items():
        f = DASH / "src/data" / name
        if not f.exists():
            out.append(f"{name}: documented in OPERATIONS.md but not present in src/data/")
            continue
        # Header only — these files run to 2 MB and must never be fully parsed
        # into a model's context (mandate 7). json.load is fine for a script.
        try:
            d = json.loads(f.read_text())
        except Exception as e:
            out.append(f"{name}: unreadable ({e})")
            continue
        got = d.get("schema")
        want = claim["contract"]
        if want and got != want:
            out.append(f"{name}: doc says contract {want!r}, file says {got!r}")
        if d.get("fixture") and "fixture" not in ops_text.lower():
            out.append(f"{name}: file has fixture:true but OPERATIONS.md does not warn about it")
        if not d.get("fixture") and f"`{name}` currently carries `fixture: true`" in ops_text:
            out.append(f"{name}: no longer a fixture — remove the warning from §6")
        gen = d.get("generated") or d.get("asOf")
        if gen:
            try:
                age = (date.today() - datetime.fromisoformat(str(gen)[:10]).date()).days
                limit = {"Weekly": 14, "Monthly": 45, "Per filing": 120}.get(claim["cadence"])
                if limit and age > limit:
                    out.append(f"{name}: generated {gen} ({age}d ago) — "
                               f"doc claims a {claim['cadence'].lower()} cadence")
            except ValueError:
                pass
    return out


def check_audit(ops_text):
    """The engine's own audit is the best source of truth for §10 Known gaps."""
    out = []
    f = DASH / "src/data/capitalMap.json"
    if not f.exists():
        return out
    try:
        audit = json.loads(f.read_text()).get("audit") or {}
    except Exception:
        return out
    warns = audit.get("warnings") or []
    by_code = {}
    for w in warns:
        code = w.split(":")[0].split()[0] if w else "?"
        by_code[code] = by_code.get(code, 0) + 1
    for code, n in sorted(by_code.items()):
        if code == "W7" and "36 of 43" not in ops_text and n:
            out.append(f"audit {code}: {n} warnings — §10 does not mention this gap")
    if not warns and "Warnings do not block" in ops_text:
        out.append("audit: zero warnings now — the 'warnings do not block' gap may be resolved")
    if audit.get("error_count"):
        out.append(f"audit: {audit['error_count']} ERRORS in the last delivery — "
                   f"the gate should have blocked it")
    return out


def check_commits(since):
    """Commits in either repo that touched something the doc describes."""
    out = []
    if not since:
        return ["OPERATIONS.md has no changelog entries — cannot scope the diff"]
    for label, repo in (("engine", ROOT), ("dashboard", DASH)):
        if not (repo / ".git").exists():
            continue
        log = sh(["git", "log", f"--since={since}", "--name-only",
                  "--pretty=format:%h%x09%ad%x09%s", "--date=short"], repo)
        if not log:
            continue
        commits, cur = [], None
        for line in log.split("\n"):
            if "\t" in line:
                cur = line.split("\t")
                commits.append((cur, []))
            elif line.strip() and commits:
                commits[-1][1].append(line.strip())
        for (meta, files) in commits:
            hit = [f for f in files if any(f.startswith(w) or w in f for w in WATCHED)]
            if hit:
                out.append(f"{label} {meta[0]} {meta[1]} — {meta[2][:70]}"
                           f"\n      touched: {', '.join(sorted(set(hit))[:4])}")
    return out


def main():
    as_json = "--json" in sys.argv
    if not OPS.exists():
        print("OPERATIONS.md not found", file=sys.stderr)
        return 2
    text = OPS.read_text()
    since = last_changelog_date(text)

    drift = check_payloads(text) + check_audit(text)
    commits = check_commits(since)

    if as_json:
        print(json.dumps({"since": since, "drift": drift, "commits_to_review": commits},
                         ensure_ascii=False, indent=2))
        return 1 if drift else 0

    print(f"OPERATIONS.md — last reconciled {since or 'never'}\n")
    if drift:
        print(f"DRIFT — {len(drift)} claim(s) no longer match reality:")
        for d in drift:
            print(f"  · {d}")
    else:
        print("No drift: every machine-checkable claim in §6/§9/§10 still holds.")
    if commits:
        print(f"\nCommits since {since} touching documented areas "
              f"({len(commits)}) — decide if any changed how we operate:")
        for c in commits[:40]:
            print(f"  · {c}")
        if len(commits) > 40:
            print(f"  … and {len(commits) - 40} more")
    else:
        print("\nNo commits since the last pass touched a documented area.")
    print("\nJudgement sections (§3 ladder, §5 goals, §7 mandates, §8 rules) are "
          "never auto-changed —\npropose a diff and ask.")
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
