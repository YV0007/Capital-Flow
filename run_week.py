"""Weekly orchestrator.

Usage: python run_week.py [YYYY-Www]   (defaults to the current ISO week)

Pipeline: research agents (Claude Code, write into runs/<week>/) -> ingest ->
themes -> beneficiaries -> report -> handoff.

The agent stage is launched via Claude Code (agents/*.md briefs); the rest is
deterministic Python. Scheduling (build step 3) will wrap this script.
"""

import sys
from datetime import date

from engine import ingest, themes, beneficiaries, report, handoff


def current_week() -> str:
    y, w, _ = date.today().isocalendar()
    return f"{y}-W{w:02d}"


def main(week: str) -> None:
    # Agent research stage runs before this script (or will be invoked here later).
    ingest.ingest_week(week)
    themes.run(week)
    beneficiaries.run(week)
    report.run(week)
    handoff.run(week)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else current_week())
