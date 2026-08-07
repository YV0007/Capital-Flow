# VC Allocators — ISO Week 2026-W32
_Disclosures ~2026-07-07 to 2026-08-07. 26 verified rows / 5 candidate rows across 7 watchlist firms._

## What moved

Watchlist VC capital this window went overwhelmingly into the **physical layer**:
inference silicon, nuclear and grid power, automated defense manufacturing, and
robotics. Every one of the seven watchlist firms produced at least one
in-window, attributable deployment — the first clean sweep in recent runs, and it
happened because two enormous rounds (Base Power, Hadrian) each pulled in three or
four watchlist names at once.

The application layer was busy too, but in a different register: a16z, Khosla and
Sequoia were repeatedly buying the **AI-agent security and control plane**
(Neo Security, Glow, Cathedral) rather than agents themselves.

## Biggest signals

1. **Base Power $1B Series D at $13B — four watchlist VCs in one round.**
   Coatue and Altimeter came in new; Thrive Capital and a16z re-upped. Confirmed
   by the company's own PR. Distributed home batteries aggregated into grid
   capacity is now being underwritten as AI-adjacent energy infrastructure by the
   same crossover funds that own the compute names. This single round supplies
   four of the distinct-allocator counts a theme_swarm on `energy_for_ai` needs.

2. **Hadrian $1.37B Series D at $7.87B — three watchlist VCs.** a16z, Founders
   Fund and Altimeter all participated in AI/robotics-automated precision
   manufacturing for aerospace and defense. Together with Cathedral ($160M,
   a16z + Sequoia co-lead) and Singularity Defense ($80M, Khosla co-lead), that
   is **five distinct watchlist firms into `defense_ai` inside 23 days** — the
   strongest theme convergence in this run.

3. **Sequoia went long the physical stack twice at the top end.** Valar Atomics
   ($1B Series B, ~$6B valuation, factory-built microreactors aimed at datacenter
   load, Shaun Maguire on the board) and Etched ($300M Series C at $10.3B, which
   the company's PR calls the highest valuation ever for a Sequoia-led Series C,
   with a16z alongside). Nuclear power and inference ASICs, both Tier-1 confirmed.

4. **Altimeter re-rated from watch to something closer to key.** It appears three
   times this window (Base Power, Hadrian, Thrive Holdings) after producing
   nothing attributable in prior runs. Worth reviewing its `tier: watch` setting
   in config/allocators.yaml.

## Confidence & limitations

- **26 verified rows: 23 `verified` on Tier-1 primaries** (company PRs, IR/newsroom
  pages, official announcement posts) **and 3 `verified_alpha`** (Cathedral x2,
  Glow x1 — see the Cathedral caveat below). **5 `candidate` rows.**
- `amount_usd` carries the **FULL round** on every allocator row because no round
  in this window disclosed a per-investor slice; `round_total_usd` repeats it and
  every note says so explicitly. Do not sum `amount_usd` across rows of the same
  deal without deduping on target.
- **Escalation-loop outcomes** (weak leads worked rather than dropped):
  - *Cathedral* — all press traces to one Reuters exclusive; not listed on a16z's
    or Sequoia's portfolio pages (company is in stealth). Held at `verified_alpha`
    only because Crunchbase's deal database records it independently. On press
    alone it would be a candidate.
  - *Databricks/Coatue* — Databricks' own newsroom PR is Tier 1 but confirms a
    **signed term sheet, not a close** ("expected to close later this summer").
    Kept at `candidate` despite the Tier-1 source, because no capital has moved.
  - *Thrive Holdings/Altimeter* — PYMNTS and every other outlet cite The
    Information. One origin, so `candidate`, not `verified_alpha`.
  - *Khosla $5.5B fund* — Bloomberg reports "in talks"; no Form D or firm
    announcement found. Target, not a close. `candidate`.
  - *Founders Fund / P-1 AI* — one trade roundup names Founders Fund; the
    company's GlobeNewswire PR names only NEA as lead and does not enumerate
    participants. Uncorroborated, not contradicted. `candidate`.
- **A prior-run/trade-press error was caught and rejected:** a July 30 techstartups
  roundup credited the Ellis seed to "Initialized Capital, Sequoia Capital". The
  company's Businesswire PR names **First Round Capital** as lead with **Khosla
  Ventures** participating and no Sequoia. No Sequoia/Ellis row was filed.
- **Thrive Capital row deliberately withheld on Ellis:** the PR names *Josh Kushner
  personally*, not the firm. That belongs to the individuals agent.
- **Off-taxonomy mappings flagged in-row:** Chai Discovery (bio → `ai-applications`
  / `biotech_ai`), Ambrook (real-economy fintech), Norm Ai and State Affairs
  (legal/policy AI), Databricks (`ai-data`). These are real watchlist deployments
  but are not AI-buildout infrastructure.
- **Explicitly checked and excluded as out-of-window or not-a-VC-event:** SSI $5B
  (Nvidia-only, corporate agent's row), Anthropic $25B (January 2026), Baseten
  $1.5B Series F (Altimeter lead, disclosed late June), Founders Fund ~$6B fund
  (March–May 2026), a16z ~$15B (January 2026), Sequoia $7B (April 2026), Thrive
  $10B fund (February 2026).

## Watch next week

- **Does Databricks close?** A close upgrades Coatue's $3B `candidate` to a
  verified event and would be the largest single VC-led slice in the DB.
- **Khosla's $5.5B fund family** — watch for a Form D or firm announcement to
  convert the `fund_launch` candidate.
- **Founders Fund on P-1 AI** — a portfolio-page listing or Form D resolves it.
- **Whether the `defense_ai` cluster keeps compounding.** Five watchlist firms in
  23 days is already swarm-level; a sixth name into defense manufacturing or
  military cyber would make this the dominant theme of the quarter.
- **Etched's rumored parallel raise at a materially higher valuation** — confirm
  whether Sequoia or a16z take their pro rata.
