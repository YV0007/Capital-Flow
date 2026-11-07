# Individuals — 2026-W39 summary

## Operating note (read first)
This run's live network egress was heavily restricted: `data.sec.gov` (the
deterministic Form D path in `engine.edgar filings`) returned a 403 from the
org's egress proxy on every call, and `WebFetch` was blocked for essentially
every publisher domain tried (TechCrunch, Yahoo Finance, SEC.gov, Crunchbase,
Benzinga, Fool, IBTimes, CuspAI's own site, etc. — `EGRESS_BLOCKED`). `engine.edgar
cik`/`exists` (local/cached) still worked. Research this week therefore ran
entirely on `WebSearch`, whose synthesized results still surface and cite real,
resolvable URLs (used as `source_url`), but no filing could be pulled
deterministically and no article could be independently re-opened for a
second read. Status grading was kept conservative given that constraint —
`verified` was only used where an official company PR/press-wire (GlobeNewswire,
company Medium blog) named the person; everything else corroborated by ≥2
independent outlets is `verified_alpha`, per class norm.

## What moved this week
Three solid, well-corroborated personal-capital events, all AI-infrastructure-adjacent:

1. **Jeff Bezos** (Bezos Expeditions) — participated in **CuspAI**'s $450M
   Series B (materials-discovery AI for the chip/semiconductor supply chain;
   valuation $520M → $2.6B in 9 months). Official company announcement names
   Bezos Expeditions directly. `verified`.
2. **Peter Thiel** — personal follow-on into **Etched**'s $700M Series D at a
   $21B valuation (AI inference ASICs), led by Jane Street. Official GlobeNewswire
   PR and Etched's own X post name Thiel individually, distinct from Founders
   Fund. Thiel was already in via Etched's July Series C ($10.3B). `verified`.
3. **Elad Gil** (Elad Gil & Co) — follow-on into **Cambridge Aerospace**'s
   $300M Series C at a $3.4B valuation (UK counter-drone/air-defense). Gil
   co-led the company's April Series B too, so this is conviction-building in
   an existing position. Corroborated by Axios, Bloomberg, Benzinga, EU-Startups,
   Aviation Week — no single official PR opened, so `verified_alpha`.

A fourth, smaller but clean event: **Reid Hoffman** personally co-led (named
individually, separate from Greylock) a €18M Series A for **Integral**, a
Berlin AI-native accounting/tax/payroll startup, alongside Mosaic Ventures —
closed 2026-09-16, the most recent event found this run. `verified_alpha`.
Flagged: Integral doesn't cleanly fit any canonical sector (it's an AI
application-layer company, not infra/compute/power) — filed under `ai-labs`
as the closest fit per CONTEXT.md's "unknown sector ingests but is flagged"
rule.

One `candidate`: **Reid Hoffman**'s own AI lab **Prentis** (co-founded with
Mark Pincus) was reported "in talks" to raise $100M as of 2026-07-24 — no
close confirmed, so no capital-moved event yet. Worth a forward check.

## Network-coinvestment flags
None. Reid Hoffman (paypal_mafia, core) is the only network member with a
confirmed event this run, and no second tracked network member co-invested
alongside him in Integral — so no `network_convergence` signal to raise.
Checked the other three events' full co-investor lists (Kleiner Perkins,
NEA, John Doerr, AMD Ventures for CuspAI; Jane Street, Kleiner Perkins,
Sequoia, a16z, Tiger Global, Bain Capital Ventures, Blackstone for Etched;
DFJ Growth, Lux Capital, Accel, Lakestar for Cambridge Aerospace) against
`networks.yaml` members — no overlaps found.

## Watchlist names checked with no filed event this run
Swept via round-announcement searches and person-tracker profiles but found
nothing new, well-sourced, and inside the ~45-day window (since ~2026-08-07):
Marc Andreessen, Vinod Khosla, Ben Horowitz, Josh Kushner, Philippe Laffont,
Brad Gerstner, Neil Mehta, Nat Friedman, Daniel Gross, Joe Lonsdale, Keith
Rabois, Garry Tan, Sam Altman, Eric Schmidt (most recent personal-vehicle hit
via Hillspire was General Intuition, disclosed 2026-06-25 — outside window),
Patrick/John Collison, Ali Ghodsi, Dylan Field, Alexandr Wang, the CEO-tier
names (correctly excluded — no sourced personal checks, their capital moves
through their companies and belongs to the corporate agent), Peter Barrett,
Bill Gurley, Mike Maples Jr., Trae Stephens, Hemant Taneja, Bill Janeway,
Masayoshi Son (only corporate/SoftBank-vehicle moves found, and even those
were outside window), Druckenmiller, Ackman, Tepper, Dalio.

Notable context: Nat Friedman and Daniel Gross appear to have gone quiet on
new personal/NFDG deals this run — Meta's partial buyout of NFDG and their
move in-house to Meta Superintelligence Labs (alongside Alexandr Wang) looks
to have absorbed their dealmaking bandwidth; worth re-checking in a few weeks
once that transition settles.

## Discovered allocator
**John Doerr** — named individually (not via Kleiner Perkins) alongside Jeff
Bezos in CuspAI's Series B. A prolific solo angel showing up in the same
AI-infra-adjacent deals as our tracked names; suggest adding to the watchlist.
See `discovered_allocators.csv`.

## What to watch next week
- Confirm/close-check Prentis (Hoffman/Pincus, ~$100M).
- Re-run the EDGAR deterministic path once egress to `data.sec.gov` is
  restored — none of this week's rows have a Tier-1 SEC confirm attempt
  behind them beyond the official-PR route.
- Nat Friedman / Daniel Gross post-Meta personal dealmaking cadence.
- Whether Elad Gil's shift toward a ~$3B institutional fund (reported
  mid-2025) starts pulling his AI-infra bets (Cambridge Aerospace, Cognition,
  Odyssey) toward the VC agent's ledger instead of this one.
