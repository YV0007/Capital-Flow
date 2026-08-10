"""Generate target-profiler batch inputs for targets missing a reference.

Usage: python tools/make_reference_batches.py <week> [batch_size]

Queries events for targets with no row in target_references and writes
runs/<week>/references/batch-N/batch_targets.json inputs (contract in
agents/target-profiler.md). Run this each cycle after ingest; if it reports
0 targets, every entity on the map already has its "what this is" card and
no profiler agents need launching. Idempotent: re-running regenerates inputs
only for still-missing targets (batch dirs are numbered fresh each time).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db  # noqa: E402


def main(week: str, batch_size: int = 18) -> int:
    con = db.connect()
    rows = con.execute("""
        SELECT e.target, MIN(e.target_type) tt, MIN(e.sector) sector,
               GROUP_CONCAT(DISTINCT a.name) allocators,
               MAX(e.disclosed_date) last_date, SUM(COALESCE(e.amount_usd,0)) capital,
               GROUP_CONCAT(DISTINCT COALESCE(e.source_url,'')) urls
        FROM events e JOIN allocators a ON a.id = e.allocator_id
        WHERE NOT EXISTS (SELECT 1 FROM target_references t WHERE t.target = e.target)
        GROUP BY e.target ORDER BY capital DESC""").fetchall()
    con.close()
    targets = [{
        "target": r["target"], "target_type": r["tt"], "sector": r["sector"],
        "allocators": (r["allocators"] or "").split(",")[:4],
        "last_event": r["last_date"], "capital_usd": r["capital"],
        "deal_source_urls": [u for u in (r["urls"] or "").split(",") if u][:3],
    } for r in rows]
    if not targets:
        print("0 targets missing references — nothing to research")
        return 0
    n_batches = (len(targets) + batch_size - 1) // batch_size
    for i in range(n_batches):
        b = targets[i::n_batches]
        d = db.RUNS_DIR / week / "references" / f"batch-{i + 1}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "batch_targets.json").write_text(json.dumps(b, indent=2))
        print(f"batch-{i + 1}: {len(b)} targets -> {d / 'batch_targets.json'}")
    print(f"{len(targets)} targets across {n_batches} batches — launch one "
          f"target-profiler agent per batch (agents/target-profiler.md)")
    return len(targets)


if __name__ == "__main__":
    wk = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 18
    main(wk, size)
