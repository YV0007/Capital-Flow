"""The core loop: poll every tracked CIK's submissions JSON and diff it.

Cadence is TRIGGERED, not calendar-driven. The system reacts the moment a tracked
entity discloses — that is the whole answer to the latency problem. A calendar
poller would sit idle for six weeks and then wake up to a cluster of 13Fs it
already missed the first day of.

Idempotency is by accession number and nothing else. `fund_filings.accession_no`
is the primary key, so a re-run — of the same day, of the whole backfill, of a
crashed half-run — can never double-count. Every downstream stage keys off the
same accession.

Nothing is silently dropped. A filing from a CIK we cannot attribute goes to
fund_unmapped_ciks; a filing we cannot parse keeps parse_status/parse_note and
surfaces in the audit. A silently skipped filing is worse than a visible error.
"""

from datetime import date, datetime, timedelta

from . import fund, fund_sec

# Forms worth storing at all. Anything else is noise for this section — we are not
# building a general filing archive, we are watching a fixed universe disclose.
WANTED = set(fund.FORM_LATENCY) | {"3/A", "4/A", "5/A", "N-PORT-P/A", "424B3",
                                   "424B5", "DEFA14A", "13FCONP"}

# The 13F deadline cluster: 45 days after each quarter end. Around these dates the
# whole universe files within a few days of each other, so the poller widens its
# window rather than trusting a single daily pass to catch a same-day burst.
DEADLINES = ((2, 14), (5, 15), (8, 14), (11, 14))
DEADLINE_WINDOW_DAYS = 6


def in_deadline_window(today: date = None) -> bool:
    d = today or date.today()
    for m, day in DEADLINES:
        due = date(d.year, m, day)
        if -2 <= (d - due).days <= DEADLINE_WINDOW_DAYS:
            return True
    return False


def _store(con, f, parent_cik: str) -> int:
    """Insert one filing. Returns 1 if it is new to us, 0 if already seen."""
    cur = con.execute(
        """INSERT OR IGNORE INTO fund_filings
             (accession_no, cik, parent_cik, form_type, filed_at, period_of_report,
              items, primary_doc, source_url, parse_status)
           VALUES (?,?,?,?,?,?,?,?,?,'pending')""",
        (f["accession"], f["cik"], parent_cik, fund.norm_form(f["form"]),
         f["filed_at"], f["period"], f["items"], f["primary_doc"], f["url"]))
    return cur.rowcount


def poll_cik(con, cik: str, parent_cik: str, since: str = None,
             all_history: bool = False) -> dict:
    """Diff one CIK's submissions against what we already hold."""
    out = {"cik": cik, "seen": 0, "new": 0, "error": None}
    try:
        sub = fund_sec.submissions(cik, all_history=all_history)
    except (fund_sec.SECError, fund_sec.SECConfigError) as exc:
        out["error"] = str(exc)
        con.execute(
            """INSERT INTO fund_poller_state (cik, last_checked_at,
                                              consecutive_errors, last_error)
               VALUES (?,datetime('now'),1,?)
               ON CONFLICT(cik) DO UPDATE SET last_checked_at=datetime('now'),
                 consecutive_errors=fund_poller_state.consecutive_errors+1,
                 last_error=excluded.last_error""", (cik, str(exc)[:400]))
        con.commit()
        return out

    for f in sub["filings"]:
        if fund.norm_form(f["form"]) not in WANTED:
            continue
        if since and (f["filed_at"] or "") < since:
            continue
        out["seen"] += 1
        out["new"] += _store(con, f, parent_cik)

    top = sub["filings"][0] if sub["filings"] else {}
    con.execute(
        """INSERT INTO fund_poller_state
             (cik, last_accession, last_filed_date, last_checked_at,
              consecutive_errors, last_error)
           VALUES (?,?,?,datetime('now'),0,NULL)
           ON CONFLICT(cik) DO UPDATE SET last_accession=excluded.last_accession,
             last_filed_date=excluded.last_filed_date,
             last_checked_at=datetime('now'), consecutive_errors=0, last_error=NULL""",
        (cik, top.get("accession"), top.get("filed_at")))
    con.commit()
    return out


def poll(con, run_id: str, lookback_days: int = None, backfill: bool = False) -> dict:
    """One pass over the whole universe, watch-only managers included.

    backfill=True is the run-now path: walk full filing history so day one already
    has 8 quarters of 13Fs per fund. Deltas, persistence and conviction scores are
    meaningless on a single quarter, and standing up an empty system that becomes
    useful in six months is not a system.
    """
    ciks = fund.pollable_ciks(con)
    if backfill:
        since = min(fund.quarter_ends(
            (fund.load_managers().get("sec") or {}).get("backfill_quarters", 8) + 2))
    else:
        days = lookback_days or (30 if in_deadline_window() else 10)
        since = (date.today() - timedelta(days=days)).isoformat()

    stats = {"ciks": len(ciks), "new_filings": 0, "seen": 0, "errors": [],
             "since": since, "backfill": backfill,
             "deadline_window": in_deadline_window()}
    for row in ciks:
        r = poll_cik(con, row["cik"], row["parent_cik"], since=since,
                     all_history=backfill)
        stats["seen"] += r["seen"]
        stats["new_filings"] += r["new"]
        if r["error"]:
            stats["errors"].append(f"{row['manager']} [{row['cik']}]: {r['error']}")

    fund.mark_source(con, "edgar", ok=not stats["errors"],
                     error="; ".join(stats["errors"])[:500] or None)
    fund.log_run(con, run_id, "poll",
                 "error" if stats["errors"] else "ok",
                 f"{stats['new_filings']} new filings across {stats['ciks']} CIKs",
                 stats)
    return stats


def pending(con, forms=None, parent_cik: str = None, limit: int = None) -> list:
    """Filings stored but not yet parsed by their stage."""
    q = """SELECT f.*, m.slug, m.manager_class, m.style_tag, m.ingest_13f
           FROM fund_filings f
           LEFT JOIN fund_managers m ON m.cik = f.parent_cik
           WHERE f.parse_status = 'pending'"""
    args = []
    if forms:
        q += f" AND f.form_type IN ({','.join('?' * len(forms))})"
        args += list(forms)
    if parent_cik:
        q += " AND f.parent_cik = ?"
        args.append(parent_cik)
    q += " ORDER BY f.filed_at DESC"
    if limit:
        q += f" LIMIT {int(limit)}"
    return [dict(r) for r in con.execute(q, args)]


def reparse(con, statuses=("unsupported", "error"), forms=None) -> int:
    """Put previously-failed filings back in the queue.

    Needed whenever a parser is FIXED: the filings it could not read are sitting at
    'unsupported', and `pending()` only returns 'pending', so a fix would silently
    never be applied to the rows that motivated it. Called by `--reparse`.
    """
    q = (f"UPDATE fund_filings SET parse_status='pending', parse_note=NULL "
         f"WHERE parse_status IN ({','.join('?' * len(statuses))})")
    args = list(statuses)
    if forms:
        q += f" AND form_type IN ({','.join('?' * len(forms))})"
        args += list(forms)
    n = con.execute(q, args).rowcount
    con.commit()
    return n


def mark(con, accession_no: str, status: str, note: str = None) -> None:
    """Record the outcome of a parse attempt. `note` is the reason — a skip
    without one is indistinguishable from a bug, so callers always pass it."""
    con.execute(
        """UPDATE fund_filings SET parse_status=?, parse_note=?,
             parsed_at=datetime('now') WHERE accession_no=?""",
        (status, note, accession_no))


# Forms stored for CONTEXT that no parsing stage claims. Left at 'pending' they
# read as "not processed yet" forever, which is indistinguishable from a stage
# quietly failing. Each gets an explicit reason instead — a filing is either
# parsed, or visibly and deliberately not.
UNCLAIMED = {
    "13F-NT": ("notice filing: holdings are reported by another manager, so there "
               "is no information table to read. Kept as a rollup hint."),
    "S-1": ("read by the cap-table scan via full-text search, not parsed here — "
            "the Principal Stockholders table needs a human eye for position size"),
    "S-1/A": "as S-1",
    "424B4": "IPO pricing supplement — read by the cap-table scan, not parsed here",
    "424B5": "shelf takedown — context only; no holdings of ours are disclosed in it",
    "424B3": "prospectus supplement — context only",
    "DEF 14A": ("read by the 13F cross-check, which pulls the beneficial-ownership "
                "table directly from the issuer's own filing"),
    "DEFA14A": "additional proxy material — context for the cross-check only",
    "13FCONP": "confidential-treatment request cover — no holdings disclosed",
}


def settle_unclaimed(con, run_id: str) -> dict:
    """Give every stored-but-unparsed filing an explicit disposition."""
    n = 0
    for form, why in UNCLAIMED.items():
        n += con.execute(
            """UPDATE fund_filings SET parse_status='skipped', parse_note=?,
                 parsed_at=datetime('now')
               WHERE form_type=? AND parse_status='pending'""", (why, form)).rowcount
    left = con.execute("SELECT COUNT(*) c FROM fund_filings "
                       "WHERE parse_status='pending'").fetchone()["c"]
    con.commit()
    fund.log_run(con, run_id, "settle", "warn" if left else "ok",
                 f"{n} context filings dispositioned, {left} still awaiting a stage",
                 {"settled": n, "still_pending": left})
    return {"settled": n, "still_pending": left}


def flag_amendments(con, run_id: str) -> dict:
    """13F-HR/A is first class. An amendment often means a CONFIDENTIAL-TREATMENT
    RELEASE — a stake built quietly over one or more quarters and revealed only
    now. Among the highest-signal events in the whole system, so it gets its own
    flagged timeline entry rather than arriving as a quiet restatement."""
    n = 0
    rows = con.execute(
        """SELECT f.*, m.slug FROM fund_filings f
           JOIN fund_managers m ON m.cik = f.parent_cik
           WHERE f.form_type = '13F-HR/A' AND m.ingest_13f = 1""").fetchall()
    for f in rows:
        # An amendment filed long after the period it restates is the CT-release
        # shape: the original filing omitted the holding under confidential
        # treatment and this is the reveal.
        lag = fund.latency_days(f["period_of_report"] or f["filed_at"], f["filed_at"])
        late = lag > 75
        n += fund.add_event(
            con, parent_cik=f["parent_cik"], cik=f["cik"],
            event_date=f["period_of_report"] or f["filed_at"],
            disclosed_date=f["filed_at"], event_type="13f_amendment",
            headline=(f"13F-HR/A amendment for period {f['period_of_report']}"
                      + (" — filed far past the deadline: check for a "
                         "confidential-treatment release" if late else "")),
            is_flagged=1 if late else 0,
            flag_reason="possible confidential-treatment release" if late else None,
            source_form="13F-HR/A", accession_no=f["accession_no"],
            source_url=f["source_url"])
    con.commit()
    fund.log_run(con, run_id, "amendments", "ok", f"{n} amendment events", {"n": n})
    return {"amendments": len(rows), "events": n}
