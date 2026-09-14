# Individuals — 2026-W38 summary

## Headline
A thin week for genuinely NEW personal-capital events. The individuals class has been
swept hard in W32/W35/W36/W37 (confirmed via `python -m engine.edgar exists` against
the live db, not the run's context.json pack, which understated coverage — it showed
0 events-on-file for every entity while the actual `events` table already carried 13
rows for Peter Thiel alone, 8 for Jeff Bezos, 3 each for Elad Gil/Dylan Field/Garry Tan,
etc.). Most fresh-looking leads this run (Etched/Thiel, CuspAI/Bezos, Dili/Garry Tan,
Odyssey/Elad Gil) turned out to already be on file from prior weeks — correctly caught
by the `exists` check before writing, avoiding duplicate rows.

## What's new
- **Elad Gil -> NavigateAI, $25M seed at $225M valuation (verified_alpha).** NavigateAI
  (Eric Wu's, ex-Opendoor CEO, new company building AI copilots for construction/trades
  workers) came out of stealth on 2026-09-07 via TechCrunch, revealing a seed round that
  had actually closed quietly back around May 2026 when the company soft-launched. Gil
  led the round; Khosla Ventures, Fifth Wall, Tishman Speyer and electrical contractor
  Helix Electric participated, alongside operator-angels Tony Xu (DoorDash), Apoorva
  Mehta (Instacart) and Brian Armstrong (Coinbase) — all flagged in
  `discovered_allocators.csv` as untracked co-investors worth a watch-tier add. This is
  a good example of the class's core pattern: capital moves quietly, disclosure lags by
  months, and the round-announcement/stealth-exit story (not a filing) is what surfaces it.

## What didn't pan out (escalated, then dropped or left to prior-week rows)
- Sam Altman/Alfred (physical-AI stealth backing) and the Meta/NFDG fund buyout are both
  real but dated June 2026 / July 2025 respectively — outside the ~45-day window even
  with this class's wider lookback.
- Vitalik Buterin's $45M ETH commitment to open-source security/privacy projects is
  dated January 2026 (outside window) and, even on-window, sits outside our canonical
  sectors (not AI-adjacent) — would file as a weak-fit candidate at best.
- Vinod Khosla's Seattle Seahawks purchase (~$9.6B, closing September 2026) is real
  personal capital but out of sector scope for this platform (sports franchise, not
  AI/compute/energy/defense) — not filed.
- Rillet's Series C naming Roelof Botha as an early backer is a Sequoia Capital
  position, not personal capital — belongs to the VC agent, not here.
- Neil Mehta/Greenoaks Q2 activity (TSMC, SpaceX, Cerebras) is fund-level 13F
  positioning, not a personal check — same reasoning, out of scope for this class.
- No new Form D "related persons" hits: ran `engine.edgar filings <name> --forms D
  --since 2026-07-31` for ~23 watchlist names (Thiel, Altman, Gil, Rabois, Lonsdale,
  Stephens, Hoffman, Wang, Gross, Friedman, Asparouhov, Luckey, Andreessen, Khosla, Son,
  Tan, Field, Guo, Deming, Russell, Sacks, Nosek, Levchin) — none resolve to a CIK under
  their own name, consistent with individuals.md's warning not to lead with SEC filings
  for this class.

## Coverage gaps / what to watch next week
- WebFetch was fully egress-blocked for every external domain this session (TechCrunch,
  GlobeNewswire, SEC.gov, CNBC, Wikipedia, etc. all returned EGRESS_BLOCKED) — all
  sourcing this run relied on WebSearch's own synthesis of article content plus the
  resolved URLs it returned, not a direct fetch-and-read of the page. Source URLs cited
  are real, specific documents (never search-query URLs), but a future run should
  re-verify the NavigateAI row's investor list directly against the TechCrunch piece if
  WebFetch access is restored.
- WebSearch budget was exhausted mid-run (200/200 calls), cutting off planned sweeps of
  the remaining untouched watchlist names (Ben Horowitz, Josh Kushner personal checks,
  Brad Gerstner, Philippe Laffont, John Collison, Ali Ghodsi, Mike Maples Jr., Bill
  Gurley, Peter Barrett, Hemant Taneja, Bill Janeway, Ken Howery, Jawed Karim, Steve
  Chen, Premal Shah, Ritesh Agarwal, Boyan Slat, the macro names (Ackman/Tepper/Dalio),
  and the corporate-CEO names) — all currently show 0 events on file and should be
  swept first next run.
- Several prior-week candidates remain unconfirmed (Palmer Luckey/Erebor, Reid
  Hoffman/Prentis, Reid Hoffman/SkillBench) — checked for a fresh Form D under the
  company name this run (no CIK found for Erebor/Prentis/SkillBench), so they stay
  candidates; worth a full-text EDGAR pass (cited only if a real document resolves).

## Row counts this run
- verified_events.csv: 1 (status verified_alpha)
- candidate_events.csv: 0
- discovered_allocators.csv: 3 (Tony Xu, Brian Armstrong, Apoorva Mehta)
