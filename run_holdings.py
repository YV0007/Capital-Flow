"""MONTHLY orchestrator — fund portfolios, both books, no human in the loop.

Usage:
  python run_holdings.py                 # current month
  python run_holdings.py 2026-08         # a specific month
  python run_holdings.py --no-agents     # ingest whatever is already on disk
  python run_holdings.py --deliver       # build-gate and deploy to the dashboard

Why this file exists. Everything needed to fill a fund's portfolio already worked:
`tools/make_holdings_batches.py` wrote correct inputs, `engine/holdings.py`
ingested correct results. Between them sat a line in RUNBOOK.md addressed to a
person — *launch one holdings-profiler agent per batch*. In W33 four batches were
written and no agent ran; in W34, three of four. Those three batches are the entire
origin of every portfolio on the site, and the reason thirty-six funds render
empty. A step that depends on someone remembering is not a pipeline.

Monthly, not weekly: a venture book does not move enough in seven days to justify
re-researching forty-odd funds, and the weekly run is already the busiest thing
here. Not quarterly either — too slow for the private book, and wrong for 13F too
(see engine/public_book.py). Schedule it on the 20th or later, so a run also picks
up the quarter's 13Fs, which land ~45 days after quarter end.

    make_holdings_batches   every fund missing a portfolio OR below the 25 floor
      -> holdings_agents    one agent per batch, in parallel — THE step that never ran
      -> reconcile          inputs written vs results found. Inputs with no result
                            is not a quiet month, it is a step that did not run,
                            and it FAILS the run instead of shipping green.
      -> holdings.ingest    unchanged
      -> public_book        13F for the allocators that file one; a cheap no-op in
                            the two months out of three with nothing new
      -> audit -> handoff -> build-gate -> deploy
"""

import subprocess
import sys
from datetime import date

from engine import (audit, db, deliver, handoff, holdings, holdings_agents,
                    public_book)
from tools import make_holdings_batches as batches


def current_month() -> str:
    return date.today().strftime("%Y-%m")


def current_week() -> str:
    y, w, _ = date.today().isocalendar()
    return f"{y}-W{w:02d}"


def main(period: str, run_agents: bool = True, do_deliver: bool = False,
         do_push: bool = False, batch_size: int = 8) -> int:
    print(f"== Fund portfolios: {period} ==")
    con = db.connect()
    failures = []

    # ── 1. what still needs work ────────────────────────────────────────────
    ents = batches.select_entities(con)
    if ents:
        n = batches.main(period, batch_size)
        for i, e in enumerate(ents):
            e["batch"] = f"batch-{i // batch_size + 1}"
        holdings.record_requests(con, period, ents)
        thin = sum(1 for e in ents if e["reason"] == "thin")
        print(f"[batches] {len(ents)} entities queued ({len(ents) - thin} with no "
              f"portfolio, {thin} below the {batches.MIN_HOLDINGS}-holding floor)")
    else:
        print("[batches] 0 funds/firms missing holdings — nothing to research")

    # ── 2. the step that never ran ──────────────────────────────────────────
    pending = holdings_agents.pending_batches(period)
    if run_agents and pending:
        launcher = holdings_agents.resolve()
        if not launcher:
            # Loud, and it fails the run. A missing launcher used to look exactly
            # like a quiet month; that is the whole bug being fixed here.
            print("[agents]  CANNOT RUN — no launcher available")
            for line in holdings_agents.remediation().splitlines():
                print("          " + line)
            failures.append("collection step could not run: no agent launcher")
        else:
            print(f"[agents]  launching {len(pending)} agents via {launcher['kind']} …")
            r = holdings_agents.launch(pending, period,
                                       minimum=batches.MIN_HOLDINGS,
                                       launcher=launcher)
            print(f"[agents]  {r['ok']}/{r['launched']} produced holdings.json")
            for f in r["failed"]:
                print("          FAILED", f)
            if r["timed_out"]:
                print("          TIMED OUT", ", ".join(r["timed_out"]))
            if r["failed"] or r["timed_out"]:
                failures.append(f"{len(r['failed']) + len(r['timed_out'])} of "
                                f"{r['launched']} collection agents did not deliver")
    elif pending:
        print(f"[agents]  SKIPPED by --no-agents ({len(pending)} batches pending)")
        failures.append(f"--no-agents: {len(pending)} batches left uncollected")

    # ── 3. ingest + reconcile ───────────────────────────────────────────────
    h = holdings.ingest_week(period)
    print(f"[ingest]  {h['entities']} portfolios, {h['holdings']} holdings, "
          f"{h['skipped']} skipped")
    for w in h.get("warnings", [])[:10]:
        print("          WARN", w)
    if h["batches_requested"]:
        print(f"[reconc]  {h['batches_delivered']}/{h['batches_requested']} batches "
              f"delivered a result")
        if h["batches_missing"]:
            # Reported separately from "0 new holdings" on purpose: they are
            # different facts and only one of them is a bug.
            print(f"          NO RESULT: {', '.join(h['batches_missing'])} — inputs "
                  f"were written and nothing came back")
            failures.append(f"{len(h['batches_missing'])} batches produced no result")
    if h["shortfalls"]:
        print(f"[depth]   {len(h['shortfalls'])} portfolios under the "
              f"{holdings.MIN_HOLDINGS}-holding floor — re-queued for next run")
        for s in h["shortfalls"][:6]:
            print(f"          {s['entity']}: {s['delivered']} of {s['true_total']}")

    # ── 4. the public book ──────────────────────────────────────────────────
    pb = public_book.refresh(con)
    print(f"[13f]     {len(pb['updated'])} books refreshed, {pb['noop']} already "
          f"current, {len(public_book.non_filers())} allocators file no 13F")
    for u in pb["updated"][:10]:
        print("          ", u)
    for e in pb["errors"]:
        print("          ERR", e)

    # ── 5. audit ────────────────────────────────────────────────────────────
    week = current_week()
    v = audit.run(week)
    print(f"[audit]   {'PASS' if v['passed'] else 'FAIL'} — {len(v['errors'])} "
          f"errors, {len(v['warnings'])} warnings")
    for e in v["errors"][:10]:
        print("          ERR", e)
    w7 = [w for w in v["warnings"] if w.startswith("W7")]
    w9 = [w for w in v["warnings"] if w.startswith("W9")]
    print(f"[gaps]    {len(w7)} funds with no portfolio, {len(w9)} below the floor")

    # ── 6. payload ──────────────────────────────────────────────────────────
    hd = handoff.run(week, audit_verdict=v)
    print(f"[handoff] {hd['nodes']} nodes, {hd['flows']} flows -> handoff/capital_map.json")

    if failures:
        print("\n[FAILED]  this run did NOT do its job:")
        for f in failures:
            print("          -", f)
        print("          Not deploying. A partial collection run that ships green "
              "is the bug this pipeline was rebuilt to remove.")
        con.close()
        return 1

    if do_deliver or do_push:
        if not v["passed"]:
            print("[deliver] BLOCKED: audit failed")
            con.close()
            return 1
        if do_push:
            # Reuse run.sh's build gate: if the dashboard does not compile, the
            # deploy does not happen.
            ab = deliver.AB_PATH if hasattr(deliver, "AB_PATH") else None
            if ab:
                print(f"[build]   checking {ab} …")
                rc = subprocess.run(["npm", "run", "build"], cwd=str(ab),
                                    capture_output=True).returncode
                if rc != 0:
                    print("[build]   FAILED — not deploying")
                    con.close()
                    return 1
                print("[build]   OK")
        print("[deliver]", deliver.run(week, push=do_push))
    con.close()
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(
        args[0] if args else current_month(),
        run_agents="--no-agents" not in sys.argv,
        do_deliver="--deliver" in sys.argv or "--push" in sys.argv,
        do_push="--push" in sys.argv,
        batch_size=int(args[1]) if len(args) > 1 else 8))
