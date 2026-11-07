# Sovereigns — 2026-W38 summary

## Coverage
Watchlist: MGX, Mubadala, Saudi PIF, US Government. Window: disclosures roughly
2026-08-15 to 2026-09-14. Checked `engine.edgar exists` before filing every
row; two strong MGX leads (Databricks $5B round, Aligned Data Centers $40B
acquisition + $5B growth capital) turned out to already be on file (verified,
run weeks W34/W32) and were **not** re-filed.

## What moved
- **US Government wrote three real checks this window, all disclosed 2026-09-08:**
  a **$1.9B DOE loan** to restart NextEra's Duane Arnold nuclear plant (615MW,
  Iowa) -- the power is contracted 25 years to Google for AI/cloud load, making
  this the second DOE loan (after the ~$1B Constellation/Three Mile Island
  deal) explicitly reviving shut nuclear capacity for AI demand. Same day,
  Commerce finalized **two CHIPS Act quantum-computing R&D awards**:
  **$375M to GlobalFoundries** (domestic quantum foundry) and **$100M to
  Rigetti** (superconducting quantum R&D, plus a ~$100M equity kicker of
  7.74M shares -- same structure as the Intel CHIPS deal). All three are
  Tier-1 sourced (energy.gov / NIST / SEC 8-K) and filed `verified`.
- **Saudi PIF's AI arm is going out to raise, not just spend:** HUMAIN is
  seeking **$2.5B** for a BSF Capital-managed data center fund, with **$1.2B
  already reportedly committed by Saudi Arabia's National Infrastructure
  Fund** -- a sovereign vehicle not currently on our watchlist (flagged in
  `discovered_allocators.csv`). Filed `candidate` under Saudi PIF since
  HUMAIN is wholly PIF-owned but PIF's own cash contribution isn't disclosed
  and the raise hasn't closed.
- **Mubadala is "weighing" a record ~$6.3B AI data center bet in Akita,
  Japan** (JPY1tn, part of a ~$12.6B total project with startup Bitgrit and
  S2 Group). Ran the escalation loop -- re-searched through 2026-09-14 for a
  signing/close and found none; every outlet still frames it as talks. Kept
  `candidate` with `amount_estimated=1` per the class brief (don't let a
  round-number pledge read as committed capital).

## Filtered out (not filed)
- Mubadala's reported ~$1B minority stake in **Luckin Coffee** (disclosed
  2026-09-10) is a real, well-sourced deal but doesn't map to any canonical
  sector (ai-labs/compute, semiconductors, fab-equipment, cloud/neocloud,
  datacenters, power/nuclear, networking, robotics, defense-tech) and sits
  outside this platform's AI-capital-flow scope -- left out of both CSVs
  rather than forced into a nonsense sector.
- MGX's $49B Fund I close and its OpenAI/Anthropic/xAI follow-ons are all
  from Feb-Jul 2026 -- outside the ~30-day window and, per context.json,
  already known to the engine (flagged there for missing ai_posture/holdings
  metadata, which is a downstream/ingest concern, not a sourcing gap).

## Watch next week
- HUMAIN's $2.5B fund raise (CMA approval could take 2-3 months per
  Bloomberg) and whether Blackstone/BlackRock convert interest into a
  committed tranche.
- Whether Mubadala/Akita produces a signed term sheet.
- National Infrastructure Fund (Saudi) as a new sovereign to track directly.

## Environment note
WebFetch was network-blocked for essentially every external domain tried
this run (energy.gov, sec.gov/data, nexteraenergy.com, mgx.ae, mubadala.com,
bloomberg.com, fortune.com, wikipedia.org, prnewswire.com, techcrunch.com,
globalswf.com, global-infra.com, caproasia.com -- all rejected at the egress
proxy). All sourcing above relied on WebSearch's returned resolved article
URLs (never a search-query URL) plus its extracted content; SEC citations
are direct Archives/edgar document links surfaced by search, not full-text-
search URLs. Flagging this because it's a material sourcing constraint, not
a shortcut taken by choice.
