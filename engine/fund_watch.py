"""§B3 — the multi-strat carve-out, answered directly.

There is no separate CIK for a "conviction sleeve" inside Citadel. Citadel
Advisors LLC files a single combined 13F covering the whole firm, and the filing
carries no strategy attribution at all — so nothing in it separates the conviction
desk from market-making inventory. No parse can recover what was never disclosed,
and anybody claiming a clean split is guessing.

So the answer is not a better parser. It is EVENT-TRIGGERED INCLUSION: a
multi-strat enters this section only when it makes a disclosure that market making
mechanically cannot produce.

  13D               an activist stake with stated intent. A market maker never files one.
  13G crossing >5%  a real single-name concentration, not inventory
  Form 4 / Form 3   became an insider or crossed 10% of a class
  named short       an entry in the ESMA / FCA registers under the fund's own name
  S-1 cap table     a pre-IPO position no 13F will ever show

These four managers have NO standing book here. They appear in the UI only when
one of these fires, rendered as a flagged trigger rather than as a portfolio.
"""

from . import fund, fund_ingest, fund_sec

# The full-text-search forms worth scanning for a watch-only name appearing in
# somebody ELSE'S filing — the pre-IPO window (§8b.3).
CAP_TABLE_FORMS = "S-1,S-1/A,424B4,DEF 14A"


def _fire(con, parent_cik: str, trigger_type: str, fired_at: str, detail: str,
          source_url: str, issuer: str = None, accession: str = None,
          event_date: str = None) -> int:
    n = con.execute(
        """INSERT OR IGNORE INTO fund_watch_triggers
             (parent_cik, trigger_type, fired_at, event_date, issuer, detail,
              accession_no, source_url)
           VALUES (?,?,?,?,?,?,?,?)""",
        (parent_cik, trigger_type, fired_at, event_date or fired_at, issuer,
         detail, accession, source_url)).rowcount
    if n:
        fund.add_event(
            con, parent_cik=parent_cik, event_date=event_date or fired_at,
            disclosed_date=fired_at, event_type="watch_trigger",
            headline=detail, issuer=issuer, is_watch_trigger=1, is_flagged=1,
            flag_reason="watch-only manager tripped a §B3 trigger",
            accession_no=accession, source_url=source_url)
    return n


def scan_filings(con, run_id: str) -> dict:
    """Every stored filing from a watch-only manager, checked against the trigger
    list. 13F-HR is deliberately absent from that list — it is the thing we refuse
    to read for these managers."""
    stats = {"checked": 0, "fired": 0, "by_type": {}}
    watch = {m["cik"]: m for m in fund.managers(con, klass="watch_only")}
    if not watch:
        return stats
    rows = con.execute(
        f"""SELECT * FROM fund_filings
            WHERE parent_cik IN ({','.join('?' * len(watch))})""",
        list(watch)).fetchall()

    for f in rows:
        stats["checked"] += 1
        ttype = fund.WATCH_TRIGGER_FORMS.get(f["form_type"])
        if not ttype:
            if f["parse_status"] == "pending":
                fund_ingest.mark(
                    con, f["accession_no"], "skipped",
                    "watch-only manager: only §B3 trigger forms are read; a 13F "
                    "here is market-making inventory and carries no strategy split")
            continue
        m = watch[f["parent_cik"]]
        # A 13G is only a trigger when it is an actual >5% crossing. The stake row
        # carries the percentage once the fast layer has parsed it; until then the
        # filing waits rather than firing on an unknown number.
        pct = None
        st = con.execute("SELECT pct_of_class, issuer, ticker FROM fund_stakes "
                         "WHERE accession_no=?", (f["accession_no"],)).fetchone()
        if st:
            pct = st["pct_of_class"]
        if ttype == "13g_crossing" and (pct is None or pct < 5.0):
            fund_ingest.mark(con, f["accession_no"], "skipped",
                             f"13G at {pct if pct is not None else 'unknown'}% — "
                             f"below the 5% crossing that makes it a trigger")
            continue
        issuer = st["issuer"] if st else None
        label = {"13d": "filed a 13D — an activist stake with stated intent, which "
                        "market making cannot produce",
                 "13g_crossing": f"crossed 5% of a single name ({pct}%)",
                 "form_4": "filed a Form 4 — insider or >10% owner",
                 "insider_3": "filed a Form 3 — became an insider or >10% owner"}[ttype]
        stats["fired"] += _fire(
            con, f["parent_cik"], ttype, f["filed_at"],
            f"{m['name']} {label}" + (f" in {issuer}" if issuer else ""),
            f["source_url"], issuer=issuer, accession=f["accession_no"],
            event_date=f["period_of_report"] or f["filed_at"])
        stats["by_type"][ttype] = stats["by_type"].get(ttype, 0) + 1
        if f["parse_status"] == "pending":
            fund_ingest.mark(con, f["accession_no"], "ok", f"§B3 trigger: {ttype}")
    con.commit()
    fund.log_run(con, run_id, "watch_filings", "ok",
                 f"{stats['fired']} triggers from {stats['checked']} filings", stats)
    return stats


def scan_shorts(con, run_id: str) -> dict:
    """A watch-only manager named in a short register is a trigger: the registers
    publish position holders by name above 0.5%, which is a disclosed directional
    bet rather than inventory."""
    stats = {"fired": 0}
    for r in con.execute(
            """SELECT s.*, m.name FROM fund_shorts s
               JOIN fund_managers m ON m.cik = s.parent_cik
               WHERE m.manager_class='watch_only' AND s.is_current=1"""):
        stats["fired"] += _fire(
            con, r["parent_cik"], "short_register", r["as_of_date"],
            f"{r['name']} named in the {r['register']} short register: "
            f"{r['pct']:.2f}% short in {r['issuer']}",
            r["source_url"], issuer=r["issuer"])
    con.commit()
    fund.log_run(con, run_id, "watch_shorts", "ok", f"{stats['fired']} triggers", stats)
    return stats


def scan_cap_tables(con, run_id: str, managers=None) -> dict:
    """Full-text search for a manager's name in filings it did NOT file — the S-1
    Principal Stockholders table and the DEF 14A holder table.

    This is the only window onto the private side: a pre-IPO cap table names funds
    that no 13F will ever show, and for a family office (§8b.3) it is often the
    only place they appear at all.

    A hit is a LEAD, not a position. The filing mentions the name; how large the
    stake is has to be read out of the table itself, which is a human step. So it
    is recorded as a flagged trigger with the document attached and nothing is
    inferred about size.
    """
    stats = {"queried": 0, "hits": 0, "fired": 0, "errors": []}
    targets = managers or (fund.managers(con, klass="watch_only")
                           + fund.managers(con, klass="sparse_coverage"))
    for m in targets:
        stats["queried"] += 1
        try:
            hits = fund_sec.full_text_search(m["name"], forms=CAP_TABLE_FORMS, limit=25)
        except (fund_sec.SECError, fund_sec.SECConfigError) as exc:
            stats["errors"].append(f"{m['slug']}: {exc}")
            continue
        for h in hits:
            if not h.get("url") or m["cik"] in (h.get("filer_ciks") or []):
                continue          # the manager's own filing is not a cap-table hit
            stats["hits"] += 1
            stats["fired"] += _fire(
                con, m["cik"], "ipo_cap_table", h["filed_at"],
                f"{m['name']} named in a {h['form']} filed by "
                f"{(h['display_names'] or ['an issuer'])[0]} — check the Principal "
                f"Stockholders / holder table for the size of the position",
                h["url"], issuer=(h["display_names"] or [None])[0],
                accession=h["accession"])
    fund.mark_source(con, "edgar_full_text", ok=not stats["errors"],
                     error="; ".join(stats["errors"])[:400] or None)
    fund.log_run(con, run_id, "watch_cap_tables",
                 "warn" if stats["errors"] else "ok",
                 f"{stats['fired']} cap-table triggers", stats)
    return stats


def run(con, run_id: str, do_cap_tables: bool = True) -> dict:
    out = {"filings": scan_filings(con, run_id), "shorts": scan_shorts(con, run_id)}
    if do_cap_tables:
        out["cap_tables"] = scan_cap_tables(con, run_id)
    return out
