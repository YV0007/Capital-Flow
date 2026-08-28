"""Generate holdings-profiler batch inputs for funds/firms that need a portfolio.

Usage: python tools/make_holdings_batches.py <period> [batch_size]

Selects fund/firm entities (VC & alt-manager allocators, plus fund-vehicle
targets) that either have NO collected holdings, or have a portfolio that is
thinner than the contract in agents/holdings-profiler.md requires, and writes
runs/<period>/holdings/batch-N/batch_entities.json.

Two things changed after the W33/W34 post-mortem:

**Depth is now a selection criterion, not just a hope.** The agent brief has always
mandated "at least the top 25 per entity". Coatue shipped 16 of 250 and nothing
noticed, because the only question ever asked was "does this fund have ANY
holdings". A fund that is present but thin is now re-queued exactly like a fund
that is absent, and the batch input tells the agent what it already has so it
knows what it is being asked to beat.

**Batches are contiguous by capital, not interleaved.** They used to be dealt
round-robin (`ents[i::n]`), which spreads the biggest funds evenly across every
batch — fine when all agents run, actively harmful when only three of four do,
because the loss is then spread across the whole list instead of falling on the
tail. Contiguous means batch-1 holds the funds people actually click, and a
partial run degrades from the bottom.

Idempotent — regenerates only what still needs work. When it reports
`0 funds/firms missing holdings`, every fund on the map has a portfolio at
contract depth.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db  # noqa: E402

# agents/holdings-profiler.md: "ship at least the top 25 per entity".
MIN_HOLDINGS = 25
# The floor alone is not enough. a16z shipped 49 of ~1,458 — over the floor, and
# still an arbitrary 3% of the book. Nobody wants all 1,458, but 49 unranked names
# are worse than 50 chosen ones, so an entity below this target while more exist
# gets one deeper, relevance-ranked pass. Above it we stop: this is a portfolio
# view, not an attempt to mirror a fund's whole book.
TARGET_DEPTH = 50
# What this map exists to track. Passed to the agent so that when a portfolio is
# far too large to enumerate (a16z has 1458), the subset it returns is the
# relevant one rather than an arbitrary one.
MAP_SECTORS = ["ai-labs", "ai-compute", "semiconductors", "fab-equipment",
               "cloud-hyperscale", "neocloud", "datacenters", "power-energy",
               "nuclear", "networking", "robotics", "defense-tech",
               "cybersecurity", "ai-applications", "ai-data"]

SELECT = """
SELECT label, kind, cls, allocators, cap, urls,
       COALESCE(p.holdings_count, 0) AS true_total,
       COALESCE(h.got, 0) AS have,
       p.portfolio_url AS portfolio_url
FROM (
  SELECT a.name AS label, 'firm' AS kind, a.class AS cls,
         NULL AS allocators, SUM(COALESCE(e.amount_usd,0)) cap,
         GROUP_CONCAT(DISTINCT COALESCE(e.source_url,'')) urls
  FROM events e JOIN allocators a ON a.id = e.allocator_id
  WHERE a.class IN ('vc','alt_manager')
  GROUP BY a.id
  UNION ALL
  SELECT e.target AS label, 'vehicle' AS kind, 'fund' AS cls,
         GROUP_CONCAT(DISTINCT a.name) allocators,
         SUM(COALESCE(e.amount_usd,0)) cap,
         GROUP_CONCAT(DISTINCT COALESCE(e.source_url,'')) urls
  FROM events e JOIN allocators a ON a.id = e.allocator_id
  WHERE e.target_type = 'fund'
  GROUP BY e.target)
LEFT JOIN portfolios p ON p.entity = label
LEFT JOIN (SELECT entity, COUNT(*) got FROM holdings GROUP BY entity) h
       ON h.entity = label
WHERE COALESCE(h.got, 0) = 0
   OR (COALESCE(h.got, 0) < ? AND COALESCE(p.holdings_count, 0) > COALESCE(h.got, 0))
ORDER BY cap DESC
"""


def select_entities(con, min_holdings: int = MIN_HOLDINGS,
                    target_depth: int = TARGET_DEPTH) -> list:
    rows = con.execute(SELECT, (max(min_holdings, target_depth),)).fetchall()
    out = []
    for r in rows:
        have, total = r["have"], r["true_total"]
        thin = have > 0
        # Never ask for more than the portfolio actually contains — Altimeter has
        # 18 holdings in total, so demanding 25 would mark a complete answer short.
        target = (min_holdings if have == 0
                  else min(total, max(min_holdings, min(target_depth, total)))
                  if total else min_holdings)
        out.append({
            "entity": r["label"], "kind": r["kind"], "class": r["cls"],
            "parent_hint": [x for x in (r["allocators"] or "").split(",") if x][:2],
            "capital_usd": r["cap"],
            "deal_source_urls": [u for u in (r["urls"] or "").split(",") if u][:3],
            # What the agent is being asked to fix, in its own words.
            "reason": "thin" if thin else "missing",
            "already_have": have,
            "known_true_total": total or None,
            "portfolio_url": r["portfolio_url"],
            "target_minimum": target,
            "instruction": (
                f"We already hold {have} of a known {total} holdings for this "
                f"entity. Return a DEEPER list — at least {target} — not a re-send "
                f"of the same names. Where the portfolio is far larger than that, "
                f"choose by RELEVANCE to this map first (see rank_by), then by "
                f"stake size and notability: {target} chosen names beat {have} "
                f"arbitrary ones."
                if thin else
                f"No holdings collected yet. Return at least {min_holdings}, "
                f"ranked, each with its own source_url."),
            "rank_by": MAP_SECTORS,
        })
    return out


def main(period: str, batch_size: int = 8, min_holdings: int = MIN_HOLDINGS) -> int:
    con = db.connect()
    ents = select_entities(con, min_holdings)
    con.close()
    if not ents:
        print("0 funds/firms missing holdings — nothing to research")
        return 0

    # Never reuse a batch directory that already holds a result. Re-running the
    # generator inside the same period is normal — a run resumes, or half the
    # agents failed — and overwriting batch-3's input while batch-3's holdings.json
    # still sits beside it would leave the two describing different entities, and
    # the reconciliation counting a stale result as a fresh delivery.
    hdir = db.RUNS_DIR / period / "holdings"
    taken = {int(d.name.split("-")[1]) for d in hdir.iterdir()
             if d.is_dir() and d.name.startswith("batch-")
             and (d / "holdings.json").exists()} if hdir.is_dir() else set()
    free = (i for i in range(1, 10_000) if i not in taken)

    n = (len(ents) + batch_size - 1) // batch_size
    numbers = [next(free) for _ in range(n)]
    for i in range(n):
        # Contiguous, capital-ordered: batch-1 is the most-clicked funds, so a
        # partial run loses the tail rather than a slice of everything.
        b = ents[i * batch_size:(i + 1) * batch_size]
        d = db.RUNS_DIR / period / "holdings" / f"batch-{numbers[i]}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "batch_entities.json").write_text(json.dumps(b, indent=2))
        miss = sum(1 for e in b if e["reason"] == "missing")
        print(f"batch-{numbers[i]}: {len(b)} entities ({miss} missing, "
              f"{len(b) - miss} thin) -> {d / 'batch_entities.json'}")
    thin = sum(1 for e in ents if e["reason"] == "thin")
    print(f"{len(ents)} funds/firms across {n} batches "
          f"({len(ents) - thin} missing, {thin} below the {min_holdings}-holding floor)")
    return len(ents)


if __name__ == "__main__":
    wk = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    main(wk, size)
