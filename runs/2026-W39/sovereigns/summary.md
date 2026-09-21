# Sovereigns — 2026-W39 summary

## Coverage
Watchlist: MGX, Mubadala, Saudi PIF, US Government. Window: disclosures roughly
2026-08-22 to 2026-09-21. `engine.edgar exists` checked before writing every
row (and re-checked against last week's own CSVs, since the exists index and
context.json both came back empty for all four entities this run despite
2026-W38 having filed real rows — see Environment note).

## What moved
- **US Government finalized four more CHIPS Act quantum-computing R&D awards**
  this window, all part of the same ~$2.0B, nine-company package that already
  gave us GlobalFoundries ($375M) and Rigetti ($100M) last week (not re-filed):
  **D-Wave Quantum ($100M, 2026-09-08)**, **Quantinuum ($100M, 2026-09-08)**,
  and **PsiQuantum ($100M, 2026-09-08)** each converted their May-2026 LOIs
  into definitive agreements, and **Anderon — a newly formed IBM subsidiary
  building a 300mm quantum wafer foundry in Albany, NY — got the largest slice,
  $1B (2026-09-16), matched by an equal ~$1B from IBM itself** (only the
  government's $1B is recorded as this allocator's row). D-Wave's own 8-K
  exhibit on EDGAR gave a genuine resolved SEC citation; the rest are sourced
  to NIST's own finalization pages plus each company's IR release. All four
  filed `verified` (Tier 1). Two LOIs in the same package — Infleqtion and
  Diraq ($38M) — have not yet converted to definitive awards and were not filed.
- **Mubadala is the reported frontrunner to take a minority stake in Ansaldo
  Energia** (Italian gas/steam turbine and generator OEM, majority-owned by
  Italy's state investment arm CDP Equity), per Corriere della Sera/Bloomberg,
  2026-09-20. No deal size, stake percentage, or signing yet — filed
  `candidate`, single-origin sourcing, amount left blank rather than guessed.
  Power-energy sector (turbines/grid gear), not itself an AI-specific deal but
  in-scope per the sector taxonomy.
- **MGX**: no new disclosures found in the window beyond the already-known
  $49B Fund I (closed July) and its OpenAI/Anthropic/xAI follow-ons — searched
  forward through 2026-09-21, nothing new to file.
- **Two known candidates re-checked, not re-filed (no material change):**
  Saudi PIF/HUMAIN's $2.5B data-center fund raise (still fundraising, CMA
  approval pending, same $1.2B National Infrastructure Fund commitment as
  last week) and Mubadala's Akita, Japan ~$6.3B data-center talks (still "in
  talks," no term sheet). Re-filing either as a fresh row would double-count
  a claim already on file from 2026-W38.

## Filtered out (not filed)
- A DoD CDAO "up to $200M each" AI contract to Anthropic/Google/OpenAI/xAI
  surfaced heavily in this week's search results (The Intercept published
  documents 2026-09-08), but the underlying Prototype Other Transaction
  Agreements were actually awarded in **July 2025** — an old commitment
  resurfacing via new document disclosure, not new capital moving this week.
  Not filed (classic "old round resurfacing" trap from the escalation loop).
- Mubadala's Luckin Coffee minority stake and Masdar City Square / Aldar real
  estate deals are real but don't map to any canonical AI-buildout sector —
  left out per the same rule applied last week.
- PIF's Gulf Coast Development Company (Al-Khafji coastal destination,
  launched 2026-09-07) is real estate, not AI capital — not filed.

## Watch next week
- Whether the Ansaldo Energia talks produce a signed term sheet with a
  disclosed stake/price.
- Infleqtion and Diraq (the two remaining LOIs in the $2.0B CHIPS quantum
  package) converting to definitive awards.
- HUMAIN's $2.5B fund raise reaching CMA approval or a first close.

## Environment note
WebFetch was network-egress-blocked for essentially every external domain
tried this run (nist.gov, sec.gov, bloomberg.com, dwavequantum.com,
newsroom.ibm.com, caproasia.com — all rejected at the proxy), same as
2026-W38. All sourcing above relies on WebSearch's returned resolved article
and press-release URLs (never a search-query URL) and its extracted content,
cross-checked across the government source (NIST), each company's own IR/
newsroom release, and independent trade press (Quantum Computing Report,
HPCwire, The Quantum Insider) before grading `verified`.

Separately, `engine.edgar exists` and this week's `context.json` both report
zero events on file and `last_event_date: null` for all four watchlist
entities, even though 2026-W38 filed three `verified` US Government rows
(Duane Arnold, GlobalFoundries, Rigetti) and two `candidate` rows (HUMAIN,
Akita). Cross-checked by re-reading `runs/2026-W38/sovereigns/*.csv`
directly — those rows exist on disk but the exists-index/context builder
hasn't ingested them as of this run. Treated 2026-W38's rows as known
(not re-filed) based on that direct read, not the (apparently stale) tool
state — worth a look on the ingest side.
