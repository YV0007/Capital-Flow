"""Monthly orchestrator — the ECOSYSTEM map.

Usage: python run_month.py [YYYY-MM] [--skip-agents] [--deliver] [--offline] [--verify-limit N]

Pipeline (mirrors run_week.py's split of responsibilities):

    6 research agents (Claude Code, write CSVs into runs/<month>/eco-*/)
      -> eco_ingest   validate, resolve names, dedupe, load
      -> eco_verify   re-fetch every citation, expire what died
      -> eco_score    criticality, gravity, layer concentration
      -> eco_cycles   closed loops, sales vs financing
      -> eco_handoff  handoff/ecosystem_map.json + ECOSYSTEM-CHANGELOG.md

The agent stage is the only non-deterministic layer, and it runs BEFORE this script
(see RUNBOOK.md). Everything this script does is Python + SQL over what the agents wrote,
so the same CSVs always produce the same map.
"""

import shutil
import sys
from pathlib import Path

from engine import eco, eco_cycles, eco_handoff, eco_ingest, eco_score, eco_verify

# Where --deliver drops the map for the dashboard repo. Read-only territory otherwise:
# this engine never writes anything else into ab-investment.
DASHBOARD_DATA = Path.home() / "Desktop/BASE/Code/ab-investment/src/data/ecosystemMap.json"

AGENTS = ["eco-silicon", "eco-systems", "eco-power", "eco-infra", "eco-models",
          "eco-capital"]


def check_agent_outputs(month: str) -> list:
    """Report which agent directories are missing or empty. Not fatal — a month where
    only two layers were refreshed is a legitimate run."""
    base = Path("runs") / month
    missing = []
    for a in AGENTS:
        d = base / a
        if not d.is_dir() or not (d / "edges.csv").exists():
            missing.append(a)
    return missing


def main(month: str, do_deliver: bool = False, offline: bool = False,
         verify_limit: int = None) -> None:
    print(f"== Capital Flow ECOSYSTEM pipeline: {month} ==")

    missing = check_agent_outputs(month)
    if missing:
        print(f"[agents]  no output from: {', '.join(missing)}")

    s = eco_ingest.ingest_month(month)
    print(f"[ingest]  {s['nodes']} nodes ({s['nodes_new']} new), {s['edges']} edges "
          f"({s['edges_new']} new), {s['evidence']} evidence rows, "
          f"{s['rejected']} rejected")
    for p in s["problems"][:25]:
        print("          ", p)
    if s["rejects_path"]:
        print(f"          rejects -> {s['rejects_path']} (next run hands these back)")

    v = eco_verify.run(month, offline=offline, limit=verify_limit)
    if offline:
        print(f"[verify]  SKIPPED (offline) — {v['skipped']} citations unchecked")
    else:
        print(f"[verify]  {v['checked']} citations checked: {v['alive']} alive, "
              f"{v['dead']} dead, {v['blocked']} blocked/paywalled")
    print(f"          {v['unverified_edges']} edges unverified, "
          f"{v['expired_edges']} expired, {v['stale_nodes']} stale nodes")

    sc = eco_score.run(month)
    print(f"[score]   {sc['nodes']} nodes scored, {sc['layers_scored']}/12 layers "
          f"populated; top: " +
          ", ".join(f"{k}={c}" for k, c in sc["top"]))

    cy = eco_cycles.run(month)
    print(f"[cycles]  {cy['cycles']} found ({cy['sales']} sales, "
          f"{cy['financing']} financing)")
    for c in cy["detail"][:5]:
        print(f"           {c['slug']} {c['type']}: {' -> '.join(c['path'])}")

    h = eco_handoff.run(month)
    print(f"[handoff] {h['nodes']} nodes, {h['edges']} edges, {h['cycles']} cycles "
          f"-> {h['path']}")
    print(f"          changelog: +{h['added']} / -{h['removed']} / ~{h['changed']}")

    if do_deliver:
        if not DASHBOARD_DATA.parent.is_dir():
            print(f"[deliver] SKIPPED — {DASHBOARD_DATA.parent} not found")
        else:
            shutil.copy(eco_handoff.OUT_JSON, DASHBOARD_DATA)
            print(f"[deliver] -> {DASHBOARD_DATA}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    month = args[0] if args else eco.current_month()
    for a in sys.argv[1:]:
        if a.startswith("--month="):
            month = a.split("=", 1)[1]
    limit = None
    for a in sys.argv[1:]:
        if a.startswith("--verify-limit="):
            limit = int(a.split("=", 1)[1])
    # --skip-agents is accepted for symmetry with run_week.py: the agent stage already
    # runs outside this script, so the flag documents intent rather than changing it.
    main(month, do_deliver="--deliver" in sys.argv, offline="--offline" in sys.argv,
         verify_limit=limit)
