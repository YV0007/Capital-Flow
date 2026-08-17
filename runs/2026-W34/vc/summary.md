# VC Allocators — ISO Week 2026-W34
_Disclosures 2026-08-10 to 2026-08-13 (~30-day lookback window; earlier-window events already
filed in W32/W33 are not repeated here). 10 verified rows / 0 candidate rows across 6 of 7
watchlist firms, spanning 4 distinct capital events plus one candidate-to-verified upgrade._

## What moved

A tight, high-conviction cluster in the back half of the window (Aug 10-13): three multi-VC
rounds where watchlist capital co-invested directly with each other (Corma, three-way; Form
Energy and Databricks, two-and three-way), plus a smaller solo a16z Series A, plus one prior
candidate (Thrive Holdings) crossing the line into a confirmed close. Sequoia, Khosla, Coatue,
Andreessen Horowitz, Thrive Capital and Altimeter all produced attributable rows this window;
Founders Fund did not clear the bar (see below). Earlier-in-window events already reported in
prior runs (Valar Atomics, Atoms, Base Power, Hadrian — all dated 2026-07-22 to 2026-08-06 and
already in `runs/2026-W32/vc/verified_events.csv`) are intentionally not re-filed to avoid pure
duplication; see Confidence & limitations.

## Biggest signals

1. **Databricks' $5B close at a $190B valuation — Coatue leads, a16z and Thrive follow on.**
   What was a signed-but-unclosed $3B/$188B term sheet in mid-July (filed as a W32 candidate)
   actually closed 2026-08-13, upsized to $5B after ~$15B of investor demand materialized on an
   original ~$1B target. Coatue is framed as lead alongside Blackstone, MGX and T. Rowe Price;
   Andreessen Horowitz and Thrive Capital both re-up as existing investors. Three watchlist VCs
   in one round, and a clean candidate-to-verified upgrade with a Tier-1 company source.

2. **Corma's $60M seed — Sequoia, Khosla and Coatue all in one round.** A Tel Aviv/SF startup
   building a foundation model purpose-built for *defensive* cybersecurity (as opposed to
   general-purpose LLMs, which the company argues are far better attackers than defenders)
   pulled three watchlist firms into a single seed round — Sequoia leading. Early Fortune
   100/500 deployments reportedly cut threat-response time by >94%.

3. **Thrive Holdings' $2B round closes — Altimeter confirmed, upgrading a 5-week-old candidate.**
   First outside capital ever into Thrive Capital's AI-services roll-up (previously funded
   solely by Thrive Capital's own LPs). SoftBank led; Altimeter and D1 Capital Partners were the
   other new investors. This was filed as a single-origin `candidate` in W32 (The Information,
   2026-07-06, "raising"); Thrive Holdings' own press release now confirms the $2B/$12B close,
   so it upgrades to `verified` this week rather than being re-filed as a fresh candidate.

4. **Form Energy's $750M Series G — Sequoia joins, Coatue re-ups.** T. Rowe Price led the
   iron-air 100-hour battery maker's raise (total equity now >$2B); Sequoia is a new investor,
   Coatue an existing one continuing. Batteries aimed squarely at AI-datacenter grid load (30 GWh
   committed to Google, 12 GWh to Crusoe).

## Confidence & limitations

- **10 verified rows, all Tier-1 primaries** (a PR-wire company release, two direct company
  press pages, and a company newsroom/blog page), each independently corroborated by 3-9 Tier
  2-4 outlets. **Zero `candidate` rows filed** — no weak/single-source lead cleared the bar for
  inclusion this week after the escalation loop; the one open lead from prior weeks (Khosla's
  reported $5.5B fund family, still "in talks" per a single Bloomberg origin, no Form D located)
  is unchanged since W32/W33 and not re-filed to avoid duplication.
- `amount_usd` carries the **FULL round** on every allocator row; no round this window disclosed
  a per-investor slice. Don't sum `amount_usd` across rows of the same target without deduping.
- **Overlap with prior weeks, by design:** this agent does a rolling ~30-day lookback each run,
  so a large fraction of the window (2026-07-18 through roughly 2026-08-09) reproduces events
  already captured in `runs/2026-W32/vc/verified_events.csv` — Sequoia/Valar Atomics ($1B,
  08-03), a16z/Atoms ($1.7B, 07-22), Coatue+Altimeter+Thrive+a16z/Base Power ($1B, 08-03), and
  a16z+Founders Fund+Altimeter/Hadrian ($1.37B, 08-06). These are not re-filed here; only events
  disclosed 2026-08-10 or later, plus the Thrive Holdings candidate-to-verified upgrade, are new
  to this run.
- **No attributable Founders Fund event this window.** Checked Founders Fund's own news/portfolio
  activity and the open P-1 AI $50M Series A lead (filed `candidate` in W32 on a single
  techstartups roundup, uncorroborated by the company's own GlobeNewswire PR) — no update found;
  not re-filed. Founders Fund's only 2026 Anthropic activity (co-leading the $30B Series G) dates
  to February 2026, well outside this window.
- **Databricks source caveat:** no single databricks.com press release was found devoted solely
  to the $5B/$190B close; the newsroom page cited bundles the funding announcement with Q2
  revenue metrics. Graded Tier-1/verified on the strength of that company page plus near-unanimous
  Tier-3 corroboration (Bloomberg, CNBC, TechCrunch, Yahoo Finance, PYMNTS, Seeking Alpha).
- **Tooling note:** WebFetch was blocked by the network egress proxy for every external domain
  attempted this session (Bloomberg, TechCrunch, valaratomics.com, en.wikipedia.org — confirmed
  across unrelated domains, consistent with W33's identical finding). All sourcing relies on
  WebSearch's synthesized summaries rather than a direct fetch/read of page HTML. URLs cited are
  real, resolved documents surfaced by search; their exact byte-for-byte content was not
  independently re-read via WebFetch.

## Watch next week

- **Khosla's $5.5B fund family** — still no Form D or firm confirmation; watching for a close.
- **P-1 AI's $50M Series A** — whether Founders Fund's disputed participation gets confirmed or
  contradicted by a company portfolio-page listing.
- **Databricks' next move** — three raises now in under 8 months ($1.6B Series H → $3B/$188B
  term sheet → $5B/$190B close); watch whether the pace continues.
- **T. Rowe Price and Point72** — both now repeat co-investors alongside watchlist VCs across
  successive weeks in large AI-adjacent rounds (see `discovered_allocators.csv`); worth tracking
  as de facto universe additions if the pattern continues.
