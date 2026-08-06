# Public Filings - 2026-W32

Two jobs: confirm other agents' candidates via Tier-1 filings, and discover
capital-allocation events straight from SEC EDGAR that others missed. All rows
here are `source_tier: 1` by definition. SEC EDGAR full-text (efts.sec.gov) and
the submissions API were reached via curl with a UA header (WebFetch 403s).

## What I confirmed (candidate -> verified)
- **Founders Fund Growth IV -> $6.02B fund_launch (CONFIRMED).** The
  individuals agent carried this as a Tier-3 candidate (Thiel personal
  commitment). SEC **Form D** (Founders Fund Growth IV, LP, CIK 2112131, filed
  2026-03-23) states `totalOfferingAmount = totalAmountSold = $6,024,585,000`,
  first sale 2026-03-06, and lists **Peter Thiel** as a related person. That
  hardens the ~$6B press figure to an exact filed number (amount_estimated
  0->1... set to 0) and upgrades the row to verified/Tier-1.

## What I discovered (new, not held by any other agent)
- **Galaxy Digital -> $3.507B project finance for a 400MW Texas AI data center.**
  8-K (Items 1.01/2.03, filed 2026-07-28): subsidiary Galaxy Helios Data Centers
  II LLC closed $3,507,000,000 of 9.875% Senior Secured Notes due 2031 (Rule
  144A, Morgan Stanley lead) to build two buildings / eight data halls =
  400MW utility / 260MW critical IT on ~260 acres in Dickens County, TX (the
  Helios campus). Clean, exact, in-taxonomy (datacenters / project_finance).

## Checked but NOT confirmed / out of scope
- **Coatue "first retail-only fund" ($8B, vc candidate):** the only recent
  Coatue Form D that surfaced is COATUE LONG ONLY PARTNERS LP - an existing
  2013-vintage vehicle ($2.46B sold, indefinite offering), NOT the new retail
  fund. No Tier-1 confirmation; left as-is for the vc agent.
- **Etched ($300M Series C), Atoms ($1.7B), Cathedral ($160M):** no issuer Form
  D in-window. Only third-party co-invest SPVs appear (e.g. "Etched Angels IV
  July 2026", "LFG Atoms a Series of LFG VC LLC") - Tier-1 evidence the rounds
  are real/closing, but they don't disclose the headline round's lead or size,
  so I did not emit them as events.
- **NVIDIA/SSI and Meta/BlackRock El Paso:** already Tier-1 via IR PRs. NVIDIA
  filed no SSI 8-K; Meta's only recent 8-K (2026-07-29) is Q2 earnings (Item
  2.02), not the JV. No extra confirmation available.
- **Brookfield AM -> Oaktree (remaining 26%, ~$3.0B, closed 2026-07-31):** a
  clean Tier-1 acquisition 8-K, but off-taxonomy (asset-manager consolidation,
  not AI buildout). Logged, not emitted.

## Confidence / limitations
High confidence on both emitted rows (primary SEC filings with exact figures).
Coverage limited by the private nature of most VC rounds - issuers of
exempt-offering rounds either had not filed Form D within the window or filed
under names that don't full-text match. 13F is quarterly/lagged and not used for
fresh alpha this week.

## Watch next week
- Galaxy Helios II debt-service / additional Helios tranches; CoreWeave lease
  disclosures against the campus.
- Late Form D filings for Etched / Atoms / Cathedral issuer entities.
- Meta 10-Q (El Paso JV / Project Sopaipilla accounting detail).
