"""13F vs DEF 14A — the independent check on our own backbone (§7).

A 13F is self-reported by the fund. A proxy statement's beneficial-ownership table
is reported by the COMPANY, verified by its counsel, and covers every >5% holder
including ones that filed nothing themselves. Where both exist they should agree,
and where they disagree the disagreement is the finding.

So a mismatch is FLAGGED, never resolved by quietly preferring one side. The two
numbers are stored next to each other with both source URLs, and the dashboard
shows the conflict. Silently picking a winner is how a dataset becomes confident
and wrong at the same time.

Dates rarely line up exactly — a proxy's "as of" record date sits between quarter
ends — so a tolerance band applies and anything inside it counts as agreement.
"""

import re

from . import fund, fund_sec

TOLERANCE_PCT = 0.15          # 15% relative difference in share count
MIN_PCT_OF_CLASS = 4.0        # proxy tables list >5% holders; allow for rounding
MIN_PROXY_SHARES = 10000      # a >5% holder of a real company holds more than this
# Consistency gate. shares / (pct/100) implies the shares outstanding each side is
# measuring against. A GENUINE disagreement — the stake moved between the filing
# date and the record date — leaves that implied total roughly unchanged. A
# MIS-PARSE does not: pairing a stray number with an unrelated percentage produces
# an implied company that is orders of magnitude the wrong size. This is what
# separates "these two sources disagree" from "we read the table wrong", and
# without it the feed fills with invented disagreements that teach the reader to
# ignore the flag.
MAX_IMPLIED_TOTAL_RATIO = 2.0

_NUM = re.compile(r"^\(?([0-9][0-9,]{3,})\)?$")
_PCT = re.compile(r"^\(?([0-9]{1,2}(?:\.[0-9]{1,2})?)\s*%?\)?\*?$")
_ROW = re.compile(r"(?is)<tr[^>]*>(.*?)</tr>")
_CELL = re.compile(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>")

# Names in a proxy holder table are legal entity names; ours are filer names. Strip
# the parts that never help distinguish one manager from another.
_NOISE = {"lp", "l.p.", "llc", "l.l.c.", "inc", "inc.", "ltd", "ltd.", "corp",
          "corporation", "the", "and", "&", "co", "co.", "plc", "management",
          "capital", "advisors", "advisers", "partners", "group", "investment",
          "investments", "asset", "holdings", "family", "office", "value"}


def _stem(name: str) -> str:
    """The distinctive part of a manager's name — 'Starboard Value LP' -> 'starboard'.
    Used as the anchor that a holder-table row has to contain."""
    toks = [t for t in re.split(r"[^A-Za-z0-9]+", (name or "").lower())
            if t and t not in _NOISE and len(t) > 2]
    return " ".join(toks[:3])


def _cells(row_html: str) -> list:
    out = []
    for c in _CELL.findall(row_html):
        t = re.sub(r"<[^>]+>", " ", c)
        t = (t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#160;", " "))
        out.append(" ".join(t.split()))
    return out


def _find_holder_row(html: str, manager_name: str):
    """(shares, percent) from the proxy's beneficial-ownership row for this manager.

    Parses actual <tr> structure rather than sliding a character window past the
    name. The window approach looked fine and produced nonsense — it happily
    returned "Berkshire holds 100,000 shares (16.9%)" by picking up unrelated
    numbers from surrounding prose. A cross-check that invents disagreements is
    worse than no cross-check: it teaches the reader to ignore the flag.

    Everything about this is deliberately strict. The row must name the manager,
    must contain BOTH a share count and a percentage as whole cell values, and the
    numbers must be plausible for a >5% holder. More than one candidate row means
    ambiguity, and ambiguity returns nothing.
    """
    stem = _stem(manager_name)
    if not stem:
        return None
    anchor = stem.split()[0]
    hits = []
    for row in _ROW.findall(html or ""):
        cells = _cells(row)
        joined = " ".join(cells).lower()
        if anchor not in joined:
            continue
        shares = pct = None
        for c in cells:
            m = _NUM.match(c)
            if m and shares is None:
                v = float(m.group(1).replace(",", ""))
                if v >= 1000:                    # a >5% holder is not 12 shares
                    shares = v
                continue
            m = _PCT.match(c)
            if m and pct is None:
                v = float(m.group(1))
                if 0.1 <= v <= 100:
                    pct = v
        if shares is not None and pct is not None:
            hits.append((shares, pct))
    # Rows repeat verbatim in these tables (a holder plus its affiliates). Identical
    # duplicates are the same claim; genuinely different rows are ambiguity.
    uniq = list(dict.fromkeys(hits))
    return uniq[0] if len(uniq) == 1 else None


def run(con, run_id: str, limit_managers: int = None) -> dict:
    """For every >5% stake we hold, look for the issuer's proxy and compare."""
    stats = {"checked": 0, "match": 0, "discrepancy": 0, "unresolved": 0,
             "errors": []}
    stakes = con.execute(
        """SELECT s.*, m.name AS manager FROM fund_stakes s
           JOIN fund_managers m ON m.cik = s.parent_cik
           WHERE s.pct_of_class >= ? AND s.issuer_cik IS NOT NULL
           GROUP BY s.parent_cik, s.issuer
           ORDER BY s.filed_at DESC""", (MIN_PCT_OF_CLASS,)).fetchall()
    if limit_managers:
        stakes = stakes[:limit_managers]

    for st in stakes:
        stats["checked"] += 1
        try:
            subs = fund_sec.submissions(st["issuer_cik"])
        except (fund_sec.SECError, fund_sec.SECConfigError) as exc:
            stats["errors"].append(f"{st['issuer']}: {exc}")
            continue
        proxies = [f for f in subs["filings"] if f["form"] == "DEF 14A"][:1]
        if not proxies:
            _write(con, st, None, None, None, "unresolved",
                   "no DEF 14A on file for this issuer", None)
            stats["unresolved"] += 1
            continue
        p = proxies[0]
        try:
            html = fund_sec.get_text(p["url"])
        except fund_sec.SECError as exc:
            stats["errors"].append(f"{st['issuer']} proxy: {exc}")
            continue
        hit = _find_holder_row(html or "", st["manager"])
        if not hit:
            _write(con, st, None, None, p["filed_at"], "unresolved",
                   "no single unambiguous holder-table row for this manager — the "
                   "table may name an affiliated entity, or list several. Left "
                   "unresolved rather than guessed at.", p["url"])
            stats["unresolved"] += 1
            continue
        proxy_shares, proxy_pct = hit
        ours = st["shares"]
        gate = _consistency(ours, st["pct_of_class"], proxy_shares, proxy_pct)
        if gate:
            _write(con, st, proxy_shares, proxy_pct, p["filed_at"], "unresolved",
                   gate, p["url"])
            stats["unresolved"] += 1
            continue
        if not ours:
            status, note = "unresolved", "no share count on our side to compare"
            delta = None
        else:
            delta = abs(proxy_shares - ours) / ours
            status = "match" if delta <= TOLERANCE_PCT else "discrepancy"
            note = (f"13D/G says {ours:,.0f} shares ({st['pct_of_class']}%); proxy "
                    f"says {proxy_shares:,.0f} ({proxy_pct}%) — "
                    f"{delta:.0%} apart. Dates differ; both are shown, neither is "
                    f"overridden.")
        _write(con, st, proxy_shares, proxy_pct, p["filed_at"], status, note, p["url"])
        stats[status if status in stats else "unresolved"] += 1
    con.commit()
    fund.log_run(con, run_id, "crosscheck",
                 "warn" if stats["discrepancy"] or stats["errors"] else "ok",
                 f"{stats['match']} match, {stats['discrepancy']} discrepancy, "
                 f"{stats['unresolved']} unresolved", stats)
    return stats


def _consistency(ours, our_pct, proxy_shares, proxy_pct):
    """None if the parsed row can be trusted, else why it cannot."""
    if proxy_shares is not None and proxy_shares < MIN_PROXY_SHARES:
        return (f"parsed holder row reads {proxy_shares:,.0f} shares — too small for "
                f"a >5% holder; treating it as a mis-read of the table, not as a "
                f"disagreement")
    if not (ours and our_pct and proxy_shares and proxy_pct):
        return None
    ours_total = ours / (our_pct / 100.0)
    proxy_total = proxy_shares / (proxy_pct / 100.0)
    ratio = max(ours_total, proxy_total) / min(ours_total, proxy_total)
    if ratio > MAX_IMPLIED_TOTAL_RATIO:
        return (f"the two rows imply share counts outstanding {ratio:.0f}x apart "
                f"({ours_total:,.0f} vs {proxy_total:,.0f}) — they are not measuring "
                f"the same class, so this is a parse failure and not a discrepancy")
    return None


def _write(con, st, proxy_shares, proxy_pct, proxy_as_of, status, note, proxy_url):
    con.execute(
        """INSERT INTO fund_crosschecks
             (parent_cik, issuer, issuer_cik, period, filed_shares, proxy_shares,
              proxy_pct, proxy_as_of, delta_pct, status, note, filing_url, proxy_url)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(parent_cik, issuer, period) DO UPDATE SET
             proxy_shares=excluded.proxy_shares, proxy_pct=excluded.proxy_pct,
             proxy_as_of=excluded.proxy_as_of, delta_pct=excluded.delta_pct,
             status=excluded.status, note=excluded.note, proxy_url=excluded.proxy_url""",
        (st["parent_cik"], st["issuer"], st["issuer_cik"], st["filed_at"][:10],
         st["shares"], proxy_shares, proxy_pct, proxy_as_of,
         (abs(proxy_shares - st["shares"]) / st["shares"])
         if proxy_shares and st["shares"] else None,
         status, note, st["source_url"], proxy_url))
