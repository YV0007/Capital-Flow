# Corporate — 2026-W40

## What moved
Three follow-on checks from tracked strategics' venture arms, all confirmed via the
target company's own press release and corroborated by independent Tier-3 press —
no new lead reached even `candidate` status beyond these.

1. **NVIDIA -> Nscale** (neocloud, follow_on, $1.0B, verified). NVIDIA committed $1B
   (convertible into non-voting shares at IPO) inside Nscale's $3.36B pre-IPO
   convertible-note raise led by Third Point, signed 2026-09-15 and disclosed via
   Nscale's own PR + its 2026-09-18 S-1 ahead of a planned NYSE listing. This is a
   follow-on — NVIDIA already held Nscale Series B warrants and Series C-4 preferred
   from before this window. Biggest single number of the week for this class.
2. **Alphabet (GV) -> Snorkel AI** (ai-data, follow_on, undisclosed amount, verified).
   GV returned in Snorkel AI's $350M Series E (Insight Partners/S32 co-lead) at a
   $3.5B valuation, announced 2026-09-22.
3. **Microsoft (M12) -> HiddenLayer** (cybersecurity, follow_on, undisclosed amount,
   verified). M12 — which co-led HiddenLayer's 2023 Series A — returned as a
   strategic participant in its $100M Series B (Delta-v Capital-led), 2026-09-02.

Amazon, Meta and Oracle: no new capital-allocation event found in the last 30 days.
Meta's only recent capital event (Stilla.ai acquisition, 2026-09-09) is already on
file. Oracle's September news (the $18B raise, the OpenAI $300B compute contract,
the Project Jupiter force-majeure notice) is Oracle raising/spending its own
capital, not Oracle deploying capital into a third party as an allocator — so it
stays at zero events for this class, consistent with prior weeks. Checked and
explicitly ruled out: Microsoft did NOT participate in Mistral's 2026-09-08 Series D
(CEO Arthur Mensch confirmed on the record that Microsoft's stake is not increasing
via that round) — logged as a negative check, not filed.

## Discovered allocator
**Abu Dhabi Investment Council** (sovereign) — an independently-run Mubadala
vehicle, co-invested alongside NVIDIA (and Third Point/Apollo/Citadel/Hudson Bay)
in the Nscale round. Only parent Mubadala sits on the sovereigns watchlist; flagged
ADIC separately per the vehicle-vs-parent convention (same logic as M12/GV/NVentures).

## Environment note
The EDGAR deterministic path (`engine.edgar filings`/`cik`) and WebFetch were both
egress-blocked in this sandbox for the entire run (`data.sec.gov`, `sec.gov`,
`techcrunch.com`, etc. all returned `EGRESS_BLOCKED` from the proxy). The local,
network-free `engine.edgar exists` check worked normally and was used before every
row. All sourcing this week was done via WebSearch, cross-checking each claim
against 2-4 independent outlets (plus the target company's own newsroom/PR page,
counted as the Tier-1 confirm) rather than fetching primary documents directly —
flagging this so a future run with EDGAR/WebFetch access re-verifies the Nscale S-1
citation directly against the filing.

## Watch next week
- Nscale's $1B NVIDIA tranche is due to fund "mid-November 2026" — re-confirm once
  cash actually moves, and watch for the NYSE IPO pricing (filed at up to $35B).
- Stale candidates carried forward untouched (no new Tier-1 confirm found this run):
  NVIDIA/OpenAI Ohio 10GW, NVIDIA/Lancium, NVIDIA/Perplexity, NVIDIA/Hugging Face
  acquisition (note: Hugging Face itself has since closed and is now `verified` on
  file from a prior run — only the older CNBC-sourced candidate row is stale),
  NVIDIA/Thinking Machines Lab (x2), Alphabet/MediaTek exact slice.
