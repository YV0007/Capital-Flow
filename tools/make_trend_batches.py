"""Generate trend-writer batch inputs for clusters that cleared Stage B.

Usage: python tools/make_trend_batches.py <week> [batch_size]

Runs the Stage-B windowed clustering (engine/trends.compute), takes the union of
clusters that appear in ANY window, and writes each with its real evidence (the
deals: allocator, target, amount, date, source) for the narrative agent. Only
clusters that cleared the bar (confidence != low) and don't already have a
narrative are emitted. If 0, every proven trend is already written.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db, trends  # noqa: E402


def main(week: str, batch_size: int = 10) -> int:
    con = db.connect()
    windows = trends.compute(con, week)
    have = {r["cluster_id"] for r in con.execute(
        "SELECT cluster_id FROM trend_narratives")}
    seen, clusters = set(), []
    for entries in windows.values():
        for e in entries:
            cid = e["cluster_id"]
            if cid in seen or cid in have or e["confidence"] == "low":
                continue
            seen.add(cid)
            ev = con.execute(
                """SELECT a.name AS allocator, e.target, e.amount_usd, e.disclosed_date,
                          e.source_url
                   FROM events e JOIN allocators a ON a.id = e.allocator_id
                   WHERE e.id IN ({}) ORDER BY e.disclosed_date""".format(
                    ",".join(str(i) for i in e["evidence"]))).fetchall()
            clusters.append({
                "cluster_id": cid, "sector": e["sector"], "subsector": e["subsector"],
                "deals": [{"allocator": r["allocator"], "target": r["target"],
                           "amount_usd": r["amount_usd"], "date": r["disclosed_date"],
                           "source_url": r["source_url"]} for r in ev]})
    con.close()
    if not clusters:
        print("0 proven clusters need a narrative — nothing to research")
        return 0
    n = (len(clusters) + batch_size - 1) // batch_size
    for i in range(n):
        b = clusters[i::n]
        d = db.RUNS_DIR / week / "trends" / f"batch-{i + 1}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "batch_clusters.json").write_text(json.dumps(b, indent=2))
        print(f"batch-{i + 1}: {len(b)} clusters -> {d / 'batch_clusters.json'}")
    print(f"{len(clusters)} clusters across {n} batches — launch one trend-writer "
          f"agent per batch (agents/trend-writer.md)")
    return len(clusters)


if __name__ == "__main__":
    wk = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    main(wk, size)
