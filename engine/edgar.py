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


# ---------------------------------------------------------------------------
# Callable tool surface (agents use this instead of fuzzy WebSearch / hand-rolled
# curl). The split that matters: KNOWN filer + KNOWN form = deterministic pull by
# CIK; an unknown deal in the wild = agent search. These functions are the first
# path — reproducible, name-collision-free, and they only ever return RESOLVED
# document URLs (never a search query, which the audit rejects as a citation).
# ---------------------------------------------------------------------------

def resolve_cik(con, entity: str):
    """Canonical entity name -> CIK from entity_external_ids (alias-aware).
    None means 'no known filer' — the agent should take the search path, not guess."""
    name = db.resolve_name(entity)
    row = con.execute(
        """SELECT x.value FROM entity_external_ids x
           JOIN allocators a ON a.id = x.allocator_id
           WHERE a.name = ? AND x.kind = 'cik'""", (name,)).fetchone()
    return row["value"] if row else None


def filing_url(cik, accession: str, primary_doc: str) -> str:
    """A RESOLVED filing document URL — the only citable EDGAR shape."""
    accn = (accession or "").replace("-", "")
    return (f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{primary_doc}"
            if accn and primary_doc else
            f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}")


def fetch_filings(cik, forms=None, since: str = None, limit: int = 40) -> list:
    """Deterministic pull: every recent filing for a CIK, optionally filtered to
    form types and a filed-on-or-after date. Returns parsed rows with resolved URLs.

    forms: iterable like ('8-K','D','SC 13D','4','S-1'); None = all forms of interest.
    """
    want = set(forms) if forms else set(FORMS_OF_INTEREST)
    data = _get(SUBMISSIONS.format(cik=str(cik).zfill(10)))
    time.sleep(REQ_INTERVAL)
    recent = (data.get("filings") or {}).get("recent") or {}
    forms_l = recent.get("form") or []
    dates = recent.get("filingDate") or []
    accns = recent.get("accessionNumber") or []
    docs = recent.get("primaryDocument") or []
    out = []
    for i, form in enumerate(forms_l):
        if form not in want or i >= len(dates):
            continue
        if since and dates[i] < since:
            continue
        out.append({
            "cik": str(cik).zfill(10),
            "entity_name": data.get("name"),
            "form": form,
            "filed_date": dates[i],
            "accession": accns[i] if i < len(accns) else None,
            "primary_doc": docs[i] if i < len(docs) else None,
            "url": filing_url(cik, accns[i] if i < len(accns) else "",
                              docs[i] if i < len(docs) else ""),
            "meaning": FORMS_OF_INTEREST.get(form),
        })
        if len(out) >= limit:
            break
    return out


def event_exists(con, allocator: str, target: str, event_type: str = None,
                 disclosed_date: str = None) -> dict:
    """'Do we already have this deal?' — call BEFORE writing a row, so a re-run
    doesn't churn duplicates through ingest. Matches the DB's own dedupe key
    (allocator, target, event_type, disclosed_date), alias-aware, and also reports
    looser same-pair matches so an agent can see a near-duplicate it should merge
    into rather than re-file."""
    name = db.resolve_name(allocator)
    rows = con.execute(
        """SELECT e.id, e.event_type, e.disclosed_date, e.status, e.amount_usd,
                  e.source_url, e.run_week
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE a.name = ? AND lower(e.target) = lower(?)
           ORDER BY e.disclosed_date DESC""", (name, target)).fetchall()
    same = [dict(r) for r in rows
            if (not event_type or r["event_type"] == event_type)
            and (not disclosed_date or r["disclosed_date"] == disclosed_date)]
    return {"exists": bool(same), "exact": same,
            "same_pair": [dict(r) for r in rows], "allocator": name, "target": target}


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
        # Institutions: skip Form 4 (exec-comp noise); individuals: it's real signal.
        forms = (set(FORMS_OF_INTEREST) - INDIVIDUAL_ONLY_FORMS
                 if r["class"] != "individual" else None)
        try:
            filings = fetch_filings(r["cik"], forms=forms, since=cutoff, limit=200)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            stats["errors"] += 1
            continue

        for f in filings:
            cur = con.execute(
                """INSERT OR IGNORE INTO leads
                     (source, entity, form_type, title, url, filed_date, run_week)
                   VALUES ('edgar',?,?,?,?,?,?)""",
                (r["name"], f["form"], FORMS_OF_INTEREST[f["form"]], f["url"],
                 f["filed_date"], week))
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


def _cli(argv):
    """Agent-facing CLI. Deterministic paths first, search only when there's no CIK.

      python -m engine.edgar filings NVIDIA --forms 8-K,D --since 2026-08-01
      python -m engine.edgar cik "Blue Owl"
      python -m engine.edgar exists --allocator NVIDIA --target "Nebius Group N.V."
      python -m engine.edgar sweep 2026-W34
    """
    if not argv or argv[0] in ("-h", "--help"):
        print(_cli.__doc__)
        return
    cmd, rest = argv[0], argv[1:]
    opts = {}
    pos = []
    i = 0
    while i < len(rest):
        if rest[i].startswith("--"):
            opts[rest[i][2:]] = rest[i + 1] if i + 1 < len(rest) else ""
            i += 2
        else:
            pos.append(rest[i])
            i += 1

    if cmd == "sweep":
        print(json.dumps(sweep(pos[0] if pos else "manual"), indent=2))
        return
    con = db.connect()
    db.sync_allocators(con, db.load_config())
    if cmd == "cik":
        entity = opts.get("entity") or (pos[0] if pos else "")
        cik = resolve_cik(con, entity)
        print(json.dumps({"entity": db.resolve_name(entity), "cik": cik,
                          "path": "deterministic" if cik else "search (no known filer)"},
                         indent=2))
    elif cmd == "filings":
        entity = opts.get("entity") or (pos[0] if pos else "")
        cik = opts.get("cik") or resolve_cik(con, entity)
        if not cik:
            print(json.dumps({"entity": entity, "cik": None, "filings": [],
                              "note": "no CIK on file — take the search path"}, indent=2))
        else:
            forms = [f.strip() for f in opts["forms"].split(",")] if opts.get("forms") else None
            print(json.dumps(fetch_filings(cik, forms=forms, since=opts.get("since"),
                                           limit=int(opts.get("limit", 40))), indent=2))
    elif cmd == "exists":
        print(json.dumps(event_exists(con, opts.get("allocator", ""),
                                      opts.get("target", ""), opts.get("event_type"),
                                      opts.get("date")), indent=2))
    else:
        print(_cli.__doc__)
    con.close()


if __name__ == "__main__":
    import sys
    _cli(sys.argv[1:])
