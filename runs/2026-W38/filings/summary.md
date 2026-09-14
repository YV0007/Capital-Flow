# Filings agent — 2026-W38

## Network constraint (confirmed, again)
Same as the five class agents this week: WebFetch is egress-blocked for every
external domain in this sandbox, and `python -m engine.edgar filings <name>
--forms ... --since ...` fails the same way (it needs `data.sec.gov` over the
network, which 403s). Only WebSearch (Anthropic-hosted) and the local,
config-only `engine.edgar cik` / `engine.edgar exists` subcommands worked.
Every citation below is a URL WebSearch actually resolved and returned in its
results — not a fetched/read page, and never a bare search-query URL.

## Job 1 — Confirm: 0 candidates upgraded to verified
Ran the escalation loop (multiple query reformulations: company name + "Form
D", + "SEC filing", + "Notice of Exempt Offering of Securities", site:sec.gov,
etc.) against every candidate and verified_alpha row from the other five
agents:

- NVIDIA → Thinking Machines Lab ($2.5B, corporate candidate) — still "in
  talks" per every outlet as of today; no 8-K, no Form D indexed.
- Apollo/BlackRock/Blackstone/Brookfield/Goldman Sachs/KKR → NVIDIA AI Compute
  Infrastructure Financing Platform MOUs (alt-managers candidates) — checked
  NVIDIA's own press release plus each institution's recent 8-Ks; this is
  explicitly framework-MOU-only, no dollar commitment disclosed by any party,
  nothing to file.
- Blackstone/Apollo → Broadcom debt/Anthropic compute financing
  (alt-managers candidates) — still reported as "in talks" (CNBC), no
  definitive-agreement 8-K found.
- Saudi PIF → Humain Data Center Fund; Mubadala → Akita AI Data Center
  (sovereigns candidates) — both foreign, pre-signing/"weighing" stage; the
  only sec.gov hit for "Humain" was an unrelated US entity ("Humain Ventures
  GP I, LLC", a 2024 filing) — flagged as a likely name collision and NOT used
  (CONTEXT.md mistake #4).
- a16z → Gimlet Labs / Lightfield / Cognition; Coatue, Founders Fund, Altimeter
  → Lightfield/Cognition; Sequoia → AIR (vc verified_alpha rows); Elad Gil →
  NavigateAI (individuals verified_alpha row) — all six rounds closed within
  the last ~2 weeks, inside Form D's 15-day filing window. No Form D for any
  of them is indexed yet under the company's public name (tried the "AI"
  brand name and, where discoverable, the likely legal entity name — e.g.
  "Cognition Labs"). Left as-is at their originating agents' grades; nothing
  to re-emit.

Every attempt (URL, tier, yielded=0/1) is logged in `source_log.csv`.

## Job 2 — Discover: 2 new filings-sourced events, 1 new allocator
**Empery Digital, Inc.** (NASDAQ: EMPD) — a bitcoin-treasury company now
running a second, parallel strategy of minority stakes in AI-data-center
projects — was on no class agent's watchlist. Found via a generic "8-K
material definitive agreement AI data center" sweep, then confirmed against
its own SEC exhibits:

1. **$20M preferred-equity stake (~8%) in Cardinal Data Power, Inc.**
   (2026-07-20, disclosed 2026-07-23) — part of CDP's ~$70M Series A led by
   Hood River Capital Management, financing a 750MW+ West-Texas data-center
   campus. Source: `sec.gov/Archives/edgar/data/1829794/000168316826005723/empery_ex9901.htm`.
2. **$65M for a 25% interest in a Hunt-Properties JV** acquiring a Midwest
   industrial site to convert into a ~150–300MW AI data center (2026-06-30).
   Source: `sec.gov/Archives/edgar/data/1829794/000168316826005178/empery_ex9901.htm`.

Both are outside the ~30-day discovery window in wall-clock terms (June/July
vs. a 2026-09-14 run date), but since Empery Digital has zero prior coverage
under any class agent, they're filed as baseline coverage for a newly found
allocator — the same precedent the alt-managers agent used for KKR's fund
close this run. Added Empery Digital, Hunt Properties, and Hood River Capital
Management to `discovered_allocators.csv`.

## Worth watching next week
- **SoftBank's $11.87B loan tied to its OpenAI position** (Bloomberg/Japan
  Times, 2026-09-14 — today) is a live, fast-moving story (SoftBank has also
  layered a $10B OpenAI-share-backed margin loan and is prepaying $25.9B of a
  bridge loan this week) but everything so far is bank-syndicate press, not a
  filing — SoftBank isn't an SEC filer for this. Belongs to the alt-managers
  or sovereigns lane if a primary (TDnet/IR) disclosure surfaces; not filed
  here per the "everything I output is Tier-1" rule in `filings.md`.
- **Thinking Machines Lab** and the **Broadcom/Anthropic debt package** are
  the two biggest amounts still sitting at "in talks" — both are the kind of
  deal that could drop a signed 8-K/definitive-agreement PR with no warning;
  worth a same-day filings check whenever the corporate/alt-manager agents
  next touch either name.
- Empery Digital said explicitly it's looking to "execute similar agreements"
  — worth a quick sweep of its 8-Ks again next run.
