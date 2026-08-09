"""Profiles: allocator-profiler JSON batches -> allocator_profiles + track_records.

Reads runs/<week>/profiles/<batch>/profiles.json (see agents/allocator-profiler.md
for the contract), validates each object, resolves the allocator name through the
alias table, and upserts. Trust rules enforced here, not just requested from agents:
  - a track-record row without a source_url is dropped (unsourced numbers don't ship);
  - YTD rows and current-fiscal-year rows are forced provisional=1;
  - a non-empty strategy without strategy_source_url is kept but flagged as a warning
    (the audit pass surfaces it).
Idempotent per allocator: the latest ingest wins (PRIMARY KEY upsert); track-record
rows upsert on (allocator, fiscal_year, metric).
"""

import json
import sys
from datetime import date

from . import db

METRICS = {
    "stock_total_return_pct", "fund_net_return_pct", "fund_irr_pct", "tvpi",
    "reported_return_pct", "aum_usd_bn", "hit_rate_pct", "moic",
}

TEXT_FIELDS = ("background", "focus", "style", "thesis",
               "latest_investments_summary", "strategy", "strategy_source_url",
               "track_record_note")


def _clean_text(v, limit=2000):
    v = (v or "").strip()
    return v[:limit] or None


def _validate_tr_row(r, warnings, who):
    fy = str(r.get("fiscal_year") or "").strip()
    metric = (r.get("metric") or "").strip()
    if not fy or not metric:
        warnings.append(f"{who}: track_record row missing fiscal_year/metric — dropped")
        return None
    if metric not in METRICS:
        warnings.append(f"{who}: unknown metric '{metric}' — dropped")
        return None
    url = (r.get("source_url") or "").strip()
    if not url:
        warnings.append(f"{who}: {fy}/{metric} has no source_url — dropped (unsourced)")
        return None
    try:
        value = float(r["value"]) if r.get("value") is not None else None
    except (TypeError, ValueError):
        warnings.append(f"{who}: {fy}/{metric} non-numeric value — dropped")
        return None
    provisional = 1 if r.get("provisional") in (1, "1", True) else 0
    # Enforce the honesty flag: YTD / current fiscal year is provisional by definition.
    cur_fy = str(date.today().year)
    if fy.upper().startswith("YTD") or fy == cur_fy:
        provisional = 1
    tier = r.get("source_tier")
    tier = int(tier) if str(tier or "").strip().isdigit() and 1 <= int(tier) <= 5 else None
    return {
        "fiscal_year": fy, "metric": metric, "value": value,
        "unit": (r.get("unit") or "").strip() or None,
        "provisional": provisional, "source_tier": tier, "source_url": url,
        "notes": _clean_text(r.get("notes"), 500),
    }


def ingest_week(week: str) -> dict:
    """Load all profile batches for a run week. Returns a summary dict."""
    con = db.connect()
    prof_dir = db.RUNS_DIR / week / "profiles"
    stats = {"profiles": 0, "track_rows": 0, "skipped": 0}
    warnings = []
    if not prof_dir.is_dir():
        stats["warnings"] = warnings
        con.close()
        return stats

    for batch_dir in sorted(p for p in prof_dir.iterdir() if p.is_dir()):
        fpath = batch_dir / "profiles.json"
        if not fpath.exists():
            continue
        try:
            objs = json.loads(fpath.read_text())
        except json.JSONDecodeError as e:
            warnings.append(f"{batch_dir.name}/profiles.json: invalid JSON ({e}) — batch skipped")
            continue
        if not isinstance(objs, list):
            warnings.append(f"{batch_dir.name}/profiles.json: not a JSON array — batch skipped")
            continue
        for o in objs:
            name = (o.get("allocator") or "").strip()
            if not name:
                stats["skipped"] += 1
                warnings.append(f"{batch_dir.name}: object with no allocator name — skipped")
                continue
            canonical = db.resolve_name(name)
            row = con.execute("SELECT id FROM allocators WHERE name = ?",
                              (canonical,)).fetchone()
            if not row:
                stats["skipped"] += 1
                warnings.append(f"{batch_dir.name}: '{name}' not in allocators — skipped "
                                f"(profiles never create entities)")
                continue
            aid = row["id"]
            t = {f: _clean_text(o.get(f)) for f in TEXT_FIELDS}
            if t["strategy"] and not t["strategy_source_url"]:
                warnings.append(f"{canonical}: strategy has no strategy_source_url")
            sources = o.get("sources") or []
            sources = [s for s in sources if isinstance(s, str) and s.startswith("http")]
            as_of = (o.get("as_of") or "").strip() or date.today().isoformat()
            con.execute(
                """INSERT INTO allocator_profiles
                     (allocator_id, background, focus, style, thesis, latest_summary,
                      strategy, strategy_source_url, sources, track_record_note,
                      as_of, run_week, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
                   ON CONFLICT(allocator_id) DO UPDATE SET
                     background=excluded.background, focus=excluded.focus,
                     style=excluded.style, thesis=excluded.thesis,
                     latest_summary=excluded.latest_summary, strategy=excluded.strategy,
                     strategy_source_url=excluded.strategy_source_url,
                     sources=excluded.sources,
                     track_record_note=excluded.track_record_note,
                     as_of=excluded.as_of, run_week=excluded.run_week,
                     updated_at=datetime('now')""",
                (aid, t["background"], t["focus"], t["style"], t["thesis"],
                 t["latest_investments_summary"], t["strategy"],
                 t["strategy_source_url"], json.dumps(sources),
                 t["track_record_note"], as_of, week))
            stats["profiles"] += 1
            for r in (o.get("track_record") or []):
                tr = _validate_tr_row(r, warnings, canonical)
                if not tr:
                    continue
                con.execute(
                    """INSERT INTO track_records
                         (allocator_id, fiscal_year, metric, value, unit, provisional,
                          source_tier, source_url, notes, run_week)
                       VALUES (?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(allocator_id, fiscal_year, metric) DO UPDATE SET
                         value=excluded.value, unit=excluded.unit,
                         provisional=excluded.provisional,
                         source_tier=excluded.source_tier,
                         source_url=excluded.source_url, notes=excluded.notes,
                         run_week=excluded.run_week""",
                    (aid, tr["fiscal_year"], tr["metric"], tr["value"], tr["unit"],
                     tr["provisional"], tr["source_tier"], tr["source_url"],
                     tr["notes"], week))
                stats["track_rows"] += 1
    con.commit()
    con.close()
    stats["warnings"] = warnings
    return stats


if __name__ == "__main__":
    s = ingest_week(sys.argv[1])
    print(f"profiles {sys.argv[1]}: {s['profiles']} profiles, {s['track_rows']} "
          f"track-record rows, {s['skipped']} skipped")
    for w in s.get("warnings", []):
        print("  WARN", w)
