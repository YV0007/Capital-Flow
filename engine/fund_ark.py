"""ARK daily holdings — the only zero-latency full book on the list.

Everything else in this section is a snapshot of the past: a 13F is up to 4.5
months old, a 13D is five days old, a Form 4 is two. ARK publishes its entire
position-level book every trading day, from its own site, as a mandated fund
disclosure. That makes it both a real signal in its own right and the thing that
keeps the timeline from going dark on a quiet week.

ARK runs several ETFs. The manager-level book is their SUM per security — holding
the same name in ARKK and ARKW is one position for Cathie Wood, not two — so the
funds are aggregated before anything is written.

The CSVs also pair CUSIP with ticker, published by the fund itself. That is a
citable, high-confidence source for the identifier map, and it is fed back into
fund_cusip_map rather than thrown away.
"""

import csv
import io
import urllib.error
import urllib.request
from datetime import datetime

from . import fund, fund_conviction

SOURCE_FORM = "ARK-CSV"
UA = "Capital Flow research (fund tracker)"


def _fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8-sig", "replace")


def _num(s):
    if s is None:
        return None
    s = str(s).strip().replace("$", "").replace(",", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_csv(text: str) -> list:
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        keys = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
        cusip = keys.get("cusip", "").upper()
        d = keys.get("date", "")
        if not cusip or not d:
            continue                     # ARK appends disclaimer lines to the file
        try:
            as_of = datetime.strptime(d, "%m/%d/%Y").date().isoformat()
        except ValueError:
            continue
        rows.append({
            "as_of": as_of, "fund": keys.get("fund"),
            "issuer": keys.get("company"), "ticker": (keys.get("ticker") or "").upper()
            or None, "cusip": cusip,
            "shares": _num(keys.get("shares")) or 0.0,
            "value_usd": _num(keys.get("market value ($)")) or 0.0,
            "weight_pct": _num(keys.get("weight (%)")),
        })
    return rows


def ingest(con, run_id: str) -> dict:
    """Pull every configured ARK fund and write one aggregated book."""
    cfg = (fund.load_sources_cfg().get("ark") or {})
    stats = {"funds": 0, "rows": 0, "positions": 0, "as_of": None, "errors": []}
    if not cfg.get("enabled"):
        fund.log_run(con, run_id, "ark", "skipped", "ARK source disabled in config")
        return stats

    man = con.execute("SELECT * FROM fund_managers WHERE slug='ark'").fetchone()
    if not man:
        fund.log_run(con, run_id, "ark", "error", "ARK not seeded")
        return stats

    base, funds = cfg["csv_base"], cfg.get("funds") or {}
    all_rows, urls = [], {}
    for code, filename in funds.items():
        url = base + filename
        urls[code] = url
        try:
            rows = parse_csv(_fetch(url))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                OSError) as exc:
            # §9: loud and logged. We do not fall back to the stale 13F and
            # pretend it is today's book.
            stats["errors"].append(f"{code}: {exc}")
            continue
        stats["funds"] += 1
        stats["rows"] += len(rows)
        for r in rows:
            r["source_url"] = url
        all_rows += rows

    if stats["errors"]:
        fund.mark_source(con, "ark", ok=False, error="; ".join(stats["errors"])[:400])
    if not all_rows:
        fund.log_run(con, run_id, "ark", "error" if stats["errors"] else "warn",
                     "no ARK rows retrieved", stats)
        return stats
    fund.mark_source(con, "ark", ok=not stats["errors"],
                     error="; ".join(stats["errors"])[:400] or None)

    as_of = max(r["as_of"] for r in all_rows)
    stats["as_of"] = as_of
    rows = [r for r in all_rows if r["as_of"] == as_of]

    # One security = one position for the manager, however many ETFs hold it.
    agg = {}
    for r in rows:
        a = agg.setdefault(r["cusip"], {
            "issuer": r["issuer"], "ticker": r["ticker"], "shares": 0.0,
            "value_usd": 0.0, "source_url": r["source_url"], "funds": set()})
        a["shares"] += r["shares"]
        a["value_usd"] += r["value_usd"]
        a["funds"].add(r["fund"])

    con.execute("DELETE FROM fund_positions WHERE parent_cik=? AND period=? "
                "AND source_form=?", (man["cik"], as_of, SOURCE_FORM))
    for cusip, a in agg.items():
        con.execute(
            """INSERT OR REPLACE INTO fund_positions
                 (cik, parent_cik, period, cusip, ticker, issuer, shares,
                  share_type, value_usd, value_scale, instrument, source_form,
                  source_url, as_of)
               VALUES (?,?,?,?,?,?,?,'SH',?,'dollars','common',?,?,?)""",
            (man["cik"], man["cik"], as_of, cusip, a["ticker"], a["issuer"],
             a["shares"], a["value_usd"], SOURCE_FORM, a["source_url"], as_of))
        stats["positions"] += 1
        # The fund publishes CUSIP and ticker side by side in its own mandated
        # disclosure — better evidence than any name match we could do.
        if a["ticker"]:
            con.execute(
                """INSERT INTO fund_cusip_map
                     (cusip, ticker, issuer_name, method, confidence, map_version,
                      source_url, updated_at)
                   VALUES (?,?,?,'ark_csv','high','ark',?,datetime('now'))
                   ON CONFLICT(cusip) DO UPDATE SET
                     ticker=excluded.ticker, method=excluded.method,
                     confidence='high', source_url=excluded.source_url,
                     updated_at=datetime('now')
                   WHERE fund_cusip_map.method NOT IN ('config')""",
                (cusip, a["ticker"], a["issuer"], a["source_url"]))
            con.execute("DELETE FROM fund_cusip_unmapped WHERE cusip=?", (cusip,))

    book = sum(a["value_usd"] for a in agg.values())
    top = sorted(agg.values(), key=lambda a: -a["value_usd"])
    con.execute(
        """INSERT INTO fund_book_stats
             (parent_cik, period, source_form, positions, book_value_usd,
              top10_share, as_of, disclosed_at, latency_days)
           VALUES (?,?,?,?,?,?,?,?,0)
           ON CONFLICT(parent_cik, period, source_form) DO UPDATE SET
             positions=excluded.positions, book_value_usd=excluded.book_value_usd,
             top10_share=excluded.top10_share""",
        (man["cik"], as_of, SOURCE_FORM, len(agg), book,
         (sum(a["value_usd"] for a in top[:10]) / book) if book else None,
         as_of, as_of))

    # Latency zero is the point of this layer, so the timeline says so explicitly.
    fund.add_event(
        con, parent_cik=man["cik"], event_date=as_of, disclosed_date=as_of,
        event_type="daily_holdings",
        headline=(f"full book published for {as_of}: {len(agg)} positions, "
                  f"${book / 1e9:.1f}B across {stats['funds']} ETFs — same-day, "
                  f"zero disclosure lag"),
        magnitude=book, magnitude_unit="usd", source_form=SOURCE_FORM,
        source_url=list(urls.values())[0] if urls else cfg["csv_base"])
    con.commit()
    fund.log_run(con, run_id, "ark", "warn" if stats["errors"] else "ok",
                 f"{stats['positions']} positions as of {as_of}", stats)
    return stats


def daily_deltas(con, parent_cik: str, limit_days: int = 2) -> list:
    """Day-over-day share moves in the ARK book. Share-based like everything else;
    at daily frequency a value-based delta would be almost pure price noise."""
    periods = [r[0] for r in con.execute(
        """SELECT DISTINCT period FROM fund_positions
           WHERE parent_cik=? AND source_form=? ORDER BY period DESC LIMIT ?""",
        (parent_cik, SOURCE_FORM, limit_days))]
    if len(periods) < 2:
        return []
    cur, prev = periods[0], periods[1]
    rows = con.execute(
        """SELECT c.cusip, c.ticker, c.issuer, c.shares, c.value_usd,
                  COALESCE(p.shares,0) prev_shares
           FROM fund_positions c
           LEFT JOIN fund_positions p ON p.parent_cik=c.parent_cik AND p.cusip=c.cusip
                AND p.period=? AND p.source_form=c.source_form
           WHERE c.parent_cik=? AND c.period=? AND c.source_form=?""",
        (prev, parent_cik, cur, SOURCE_FORM)).fetchall()
    out = []
    for r in rows:
        d = r["shares"] - r["prev_shares"]
        if not d:
            continue
        out.append({"cusip": r["cusip"], "ticker": r["ticker"], "issuer": r["issuer"],
                    "share_delta": d, "shares": r["shares"], "as_of": cur,
                    "share_delta_pct": (d / r["prev_shares"]) if r["prev_shares"] else None,
                    "value_usd": r["value_usd"],
                    "action": "NEW" if not r["prev_shares"] else
                              ("ADD" if d > 0 else "TRIM")})
    return sorted(out, key=lambda x: -abs(x["share_delta"] or 0))
