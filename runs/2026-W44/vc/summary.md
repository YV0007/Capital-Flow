# VC Capital Allocation — Week 2026-W44 (window: ~2026-09-26 to 2026-10-26)

## What moved
A quieter cycle for the watchlist's headline mega-rounds, but steady lead/co-lead
activity from the two most active firms, **Andreessen Horowitz (a16z)** and
**Sequoia**, almost entirely at seed/Series A/B. Seven rows filed this week
across those two allocators (6 for a16z, 3 for Sequoia, with TypeSafe AI shared
between them). No new, in-window events were found for Thrive Capital,
Founders Fund, Khosla Ventures, Coatue, or Altimeter despite checking each
firm's own site, portfolio trackers, press, and known co-investment rounds
(Anduril, Switch, Thrive Holdings, Ramp, Mistral, Anthropic, xAI, Perplexity,
SSI) — all the real deals touching those names fall well outside the ~30-day
window (May–Aug 2026) and were presumably already captured in earlier runs.

Two deals that looked new on the surface — **TypeSafe AI**'s $870M Series A
(a16z lead / Sequoia participant, Oct 9–10) and **Mecka**'s $60M Series B
(Sequoia lead, Oct 7) — turned out to already be on file from 2026-W42 (Tier
2/verified_alpha, via dealroom.co). Rather than re-file them as duplicates,
those two rows were kept but repointed to the lead firm's own announcement
page (a16z.com, sequoiacap.com) to **upgrade the source from Tier 2 to Tier
1 / status to verified** — flagged explicitly in `notes` so ingest merges
forward instead of creating churn. **Instinct**'s $1B Series C (Sequoia +
Coatue, Sept 28) is also already on file from W42 at the same tier (Tier 3);
since the new source found here wasn't stronger, it was **not** re-filed.

## Biggest signals
1. **a16z's agentic-security and robotics push.** Three of a16z's six rows
   this week are security- or robotics-adjacent: **Armadin** ($255.5M Series
   B, Kevin Mandia's autonomous security platform, co-led with Accel, >$2.5B
   valuation), **doxxnet** ($38M Series A for encrypted P2P networking
   between people and their AI agents), and **Eka Robotics** ($150M Series A
   at $1.45B for a vision-force-action manipulation model, co-led with new
   co-investor F-Prime Capital). Read together with **Preference Model**'s
   $16M a16z-led seed (RL training environments for frontier labs), a16z is
   funding the picks-and-shovels layer around frontier models — security,
   networking, and training data/environments — as much as the labs
   themselves this cycle.
2. **Sequoia's TypeSafe upgrade is the quarter's biggest check by far.**
   $870M at a $7.5B valuation, just three weeks after a $40M seed, for a
   "decision model" (Jev) aimed at embedding AI-driven decisions inside
   software at runtime — a huge markup even by 2026 AI standards, and now
   confirmed directly by both a16z's and Sequoia's own posts rather than
   secondary aggregation.
3. **New untracked co-investor: F-Prime Capital**, co-leading Eka Robotics
   alongside a16z — logged in `discovered_allocators.csv`. (Benchmark and
   Accel, the other repeat co-investors seen this cycle, were already
   flagged in W42/W38/W41 and weren't re-flagged.)

## What to watch next week
- Whether **Khosla Ventures**' reported $5.5B fund (talks since July 2026)
  reaches a final close — still unconfirmed as of this run.
- **Anduril**'s discussed new round at a >$60B valuation (The Information,
  undated headline-only) — watch for Founders Fund/Thrive/a16z participation
  to firm up.
- Any primary (Tier 1) confirmation surfacing for **Instinct**'s Sequoia/
  Benchmark/Coatue Series C, which is still resting on Tier 3 press.
