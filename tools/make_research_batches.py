"""Close the feedback loop: build the per-class context pack each research agent
reads at the START of a run.

We already COLLECT the signals that would make agents better; nothing fed them back
in. This does exactly that — memory-in-files, no ML, no hidden state, no auto-tuning.
Every "lesson" below is plain text a human can read and argue with.

Three levers, one file per agent (runs/<week>/<agent>/context.json):

  1. WHAT YOU ALREADY HAVE — per watchlist entity: last event date, sectors it's
     active in, known vehicles, aliases, CIK/ticker. The agent searches FORWARD from
     the last known event instead of re-finding old deals (fewer duplicates).
     Plus `stale_candidates`: rows stuck at `candidate` that a Tier-1 confirm would
     promote — the highest-value work in a run, and the easiest to forget.

  2. WHAT WORKED — source_log's `yielded` column, aggregated per class over recent
     runs, as a short ranked list: "these sources hit recently, check them first."

  3. WHAT YOU GOT WRONG — recent audit rejects/warnings for this class as
     "don't repeat these" examples, with the count so recurring types stand out.

Usage: python tools/make_research_batches.py <week> [stale_days]
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db  # noqa: E402

# runs/<week>/<dir> per allocator class — mirrors db.AGENT_CLASS.
CLASS_DIR = {"corporate": "corporate", "vc": "vc", "individual": "individuals",
             "alt_manager": "alt-managers", "sovereign": "sovereigns"}
ALL_DIRS = [*dict.fromkeys(CLASS_DIR.values()), "filings"]
STALE_DAYS = 21
RECENT_RUNS = 3          # how many past weeks of feedback to fold in
TOP_SOURCES = 12
MAX_EXAMPLES = 2         # verbatim rejects per error type

# Plain-text lesson per audit code — what the agent should DO differently.
LESSONS = {
    "SKIP": "a row was REJECTED at ingest and never made the DB (missing required "
            "field, bad enum, or bad tier). Fix the row shape — a skipped row is a "
            "lost event.",
    "WARN": "a row ingested but with a warning (usually a non-canonical sector or "
            "theme). Map to the canonical taxonomy in config/rules.yaml.",
    "E0": "source_url was a search QUERY, not a document. Cite the filing/article you "
          "actually opened (engine strips search URLs; the audit blocks them).",
    "E1": "a verified/verified_alpha row shipped with no source_url. If you can't cite "
          "it, file it as `candidate` with the reason in notes.",
    "E2": "the allocator's slice exceeded the full round. Put the round in "
          "round_total_usd and the slice in amount_usd — never the round in both.",
    "E3": "row reached the DB without a confidence grade (a pipeline-level fault; "
          "report it rather than working around it).",
    "E4": "a track-record row had no source_url — unsourced numbers don't ship.",
    "E5": "a current-year/YTD figure wasn't flagged provisional.",
    "W1": "sector wasn't in the canonical taxonomy — map to the closest canonical slug "
          "(config/rules.yaml) or flag it, don't invent one.",
    "W2": "amount == valuation on a large deal — classic valuation/raise conflation. "
          "Never put a valuation in amount_usd.",
    "W3": "a key allocator with events has no profile yet (profiler coverage gap).",
    "W4": "profile strategy text shipped without strategy_source_url attribution.",
    "W5": "a 'verified' row rested on a tier-4/5 source. Tier 1 confirms; otherwise "
          "verified_alpha or candidate.",
    "W6": "a >=$1B target has no reference card (what-this-is coverage gap).",
    "W7": "a >=$1B fund/firm has no holdings collected.",
    "W8": "a >=$1B investable target has no ai_posture tag.",
}
# Which classes a reject line concerns; audit lines name the allocator, so we route
# by matching that name to its class at build time.
_CODE_RE = re.compile(r"^- ([EW]\d) (.+)$")


def _aliases_for(canonical: str) -> list:
    return sorted({a for a, c in db.load_aliases().items() if c == canonical
                   and a != canonical.lower()})


def _recent_weeks(week: str) -> list:
    """The N most recent run weeks on disk up to and including `week`."""
    weeks = sorted(p.name for p in db.RUNS_DIR.iterdir()
                   if p.is_dir() and not p.name.startswith("."))
    weeks = [w for w in weeks if w <= week] or weeks
    return weeks[-RECENT_RUNS:]


def _what_worked(con, weeks: list) -> dict:
    """Lever 2: yielded sources per agent-class over recent runs, ranked."""
    ph = ",".join("?" * len(weeks))
    rows = con.execute(
        f"""SELECT agent, source_url, source_tier,
                   SUM(yielded) hits, COUNT(*) checks
            FROM source_log WHERE run_week IN ({ph})
            GROUP BY agent, source_url
            HAVING hits > 0
            ORDER BY agent, hits DESC, checks ASC""", weeks).fetchall()
    out = defaultdict(list)
    for r in rows:
        if len(out[r["agent"]]) >= TOP_SOURCES:
            continue
        # Domain is the reusable lesson; the exact URL is the example.
        dom = (r["source_url"] or "").split("//")[-1].split("/")[0].removeprefix("www.")
        out[r["agent"]].append({"source": dom or r["source_url"], "example_url": r["source_url"],
                                "tier": r["source_tier"], "hits": r["hits"],
                                "checks": r["checks"]})
    # Also a domain-level roll-up: the actual "check these first" list.
    ranked = {}
    for agent, items in out.items():
        agg = Counter()
        for it in items:
            agg[it["source"]] += it["hits"]
        ranked[agent] = {
            "check_first": [d for d, _ in agg.most_common(8)],
            "detail": items[:TOP_SOURCES],
        }
    return ranked


def _what_went_wrong(weeks: list, name_class: dict) -> dict:
    """Lever 3: recent audit rejects/warnings, grouped by type, routed to the class
    whose allocator the line names."""
    per_class = defaultdict(lambda: defaultdict(lambda: {"count": 0, "examples": []}))
    globals_ = defaultdict(lambda: {"count": 0, "examples": []})
    for w in weeks:
        p = db.RUNS_DIR / w / "audit_report.md"
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            m = _CODE_RE.match(line.strip())
            if not m:
                continue
            code, text = m.group(1), m.group(2)
            hit_dir = None
            for nm, cls in name_class.items():
                if nm and nm in text:
                    hit_dir = CLASS_DIR.get(cls)
                    break
            bucket = per_class[hit_dir][code] if hit_dir else globals_[code]
            bucket["count"] += 1
            if len(bucket["examples"]) < MAX_EXAMPLES:
                bucket["examples"].append(text[:220])
    # Row-level ingest rejects (persisted by run_week) — these name the agent
    # directory directly, so they route exactly.
    for w in weeks:
        p = db.RUNS_DIR / w / "ingest_problems.txt"
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            agent_dir = line.split("/", 1)[0]
            code = "SKIP" if " SKIP " in line else "WARN"
            bucket = (per_class[agent_dir][code] if agent_dir in ALL_DIRS
                      else globals_[code])
            bucket["count"] += 1
            if len(bucket["examples"]) < MAX_EXAMPLES:
                bucket["examples"].append(line[:220])

    def _fmt(d):
        return [{"code": c, "lesson": LESSONS.get(c, "see audit_report.md"),
                 "occurrences": v["count"], "examples": v["examples"]}
                for c, v in sorted(d.items(), key=lambda kv: -kv[1]["count"])]
    return {"per_class": {k: _fmt(v) for k, v in per_class.items() if k},
            "all_classes": _fmt(globals_)}


def run(week: str, stale_days: int = STALE_DAYS) -> dict:
    con = db.connect()
    db.sync_allocators(con, db.load_config())
    weeks = _recent_weeks(week)

    ext = defaultdict(dict)
    for r in con.execute(
        """SELECT a.name, x.kind, x.value FROM entity_external_ids x
           JOIN allocators a ON a.id = x.allocator_id""").fetchall():
        ext[r["name"]][r["kind"]] = r["value"]

    vehicles = defaultdict(list)
    for r in con.execute(
        """SELECT a.name, r.child_name FROM entity_relationships r
           JOIN allocators a ON a.id = r.parent_id""").fetchall():
        vehicles[r["name"]].append(r["child_name"])

    name_class = {}
    packs = defaultdict(list)
    for a in con.execute(
        """SELECT id, name, class, tier, country, network FROM allocators
           WHERE tier IN ('key','core') OR EXISTS
             (SELECT 1 FROM events e WHERE e.allocator_id = allocators.id)
           ORDER BY class, name""").fetchall():
        name_class[a["name"]] = a["class"]
        hist = con.execute(
            """SELECT MAX(disclosed_date) last_date, COUNT(*) n,
                      GROUP_CONCAT(DISTINCT sector) sectors
               FROM events WHERE allocator_id = ?""", (a["id"],)).fetchone()
        recent = [r["target"] for r in con.execute(
            """SELECT target FROM events WHERE allocator_id = ?
               ORDER BY disclosed_date DESC LIMIT 6""", (a["id"],)).fetchall()]
        ids = ext.get(a["name"], {})
        packs[CLASS_DIR.get(a["class"], a["class"])].append({
            "allocator": a["name"], "class": a["class"], "tier": a["tier"],
            "country": a["country"], "network": a["network"],
            "last_event_date": hist["last_date"],
            "events_on_file": hist["n"],
            "sectors_active": sorted(x for x in (hist["sectors"] or "").split(",") if x),
            "known_vehicles": sorted(vehicles.get(a["name"], [])),
            "aliases": _aliases_for(a["name"]),
            "cik": ids.get("cik"), "ticker": ids.get("ticker"),
            "edgar_path": "deterministic" if ids.get("cik") else "search",
            "recent_targets": recent,
        })

    # Candidates aging without a Tier-1 confirm — chase these first.
    stale = defaultdict(list)
    for r in con.execute(
        """SELECT a.name AS allocator, a.class, e.target, e.event_type,
                  e.disclosed_date, e.source_tier, e.source_url, e.notes
           FROM events e JOIN allocators a ON a.id = e.allocator_id
           WHERE e.status = 'candidate' AND e.disclosed_date <= date('now', ?)
           ORDER BY e.disclosed_date""", (f"-{stale_days} days",)).fetchall():
        stale[CLASS_DIR.get(r["class"], r["class"])].append({
            "allocator": r["allocator"], "target": r["target"],
            "event_type": r["event_type"], "disclosed_date": r["disclosed_date"],
            "source_tier": r["source_tier"], "source_url": r["source_url"],
            "why_still_candidate": (r["notes"] or "")[:300],
        })

    worked = _what_worked(con, weeks)
    wrong = _what_went_wrong(weeks, name_class)
    con.close()

    # The filings agent has no class watchlist — its job is confirming everyone
    # else's candidates against primary documents. Give it the cross-class confirm
    # queue and the entities that have a deterministic EDGAR path.
    packs["filings"] = [e for e in
                        (x for lst in packs.values() for x in lst)
                        if e["cik"]]
    stale["filings"] = [s for lst in stale.values() for s in lst]

    written = {}
    for agent_dir in ALL_DIRS:
        entities = packs.get(agent_dir, [])
        w_class = wrong["per_class"].get(agent_dir, [])
        pack = {
            "week": week, "agent": agent_dir, "feedback_from_runs": weeks,
            "how_to_use": (
                "1) WHAT YOU ALREADY HAVE — search FORWARD from each entity's "
                "last_event_date; don't re-find old deals. Use the deterministic EDGAR "
                "path when cik is present (agents/CONTEXT.md → Tools) and run "
                "`engine.edgar exists` before writing a row. Aliases are the SAME "
                "entity — never file one as new. stale_candidates are existing rows "
                "needing a Tier-1 confirm, not new deals to re-file. "
                "2) WHAT WORKED — check `check_first` sources before searching broadly. "
                "3) WHAT YOU GOT WRONG — these are real rejects from recent runs; "
                "don't repeat them."),
            "what_you_already_have": {
                "entities": entities,
                "stale_candidates": stale.get(agent_dir, []),
            },
            "what_worked": worked.get(agent_dir, {"check_first": [], "detail": []}),
            "what_you_got_wrong": {
                "this_class": w_class,
                "all_classes": wrong["all_classes"],
            },
        }
        d = db.RUNS_DIR / week / agent_dir
        d.mkdir(parents=True, exist_ok=True)
        (d / "context.json").write_text(json.dumps(pack, indent=2))
        written[agent_dir] = {
            "entities": len(entities),
            "stale_candidates": len(stale.get(agent_dir, [])),
            "check_first": len(pack["what_worked"]["check_first"]),
            "reject_types": len(w_class),
        }
    return written


if __name__ == "__main__":
    wk = sys.argv[1] if len(sys.argv) > 1 else None
    if not wk:
        raise SystemExit("usage: python tools/make_research_batches.py <week> [stale_days]")
    days = int(sys.argv[2]) if len(sys.argv) > 2 else STALE_DAYS
    for agent, s in sorted(run(wk, days).items()):
        print(f"{agent:14s} {s['entities']:3d} entities · {s['stale_candidates']:2d} stale "
              f"· {s['check_first']} high-yield sources · {s['reject_types']} reject types")
