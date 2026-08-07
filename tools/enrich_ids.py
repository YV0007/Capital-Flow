"""Attach ticker + CIK external IDs to public allocators (offline-triggered).

Fetches SEC's single company_tickers.json (one small file, respects fair-access)
and matches allocator names to ticker/CIK, writing into entity_external_ids. Kept
OUT of run_week's hot path so the pipeline stays deterministic and offline.

Usage: python tools/enrich_ids.py
Follow-on: GLEIF↔OpenCorporates bulk mapping for LEIs (WS4).
"""

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db  # noqa: E402

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
UA = "capital-flow research contact@example.com"

# Corporate suffixes/noise to strip before matching ("NVIDIA CORP" -> "nvidia").
_SUFFIXES = {"corp", "corporation", "inc", "incorporated", "co", "company", "ltd",
             "limited", "plc", "lp", "llc", "group", "holdings", "holding", "the",
             "sa", "nv", "ag", "&"}


def _strip(name: str) -> str:
    words = [w.strip(".,") for w in db._normalize(name).split()]
    kept = [w for w in words if w not in _SUFFIXES]
    return " ".join(kept or words)


def run() -> dict:
    con = db.connect()
    db.sync_allocators(con, db.load_config())
    req = urllib.request.Request(TICKERS_URL, headers={"User-Agent": UA})
    data = json.loads(urllib.request.urlopen(req, timeout=30).read())
    # {index: {cik_str, ticker, title}} -> stripped title -> (cik, ticker).
    # SEC titles carry corporate suffixes ("NVIDIA CORP") our canonical names don't.
    by_title = {}
    for v in data.values():
        key = _strip(v["title"])
        by_title.setdefault(key, (str(v["cik_str"]).zfill(10), v["ticker"]))

    attached = 0
    for a in con.execute(
        "SELECT id, name FROM allocators WHERE class IN ('corporate','alt_manager','vc')"
    ).fetchall():
        canonical = db.resolve_name(a["name"])
        hit = by_title.get(_strip(canonical))
        if not hit:
            continue
        cik, ticker = hit
        for kind, value in (("cik", cik), ("ticker", ticker)):
            con.execute(
                """INSERT OR IGNORE INTO entity_external_ids (allocator_id, kind, value)
                   VALUES (?,?,?)""", (a["id"], kind, value))
        attached += 1
    con.commit()
    con.close()
    return {"attached": attached}


if __name__ == "__main__":
    print(run())
