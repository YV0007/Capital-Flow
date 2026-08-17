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


def _match(name: str, by_title: dict, titles: list):
    """Resolve a name to (cik, ticker) from SEC's own file. Exact stripped-title
    match first; else a UNIQUE token-subset match ('meta' ⊆ 'meta platforms').
    Uniqueness is the guard: an ambiguous prefix resolves to nothing rather than to
    a wrong CIK (same discipline as 'a wrong logo is worse than none')."""
    key = _strip(name)
    if key in by_title:
        return by_title[key]
    toks = set(key.split())
    if not toks:
        return None
    hits = [(t, v) for t, v in titles if toks and toks <= set(t.split())]
    return hits[0][1] if len(hits) == 1 else None


def run(export: bool = True) -> dict:
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
    titles = list(by_title.items())

    # Alias spellings are legitimate search keys ("Meta Platforms" for Meta).
    aliases = {}
    for norm_alias, canonical in db.load_aliases().items():
        aliases.setdefault(canonical, []).append(norm_alias)

    attached, resolved = 0, {}
    for a in con.execute(
        "SELECT id, name FROM allocators WHERE class IN ('corporate','alt_manager','vc')"
    ).fetchall():
        canonical = db.resolve_name(a["name"])
        hit = None
        for cand in [canonical, *aliases.get(canonical, [])]:
            hit = _match(cand, by_title, titles)
            if hit:
                break
        if not hit:
            continue
        cik, ticker = hit
        for kind, value in (("cik", cik), ("ticker", ticker)):
            con.execute(
                """INSERT OR IGNORE INTO entity_external_ids (allocator_id, kind, value)
                   VALUES (?,?,?)""", (a["id"], kind, value))
        resolved[a["name"]] = {"cik": cik, "ticker": ticker}
        attached += 1
    con.commit()
    con.close()
    # Persist so a DB rebuild (db/capital.db is gitignored) keeps the ids OFFLINE —
    # otherwise every rebuild silently drops CIKs and the EDGAR tool falls back to
    # fuzzy search. config/external_ids.yaml is loaded by db.sync_allocators.
    if export and resolved:
        import yaml
        p = db.CONFIG_DIR / "external_ids.yaml"
        prev = (yaml.safe_load(p.read_text()) or {}).get("external_ids", {}) if p.exists() else {}
        merged = {**prev, **resolved}
        p.write_text(
            "# SEC-resolved external ids (tools/enrich_ids.py). Committed so a DB\n"
            "# rebuild restores them offline; loaded by db.sync_allocators.\n"
            + yaml.safe_dump({"external_ids": dict(sorted(merged.items()))},
                             sort_keys=False))
    return {"attached": attached, "exported": len(resolved)}


if __name__ == "__main__":
    print(run())
