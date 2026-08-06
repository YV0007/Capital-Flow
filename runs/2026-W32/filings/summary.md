# Public Filings Agent — 2026-W32

**Access note:** SEC EDGAR blocks WebFetch (HTTP 403), but the EDGAR full-text
search API (`efts.sec.gov`) and document archive both work via `curl` with a
declared User-Agent header. Every `source_tier: 1` row below is a primary filing I
actually opened.

## What I confirmed (Tier-1)

- **Brookfield -> Bloom Energy on-site power partnership (project_finance).** Already
  verified by the alt-managers agent via the businesswire PR; I added the primary
  SEC filing. Bloom Energy's **Q2 2026 Form 10-Q** (filed 2026-07-28), Note 7,
  confirms the structure: JVs "housed in an AI Infrastructure Fund created by
  Brookfield," Brookfield as principal owner/primary beneficiary, $22.8M into the JVs
  in H1 2026, revenue from "multiple projects executed through the joint venture with
  Brookfield." The 10-Q does not restate the "up to $25B" program size (PR-sourced),
  so amount_estimated=1.

## What I newly discovered (Tier-1 Form D feeders)

Four small Form D filings other agents missed. All are **off-watchlist SPV / angel
vehicles** pooling into tracked AI targets — genuine capital-in-window evidence, but
none names the lead allocator, so none upgrades a tracked row. Logged as `candidate`:

- **LFG Atoms SPV -> Atoms** — $1.335M (Form D 2026-07-15). Corroborates the
  a16z-led ~$1.7B Atoms round (verified_alpha), does not name a16z.
- **Etched Angels IV (Jul 2026) -> Etched** — $479.55K (2026-07-15), aligned with the
  Sequoia-led $300M Series C.
- **Etched Angels III (May 2026) -> Etched** — $8.76M (2026-07-13); "May" series
  suggests an earlier raise, timing caveat.
- **Databricks (Moreno VC) SPV -> Databricks** — $1.955M (2026-07-13). Corroborates
  private capital into Databricks; far smaller than, and does not name, the
  Coatue-led round.

## What I could NOT confirm, and why

This week's headline candidates are overwhelmingly **private-market deals** that were
either already confirmed at Tier-1 by other agents via official PRs, or leave no SEC
trail in the W32 window:

- **Databricks/Coatue, Khosla $5.5B fund family, Altimeter/Thrive, Cathedral,
  SoftBank's $40B OpenAI loan, MGX Fund I, Blackstone AirTrunk/QTS, Blue Owl Stack** —
  no company-level Form D or 8-K found in-window. Cathedral, Thrive and Databricks'
  own entity returned zero Form D hits; Khosla's only in-window Form D is a $60.5M
  co-invest SPV, not the $5.5B fund family (still "in talks"). MGX (Abu Dhabi) and the
  SoftBank syndicated loan are non-SEC.
- **US Gov nuclear / Oklo / X-Energy $200M program** — no Tier-1 energy.gov release
  found for the July 2026 AI-nuclear effort naming committed awards to specific
  targets. The DOE Reactor Pilot Program energy.gov page is Aug 2025 and states
  companies bear their own costs; the AI-licensing page is Mar 2026. Oklo's only
  in-window 8-K (event 2026-07-22) is about officer appointments, not the program.
  Stays `candidate`.
- **"Anthropic Capital Fund, LP"** Form D (2026-07-30, $2.1M) is an unrelated
  investment fund (principals Joe Miller / Timothy Hightower), NOT Anthropic PBC —
  discarded to avoid a false positive.

## Bottom line

1 Tier-1 filing confirmation added (Brookfield/Bloom via 10-Q — corroborates an
already-verified row, no status change), **0 net new upgrades** of candidate/
verified_alpha rows to verified, and **4 new discovery rows** (small SPV feeders).
Confidence high on everything emitted (all primary filings opened directly);
principal limitation is structural — this cycle's flows are private deals confirmed
by official PRs rather than SEC filings, so EDGAR offered little fresh Tier-1 alpha.
