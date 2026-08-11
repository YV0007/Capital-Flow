"""Trends: named, grounded sub-sector narratives per time window (7d / 30d / all).

Two stages:
  Stage B (here, mechanical): cluster confirmed flows by (sector, subsector) among
    key/core allocators, over a generous lookback. For each of the three windows,
    filter each cluster's evidence to in-window events and RE-CHECK the bar within
    that window, rank by capital then allocator count, take the top 1-3. Every
    field is SQL-provable from real events — named allocators, real numbers.
  Stage A (agents/trend-writer.md → ingest_week here): a research agent writes a
    grounded narrative for clusters that cleared the bar; merged in by cluster id.

The mechanical block ships value on its own (names + numbers); the narrative is an
enrichment. Nothing is fabricated: a quiet window ships an empty list, and a
borderline cluster is flagged confidence:"low", never dressed up as certain.
"""

import json
import sys
from datetime import date

from . import db

WINDOWS = {"week": 7, "month": 30, "all": None}
MIN_ALLOCATORS = 2          # the qualifying bar within a window
TOP_N = 3
LOOKBACK_DAYS = 400         # Stage-B clustering horizon


def _cluster_id(sector, subsector):
    return f"{sector}::{subsector}"


def _clusters(con):
    """All (sector, subsector) groups among confirmed key/core flows over the
    lookback, with per-event rows so the export can window them."""
    rows = con.execute(
        """SELECT e.id, e.sector, e.subsector, e.disclosed_date AS date,
                  COALESCE(e.amount_usd,0) AS amount, a.name AS allocator, a.tier
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE a.tier IN ('key','core') AND e.subsector IS NOT NULL
                 AND e.status IN ('verified','verified_alpha')
                 AND e.disclosed_date >= date('now', ?)
           ORDER BY e.disclosed_date""", (f"-{LOOKBACK_DAYS} days",)).fetchall()
    groups = {}
    for r in rows:
        groups.setdefault((r["sector"], r["subsector"]), []).append(r)
    return groups


def _window_entry(sector, subsector, evs, narratives):
    """Build one ranked trend entry from a cluster's in-window events (already
    filtered). Returns None if empty."""
    if not evs:
        return None
    allocs = sorted({e["allocator"] for e in evs})
    dates = sorted(e["date"] for e in evs if e["date"])
    cid = _cluster_id(sector, subsector)
    nar = narratives.get(cid)
    cleared = len(allocs) >= MIN_ALLOCATORS
    entry = {
        "cluster_id": cid,
        "title": (nar or {}).get("title") or subsector.replace("-", " ").title(),
        "sector": sector, "subsector": subsector,
        "deals": len(evs),
        "capital_usd": sum(e["amount"] for e in evs),
        "date_range": [dates[0], dates[-1]] if dates else [None, None],
        "allocators": allocs,
        "evidence": [e["id"] for e in evs],
        # A cluster that didn't clear the bar in THIS window is surfaced (top 1-3
        # even when a window is quiet) but honestly flagged, never asserted equal.
        "confidence": ((nar or {}).get("confidence") or "high") if cleared else "low",
        "provisional": bool((nar or {}).get("provisional")) or not cleared,
        "narrative": (nar or {}).get("narrative"),
    }
    return entry


def compute(con, week: str | None = None) -> dict:
    groups = _clusters(con)
    narratives = _load_narratives(con)
    today_ord = date.today().toordinal()
    out = {}
    for wkey, days in WINDOWS.items():
        entries = []
        for (sector, subsector), evs in groups.items():
            if days is not None:
                cutoff = today_ord - days
                evs = [e for e in evs if e["date"]
                       and date.fromisoformat(e["date"]).toordinal() >= cutoff]
            entry = _window_entry(sector, subsector, evs, narratives)
            if entry:
                entries.append(entry)
        # Rank by capital, then allocator count. Prefer bar-clearing clusters, but
        # still surface the strongest 1-3 even if a window is quiet (they carry the
        # low-confidence flag). Zero clusters → empty list (never fabricate one).
        entries.sort(key=lambda e: (e["confidence"] != "low", e["capital_usd"],
                                    len(e["allocators"])), reverse=True)
        out[wkey] = entries[:TOP_N]
    return out


# --- Stage A narrative store (written by the trend-writer agent) ---------------

def _load_narratives(con) -> dict:
    try:
        rows = con.execute("SELECT * FROM trend_narratives").fetchall()
    except Exception:
        return {}
    return {r["cluster_id"]: dict(r) for r in rows}


def ingest_week(week: str) -> dict:
    """Load runs/<week>/trends/<batch>/trends.json (contract in
    agents/trend-writer.md) into trend_narratives. Facts-only: a narrative whose
    cluster no longer exists, or that lacks a title, is skipped."""
    con = db.connect()
    tdir = db.RUNS_DIR / week / "trends"
    stats = {"narratives": 0, "skipped": 0, "warnings": []}
    if not tdir.is_dir():
        con.close()
        return stats
    live = {f"{s}::{ss}" for s, ss in con.execute(
        "SELECT DISTINCT sector, subsector FROM events WHERE subsector IS NOT NULL")}
    for batch_dir in sorted(p for p in tdir.iterdir() if p.is_dir()):
        fpath = batch_dir / "trends.json"
        if not fpath.exists():
            continue
        try:
            objs = json.loads(fpath.read_text())
        except json.JSONDecodeError as e:
            stats["warnings"].append(f"{batch_dir.name}/trends.json: invalid JSON ({e})")
            continue
        for o in objs if isinstance(objs, list) else []:
            cid = (o.get("cluster_id") or "").strip()
            title = (o.get("title") or "").strip()
            if not cid or not title:
                stats["skipped"] += 1
                continue
            if cid not in live:
                stats["skipped"] += 1
                stats["warnings"].append(f"{cid}: cluster no longer exists — skipped")
                continue
            con.execute(
                """INSERT INTO trend_narratives
                     (cluster_id, title, narrative, confidence, provisional, run_week, updated_at)
                   VALUES (?,?,?,?,?,?,datetime('now'))
                   ON CONFLICT(cluster_id) DO UPDATE SET
                     title=excluded.title, narrative=excluded.narrative,
                     confidence=excluded.confidence, provisional=excluded.provisional,
                     run_week=excluded.run_week, updated_at=datetime('now')""",
                (cid, title[:120], (o.get("narrative") or "").strip()[:1200] or None,
                 (o.get("confidence") or "").strip() or None,
                 1 if o.get("provisional") in (1, "1", True) else 0, week))
            stats["narratives"] += 1
    con.commit()
    con.close()
    return stats


if __name__ == "__main__":
    con = db.connect()
    t = compute(con, sys.argv[1] if len(sys.argv) > 1 else None)
    con.close()
    for wk, entries in t.items():
        print(f"\n== {wk} ({len(entries)}) ==")
        for e in entries:
            print(f"  {e['title']} [{e['sector']}/{e['subsector']}] "
                  f"{e['deals']} deals ${e['capital_usd']/1e6:.0f}M "
                  f"{e['allocators']} conf={e['confidence']}")
