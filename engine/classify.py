"""Classify: deal-classifier JSON batches -> round_backers + target_classification.

Reads runs/<week>/classification/<batch>/{backers.json,classification.json}
(contract in agents/deal-classifier.md). Two independent, additive layers:

  backers.json         -> round_backers   (dated per-allocator participation edges;
                          unlocks lead-time + bellwether). Kept out of the events
                          ledger so capital accounting stays clean.
  classification.json  -> target_classification  (outcome / valuation trail,
                          investability, ai_posture; unlocks strike-rate,
                          actionable-path, and the moat factor).

Trust rules enforced here (not just requested from agents):
  - an asserted block with no source_url is dropped (facts only);
  - ai_class must be in the controlled vocabulary, else the ai_posture block is
    dropped (never ship an out-of-vocab tag the dashboard can't weight);
  - a verified value is never downgraded by a weaker (candidate/provisional) one
    on re-run — mirrors engine/ingest.py's merge discipline.
Idempotent: upsert per (round, allocator) and per target.
"""

import json
import sys
from datetime import date

from . import db

AI_CLASSES = {"compounds", "neutral", "at_risk"}
ROLES = {"lead", "co-lead", "participant", "follow-on"}
OUTCOME = {"active", "up_round", "ipo", "acquired", "shut_down"}
LISTING = {"public", "filed_s1", "rumored_ipo", "private", "subsidiary"}
_RANK = {"candidate": 0, "verified_alpha": 1, "verified": 2}


def _num(v):
    try:
        return float(v) if v is not None and str(v).strip() != "" else None
    except (TypeError, ValueError):
        return None


def _prov(v):
    return 1 if v in (1, "1", True) else 0


def _ingest_backers(con, batch, objs, known_alloc, stats, warnings):
    for rnd in objs if isinstance(objs, list) else []:
        round_id = (rnd.get("round_id") or "").strip()
        target = (rnd.get("target") or "").strip()
        if not round_id or not target:
            warnings.append(f"{batch}: backer round missing round_id/target — skipped")
            continue
        rdate = (rnd.get("disclosed_date") or rnd.get("date") or "").strip() or None
        for b in rnd.get("backers") or []:
            name = db.resolve_name((b.get("allocator") or "").strip())
            url = (b.get("source_url") or "").strip()
            if name not in known_alloc:
                # tolerate: a named backer we don't track yet still forms an edge,
                # but only if it carries a source; else it's noise.
                if not url:
                    stats["skipped"] += 1
                    continue
            if not url:
                warnings.append(f"{batch}: backer '{name[:30]}' in {round_id} "
                                f"has no source_url — dropped")
                continue
            role = (b.get("role") or "").strip().lower()
            role = role if role in ROLES else None
            status = (b.get("status") or "candidate").strip() or "candidate"
            entry = (b.get("date") or "").strip() or rdate
            prov = _prov(b.get("provisional")) or (1 if entry == rdate else 0)
            tier = b.get("source_tier")
            tier = int(tier) if str(tier or "").strip().isdigit() and 1 <= int(tier) <= 5 else None
            # never downgrade a stronger prior edge
            cur = con.execute(
                "SELECT status FROM round_backers WHERE round_id=? AND allocator=?",
                (round_id, name)).fetchone()
            if cur and _RANK.get(status, 0) < _RANK.get(cur["status"], 0):
                continue
            con.execute(
                """INSERT INTO round_backers
                     (round_id, target, allocator, role, entry_date, amount_usd,
                      status, source_tier, source_url, provisional, run_week)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(round_id, allocator) DO UPDATE SET
                     target=excluded.target, role=excluded.role,
                     entry_date=excluded.entry_date, amount_usd=excluded.amount_usd,
                     status=excluded.status, source_tier=excluded.source_tier,
                     source_url=excluded.source_url, provisional=excluded.provisional,
                     run_week=excluded.run_week""",
                (round_id, target, name, role, entry, _num(b.get("amount")),
                 status, tier, url, prov, stats["_week"]))
            stats["backers"] += 1


def _ingest_classification(con, batch, objs, known_target, stats, warnings, week):
    for o in objs if isinstance(objs, list) else []:
        target = (o.get("target") or "").strip()
        if target not in known_target:
            stats["skipped"] += 1
            warnings.append(f"{batch}: classification target '{target[:40]}' not "
                            f"a known node — skipped")
            continue
        row = {"target": target, "as_of": (o.get("as_of") or "").strip()
               or date.today().isoformat(), "run_week": week}

        oc = o.get("outcome") or {}
        if oc:
            st = (oc.get("status") or "").strip()
            if st and st not in OUTCOME:
                warnings.append(f"{target}: bad outcome.status '{st}' — cleared")
                st = None
            if st and not (oc.get("source_url") or "").strip():
                warnings.append(f"{target}: outcome asserted without source — dropped")
                oc = {}
                st = None
            entry_v, latest_v = _num(oc.get("entry_valuation_usd")), _num(oc.get("latest_valuation_usd"))
            step = _num(oc.get("step_up_multiple"))
            if step is None and entry_v and latest_v and entry_v > 0:
                step = round(latest_v / entry_v, 2)
            row.update(outcome_status=st, entry_valuation_usd=entry_v,
                       latest_valuation_usd=latest_v, step_up_multiple=step,
                       latest_as_of=(oc.get("latest_as_of") or "").strip() or None,
                       outcome_source_url=(oc.get("source_url") or "").strip() or None,
                       outcome_provisional=_prov(oc.get("provisional")))

        inv = o.get("investability") or {}
        if inv:
            ls = (inv.get("listing_status") or "").strip()
            if ls and ls not in LISTING:
                warnings.append(f"{target}: bad listing_status '{ls}' — cleared")
                ls = None
            proxies = [p for p in (inv.get("public_proxies") or [])
                       if isinstance(p, dict) and p.get("ticker") and (p.get("source_url") or "").strip()]
            row.update(listing_status=ls,
                       public_ticker=(inv.get("public_ticker") or "").strip() or None,
                       public_proxies=json.dumps(proxies) if proxies else None)

        ap = o.get("ai_posture") or {}
        if ap:
            cls = (ap.get("class") or "").strip()
            src = (ap.get("source_url") or "").strip()
            if cls and cls not in AI_CLASSES:
                warnings.append(f"{target}: ai_posture.class '{cls}' not in vocab — dropped")
                ap = {}
            elif cls and not src:
                warnings.append(f"{target}: ai_posture asserted without source — dropped")
                ap = {}
            if ap:
                row.update(ai_class=cls or None,
                           ai_rationale=(ap.get("rationale") or "").strip()[:400] or None,
                           ai_source_url=src or None,
                           ai_confidence=(ap.get("confidence") or "").strip() or None,
                           ai_provisional=_prov(ap.get("provisional")))

        cols = ", ".join(row)
        ph = ", ".join(f":{k}" for k in row)
        upd = ", ".join(f"{k}=excluded.{k}" for k in row if k != "target")
        con.execute(
            f"""INSERT INTO target_classification ({cols}) VALUES ({ph})
                ON CONFLICT(target) DO UPDATE SET {upd}, updated_at=datetime('now')""",
            row)
        stats["targets"] += 1


def ingest_week(week: str) -> dict:
    con = db.connect()
    cdir = db.RUNS_DIR / week / "classification"
    stats = {"backers": 0, "targets": 0, "skipped": 0, "_week": week}
    warnings = []
    if not cdir.is_dir():
        stats.pop("_week")
        stats["warnings"] = warnings
        con.close()
        return stats

    known_alloc = {r["name"] for r in con.execute("SELECT name FROM allocators")}
    known_target = {r["target"] for r in con.execute("SELECT DISTINCT target FROM events")}

    for batch_dir in sorted(p for p in cdir.iterdir() if p.is_dir()):
        for fname, fn, known in (
                ("backers.json", _ingest_backers, known_alloc),
                ("classification.json", _ingest_classification, known_target)):
            fpath = batch_dir / fname
            if not fpath.exists():
                continue
            try:
                objs = json.loads(fpath.read_text())
            except json.JSONDecodeError as e:
                warnings.append(f"{batch_dir.name}/{fname}: invalid JSON ({e}) — skipped")
                continue
            if fn is _ingest_backers:
                fn(con, batch_dir.name, objs, known, stats, warnings)
            else:
                fn(con, batch_dir.name, objs, known, stats, warnings, week)
    con.commit()
    con.close()
    stats.pop("_week")
    stats["warnings"] = warnings
    return stats


if __name__ == "__main__":
    s = ingest_week(sys.argv[1])
    print(f"classify {sys.argv[1]}: {s['backers']} backer edges, {s['targets']} "
          f"classified targets, {s['skipped']} skipped")
    for w in s.get("warnings", []):
        print("  WARN", w)
