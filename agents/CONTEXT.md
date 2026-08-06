# Agent Operating Context (shared)

Every research agent reads this file first. It defines the mission, what counts
as an event, the exact output contract, and the vocabularies. Class-specific
briefs (corporate.md, vc.md, …) add only what's unique to that class.

## Mission
Discover real capital allocation before consensus. Track where elite allocators
move money, so private flows can later be mapped to public beneficiaries. This
is an intelligence platform, not a news feed — a headline is a lead, not an event.

## What counts as an event (SCOPE)
Record ONLY capital allocation — money committed or deployed. The event_type must
be one of:

| event_type            | meaning                                             |
|-----------------------|-----------------------------------------------------|
| equity                | cash for ownership (not a priced round)             |
| funding_round         | a priced venture/growth round                       |
| follow_on             | additional capital into an existing position        |
| acquisition           | buying control of a company or asset                |
| minority_stake        | non-control stake                                   |
| fund_launch           | a new fund/vehicle raised (amount = fund size)      |
| spv                   | special-purpose vehicle for a specific deal         |
| grant                 | non-dilutive government/foundation money            |
| project_finance       | debt/structured finance for a physical build        |
| corporate_investment  | a corporate deploying balance-sheet capital         |
| sovereign_investment  | a state / SWF deploying capital                     |

NOT events: product launches, hires, opinions, MOUs with no money, revenue,
guidance, partnerships with no capital committed. If no capital moved or was
firmly committed, it is at most a `candidate`.

## Canonical sectors — map every event to exactly one
`ai-labs`, `ai-compute`, `semiconductors`, `fab-equipment`, `cloud-hyperscale`,
`neocloud`, `datacenters`, `power-energy`, `nuclear`, `networking`, `robotics`,
`defense-tech`. (Full definitions in config/rules.yaml.) If nothing fits, use the
closest and note it — an unknown sector ingests but is flagged.

## Sources & tiers (see config/sources.yaml)
- **Tier 1** SEC/EDGAR, company IR, official PRs, portfolio pages, government DBs — *confirms*.
- **Tier 2** PitchBook, Preqin, Crunchbase, Dealroom, Capital IQ, Bloomberg, Harmonic.
- **Tier 3** Reuters, FT, WSJ, Bloomberg News, The Information.
- **Tier 4** SemiAnalysis, Stratechery, conference talks.
- **Tier 5** podcasts, YouTube, X, LinkedIn, blogs — *discovers leads only*.

Use WebSearch / WebFetch for all tiers. SEC EDGAR full-text search is free and is
your best Tier-1 confirm. Tier 5 finds the lead; a higher tier must confirm it.

## Status — how sure are you
- `verified` — a Tier-1 source confirms it (filing, official PR, IR page, gov DB).
- `verified_alpha` — strong: ≥2 independent Tier 2–4 sources agree, but no Tier-1 yet.
- `candidate` — a single source or a Tier-5 lead. Honest defaults beat false confidence.

## Output contract — write into `runs/<week>/<agent>/`

**verified_events.csv** and **candidate_events.csv** — identical columns, this exact header:
```
event_date,disclosed_date,allocator,allocator_class,target,target_type,sector,subsector,event_type,amount_usd,amount_estimated,status,source_tier,source_url,notes
```
Field rules:
- `event_date` when capital moved (ISO YYYY-MM-DD, may be approximate/blank).
- `disclosed_date` when it became known (ISO, REQUIRED).
- `allocator` the entity deploying capital, exactly as named in config/allocators.yaml.
- `allocator_class` one of corporate|vc|individual|alt_manager|sovereign (optional
  for a single-class agent — derived from the agent — but REQUIRED for the filings agent).
- `target` who received the capital.
- `target_type` private|public|fund|project|asset (optional).
- `sector` one canonical slug (above).
- `subsector` free text (optional).
- `event_type` one of the table above.
- `amount_usd` number only, no `$`/commas; blank if undisclosed.
- `amount_estimated` 1 if the amount is a press/analyst estimate, else 0.
- `status` candidate|verified|verified_alpha.
- `source_tier` 1–5 (the BEST tier that supports the row).
- `source_url` the confirming link.
- `notes` lead/participant, vehicle name, caveats.

**source_log.csv** — every source you actually checked, header:
```
source_url,source_tier,yielded
```
`yielded` = 1 if it produced at least one event, else 0. This is the audit trail —
log Tier-1 sources checked even when they yield nothing.

**summary.md** — a short narrative: what moved this week in your class, the 2–3
biggest signals, and what to watch next week.
> IMPORTANT: write `summary.md` with **Bash** (`printf`/heredoc), NOT the Write tool —
> the agent Write tool blocks report-style markdown ("report file") and will fail. The
> CSVs are fine via Write. This keeps unattended/scheduled runs from breaking.

## Operating loop
1. Read this file, then your class brief, then config/allocators.yaml (your class)
   and config/sources.yaml.
2. For each allocator on your watchlist: check its mandatory Tier-1 sources, then
   search broadly (Tiers 2–5) for new capital movements.
3. Verify each candidate — try to confirm with a higher tier before storing.
4. Write the four output files. Deduping and storage are handled downstream by the
   Python engine — your job is coverage + accuracy, not database hygiene.
