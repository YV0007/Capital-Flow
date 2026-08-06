# Agent brief template

Every research agent follows the same operating loop:

1. **Check mandatory sources** for your allocator class (config/sources.yaml).
2. **Search for alpha** — broadly, across all tiers. Tier 5 is for lead discovery.
3. **Verify capital movement** — an event counts only if capital actually moved or was
   committed (see ARCHITECTURE.md scope list). Announcements of intent without commitment
   are candidates at best.
4. **Output** into `runs/<week>/<agent>/`:
   - `verified_events.csv` — Tier 1–2 confirmed, columns matching db/schema.sql events table
   - `candidate_events.csv` — same columns, unconfirmed leads
   - `source_log.csv` — every source consulted: url, tier, yielded
   - `summary.md` — narrative: what moved this week, what to watch

Status marking: `verified` (Tier 1 confirmed) / `verified_alpha` (strong multi-source but
no Tier 1 yet) / `candidate` (lead).

CSV columns: event_date, disclosed_date, allocator, target, target_type, sector, subsector,
event_type, amount_usd, amount_estimated, status, source_tier, source_url, notes
