"""Handoff: DB -> handoff/ files for the dashboard side.

The dashboard (ab-investment) is a separate repo. The connection is NOT a live
data feed: this module exports a self-contained map-state file that a Claude
session on the dashboard side consumes to RECONSTRUCT the Capital Flow Map —
adding new entities, retiring stale ones, adjusting visuals per handoff/RULES.md.

Outputs:
  handoff/capital_map.json   current map state: nodes (allocators + targets) with
                             first_seen / last_activity / totals, flows (edges),
                             sector aggregates, and fired signals.
  handoff/CHANGELOG.md       delta vs the previous capital_map.json (new / stale).

Reconstruction rules (when to add / drop / keep an entity, display thresholds)
live in handoff/RULES.md — authored later; this exporter just ships the state.
"""

import json
from datetime import date, datetime

from . import aggregates, db

STALE_DAYS = 180  # entities with no activity beyond this are flagged stale (not dropped)
CONFIDENCE_THRESHOLD = 60  # D3: main-map floor; flows scoring below this belong in "Watch"


def _build_map(con) -> dict:
    events = con.execute(
        """SELECT e.*, a.name AS allocator, a.class AS allocator_class,
                  a.tier AS allocator_tier, a.network AS allocator_network,
                  a.country AS allocator_country
           FROM events e JOIN allocators a ON a.id = e.allocator_id""").fetchall()

    nodes = {}

    def touch(node_id, **base):
        n = nodes.get(node_id)
        if not n:
            n = {**base, "id": node_id, "deals": 0, "capital": 0.0,
                 "first_seen": None, "last_activity": None}
            nodes[node_id] = n
        return n

    flows = []
    for e in events:
        amt = e["amount_usd"] or 0.0
        a_id = f"alloc:{e['allocator']}"
        t_id = f"target:{e['target']}"
        a = touch(a_id, label=e["allocator"], kind="allocator",
                  cls=e["allocator_class"], tier=e["allocator_tier"], sector=None,
                  network=e["allocator_network"], country=e["allocator_country"])
        t = touch(t_id, label=e["target"], kind="target",
                  cls=e["target_type"], tier=None, sector=e["sector"], network=None,
                  country=None)
        for n in (a, t):
            n["deals"] += 1
            n["capital"] += amt
            d = e["disclosed_date"]
            n["first_seen"] = min(n["first_seen"] or d, d)
            n["last_activity"] = max(n["last_activity"] or d, d)
        flows.append({
            "source": a_id, "target": t_id, "sector": e["sector"],
            "event_type": e["event_type"], "amount": e["amount_usd"],
            "status": e["status"], "date": e["disclosed_date"], "tier": e["source_tier"],
            "confidence": e["confidence_score"],
            "grade": (f"{e['source_reliability']}{e['info_credibility']}"
                      if e["source_reliability"] else None),
        })

    today = date.today().isoformat()
    for n in nodes.values():
        stale_before = (datetime.fromisoformat(today).toordinal() - STALE_DAYS)
        last = datetime.fromisoformat(n["last_activity"]).toordinal() if n["last_activity"] else 0
        n["stale"] = last < stale_before

    sectors = {}
    for s in con.execute(
        """SELECT sector, COUNT(*) n, SUM(COALESCE(amount_usd,0)) total,
                  COUNT(DISTINCT allocator_id) allocs FROM events GROUP BY sector""").fetchall():
        sectors[s["sector"]] = {"deals": s["n"], "capital": s["total"],
                                "allocators": s["allocs"], "signals": []}
    for t in con.execute(
        "SELECT theme, sector, rule, strength FROM themes ORDER BY strength DESC").fetchall():
        sectors.setdefault(t["sector"], {"deals": 0, "capital": 0, "allocators": 0, "signals": []})
        sectors[t["sector"]]["signals"].append(
            {"theme": t["theme"], "rule": t["rule"], "strength": t["strength"]})

    # Theme aggregates (WS5) — the cross-cutting dimension alongside sectors.
    themes_agg = {}
    for t in con.execute(
        """SELECT theme, COUNT(*) n, SUM(COALESCE(amount_usd,0)) total,
                  COUNT(DISTINCT allocator_id) allocs FROM events
           WHERE theme IS NOT NULL GROUP BY theme""").fetchall():
        themes_agg[t["theme"]] = {"deals": t["n"], "capital": t["total"],
                                  "allocators": t["allocs"], "signals": []}
    for t in con.execute(
        """SELECT th.theme AS label, th.rule, th.strength, e.theme AS ev_theme
           FROM themes th JOIN events e
             ON e.id = CAST(json_extract(th.evidence, '$[0]') AS INTEGER)
           WHERE e.theme IS NOT NULL""").fetchall():
        if t["ev_theme"] in themes_agg:
            themes_agg[t["ev_theme"]]["signals"].append(
                {"theme": t["label"], "rule": t["rule"], "strength": t["strength"]})

    # Canonical allocator summaries (spec §4/§5) — built ONCE here: the researched
    # profile + sourced track record merged with the event-derived rollup. The
    # dashboard's aggregates and its detail panel both read this block.
    agg = aggregates.compute(con)
    rollups = agg.pop("investor_summaries")
    profiles = {p["name"]: p for p in con.execute(
        """SELECT a.name, p.* FROM allocator_profiles p
           JOIN allocators a ON a.id = p.allocator_id""").fetchall()}
    track = {}
    for t in con.execute(
        """SELECT a.name, t.fiscal_year, t.metric, t.value, t.unit, t.provisional,
                  t.source_tier, t.source_url, t.notes
           FROM track_records t JOIN allocators a ON a.id = t.allocator_id
           ORDER BY t.fiscal_year""").fetchall():
        track.setdefault(t["name"], []).append(
            {"fiscal_year": t["fiscal_year"], "metric": t["metric"],
             "value": t["value"], "unit": t["unit"],
             "provisional": bool(t["provisional"]), "source_tier": t["source_tier"],
             "source_url": t["source_url"], "notes": t["notes"]})
    allocator_summaries = {}
    for name in set(rollups) | set(profiles):
        p = profiles.get(name)
        allocator_summaries[name] = {
            **(rollups.get(name) or {}),
            "profile": ({"background": p["background"], "focus": p["focus"],
                         "style": p["style"], "thesis": p["thesis"],
                         "latest_investments_summary": p["latest_summary"],
                         "strategy": p["strategy"],
                         "strategy_source_url": p["strategy_source_url"],
                         "sources": json.loads(p["sources"] or "[]"),
                         "track_record_note": p["track_record_note"],
                         "as_of": p["as_of"]} if p else None),
            "track_record": track.get(name, []),
        }

    return {
        "generated": today,
        "totals": {"nodes": len(nodes), "flows": len(flows), "sectors": len(sectors)},
        "aggregates": agg,
        "allocators": allocator_summaries,
        # D3: flows at or above this confidence score belong on the main map; below → Watch.
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "nodes": sorted(nodes.values(), key=lambda n: -n["capital"]),
        "flows": flows,
        "sectors": sectors,
        "themes": themes_agg,
    }


def _changelog(prev: dict | None, cur: dict) -> str:
    cur_ids = {n["id"] for n in cur["nodes"]}
    prev_ids = {n["id"] for n in prev["nodes"]} if prev else set()
    new = sorted(cur_ids - prev_ids)
    stale = sorted(n["id"] for n in cur["nodes"] if n["stale"])
    L = [f"# Handoff changelog — {cur['generated']}", "",
         f"- nodes: {cur['totals']['nodes']}  flows: {cur['totals']['flows']}  "
         f"sectors: {cur['totals']['sectors']}", ""]
    L.append(f"## New entities ({len(new)})")
    L += [f"- {i}" for i in new] or ["_none_"]
    L.append("")
    L.append(f"## Stale entities — no activity in {STALE_DAYS}d ({len(stale)})")
    L += [f"- {i}" for i in stale] or ["_none_"]
    L.append("")
    return "\n".join(L)


def run(week: str, audit_verdict: dict | None = None) -> dict:
    con = db.connect()
    db.HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    map_path = db.HANDOFF_DIR / "capital_map.json"
    prev = json.loads(map_path.read_text()) if map_path.exists() else None

    cur = _build_map(con)
    # Ship the audit verdict with the payload (spec §6): the dashboard can state
    # when the data was last verified and whether anything is flagged.
    if audit_verdict is None:
        from . import audit as _audit
        audit_verdict = _audit.run(week)
    cur["audit"] = {
        "generated": audit_verdict["generated"], "week": audit_verdict["week"],
        "passed": audit_verdict["passed"], "checked": audit_verdict["checked"],
        "error_count": len(audit_verdict["errors"]),
        "warning_count": len(audit_verdict["warnings"]),
        "warnings": audit_verdict["warnings"][:25],
        "stats": audit_verdict["stats"],
    }
    map_path.write_text(json.dumps(cur, indent=2))
    (db.HANDOFF_DIR / "CHANGELOG.md").write_text(_changelog(prev, cur))
    con.close()
    return {"nodes": cur["totals"]["nodes"], "flows": cur["totals"]["flows"]}


if __name__ == "__main__":
    import sys
    print(run(sys.argv[1]))
