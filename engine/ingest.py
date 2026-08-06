"""Ingest: agent CSVs -> validate -> dedupe -> SQLite.

Reads runs/<week>/<agent>/{verified,candidate}_events.csv + source_log.csv,
validates each row against the schema, resolves allocator names to ids (deriving
class from the agent when the CSV omits it), and upserts into the events table.
The UNIQUE(allocator_id, target, event_type, disclosed_date) constraint is the
dedupe guard; a duplicate is merged keeping the stronger status and better tier.
"""

import csv
import sqlite3
import sys

from . import db


def _num(v):
    v = (v or "").strip().replace(",", "").replace("$", "")
    if v == "":
        return None
    return float(v)


def _validate(row: dict, agent: str, sectors: set):
    """Return (clean|None, class|None, errors, warnings)."""
    errors, warnings = [], []
    disclosed = (row.get("disclosed_date") or "").strip()
    allocator = (row.get("allocator") or "").strip()
    target = (row.get("target") or "").strip()
    sector = (row.get("sector") or "").strip()
    etype = (row.get("event_type") or "").strip()
    tier_raw = (row.get("source_tier") or "").strip()

    for field, val in [("disclosed_date", disclosed), ("allocator", allocator),
                       ("target", target), ("sector", sector), ("event_type", etype)]:
        if not val:
            errors.append(f"missing {field}")
    if etype and etype not in db.EVENT_TYPES:
        errors.append(f"bad event_type '{etype}'")
    try:
        tier = int(tier_raw)
        if not 1 <= tier <= 5:
            errors.append(f"source_tier {tier} out of range")
    except ValueError:
        errors.append(f"bad source_tier '{tier_raw}'")
        tier = None

    status = (row.get("status") or "candidate").strip() or "candidate"
    if status not in db.STATUSES:
        errors.append(f"bad status '{status}'")
    ttype = (row.get("target_type") or "").strip() or None
    if ttype and ttype not in db.TARGET_TYPES:
        errors.append(f"bad target_type '{ttype}'")

    try:
        amount = _num(row.get("amount_usd"))
    except ValueError:
        errors.append(f"bad amount_usd '{row.get('amount_usd')}'")
        amount = None

    cls = (row.get("allocator_class") or "").strip() or db.AGENT_CLASS.get(agent)
    if not cls:
        errors.append(f"no allocator_class (agent '{agent}' can't derive one)")
    elif cls not in db.CLASSES:
        errors.append(f"bad allocator_class '{cls}'")

    if sectors and sector and sector not in sectors:
        warnings.append(f"sector '{sector}' not in canonical taxonomy")

    if errors:
        return None, None, errors, warnings

    clean = {
        "event_date": (row.get("event_date") or "").strip() or None,
        "disclosed_date": disclosed,
        "target": target, "target_type": ttype, "sector": sector,
        "subsector": (row.get("subsector") or "").strip() or None,
        "event_type": etype, "amount_usd": amount,
        "amount_estimated": 1 if (row.get("amount_estimated") or "").strip() in ("1", "true", "yes") else 0,
        "status": status, "source_tier": tier,
        "source_url": (row.get("source_url") or "").strip() or None,
        "notes": (row.get("notes") or "").strip() or None,
        "allocator": allocator,
    }
    return clean, cls, [], warnings


def _upsert_event(con, e: dict, allocator_id: int, week: str, agent: str):
    """Insert; on dedupe conflict keep the stronger status / better (lower) tier.
    Returns 'inserted' | 'updated' | 'unchanged'."""
    try:
        con.execute(
            """INSERT INTO events (event_date, disclosed_date, allocator_id, target,
                 target_type, sector, subsector, event_type, amount_usd, amount_estimated,
                 status, source_tier, source_url, run_week, agent, notes)
               VALUES (:event_date,:disclosed_date,:aid,:target,:target_type,:sector,
                 :subsector,:event_type,:amount_usd,:amount_estimated,:status,:source_tier,
                 :source_url,:week,:agent,:notes)""",
            {**e, "aid": allocator_id, "week": week, "agent": agent},
        )
        return "inserted"
    except sqlite3.IntegrityError:
        cur = con.execute(
            """SELECT id, status, source_tier FROM events
               WHERE allocator_id=? AND target=? AND event_type=? AND disclosed_date=?""",
            (allocator_id, e["target"], e["event_type"], e["disclosed_date"]),
        ).fetchone()
        better_status = db.STATUS_RANK[e["status"]] > db.STATUS_RANK[cur["status"]]
        better_tier = e["source_tier"] < cur["source_tier"]
        if better_status or better_tier:
            con.execute(
                """UPDATE events SET
                     status = CASE WHEN ? THEN ? ELSE status END,
                     source_tier = MIN(source_tier, ?),
                     amount_usd = COALESCE(amount_usd, ?),
                     source_url = COALESCE(source_url, ?)
                   WHERE id = ?""",
                (better_status, e["status"], e["source_tier"], e["amount_usd"],
                 e["source_url"], cur["id"]),
            )
            return "updated"
        return "unchanged"


def _ingest_source_log(con, week: str, agent: str, path):
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            con.execute(
                """INSERT INTO source_log (run_week, agent, source_url, source_tier, yielded)
                   VALUES (?,?,?,?,?)""",
                (week, agent, (row.get("source_url") or row.get("url") or "").strip(),
                 int(row["source_tier"]) if (row.get("source_tier") or "").strip().isdigit() else None,
                 1 if (row.get("yielded") or "").strip() in ("1", "true", "yes") else 0),
            )


def ingest_week(week: str) -> dict:
    """Load all agent outputs for a run week (e.g. '2026-W32'). Returns a summary."""
    con = db.connect()
    cfg = db.load_config()
    db.sync_allocators(con, cfg)

    week_dir = db.RUNS_DIR / week
    stats = {"inserted": 0, "updated": 0, "unchanged": 0, "skipped": 0, "warnings": 0}
    problems = []
    if not week_dir.is_dir():
        raise FileNotFoundError(f"no run directory: {week_dir}")

    for agent_dir in sorted(p for p in week_dir.iterdir() if p.is_dir()):
        agent = agent_dir.name
        for fname in ("verified_events.csv", "candidate_events.csv"):
            fpath = agent_dir / fname
            if not fpath.exists():
                continue
            with fpath.open(newline="") as f:
                for i, row in enumerate(csv.DictReader(f), start=2):
                    clean, cls, errs, warns = _validate(row, agent, cfg["sectors"])
                    stats["warnings"] += len(warns)
                    for w in warns:
                        problems.append(f"{agent}/{fname}:{i} WARN {w}")
                    if errs:
                        stats["skipped"] += 1
                        problems.append(f"{agent}/{fname}:{i} SKIP {'; '.join(errs)}")
                        continue
                    aid = db.get_or_create_allocator(con, clean.pop("allocator"), cls)
                    stats[_upsert_event(con, clean, aid, week, agent)] += 1
        slog = agent_dir / "source_log.csv"
        if slog.exists():
            _ingest_source_log(con, week, agent, slog)

    con.commit()
    con.close()
    stats["problems"] = problems
    return stats


if __name__ == "__main__":
    s = ingest_week(sys.argv[1])
    print(f"ingest {sys.argv[1]}: +{s['inserted']} new, {s['updated']} updated, "
          f"{s['unchanged']} unchanged, {s['skipped']} skipped, {s['warnings']} warnings")
    for p in s["problems"]:
        print("  ", p)
