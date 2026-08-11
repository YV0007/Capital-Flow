"""Theme engine: SQL signal rules over events -> themes table.

Rules are declared in config/rules.yaml; each rule id maps to a routine here.
Themes for a run week are rebuilt idempotently (old rows for the week dropped
first). Evidence is stored as a JSON array of event ids.

Rules implemented:
  sector_swarm        N distinct key allocators into one sector in a window
  capital_acceleration  sector's window capital vs the prior window >= factor
  first_entry         an established key allocator enters a brand-new sector
"""

import json
from collections import defaultdict
from datetime import date, timedelta

from . import db


def _rule(cfg, rule_id, default):
    for r in cfg["rules"]:
        if r.get("id") == rule_id:
            return r
    return default


def _sector_swarm(con, week, p):
    win = f"-{p.get('window_days', 30)} days"
    # Count only CONFIRMED capital (verified / verified_alpha) — candidates are leads,
    # not committed money, and shouldn't trigger an alpha signal.
    rows = con.execute(
        """SELECT e.sector AS sector, COUNT(DISTINCT e.allocator_id) AS inv,
                  SUM(COALESCE(e.amount_usd,0)) AS total,
                  GROUP_CONCAT(e.id) AS ids
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE a.tier IN ('key','core') AND e.disclosed_date >= date('now', ?)
                 AND e.status IN ('verified','verified_alpha')
           GROUP BY e.sector
           HAVING inv >= ?""",
        (win, p.get("min_allocators", 5)),
    ).fetchall()
    out = []
    for r in rows:
        ids = [int(x) for x in r["ids"].split(",")]
        out.append((f"{r['sector']}: {r['inv']} key allocators in {p.get('window_days',30)}d",
                    r["sector"], "sector_swarm", json.dumps(ids), float(r["inv"])))
    return out


def _subsector_swarm(con, week, p):
    """Like sector_swarm but one level deeper — N distinct key/core allocators
    converging on the same (sector, subsector) narrative. Sub-buckets are smaller
    populations, so the bar is lower (min_allocators default 2). Scans a generous
    lookback; the trends[] export re-checks the bar per time window (7/30/all)."""
    win = f"-{p.get('window_days', 400)} days"
    rows = con.execute(
        """SELECT e.sector AS sector, e.subsector AS subsector,
                  COUNT(DISTINCT e.allocator_id) AS inv, GROUP_CONCAT(e.id) AS ids
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE a.tier IN ('key','core') AND e.subsector IS NOT NULL
                 AND e.status IN ('verified','verified_alpha')
                 AND e.disclosed_date >= date('now', ?)
           GROUP BY e.sector, e.subsector
           HAVING inv >= ?""", (win, p.get("min_allocators", 2))).fetchall()
    return [(f"{r['sector']}/{r['subsector']}: {r['inv']} key allocators converge",
             r["sector"], "subsector_swarm",
             json.dumps([int(x) for x in r["ids"].split(",")]), float(r["inv"]))
            for r in rows]


def _capital_acceleration(con, week, p):
    win = p.get("window_days", 90)
    factor = p.get("growth_factor", 2.0)
    cur = {r["sector"]: r["t"] for r in con.execute(
        """SELECT sector, SUM(COALESCE(amount_usd,0)) t FROM events
           WHERE disclosed_date >= date('now', ?) GROUP BY sector""",
        (f"-{win} days",)).fetchall()}
    prev = {r["sector"]: r["t"] for r in con.execute(
        """SELECT sector, SUM(COALESCE(amount_usd,0)) t FROM events
           WHERE disclosed_date >= date('now', ?) AND disclosed_date < date('now', ?)
           GROUP BY sector""", (f"-{2*win} days", f"-{win} days")).fetchall()}
    out = []
    for sector, c in cur.items():
        pv = prev.get(sector, 0)
        if pv > 0 and c / pv >= factor:
            ids = [r["id"] for r in con.execute(
                "SELECT id FROM events WHERE sector=? AND disclosed_date >= date('now', ?)",
                (sector, f"-{win} days")).fetchall()]
            out.append((f"{sector}: capital {c/pv:.1f}x vs prior {win}d", sector,
                        "capital_acceleration", json.dumps(ids), round(c / pv, 2)))
    return out


def _first_entry(con, week, p):
    look = p.get("lookback_days", 365)
    rows = con.execute(
        """SELECT e.id, e.allocator_id, e.sector, e.disclosed_date, a.name
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE a.tier IN ('key','core')""").fetchall()
    by_alloc = defaultdict(list)
    for r in rows:
        by_alloc[(r["allocator_id"], r["name"])].append(r)
    cutoff = con.execute("SELECT date('now', ?)", (f"-{look} days",)).fetchone()[0]
    out = []
    for (aid, name), evs in by_alloc.items():
        established = any(e["disclosed_date"] < cutoff for e in evs)
        if not established:
            continue
        by_sector = defaultdict(list)
        for e in evs:
            by_sector[e["sector"]].append(e)
        for sector, sevs in by_sector.items():
            if min(e["disclosed_date"] for e in sevs) >= cutoff:
                ids = [e["id"] for e in sevs]
                out.append((f"{name} enters {sector} (first time)", sector,
                            "first_entry", json.dumps(ids), 1.0, f"alloc:{name}"))
    return out


def _network_convergence(con, week, p):
    """N+ members of one elite network putting confirmed capital into the same sector
    within a window — the coordinated-network signal (config/networks.yaml)."""
    win = f"-{p.get('window_days', 180)} days"
    rows = con.execute(
        """SELECT a.network AS network, e.sector AS sector,
                  COUNT(DISTINCT a.id) AS members, GROUP_CONCAT(e.id) AS ids
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE a.network IS NOT NULL AND e.status IN ('verified','verified_alpha')
                 AND e.disclosed_date >= date('now', ?)
           GROUP BY a.network, e.sector
           HAVING members >= ?""",
        (win, p.get("min_members", 3)),
    ).fetchall()
    out = []
    for r in rows:
        ids = [int(x) for x in r["ids"].split(",")]
        out.append((f"{r['network']}: {r['members']} members converge on {r['sector']} "
                    f"({p.get('window_days', 180)}d)", r["sector"], "network_convergence",
                    json.dumps(ids), float(p.get("weight", 5))))
    return out


def _theme_swarm(con, week, p):
    """Like sector_swarm but on the cross-cutting THEME dimension (WS5) — catches
    convergence that spans sectors (e.g. energy_for_ai across power + nuclear)."""
    win = f"-{p.get('window_days', 30)} days"
    rows = con.execute(
        """SELECT e.theme AS theme, COUNT(DISTINCT e.allocator_id) AS inv,
                  GROUP_CONCAT(e.id) AS ids, MIN(e.sector) AS sector
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE e.theme IS NOT NULL AND a.tier IN ('key','core')
                 AND e.status IN ('verified','verified_alpha')
                 AND e.disclosed_date >= date('now', ?)
           GROUP BY e.theme HAVING inv >= ?""",
        (win, p.get("min_allocators", 4))).fetchall()
    return [(f"{r['theme']}: {r['inv']} key allocators converge ({p.get('window_days',30)}d)",
             r["sector"], "theme_swarm", json.dumps([int(x) for x in r["ids"].split(",")]),
             float(r["inv"])) for r in rows]


def _smart_money_follow(con, week, p):
    """A key/core allocator enters a sector, then N+ others follow shortly after —
    the 'smart money leads, the rest chase' pattern."""
    win, follow, min_f = (p.get("window_days", 90), p.get("follow_days", 21),
                          p.get("min_followers", 2))
    rows = con.execute(
        """SELECT e.sector AS sector, e.allocator_id AS aid, e.disclosed_date AS d,
                  e.id AS id, a.name AS name
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE a.tier IN ('key','core') AND e.status IN ('verified','verified_alpha')
                 AND e.disclosed_date >= date('now', ?)
           ORDER BY e.sector, e.disclosed_date""", (f"-{win} days",)).fetchall()
    by_sector = defaultdict(list)
    for r in rows:
        by_sector[r["sector"]].append(r)
    out = []
    for sector, evs in by_sector.items():
        leader = evs[0]
        end = (date.fromisoformat(leader["d"]) + timedelta(days=follow)).isoformat()
        followers = {e["aid"] for e in evs
                     if e["aid"] != leader["aid"] and leader["d"] < e["d"] <= end}
        if len(followers) >= min_f:
            ids = [e["id"] for e in evs if e["d"] <= end]
            out.append((f"{sector}: smart money — {leader['name']} led, "
                        f"{len(followers)} followed in {follow}d", sector,
                        "smart_money_follow", json.dumps(ids), float(len(followers) + 1)))
    return out


def _stealth_accumulation(con, week, p):
    """N+ stakes into one target within a window — quiet accumulation."""
    win, min_stakes = p.get("window_days", 90), p.get("min_stakes", 3)
    rows = con.execute(
        """SELECT e.target AS target, COUNT(*) AS n, GROUP_CONCAT(e.id) AS ids,
                  MIN(e.sector) AS sector
           FROM events e
           WHERE e.event_type IN ('minority_stake','equity','follow_on')
                 AND e.status IN ('verified','verified_alpha')
                 AND e.disclosed_date >= date('now', ?)
           GROUP BY e.target HAVING n >= ?""", (f"-{win} days", min_stakes)).fetchall()
    return [(f"{r['target']}: stealth accumulation — {r['n']} stakes in {win}d",
             r["sector"] or "unknown", "stealth_accumulation",
             json.dumps([int(x) for x in r["ids"].split(",")]), float(r["n"]),
             f"target:{r['target']}") for r in rows]


def _beneficiary_concentration(con, week, p):
    """N+ private flows map to one public beneficiary ticker — the public read-through."""
    min_flows = p.get("min_flows", 3)
    rows = con.execute(
        """SELECT b.ticker AS ticker, b.company AS company,
                  COUNT(DISTINCT b.event_id) AS flows, GROUP_CONCAT(DISTINCT b.event_id) AS ids
           FROM beneficiaries b GROUP BY b.ticker HAVING flows >= ?""", (min_flows,)).fetchall()
    out = []
    for r in rows:
        ids = [int(x) for x in r["ids"].split(",")]
        ph = ",".join("?" * len(ids))
        sec = con.execute(f"SELECT sector, COUNT(*) c FROM events WHERE id IN ({ph}) "
                          f"GROUP BY sector ORDER BY c DESC LIMIT 1", ids).fetchone()
        out.append((f"{r['ticker']} ({r['company']}): {r['flows']} private flows converge",
                    sec["sector"] if sec else "unknown", "beneficiary_concentration",
                    json.dumps(ids), float(r["flows"]), f"ticker:{r['ticker']}"))
    return out


def _thiel_repeat_conviction(con, week, p):
    """A network member (or their vehicle) backs the same theme 3+ times — repeat
    conviction is a stronger tell than a single large check."""
    rows = con.execute(
        """SELECT a.name AS name, a.network AS network, e.theme AS theme,
                  COUNT(*) AS n, GROUP_CONCAT(e.id) AS ids, MIN(e.sector) AS sector
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE a.network IS NOT NULL AND e.theme IS NOT NULL
                 AND e.status IN ('verified','verified_alpha')
           GROUP BY a.id, e.theme HAVING n >= ?""", (p.get("min_repeats", 3),)).fetchall()
    return [(f"{r['name']}: repeat conviction — {r['n']}x into {r['theme']}",
             r["sector"], "repeat_conviction",
             json.dumps([int(x) for x in r["ids"].split(",")]), float(r["n"]))
            for r in rows]


def _defense_network_convergence(con, week, p):
    """Network capital + strategic corporate/government capital landing in one sector —
    the pattern behind defense/national-security build-outs."""
    rows = con.execute(
        """SELECT e.sector AS sector,
                  COUNT(DISTINCT CASE WHEN a.network IS NOT NULL THEN a.id END) AS net_n,
                  COUNT(DISTINCT CASE WHEN a.class IN ('corporate','sovereign')
                                      THEN a.id END) AS strat_n,
                  GROUP_CONCAT(e.id) AS ids
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE e.status IN ('verified','verified_alpha')
                 AND e.disclosed_date >= date('now', ?)
           GROUP BY e.sector
           HAVING net_n >= ? AND strat_n >= ?""",
        (f"-{p.get('window_days', 180)} days", p.get("min_network", 2),
         p.get("min_strategic", 2))).fetchall()
    return [(f"{r['sector']}: network + strategic capital converge "
             f"({r['net_n']} network, {r['strat_n']} strategic)", r["sector"],
             "defense_network_convergence",
             json.dumps([int(x) for x in r["ids"].split(",")]),
             float(r["net_n"] + r["strat_n"])) for r in rows]


RULES = {
    "sector_swarm": _sector_swarm,
    "subsector_swarm": _subsector_swarm,
    "theme_swarm": _theme_swarm,
    "capital_acceleration": _capital_acceleration,
    "first_entry": _first_entry,
    "smart_money_follow": _smart_money_follow,
    "stealth_accumulation": _stealth_accumulation,
    "beneficiary_concentration": _beneficiary_concentration,
}


def run(week: str) -> dict:
    """Evaluate all configured rules for a run week and persist fired themes."""
    con = db.connect()
    cfg = db.load_config()
    con.execute("DELETE FROM themes WHERE run_week = ?", (week,))
    fired = []
    for r in cfg["rules"]:
        fn = RULES.get(r.get("id"))
        if not fn:
            continue
        for row in fn(con, week, r):
            theme, sector, rule, evidence, strength = row[:5]
            entity_id = row[5] if len(row) > 5 else None
            con.execute(
                """INSERT INTO themes (run_week, theme, sector, rule, evidence,
                     strength, entity_id) VALUES (?,?,?,?,?,?,?)""",
                (week, theme, sector, rule, evidence, strength, entity_id))
            fired.append(theme)
    # Network rules live in config/networks.yaml; evaluate the active ones.
    network_rules = {
        "network_convergence": _network_convergence,
        "thiel_repeat_conviction": _thiel_repeat_conviction,
        "defense_network_convergence": _defense_network_convergence,
    }
    for nr in db.load_networks()["rules"]:
        fn = network_rules.get(nr.get("signal"))
        if not fn or nr.get("status") != "active":
            continue
        for row in fn(con, week, nr):
            theme, sector, rule, evidence, strength = row[:5]
            entity_id = row[5] if len(row) > 5 else None
            con.execute(
                """INSERT INTO themes (run_week, theme, sector, rule, evidence,
                     strength, entity_id) VALUES (?,?,?,?,?,?,?)""",
                (week, theme, sector, rule, evidence, strength, entity_id))
            fired.append(theme)
    con.commit()
    con.close()
    return {"fired": fired}


if __name__ == "__main__":
    import sys
    print(run(sys.argv[1]))
