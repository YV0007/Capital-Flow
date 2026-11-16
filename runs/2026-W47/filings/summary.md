# Filings Agent — 2026-W47 Summary

## Confirmations (job 1: chase the other agents' candidates)

- **Altimeter $2.5-3B fund_launch (vc candidate) → VERIFIED.** Form D filed
  2026-11-09 by *Altimeter Premier Growth IX, L.P.* (CIK 0002151688): total
  offering $2,500,000,000, min investment $2M, $0 sold to date. The dollar
  figure and disclosed_date match the Bloomberg-sourced candidate exactly —
  this is clearly the vehicle Bloomberg was describing. Re-filed as a new
  `verified`, `source_tier=1` row so ingest keeps the stronger status. The
  reported ~$800-900M "companion early-stage fund" is **not** separately
  confirmed — Altimeter Venture Partners Fund VIII's only Form D is from
  March 2026, not a new vehicle this week — so that second-fund claim stays
  unconfirmed, per the original candidate's own caveat.
- **NVIDIA / d-Matrix (corporate candidate) → still unconfirmed.** NVIDIA's
  two most recent 8-Ks (2026-09-03, 2026-11-12) were checked; the Nov 12 one
  is a CEO transition (Jensen Huang resigned, Colette Kress interim CEO —
  itself newsworthy but out of scope, not a capital event) and neither
  mentions d-Matrix. No Form D for d-Matrix (private co) on EDGAR. Left
  alone, not re-filed.
- **Vinod Khosla / Wajo (individuals candidate) → still unconfirmed.** No
  Form D naming Wajo found under any Khosla Ventures SPV. The only
  Khosla-linked Form D activity this window (Khosla Ventures GI SPV II,
  Khosla Ventures MM SPV) doesn't reference Wajo. Left alone.
- Alt-managers and sovereigns candidate files were empty, as flagged — nothing
  to chase there.

## New filings-only discoveries (job 2: direct EDGAR sweep)

- **Brookfield → NAVER/NVIDIA Korea AI factory, up to $9B (verified, Tier 1).**
  Brookfield's own Q3 2026 earnings release (8-K Item 8.01 / Exhibit 99.1,
  filed 2026-11-06) states under Infrastructure: "NAVER and NVIDIA: Agreed to
  invest up to $9 billion in next-generation AI computing infrastructure in
  Korea." This is the company's own primary disclosure firming up July 2026
  press reports of a nonbinding term sheet (GAK Sejong AI factory expansion,
  NVIDIA DSX 55MW→200MW by 2028, ~$10B total project, NVIDIA ~$1B). Filed
  only Brookfield's $9B slice — NVIDIA's reported ~$1B piece has no primary
  confirmation of its own, so it was not filed as a separate row. Not
  previously on file (Brookfield had 0 events on file per context.json).
- **SK hynix → Penguin Solutions, $377.2M minority stake (verified, Tier 1).**
  Schedule 13D filed 2026-11-03 by SK hynix Inc. via new subsidiaries HYAICO
  Corporation / SHIFTIX1 LLC: 200,000 shares convertible preferred (9.1%
  as-converted), $377,162,666 cash, transaction closed 2026-10-29, bought
  from an SK Telecom SPV (Astra AI Infra LLC). Comes with board-nomination
  and participation/registration rights. Corroborated by SK Telecom's own
  13D/A on the seller side (2026-11-02). SK hynix was not on the watchlist —
  added to discovered_allocators.csv as a corporate allocator worth tracking
  (a major memory/semiconductor maker taking board-level equity stakes in
  AI-data-center infrastructure companies).
- Swept Microsoft, Amazon, Alphabet, Meta, Oracle, NVIDIA, Blackstone,
  BlackRock, Goldman Sachs, KKR 8-Ks/press-release exhibits filed since
  2026-11-01: all were debt/equity capital-raising (notes offerings,
  buybacks), routine Form 4 insider sales, or governance items (board
  departures, preferred-stock redemption) — none named a specific
  capital-allocation target this week beyond what's above. KKR's and
  Brookfield's Q3 earnings releases were read in full for exactly this
  reason (they're where a flagship manager discloses new deals in prose);
  Brookfield's yielded the NAVER/NVIDIA row, KKR's did not surface a new
  named AI/semiconductor/power/datacenter deal with a disclosed amount.
  `python -m engine.edgar sweep 2026-W47` independently returned
  `leads_new: 0` across its 14 tracked entities, consistent with this.

## allocator_class coverage
All four rows in verified_events.csv carry allocator_class: `vc` (Altimeter),
`alt_manager` (Brookfield), `corporate` (SK hynix) — set on every row, as
required for this agent.

## Watch next week
- Altimeter Premier Growth IX: date-of-first-sale not yet occurred as of this
  filing — watch for an amendment once capital actually lands, and for any
  Form D on the separate early-stage/companion vehicle.
- d-Matrix / NVIDIA and Khosla / Wajo: still single-sourced; re-check EDGAR
  (Form D for d-Matrix if it stays private, or an NVIDIA 8-K/13D if the
  stake is large enough to trigger one) and for any Khosla Ventures SPV
  naming Wajo specifically.
- NVIDIA's own ~$1B Korea commitment: watch NVIDIA's own 8-K/10-Q filings for
  a primary confirmation of its slice of the NAVER AI-factory build.
- SK hynix/HYAICO: newly surfaced balance-sheet AI-infrastructure investor —
  worth a recurring EDGAR check given board seats obtained.
