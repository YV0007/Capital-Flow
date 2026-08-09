"""Weekly orchestrator.

Usage: python run_week.py [YYYY-Www]   (defaults to the current ISO week)

Pipeline: research agents (Claude Code, write into runs/<week>/) -> ingest ->
themes -> beneficiaries -> report -> handoff.

The agent stage is launched via Claude Code (agents/*.md briefs); the rest is
deterministic Python. Scheduling (build step 3) will wrap this script.
"""

import sys
from datetime import date

from engine import (audit, beneficiaries, deliver, handoff, ingest, profiles,
                    report, themes)


def current_week() -> str:
    y, w, _ = date.today().isocalendar()
    return f"{y}-W{w:02d}"


def main(week: str, do_deliver: bool = False, do_push: bool = False,
         do_sweep: bool = False, do_logos: bool = True) -> None:
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
    p = profiles.ingest_week(week)  # allocator intelligence (§5), when batches exist
    print(f"[profile] {p['profiles']} profiles, {p['track_rows']} track-record rows, "
          f"{p['skipped']} skipped")
    for w in p.get("warnings", []):
        print("          WARN", w)
    t = themes.run(week)  # after beneficiaries so beneficiary_concentration can see them
    print(f"[themes]  {len(t['fired'])} fired: {'; '.join(t['fired']) or '—'}")
    rp = report.run(week)
    print(f"[report]  {rp}")
    v = audit.run(week)  # §6: periodic verification pass, gates delivery
    print(f"[audit]   {'PASS' if v['passed'] else 'FAIL'} — {len(v['errors'])} errors, "
          f"{len(v['warnings'])} warnings -> runs/{week}/audit_report.md")
    for e in v["errors"]:
        print("          ERR", e)
    h = handoff.run(week, audit_verdict=v)
    print(f"[handoff] {h['nodes']} nodes, {h['flows']} flows -> handoff/capital_map.json")
    if (do_deliver or do_push) and not v["passed"]:
        print("[deliver] BLOCKED: audit failed — fix errors and re-run")
        sys.exit(1)
    if do_deliver or do_push:
        # deliver also refreshes dashboard logos for this cycle's new entities
        # (network call, best-effort — see engine/deliver.py).
        d = deliver.run(week, push=do_push, refresh_logos_first=do_logos)
        print(f"[deliver] {d}")


if __name__ == "__main__":
    # Usage: python run_week.py [week] [--deliver] [--push] [--sweep] [--no-logos]
    # --deliver copies capitalMap.json into ab-investment; --push also commits + pushes to main.
    # --no-logos skips the dashboard logo refresh (offline / data-only runs).
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    week = args[0] if args else current_week()
    main(week, do_deliver="--deliver" in sys.argv, do_push="--push" in sys.argv,
         do_sweep="--sweep" in sys.argv, do_logos="--no-logos" not in sys.argv)
