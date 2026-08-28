"""Sector of the ISSUER, from its SIC code on EDGAR.

The book tables answer "what does this fund own" but not "what business is that".
A weight of 9.5% in FirstEnergy reads differently once the row says Utilities, and
a book that is 72% one sector is a statement that no single line makes.

Two rules govern this module, both borrowed from the rest of the section:

  * **One door in.** The mapping lives in `config/fund_sectors.yaml` as an ordered
    first-match-wins rule list. No SIC range is written in Python.
  * **Unmapped is recorded, never guessed.** A code that matches nothing is stored
    with sector NULL and surfaced by the audit. A blank sector is a gap to close;
    a wrong one is a lie the reader cannot see.

The SIC arrives on the same submissions endpoint the identity layer already calls,
so this costs one request per ISSUER cik and nothing per position.
"""

from . import db, fund, fund_sec

_RULES = None


def cfg() -> dict:
    global _RULES
    if _RULES is None:
        p = db.CONFIG_DIR / "fund_sectors.yaml"
        if not p.exists():
            raise fund.FundConfigError(f"missing {p}")
        import yaml
        c = yaml.safe_load(p.read_text()) or {}
        known = set(c.get("sectors") or {})
        for r in c.get("rules") or []:
            if r["sector"] not in known:
                raise fund.FundConfigError(
                    f"fund_sectors.yaml: rule {r['from']}-{r['to']} points at "
                    f"unknown sector '{r['sector']}'")
            if int(r["from"]) > int(r["to"]):
                raise fund.FundConfigError(
                    f"fund_sectors.yaml: rule {r['from']}-{r['to']} is inverted")
        _RULES = c
    return _RULES


def classify(sic_code) -> tuple:
    """(sector_slug, sector_label) for a 4-digit SIC, or (None, None).

    First match wins, so the ORDER of `rules` in the config is the semantics —
    2834 must be tested against the pharma rule before the chemicals range.
    """
    try:
        code = int(str(sic_code).strip())
    except (TypeError, ValueError):
        return None, None
    c = cfg()
    for r in c["rules"]:
        if int(r["from"]) <= code <= int(r["to"]):
            return r["sector"], c["sectors"][r["sector"]]["label"]
    return None, None


def ensure_table(con):
    con.executescript("""
        CREATE TABLE IF NOT EXISTS fund_issuer_sector (
          issuer_cik    TEXT PRIMARY KEY,
          sic_code      TEXT,
          sic_label     TEXT,
          sector        TEXT,
          sector_label  TEXT,
          source_url    TEXT,
          fetched_at    TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ix_issuer_sector_sector
          ON fund_issuer_sector(sector);
    """)
    con.commit()


def pull(con, run_id: str = None, limit: int = None, refresh: bool = False) -> dict:
    """Fetch and classify the SIC of every issuer we hold but have not resolved.

    Incremental by default: an issuer's SIC changes about never, so a second run
    costs nothing. `refresh=True` re-fetches everything.
    """
    ensure_table(con)
    q = """SELECT DISTINCT m.issuer_cik
             FROM fund_cusip_map m
             JOIN fund_positions p ON p.cusip = m.cusip
            WHERE m.issuer_cik IS NOT NULL"""
    if not refresh:
        q += """ AND m.issuer_cik NOT IN (SELECT issuer_cik FROM fund_issuer_sector)"""
    q += " ORDER BY m.issuer_cik"
    ciks = [r[0] for r in con.execute(q)]
    if limit:
        ciks = ciks[:limit]

    out = {"requested": len(ciks), "resolved": 0, "unmapped": [], "errors": []}
    for cik in ciks:
        try:
            sub = fund_sec.submissions(cik)
        except (fund_sec.SECError, fund_sec.SECConfigError) as exc:
            out["errors"].append(f"{cik}: {str(exc)[:120]}")
            continue
        code = sub.get("sicCode")
        sector, label = classify(code)
        if not sector:
            out["unmapped"].append(f"{cik} SIC={code or '—'} ({sub.get('sic') or '—'})")
        con.execute(
            """INSERT INTO fund_issuer_sector
                 (issuer_cik, sic_code, sic_label, sector, sector_label,
                  source_url, fetched_at)
               VALUES (?,?,?,?,?,?,datetime('now'))
               ON CONFLICT(issuer_cik) DO UPDATE SET
                 sic_code=excluded.sic_code, sic_label=excluded.sic_label,
                 sector=excluded.sector, sector_label=excluded.sector_label,
                 source_url=excluded.source_url, fetched_at=excluded.fetched_at""",
            (cik, code, sub.get("sic"), sector, label,
             f"https://data.sec.gov/submissions/CIK{cik}.json"))
        out["resolved"] += 1 if sector else 0
    con.commit()
    if run_id:
        fund.log_run(con, run_id, "sectors", "ok",
                     f"{out['resolved']}/{out['requested']} issuers classified", out)
    return out


def by_cusip(con) -> dict:
    """{cusip: {'sector':…, 'sectorLabel':…, 'sicCode':…}} for the handoff.

    Keyed by CUSIP rather than issuer CIK because that is what a position row
    carries; the join through fund_cusip_map happens once, here.
    """
    ensure_table(con)
    out = {}
    for r in con.execute(
            """SELECT m.cusip, s.sector, s.sector_label, s.sic_code, s.sic_label
                 FROM fund_cusip_map m
                 JOIN fund_issuer_sector s ON s.issuer_cik = m.issuer_cik
                WHERE s.sector IS NOT NULL"""):
        out[r[0]] = {"sector": r[1], "sectorLabel": r[2],
                     "sicCode": r[3], "sicLabel": r[4]}
    return out


def coverage(con) -> dict:
    """What the audit needs: how much of the held book carries a sector."""
    ensure_table(con)
    row = con.execute(
        """SELECT COUNT(*) held,
                  SUM(CASE WHEN s.sector IS NOT NULL THEN 1 ELSE 0 END) classified
             FROM (SELECT DISTINCT cusip FROM fund_positions) p
             LEFT JOIN fund_cusip_map m ON m.cusip = p.cusip
             LEFT JOIN fund_issuer_sector s ON s.issuer_cik = m.issuer_cik""").fetchone()
    held, classified = row[0] or 0, row[1] or 0
    return {"securities": held, "classified": classified,
            "pct": round(100.0 * classified / held, 1) if held else 0.0}
