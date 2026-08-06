"""Beneficiary engine: map private capital flows to public-market beneficiaries.

The mapping itself (which public names benefit from a private flow) is reasoning
work done by an agent, which drops runs/<week>/beneficiaries.csv. This module is
the deterministic loader: it validates that CSV and stores rows against the
matching event, so the DB stays the single source of truth.

beneficiaries.csv columns:
  allocator, target, event_type, disclosed_date,   -- identifies the source event
  ticker, company, rationale, confidence            -- the beneficiary

If no beneficiaries.csv exists for the week, this is a no-op.
"""

import csv

from . import db

CONFIDENCE = {"low", "medium", "high"}


def run(week: str) -> dict:
    con = db.connect()
    path = db.RUNS_DIR / week / "beneficiaries.csv"
    stats = {"linked": 0, "unmatched": 0}
    if not path.exists():
        con.close()
        return stats

    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            ev = con.execute(
                """SELECT e.id FROM events e JOIN allocators a ON a.id = e.allocator_id
                   WHERE a.name=? AND e.target=? AND e.event_type=? AND e.disclosed_date=?""",
                ((row.get("allocator") or "").strip(), (row.get("target") or "").strip(),
                 (row.get("event_type") or "").strip(), (row.get("disclosed_date") or "").strip()),
            ).fetchone()
            if not ev:
                stats["unmatched"] += 1
                continue
            conf = (row.get("confidence") or "medium").strip()
            con.execute(
                """INSERT INTO beneficiaries (event_id, ticker, company, rationale, confidence)
                   VALUES (?,?,?,?,?)""",
                (ev["id"], (row.get("ticker") or "").strip().upper(),
                 (row.get("company") or "").strip(), (row.get("rationale") or "").strip(),
                 conf if conf in CONFIDENCE else "medium"))
            stats["linked"] += 1
    con.commit()
    con.close()
    return stats


if __name__ == "__main__":
    import sys
    print(run(sys.argv[1]))
