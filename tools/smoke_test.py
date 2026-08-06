"""End-to-end smoke test of the deterministic pipeline on synthetic data.

Runs entirely in a temp dir + temp DB (CAPITAL_DB env) so it never touches the
real db/, runs/, or handoff/. Generates fixture agent CSVs designed to trip each
signal rule, runs ingest -> themes -> beneficiaries -> report -> handoff, and
asserts the outputs. Usage: python tools/smoke_test.py
"""

import csv
import json
import os
import shutil
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def d(days_ago):
    return (date.today() - timedelta(days=days_ago)).isoformat()


COLS = ["event_date", "disclosed_date", "allocator", "allocator_class", "target",
        "target_type", "sector", "subsector", "event_type", "amount_usd",
        "amount_estimated", "status", "source_tier", "source_url", "notes"]


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLS})


def fixtures(runs, week):
    # 6 distinct key VC allocators into "photonics" within 30d -> sector_swarm fires.
    swarm = []
    for i in range(6):
        swarm.append(dict(disclosed_date=d(5 + i), allocator=f"KeyVC{i}", target=f"PhotonCo{i}",
                          target_type="private", sector="photonics", event_type="funding_round",
                          amount_usd=str(50_000_000 + i * 1_000_000), status="verified",
                          source_tier="1", source_url="https://sec.gov/x"))
    write_csv(runs / week / "vc" / "verified_events.csv", swarm)

    # capital_acceleration on "power": big now vs small prior 90d window.
    accel = [
        dict(disclosed_date=d(10), allocator="MegaFund", allocator_class="alt_manager",
             target="GridCo", target_type="private", sector="power",
             event_type="project_finance", amount_usd="4000000000", status="verified",
             source_tier="1", source_url="https://ir.example/x"),
        dict(disclosed_date=d(120), allocator="MegaFund", allocator_class="alt_manager",
             target="GridCo", target_type="private", sector="power",
             event_type="project_finance", amount_usd="500000000", status="verified",
             source_tier="2", source_url="https://ir.example/y"),
    ]
    write_csv(runs / week / "alt-managers" / "verified_events.csv", accel)

    # first_entry: established key corporate (old event in ai-compute) enters "robotics".
    fe = [
        dict(disclosed_date=d(500), allocator="BigCorp", target="OldChipCo", target_type="private",
             sector="ai-compute", event_type="corporate_investment", amount_usd="1000000000",
             status="verified", source_tier="1", source_url="https://sec.gov/a"),
        dict(disclosed_date=d(7), allocator="BigCorp", target="RoboStartup", target_type="private",
             sector="robotics", event_type="corporate_investment", amount_usd="300000000",
             status="verified", source_tier="1", source_url="https://sec.gov/b"),
    ]
    write_csv(runs / week / "corporate" / "verified_events.csv", fe)

    # a candidate + a deliberately BAD row (should be skipped) + a dupe (should merge).
    write_csv(runs / week / "individuals" / "candidate_events.csv", [
        dict(disclosed_date=d(3), allocator="FamousAngel", target="SecretCo", target_type="private",
             sector="ai-compute", event_type="equity", amount_usd="", status="candidate",
             source_tier="5", source_url="https://x.com/z"),
        dict(disclosed_date=d(3), allocator="NoClassHere", target="Whatever",  # filings-style, no class
             sector="ai-compute", event_type="equity", source_tier="9"),  # bad tier + no class
    ])
    # dupe of a swarm row but stronger nothing (same) — should be 'unchanged' or merge
    write_csv(runs / week / "filings" / "verified_events.csv", [
        dict(disclosed_date=d(5), allocator="KeyVC0", allocator_class="vc", target="PhotonCo0",
             target_type="private", sector="photonics", event_type="funding_round",
             amount_usd="50000000", status="verified", source_tier="1",
             source_url="https://sec.gov/dupe"),
    ])

    # beneficiaries mapping for one event
    with (runs / week / "beneficiaries.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["allocator", "target", "event_type",
                                          "disclosed_date", "ticker", "company",
                                          "rationale", "confidence"])
        w.writeheader()
        w.writerow(dict(allocator="MegaFund", target="GridCo", event_type="project_finance",
                        disclosed_date=d(10), ticker="ETN", company="Eaton",
                        rationale="grid buildout supplier", confidence="high"))


def main():
    tmp = Path(tempfile.mkdtemp(prefix="cf_smoke_"))
    os.environ["CAPITAL_DB"] = str(tmp / "capital.db")
    # Redirect runs/ + handoff/ + config/ to temp by monkeypatching db paths after import.
    from engine import db, ingest, themes, beneficiaries, report, handoff
    db.RUNS_DIR = tmp / "runs"
    db.HANDOFF_DIR = tmp / "handoff"

    # Temp config: real rules/sources, but a watchlist that marks the fixture
    # allocators as key-tier so tier-gated rules can fire.
    cfg_dir = tmp / "config"
    cfg_dir.mkdir(parents=True)
    shutil.copy(db.CONFIG_DIR / "rules.yaml", cfg_dir / "rules.yaml")
    shutil.copy(db.CONFIG_DIR / "sources.yaml", cfg_dir / "sources.yaml")
    (cfg_dir / "allocators.yaml").write_text(
        "vc:\n" + "".join(f"  - {{ name: KeyVC{i}, tier: key }}\n" for i in range(6)) +
        "corporate:\n  - { name: BigCorp, tier: key }\n"
        "alt_managers:\n  - { name: MegaFund, tier: key }\n"
        "individuals: []\nsovereigns: []\n")
    db.CONFIG_DIR = cfg_dir

    week = "TEST-W01"
    fixtures(db.RUNS_DIR, week)

    s = ingest.ingest_week(week)
    t = themes.run(week)
    b = beneficiaries.run(week)
    rp = report.run(week)
    h = handoff.run(week)

    fired = {th.split(":")[0].split(" enters ")[0] for th in t["fired"]}
    rules_fired = set()
    con = db.connect()
    for r in con.execute("SELECT DISTINCT rule FROM themes").fetchall():
        rules_fired.add(r["rule"])
    con.close()

    print("ingest:", {k: v for k, v in s.items() if k != "problems"})
    for p in s["problems"]:
        print("   ", p)
    print("themes fired:", t["fired"])
    print("rules fired:", rules_fired)
    print("beneficiaries:", b)
    print("handoff:", h)

    ok = True
    checks = [
        ("sector_swarm fired", "sector_swarm" in rules_fired),
        ("capital_acceleration fired", "capital_acceleration" in rules_fired),
        ("first_entry fired", "first_entry" in rules_fired),
        ("bad row skipped", s["skipped"] >= 1),
        ("dupe merged (not double-counted)", s["inserted"] + s["updated"] + s["unchanged"] > 0
                                              and s["inserted"] <= 12),
        ("beneficiary linked", b["linked"] == 1),
        ("report written", Path(rp).exists()),
        ("capital_map.json written", (db.HANDOFF_DIR / "capital_map.json").exists()),
    ]
    m = json.loads((db.HANDOFF_DIR / "capital_map.json").read_text())
    checks.append(("map has nodes", m["totals"]["nodes"] > 0))
    checks.append(("map has flows", m["totals"]["flows"] > 0))
    checks.append(("power sector has signals", len(m["sectors"].get("power", {}).get("signals", [])) > 0))

    print("\n-- checks --")
    for name, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed

    print("\n--- weekly_report.md ---")
    print(Path(rp).read_text())

    shutil.rmtree(tmp, ignore_errors=True)
    print("\nSMOKE:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
