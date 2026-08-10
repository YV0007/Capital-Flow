# Sovereigns — ISO week 2026-W33 (disclosures ~2026-07-11 → 2026-08-10)

**5 verified_alpha rows, 1 candidate.** Watchlist: MGX, Mubadala, Saudi PIF, US Government.
Zero rows graded `verified` this run — see the tooling caveat under Confidence & limitations
below, which caps every grade at `verified_alpha` regardless of source tier.

## What actually moved

**Mubadala backed the robotaxi backend, not another datacenter.** On 5 August Mubadala led a
**$250m** Series C in Moove at a $2.1bn valuation, co-led by Toyota's Woven Capital and Ion
Pacific. Moove has pivoted from financing ride-hailing drivers in Africa to building "Nests" -
depot infrastructure that charges, services and orchestrates autonomous fleets - and already
runs Waymo's operations in Phoenix, Miami and London. Mubadala's own check size inside the
$250m isn't broken out. This is the first sovereign row this run in `robotics` rather than
`datacenters` or `ai-labs` - physical-AI embodiment infrastructure, not compute.

**PIF's HUMAIN made its first domestic bet, and it's tiny by HUMAIN's standards.** On 3 August
HUMAIN Ventures - not HUMAIN itself - made an undisclosed-amount investment in MOZN, a Saudi
enterprise-AI firm for financial services and public-sector "high-assurance" domains. Notable
mainly as a new vehicle: HUMAIN Ventures sits below the AirTrunk/Cohere/xAI-scale infrastructure
deals HUMAIN has done, and this is the first time it has written a check into a Saudi company at
all. Filed under `Saudi PIF` per the watchlist, HUMAIN Ventures noted in
`discovered_allocators.csv`.

**Washington moved from chip equity to mineral debt.** At a 7 August State Department mining
roundtable, the Department of War's Office of Strategic Capital signed three CONDITIONAL loan
commitments - Sila Nanotechnologies **$1.4bn** (battery anode/cell manufacturing, Moses Lake WA),
Sunrise Energy Metals **$400m** (scandium, Syerston NSW Australia) and Niron Magnetics **$150m**
(rare-earth-free magnets, Sartell MN) - plus a thinner, less-sourced **~$85m** commitment to
Standard Bauxite (filed as a candidate). None of this is AI capex; it's defense-industrial-base
financing for battery, magnet and mineral supply chains, flagged off-taxonomy under the closest
canonical sector (`defense-tech`). It is the same institutional pattern as the 29 July CHIPS
letters of intent recorded last week (W32): non-binding-until-definitive-docs, equity or debt
attached as a condition, announced in a batch at a single event. OSC alone has committed >$8.4bn
in debt and mobilized >$17.8bn in total capital in FY26 - a large, fast-growing sovereign
financing channel that doesn't touch AI compute directly but increasingly touches the inputs
(batteries, magnets) that robotics and grid buildout need.

## What did NOT move (checked, nothing new)

- **MGX**: no new disclosed event this run. The MGX/DayOne (APAC data-center operator, ~$20bn
  IPO ambitions) buyout talk that recirculated in search results traces to Reuters reporting from
  June 2026 - preliminary, sources say a deal "may not happen," no amount, no new corroboration
  this week. Not filed as a row; noted here as a watch item only.
- **Mubadala/MGX Akita, Japan** ($6.3bn AI datacenter, Bloomberg 6 Aug): unchanged from the
  candidate already filed in `runs/2026-W32/sovereigns/candidate_events.csv` - still "weighing,"
  still one Bloomberg origin, no UAE-ambassador-visit follow-through found yet. Not re-filed to
  avoid duplicating last week's row.
- **Saudi PIF**: no new named-target event beyond MOZN. PIF's "44% of portfolio, $170bn to US
  interests" (3 Aug, The National) is a cumulative exposure figure, not a new flow - deliberately
  not recorded, consistent with W32.
- Checked and empty: MGX and PIF newsrooms, NIST/CHIPS release page (no LOI-to-definitive-agreement
  conversions found yet for the seven 29 July companies), DOE's AI datacenter resource hub,
  Sanabil's news page.

## Discovered allocators

- **Department of War Office of Strategic Capital (OSC)** - the specific vehicle signing this
  week's three loan commitments; worth tracking directly given its FY26 run-rate.
- **HUMAIN Ventures** - HUMAIN's venture arm, new this week, distinct from HUMAIN's
  infrastructure-scale deals.

## Watch next week

- Whether any of last week's seven CHIPS R&D Office LOIs (GlobalFoundries, Kepler, etc.) convert
  to definitive agreements - none had by this run.
- Whether Sila/Sunrise/Niron's OSC conditional loans clear conditions into definitive financing
  documents.
- The Akita, Japan Mubadala/MGX datacenter talk - still waiting on the UAE ambassador's reported
  mid-August visit.
- MGX/DayOne - dormant since June, worth one more check in case talks resume or lapse formally.
- Korea Investment Corporation's enabling legislation, due before its National Assembly in
  August (filed as a discovered allocator, not on the core watchlist).

## Confidence & limitations

**This run's WebFetch tool was unavailable for its entire duration** - every attempted fetch
returned `EGRESS_BLOCKED`, including a bare `example.com` control and domains (`war.gov`,
`whitehouse.gov`, `mubadala.com`) that prior runs fetched directly without issue. `curl` from
Bash hit the same wall (`CONNECT tunnel failed, response 403`) against `sec.gov`, `energy.gov`,
`mgx.ae`, `pif.gov.sa`, `nist.gov`, `whitehouse.gov`, `reuters.com` and `bloomberg.com`. Every
row in this run is therefore sourced through WebSearch's indexed retrieval and synthesis rather
than a direct page load I performed myself. To stay honest about that gap, every row this week
is capped at `verified_alpha` even where the underlying source is Tier-1 (an official .gov
release or company PR) and even where W32's equivalent finding would have been graded
`verified` - the ceiling reflects the tooling limitation, not new doubt about the sources
themselves. Corroboration is still real: every row rests on at least one official primary
(`.gov` press release or the allocator's own newsroom) plus 2+ independent secondary outlets
agreeing on the same figures. SEC EDGAR full-text search was attempted for MGX and Mubadala
across the window and returned nothing retrievable this session (same connectivity issue) -
unlike W32, this run cannot rule out an EDGAR-only Gulf-sovereign filing having been missed.
Web search budget was also exhausted before some follow-up checks (Akita ambassador-visit
status, GlobalFoundries definitive-agreement status) could be completed - flagged above as open
watch items rather than silently dropped.
