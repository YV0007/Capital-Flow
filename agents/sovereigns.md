# Sovereigns Agent

**Read `agents/CONTEXT.md` first.** Then read the `sovereigns:` block of
`config/allocators.yaml` — your watchlist.

## Who you track
Sovereign wealth and government capital: MGX (Abu Dhabi), Mubadala, Saudi PIF,
US Government — plus other SWFs/state vehicles discovered funding AI infrastructure.

## What to look for
- `sovereign_investment`, `grant`, `project_finance`, `minority_stake`, `fund_launch`.

## Mandatory checks per name
- Official government / fund announcements and annual reports (Tier 1).
- For US Government: agency press (DoE, DoD, CHIPS program), grant/loan databases.

## Class gotchas
- Sovereigns announce very large round-number *targets* ("$X billion AI fund"). Flag
  `amount_estimated: 1` aggressively and separate the headline pledge from money
  actually committed to a named target.
- Co-investment vehicles (e.g. MGX with a fund) — record the sovereign's share, note
  the partner in `notes`.
