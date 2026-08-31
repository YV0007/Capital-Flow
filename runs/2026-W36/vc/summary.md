# VC agent — 2026-W36 summary

## Coverage
Swept all seven watchlist names (Sequoia, Andreessen Horowitz, Thrive Capital, Founders
Fund, Khosla Ventures, Coatue, Altimeter) forward from their `last_event_date` in
context.json, plus a ~30-day back-sweep. Six of seven had no new capital-allocation
event beyond what's already on file — their August activity (Valar Atomics, Etched,
Firmus, Form Energy, Databricks, Veeda AI, Thrive Holdings/Amazon) all checked `exists:
true` against the local ledger before I looked twice. One new event filed, one weak
lead filed as candidate, four new co-investor names surfaced for the watchlist.

**Environment note:** `data.sec.gov`/`www.sec.gov` are blocked by this session's egress
policy (`engine.edgar filings`/`sweep` both fail with 403 on the CONNECT tunnel — the
`cik`/`exists` subcommands still work since they hit local/cached data, not the network).
WebFetch is also blocked for every external domain tried (a16z.com, sec.gov,
bloomberg.com, techcrunch.com, crunchbase.com, convergedigest.com). All research this
run relied on WebSearch, whose returned snippets are drawn from the live pages — I cite
the resolved article/page URL each search surfaced, never a query URL, but could not
independently re-fetch primary documents to double-check formatting/exact wording
beyond what the search summaries quoted. Flagging this so a future run with working
EDGAR/WebFetch access re-verifies the Tier-1 citation below directly.

## Biggest signal: a16z's Machine Age Fund ($1.1B, fund_launch)
Andreessen Horowitz launched a new $1.1 billion fund on 2026-08-28 — its first vehicle
dedicated purely to AI physical infrastructure: chips, memory, networking, systems
software, power, data centers, and robotics. Five partners are on the announcement
(Ben Horowitz, Martin Casado, Raghu Raghuram, David Ulevitch, David George), and it's
explicitly framed as attacking the "wall" AI is hitting on the hardware side — compute
clusters outrunning the memory/interconnect/power/cooling beneath them. This is the
clearest evidence yet of a top-tier generalist VC formally institutionalizing a
dedicated sleeve for the AI-buildout thesis this dashboard tracks, rather than making
one-off infra bets out of a general fund. Filed `verified` / tier 1, citing a16z's own
fund page, corroborated independently by TechCrunch, Dealroom, and TheNextWeb.

## Other notable context (already on file, not re-filed)
- **Sequoia**'s $10B "AI + reindustrialization" reallocation (led by Valar Atomics'
  $1B nuclear round and the Etched follow-on) continues to be the dominant Sequoia
  story this month — both events were already captured in prior runs.
- **Coatue** stayed the most active name on the sheet: Firmus ($2B), Form Energy
  ($750M), and lead on Databricks' record $5B/$190B round — all pre-existing.
- **Altimeter/Thrive Holdings** ($2B, minority_stake) — the context pack listed this
  as a stale candidate needing a Tier-1 confirm, but it was already upgraded to
  `verified` in run W34 using Thrive Holdings' own fundraise page
  (thriveholdings.com/thrive-holdings-fundraise) as the Tier-1 source. No further
  action needed; flagging that the context pack's `stale_candidates` entry is itself
  stale and should drop off next week's pack.

## Rejected / not filed
- **Founders Fund / P-1 AI** (a standing stale candidate): searched specifically for
  Founders Fund's involvement in P-1 AI's rounds. Every source found (seed: Radical
  Ventures/Village Global/Schematic/Lerer Hippeau; Series A: NEA) names other leads —
  none mention Founders Fund. This candidate looks unconfirmable and possibly a
  misattribution; recommend downgrading/dropping unless a source naming Founders Fund
  specifically turns up.
- **Founders Fund / Khartis Therapeutics** ($50M Series B, Aug 13): real round, real
  Founders Fund seed history, but the target is small-molecule biotech — doesn't map
  to any canonical sector in this pipeline's AI-buildout taxonomy, so left unfiled
  rather than forcing a sector tag.
- **Sequoia / Mach Industries** and **Khosla Ventures / Mach Industries** (defense-tech,
  $300M Series C): both are longstanding backers per press, but the round itself
  closed ~June 2026, predating both allocators' `last_event_date` — old news, not a
  new event this window.
- **Khosla Ventures / Rhoda AI** ($450M Series A, robotics): same issue — round is
  dated March 2026, well outside the forward-search window.
- **Khosla Ventures' new fund family** (targeting up to $5.5B) remains "in talks" per
  Bloomberg as of this run — no close confirmed, stays a candidate un-refiled.
- **Sequoia / "Preview"** ($10M seed, AI coding tool, Aug 13): only a single Dealroom
  listing surfaces this, no corroborating press, and the company name is too generic
  to disambiguate confidently. Filed as `candidate` (tier 2) per the name-collision
  caution in CONTEXT.md rather than dropped silently.

## New allocators discovered (see discovered_allocators.csv)
Four untracked names turned up co-investing directly alongside watchlist VCs/alt
managers in August's biggest AI-infra rounds: **D1 Capital Partners** (with Altimeter,
Thrive Holdings), **Sixth Street Growth** and **T. Rowe Price** (with Coatue,
Databricks), and **Jane Street** (with Coatue, Firmus). All four are recurring enough
in AI-buildout crossover rounds to be worth adding to the watchlist.

## Watch next week
- Whether a16z's Machine Age Fund makes its first portfolio company announcement.
- Whether Khosla Ventures' reported $5.5B fund family actually closes.
- Whether the Founders Fund/P-1 AI attribution gets corrected or confirmed anywhere.
