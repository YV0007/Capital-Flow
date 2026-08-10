"""Generate holdings-profiler batch inputs for funds/firms lacking a portfolio.

Usage: python tools/make_holdings_batches.py <week> [batch_size]

Selects fund/firm entities (VC & alt-manager allocators, plus fund-vehicle
targets) that don't yet have collected holdings, and writes
runs/<week>/holdings/batch-N/batch_entities.json inputs (contract in
agents/holdings-profiler.md). Run after ingest; if it reports 0, every fund on
the map already has its portfolio. Idempotent — regenerates only still-missing
entities.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db  # noqa: E402


def main(week: str, batch_size: int = 12) -> int:
    con = db.connect()
    rows = con.execute("""
        SELECT label, kind, cls, allocators, cap, urls FROM (
          SELECT a.name AS label, 'firm' AS kind, a.class AS cls,
                 NULL AS allocators, SUM(COALESCE(e.amount_usd,0)) cap,
                 GROUP_CONCAT(DISTINCT COALESCE(e.source_url,'')) urls
          FROM events e JOIN allocators a ON a.id = e.allocator_id
          WHERE a.class IN ('vc','alt_manager')
          GROUP BY a.id
          UNION ALL
          SELECT e.target AS label, 'vehicle' AS kind, 'fund' AS cls,
                 GROUP_CONCAT(DISTINCT a.name) allocators,
                 SUM(COALESCE(e.amount_usd,0)) cap,
                 GROUP_CONCAT(DISTINCT COALESCE(e.source_url,'')) urls
          FROM events e JOIN allocators a ON a.id = e.allocator_id
          WHERE e.target_type = 'fund'
          GROUP BY e.target)
        WHERE label NOT IN (SELECT entity FROM portfolios WHERE holdings_count > 0)
        ORDER BY cap DESC""").fetchall()
    con.close()
    ents = [{
        "entity": r["label"], "kind": r["kind"], "class": r["cls"],
        "parent_hint": [x for x in (r["allocators"] or "").split(",") if x][:2],
        "capital_usd": r["cap"],
        "deal_source_urls": [u for u in (r["urls"] or "").split(",") if u][:3],
    } for r in rows]
    if not ents:
        print("0 funds/firms missing holdings — nothing to research")
        return 0
    n = (len(ents) + batch_size - 1) // batch_size
    for i in range(n):
        b = ents[i::n]
        d = db.RUNS_DIR / week / "holdings" / f"batch-{i + 1}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "batch_entities.json").write_text(json.dumps(b, indent=2))
        print(f"batch-{i + 1}: {len(b)} entities -> {d / 'batch_entities.json'}")
    print(f"{len(ents)} funds/firms across {n} batches — launch one "
          f"holdings-profiler agent per batch (agents/holdings-profiler.md)")
    return len(ents)


if __name__ == "__main__":
    wk = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    main(wk, size)
