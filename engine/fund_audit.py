"""Verification pass for the Fund Tracker (§7). Trust is the product.

Same discipline as Section 2's audit: it runs every cycle, writes a readable
report into the run directory, and returns a verdict that GATES delivery. Errors
block the payload; warnings ship but are listed on it.

The checks are chosen around the specific ways this dataset could lie:

  F0  a row with no source, or a source that is a search query rather than a
      document. A query cites nothing.
  F1  value/share unit anomaly — the 13F thousands-vs-dollars trap. A book scaled
      by 1000 looks entirely plausible until you compare it to reality. Applied to
      COMMON only: a warrant or a right legitimately trades at a fraction of a
      cent, and holding those to an equity price band produces false alarms that
      teach the reader to ignore the check.
  F2  a holder owning more than 100% of a class. Impossible; means a units or
      rollup error.
  F3  negative shares, negative value or a negative weight.
  F4  an orphan position whose parent is not a tracked manager.
  F5  a watch-only manager with 13F positions — the §B3 carve-out breached.
  F6  a short attributed to a fund from a source that is not a NAMED register.
      Presenting FINRA/COT aggregates as a fund's position is the single most
      damaging thing this section could do.
  F7  a current-year or YTD return not flagged provisional.
  F8  a quant manager present at all.
  F9  a conviction score attached to a put.
"""

import json
from datetime import date

from . import db, fund

NAMED_REGISTERS = {"ESMA", "BaFin", "AMF", "FCA"}
SEARCH_URL_HINTS = ("efts.sec.gov/LATEST/search-index", "cgi-bin/browse-edgar",
                    "/cgi-bin/srqsb", "google.com/search", "?q=")


def _is_search_url(u) -> bool:
    return bool(u) and any(h in u for h in SEARCH_URL_HINTS)


def run(con, run_id: str) -> dict:
    cfg = fund.load_conviction_cfg()["audit"]
    errors, warnings, stats = [], [], {}

    # F0 — sourcing
    for table, key in (("fund_positions", "issuer"), ("fund_stakes", "issuer"),
                       ("fund_shorts", "issuer"), ("fund_events", "headline")):
        col = "source_doc" if table == "fund_vehicle_holdings" else "source_url"
        for r in con.execute(f"SELECT rowid, {key} k, {col} u FROM {table} "
                             f"WHERE {col} IS NULL OR {col}=''"):
            errors.append(f"F0 {table}#{r['rowid']} ({r['k']}): no source URL")
        for r in con.execute(f"SELECT rowid, {key} k, {col} u FROM {table} "
                             f"WHERE {col} LIKE '%q=%' OR {col} LIKE '%browse-edgar%'"):
            if _is_search_url(r["u"]):
                errors.append(f"F0 {table}#{r['rowid']} ({r['k']}): source is a "
                              f"search query, not a document")
    for r in con.execute("SELECT rowid, name FROM fund_vehicle_holdings "
                         "WHERE source_doc IS NULL OR source_doc=''"):
        errors.append(f"F0 fund_vehicle_holdings#{r['rowid']} ({r['name']}): no source_doc")

    # F1 — units
    lo, hi = cfg["implied_price_min"], cfg["implied_price_max"]
    for r in con.execute(
            """SELECT parent_cik, period, issuer, shares, value_usd,
                      value_usd/NULLIF(shares,0) px, source_form
               FROM fund_positions
               WHERE share_type='SH' AND shares>0 AND value_usd>0
                 AND instrument='common'
                 AND (value_usd/shares < ? OR value_usd/shares > ?)""", (lo, hi)):
        errors.append(f"F1 {r['parent_cik']} {r['period']} {r['issuer']}: implied "
                      f"price ${r['px']:.4f} outside [{lo}, {hi}] — value units are "
                      f"probably mis-scaled ({r['source_form']})")
    for r in con.execute("""SELECT parent_cik, period, book_value_usd FROM fund_book_stats
                            WHERE book_value_usd > ?""", (cfg["max_book_value_usd"],)):
        errors.append(f"F1 {r['parent_cik']} {r['period']}: book value "
                      f"${r['book_value_usd']:,.0f} exceeds the sanity ceiling")

    # F2 — impossible ownership. Three things this comparison has to get right or
    # it manufactures errors out of perfectly good data:
    #   * COMMON only. An option line reports the notional underlying share count;
    #     holding calls over 40m shares is not owning 40m shares.
    #   * dates close together. A 2024 position against a 2026 share count spans
    #     reverse splits and issuance — Ginkgo's 1-for-40 makes an old position look
    #     like 300% of the company.
    #   * a plausible denominator, which is enforced upstream at pull time.
    for r in con.execute(
            """SELECT p.parent_cik, p.issuer, p.period, p.shares, o.shares total,
                      o.as_of
               FROM fund_positions p
               JOIN fund_cusip_map c ON c.cusip = p.cusip
               JOIN fund_shares_outstanding o ON o.issuer_cik = c.issuer_cik
               WHERE o.shares > 0 AND p.instrument = 'common'
                 AND ABS(julianday(o.as_of) - julianday(p.period)) <= 200
                 AND p.shares > o.shares * ?""",
            (cfg["max_pct_of_shares_outstanding"],)):
        errors.append(f"F2 {r['parent_cik']} {r['issuer']} ({r['period']}): holds "
                      f"{r['shares']:,.0f} of {r['total']:,.0f} shares outstanding "
                      f"as of {r['as_of']} (>100%)")
    for r in con.execute("SELECT rowid, issuer, pct FROM fund_shorts WHERE pct > 100"):
        errors.append(f"F2 fund_shorts#{r['rowid']} {r['issuer']}: {r['pct']}% short")

    # F3 — impossible arithmetic
    for r in con.execute("""SELECT rowid, issuer, shares, value_usd FROM fund_positions
                            WHERE shares < 0 OR value_usd < 0"""):
        errors.append(f"F3 fund_positions#{r['rowid']} {r['issuer']}: negative "
                      f"shares/value")
    for r in con.execute("SELECT rowid, issuer, weight FROM fund_position_deltas "
                         "WHERE weight < 0"):
        errors.append(f"F3 fund_position_deltas#{r['rowid']} {r['issuer']}: negative weight")

    # F4 — orphans
    for r in con.execute(
            """SELECT DISTINCT p.parent_cik FROM fund_positions p
               LEFT JOIN fund_managers m ON m.cik = p.parent_cik
               WHERE m.cik IS NULL"""):
        errors.append(f"F4 positions under {r['parent_cik']}, which is not a "
                      f"tracked manager")

    # F5 — the §B3 carve-out
    for r in con.execute(
            """SELECT m.slug, COUNT(*) n FROM fund_positions p
               JOIN fund_managers m ON m.cik = p.parent_cik
               WHERE m.manager_class='watch_only' AND p.source_form LIKE '13F%'
               GROUP BY m.slug"""):
        errors.append(f"F5 watch-only manager {r['slug']} has {r['n']} 13F positions "
                      f"— the market-making carve-out has been breached")

    # F6 — never attribute an aggregate to a fund
    for r in con.execute("SELECT DISTINCT register FROM fund_shorts"):
        if r["register"] not in NAMED_REGISTERS:
            errors.append(f"F6 fund_shorts contains register '{r['register']}', which "
                          f"is not a NAMED register — aggregate short interest must "
                          f"never be attributed to a fund")

    # F7 — provisional discipline
    cur_fy = str(date.today().year)
    for r in con.execute(
            """SELECT rowid, parent_cik, fiscal_year FROM fund_track_record
               WHERE (fiscal_year = ? OR upper(fiscal_year) LIKE 'YTD%')
                 AND is_provisional = 0""", (cur_fy,)):
        errors.append(f"F7 track record {r['parent_cik']} {r['fiscal_year']}: "
                      f"current-year figure not flagged provisional")
    for r in con.execute("SELECT rowid, parent_cik FROM fund_track_record "
                         "WHERE source_url IS NULL OR source_url=''"):
        errors.append(f"F7 track record {r['parent_cik']}: no source_url")

    # F8 / F9
    for r in con.execute("SELECT slug FROM fund_managers WHERE style_tag='quant'"):
        errors.append(f"F8 quant manager {r['slug']} present — quant filings are "
                      f"model output and must not be ingested")
    for r in con.execute("""SELECT rowid, issuer FROM fund_position_deltas
                            WHERE instrument='put' AND conviction_score IS NOT NULL"""):
        errors.append(f"F9 put on {r['issuer']} carries a long conviction score — a "
                      f"put is a hedge, not a long bet")

    # ── warnings ─────────────────────────────────────────────────────────────
    for r in con.execute(
            """SELECT form_type, parse_status, COUNT(*) n, MIN(parse_note) note
               FROM fund_filings WHERE parse_status IN ('error','unsupported')
               GROUP BY form_type, parse_status"""):
        warnings.append(f"W1 {r['n']} {r['form_type']} filings {r['parse_status']}: "
                        f"{r['note']}")
    unmapped = con.execute("SELECT COUNT(*) c, SUM(seen_count) s "
                           "FROM fund_cusip_unmapped").fetchone()
    if unmapped["c"]:
        warnings.append(f"W2 {unmapped['c']} CUSIPs unmapped to a ticker "
                        f"({unmapped['s']} sightings) — positions kept, ticker blank")
    for r in con.execute("""SELECT parent_cik, issuer, note FROM fund_crosschecks
                            WHERE status='discrepancy'"""):
        warnings.append(f"W3 13F/DEF 14A disagree — {r['parent_cik']} {r['issuer']}: "
                        f"{r['note']}")
    for r in con.execute("""SELECT source, consecutive_failures, last_error
                            FROM fund_source_health WHERE consecutive_failures > 0"""):
        warnings.append(f"W4 source '{r['source']}' failing "
                        f"({r['consecutive_failures']}x): {r['last_error']}")
    for r in con.execute(
            """SELECT m.slug, m.manager_class FROM fund_managers m
               WHERE m.active=1 AND m.manager_class != 'watch_only'
                 AND NOT EXISTS (SELECT 1 FROM fund_positions p WHERE p.parent_cik=m.cik)
                 AND NOT EXISTS (SELECT 1 FROM fund_events e WHERE e.parent_cik=m.cik)"""):
        warnings.append(f"W5 {r['slug']} has no positions and no events — either it "
                        f"has not been polled yet, or an ingest is silently failing")
    for r in con.execute(
            """SELECT m.slug, MAX(b.latency_days) lat FROM fund_book_stats b
               JOIN fund_managers m ON m.cik=b.parent_cik
               WHERE b.period=(SELECT MAX(period) FROM fund_book_stats b2
                               WHERE b2.parent_cik=b.parent_cik)
               GROUP BY m.slug HAVING lat > 100"""):
        warnings.append(f"W6 {r['slug']}: latest book is {r['lat']}d stale — the "
                        f"fast layer is carrying this manager, not the 13F")
    for r in con.execute("""SELECT slug FROM fund_managers
                            WHERE manager_class='sparse_coverage'"""):
        warnings.append(f"W7 {r['slug']} is sparse_coverage: a thin record means "
                        f"'below disclosure thresholds', NOT 'low activity'. The UI "
                        f"must render the coverage as intentionally incomplete.")

    # ── stats ────────────────────────────────────────────────────────────────
    for name, q in (
            ("managers", "SELECT COUNT(*) c FROM fund_managers WHERE active=1"),
            ("watch_only", "SELECT COUNT(*) c FROM fund_managers WHERE manager_class='watch_only'"),
            ("filings", "SELECT COUNT(*) c FROM fund_filings"),
            ("positions", "SELECT COUNT(*) c FROM fund_positions"),
            ("deltas", "SELECT COUNT(*) c FROM fund_position_deltas"),
            ("stakes", "SELECT COUNT(*) c FROM fund_stakes"),
            ("insider_txns", "SELECT COUNT(*) c FROM fund_insider_txns"),
            ("shorts_current", "SELECT COUNT(*) c FROM fund_shorts WHERE is_current=1"),
            ("events", "SELECT COUNT(*) c FROM fund_events"),
            ("watch_triggers", "SELECT COUNT(*) c FROM fund_watch_triggers"),
            ("cusips_mapped", "SELECT COUNT(*) c FROM fund_cusip_map WHERE ticker IS NOT NULL"),
            ("cusips_unmapped", "SELECT COUNT(*) c FROM fund_cusip_unmapped"),
            ("parse_failures", "SELECT COUNT(*) c FROM fund_filings WHERE parse_status IN ('error','unsupported')")):
        stats[name] = con.execute(q).fetchone()["c"]

    verdict = {"generated": date.today().isoformat(), "run_id": run_id,
               "passed": not errors, "errors": errors, "warnings": warnings,
               "stats": stats}
    _report(run_id, verdict)
    fund.log_run(con, run_id, "audit", "error" if errors else "ok",
                 f"{len(errors)} errors, {len(warnings)} warnings", stats)
    return verdict


def _report(run_id: str, v: dict) -> None:
    d = db.RUNS_DIR / run_id
    d.mkdir(parents=True, exist_ok=True)
    L = [f"# Fund Tracker audit — {v['generated']} ({run_id})", "",
         f"**{'PASS' if v['passed'] else 'FAIL'}** — {len(v['errors'])} errors, "
         f"{len(v['warnings'])} warnings", "", "## Counts", ""]
    L += [f"- {k}: {n}" for k, n in v["stats"].items()]
    L += ["", f"## Errors ({len(v['errors'])}) — these block delivery", ""]
    L += [f"- {e}" for e in v["errors"]] or ["_none_"]
    L += ["", f"## Warnings ({len(v['warnings'])}) — shipped, but surfaced", ""]
    L += [f"- {w}" for w in v["warnings"]] or ["_none_"]
    (d / "fund_audit_report.md").write_text("\n".join(L) + "\n")
