# Public Filings Agent

**Read `agents/CONTEXT.md` first.** This agent has no fixed watchlist class — it
sweeps public filings directly and works across all allocator classes, so it MUST
set `allocator_class` on every row it writes.

## What you do — two jobs
1. **Discover** capital-allocation events other agents missed, straight from filings.
2. **Confirm** — upgrade other agents' `candidate` / `verified_alpha` rows to
   `verified` by finding the Tier-1 filing. (The engine merges duplicates and keeps
   the stronger status/tier, so just re-emit the event with `status: verified,
   source_tier: 1` and the filing URL.)

## Sources (all Tier 1)
- SEC EDGAR full-text + company search: 13F, 13D/G, Form 4, 8-K, S-1, 10-K/Q.
- Non-US equivalents where relevant (e.g. UK RNS, other national registries).

## Gotchas
- 13F is quarterly and lagged — useful for confirming public-stake changes, not for
  fresh alpha. Prefer 8-K/13D/Form 4 for timeliness.
- Everything you output is `source_tier: 1` by definition.
- Read the other agents' `runs/<week>/*/candidate_events.csv` first so you know what
  to hunt confirmations for.
