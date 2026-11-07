# Corporate — 2026-W44

## Tooling note
`python -m engine.edgar` is blocked in this sandbox this week: outbound calls to
`data.sec.gov` are rejected at the egress proxy (403 on CONNECT), and `WebFetch`
cannot resolve DNS for any host (including sec.gov, nvidia.com, reuters.com). All
research this week ran through `WebSearch` only, citing the resolved article/press-
release URLs it returned. No deterministic EDGAR pull or direct document fetch was
possible — flag this for whoever owns the sandbox network policy.

## What moved
NVIDIA was the only one of the six watchlist names with confirmed, dated capital
moves in the last ~30 days; Microsoft, Amazon (ex. one deal below), Alphabet, Meta
and Oracle news this window was either old (Aug 2026 or earlier, outside the
lookback), pure talk/rumor with no capital committed, or about *raising* capital
for their own buildout rather than *deploying* it as an allocator.

**1. NVIDIA's European AI push (Oct 13-14, Paris).** Jensen Huang announced ~$2B in
new European AI commitments, including confirmed minority stakes in four French
companies — Doctolib (healthcare-admin SaaS), Genesis AI (robot foundation models),
Pigment (FP&A software) and Entalpic (AI for materials/chemistry). Doctolib and
Genesis AI confirmed the stakes directly to Reuters; Pigment and Entalpic come from
Les Echos reporting that the companies hadn't yet confirmed, so those two are graded
`verified_alpha`. None of the four disclosed amount or stake size — this is a volume
signal (NVIDIA broadening its balance-sheet bets into European application-layer AI,
not just compute/infra) more than a sizing signal. Same trip: a **$250M, 5-year
compute donation** (not cash) to UK AI-safety research (Oxford's BOLD, UCL's SOFAIR,
Imperial College London), confirmed independently by UCL's own newsroom.

**2. NVIDIA's $1B US-science commitment (Oct 8).** Five-year, non-dilutive pledge
to university research, US quantum-computing leadership, and government-mission
cloud providers, tied to the DOE's Genesis Mission. This and the UK compute grant
are both balance-sheet capital with no equity attached — filed as `grant`, mapped to
the closest canonical sector (`ai-applications` / `ai-for-science`) since no
"science-funding" sector slug exists in `config/rules.yaml`.

**3. Amazon's Hong Kong data-center acquisition (~Sept 29).** Amazon Data Services
Hong Kong Limited agreed to buy iTech Tower 3.1 and 3.2 in Fanling from two Grand
Ming Group Holdings subsidiaries, for a minimum HK$2.18bn (~US$277.9M), with a
contingent earn-out up to ~US$311.7M. Tower 3.1 is already built and leased to
Amazon; 3.2 is still under construction. Close expected Feb 2027. Graded
`verified_alpha` rather than `verified` because the original HKEX disclosure
couldn't be fetched directly this run (see tooling note) — only via
DataCenterDynamics' report of it.

## Dropped / filed as candidate, not fabricated
- **Isomorphic Labs** (Alphabet/DeepMind drug-discovery spinout): Bloomberg (Oct 8)
  reports early-stage talks to raise at a $40-50B valuation. No deal closed, no
  confirmed Alphabet participation in *this* round (vs. the earlier $600M and
  $2.1B rounds Alphabet/GV did back). Filed in `candidate_events.csv`, not dropped.
- Microsoft/Inception ($1B talks), Meta/Scale AI, Nvidia/Figure AI (2nd $1B,
  discussed Oct 7 but unconfirmed), Nvidia/Lancium ($3B, Aug 7 — outside the 30-day
  window) and Oracle/Ampere (SoftBank's acquisition of Ampere actually closed Nov
  2025, ending Oracle's stake — old news, not this week's event) were all checked
  and are either stale, pure rumor with no capital committed, or already resolved
  before this window. None were written up as events.

## Watch next week
- Whether NVIDIA's French stakes (Doctolib/Genesis AI/Pigment/Entalpic) get amounts
  disclosed, and whether the rest of the ~$2B European pledge (the French four were
  reported as a subset) names more targets.
- Isomorphic Labs: whether the $40-50B-valuation round actually closes and whether
  Alphabet/GV re-up.
- Re-run the EDGAR deterministic path once sandbox network access to data.sec.gov
  is restored — this run's 8-K/Form D sweep for all six names was done blind.

## Counts
verified_events.csv: 7 rows (5 `verified`, 2 `verified_alpha`)
candidate_events.csv: 1 row
discovered_allocators.csv: not written — no untracked co-investor surfaced
alongside a tracked allocator this week (NVIDIA appears to be the sole investor in
each deal per current reporting).
