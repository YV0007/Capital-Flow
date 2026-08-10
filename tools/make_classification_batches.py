"""Generate deal-classifier batch inputs for INVESTABLE targets lacking a tag.

Usage: python tools/make_classification_batches.py <week> [batch_size]

Mirrors the dashboard's investable gate (classification.js): excludes
project/asset targets and the datacenters/power-energy/nuclear/neocloud sectors.
Selects investable targets that don't yet have an ai_posture, and writes
runs/<week>/classification/batch-N/batch_targets.json with the round context
(allocators, co_investors, amounts, dates, deal URLs) the agent needs.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db  # noqa: E402

EXCLUDED_SECTORS = ("datacenters", "power-energy", "nuclear", "neocloud")
EXCLUDED_TARGET_TYPES = ("project", "asset")


def main(week: str, batch_size: int = 12) -> int:
    con = db.connect()
    ph_sec = ",".join("?" * len(EXCLUDED_SECTORS))
    ph_tt = ",".join("?" * len(EXCLUDED_TARGET_TYPES))
    rows = con.execute(f"""
        SELECT e.target, MIN(e.target_type) tt, MIN(e.sector) sector,
               GROUP_CONCAT(DISTINCT a.name) allocators,
               GROUP_CONCAT(DISTINCT e.co_investors) co_investors,
               GROUP_CONCAT(DISTINCT e.disclosed_date) dates,
               SUM(COALESCE(e.amount_usd,0)) capital,
               MAX(COALESCE(e.valuation_usd,0)) valuation,
               GROUP_CONCAT(DISTINCT COALESCE(e.source_url,'')) urls
        FROM events e JOIN allocators a ON a.id = e.allocator_id
        WHERE (e.target_type IS NULL OR e.target_type NOT IN ({ph_tt}))
          AND e.sector NOT IN ({ph_sec})
          AND e.event_type NOT IN ('project_finance','grant','fund_launch')
          AND NOT EXISTS (SELECT 1 FROM target_classification t
                          WHERE t.target = e.target AND t.ai_class IS NOT NULL)
        GROUP BY e.target ORDER BY capital DESC""",
        (*EXCLUDED_TARGET_TYPES, *EXCLUDED_SECTORS)).fetchall()
    con.close()
    targets = [{
        "target": r["target"], "target_type": r["tt"], "sector": r["sector"],
        "allocators": [x for x in (r["allocators"] or "").split(",") if x][:6],
        "co_investors": [x for x in (r["co_investors"] or "").split(",") if x][:8],
        "disclosed_dates": [x for x in (r["dates"] or "").split(",") if x],
        "capital_usd": r["capital"], "valuation_usd": r["valuation"] or None,
        "deal_source_urls": [u for u in (r["urls"] or "").split(",") if u][:4],
    } for r in rows]
    if not targets:
        print("0 investable targets missing classification — nothing to research")
        return 0
    n = (len(targets) + batch_size - 1) // batch_size
    for i in range(n):
        b = targets[i::n]
        d = db.RUNS_DIR / week / "classification" / f"batch-{i + 1}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "batch_targets.json").write_text(json.dumps(b, indent=2))
        print(f"batch-{i + 1}: {len(b)} targets -> {d / 'batch_targets.json'}")
    print(f"{len(targets)} investable targets across {n} batches — launch one "
          f"deal-classifier agent per batch (agents/deal-classifier.md)")
    return len(targets)


if __name__ == "__main__":
    wk = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    main(wk, size)
