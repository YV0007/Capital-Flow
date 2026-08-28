"""13F information-table parser — the backbone layer.

The 13F is the slowest thing in this section (quarterly, up to 45 days late) and
also the only source that gives a whole long book at once. So it is the backbone,
never the heartbeat: the fast layer in fund_fast.py is what keeps the UI alive
between prints.

Two things here are easy to get wrong and expensive to get wrong:

VALUE UNITS. Before the 2023 amendment, `value` was reported in THOUSANDS. After
it, in whole dollars. Filers did not all switch on the same date and some still
report thousands years later — a live 2026 filing in this universe does exactly
that. So the scale is DETECTED per filing from the implied price (value/shares),
never assumed from the period. Getting this wrong scales a whole book by 1000x
and every weight, rank and conviction score computed from it.

PUTS. `putCall` is not a footnote. A put is a hedge or a short expression, not a
long conviction bet, and folding it into the long book both inflates the book and
inverts the meaning of the position. Puts are stored with instrument='put' and the
scorer keeps them off the long-conviction track entirely.
"""

import re
import statistics
import xml.etree.ElementTree as ET

from . import fund, fund_ident, fund_ingest, fund_sec

# Filenames EDGAR uses for the information table vary by filer and by year, so we
# identify it by CONTENT (root tag informationTable) after a cheap name filter
# rather than by trusting any single naming convention.
_TABLE_HINT = re.compile(r"(infotable|informationtable|form13f|13flist|table)", re.I)
_SKIP = re.compile(r"(primary_doc|index|\.txt$|\.html?$|\.gif$|\.jpg$)", re.I)
# The root element is <informationTable> and the rows are <infoTable> — but plenty
# of filers emit them namespace-PREFIXED (<ns1:infoTable>). Sniffing for the bare
# tag silently loses every one of those filers' books, which is how three managers
# came back with an empty 8-quarter history on the first live run.
_IS_TABLE = re.compile(r"<(?:[A-Za-z0-9_.-]+:)?infoTable[\s>]")

# Implied-price sanity band, in dollars. A book whose median implied price sits
# under a dollar is reporting thousands; one in a normal equity range is dollars.
THOUSANDS_CEILING = 1.0
DOLLARS_FLOOR = 1.0


def _tag(el) -> str:
    """Local tag name, namespace stripped. 13F XML carries a namespace that is not
    stable across schema versions, so matching on the qualified name breaks
    silently on old filings."""
    return el.tag.rsplit("}", 1)[-1]


def _child_text(el, name):
    for c in el.iter():
        if _tag(c) == name and (c.text or "").strip():
            return c.text.strip()
    return None


def find_info_table(cik, accession: str):
    """URL of the information table document inside a filing, or None."""
    idx = fund_sec.filing_index(cik, accession)
    items = (idx.get("directory") or {}).get("item") or []
    names = [i.get("name", "") for i in items]
    candidates = [n for n in names
                  if n.lower().endswith(".xml") and not _SKIP.search(n)]
    # Prefer a name that looks like the table; fall back to sniffing every xml.
    ordered = ([n for n in candidates if _TABLE_HINT.search(n)]
               + [n for n in candidates if not _TABLE_HINT.search(n)])
    for n in ordered:
        url = fund_sec.doc_url(cik, accession, n)
        txt = fund_sec.get_text(url)
        if txt and "informationTable" in txt and _IS_TABLE.search(txt):
            return url, txt
    return None, None


def parse_info_table(xml: str) -> list:
    """Rows out of the information table XML. Raises on malformed XML — a filing we
    cannot parse must be recorded as a failure, not returned as an empty book."""
    root = ET.fromstring(xml.encode("utf-8", "replace")
                         if isinstance(xml, str) else xml)
    rows = []
    for el in root.iter():
        if _tag(el) != "infoTable":
            continue
        shares_el = None
        for c in el.iter():
            if _tag(c) == "shrsOrPrnAmt":
                shares_el = c
                break
        amt = _child_text(shares_el, "sshPrnamt") if shares_el is not None else None
        amt_type = _child_text(shares_el, "sshPrnamtType") if shares_el is not None else None
        put_call = _child_text(el, "putCall")
        value = _child_text(el, "value")
        rows.append({
            "issuer": _child_text(el, "nameOfIssuer"),
            "class_title": _child_text(el, "titleOfClass"),
            "cusip": (_child_text(el, "cusip") or "").strip().upper(),
            "value_raw": float(value.replace(",", "")) if value else 0.0,
            "shares": float(amt.replace(",", "")) if amt else 0.0,
            "share_type": (amt_type or "SH").upper(),
            "put_call": (put_call or "").strip().upper() or None,
            "discretion": _child_text(el, "investmentDiscretion"),
            "other_managers": _child_text(el, "otherManager"),
        })
    return rows


def detect_value_scale(rows) -> tuple:
    """('dollars'|'thousands_x1000', multiplier, median_implied_price).

    Detected, never assumed.
    """
    # What feeds the estimate is any line whose value/shares is a real share price.
    # A PRN line reports a principal amount and a warrant line a sub-cent price;
    # either would drag the median into the thousands band and mis-scale an entire
    # equity book by 1000x. A PUT or CALL, though, reports the value of the
    # UNDERLYING shares — its implied price is an ordinary equity price, and
    # excluding options costs us the scale entirely on an options-only filing.
    # Elliott has filed exactly that: a single-line 13F holding PepsiCo puts.
    prices = [r["value_raw"] / r["shares"] for r in rows
              if r["share_type"] == "SH" and r["shares"] > 0 and r["value_raw"] > 0
              and instrument_of(r) not in ("warrant", "right", "unit",
                                           "convertible", "prn")]
    if not prices:
        return "unknown", 1.0, None
    med = statistics.median(prices)
    if med < THOUSANDS_CEILING:
        return "thousands_x1000", 1000.0, med
    return "dollars", 1.0, med


# ── what counts as OWNERSHIP ────────────────────────────────────────────────
#
# A portfolio answers one question: what does this fund own and believe in right
# now. That makes the instrument field load-bearing rather than descriptive.
#
# A PUT is a bet the stock FALLS. Listed in a holdings table it states the exact
# opposite of the truth. And 13F reports an option at the NOTIONAL value of the
# underlying shares, not the premium paid — so a single index put can dwarf every
# real holding in the file and then poison everything computed from it: the row's
# own value, the fund's total, every weight (they are all shares of that inflated
# total), the ranking, and the quarter-over-quarter deltas, which end up comparing
# option contracts against share counts as if they were the same unit.
#
# An ADR is the opposite case and is kept: a depositary receipt is genuine
# ownership of the underlying foreign shares.
OWNED = ("common", "adr")
DERIVATIVE = ("put", "call", "warrant", "right", "unit", "convertible", "prn")

_WARRANT = re.compile(r"(^|\W)(\*?W|WT|WTS|WARRANT|WARRANTS)(\W|$)", re.I)
_RIGHT = re.compile(r"(^|\W)(RT|RTS|RIGHT|RIGHTS)(\W|$)", re.I)
_UNIT = re.compile(r"(^|\W)(UNIT|UNITS)(\W|$)", re.I)
_CONVERTIBLE = re.compile(
    r"(^|\W)(NOTE|NOTES|NTS|DBCV|CVT|CONV|CONVERTIBLE|DEB|DEBENTURE|BOND)(\W|$)",
    re.I)
# ADR / ADS / GDR, however the filer spells the sponsorship.
_ADR = re.compile(r"(^|\W)(ADR|ADS|ADRS|GDR|SPON|SPONSORED|SP\s*ADR)(\W|$)", re.I)


def instrument_of(row) -> str:
    """Classify a 13F line. Only `common` and `adr` are ownership.

    Order matters: putCall wins over everything (a put on common stock is still a
    put), PRN next (a bond is not equity however it is titled), then the
    titleOfClass families, and ADR last among the specific tests so that a
    "SPONSORED ADR WT" is caught as a warrant rather than as ownership.
    """
    pc = (row.get("put_call") or "").strip().upper()
    if pc.startswith("PUT"):
        return "put"
    if pc.startswith("CALL"):
        return "call"
    if (row.get("share_type") or "").upper() == "PRN":
        return "prn"
    title = row.get("class_title") or ""
    if _WARRANT.search(title):
        return "warrant"
    if _RIGHT.search(title):
        return "right"
    if _UNIT.search(title):
        return "unit"
    if _CONVERTIBLE.search(title):
        return "convertible"
    if _ADR.search(title):
        return "adr"
    return "common"


def is_owned(instrument: str) -> bool:
    return instrument in OWNED


def ingest_filing(con, filing: dict, cusip_cache: dict = None) -> dict:
    """Parse one 13F-HR / 13F-HR/A into fund_positions.

    Positions are written under parent_cik, which is what makes the rollup real:
    Point72 files under six CIKs and Greenlight under three, and summing the child
    filings separately would show each manager at a fraction of its true size with
    every weight and conviction score wrong as a consequence.
    """
    accn, cik = filing["accession_no"], filing["cik"]
    out = {"accession": accn, "rows": 0, "unmapped": 0, "scale": None,
           "empty": False, "error": None}
    try:
        url, xml = find_info_table(cik, accn)
    except (fund_sec.SECError, fund_sec.SECConfigError) as exc:
        out["error"] = f"fetch failed: {exc}"
        fund_ingest.mark(con, accn, "error", out["error"])
        return out
    if not xml:
        # A 13F-HR with no information table is legitimate (a holdings report that
        # defers entirely to another manager). Recorded, not hidden.
        out["error"] = "no information table in filing directory"
        fund_ingest.mark(con, accn, "unsupported", out["error"])
        return out
    try:
        rows = parse_info_table(xml)
    except ET.ParseError as exc:
        out["error"] = f"malformed information table XML: {exc}"
        fund_ingest.mark(con, accn, "error", out["error"])
        return out
    if not rows:
        out["error"] = "information table parsed to zero rows"
        fund_ingest.mark(con, accn, "error", out["error"])
        return out

    # A 13F-HR reporting NO holdings is a real disclosure state, not a broken file:
    # filers submit a single placeholder line with zero shares and zero value. It
    # matters — for a concentrated manager an empty book means either nothing
    # 13F-eligible is held, or the whole book sits under confidential treatment,
    # and the second of those is a signal. Calling it a parse error would bury it
    # in the failure list where it reads as a bug in us rather than a fact about them.
    if not any((r["shares"] or 0) > 0 or (r["value_raw"] or 0) > 0 for r in rows):
        out["empty"] = True
        fund_ingest.mark(con, accn, "ok",
                         "filing reports NO 13F-eligible holdings (placeholder row "
                         "only) — an empty book, not a parse failure")
        fund.add_event(
            con, parent_cik=filing["parent_cik"], cik=cik,
            event_date=filing["period_of_report"] or filing["filed_at"],
            disclosed_date=filing["filed_at"], event_type="13f_exit",
            headline=("filed an EMPTY 13F for period "
                      f"{filing['period_of_report']} — no 13F-eligible holdings "
                      "reported. Either nothing qualifying is held, or the book is "
                      "under confidential treatment."),
            is_flagged=1,
            flag_reason="empty 13F — check for a later amendment releasing "
                        "confidentially-treated holdings",
            source_form=filing["form_type"], accession_no=accn,
            source_url=url)
        con.commit()
        return out

    scale, mult, med = detect_value_scale(rows)
    out["scale"], out["median_implied_price"] = scale, med
    if scale == "unknown":
        out["error"] = "could not determine value units (no usable SH lines)"
        fund_ingest.mark(con, accn, "error", out["error"])
        return out

    period = filing["period_of_report"] or filing["filed_at"]
    parent = filing["parent_cik"]
    cache = cusip_cache if cusip_cache is not None else fund_ident.load_map(con)

    # A re-filed accession replaces its own rows rather than duplicating them.
    con.execute("DELETE FROM fund_positions WHERE accession_no = ?", (accn,))
    for r in rows:
        got = fund_ident.resolve(con, r["cusip"], r["issuer"], accession=accn,
                                 cache=cache, class_title=r["class_title"])
        if not got["ticker"]:
            out["unmapped"] += 1
        con.execute(
            """INSERT OR REPLACE INTO fund_positions
                 (cik, parent_cik, period, cusip, ticker, issuer, class_title,
                  shares, share_type, value_usd, value_scale, instrument, put_call,
                  discretion, other_managers, source_form, accession_no, source_url)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (cik, parent, period, r["cusip"], got["ticker"], r["issuer"],
             r["class_title"], r["shares"], r["share_type"], r["value_raw"] * mult,
             scale, instrument_of(r), r["put_call"], r["discretion"],
             r["other_managers"], filing["form_type"], accn, url))
        out["rows"] += 1

    fund_ingest.mark(con, accn, "ok",
                     f"{out['rows']} positions, values={scale}"
                     f" (median implied price {med:.2f})"
                     + (f", {out['unmapped']} unmapped CUSIPs" if out["unmapped"] else ""))
    con.commit()
    return out


def ingest_pending(con, run_id: str, limit: int = None) -> dict:
    """Parse every stored-but-unparsed 13F for managers whose 13F we actually read.

    watch_only managers are excluded HERE as well as at seed. Their 13F is
    market-making inventory; parsing it would put thousands of meaningless lines
    into the same table the conviction model reads and quietly corrupt every
    cross-fund crowding count.
    """
    stats = {"filings": 0, "positions": 0, "unmapped": 0, "empty_books": 0,
             "failures": []}
    cache = fund_ident.load_map(con)
    rows = [f for f in fund_ingest.pending(con, forms=sorted(fund.POSITION_FORMS),
                                           limit=limit)
            if f.get("ingest_13f")]
    skipped = [f for f in fund_ingest.pending(con, forms=sorted(fund.POSITION_FORMS))
               if not f.get("ingest_13f")]
    for f in skipped:
        fund_ingest.mark(con, f["accession_no"], "skipped",
                         "watch-only manager: 13F is not read for conviction (§B3)")
    con.commit()

    for f in rows:
        r = ingest_filing(con, f, cusip_cache=cache)
        stats["filings"] += 1
        stats["positions"] += r["rows"]
        stats["unmapped"] += r["unmapped"]
        stats["empty_books"] += int(r.get("empty", False))
        if r["error"]:
            stats["failures"].append(f"{f['slug']} {f['period_of_report']} "
                                     f"[{f['accession_no']}]: {r['error']}")
    stats["skipped_watch_only"] = len(skipped)
    fund.log_run(con, run_id, "13f",
                 "warn" if stats["failures"] else "ok",
                 f"{stats['positions']} positions from {stats['filings']} filings",
                 stats)
    return stats


def book_stats(con, parent_cik: str, period: str, source_form: str = "13F-HR") -> dict:
    """Fund-level context for one period: book value, top-10 share, put/call use.
    Computed on COMMON only for the book value that weights are taken against —
    a put's notional is not part of a long book."""
    rows = con.execute(
        """SELECT instrument, value_usd, shares FROM fund_positions
           WHERE parent_cik=? AND period=? AND source_form LIKE ?""",
        (parent_cik, period, source_form.split("/")[0] + "%")).fetchall()
    if not rows:
        return {}
    longs = sorted((r["value_usd"] for r in rows if r["instrument"] in ("common", "other")),
                   reverse=True)
    book = sum(longs)
    return {
        "positions": len(rows),
        "book_value_usd": book,
        "top10_share": (sum(longs[:10]) / book) if book else None,
        "put_value_usd": sum(r["value_usd"] for r in rows if r["instrument"] == "put"),
        "call_value_usd": sum(r["value_usd"] for r in rows if r["instrument"] == "call"),
    }
