# Sovereigns — ISO week 2026-W34 (disclosures ~2026-07-18 → 2026-08-17)

**2 verified_alpha rows, 0 candidates.** Watchlist: MGX, Mubadala, Saudi PIF, US Government.
A quiet week for named-target sovereign capital after last week's Moove/MOZN/OSC-mining
burst — most of the loudest headlines this week (MGX/Databricks aside) were either
strategy documents, cumulative-exposure figures, or continuations of deals already filed
in W32/W33. Zero rows graded `verified` this run for the same tooling reason as W33 (see
Confidence & limitations below).

## What actually moved

**MGX bought into the AI-agent data layer, not another compute deal.** On 13 August MGX
co-led a **$5bn** strategic round in Databricks alongside Coatue Management (lead),
Blackstone, T. Rowe Price and new entrant Sixth Street Growth, with BOND, Clearlake
Capital, Point72, Premji Invest and TPG also participating. The round closed at a
**$190bn** valuation - up 42% from the $134bn mark set in February - and follows a
familiar sovereign pattern: MGX's own check size inside the $5bn is undisclosed. Notable
because it is MGX's first large disclosed move into the AI *application/data* layer
(Databricks' Lakebase, Genie and Unity AI Gateway are agent-deployment infrastructure)
rather than frontier labs (OpenAI/Anthropic/xAI) or physical infrastructure
(Aligned, robotaxi depots). CEO Ali Ghodsi said the company meant to raise $1bn and
scaled to $5bn against ~$15bn of demand from a handful of investors alone - a demand
signal worth watching across the rest of the AI-infra stack.

**Washington kept signing conditional drone/mineral loans, one at a time.** On 31 July
the Department of War's Office of Strategic Capital signed an **up-to-$820m** conditional
loan commitment with Performance Drone Works (Huntsville, AL) to build domestic
manufacturing capacity for drone propulsion, power electronics, flight-control and vision
components - the same conditional-loan instrument used for the Sila/Sunrise/Niron
commitments filed last week (W33), and part of the same institutional pattern traced back
through W32's CHIPS LOIs: batch-signed, non-binding until definitive documents, framed as
defense-industrial-base rather than AI capex. This row was sitting in the ~30-day
lookback window and had not been captured by either W32 or W33 - caught this run by
widening the OSC sweep beyond the single 7 August roundtable batch.

## What did NOT move (checked, nothing new)

- **Mubadala**: no new named-target event this week. The Akita, Japan data-centre talks
  (Mubadala weighing up to ~$6.3-7bn of a ~$12.6bn, 500MW project led by Bitgrit/S2) are
  unchanged from the candidate already filed in `runs/2026-W32/sovereigns/candidate_events.csv`
  - still "in talks," still no signed commitment, no new corroboration this week. Not
    re-filed, to avoid duplicating an unchanged candidate across weeks. Mubadala's stake
    increase in Aldar Properties (27.01% → 28.03%, market purchases 8 May-11 Aug) was
    checked and deliberately excluded: real estate/domestic developer, no canonical sector
    fits even loosely, and it's secondary-market accumulation rather than new capital to a
    company - out of mission scope, unlike the EA or Sila-class rows that at least touch
    tech, defense or AI-adjacent supply chains.
- **Saudi PIF**: no new named-target event beyond the EA close and Brookfield Middle East
  Partners fund, both already recorded in W32. PIF's new 2026-2030 strategy document
  (published 12 Aug, emphasizing returns and private-sector capital over giga-projects) is
  a strategic pivot, not a flow - deliberately not recorded, consistent with prior weeks'
  treatment of headline pledges. No new HUMAIN/HUMAIN Ventures deal found; HUMAIN's
  LEAP-conference product news (HUMAIN OS, HUMAIN Chat, HUMAIN Academy - all late
  Aug/Sept) is product launch, not capital allocation.
- **US Government**: the seven CHIPS R&D Office letters of intent from 29 July (GlobalFoundries,
  Kepler, Multibeam, Extropic, Thintronics, OBSIDIA, Aeluma - all recorded in W32) have not
  converted to definitive agreements yet - checked via NIST/Commerce, no update. DOE's
  Genesis Open Models Initiative (launched 7 Aug) is a call for model/data contributions
  with no dedicated funding amount attached - not a capital event. No new DOE Loan
  Programs Office conditional commitments found in-window beyond already-known items.
- Checked and empty this run: Mubadala newsroom, PIF newsroom, DOE AI topic page,
  NIST/CHIPS release page, PIF's State Street ETF anchor investment (confirmed dated
  April 2026, well outside window).

## Discovered allocators

- **Sixth Street Growth** - new named co-lead in Databricks' $5bn round alongside MGX;
  not on any watchlist checked. Worth tracking given the size of the ticket it's willing
  to write into marquee AI rounds.

## Watch next week

- Whether MGX's own Databricks check size gets disclosed in a later filing or interview.
- Whether the Mubadala/Akita Japan talks (weighing since early August) convert to a signed
  commitment - still the largest unresolved sovereign lead on the board.
- Whether any more CHIPS R&D Office LOIs convert to definitive agreements.
- Whether OSC signs further conditional loans in the critical-minerals/drone-component
  cadence (roughly one per 1-2 weeks through the summer) - worth a dedicated sweep of
  war.gov's release index rather than relying on the most recent batch alone, since this
  is exactly how the Performance Drone Works row was nearly missed twice.
- HUMAIN's LEAP 2026 conference (31 Aug-3 Sep, Riyadh) is likely to produce fresh PIF/HUMAIN
  capital announcements - flag for the W35/W36 runs.

## Confidence & limitations

**This run's WebFetch tool was unavailable for its entire duration**, the same failure
mode documented in `runs/2026-W33/sovereigns/summary.md`: every attempted fetch returned
`EGRESS_BLOCKED`, including a bare `example.com` control and domains (`war.gov`,
`mubadala.com`) that earlier runs (W32) fetched directly. Bash `curl` hit the identical
wall (`CONNECT tunnel failed, response 403`). Both rows in this run are therefore sourced
through WebSearch's indexed retrieval and synthesis of primary pages (Databricks' own
newsroom, war.gov's release) rather than a direct page load performed this session - so,
consistent with W33's convention, both rows are capped at `verified_alpha` even though the
underlying sources are Tier-1 official pages, and even though corroboration is strong
(3-5 independent secondaries agreeing on the same figures for each row). No SEC EDGAR
full-text search could be attempted this session for the same connectivity reason - a
gap unchanged from W33.
