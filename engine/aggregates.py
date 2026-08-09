"""Aggregates: the derived "alpha" views of spec §4, computed from the DB.

Pure read-side module — no tables written. handoff.py calls compute(con) and
ships the result inside capital_map.json, so the dashboard renders derived
numbers this repo computed (one source of truth), never recomputing its own.

Views:
  top_sector        capital-weighted top sector across CONFIRMED events
                    (verified / verified_alpha — candidates are leads, not money).
  top_company       target backed by the most distinct tracked allocators
                    (tie-break: capital behind it).
  thesis_shares     distribution of stated rationale — the canonical `theme`
                    dimension — by deal count and by capital.
  investor_summaries  per-allocator rollup from events: deals, capital, sectors,
                    personal thesis mix, recency. (Researched narrative + track
                    record live in allocator_profiles / track_records; handoff
                    merges both into the canonical allocator summary.)

Every view carries a `basis` string so a number on the dashboard is always
traceable to its definition (spec §6: every derived number traceable).
"""

CONFIRMED = "('verified','verified_alpha')"


def _round_shares(pairs):
    """[(key, weight)] -> {key: share} with shares summing to ~1.0 (3 dp)."""
    total = sum(w for _, w in pairs) or 1.0
    return {k: round(w / total, 3) for k, w in pairs if w > 0}


def top_sector(con) -> dict:
    rows = con.execute(
        f"""SELECT sector, SUM(COALESCE(amount_usd,0)) capital, COUNT(*) deals,
                   COUNT(DISTINCT allocator_id) allocators
            FROM events WHERE status IN {CONFIRMED}
            GROUP BY sector ORDER BY capital DESC""").fetchall()
    ranked = [{"sector": r["sector"], "capital_usd": r["capital"],
               "deals": r["deals"], "allocators": r["allocators"]} for r in rows]
    return {
        "top": ranked[0] if ranked else None,
        "ranked": ranked[:8],
        "basis": "confirmed events (verified/verified_alpha), capital-weighted; "
                 "undisclosed amounts count as 0",
    }


def top_company(con) -> dict:
    rows = con.execute(
        f"""SELECT target, COUNT(DISTINCT allocator_id) investors,
                   SUM(COALESCE(amount_usd,0)) capital,
                   GROUP_CONCAT(DISTINCT sector) sectors
            FROM events WHERE status IN {CONFIRMED}
            GROUP BY target
            ORDER BY investors DESC, capital DESC""").fetchall()
    ranked = [{"target": r["target"], "investors": r["investors"],
               "capital_usd": r["capital"],
               "sectors": sorted((r["sectors"] or "").split(","))} for r in rows]
    return {
        "top": ranked[0] if ranked else None,
        "ranked": ranked[:8],
        "basis": "confirmed events; ranked by distinct tracked allocators, "
                 "then capital behind the target",
    }


def thesis_shares(con) -> dict:
    rows = con.execute(
        f"""SELECT theme, COUNT(*) deals, SUM(COALESCE(amount_usd,0)) capital
            FROM events WHERE status IN {CONFIRMED} AND theme IS NOT NULL
            GROUP BY theme""").fetchall()
    return {
        "by_deals": _round_shares([(r["theme"], r["deals"]) for r in rows]),
        "by_capital": _round_shares([(r["theme"], r["capital"]) for r in rows]),
        "basis": "share of confirmed events per canonical theme (the stated "
                 "rationale dimension of config/rules.yaml); by_capital ignores "
                 "undisclosed amounts",
    }


def investor_summaries(con) -> dict:
    out = {}
    allocs = con.execute(
        """SELECT a.id, a.name, a.class, a.tier, a.country, a.network
           FROM allocators a WHERE EXISTS
             (SELECT 1 FROM events e WHERE e.allocator_id = a.id)""").fetchall()
    for a in allocs:
        evs = con.execute(
            """SELECT status, sector, theme, amount_usd, disclosed_date
               FROM events WHERE allocator_id = ?""", (a["id"],)).fetchall()
        confirmed = [e for e in evs if e["status"] in ("verified", "verified_alpha")]
        sectors = {}
        for e in confirmed:
            s = sectors.setdefault(e["sector"], {"deals": 0, "capital_usd": 0.0})
            s["deals"] += 1
            s["capital_usd"] += e["amount_usd"] or 0.0
        out[a["name"]] = {
            "class": a["class"], "tier": a["tier"], "country": a["country"],
            "network": a["network"],
            "deals": len(evs), "confirmed_deals": len(confirmed),
            "capital_usd": sum(e["amount_usd"] or 0.0 for e in confirmed),
            "first_seen": min((e["disclosed_date"] for e in evs), default=None),
            "last_activity": max((e["disclosed_date"] for e in evs), default=None),
            "sectors": dict(sorted(sectors.items(),
                                   key=lambda kv: -kv[1]["capital_usd"])),
            "thesis_shares": _round_shares(
                [(t, sum(1 for e in confirmed if e["theme"] == t))
                 for t in {e["theme"] for e in confirmed if e["theme"]}]),
        }
    return out


def compute(con) -> dict:
    return {
        "top_sector": top_sector(con),
        "top_company": top_company(con),
        "thesis_shares": thesis_shares(con),
        "investor_summaries": investor_summaries(con),
    }


if __name__ == "__main__":
    import json
    from . import db
    con = db.connect()
    agg = compute(con)
    con.close()
    print(json.dumps({k: v for k, v in agg.items() if k != "investor_summaries"},
                     indent=2)[:2000])
