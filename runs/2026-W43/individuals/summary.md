# Individuals — 2026-W43 summary

## Bottom line
Zero `verified` or `verified_alpha` *new* personal-capital events this run. Three
weak `candidate` rows filed (Elad Gil → Applied Compute, Elad Gil → Cognition,
Jeff Bezos/Bezos Expeditions → Generalist AI), none of them previously on file.
This is the hardest class by design, and this week it ran into real tooling
limits on top of the usual lag — see Environment notes below before reading
too much into the thin count.

## What moved (or didn't)
- Swept the ~45-day window (since ~2026-09-04) across the ~40-name watchlist
  plus the PayPal Mafia / Thiel-extended / Thiel Fellowship network rosters.
  No freshly-dated (Sept–Oct 2026), adequately-sourced personal check turned
  up for Thiel, Andreessen, Khosla, Hoffman, Rabois, Lonsdale, Gross, Friedman,
  Sacks, Wang, Luckey, Asparouhov, Schmidt, Bezos, Son, or the Collison
  brothers in this specific window.
- Backfill found three not-yet-filed leads from spring 2026 (outside the
  45-day window but confirmed via `engine.edgar exists` to be absent from the
  database): Elad Gil's reported first AI-sector angel check (Applied Compute,
  ~Apr 8), a reported Gil personal stake in Cognition (~May), and a Bezos
  Expeditions slice of Generalist AI's $400M Series B (~June, the one member
  of that month's 5-deal Bezos cluster not already on file). All filed
  `candidate` — single/aggregator-sourced, no press release, no amounts.
- **Erebor Bank** ($1.5B raise talks at $8B valuation) is the closest thing to
  a live Thiel/Lonsdale/Luckey story this week, but the capital is Founders
  Fund's (VC-agent territory) and the round hadn't closed as of the latest
  (Aug 2026) reporting found — no capital moved, so it's not an event, and
  Lonsdale/Luckey's "financial backing" is described in terms too vague to
  attribute as a sourced personal check. Worth a follow-up check once/if it
  closes.
- A stray reference surfaced to Daniel Gross, Nat Friedman, Patrick Collison
  and John Collison as "anchor investors" in some new, unnamed investment
  firm. Could not run it down (no firm name, no amount, no date) before the
  search budget ran out — flagging as a lead, not filing it.
- Network coinvestment: none observed this week (no 2+ tracked-network member
  deal found).

## Data-quality finding for the pipeline
`runs/2026-W43/individuals/context.json` lists every tracked individual with
`last_event_date: null` / `events_on_file: 0`. That's stale: `engine.edgar
exists` shows Jeff Bezos and Elad Gil already carry several events on file
from **run_week 2026-W32** (Prometheus, CuspAI, Flourish, General Intuition,
Odyssey). The context pack's "what_you_already_have" section needs to be
regenerated for this agent — as given, it would have caused this run to
re-file deals already in the database had they not been individually checked
with `exists` first.

## Environment constraints hit this run
- **WebFetch was non-functional all session** (`getaddrinfo ENOTFOUND` on
  every domain tried: techcrunch.com, geekwire.com, f4.fund, buttondown.com).
  Could not deep-read any article beyond the WebSearch tool's own snippets,
  which blocked verifying several thinner leads (e.g. raisetrack's angel
  registry digests for 2026-09-09/10/11, which looked promising).
- Direct SEC/EDGAR access via Bash curl was proxy-denied (403 on
  `data.sec.gov`). `engine.edgar filings`/`cik` ran fine but returned "no
  CIK on file" for every personal vehicle checked (Thiel Capital, Mithril
  Capital, Gigafund, NFDG, SciFi VC, Bezos Expeditions, Backend Capital,
  Craft Ventures) — consistent with the brief's expectation that individuals
  rarely surface as named SEC filers, but it means zero Tier-1 confirms were
  reachable this run regardless of lead quality.

## Watch next week
- Erebor Bank's $1.5B raise, if it closes — check whether Thiel/Lonsdale/
  Luckey show up as personal backers vs. Founders Fund only.
- The Gross/Friedman/Collison "anchor investor" firm rumor — needs a firm
  name to chase.
- Re-run the raisetrack angel-registry digests (buttondown.com) once WebFetch
  is working — they looked like genuine Sept 2026 angel-list signal that
  this run couldn't read.
- No new allocators discovered with enough confidence to file
  `discovered_allocators.csv` this week.
