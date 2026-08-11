"""Build trend-writer batch inputs: the clusters that cleared Stage B's bar.

Stage B (engine/trends.py) finds real (sector, subsector) convergence. This writes
each qualifying cluster — with its FULL evidence rows (allocator, target, amount,
date, source) — to runs/<week>/trends/batch-N/batch_clusters.json so a trend-writer
agent can write a grounded narrative WITHOUT inventing anything.

Only clusters that cleared the bar in at least one window are emitted: the narrative
agent never writes about a single deal or a vibe.

Usage: python tools/make_trend_batches.py <week> [per_batch]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db, trends  # noqa: E402

PER_BATCH = 6


def run(week: str, per_batch: int = PER_BATCH) -> dict:
    con = db.connect()
    computed = trends.compute(con, week)

    # A cluster is worth writing about if it cleared the bar in ANY window.
    qualified = {}
    for wkey, entries in computed.items():
        for e in entries:
            if e["confidence"] == "low":
                continue  # borderline: surfaced in the payload, but not narrated
            q = qualified.setdefault(e["cluster_id"], {**e, "windows": []})
            q["windows"].append(wkey)

    out = []
    for cid, c in qualified.items():
        ids = c["evidence"]
        ph = ",".join("?" * len(ids))
        rows = con.execute(
            f"""SELECT a.name AS allocator, e.target, e.amount_usd, e.disclosed_date,
                       e.event_type, e.stage, e.capital_role, e.co_investors,
                       e.status, e.source_url, e.notes
                FROM events e JOIN allocators a ON a.id = e.allocator_id
                WHERE e.id IN ({ph}) ORDER BY e.disclosed_date""", ids).fetchall()
        out.append({
            "cluster_id": cid,
            "sector": c["sector"], "subsector": c["subsector"],
            "windows_qualified": c["windows"],
            "deals": c["deals"], "capital_usd": c["capital_usd"],
            "date_range": c["date_range"], "allocators": c["allocators"],
            "evidence": [dict(r) for r in rows],
        })
    con.close()

    tdir = db.RUNS_DIR / week / "trends"
    tdir.mkdir(parents=True, exist_ok=True)
    batches = 0
    for i in range(0, len(out), per_batch):
        batches += 1
        bdir = tdir / f"batch-{batches}"
        bdir.mkdir(exist_ok=True)
        (bdir / "batch_clusters.json").write_text(json.dumps(out[i:i + per_batch], indent=2))
    return {"clusters": len(out), "batches": batches, "dir": str(tdir)}


if __name__ == "__main__":
    wk = sys.argv[1] if len(sys.argv) > 1 else None
    if not wk:
        raise SystemExit("usage: python tools/make_trend_batches.py <week> [per_batch]")
    print(run(wk, int(sys.argv[2]) if len(sys.argv) > 2 else PER_BATCH))
