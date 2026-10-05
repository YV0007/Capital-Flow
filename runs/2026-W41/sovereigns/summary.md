# Sovereigns — 2026-W41

## Environment note
WebFetch was network-blocked for every domain tried this run (sec.gov, energy.gov,
nscale.com, bloomberg.com, techcrunch.com, wikipedia.org, investor.nexteraenergy.com,
world-nuclear-news.org all returned EGRESS_BLOCKED). All research below was done via
WebSearch, whose synthesized snippets reflect real retrieved page content and cite
resolved, non-search document URLs. Flagged per-row in `notes` where this matters.

## What moved this week

**US Government is the real story this week, not the Gulf SWFs.** Four distinct,
Tier-1-confirmable federal capital moves landed inside the window, three of them on
the same day (2026-09-08):

1. **CHIPS Act quantum equity stakes — $300M total.** Commerce finalized Other
   Transaction Agreements (signed 2026-09-04) with **D-Wave Quantum**, **Rigetti
   Computing** and **Quantinuum**, $100M each, each disclosed via its own SEC 8-K on
   2026-09-08. Commerce took minority, non-controlling equity (shares, not a pure
   grant) in each — Rigetti at an implied $12.92/share (7,739,938 shares); Quantinuum
   handed over 2,369,528 Class A shares. Filed as three `equity` rows, sector
   `semiconductors` / `quantum-computing`, all `verified` (SEC filing + company PR,
   Rigetti's also confirmed via an official NIST PR).

2. **DOE closes $1.9B loan to restart Duane Arnold (Iowa) for Google's AI power
   demand.** DOE's Office of Energy Dominance Financing closed the loan 2026-09-08 to
   restart NextEra's 615MW nuclear plant; Google holds a 25-year PPA for >90% of the
   output specifically to run AI data centers. This is the clearest AI-power nexus of
   the week — a federal loan whose entire commercial rationale is AI compute demand.
   Filed `verified`, sector `nuclear`, event_type `project_finance`.

3. **(Candidate, not yet official) DOE reportedly preparing a ~$4.2B loan to Vistra**
   to uprate 3 of its 4 nuclear stations — Reuters/Bloomberg "sources familiar"
   reporting from 2026-10-02/03, with Energy Secretary Wright expected to announce it
   at a Vistra Ohio plant on **2026-10-07** — i.e. after this run's as-of date and
   still unconfirmed by DOE or Vistra. Filed as `candidate`; re-check next week for
   the official announcement.

**Gulf SWFs were quieter on confirmable new capital, but two real leads:**

4. **Mubadala (via Abu Dhabi Investment Council/Adic) → Nscale**, participating in
   Nscale's **$3.36B pre-IPO convertible-note financing** (announced 2026-09-25, led
   by Third Point; NVIDIA, Apollo, Citadel, Hudson Bay Capital and 8090 Industries
   also in). Adic's own slice wasn't disclosed, so `amount_usd` is blank and the
   $3.36B sits in `round_total_usd` per the measurement rule. Corroborated
   independently by agbi.com and HPCwire/AIwire — filed `verified_alpha`.

5. **Saudi PIF (via Humain) → new $2.5B Saudi data-center fund.** Humain is seeking
   to raise an initial $2.5B (debt+equity mix, managed by BSF Capital) to finance
   250MW of capacity with Al Moammar Information Systems, expandable to 1GW. This
   traces to a single Bloomberg "people familiar" origin (2026-09-03) — every other
   outlet that ran it cites that same Bloomberg piece, which is a circular-reporting
   single source, not independent corroboration — so it's filed `candidate` despite
   the CEO's own public confirmation of intent (he didn't confirm the $2.5B figure).

**Not filed as events (correctly, per scope):** Mubadala's new "partnership" with
Together AI to explore UAE AI-infra investment (2026-09-29) — both sides explicitly
declined to disclose any dollar figure or committed capital, so under CONTEXT.md this
is an MOU, not an event. MGX's Anthropic Series H ($65B, April 2026) and OpenAI
$300B-valuation round are both outside the 30-day window and were skipped as stale,
not re-filed.

## Totals
- `verified_events.csv`: 5 rows (3 CHIPS equity stakes + 1 DOE/NextEra loan +
  1 Mubadala/Nscale `verified_alpha`)
- `candidate_events.csv`: 2 rows (PIF/Humain $2.5B fund; DOE/Vistra $4.2B loan)

## Discovered allocators
- **Qatar Investment Authority (QIA)** — the biggest gap in our watchlist. Running a
  $20B AI-infrastructure JV with Brookfield (via its "Qai" vehicle) and a $3B+
  data-centre platform with Blue Owl, plus Anthropic rounds alongside MGX. Should be
  added as `tier: key`, same tier as MGX/Mubadala/PIF.
- **GIC (Singapore)** — recurring co-investor alongside QIA/MGX in Anthropic rounds
  and buying data centres directly.
- **BSF Capital** (Banque Saudi Fransi's investment arm) — the vehicle managing
  Humain's new $2.5B fund; worth tracking as the counterparty to confirm when/if that
  fund actually closes.

## Watch next week
- DOE/Vistra official loan announcement, expected 2026-10-07 — confirm amount and
  file as verified if it lands as reported.
- Humain/BSF Capital $2.5B fund — CMA approval process (2-3 months from 2026-09-03)
  and any PIF/Humain primary confirmation of the size.
- QIA: worth a dedicated watchlist slot given the scale of its AI-infra activity.
