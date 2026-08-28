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

Depth is enforced HERE, not merely requested of the agent. agents/holdings-profiler.md
has always said "at least the top 25 per entity"; Coatue arrived with 16 of 250 and
nothing objected, because the only question ever asked was whether a fund had ANY
holdings. A portfolio that comes back under the floor while its own holdings_count
says more exist is recorded as a SHORTFALL — it stays queued for the next run and
the audit says so.
"""

import json
import sys
from datetime import date

from . import db

# agents/holdings-profiler.md: "ship at least the top 25 per entity".
MIN_HOLDINGS = 25


def _stake(v):
    if v is None:
        return None
    return str(v).strip() or None


def ingest_week(week: str) -> dict:
    con = db.connect()
    hdir = db.RUNS_DIR / week / "holdings"
    stats = {"entities": 0, "holdings": 0, "skipped": 0, "shortfalls": [],
             "batches_requested": 0, "batches_delivered": 0, "batches_missing": []}
    warnings = []
    if not hdir.is_dir():
        stats["warnings"] = warnings
        con.close()
        return stats

    # Reconcile what was ASKED for against what came back. A batch directory with
    # an input and no holdings.json is not a quiet batch — it is an agent that
    # never ran, and it has to be distinguishable from one that found nothing.
    for bd in sorted(p for p in hdir.iterdir() if p.is_dir()):
        if not (bd / "batch_entities.json").exists():
            continue
        stats["batches_requested"] += 1
        if (bd / "holdings.json").exists():
            stats["batches_delivered"] += 1
        else:
            stats["batches_missing"].append(bd.name)

    seen_entities = set()
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
            delivered_now = len(valid)
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

            # Under-delivery: fewer than the floor, while the entity's own true
            # total says more exist. Not an error — the data that did arrive is
            # good — but the entity stays on the queue instead of being counted done.
            short = delivered_now < MIN_HOLDINGS and count > delivered_now
            if short:
                stats["shortfalls"].append(
                    {"entity": canonical, "delivered": delivered_now,
                     "true_total": count})
                warnings.append(
                    f"{canonical}: {delivered_now} holdings delivered against a true "
                    f"total of {count} — under the {MIN_HOLDINGS} floor in "
                    f"agents/holdings-profiler.md; re-queued for the next run")
            con.execute(
                """UPDATE holdings_requests SET delivered=1, delivered_count=?,
                     shortfall=?, outcome='delivered', resolved_at=datetime('now')
                   WHERE period=? AND entity=?""",
                (delivered_now, int(short), week, canonical))
            seen_entities.add(canonical)

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
    # An entity whose batch DID come back but which is absent from the result was
    # researched and found to have no public disclosure of its holdings — an SPV
    # named only in a Form D, typically. That is a fact about the vehicle, not a
    # failure of the pipeline, and it must not escalate into an audit error the way
    # an un-run batch does.
    if stats["batches_requested"]:
        # Whether a batch RAN is the presence of its holdings.json, not whether any
        # entity came back in it. batch-6 returned a valid empty array — three SPVs
        # with genuinely nothing public — and treating that as "never ran" would
        # escalate an honest answer into an audit error.
        ran = {d.name for d in hdir.iterdir()
               if d.is_dir() and (d / "holdings.json").exists()}
        rows = con.execute(
            "SELECT entity, batch FROM holdings_requests WHERE period=? AND delivered=0",
            (week,)).fetchall()
        researched = [r["entity"] for r in rows if r["batch"] in ran]
        undisclosed = [r["entity"] for r in rows if r["batch"] not in ran]
        for e in researched:
            con.execute(
                """UPDATE holdings_requests SET outcome='no_disclosure',
                     resolved_at=datetime('now') WHERE period=? AND entity=?""",
                (week, e))
        for e in undisclosed:
            con.execute(
                "UPDATE holdings_requests SET outcome='not_run' WHERE period=? AND entity=?",
                (week, e))
        stats["no_disclosure"] = researched
        stats["not_run"] = undisclosed
    con.commit()
    con.close()
    stats["warnings"] = warnings
    return stats


def record_requests(con, period: str, entities: list) -> int:
    """Log what a run asked for, so a missing result is provably a missing STEP."""
    n = 0
    for e in entities:
        n += con.execute(
            """INSERT INTO holdings_requests
                 (period, entity, batch, reason, already_have, true_total)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(period, entity) DO UPDATE SET
                 batch=excluded.batch, reason=excluded.reason,
                 already_have=excluded.already_have, true_total=excluded.true_total""",
            (period, db.resolve_name(e["entity"]), e.get("batch"), e["reason"],
             e.get("already_have") or 0, e.get("known_true_total"))).rowcount
    con.commit()
    return n


def unresolved(con, periods: int = 2) -> list:
    """Entities asked for in the last N run periods that never came back.

    This is what turns W7 from a warning nobody reads into an error that stops a
    deploy: one miss is a bad week, two in a row is a broken step.
    """
    recent = [r["period"] for r in con.execute(
        "SELECT DISTINCT period FROM holdings_requests ORDER BY period DESC LIMIT ?",
        (periods,))]
    if len(recent) < periods:
        return []
    rows = con.execute(
        f"""SELECT entity, COUNT(*) misses FROM holdings_requests
            WHERE period IN ({','.join('?' * len(recent))}) AND delivered = 0
              AND COALESCE(outcome, 'not_run') != 'no_disclosure'
            GROUP BY entity HAVING misses >= ?""", recent + [periods]).fetchall()
    return [r["entity"] for r in rows]


if __name__ == "__main__":
    s = ingest_week(sys.argv[1])
    print(f"holdings {sys.argv[1]}: {s['entities']} portfolios, {s['holdings']} "
          f"holdings, {s['skipped']} skipped")
    for w in s.get("warnings", []):
        print("  WARN", w)
