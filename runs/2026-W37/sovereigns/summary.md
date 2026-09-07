# Sovereigns — 2026-W37 summary

**Coverage window:** ~2026-08-08 to 2026-09-07, watchlist = MGX, Mubadala, Saudi PIF, US Government.

## Counts
- verified_events.csv: 3 rows
- candidate_events.csv: 2 rows

## Biggest signals

1. **AWS x HUMAIN "AI Zone" — $5B+ joint commitment (2026-09-02, verified, Tier 1).**
   Announced at LEAP 2026 in Riyadh: AWS and HUMAIN (PIF's AI vehicle) will jointly put
   more than $5B behind a shared AI Zone in Saudi Arabia — up to 50MW of AWS Trainium /
   NVIDIA capacity by 2028. Confirmed on AWS's own newsroom (aboutamazon.com). PIF's own
   slice of the $5B isn't broken out, so amount_usd is blank and amount_estimated=1 —
   this is a partnership headline, not a disclosed PIF cash outlay.

2. **MGX co-leads Databricks' $5B round at a $190B valuation (2026-08-13, verified_alpha).**
   MGX joined Coatue, Blackstone, T. Rowe Price and Sixth Street Growth. No outlet
   disclosed MGX's individual check size, so amount_usd is blank with round_total_usd
   carrying the full $5B and valuation_usd the $190B mark — avoids the "valuation in the
   amount column" mistake.

3. **US Department of War takes a ~10% equity stake in Trilogy Metals for $35.6M
   (executed 2026-08-28, verified, Tier 1 — official war.gov release + company 8-K).**
   Backs the Upper Kobuk Mineral Projects (copper/cobalt/germanium) in Alaska via the
   Ambler Metals JV with South32 — part of the same critical-minerals equity-stake
   pattern as MP Materials/USA Rare Earth, but those two are outside this week's window
   (Jul 2025 and Jan 2026 respectively) so were not re-filed.

## Candidates (weak leads, escalated, still unconfirmed)
- **Mubadala weighing ~$6.3B for a 500MW AI data center in Akita, Japan** (Bitgrit/S2
  project). Single-origin Bloomberg report (2026-08-06); every other outlet found cites
  Bloomberg directly (circular-reporting guard applied, counted as one source). No
  Mubadala IR confirmation, no SEC/registry hit — filed candidate, amount_estimated=1.
- **HUMAIN reportedly planning a $2.5B data center investment fund** (2026-09-03,
  Bloomberg/Techmeme) to back ~250MW built with Al Moammar Information Systems. This is
  capital HUMAIN wants to *raise from* outside investors, not PIF's own committed money —
  filed candidate under Saudi PIF with amount_estimated=1 and the distinction noted.

## Rejected / not re-filed (old news resurfacing)
- The AMD–HUMAIN "$10B AI infrastructure" figure re-surfaced heavily at LEAP 2026
  (Aug 31–Sep 3) as "AMD Instinct systems now live in Saudi Arabia," but AMD's own IR
  press release for the $10B commitment dates to May 2025 — this week's news is an
  operational go-live milestone, not new capital. Not filed as an event.
- Commerce's $874M CHIPS letters of intent (GlobalFoundries, Kepler, etc.) and the
  USA Rare Earth equity stake both predate the window (2026-07-29 and 2026-01-26).
- MGX Fund I ($49B close, 2026-07-01) and the Mubadala Capital credit platform are
  already on file per context.json's what_you_got_wrong examples — not re-filed.

## Coverage gaps / notes for next run
- **EDGAR/gov-site fetch was blocked in this environment**: `data.sec.gov`, `sec.gov`,
  `war.gov`, `nist.gov`, and most news-outlet domains returned EGRESS_BLOCKED on
  WebFetch, so rows here are sourced from WebSearch result snippets/summaries citing
  resolved article URLs, not full WebFetch reads. `engine.edgar` itself resolves CIKs
  from the local DB (no live SEC calls were needed for the `exists` checks used here),
  but a live filings sweep would have hit the same block.
- Saudi PIF capital overwhelmingly flows through HUMAIN, not PIF-branded press — see
  discovered_allocators.csv (re-flagged, third week in a row).
- US Government: no new AI-specific DoE/DoD grant or CHIPS award observed strictly
  inside the window beyond the Trilogy Metals stake; worth re-checking early-to-mid
  September for any DoE Office of Energy Dominance Financing or CHIPS Program Office
  announcements that land after this run's cutoff.
- Next week: check whether Mubadala's Japan data center talks convert to a signed deal,
  and whether HUMAIN's $2.5B fund actually closes a first tranche.
