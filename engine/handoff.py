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

import hashlib
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
        # Stable, deterministic flow id (same components as the DB dedupe key) so
        # the dashboard can cache a generated "read" against it and only re-word a
        # flow when the flow itself is new or changed — never on every delivery.
        flow_id = "flow:" + hashlib.sha1(
            "|".join((e["allocator"], e["target"], e["event_type"],
                      e["disclosed_date"] or "")).encode()).hexdigest()[:16]
        flows.append({
            "id": flow_id,
            "source": a_id, "target": t_id, "sector": e["sector"],
            "subsector": e["subsector"],
            "event_type": e["event_type"], "amount": e["amount_usd"],
            "amount_estimated": bool(e["amount_estimated"]),
            "round_total": e["round_total_usd"],
            # co_investors is fact (who else was in the round) — editorially useful
            # for the dashboard's read, but it stays a fact the engine sources.
            "co_investors": e["co_investors"],
            "capital_role": e["capital_role"],
            "instrument": e["instrument"], "stage": e["stage"],
            "status": e["status"], "date": e["disclosed_date"], "tier": e["source_tier"],
            "source_url": e["source_url"],
            "confidence": e["confidence_score"],
            "grade": (f"{e['source_reliability']}{e['info_credibility']}"
                      if e["source_reliability"] else None),
        })

    # Target references (engine-owned "what this is"): description + links emitted
    # directly on target nodes. The dashboard's local entityReference.json yields
    # precedence to these fields (per its own _note).
    refs = {r["target"]: r for r in con.execute("SELECT * FROM target_references")}
    for n in nodes.values():
        if n["kind"] != "target":
            continue
        r = refs.get(n["label"])
        if not r:
            continue
        n["description"] = r["description"]
        links = []
        if r["website"]:
            dom = r["website"].split("//")[-1].split("/")[0].removeprefix("www.")
            # Authoritative logo domain — the official site the engine researched.
            # The dashboard's logo fetcher should prefer this over guessing from the
            # entity name (which fails for campuses, fund vehicles and SPVs).
            n["domain"] = dom
            links.append({"kind": "website", "label": dom, "url": r["website"]})
        if r["read_more_url"]:
            links.append({"kind": "read_more", "label": r["read_more_label"] or "Read more",
                          "url": r["read_more_url"]})
        n["links"] = links
        n["reference_as_of"] = r["as_of"]

    # Fund/firm PORTFOLIOS (holdings task): the companies an entity deploys into —
    # the layer below the map's LP flows. Attached to any node (allocator firm or
    # fund-vehicle target) whose label matches a portfolio entity. Holdings are
    # ranked most-notable first so the dashboard's top-5 / top-25 / all views work.
    portfolios = {r["entity"]: r for r in con.execute("SELECT * FROM portfolios")}
    holdings_by = {}
    for h in con.execute(
        """SELECT entity, name, sector, subsector, note, stake, lead, rank,
                  as_of, source_url FROM holdings
           ORDER BY entity, CASE WHEN rank IS NULL THEN 1 ELSE 0 END, rank, name"""):
        holdings_by.setdefault(h["entity"], []).append({
            "name": h["name"], "sector": h["sector"], "subsector": h["subsector"],
            "note": h["note"], "stake": h["stake"], "lead": bool(h["lead"]),
            "as_of": h["as_of"], "source_url": h["source_url"]})
    for n in nodes.values():
        p, hs = portfolios.get(n["label"]), holdings_by.get(n["label"])
        if not p and not hs:
            continue
        if p and p["portfolio_url"]:
            n["portfolio_url"] = p["portfolio_url"]
            # A fund vehicle with no site of its own can still resolve a logo from
            # its portfolio-page host (usually the manager's domain).
            if not n.get("domain"):
                n["domain"] = (p["portfolio_url"].split("//")[-1].split("/")[0]
                               .removeprefix("www."))
        n["holdings"] = hs or []
        n["holdings_count"] = (p["holdings_count"] if p and p["holdings_count"] is not None
                               else len(hs or []))
        n["holdings_as_of"] = (p["as_of"] if p else (hs[0]["as_of"] if hs else None))

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
        """SELECT a.name, t.fiscal_year, t.metric, t.scope, t.value, t.unit,
                  t.provisional, t.source_tier, t.source_url, t.notes
           FROM track_records t JOIN allocators a ON a.id = t.allocator_id
           ORDER BY t.fiscal_year, t.scope""").fetchall():
        track.setdefault(t["name"], []).append(
            {"fiscal_year": t["fiscal_year"], "metric": t["metric"],
             "scope": t["scope"] or None, "value": t["value"], "unit": t["unit"],
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
