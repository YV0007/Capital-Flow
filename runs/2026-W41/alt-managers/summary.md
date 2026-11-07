# Alt-Managers — Week 2026-W41

## Headline
Three verified, Tier-1-anchored capital events this week, plus three candidates
that need a stronger confirm. The through-line: SoftBank converted on two fronts
at once (closed the final $10B OpenAI tranche AND closed its own $3.1B buyout of
fellow-watchlist name DigitalBridge, same week), while Apollo's financing arm
keeps showing up as the "pickaxe seller" behind physical AI buildout — this time
backing a >$15B power-anchored data center in Japan.

## Rows written
- **verified_events.csv: 3 rows** (all status=verified, source_tier=1)
- **candidate_events.csv: 3 rows** (all status=candidate, source_tier=3, single-origin
  Bloomberg reporting or explicit plan-stage — none met the bar for verified_alpha)
- **discovered_allocators.csv: 3 rows** (RHAELM Holdings, JERA, Crux AI)

## Top signals
1. **SoftBank → OpenAI, $10B, verified (Tier 1).** Third and final tranche of the
   $30B follow-on commitment, executed 2026-10-01 per SoftBank's own IR release.
   Cumulative SoftBank stake in OpenAI is now $64.6B (~13%). This closes out a
   three-tranche program (Apr/Jul/Oct) — don't re-file the earlier two tranches,
   they're outside this window and were presumably filed in prior runs.
2. **SoftBank → DigitalBridge, $3.1B, verified (Tier 1).** Closed 2026-09-30,
   $16.00/share cash; DigitalBridge delisted from NYSE and becomes a controlled
   SoftBank subsidiary. Notable because **both sides are on our own watchlist** —
   one key alt-manager acquiring another. Recommend flagging DigitalBridge for a
   watchlist-status review (it's now a SoftBank subsidiary, not an independent
   allocator) in the next allocators.yaml pass.
3. **Apollo → RHAELM/JERA/Dell (Chiba, Japan), project_finance, verified (Tier 1).**
   RHAELM's own release names Apollo as its strategic investment/financing partner
   on a >$15B AI-datacenter build powered by JERA (Japan's largest power generator,
   up to 400MW) with Dell supplying rack-scale infrastructure. Apollo's own slice
   is undisclosed — amount_usd left blank, headline $15B flagged amount_estimated=1
   per the class brief's target-vs-committed rule.

## Candidates needing a stronger confirm
- **Goldman Sachs → Crux AI, $22B chip-backed loan (candidate, Tier 3).** 10-bank
  consortium incl. Goldman financing TPU purchases for Blackstone/Alphabet's Crux
  AI JV. Single-origin Bloomberg (2026-09-16); every other outlet found explicitly
  cites "Bloomberg News reports" — circular-reporting guard kept this at candidate.
  Worth re-checking Crux AI / lead-bank PR or an SEC filing next run.
- **Brookfield → BAIIF, Nvidia's $2B anchor LP stake (candidate, Tier 3).** Investor
  documents reportedly reveal Nvidia's $2B commitment to Brookfield's $10B AI
  Infrastructure Fund for the first time (2026-09-17). Found the likely source —
  a Brookfield Asset Management 8-K exhibit on EDGAR (CIK 1937926) — but **could
  not fetch it**: WebFetch to sec.gov was blocked by egress policy this run (see
  constraint note below). Flagging for next run's EDGAR sweep to upgrade to verified.
- **Blue Owl → proposed Data Center REIT, ~$6.5B seed (candidate, Tier 3).**
  Explicitly plan-stage ("remains under discussion... may change" per the
  reporting) — graded candidate on principle regardless of source count, since no
  capital has firmly moved yet.

## Discovered allocators
- **RHAELM Holdings** (UK AI-infra developer) and **JERA** (Japan's largest power
  generator) — both recurring counterparties on the Apollo-financed Chiba project,
  and RHAELM is explicitly planning to replicate the model in other markets.
- **Crux AI** (Blackstone/Alphabet TPU cloud JV) — now has its own $22B debt stack
  and may be worth tracking as an entity in its own right, not only via sponsors.

## What didn't make the cut (and why)
- KKR's Helix Digital Infrastructure drawing a $1B Samsung investment (2026-09-29)
  — real event, but Samsung is the allocator deploying capital here, not KKR; better
  filed by the corporate-class agent.
- Williams' $5.34B Blackstone/Apollo/KKR behind-the-meter power deal and KKR's
  $19.2B Global Infrastructure Investors V close — both real but disclosed in
  July/early August 2026, outside the ~30-day window; noted in source_log as
  checked-but-not-filed.
- The widely-recirculated "Crusoe/Blue Owl/Primary Digital $15B Abilene phase 2"
  story is actually from May 2025 — several aggregators resurface it with current
  dates. Confirmed against the original Crusoe newsroom post and excluded as stale,
  per the "don't re-find old deals" / stale-recency trap called out in CONTEXT.md.
- A Tracxn listing dated SoftBank Vision Fund → Helion "2026-09-15" turned out, on
  closer check, to be the January 2025 $425M round resurfacing with a stale
  "latest activity" date — excluded rather than filed as new.
- BlackRock/GIP's $1.8B TotalEnergies African pipeline deal (2026-09-19) is real
  and in-window but doesn't fit the canonical AI-buildout sector taxonomy
  (traditional oil & gas infrastructure, not AI-compute/power-for-AI) — excluded
  as out of mission scope rather than force-fit into a sector.

## Constraint note
As in recent runs, **WebFetch and direct `engine.edgar` network calls were blocked
by egress policy** this run (confirmed via `python -m engine.edgar filings` →
`Tunnel connection failed: 403 Forbidden`, and via WebFetch → `EGRESS_BLOCKED` on
group.softbank and sec.gov). The local, non-network `engine.edgar cik` and
`engine.edgar exists` commands worked fine and were used to resolve CIKs and check
for duplicates before filing (none found — context.json showed 0 events on file
for every alt-managers entity this week). For sourcing, I used WebSearch's own
returned reads of each page (including the official SoftBank and RHAELM press
pages) and cited the resolved article/press URLs it surfaced — never a bare
search-query link. Two rows (Brookfield/BAIIF, Goldman/Crux AI) stayed at
candidate specifically because I could not independently fetch the primary
document (an SEC 8-K exhibit) to upgrade them past a single Bloomberg origin;
that's the main thing to re-check next week if network access is restored.

## Watch next week
- Brookfield Asset Management 8-K (CIK 1937926) confirming the Nvidia $2B BAIIF
  commitment — would upgrade that row to verified.
- Whether the Goldman-led Crux AI $22B loan actually prices/closes (currently
  "lining up" / in syndication).
- DigitalBridge's status now that it's a SoftBank subsidiary — may need a
  watchlist/allocators.yaml update.
