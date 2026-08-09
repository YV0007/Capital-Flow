"""Audit: the pre-deployment verification pass of spec §6.

Trust is the product — a few visible errors and the user distrusts the whole
dataset. This pass runs every cycle (not one-time), writes a human-readable
audit report into the run directory, and returns a verdict the pipeline uses
to GATE delivery: errors block --deliver/--push; warnings ship but are listed.

ERRORS (block deployment):
  E1  confirmed event (verified / verified_alpha) with no source_url
  E2  event where this allocator's slice exceeds the full round
      (amount_usd > round_total_usd)
  E3  event missing its confidence grade (reliability/credibility/score)
  E4  track-record row with no source_url (unsourced numbers must not ship)
  E5  current-fiscal-year / YTD track-record row not flagged provisional

WARNINGS (ship, but surfaced):
  W1  sector outside the canonical taxonomy
  W2  amount equals valuation on a >= $1B event — possible valuation/raise
      conflation (data-hygiene rule: never conflate valuation with cash raised)
  W3  key/core allocator with events but no canonical profile (§5 coverage gap)
  W4  profile strategy text without strategy_source_url attribution
  W5  verified event sourced from tier >= 4 (weak source for a 'verified' claim)
"""

import json
from datetime import date

from . import db


def _check_events(con, sectors, errors, warnings):
    rows = con.execute("""SELECT e.*, a.name AS allocator FROM events e
                          JOIN allocators a ON a.id = e.allocator_id""").fetchall()
    for e in rows:
        who = f"event #{e['id']} {e['allocator']} -> {e['target']}"
        if e["status"] in ("verified", "verified_alpha") and not e["source_url"]:
            errors.append(f"E1 {who}: confirmed but no source_url")
        if (e["amount_usd"] and e["round_total_usd"]
                and e["amount_usd"] > e["round_total_usd"] * 1.001):
            errors.append(f"E2 {who}: slice ${e['amount_usd']:,.0f} exceeds round "
                          f"total ${e['round_total_usd']:,.0f}")
        if e["confidence_score"] is None or not e["source_reliability"]:
            errors.append(f"E3 {who}: missing confidence grade")
        if sectors and e["sector"] not in sectors:
            warnings.append(f"W1 {who}: sector '{e['sector']}' not canonical")
        if (e["amount_usd"] and e["valuation_usd"]
                and e["amount_usd"] == e["valuation_usd"] and e["amount_usd"] >= 1e9):
            warnings.append(f"W2 {who}: amount == valuation "
                            f"(${e['amount_usd']:,.0f}) — check conflation")
        if e["status"] == "verified" and e["source_tier"] >= 4:
            warnings.append(f"W5 {who}: 'verified' on tier-{e['source_tier']} source")
    return len(rows)


def _check_track_records(con, errors):
    cur_fy = str(date.today().year)
    rows = con.execute("""SELECT t.*, a.name AS allocator FROM track_records t
                          JOIN allocators a ON a.id = t.allocator_id""").fetchall()
    for t in rows:
        who = f"track_record {t['allocator']} {t['fiscal_year']}/{t['metric']}"
        if not t["source_url"]:
            errors.append(f"E4 {who}: no source_url")
        if ((t["fiscal_year"].upper().startswith("YTD") or t["fiscal_year"] == cur_fy)
                and not t["provisional"]):
            errors.append(f"E5 {who}: current-year figure not flagged provisional")
    return len(rows)


def _check_profiles(con, warnings):
    gaps = con.execute(
        """SELECT a.name FROM allocators a
           WHERE a.tier IN ('key','core')
             AND EXISTS (SELECT 1 FROM events e WHERE e.allocator_id = a.id)
             AND NOT EXISTS (SELECT 1 FROM allocator_profiles p
                             WHERE p.allocator_id = a.id)
           ORDER BY a.name""").fetchall()
    for g in gaps:
        warnings.append(f"W3 {g['name']}: key allocator with events but no profile")
    noattr = con.execute(
        """SELECT a.name FROM allocator_profiles p JOIN allocators a
             ON a.id = p.allocator_id
           WHERE p.strategy IS NOT NULL AND p.strategy_source_url IS NULL""").fetchall()
    for n in noattr:
        warnings.append(f"W4 {n['name']}: strategy without source attribution")
    return con.execute("SELECT COUNT(*) c FROM allocator_profiles").fetchone()["c"]


def _stats(con):
    s = {r["status"]: r["c"] for r in con.execute(
        "SELECT status, COUNT(*) c FROM events GROUP BY status").fetchall()}
    src = con.execute("SELECT COUNT(*) c FROM events WHERE source_url IS NOT NULL"
                      ).fetchone()["c"]
    total = sum(s.values()) or 1
    return {"events": sum(s.values()), "by_status": s,
            "source_url_coverage": round(src / total, 3),
            "estimated_amounts": con.execute(
                "SELECT COUNT(*) c FROM events WHERE amount_estimated=1"
            ).fetchone()["c"],
            "provisional_track_rows": con.execute(
                "SELECT COUNT(*) c FROM track_records WHERE provisional=1"
            ).fetchone()["c"]}


def run(week: str) -> dict:
    con = db.connect()
    cfg = db.load_config()
    errors, warnings = [], []
    n_events = _check_events(con, cfg["sectors"], errors, warnings)
    n_tr = _check_track_records(con, errors)
    n_prof = _check_profiles(con, warnings)
    stats = _stats(con)
    con.close()

    verdict = {"generated": date.today().isoformat(), "week": week,
               "checked": {"events": n_events, "track_records": n_tr,
                           "profiles": n_prof},
               "errors": errors, "warnings": warnings, "stats": stats,
               "passed": not errors}

    out = db.RUNS_DIR / week
    out.mkdir(parents=True, exist_ok=True)
    L = [f"# Audit report — {week} ({verdict['generated']})", "",
         f"**Verdict: {'PASS' if verdict['passed'] else 'FAIL — delivery blocked'}**",
         f"Checked {n_events} events, {n_tr} track-record rows, {n_prof} profiles.", "",
         f"## Errors ({len(errors)})"]
    L += [f"- {e}" for e in errors] or ["_none_"]
    L += ["", f"## Warnings ({len(warnings)})"]
    L += [f"- {w}" for w in warnings] or ["_none_"]
    L += ["", "## Stats", "```json", json.dumps(stats, indent=2), "```", ""]
    (out / "audit_report.md").write_text("\n".join(L))
    return verdict


if __name__ == "__main__":
    import sys
    v = run(sys.argv[1])
    print(f"audit {v['week']}: {'PASS' if v['passed'] else 'FAIL'} — "
          f"{len(v['errors'])} errors, {len(v['warnings'])} warnings")
    for e in v["errors"]:
        print("  ERR ", e)
