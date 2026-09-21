# VC Agent — Run Summary — 2026-W39 (week of 2026-09-21)

## Coverage
Watchlist: Sequoia, Andreessen Horowitz (a16z), Thrive Capital, Founders Fund,
Khosla Ventures, Coatue (all "key"), Altimeter ("watch"). `context.json` again
reported `events_on_file: 0` / `last_event_date: null` for every entity, but
`engine.edgar exists` showed W32-W38 already carry a well-sourced backlog
through 2026-09-09 (Lightfield, Cognition, AIR, Databricks, Firmus, Valar
Atomics, Corma, Mariana Minerals, Machine Age Fund, Growth Fund V, Thrive
Holdings). This run searched forward from that Sep 9 high-water mark through
today (Sep 21) and re-swept ~30 days back to catch anything missed earlier.
Every allocator/target pair below was checked against `engine.edgar exists`
before filing; none were already on file.

## Output
**18 verified_alpha rows written, 0 candidate rows, 0 verified rows.**
All 7 watchlist names got at least one new row this run:
Khosla Ventures (5), Sequoia (3), Founders Fund (3), Thrive Capital (2),
Altimeter (2), Andreessen Horowitz (2), Coatue (1).

0 rows graded fully `verified`: **this session's WebFetch tool was blocked for
every domain tried** (sec.gov, a16z.com, tryprofound.com, voya.energy,
dealroom.co, techcrunch.com — confirmed via repeated attempts across unrelated
domains, same total-outage pattern as last week's W38 run). All sourcing
therefore came from WebSearch's own synthesis over real, resolved article
URLs I never personally fetched — so every row is capped at `verified_alpha`
even for several where an official company newsroom or PR-wire release
(GlobeNewswire, Business Wire, regentcraft.com, crusoe.ai) clearly exists and
is cited in `notes`, out of honesty about what was actually confirmed this
run versus mirrored via search. Every row has 2+ independent Tier 1-4 sources.

## The 3 biggest findings
1. **Harvey's $550M round (Sep 9) pulled in three watchlist firms at once** —
   Andreessen Horowitz, Sequoia and Coatue all continued as existing-investor
   participants alongside new co-leads Lightspeed Venture Partners and
   **Diffusion**, a brand-new firm founded by a former Coatue investor (see
   discovered_allocators.csv). Valuation jumped to $15.5-15.6B from $11B just
   five months earlier — legal AI remains one of the fastest-repricing
   application categories on the watchlist.
2. **Khosla Ventures had the busiest 30 days of any watchlist firm** — five
   distinct events: led Nara Health's $14M AI-native health-insurance seed
   (Sep 14), led (with Thrive Capital participating) Split Pay's $125M
   combined A/B (Sep 8), and continued as a participant in Profound's $180M
   Series D (Sep 15, alongside lead Sequoia), Factory's $200M growth round
   (Sep 15, alongside Sequoia again), and Mazama Energy's $135M geothermal
   Series B (Sep 17).
3. **Founders Fund and Altimeter both showed up in Crusoe's $3.9B Series F**
   (Sep 17, $30.9B valuation) — the single largest capital event on the
   watchlist this run, and a clean neocloud/GPU-capacity signal alongside
   Founders Fund's continuing bets in power-energy (Voya Energy) and
   defense-adjacent maritime (REGENT Craft).

## Already on file — skipped (confirmed via `engine.edgar exists`)
None of this run's 18 allocator/target pairs were already on file — the
Sep 9-21 window was genuinely unfiled territory once the (stale) `null`
last_event_date in context.json was cross-checked against the real backlog.

## Leads investigated and dropped (not filed, no candidate row)
- **a16z / Westmag** ($11M seed) — funding actually closed in 2025; the
  business-wire/a16z public announcement only went out June 2, 2026. Both the
  event date and the disclosed date fall well outside the ~30-day window.
- **Coatue / Anysphere (Cursor)** ($2.3B Series D, $29.3B valuation) — real
  and unfiled anywhere in the run history, but announced Nov 13, 2025 —
  far outside this run's window. Flagging here rather than filing on an old
  date; worth a dedicated backfill pass if the engine wants historical
  coverage.
- **Anthropic $30B Series G at $380B** (Coatue, Founders Fund co-leads) —
  closed Feb 12, 2026, outside window.
- **Anthropic's ~$900B-valuation round** (Sequoia, Altimeter, Dragoneer,
  Greenoaks reported as co-leads) — sourcing (Bloomberg, The Information) is
  all from late April/early May 2026 coverage of a round "closing as soon as
  next week"; no fresh September confirmation found, so not re-chased this
  run to avoid filing on a stale date.
- **Split Pay's AI angle** — filed both rows (Khosla lead, Thrive Capital
  participant) but flagged rather than confidently tagged: coverage
  establishes AI-driven underwriting is standard for this niche, not that
  Split Pay itself is AI-core. Sector left as the closest bucket
  (ai-applications/fintech-ai) per CONTEXT.md's unknown-sector rule, not
  dropped.

## Discovered allocators (see discovered_allocators.csv)
- **Diffusion** — new firm, founded by ex-Coatue investor Kris Fredrickson,
  co-led Harvey's $550M round.
- **Halo Fund** — led Savvy Wealth's $100M Series C.
- **Doerr Capital** and **Centaurus Capital** — co-led Mazama Energy's $135M
  Series B.
- **Energy Impact Partners** — led both of Voya Energy's rounds to date.
- **Madrona Venture Group** — co-led SciFin's $44M seed with Altimeter.
- **Mare Liberum** — co-led REGENT Craft's $240M Series B.

## Watch next week
- Whether Diffusion (the new Harvey co-lead) shows up leading or co-leading
  another round — worth tracking as its own entity given the Coatue lineage.
- Crusoe's Series F was reported as an "initial close" (Sep 17) — watch for
  a final-close amendment or additional participants disclosed later.
- Anthropic's ~$900B round: chase a fresh, dated confirmation next run rather
  than re-citing April/May reporting.
- Re-run WebFetch access next session; this run's grading was artificially
  capped at verified_alpha by a total WebFetch outage for the second week
  running, not by the underlying evidence quality.
