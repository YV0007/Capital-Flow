"""Identifiers: CUSIP -> ticker, and shares outstanding.

CUSIP is a commercial identifier and the SEC publishes no public crosswalk, so
this map has to be DERIVED. That is fine — what is not fine is deriving it
invisibly. Every mapping records its method and confidence, the override file is
versioned, and a CUSIP we cannot resolve is logged rather than dropped.

The distinction matters more than it looks: a position with a missing ticker is a
display gap, a dropped position is a lie about the size of the book.

Shares outstanding comes from the XBRL company-facts API. Without it a holder row
is an uninterpretable share count; with it, it is a percentage of the company —
which is the only form in which "who owns this" means anything (§8b.5).
"""

import re

import yaml

from . import fund, fund_sec

_SUFFIX = re.compile(
    r"\b(inc|incorporated|corp|corporation|co|company|ltd|limited|plc|lp|llc|"
    r"holdings?|group|the|sa|nv|ag|se|spa|ab|as|oyj|adr|ads|sponsored|cl|class|"
    r"com|common|new|stock|shares?|units?|ordinary|reit|trust|technologies|tech)\b",
    re.I)
_PUNCT = re.compile(r"[^a-z0-9 ]+")
# 13F issuer fields routinely append the state or country of incorporation
# ("Danaher Corp Del", "ARM HOLDINGS PLC /UK"). SEC's registrant name appends its
# own variant of the same thing, and the two spellings rarely agree — so both
# sides get it stripped rather than being treated as part of the name.
_JURISDICTION = {"de", "del", "dela", "ny", "md", "ca", "nv", "tx", "ma", "mn",
                 "nj", "pa", "oh", "il", "wa", "va", "ga", "fl", "uk", "usa",
                 "us", "cayman", "bermuda", "jersey", "guernsey", "ireland"}
_CLASS_HINT = re.compile(r"\b(?:CL|CLASS|SER|SERIES)\s*([A-Z])\b", re.I)


def norm_issuer(name: str) -> str:
    """Reduce an issuer name to its distinctive tokens. '10X Genomics Inc' and
    '10x Genomics, Inc.' must land on the same key; 'Alphabet Inc Class A' and
    'Alphabet Inc Class C' deliberately do NOT — multi-class issuers are exactly
    where an over-eager normaliser starts mapping the wrong share class."""
    s = _PUNCT.sub(" ", (name or "").lower())
    s = _SUFFIX.sub(" ", s)
    toks = s.split()
    while toks and toks[-1] in _JURISDICTION:
        toks.pop()
    return " ".join(toks)


def class_hint(class_title: str):
    """The share class a 13F line refers to ('CAP STK CL A' -> 'A'), or None.
    For a multi-class issuer this is the only thing in the filing that says which
    ticker the position actually is."""
    m = _CLASS_HINT.search(class_title or "")
    return m.group(1).upper() if m else None


_OVERRIDES = None
_NAME_INDEX = None


def overrides() -> dict:
    global _OVERRIDES
    if _OVERRIDES is None:
        d = yaml.safe_load(fund.CUSIP_CFG.read_text()) if fund.CUSIP_CFG.exists() else {}
        _OVERRIDES = {"version": (d or {}).get("version", "0"),
                      "map": (d or {}).get("overrides") or {}}
    return _OVERRIDES


def name_index(con=None) -> dict:
    """{normalized issuer name: [(ticker, cik, title), ...]} from SEC's own file.

    Kept as a LIST on purpose. A name resolving to several tickers is the normal
    case for multi-class issuers (GOOGL/GOOG) and dual-listings (BIDU/BAIDF), and
    collapsing that to one entry at index time throws away exactly the information
    needed to choose correctly. The choice is made in _match(), with the filing's
    own class title in hand.
    """
    global _NAME_INDEX
    if _NAME_INDEX is not None:
        return _NAME_INDEX
    try:
        tickers = fund_sec.company_tickers()
    except (fund_sec.SECError, fund_sec.SECConfigError):
        if con is not None:
            fund.mark_source(con, "sec_company_tickers", ok=False,
                             error="company_tickers.json unavailable")
        _NAME_INDEX = {}
        return _NAME_INDEX
    idx = {}
    for tk, v in tickers.items():
        key = norm_issuer(v["title"])
        if key:
            idx.setdefault(key, []).append((tk, v["cik"], v["title"]))
    if con is not None:
        fund.mark_source(con, "sec_company_tickers", ok=True)
    _NAME_INDEX = idx
    return idx


def _pick(cands, hint):
    """Choose one ticker from the candidates for a single issuer, or None.

    Candidates spanning more than one CIK are different companies that happen to
    normalise alike — always ambiguous, always refused.

    Within one CIK they are share classes or listing venues of the same company:
      * with a class hint from the filing, take the ticker that carries that class
        letter (FOXA for 'CL A'). If none does — GOOGL/GOOG encode class A and C
        without spelling either — refuse, and let the override file settle it. A
        coin flip here silently attributes a class-A stake to the class-C line.
      * with no class hint, take the primary listing: the shortest ticker, and
        never a 5-letter F/Y suffix, which is an OTC or ADR board quote.
    """
    ciks = {c[1] for c in cands}
    if len(ciks) > 1:
        return None, None
    if len(cands) == 1:
        return cands[0], "exact"
    if hint:
        exact = [c for c in cands if c[0].upper().endswith(hint)]
        return (exact[0], "class") if len(exact) == 1 else (None, None)
    primary = sorted(cands,
                     key=lambda c: (len(c[0]) == 5 and c[0][-1] in "FY",
                                    len(c[0]), c[0]))
    return primary[0], "primary"


def _match(idx: dict, issuer_name: str, class_title: str = None):
    """(hit, how) for one issuer name. Three passes, each weaker than the last and
    each labelled, so a low-confidence ticker is visibly low-confidence rather
    than indistinguishable from a checked one.

      exact   normalised names are identical
      prefix  the 13F name is a truncation of exactly one registrant name — 13F
              issuer fields are commonly cut short ("Taiwan Semiconductor Manufac")
      subset  every distinctive token appears in exactly one registrant name

    Ambiguity always loses: if a pass matches more than one registrant we fall
    through rather than pick. A wrong ticker is worse than a missing one — it
    attributes a real position to the wrong company.
    """
    key = norm_issuer(issuer_name)
    if not key:
        return None, None
    hint = class_hint(class_title)
    if key in idx:
        hit, how = _pick(idx[key], hint)
        if hit:
            return hit, how
        return None, None
    keys = [k for k in idx if k.startswith(key) or key.startswith(k)]
    if len(keys) == 1:
        hit, _ = _pick(idx[keys[0]], hint)
        if hit:
            return hit, "prefix"
    toks = set(key.split())
    if len(toks) >= 2:
        keys = [k for k in idx if toks <= set(k.split())]
        if len(keys) == 1:
            hit, _ = _pick(idx[keys[0]], hint)
            if hit:
                return hit, "subset"
    return None, None


def load_map(con) -> dict:
    """{cusip: row} of everything already resolved."""
    return {r["cusip"]: dict(r) for r in con.execute("SELECT * FROM fund_cusip_map")}


def resolve(con, cusip: str, issuer_name: str, accession: str = None,
            cache: dict = None, class_title: str = None) -> dict:
    """Map one CUSIP. Order: override file > already-resolved > name match.
    Returns {'ticker','confidence','method'}; ticker may be None."""
    cusip = (cusip or "").strip().upper()
    cache = cache if cache is not None else load_map(con)
    ov = overrides()

    if cusip in ov["map"]:
        e = ov["map"][cusip]
        row = {"ticker": e.get("ticker"), "issuer_name": e.get("issuer") or issuer_name,
               "issuer_cik": None, "method": "config", "confidence": "high",
               "map_version": ov["version"], "source_url": None}
    elif cusip in cache and cache[cusip].get("ticker"):
        return {"ticker": cache[cusip]["ticker"],
                "confidence": cache[cusip]["confidence"],
                "method": cache[cusip]["method"]}
    else:
        hit, how = _match(name_index(con), issuer_name, class_title)
        if not hit:
            con.execute(
                """INSERT INTO fund_cusip_unmapped (cusip, issuer_name, example_accession)
                   VALUES (?,?,?)
                   ON CONFLICT(cusip) DO UPDATE SET
                     seen_count = fund_cusip_unmapped.seen_count + 1,
                     last_seen = datetime('now')""", (cusip, issuer_name, accession))
            return {"ticker": None, "confidence": None, "method": "unmapped"}
        tk, cik, title = hit
        row = {"ticker": tk, "issuer_name": title, "issuer_cik": cik,
               "method": f"name_match:{how}",
               "confidence": "high" if how == "exact" else
                             ("medium" if how in ("class", "primary") else "low"),
               "map_version": ov["version"],
               "source_url": fund_sec.COMPANY_TICKERS}

    con.execute(
        """INSERT INTO fund_cusip_map
             (cusip, ticker, issuer_name, issuer_cik, method, confidence,
              map_version, source_url, updated_at)
           VALUES (?,?,?,?,?,?,?,?,datetime('now'))
           ON CONFLICT(cusip) DO UPDATE SET ticker=excluded.ticker,
             issuer_name=excluded.issuer_name, issuer_cik=excluded.issuer_cik,
             method=excluded.method, confidence=excluded.confidence,
             map_version=excluded.map_version, updated_at=datetime('now')""",
        (cusip, row["ticker"], row["issuer_name"], row["issuer_cik"], row["method"],
         row["confidence"], row["map_version"], row["source_url"]))
    cache[cusip] = dict(row, cusip=cusip)
    return {"ticker": row["ticker"], "confidence": row["confidence"],
            "method": row["method"]}


def backfill_tickers(con) -> int:
    """Re-run the map over positions that landed without a ticker — a later run's
    override file or a newly-listed registrant can resolve what an earlier one
    could not."""
    n = 0
    cache = load_map(con)
    rows = con.execute(
        """SELECT cusip, issuer, max(class_title) AS class_title FROM fund_positions
           WHERE ticker IS NULL GROUP BY cusip, issuer""").fetchall()
    for r in rows:
        got = resolve(con, r["cusip"], r["issuer"], cache=cache,
                      class_title=r["class_title"])
        if got["ticker"]:
            con.execute("UPDATE fund_positions SET ticker=? WHERE cusip=? AND ticker IS NULL",
                        (got["ticker"], r["cusip"]))
            con.execute("UPDATE fund_position_deltas SET ticker=? WHERE cusip=? AND ticker IS NULL",
                        (got["ticker"], r["cusip"]))
            con.execute("DELETE FROM fund_cusip_unmapped WHERE cusip=?", (r["cusip"],))
            n += 1
    con.commit()
    return n


MIN_PLAUSIBLE_SHARES = 100_000


def pull_shares_outstanding(con, issuer_ciks, run_id: str = None) -> dict:
    """Fetch shares outstanding for a set of issuers. Best-effort per issuer, but
    every failure is recorded — an issuer silently missing its share count would
    make every ownership percentage for it quietly disappear."""
    stats = {"pulled": 0, "missing": 0, "errors": 0, "implausible": 0}
    for n, cik in enumerate(issuer_ciks, 1):
        if n % 100 == 0:
            con.commit()
        try:
            got = fund_sec.shares_outstanding(cik)
        except (fund_sec.SECError, fund_sec.SECConfigError):
            stats["errors"] += 1
            continue
        if not got:
            stats["missing"] += 1
            continue
        # XBRL share counts are filer-tagged and sometimes nonsense — a per-class
        # figure of 1, or a placeholder of 100. Any company whose stock a 13F filer
        # can hold has a float orders of magnitude larger than this, and a bogus
        # denominator turns every ownership percentage computed from it into
        # garbage, which then trips the >100%-of-class audit rule as if the
        # POSITION were wrong.
        if got["shares"] < MIN_PLAUSIBLE_SHARES:
            stats["implausible"] = stats.get("implausible", 0) + 1
            continue
        con.execute(
            """INSERT OR REPLACE INTO fund_shares_outstanding
                 (issuer_cik, as_of, shares, source_url) VALUES (?,?,?,?)""",
            (str(cik).zfill(10), got["as_of"], got["shares"], got["source_url"]))
        stats["pulled"] += 1
    con.commit()
    return stats
