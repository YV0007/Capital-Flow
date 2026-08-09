"""References: target-profiler JSON batches -> target_references.

Reads runs/<week>/references/<batch>/references.json (contract in
agents/target-profiler.md) and upserts one reference per TARGET entity. Only
targets that actually exist in events are accepted — references never create
entities. A reference without a description or read_more link is rejected
(that's the whole product). Idempotent: latest ingest wins.
"""

import json
import sys
from datetime import date

from . import db


def ingest_week(week: str) -> dict:
    con = db.connect()
    ref_dir = db.RUNS_DIR / week / "references"
    stats = {"references": 0, "skipped": 0}
    warnings = []
    if not ref_dir.is_dir():
        stats["warnings"] = warnings
        con.close()
        return stats

    known = {r["target"] for r in con.execute("SELECT DISTINCT target FROM events")}

    for batch_dir in sorted(p for p in ref_dir.iterdir() if p.is_dir()):
        fpath = batch_dir / "references.json"
        if not fpath.exists():
            continue
        try:
            objs = json.loads(fpath.read_text())
        except json.JSONDecodeError as e:
            warnings.append(f"{batch_dir.name}/references.json: invalid JSON ({e}) — skipped")
            continue
        for o in objs if isinstance(objs, list) else []:
            target = (o.get("target") or "").strip()
            desc = (o.get("description") or "").strip()
            rm = o.get("read_more") or {}
            rm_url = (rm.get("url") or "").strip()
            if target not in known:
                stats["skipped"] += 1
                warnings.append(f"{batch_dir.name}: unknown target '{target[:50]}' — skipped")
                continue
            if not desc or not rm_url:
                stats["skipped"] += 1
                warnings.append(f"{batch_dir.name}: '{target[:50]}' missing "
                                f"description/read_more — skipped")
                continue
            website = (o.get("website") or "").strip() or None
            if website and not website.startswith("http"):
                website = None
            sources = [s for s in (o.get("sources") or [])
                       if isinstance(s, str) and s.startswith("http")]
            con.execute(
                """INSERT INTO target_references
                     (target, description, website, read_more_url, read_more_label,
                      sources, as_of, run_week, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,datetime('now'))
                   ON CONFLICT(target) DO UPDATE SET
                     description=excluded.description, website=excluded.website,
                     read_more_url=excluded.read_more_url,
                     read_more_label=excluded.read_more_label,
                     sources=excluded.sources, as_of=excluded.as_of,
                     run_week=excluded.run_week, updated_at=datetime('now')""",
                (target, desc[:600], website, rm_url,
                 (rm.get("label") or "").strip()[:60] or None,
                 json.dumps(sources),
                 (o.get("as_of") or "").strip() or date.today().isoformat(), week))
            stats["references"] += 1
    con.commit()
    con.close()
    stats["warnings"] = warnings
    return stats


if __name__ == "__main__":
    s = ingest_week(sys.argv[1])
    print(f"references {sys.argv[1]}: {s['references']} upserted, {s['skipped']} skipped")
    for w in s.get("warnings", []):
        print("  WARN", w)
