"""§8b.5 — the reverse lookup: security -> every institutional holder.

The rest of this section reads fund → positions. This reads the other way, which
is what makes a position interpretable: knowing Duquesne owns 3.2m shares of a name
says little until you can see whether that is 0.4% or 14% of the company, and
whether the wider institutional base was buying it that quarter or leaving.

Built on SEC's own quarterly Form 13F structured data sets — the same information
tables, already parsed and published as TSV. Every filer is in there, not just our
fourteen, which is the point: tracked funds render prominently and everyone else
forms the background that says whether our fund is EARLY or LATE into a name.

**Scope decision.** The raw INFOTABLE is ~400MB per quarter and holds every line
item filed by every institution. Storing all of it would multiply this database by
an order of magnitude to answer questions about securities nobody here tracks. So
the ingest keeps only rows for CUSIPs our funds actually hold — roughly 1,500
securities — and streams the rest past. That is a deliberate narrowing, stated here
and in the payload rather than left for someone to discover from a row count.

The data set trails the newest filings by about a quarter, so `period` on these
rows is normally one quarter behind the fund books. That is recorded per row, not
smoothed over.
"""

import csv
import io
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

from . import fund, fund_sec

INDEX_PAGE = "https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets"
CACHE = Path("/tmp") / "capital-flow-13f-datasets"

_MONTHS = {"JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05",
           "JUN": "06", "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10",
           "NOV": "11", "DEC": "12"}


def _date(s: str):
    """'31-MAR-2026' -> '2026-03-31'."""
    m = re.match(r"(\d{2})-([A-Z]{3})-(\d{4})", (s or "").strip().upper())
    return f"{m.group(3)}-{_MONTHS[m.group(2)]}-{m.group(1)}" if m else None


def latest_dataset_url():
    """Newest published quarterly data set, from SEC's own index page."""
    req = urllib.request.Request(INDEX_PAGE, headers={"User-Agent": fund_sec.user_agent()})
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", "replace")
    links = sorted(set(re.findall(
        r'href="(/files/structureddata/data/form-13f-data-sets/[^"]+\.zip)"', html)))
    if not links:
        raise RuntimeError("no 13F data-set links on the SEC index page")
    # Names are either '2023q4_form13f.zip' or '01mar2026-31may2026_form13f.zip'.
    # Sort by the last 4-digit year then by month, newest last.
    def key(u):
        name = u.rsplit("/", 1)[-1].lower()
        m = re.search(r"(\d{2})([a-z]{3})(\d{4})_form13f", name)
        if m:
            return (int(m.group(3)), int(_MONTHS[m.group(2).upper()]))
        m = re.search(r"(\d{4})q(\d)", name)
        return (int(m.group(1)), int(m.group(2)) * 3) if m else (0, 0)
    return "https://www.sec.gov" + sorted(links, key=key)[-1]


def fetch(url: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / url.rsplit("/", 1)[-1]
    if dest.exists() and dest.stat().st_size > 1_000_000:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": fund_sec.user_agent()})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, "wb") as fh:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    return dest


def _tsv(z: zipfile.ZipFile, name: str):
    with z.open(name) as fh:
        yield from csv.DictReader(io.TextIOWrapper(fh, "utf-8", errors="replace"),
                                  delimiter="\t")


def ingest(con, run_id: str, url: str = None, max_holders_per_security: int = 60) -> dict:
    """Load one quarter of institutional holders for the securities we track."""
    stats = {"dataset": None, "period": None, "our_cusips": 0, "rows_scanned": 0,
             "rows_kept": 0, "securities": 0, "security_periods": 0, "filers": 0,
             "ct_releases": 0, "error": None}
    try:
        url = url or latest_dataset_url()
        stats["dataset"] = url.rsplit("/", 1)[-1]
        path = fetch(url)
    except Exception as exc:                      # network / index shape
        stats["error"] = str(exc)
        fund.mark_source(con, "sec_13f_datasets", ok=False, error=str(exc)[:400])
        fund.log_run(con, run_id, "holders", "error", str(exc)[:300], stats)
        return stats

    ours = {r["cusip"]: (r["ticker"], r["issuer"]) for r in con.execute(
        "SELECT DISTINCT cusip, ticker, issuer FROM fund_positions")}
    stats["our_cusips"] = len(ours)
    if not ours:
        fund.log_run(con, run_id, "holders", "skipped",
                     "no tracked positions yet — nothing to look up holders for", stats)
        return stats

    # is_tracked drives what the UI renders prominently, so it must mean "one of
    # our books" and nothing else. A watch-only multi-strat appears in this data
    # like every other institution — it files a 13F — but flagging it tracked would
    # reinstate through the back door exactly the standing book §B3 refuses it.
    tracked = {r["cik"] for r in con.execute(
        """SELECT e.cik FROM fund_manager_entities e
           JOIN fund_managers m ON m.cik = e.parent_cik
           WHERE m.manager_class != 'watch_only'""")}
    # CT-release detection still needs to see watch-only filers' amendments.
    all_filers = {r["cik"] for r in con.execute("SELECT cik FROM fund_manager_entities")}
    z = zipfile.ZipFile(path)

    subs = {}
    for r in _tsv(z, "SUBMISSION.tsv"):
        if r.get("SUBMISSIONTYPE", "").startswith("13F-HR"):
            subs[r["ACCESSION_NUMBER"]] = {
                "cik": (r.get("CIK") or "").zfill(10),
                "period": _date(r.get("PERIODOFREPORT")),
                "filed": _date(r.get("FILING_DATE"))}
    names = {}
    for r in _tsv(z, "COVERPAGE.tsv"):
        accn = r["ACCESSION_NUMBER"]
        names[accn] = r.get("FILINGMANAGER_NAME")
        # The data set exposes what the filing itself does not spell out: an
        # amendment whose type is NEW HOLDINGS, or a confidential-treatment period
        # that has expired. That is the confidential-treatment RELEASE — a stake
        # built quietly and revealed late — and it is among the highest-signal
        # events in this whole system, so it is detected here rather than inferred
        # from a filing-lag heuristic.
        if (r.get("AMENDMENTTYPE") or "").strip().upper() == "NEW HOLDINGS" \
                or (r.get("CONFDENIEDEXPIRED") or "").strip().upper() == "Y":
            s = subs.get(accn)
            if s and s["cik"] in all_filers:
                parent = fund.parent_of(con, s["cik"])
                if parent:
                    stats["ct_releases"] += fund.add_event(
                        con, parent_cik=parent, cik=s["cik"],
                        event_date=s["period"], disclosed_date=s["filed"],
                        event_type="13f_amendment",
                        headline=("CONFIDENTIAL-TREATMENT RELEASE: an amendment for "
                                  f"period {s['period']} discloses holdings withheld "
                                  f"from the original filing"),
                        is_flagged=1,
                        flag_reason="stake built under confidential treatment, revealed late",
                        source_form="13F-HR/A", accession_no=accn,
                        source_url=f"https://www.sec.gov/Archives/edgar/data/"
                                   f"{int(s['cik'])}/{accn.replace('-', '')}/")

    agg = {}
    for r in _tsv(z, "INFOTABLE.tsv"):
        stats["rows_scanned"] += 1
        cusip = (r.get("CUSIP") or "").strip().upper()
        if cusip not in ours or (r.get("PUTCALL") or "").strip():
            continue                       # long common only; options are not ownership
        s = subs.get(r["ACCESSION_NUMBER"])
        if not s or (r.get("SSHPRNAMTTYPE") or "").upper() != "SH":
            continue
        key = (cusip, s["period"], s["cik"])
        a = agg.setdefault(key, {"shares": 0.0, "value": 0.0,
                                 "accn": r["ACCESSION_NUMBER"]})
        try:
            a["shares"] += float(r.get("SSHPRNAMT") or 0)
            a["value"] += float(r.get("VALUE") or 0)
        except ValueError:
            continue
        stats["rows_kept"] += 1

    outstanding = {r["issuer_cik"]: r["shares"] for r in con.execute(
        """SELECT issuer_cik, shares FROM fund_shares_outstanding
           WHERE (issuer_cik, as_of) IN
                 (SELECT issuer_cik, MAX(as_of) FROM fund_shares_outstanding
                  GROUP BY issuer_cik)""")}
    cusip_cik = {r["cusip"]: r["issuer_cik"] for r in con.execute(
        "SELECT cusip, issuer_cik FROM fund_cusip_map WHERE issuer_cik IS NOT NULL")}

    # Keep the largest holders per security; the tail is a long list of tiny index
    # positions that adds rows without adding meaning. The cut is logged, not silent.
    by_sec = {}
    for (cusip, period, cik), a in agg.items():
        by_sec.setdefault((cusip, period), []).append((cik, a))
    dropped = 0
    for (cusip, period), holders in by_sec.items():
        holders.sort(key=lambda h: -h[1]["shares"])
        keep = [h for h in holders[:max_holders_per_security]]
        keep += [h for h in holders[max_holders_per_security:] if h[0] in tracked]
        dropped += len(holders) - len(keep)
        total = outstanding.get(cusip_cik.get(cusip))
        ticker, issuer = ours[cusip]
        for cik, a in keep:
            con.execute(
                """INSERT INTO fund_holders
                     (cusip, ticker, issuer, period, filer_cik, filer_name, shares,
                      value_usd, pct_of_shares_outstanding, is_tracked,
                      accession_no, source_url)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(cusip, period, filer_cik) DO UPDATE SET
                     shares=excluded.shares, value_usd=excluded.value_usd,
                     pct_of_shares_outstanding=excluded.pct_of_shares_outstanding""",
                (cusip, ticker, issuer, period, cik, names.get(a["accn"]) or cik,
                 a["shares"], a["value"],
                 (a["shares"] / total) if total else None,
                 int(cik in tracked), a["accn"], url))
            stats["filers"] += 1
        stats["security_periods"] += 1
    stats["securities"] = len({c for c, _ in by_sec})
    stats["tail_dropped"] = dropped
    stats["period"] = max((p for _, p in by_sec), default=None)
    con.commit()
    fund.mark_source(con, "sec_13f_datasets", ok=True)
    fund.log_run(con, run_id, "holders", "ok",
                 f"{stats['filers']} holder rows across {stats['securities']} "
                 f"securities (tail beyond {max_holders_per_security} per security "
                 f"dropped: {dropped})", stats)
    return stats


def early_or_late(con, cusip: str, period: str) -> dict:
    """Where our funds sit against the wider institutional base for one security."""
    rows = [dict(r) for r in con.execute(
        """SELECT * FROM fund_holders WHERE cusip=? AND period=?
           ORDER BY shares DESC""", (cusip, period))]
    if not rows:
        return {}
    total = sum(r["shares"] for r in rows)
    return {
        "cusip": cusip, "period": period, "holders": len(rows),
        "institutionalShares": total,
        "trackedHolders": [
            {"filerName": r["filer_name"], "shares": r["shares"],
             "pctOfSharesOutstanding": r["pct_of_shares_outstanding"],
             "rankAmongHolders": i + 1, "shareOfInstitutional": r["shares"] / total}
            for i, r in enumerate(rows) if r["is_tracked"]],
    }


if __name__ == "__main__":
    con = fund.connect()
    print(ingest(con, sys.argv[1] if len(sys.argv) > 1 else "holders-manual"))
