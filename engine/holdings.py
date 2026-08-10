"""Holdings: fund/firm portfolio holdings -> portfolios + holdings tables.

Reads runs/<week>/holdings/<batch>/holdings.json (contract in
agents/holdings-profiler.md). A fund's LP inflows are on the map; this is the
layer BELOW — the companies the fund actually deploys into.

Trust rules enforced here (not just requested from agents):
  - a holding without a source_url is dropped (facts only);
  - the entity must resolve to a known node (an allocator name or an events
    target) so the holdings attach to something downstream.
Cumulative like the map: upsert on (entity, name), never delete — a quiet cycle
never drops a fund's portfolio.
"""

import json
import sys
from datetime import date

from . import db


def _stake(v):
    if v is None:
        return None
    return str(v).strip() or None


def ingest_week(week: str) -> dict:
    con = db.connect()
    hdir = db.RUNS_DIR / week / "holdings"
    stats = {"entities": 0, "holdings": 0, "skipped": 0}
    warnings = []
    if not hdir.is_dir():
        stats["warnings"] = warnings
        con.close()
        return stats

    known_alloc = {r["name"] for r in con.execute("SELECT name FROM allocators")}
    known_target = {r["target"] for r in con.execute("SELECT DISTINCT target FROM events")}

    for batch_dir in sorted(p for p in hdir.iterdir() if p.is_dir()):
        fpath = batch_dir / "holdings.json"
        if not fpath.exists():
            continue
        try:
            objs = json.loads(fpath.read_text())
        except json.JSONDecodeError as e:
            warnings.append(f"{batch_dir.name}/holdings.json: invalid JSON ({e}) — skipped")
            continue
        for o in objs if isinstance(objs, list) else []:
            entity = (o.get("entity") or "").strip()
            canonical = db.resolve_name(entity)
            if canonical not in known_alloc and canonical not in known_target:
                stats["skipped"] += 1
                warnings.append(f"{batch_dir.name}: entity '{entity[:40]}' not a known "
                                f"node — skipped (holdings never create entities)")
                continue
            valid = []
            for i, h in enumerate(o.get("holdings") or []):
                name = (h.get("name") or "").strip()
                url = (h.get("source_url") or "").strip()
                if not name or not url:
                    warnings.append(f"{canonical}: holding '{name[:40]}' missing "
                                    f"name/source_url — dropped")
                    continue
                valid.append((i, name, url, h))
            raw_count = o.get("holdings_count")
            count = (int(raw_count) if isinstance(raw_count, (int, float))
                     and raw_count >= len(valid) else len(valid))
            as_of = (o.get("as_of") or "").strip() or date.today().isoformat()
            purl = (o.get("portfolio_url") or "").strip() or None
            if purl and not purl.startswith("http"):
                purl = None
            con.execute(
                """INSERT INTO portfolios
                     (entity, portfolio_url, holdings_count, as_of, run_week, updated_at)
                   VALUES (?,?,?,?,?,datetime('now'))
                   ON CONFLICT(entity) DO UPDATE SET
                     portfolio_url=COALESCE(excluded.portfolio_url, portfolios.portfolio_url),
                     holdings_count=MAX(excluded.holdings_count, COALESCE(portfolios.holdings_count,0)),
                     as_of=excluded.as_of, run_week=excluded.run_week,
                     updated_at=datetime('now')""",
                (canonical, purl, count, as_of, week))
            stats["entities"] += 1
            for i, name, url, h in valid:
                rank = h.get("rank")
                rank = int(rank) if isinstance(rank, (int, float)) else i + 1
                con.execute(
                    """INSERT INTO holdings
                         (entity, name, sector, subsector, note, stake, lead, rank,
                          as_of, source_url, run_week)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(entity, name) DO UPDATE SET
                         sector=excluded.sector, subsector=excluded.subsector,
                         note=excluded.note, stake=excluded.stake, lead=excluded.lead,
                         rank=excluded.rank, as_of=excluded.as_of,
                         source_url=excluded.source_url, run_week=excluded.run_week""",
                    (canonical, name, (h.get("sector") or "").strip() or None,
                     (h.get("subsector") or "").strip() or None,
                     (h.get("note") or "").strip()[:120] or None, _stake(h.get("stake")),
                     1 if h.get("lead") in (1, "1", True) else 0, rank,
                     (h.get("as_of") or "").strip() or as_of, url, week))
                stats["holdings"] += 1
    con.commit()
    con.close()
    stats["warnings"] = warnings
    return stats


if __name__ == "__main__":
    s = ingest_week(sys.argv[1])
    print(f"holdings {sys.argv[1]}: {s['entities']} portfolios, {s['holdings']} "
          f"holdings, {s['skipped']} skipped")
    for w in s.get("warnings", []):
        print("  WARN", w)
