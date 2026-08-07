"""Weekly orchestrator.

Usage: python run_week.py [YYYY-Www]   (defaults to the current ISO week)

Pipeline: research agents (Claude Code, write into runs/<week>/) -> ingest ->
themes -> beneficiaries -> report -> handoff.

The agent stage is launched via Claude Code (agents/*.md briefs); the rest is
deterministic Python. Scheduling (build step 3) will wrap this script.
"""

import sys
from datetime import date

from engine import ingest, themes, beneficiaries, report, handoff, deliver


def current_week() -> str:
    y, w, _ = date.today().isocalendar()
    return f"{y}-W{w:02d}"


def main(week: str, do_deliver: bool = False, do_push: bool = False,
         do_sweep: bool = False) -> None:
    # Agent research stage runs before this script (or will be invoked here later).
    print(f"== Capital Flow pipeline: {week} ==")
    if do_sweep:  # network call — opt-in so offline runs stay deterministic
        from engine import edgar
        sw = edgar.sweep(week)
        print(f"[edgar]   {sw['entities']} entities swept, {sw['leads_new']} new leads, "
              f"{sw['errors']} errors")
    s = ingest.ingest_week(week)
    print(f"[ingest]  +{s['inserted']} new, {s['updated']} updated, "
          f"{s['skipped']} skipped, {s['warnings']} warnings")
    for p in s["problems"]:
        print("          ", p)
    b = beneficiaries.run(week)
    print(f"[benefic] {b['linked']} linked, {b['unmatched']} unmatched")
    t = themes.run(week)  # after beneficiaries so beneficiary_concentration can see them
    print(f"[themes]  {len(t['fired'])} fired: {'; '.join(t['fired']) or '—'}")
    rp = report.run(week)
    print(f"[report]  {rp}")
    h = handoff.run(week)
    print(f"[handoff] {h['nodes']} nodes, {h['flows']} flows -> handoff/capital_map.json")
    if do_deliver or do_push:
        d = deliver.run(week, push=do_push)
        print(f"[deliver] {d}")


if __name__ == "__main__":
    # Usage: python run_week.py [week] [--deliver] [--push]
    # --deliver copies capitalMap.json into ab-investment; --push also commits + pushes to main.
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    week = args[0] if args else current_week()
    main(week, do_deliver="--deliver" in sys.argv, do_push="--push" in sys.argv,
         do_sweep="--sweep" in sys.argv)
