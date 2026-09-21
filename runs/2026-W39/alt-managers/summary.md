# Alt-Managers — 2026-W39

## Headline
Five verified rows, two candidates, across 5 of the 9 watchlist names (KKR x2,
Blue Owl, Brookfield, Goldman Sachs). SoftBank, BlackRock/GIP and DigitalBridge
produced no new capital-allocation event inside the ~30-day window despite
broad searching — each had adjacent noise (SoftBank's OpenAI-funding debt
raises, BlackRock/GIP's July close of Aligned Data Centers, DigitalBridge's
pending SoftBank take-private) but nothing that is itself a fresh commitment
or deployment this period.

## Biggest signals
1. **Korea's AI data-center buildout is being financed by Western alt-managers.**
   KKR took a 29% stake in SK Telecom's new AI data-center unit, SK Horizon
   (KRW 3.08tn combined with Korean co-investors IMM/Stonebridge, 2026-08-27),
   and separately completed the KKR-Singtel consortium's full buyout of
   Singapore's ST Telemedia Global Data Centres (~US$5.1-5.2B for the final
   82%, EV ~US$10.9B, completed 2026-09-02/03). Two large, real Asian
   data-center control/stake events from one allocator in the same window.
2. **Private credit keeps underwriting GPU purchases directly.** Blue Owl
   (with PIMCO) led a $2.4B debt package so IREN can buy NVIDIA Blackwell
   Ultra GPUs for its Canada campus (2026-08-28) — equipment financing, not
   equity, at a 9% coupon. This is the same private-credit-for-compute
   pattern as the Meta/Blue Owl Hyperion deal, just smaller and faster to
   close.
3. **Nuclear-linked dry powder, not yet AI-earmarked.** Brookfield won a
   $1B initial mandate from the UK's Nuclear Liabilities Fund (2026-09-08) —
   real, Tier-1-confirmed capital, but a general multi-strategy SMA rather
   than a named AI/datacenter deployment; flagged sector=nuclear and called
   out in notes as adjacent, not core, AI-buildout capital.

## What didn't make verified
- Blackstone is reportedly targeting **$8B** for its 4th energy-transition/
  digital-infra private-credit fund (Bloomberg, 2026-09-15) — a target, not a
  close, and single-origin (every other outlet cites the same Bloomberg
  story), so filed as candidate with amount_usd blank.
- Apollo's only AI-adjacent lead this window is a "low tens of millions"
  (sourcing conflicts with a separate "$1-10M" figure) ticket into Mercor's
  in-progress round — single Tier-5-derivative source, filed as candidate,
  amount left blank rather than guessed.

## Operating note — network restriction this run
`python -m engine.edgar` (Bash) could not reach EDGAR — every call failed
with `Tunnel connection failed: 403 Forbidden` from this session's egress
proxy, so the deterministic `exists` de-dup check and `filings` sweep could
not be run for any of the 9 names. WebFetch was also blocked for the large
majority of domains touched this run (sec.gov, businesswire.com,
prnewswire.com, blueowl.com, kkr media, nasdaq.com, finance.yahoo.com,
datacenterdynamics.com, mingtiandi.com, alternativeswatch.com, reuters.com,
and more) — all research here was done via WebSearch's own fetch-and-summarize
path, citing the specific resolved article/press-release URL each finding
came from (never a search-query URL). Given `context.json` showed
`events_on_file: 0` / `last_event_date: null` for all 9 entities, duplicate
risk this run is low, but the engine-side ingest should still run its own
`exists` pass before merging.

## Watch next week
- SoftBank's third $10B OpenAI follow-on tranche is scheduled to execute
  2026-10-01 (per SoftBank's own 2026-02-27 press release program) — expect
  a disclosed capital-movement event right at the start of next window,
  funded by the $11B+ junk-bond and $11.9B loan facilities raised this week.
- Blackstone Green Private Credit Fund IV — check for an official
  Blackstone.com close announcement (would upgrade candidate → verified).
- BlackRock/GIP and DigitalBridge had no event this run; re-check GIP's
  power-generation / Allete-style vertical-integration deals and
  DigitalBridge Credit's loan pipeline (60+ loans reported "in the works").
