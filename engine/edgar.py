"""Standing EDGAR net (WS2) — the deterministic "never-miss" layer.

Agents search; this sweeps. For every tracked entity with a CIK, poll the SEC
submissions API and record capital-relevant filings as LEADS for agents to chase.

Design honesty: a filing's existence is NOT a capital-allocation event — an 8-K can
be an officer appointment. So this emits `leads`, not events. Agents (esp. filings)
promote a lead to an event once they read it, or dismiss it with a reason. Nothing
is silently dropped.

Fair access: SEC asks for <=10 req/s and a declared User-Agent
(https://www.sec.gov/about/developer-resources). We sleep between calls.
"""

import json
import time
import urllib.error
import urllib.request

from . import db

UA = "capital-flow research contact@example.com"
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"

# Forms that can carry a capital-allocation event.
FORMS_OF_INTEREST = {
    "8-K": "material event (may include an acquisition/investment)",
    "D": "private placement (Form D)",
    "D/A": "private placement amendment",
    "SC 13D": "activist/major stake",
    "SC 13G": "passive major stake",
    "4": "insider transaction",
    "S-1": "registration",
}
# Form 4 is executive-comp noise for institutions, but real signal when the filer is a
# tracked individual (a personal stake change). Only sweep it for class='individual'.
INDIVIDUAL_ONLY_FORMS = {"4"}
REQ_INTERVAL = 0.15  # ~7 req/s, under the 10 req/s guidance


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def sweep(week: str, lookback_days: int = 45, limit_entities: int = None) -> dict:
    """Poll EDGAR for tracked entities that have a CIK; store new leads."""
    con = db.connect()
    db.sync_allocators(con, db.load_config())
    cutoff = con.execute("SELECT date('now', ?)", (f"-{lookback_days} days",)).fetchone()[0]

    rows = con.execute(
        """SELECT a.id, a.name, a.class, x.value AS cik FROM allocators a
           JOIN entity_external_ids x ON x.allocator_id = a.id AND x.kind = 'cik'"""
    ).fetchall()
    if limit_entities:
        rows = rows[:limit_entities]

    stats = {"entities": len(rows), "leads_new": 0, "errors": 0}
    for r in rows:
        try:
            data = _get(SUBMISSIONS.format(cik=str(r["cik"]).zfill(10)))
            time.sleep(REQ_INTERVAL)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            stats["errors"] += 1
            continue

        recent = (data.get("filings") or {}).get("recent") or {}
        forms = recent.get("form") or []
        dates = recent.get("filingDate") or []
        accns = recent.get("accessionNumber") or []
        docs = recent.get("primaryDocument") or []
        for i, form in enumerate(forms):
            if form not in FORMS_OF_INTEREST or i >= len(dates):
                continue
            if form in INDIVIDUAL_ONLY_FORMS and r["class"] != "individual":
                continue  # exec-comp noise for institutions
            if dates[i] < cutoff:
                continue
            accn = accns[i].replace("-", "") if i < len(accns) else ""
            doc = docs[i] if i < len(docs) else ""
            url = (f"https://www.sec.gov/Archives/edgar/data/{int(r['cik'])}/{accn}/{doc}"
                   if accn else f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
                                f"&CIK={r['cik']}")
            cur = con.execute(
                """INSERT OR IGNORE INTO leads
                     (source, entity, form_type, title, url, filed_date, run_week)
                   VALUES ('edgar',?,?,?,?,?,?)""",
                (r["name"], form, FORMS_OF_INTEREST[form], url, dates[i], week))
            stats["leads_new"] += cur.rowcount
        # coverage: we checked this allocator's primary source this run
        con.execute(
            """INSERT INTO coverage (run_week, agent, allocator, sources_checked)
               VALUES (?,?,?,1)
               ON CONFLICT(run_week, agent, allocator)
               DO UPDATE SET sources_checked = sources_checked + 1""",
            (week, "edgar-auto", r["name"]))
    con.commit()
    con.close()
    return stats


if __name__ == "__main__":
    import sys
    print(sweep(sys.argv[1] if len(sys.argv) > 1 else "manual"))
