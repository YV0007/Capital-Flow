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

from . import db

STALE_DAYS = 180  # entities with no activity beyond this are flagged stale (not dropped)


def _build_map(con) -> dict:
    events = con.execute(
        """SELECT e.*, a.name AS allocator, a.class AS allocator_class,
                  a.tier AS allocator_tier, a.network AS allocator_network
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
                  network=e["allocator_network"])
        t = touch(t_id, label=e["target"], kind="target",
                  cls=e["target_type"], tier=None, sector=e["sector"], network=None)
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

    return {
        "generated": today,
        "totals": {"nodes": len(nodes), "flows": len(flows), "sectors": len(sectors)},
        "nodes": sorted(nodes.values(), key=lambda n: -n["capital"]),
        "flows": flows,
        "sectors": sectors,
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


def run(week: str) -> dict:
    con = db.connect()
    db.HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    map_path = db.HANDOFF_DIR / "capital_map.json"
    prev = json.loads(map_path.read_text()) if map_path.exists() else None

    cur = _build_map(con)
    map_path.write_text(json.dumps(cur, indent=2))
    (db.HANDOFF_DIR / "CHANGELOG.md").write_text(_changelog(prev, cur))
    con.close()
    return {"nodes": cur["totals"]["nodes"], "flows": cur["totals"]["flows"]}


if __name__ == "__main__":
    import sys
    print(run(sys.argv[1]))
