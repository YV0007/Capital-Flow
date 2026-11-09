# VC Agent — Week 2026-W46 Summary

## Headline
A quiet news month by dollar volume compared to recent AI-lab megarounds, but three real
signals: Sequoia restructured and raised fresh capital, Thrive Capital/Founders Fund backed
Ramp's huge fintech round, and Khosla Ventures stayed active on healthcare/India and
hard-tech bets. Coverage this week skewed fintech/healthtech/climate-tech rather than pure
AI-lab/compute — none of it maps cleanly onto the canonical AI-buildout sectors, which is
flagged row-by-row in `notes`.

## Biggest signals
1. **Sequoia's "Sequoia of Tomorrow" memo (Nov 4).** Raised ~$10B in new funds while
   collapsing its Early + Growth division into one team, ending the Arc accelerator and
   Scouts program, and closing its London office. This is a structural/strategic move as
   much as a capital event — graded `verified_alpha` (TechCrunch directly quotes the primary
   memo, but I didn't fetch the memo itself on X).
2. **Ramp's $1.85B round at a $60B valuation (Oct 9).** Dragoneer and Thrive Capital co-led,
   with Founders Fund, Sands Capital and Avenir Growth also in; filed as one row per
   watchlist allocator (Thrive = co-lead, Founders Fund = participant) with blank
   `amount_usd` and `round_total_usd` = $1.85B to avoid double-counting. This is the week's
   largest confirmed capital-allocation event touching our watchlist.
3. **Khosla Ventures' steady cadence.** A confirmed $50M Series B follow-on into Even
   Healthcare (India hospital economics, Oct 19) plus several weaker/disputed leads: Sabi
   (brain-computer interface, lead role disputed), Hertha Metals (green steel, date/amount
   conflicting across sources), and a disputed "returning investor" slot in Abby Care's
   Series C that I could not confirm against primary reporting.
4. **a16z's Tutor Intelligence Series B (Nov 2)** is the cleanest Tier-1 row this week —
   a16z's own announcement names itself as the robotics round's lead, though the amount is
   undisclosed anywhere.
5. **Lambda's reported $4B pre-IPO round (Coatue + Blackstone leading)** is still just
   reported/in-talks per the most recent recheck (Oct 28) — filed as `candidate` since no
   capital is confirmed to have moved.

## What's weak / unconfirmed
- **Abby Care Series C ($82M, Oct 15):** Transformation Capital is the confirmed lead per
  Fortune's exclusive. Khosla Ventures, Thrive Capital and Sequoia appear as "returning
  investors" only in aggregator tables (Caplight, Fundz), explicitly marked "unverified" by
  one tracker, and are absent from Fortune/HIT Consultant/Home Health Care News reporting.
  Filed all three as `candidate` rather than dropped, per the escalation rule.
- **Sabi's $50M seed (Oct 9):** the raise and investor list are solid (CEO's own X post),
  but "led by Khosla Ventures" rests on an unverifiable Forbes headline; one analysis
  disputes it outright. Filed as `candidate` with the dispute spelled out.
- **Hertha Metals Series A (~$134M):** Khosla/Doerr co-lead is solid, but sources disagree
  on the date by about three weeks (Sept 29 vs. Oct 19) — could be an initial close vs. a
  later disclosure. Filed as `candidate`.

## Discovered allocators
- **Dragoneer Investment Group** — co-led Ramp with Thrive Capital; recurring crossover
  growth fund in large AI-adjacent fintech/infra syndicates.
- **Alpha Wave Global** — co-invested with Khosla in Even Healthcare.
- **Doerr Capital** — co-led Hertha Metals with Khosla; climate/deep-tech specialist.

## Watch next week
- Whether Lambda's $4B Coatue/Blackstone round actually closes (or gets a company
  confirmation / S-1 signal).
- Whether Sequoia discloses fund-level detail behind the "~$10B" headline figure.
- Whether Abby Care's own channels (or a primary outlet) ever name Khosla/Thrive/Sequoia
  directly, resolving the aggregator-only "returning investor" claim.
- General market note: little disclosed watchlist-VC activity in pure ai-labs/ai-compute/
  semiconductor sectors this specific week — most hits were fintech, Indian healthtech and
  climate/industrial deals, which don't map cleanly to the canonical sector list (flagged
  throughout).

## Correction (post-ingest)
- This candidate Hertha Metals row was removed after ingest: it is the SAME Series A follow-on the filings agent independently confirmed at Tier 1 via Hertha Metals own SEC Form D (filed 2026-10-27), which superseded this row per its own merge note. Because the two rows carried different disclosed_date values (2026-10-19 here vs 2026-10-27 on the Form D), engine/ingest.py exact-match dedup could not merge them automatically, so the weaker candidate row was removed manually to avoid double-counting one round as two stakes. See filings/verified_events.csv for the surviving, Tier-1-confirmed row.
