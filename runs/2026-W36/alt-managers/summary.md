# Alt-Managers — 2026-W36 summary

## Environment note
`python -m engine.edgar` (the deterministic EDGAR CLI) and the `WebFetch` tool
were both blocked by this session's network egress policy for every host tried
(data.sec.gov via the CLI returned 403 at the proxy; WebFetch returned
EGRESS_BLOCKED for every domain attempted, including sec.gov, bloomberg.com,
apollo.com, mingtiandi.com, w.media, finance.yahoo.com and others). All
research this run relied on `WebSearch` only, citing the resolved article/PR
URLs it returned. No `engine.edgar exists` deduping was affected — that tool
worked fine over the proxy for the dedupe checks — only the filings-fetch and
raw-page-fetch paths were unavailable. Worth flagging to the operator: EDGAR
filing sweeps (8-K/Form D) could not be run this week.

## Filed this run
- **verified_events.csv**: 6 rows
- **candidate_events.csv**: 2 rows
- **discovered_allocators.csv**: 3 rows (Jane Street, PIMCO, IMM Investment)

## Biggest signals

1. **Blue Owl leads a $2.4B GPU-equipment financing for IREN** (2026-08-28) —
   a $1.2B term loan + $1.2B senior secured notes, PIMCO co-backing, funding
   NVIDIA Blackwell Ultra purchases for IREN's Mackenzie, BC campus. This is
   the "equipment finance at AI scale" model Blue Owl is now repeating
   (following the $27B Meta/Hyperion SPV notes) — asset-backed GPU debt is
   becoming its own product line for the alt-managers.

2. **KKR takes a 29% stake in SK Telecom's new AI-datacenter spinout, SK
   Horizon** (2026-08-27), alongside a Korean IMM/Stonebridge consortium
   (20%) — $2.23B combined. Brookfield separately committed up to $9B
   (nonbinding) to NAVER's GAK Sejong AI factory with NVIDIA in late July.
   Korea is emerging as a real secondary front for alt-manager AI-infra
   capital, alongside the US/Australia core.

3. **Blackstone joins Firmus's $2B strategic equity round** (2026-08-07,
   Firmus now >$10.5B post-money) alongside Coatue, NVIDIA and new entrant
   Jane Street — continuing Blackstone's pattern of following its own debt
   financing (the ~$10B facility earlier in 2026) with equity.

4. **Coverage backfill**: SoftBank's ~$4.0B definitive agreement to acquire
   DigitalBridge (signed 2025-12-29, shareholder-approved 2026-04-23, still
   not closed) was missing from the sheet entirely despite both firms being
   tracked key allocators. Filed as verified (signed + approved, but
   event_date left blank since no cash has moved) — worth a dedicated watch
   for the actual H2-2026 close.

## Stale-candidate chase (14 flagged) — results
- **Resolved / already handled elsewhere**: the SoftBank/ABB-Robotics $1.75B
  loan candidate is superseded by an existing **verified** row already on
  file (id 22, W32, Bloomberg 2026-07-21) — no action needed, just noting the
  stale-candidate list itself is a bit behind.
- **No material update found** (left as-is, not re-filed): Blackstone Japan
  $30B AI-datacenter plan (still a stated 3–5yr intention, no vehicle);
  Apollo Mexico $20B private-credit target (still a target, no pipeline);
  Blue Owl/Stack Melbourne A$8.5B loan (still early-stage bank talks per
  latest coverage); Blue Owl/Meta Hyperion Louisiana (the July capex-scale-up
  headline is a Meta-side program figure, not a new Blue Owl commitment); all
  6 NVIDIA AI Compute Infrastructure Financing Platform MOU rows (Apollo,
  BlackRock, Blackstone, Brookfield, Goldman Sachs, KKR — confirmed via
  fresh search that no partner has disclosed a dollar figure or named a first
  project yet).
- **Updated with fresher detail, still candidate**: AirTrunk SYD3 — now an
  8-bank prospective syndicate (added MUFG, UOB to the known list), still no
  confirmed signing date.
- **Likely superseded (flagged, not re-filed as new)**: the SoftBank/Gravis
  Robotics AG "acquisition" candidate (2026-07-24, >$500M valuation,
  exploratory) appears to be the same underlying story that resolved into
  the already-verified $200M Gravis Robotics Series A (2026-08-17) rather
  than a separate acquisition — worth a downstream merge/dedupe check.

## New candidate lead
- SoftBank in talks for a majority stake in humanoid-robot maker 1X
  Technologies at a ~$6B valuation (The Information, 2026-08-26/27,
  single-origin, terms could change) — filed as candidate.

## What to watch next week
- SoftBank/DigitalBridge actual close (expected H2 2026).
- Whether any of the six NVIDIA-anchored financing platforms names a first
  project or dollar figure.
- AirTrunk SYD3 and Stack/Melbourne loan signings.
- Whether SoftBank's 1X Technologies talks convert to a signed deal.
