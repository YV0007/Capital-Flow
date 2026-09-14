# Alt-Managers — Week 2026-W38 Summary

## Environment note (read first)
Both deterministic paths were unavailable this run: `python -m engine.edgar` failed
on every call (`data.sec.gov` / `www.sec.gov` CONNECT rejected with 403 by the
network egress policy), and `WebFetch` returned `EGRESS_BLOCKED` for every external
domain tried (Blackstone, Bloomberg, SEC, PR Newswire, Businesswire, CNBC, DCD,
Reuters, even en.wikipedia.org). All research below relies on `WebSearch`, which
still resolves and reads pages server-side and returns real article/press-release
URLs (never search-query URLs) with synthesized content. No `engine.edgar exists`
dedup checks were possible — moot this run since the context pack shows 0 events
on file for every watchlist entity. Flagging for the maintainer: this class's
Tier-1 SEC confirms are structurally blocked until `data.sec.gov`/`www.sec.gov`
egress is allowed for this agent.

## What moved
This is the first populated run for alt-managers (context pack showed 0 events,
null `last_event_date` for all 9 watchlist names), so coverage below spans
~early August through today (2026-09-14) rather than a strict trailing 30 days,
to seed a real baseline.

**4 verified, 0 verified_alpha, 8 candidate rows.**

- **KKR** closed **Global Infrastructure Investors V at $19.2B** (Aug 3) — its
  largest infra fund ever, already >$9B deployed across data-center, fiber and
  power platforms — then two weeks later took a **29% stake in SK Telecom's new
  AI-datacenter spinout SK Horizon** alongside a Korean IMM-Stonebridge
  consortium (combined $2.23B, Aug 27). KKR is clearly the most active name on
  this watchlist this cycle.
- **Blue Owl** led a **$2.4B GPU-collateralized debt package for IREN** (Aug 28)
  — $1.2B term loan + $1.2B secured notes at 9%, PIMCO co-investing — to fund
  Nvidia Blackwell Ultra purchases for a Canadian data-center campus. Same
  playbook as Blue Owl's earlier Meta Hyperion SPV, now extended to a
  smaller/riskier neocloud counterparty.
- **DigitalBridge** acquired **PLUS ES**, an Australian smart-metering platform
  carved out of Ausgrid (Aug 27, amount undisclosed) — grid-data infrastructure
  adjacent to, but not squarely inside, the core AI-buildout thesis; flagged in
  notes for a scope check.
- The big story that did **not** clear the bar for a verified/candidate capital
  event: NVIDIA's **Aug 10 MOUs with six of our nine watchlist names** (Apollo,
  BlackRock, Blackstone, Brookfield, Goldman Sachs, KKR) to build "compute
  financing platforms" targeting >$500B of third-party capital. Press explicitly
  confirms no dollar figure or first project has been disclosed by any partner —
  textbook MOU-with-no-money per CONTEXT.md. Filed all six as `candidate` rows
  (amount blank, not estimated) rather than dropped, since this is the single
  biggest structural signal for the whole alt-manager watchlist this quarter and
  is worth tracking to a definitive agreement.
- Also candidate-only: Broadcom's reported **$70-100B AI-chip debt package**
  (Blackstone + Apollo "in talks," CNBC Aug 21) as a follow-on to their June
  $35B Anthropic compute platform — real momentum, but still unconfirmed as a
  closed deal.

## Biggest findings
1. **KKR is the pace-setter this cycle** — a record $19.2B fund close plus a
   fresh $2.23B AI-datacenter stake in Korea inside the same month, both with
   Tier-1 sourcing.
2. **The NVIDIA $500B compute-financing framework is the structural story to
   watch** — it touches 6 of 9 watchlist names at once but is pure MOU; the
   moment any partner discloses a dollar figure or names a first project, that
   graduates from candidate to a real fund_launch/project_finance event and
   should be chased hard next week.
3. **Blue Owl keeps extending its GPU-collateral debt playbook down-market**
   (Meta Hyperion → IREN), with PIMCO as a recurring anchor investor across
   deals — worth watching PIMCO as its own allocator (see discovered_allocators.csv).

## What to watch next week
- Definitive-agreement follow-through on the NVIDIA six-way MOU (any disclosed
  dollar commitment or named first project graduates it out of candidate).
- Whether the Broadcom $70-100B debt package (Blackstone/Apollo) actually
  closes, and at what tranche sizes.
- SoftBank's **third $10B OpenAI tranche**, due Oct 1 2026 per its disclosed
  schedule (tranches 1 and 2 already executed Apr 1 and reportedly Jul 1 2026,
  both outside this run's window) — first real SoftBank capital-allocation
  event to expect once it lands.
- DigitalBridge/SoftBank's own $4B take-private, approved by DBRG holders in
  April, still hasn't closed as of Sep 14 (regulatory approvals pending) —
  chase the closing announcement.
- Apollo and Goldman Sachs had no allocator-specific committed-capital event
  this cycle beyond the NVIDIA MOU candidate row; worth a deeper sweep next run
  (both are very active in AI-infra financing generally per their own IR
  commentary, so this is likely a coverage gap rather than true inactivity).

## Allocators flagged for discovery
See `discovered_allocators.csv`: **PIMCO** (recurring anchor investor across
Blue Owl / BlackRock AI-infra debt SPVs) and the **IMM Investment-Stonebridge
consortium** (South Korean co-investor alongside KKR on SK Horizon).
