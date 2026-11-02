# Corporate — Week 2026-W45 Summary

## What moved
First populated run for the corporate watchlist (Microsoft, Amazon, Alphabet, Meta,
Oracle, NVIDIA — all had 0 events on file). Of the six, **NVIDIA** was the only
genuinely active allocator this window; Amazon added one asset acquisition;
Microsoft, Alphabet and Oracle produced guidance, financing plans and old
(pre-window) stakes but no new confirmed capital deployment as allocator in the
last ~30 days.

## Biggest signals
1. **NVIDIA's $3B check into Meta's equity offering (Oct 26, 2026).** One day
   after Meta announced its ~$95-97.5B AI-financing plan, NVIDIA confirmed a $3B
   investment in the raise alongside an expanded Muse AI-agent partnership
   (Vera Rubin GPUs, Spectrum-X, BlueField-4). AMD took $1B of the same raise and
   Broadcom expressed non-binding interest — AMD is a new discovered allocator
   worth adding to the watchlist (see `discovered_allocators.csv`).
2. **NVIDIA's European minority-stake sweep (Oct 13-14, 2026).** Jensen Huang,
   on a Paris-then-London swing, announced planned minority stakes in 9 named
   startups — 4 French (Doctolib, Genesis AI, Pigment, Entalpic) and 5 British
   (Prima Mente, Boltz, Foresight, Hiverge, Riverlane) — plus a separate $250M/5yr
   UK AI-safety compute pledge. No per-company or aggregate cash amount was
   confirmed by NVIDIA; a CNBC-sourced $1.16B UK aggregate is directly disputed
   by TechFundingNews's reporting that no cheque size was disclosed at all. Filed
   all 9 as individual minority_stake rows with blank amounts and the dispute
   flagged in `notes`.
3. **Amazon's Hong Kong datacenter buy-out.** Amazon Data Services HK agreed to
   buy iTech Tower 3.1 (already partly leased to it) and 3.2 from debt-laden
   Grand Ming Group Holdings for a reported minimum ~US$277.9M — disclosed via
   the seller's own filing (counterparty disclosure), not an Amazon statement.
   Slightly outside the nominal 30-day window but included since Amazon had zero
   events on file.

## Candidate on the board
NVIDIA's reported (but unconfirmed) further ~$1B look at Figure AI (The
Information, Oct 7) — talks only, no signed deal found; filed as `candidate`.

## Environment note (affects coverage, not findings)
This sandbox's network policy blocked **all** direct fetches this run: both
`python -m engine.edgar` (SEC EDGAR via the agent proxy, 403) and `WebFetch`
(DNS-blocked for every external host tried, including sec.gov, nvidia.com,
meta.com, reuters.com, cnbc.com, businesswire.com). All research here was done
through `WebSearch` only, citing the resolved article URLs it surfaced. No
`engine.edgar exists` de-dupe check could be run either — context.json already
showed 0 events on file for all six names, so this run should not create
duplicates, but downstream ingest should still run its own dedupe pass.

## What to watch next week
- Confirm/close status of the Meta equity offering tranche NVIDIA/AMD are buying
  into (currently "pending customary closing conditions").
- Watch for an actual per-company amount on NVIDIA's 9 European stakes (EU/UK
  startup-funding trackers, Crunchbase/Dealroom, or a NVIDIA 10-Q footnote).
- Figure AI: watch for a Form D amendment or joint NVIDIA/Figure press release
  confirming (or killing) the reported $1B follow-on.
- Oracle's Oct 28 investor day capped future capital raises at $20B through
  FY30 (split equity/debt) — worth a dedicated financing-event row once a
  specific raise/instrument is announced, rather than the guidance itself.
- Re-run EDGAR checks once network/proxy access to sec.gov is restored.
