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
           WHERE a.tier = ? AND e.disclosed_date >= date('now', ?)
                 AND e.status IN ('verified','verified_alpha')
           GROUP BY e.sector
           HAVING inv >= ?""",
        (p.get("allocator_tier", "key"), win, p.get("min_allocators", 5)),
    ).fetchall()
    out = []
    for r in rows:
        ids = [int(x) for x in r["ids"].split(",")]
        out.append((f"{r['sector']}: {r['inv']} key allocators in {p.get('window_days',30)}d",
                    r["sector"], "sector_swarm", json.dumps(ids), float(r["inv"])))
    return out


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
           WHERE a.tier = ?""", (p.get("allocator_tier", "key"),)).fetchall()
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
                            "first_entry", json.dumps(ids), 1.0))
    return out


RULES = {
    "sector_swarm": _sector_swarm,
    "capital_acceleration": _capital_acceleration,
    "first_entry": _first_entry,
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
        for theme, sector, rule, evidence, strength in fn(con, week, r):
            con.execute(
                """INSERT INTO themes (run_week, theme, sector, rule, evidence, strength)
                   VALUES (?,?,?,?,?,?)""",
                (week, theme, sector, rule, evidence, strength))
            fired.append(theme)
    con.commit()
    con.close()
    return {"fired": fired}


if __name__ == "__main__":
    import sys
    print(run(sys.argv[1]))
