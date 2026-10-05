# VC agent — 2026-W41 summary

## Coverage
14 verified rows (12 `verified`, 2 `verified_alpha`), 0 candidates, across 7 distinct
targets and all 7 watchlist names except Thrive Capital's sister events were folded
into one target (Fortell) alongside Founders Fund. Every row has a resolved,
fetched/read source URL (never a search-query link) and passed
`engine.edgar exists` checks clean (no duplicates on file — the class had zero
events on record going into this run per context.json).

## Biggest signals
1. **AI-application layer is the swarm, not infra.** All six underlying deals this
   week (Cognition, Factory, Harvey, Profound, EliseAI, Fortell) sit in
   `ai-applications` (coding agents, legal AI, marketing AI, housing/health ops AI,
   AI hearing aids) — none in the hardware/datacenter stack. Three of these rounds
   (Cognition, Factory, Harvey) each pulled in 2-3 watchlist names simultaneously
   (Cognition: a16z lead + Founders Fund + Altimeter participants; Factory: Khosla +
   Sequoia co-leads; Harvey: Sequoia + a16z + Coatue all returning as participants
   in a round led by two new entrants). That's a real `sector_swarm`/`subsector_swarm`
   pattern on enterprise-AI-agents and legal/vertical AI, not a single outlier deal.
2. **Valuation re-rates are extreme and fast.** Cognition: $26B (May) -> $48B (Sep),
   in ~4 months. Factory: $1.5B (Apr) -> $5B (Sep), in ~5 months. Harvey: $11B (Mar)
   -> $15.5B (Sep). This is the AI-application layer re-pricing on revenue growth
   (Cognition's ARR: $492M -> ~$900M in the same window) rather than new-logo hype —
   worth flagging for anyone reading `amount_usd` vs `valuation_usd` on these rows.
3. **Kleiner Perkins is the most conspicuous gap in the current watchlist.** It
   co-led or participated alongside three different watchlist VCs (Sequoia, a16z,
   Founders Fund, Coatue) across three separate rounds this single week — see
   `discovered_allocators.csv`.

## What I couldn't do, and why
This session's network egress is blocked for all direct HTTP(S) fetches except the
WebSearch tool's own backend — confirmed by testing `WebFetch` against seven
unrelated domains (globenewswire, finsmes, dealroom, benzinga, techfundingnews,
techcrunch, wikipedia, sec.gov) and the `engine.edgar filings`/raw `requests` path
against `data.sec.gov` / `www.sec.gov` directly: all returned
`EGRESS_BLOCKED` / `403 Forbidden` from the local proxy. `engine.edgar cik` still
works because it resolves against the local `entity_external_ids` table, not a
live network call — it correctly returned `null` for all four private targets
(Harvey, Cognition, Factory, EliseAI; none file with the SEC as private companies
without public debt/equity).
Given that, every row's `source_url` is an article I located and had fully read
back to me (verbatim quotes, figures, named investors) via WebSearch's own
fetch-and-summarize step — not an additional independent WebFetch pass by me. Where
possible I cited the company's own blog/newsroom post or official PR-wire release
(Cognition, Factory, Harvey, Profound, EliseAI, Mazama Energy all have one) and
graded `verified`; where no such primary existed (Fortell) I required 2+
independent outlets plus a TechCrunch podcast featuring the investors themselves
before grading `verified_alpha`, consistent with the status rubric.

## Rejected / discarded leads (recurring-mistakes guard)
- Several aggregator pages (`blog.mean.ceo`, one `tracxn` listing) returned
  fabricated-looking per-deal amounts (e.g. a "$4.931B Series F" and a "$6.556B debt
  round" on the same day, a "$7.563B Series C" for a startup) that don't survive a
  sanity check against the stage/company. Discarded outright rather than filed —
  logged in `source_log.csv` with `yielded=0`.
- a16z's $15B (Jan), $2.2B crypto fund (May), and reported $20B AI-fund target are
  all either outside the 30-day window or not yet closed (a target, not a committed
  vehicle) — left out per SCOPE (committed/deployed capital only).
- Thrive Capital / Collaborative Fund's move into pro-sports ownership (Giants,
  Lakers via Thrive Eternal) predates this window and is analysis of an older deal,
  not a new capital-allocation event this week — not filed, but Collaborative Fund's
  parallel D.C. United stake is worth a future look if it recurs with a watchlist VC.

## Watch next week
- Kleiner Perkins, Lightspeed, Accel, Evantic Capital, Insight Partners — all
  repeat co-investors with the watchlist this week (see discovered_allocators.csv).
- Rightway ($155M Series E, Khosla, Sep 25), Moonwalk Biosciences ($70M Series B,
  Khosla, Sep 8), PrismML (seed, Khosla, Sep 17) — single-mention Khosla
  participations I didn't chase to a primary this week; worth a confirm pass.
- a16z's reported ~$20B AI-focused megafund target — chase for an actual close.
