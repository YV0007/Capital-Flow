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

from . import aggregates, db, trends

STALE_DAYS = 180  # entities with no activity beyond this are flagged stale (not dropped)
CONFIDENCE_THRESHOLD = 60  # D3: main-map floor; flows scoring below this belong in "Watch"


def _build_map(con, week: str | None = None) -> dict:
    events = con.execute(
        """SELECT e.*, a.name AS allocator, a.class AS allocator_class,
                  a.tier AS allocator_tier, a.network AS allocator_network,
                  a.country AS allocator_country
           FROM events e JOIN allocators a ON a.id = e.allocator_id""").fetchall()

    # Rotation keep-alive (deterministic): a flow whose event is part of a signal
    # fired THIS cycle stays in the dashboard's default time-window even if older.
    # The dashboard filters on age_days; active_signal is the rule-based rescue.
    latest = week or (con.execute(
        "SELECT MAX(run_week) w FROM themes").fetchone()["w"])
    active_event_ids, active_targets = set(), set()
    for r in con.execute("SELECT evidence FROM themes WHERE run_week = ?", (latest,)):
        try:
            active_event_ids.update(int(x) for x in json.loads(r["evidence"]))
        except (ValueError, TypeError):
            pass
    if active_event_ids:
        ph = ",".join("?" * len(active_event_ids))
        active_targets = {row["target"] for row in con.execute(
            f"SELECT DISTINCT target FROM events WHERE id IN ({ph})",
            tuple(active_event_ids))}

    today_ord = date.today().toordinal()

    def _age(d):
        try:
            return today_ord - datetime.fromisoformat(d).toordinal() if d else None
        except ValueError:
            return None

    nodes = {}

    def touch(node_id, **base):
        n = nodes.get(node_id)
        if not n:
            n = {**base, "id": node_id, "deals": 0, "capital": 0.0,
                 "first_seen": None, "last_activity": None}
            nodes[node_id] = n
        return n

    # Dated backers (deal-classifier): round_id + role per (target, allocator), and
    # the full set of participation edges. Event flows are enriched from this; any
    # backer with no matching event becomes an extra dated edge (amount may be null).
    backers = con.execute("SELECT * FROM round_backers").fetchall()
    backer_by_pair = {}
    for b in backers:
        backer_by_pair.setdefault((b["target"], b["allocator"]), b)

    def _derived_role(e):
        if e["event_type"] == "follow_on":
            return "follow-on"
        cr = (e["capital_role"] or "").lower()
        return "lead" if cr in ("lead", "sole") else ("participant" if cr == "participant" else None)

    flows = []
    seen_edges = set()
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
        seen_edges.add((e["target"], e["allocator"]))
        bk = backer_by_pair.get((e["target"], e["allocator"]))
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
            # Dated-backer enrichment (deal-classifier): round grouping + role so the
            # dashboard can order who entered before the crowd (lead-time/bellwether).
            "round_id": bk["round_id"] if bk else None,
            "role": (bk["role"] if bk and bk["role"] else _derived_role(e)),
            "provisional": bool(bk["provisional"]) if bk else False,
            # Rotation fields — the dashboard's default view is a trailing window
            # on age_days; active_signal keeps a pivotal older flow in view by rule.
            "age_days": _age(e["disclosed_date"]),
            "active_signal": e["id"] in active_event_ids,
            "status": e["status"], "date": e["disclosed_date"], "tier": e["source_tier"],
            "source_url": e["source_url"],
            "confidence": e["confidence_score"],
            "grade": (f"{e['source_reliability']}{e['info_credibility']}"
                      if e["source_reliability"] else None),
        })

    # Classifier-only backer edges: a participant with no capital event of its own
    # still forms a dated edge (amount may be null — it's participation, not a
    # sourced capital move). These extend the graph for lead-time / bellwether.
    for b in backers:
        if (b["target"], b["allocator"]) in seen_edges:
            continue
        a_id, t_id = f"alloc:{b['allocator']}", f"target:{b['target']}"
        if t_id not in nodes:  # only attach to targets already on the map
            continue
        a = touch(a_id, label=b["allocator"], kind="allocator", cls=None,
                  tier=None, sector=None, network=None, country=None)
        d = b["entry_date"] or ""
        a["deals"] += 1
        a["first_seen"] = min(a["first_seen"] or d, d) if d else a["first_seen"]
        a["last_activity"] = max(a["last_activity"] or d, d) if d else a["last_activity"]
        flows.append({
            "id": "flow:" + hashlib.sha1(
                "|".join((b["allocator"], b["target"], b["round_id"])).encode()
            ).hexdigest()[:16],
            "source": a_id, "target": t_id, "sector": nodes[t_id]["sector"],
            "event_type": "funding_round", "amount": b["amount_usd"],
            "round_id": b["round_id"], "role": b["role"],
            "age_days": _age(b["entry_date"]),
            "active_signal": b["target"] in active_targets,
            "status": b["status"], "date": b["entry_date"], "tier": b["source_tier"],
            "source_url": b["source_url"], "provisional": bool(b["provisional"]),
            "backer_edge": True,  # participation metadata, not a sourced capital move
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

    # Per-target deep classification (deal-classifier): outcome/valuation trail,
    # investability, ai_posture. Lights up the dashboard's Rank-1 deal factors.
    for c in con.execute("SELECT * FROM target_classification").fetchall():
        n = nodes.get(f"target:{c['target']}")
        if not n:
            continue
        if c["outcome_status"] or c["latest_valuation_usd"]:
            n["outcome"] = {
                "status": c["outcome_status"],
                "entry_valuation_usd": c["entry_valuation_usd"],
                "latest_valuation_usd": c["latest_valuation_usd"],
                "latest_as_of": c["latest_as_of"],
                "step_up_multiple": c["step_up_multiple"],
                "source_url": c["outcome_source_url"],
                "provisional": bool(c["outcome_provisional"])}
        if c["listing_status"] or c["public_ticker"] or c["public_proxies"]:
            n["investability"] = {
                "listing_status": c["listing_status"],
                "public_ticker": c["public_ticker"],
                "public_proxies": json.loads(c["public_proxies"] or "[]")}
        if c["ai_class"]:
            n["ai_posture"] = {
                "class": c["ai_class"], "rationale": c["ai_rationale"],
                "source_url": c["ai_source_url"], "confidence": c["ai_confidence"],
                "provisional": bool(c["ai_provisional"])}

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
    # Signals for THIS run week only (prereq fix: the old query had no run_week
    # filter, so next week it would mix every prior week's signals with no way to
    # tell which are current), and it now carries `evidence` (the event ids) —
    # previously computed then dropped at export, which left nothing able to
    # resolve a signal back to real allocator/target names.
    for t in con.execute(
        """SELECT theme, sector, rule, strength, evidence, entity_id FROM themes
           WHERE run_week = ? ORDER BY strength DESC""", (latest,)).fetchall():
        sectors.setdefault(t["sector"], {"deals": 0, "capital": 0, "allocators": 0, "signals": []})
        try:
            ev = [int(x) for x in json.loads(t["evidence"] or "[]")]
        except (ValueError, TypeError):
            ev = []
        sectors[t["sector"]]["signals"].append(
            {"theme": t["theme"], "rule": t["rule"], "strength": t["strength"],
             "evidence": ev,
             # Anchors a signal to a specific node (target:/ticker:/alloc:) so the
             # dashboard can pin it to a company, not just a sector zone.
             "entity_id": t["entity_id"]})

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
           WHERE e.theme IS NOT NULL AND th.run_week = ?""", (latest,)).fetchall():
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

    # Weekly promotion queue — discovered co-investors awaiting the user's Monday
    # review. The dashboard renders these as the pop-up (yes/no per name); the
    # engine NEVER auto-promotes. An accepted name is applied by tools/promote.py.
    promotion_queue = []
    for c in con.execute(
        """SELECT name, GROUP_CONCAT(DISTINCT suggested_class) classes,
                  GROUP_CONCAT(DISTINCT seen_with) seen_with,
                  GROUP_CONCAT(DISTINCT rationale) rationale,
                  COUNT(*) times_seen, MIN(created_at) first_seen
           FROM universe_candidates WHERE status = 'new'
           GROUP BY name ORDER BY times_seen DESC, name""").fetchall():
        seen = sorted({s for s in (c["seen_with"] or "").split(",") if s})
        promotion_queue.append({
            "candidate_id": "cand:" + c["name"].lower().replace(" ", "-"),
            "name": c["name"],
            "suggested_class": (c["classes"] or "").split(",")[0] or None,
            "seen_with": seen,
            "description": (c["rationale"] or "").split(",")[0]
            or (f"Co-invested with {', '.join(seen[:3])}" if seen else "Discovered co-investor"),
            "times_seen": c["times_seen"], "first_seen": c["first_seen"],
        })

    return {
        "generated": today,
        "totals": {"nodes": len(nodes), "flows": len(flows), "sectors": len(sectors)},
        "aggregates": agg,
        "allocators": allocator_summaries,
        # D3: flows at or above this confidence score belong on the main map; below → Watch.
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        # Rotation: dashboard default view = trailing window on flow.age_days;
        # keep any flow with active_signal:true regardless of age. Toggles let the
        # user widen to 7 / 30 / 90 / all. Nothing is ever deleted — only filtered.
        "view_defaults": {"default_window_days": 30, "windows": [7, 30, 90, None],
                          "keep_active_signal": True},
        "promotion_queue": promotion_queue,
        # Named, grounded sub-sector narratives per window (7d/30d/all). Top 1-3
        # each, ranked by capital then allocator count; mechanical numbers + named
        # allocators are SQL-derived, narrative is the trend-writer enrichment.
        "trends": trends.compute(con, week),
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

    cur = _build_map(con, week)
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
