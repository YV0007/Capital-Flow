# VC Agent — Run Summary — 2026-W38 (week of 2026-09-14)

## Coverage
Watchlist: Sequoia, Andreessen Horowitz (a16z), Thrive Capital, Founders Fund,
Khosla Ventures, Coatue (all "key"), Altimeter ("watch"). The context pack
(`context.json`) reported `events_on_file: 0` / `last_event_date: null` for
every entity, but `engine.edgar exists` showed this was stale — W32 through
W37 already have a well-sourced backlog (Valar Atomics, Form Energy, Databricks
$5B, Mariana Minerals, Machine Age Fund, Growth Fund V, Thrive Holdings,
Corma, Firmus, Discovery Loop). Every allocator/target pair below was checked
against `engine.edgar exists` before filing; pairs already on file were
**not** re-filed (see "Already on file — skipped" below).

## Output
- **7 verified_alpha rows written, 0 candidate rows, 0 verified rows.**
- 0 rows graded fully `verified`: this session's **WebFetch tool was blocked
  for every domain tried, including sec.gov, a16z.com, formenergy.com,
  prnewswire.com and even example.com** (network egress policy denial, not a
  domain-specific block — confirmed via the agent-proxy status endpoint).
  All sourcing this run therefore came from WebSearch synthesis over real,
  resolved article URLs (never a query URL), not a direct Tier-1 fetch I
  personally read — so every row was capped at `verified_alpha` even where a
  Tier-1 primary (official PR, firm announcement) clearly exists and is cited
  in coverage, out of honesty about what was actually confirmed this run.
  Every row has ≥2 independent Tier 2–4 sources.

## The 3 biggest findings
1. **Andreessen Horowitz had the most active 30 days of any watchlist firm**,
   with three fresh, unfiled deals: led Gimlet Labs' $300M Series B (multi-silicon
   AI inference, $3B valuation, Sep 4), led Lightfield's $47M agentic-CRM Series A
   (Sep 9, with Coatue participating), and co-led (with new entrant Accel)
   Cognition's $2B+ Series E at a $48B valuation (Sep 8) — Founders Fund and
   Altimeter both continued/joined as participants in the same Cognition round.
2. **Cognition's Series E is the quarter's biggest single AI-application print
   among watchlist names** — $48B valuation, up from $26B just four months
   earlier — and pulled in three separate watchlist allocators at once
   (a16z co-lead, Founders Fund follow-on, Altimeter participant), filed as
   three rows per CONTEXT.md's one-row-per-allocator rule with the round total
   recorded once (on the a16z row) to avoid double-counting.
3. **Sequoia's $10M tranche in AI-agent-security startup AIR** (Sep 1) is a rare
   case where the allocator's own slice was actually disclosed (of a $50M seed
   split into a $10M Sequoia-led tranche + $40M Greenoaks-led tranche) rather
   than needing to be left blank — a cleaner data point than most co-led rounds.

## Already on file — skipped (confirmed via `engine.edgar exists`)
Sequoia/Form Energy, Coatue/Form Energy, Coatue/Databricks, Andreessen
Horowitz/Databricks, Thrive Capital/Databricks, Andreessen Horowitz/Machine Age
Fund, Andreessen Horowitz/Andreessen Horowitz Growth Fund V, Sequoia/Valar
Atomics, Khosla Ventures/Discovery Loop.

## Leads investigated and dropped (not filed, no candidate row)
- **a16z / OpenReserve** ($25M seed, Sep 3) — real event but a crypto/banking
  product with no fit in the canonical sector list; low priority, dropped
  rather than force a bad sector tag.
- **a16z / Kalanick robotics co.** ($1.7B, Jul 22) — outside the ~30-day window.
- **Altimeter / Cerebras** ($2B stake, SC 13G) — sources conflict on timing
  (one dates the position build to Q1 2026, another to an Aug 14 13G) with no
  way to resolve which reflects genuinely new capital in the window; dropped
  per the ambiguous-entity/ambiguous-timing rule rather than guess.
- **Khosla Ventures** $5.5B new-fund talks (Bloomberg, Jul 23) — explicitly
  not closed, and outside the 30-day window regardless.
- **Founders Fund / Ramp** ($1B raise "targeting", early Sep) — no confirmed
  close or investor list found before this session's WebSearch budget was
  exhausted; dropped rather than file on a headline-only lead.
- **Thrive Capital / Amazon** ($215M per 13F, disclosed Aug 14) and **Thrive
  Capital's $10B flagship fund** (closed Feb 17, 2026) — both real and
  well-sourced, but out of this run's forward-looking window / already
  superseded by the Databricks row on file; not re-filed.

## Discovered allocators (see discovered_allocators.csv)
- **Greenoaks Capital** — co-led AIR's seed with Sequoia.
- **Radical Ventures** — co-led Discovery Loop's seed with Khosla Ventures.
- **Accel** — new co-lead alongside a16z on Cognition's Series E.

## Watch next week
- Cognition's Series E close/8-K-equivalent disclosures, if any come through
  an EDGAR-registered participant.
- Whether a16z's Machine Age Fund ($1.1B, Aug 28) starts deploying into named
  targets — it is brand new and thesis-only so far.
- Founders Fund/Ramp — worth a fresh check once the round actually closes.
- Re-run EDGAR/WebFetch access next session; this run's grading was
  artificially capped at verified_alpha by a total WebFetch outage, not by
  the underlying evidence.
