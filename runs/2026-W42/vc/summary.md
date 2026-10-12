# VC Capital Allocation — Week 2026-W42 (window: ~2026-09-12 to 2026-10-12)

## What moved
Coverage of the seven-firm watchlist was thin on classic mega-round AI-lab
news this cycle and heavier on smaller, fast-moving Series A/B/seed and one
large agent-startup round:

- **Sequoia** was the most active name on file this week, appearing in three
  separate rounds: sole lead of Mecka's $60M Series B (robotics training
  data, Oct 7), sole lead of Catalyst's $30M seed (AI retail-trading agents,
  Oct 8, Fortune exclusive), and a participant (not lead) in a16z-led
  TypeSafe AI's $870M Series A at a $7.5B valuation (Oct 9).
- **Andreessen Horowitz** led that TypeSafe AI round — a striking data point
  on its own: TypeSafe hit a $7.5B valuation roughly three weeks after
  exiting stealth with a $40M DCVC seed. a16z GP Martin Casado takes a board
  seat.
- **Sequoia + Coatue** both appear in Instinct's $1B Series C at a $10B
  valuation (personal AI-agent startup, announced Sept 28 via Reuters/
  TechCrunch) — a ~4x valuation jump in about a month. Benchmark Capital
  co-invested here too and is not yet on our watchlist (see
  discovered_allocators.csv).

## Biggest signals
1. **AI-agent startups are repricing in weeks, not quarters.** TypeSafe AI
   (seed to $7.5B in 3 weeks) and Instinct (Series B to $10B in ~1 month)
   both show watchlist VCs chasing fast-moving agent/model companies at
   extreme velocity — closer to momentum investing than traditional
   diligence cycles.
2. **Sequoia's breadth this week:** three rounds across robotics, fintech-AI
   agents, and frontier models, lead on two of three — consistent with the
   firm's stated early-stage push.
3. **A quieter month for Thrive Capital, Founders Fund, Khosla Ventures and
   Altimeter** — no new capital-allocation event confirmed inside this
   window for any of the four despite broad searching (fund-raise talks and
   several deals exist, but all dated before 2026-09-12). One possible
   Altimeter lead (Thrive Holdings' ~$2B raise) has conflicting investor
   lists and an ambiguous close date and is filed as `candidate`, not
   `verified`.

## Blocked / infra notes
Outbound HTTPS to ordinary web hosts (sequoiacap.com, a16z.com, techcrunch.com,
reuters.com, sec.gov, bloomberg.com, etc.) was blocked at the agent-proxy
layer with a 403 (organization policy denial) for this session, so WebFetch
could not open any URL directly — portfolio/news pages for Sequoia and a16z
could not be checked directly (logged as yielded=0 Tier-1 attempts). All
sourcing this week relied on the WebSearch tool's own retrieval and its
returned resolved article URLs; `engine.edgar` (local CIK lookup) worked
normally and returned no existing records for any of this week's pairs.
WebSearch's own query budget for the run was also exhausted before a
follow-on check on the Thrive Holdings/Altimeter lead could be completed.

## What to watch next week
- Confirm Instinct's actual lead investor(s) — Sequoia, Benchmark and Coatue
  are all named across different reports with no single clean primary source.
- Chase a primary source (company announcement, Reuters/Bloomberg wire) for
  TypeSafe AI's round — only secondary/aggregator coverage was found.
- Re-check Thrive Holdings' ~$2B raise for Altimeter's actual role and the
  real close date.
- Watch for Thrive Capital, Founders Fund and Khosla Ventures activity —
  all three were quiet this window after large fund-raises earlier in 2026
  (Thrive X $10B close in Feb, Founders Fund $6B fund in May, Khosla's
  reported $5.5B fund talks in July); a next tranche of portfolio deployment
  from those vehicles is plausible soon.
