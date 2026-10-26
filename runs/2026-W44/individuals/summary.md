# Individuals — Week 2026-W44 Summary

## Bottom line
Zero events (verified or candidate) filed this week. Swept roughly 30 of the
~40 names on the individuals watchlist, leading with round-announcement angel
lists per `agents/individuals.md`'s mandated search order, then tried Form D
and person-tracker follow-ups. Nothing that cleared the bar of (a) a specific,
dated capital-allocation event, (b) attributed to the *person* rather than
their firm/company, and (c) falling inside the ~45-day lookback (2026-09-11
through 2026-10-26) turned up. Writing header-only CSVs rather than forcing
weak leads into rows — see "Leads that didn't make the cut" below for what
was chased and why each was dropped, per the escalation-loop requirement to
document rather than silently drop.

## Environment constraint (flag for the engine owner)
SEC EDGAR was unreachable from this sandbox for the entire run:
- `python -m engine.edgar sweep 2026-W44` returned `{"entities": 14, "errors": 14}`
  — every context-pack entity errored.
- `python -m engine.edgar filings "<name>" --forms D --since ...` returned
  `cik: null` / "take the search path" for every name tried (Peter Thiel,
  Founders Fund).
- Direct network access to `sec.gov` / `data.sec.gov` / `efts.sec.gov` failed
  at the proxy layer (403 on CONNECT), and `WebFetch` itself returned
  `getaddrinfo ENOTFOUND` for *every* URL tried this session, including
  non-SEC domains (techcrunch.com, google.com) — so no page could be
  re-fetched and read directly this run, only `WebSearch`'s own synthesis.
This means the Tier-1 Form-D-related-person path (individuals.md's #2 primary
confirm) was completely unavailable, and no `source_url` could be hand-verified
by re-fetching it. All source_log entries below reflect what WebSearch surfaced
and summarized, cited at the resolved article URL it returned (never a search
query URL). This should be treated as reduced confidence across the board for
this run, not a signal that nothing happened in the market.

## What moved — nothing cleanly attributable
No personal check, personal SPV, or personal fund-launch by a watchlist
individual was found dated inside the window with a usable source. The
closest things to real signal:

1. **NFDG (Nat Friedman / Daniel Gross) has effectively gone quiet.** Multiple
   sources confirm Meta's 2025 deal to buy into NFDG's funds and hire both
   men into Meta Superintelligence Labs (alongside Alexandr Wang, also now a
   Meta exec) means NFDG "won't make net new investments" — a structural drop
   in personal-check velocity from two `thiel_extended` core names, worth
   flagging for future runs rather than chasing further. (tier 3,
   https://www.saastr.com/the-1-1b-vc-fund-that-4xd-in-two-years-then-got-acquired-by-meta)
2. **David Sacks' personal portfolio is shrinking, not growing**, following
   his White House AI & Crypto czar appointment — reporting describes >$200M
   in personal + Craft Ventures crypto/AI-related holdings sold off ahead of
   the role, under an ethics-waiver controversy. No new personal checks
   expected while the waiver scrutiny continues. (tier 3,
   https://www.nbcnews.com/business/markets/david-sacks-sold-200-million-crypto-related-holdings-trump-admin-rcna196514)
3. **Bezos Expeditions was the most active named family office in 2026**
   (Fintrx-sourced: 8 direct AI-startup investments YTD as of the ~July
   report, 5 in June alone, headlined by Jeff Bezos co-leading Project
   Prometheus's ~$12B Series B), but every dated instance I could confirm
   falls in H1 2026 — outside this week's ~45-day window — so nothing new to
   file this run. Worth checking again next week; this is a `check_first`
   candidate for the context pack going forward.

No network-coinvestment signal (2+ tracked-network members in the same deal)
surfaced this week — nothing above cleared even candidate status, so there's
nothing to test the 2+ threshold against.

## Leads that didn't make the cut
- **Mercor's reported Nvidia talks at a $20B valuation** (The Information, ~Aug
  19 2026): unclosed ("no indication the investment has closed"), outside the
  45-day window, and the named individual backers I found (Peter Thiel, Jack
  Dorsey, Adam D'Angelo, Larry Summers) are tied to Mercor's *October 2025*
  Series C, not this pending round — filing any of them against the new round
  would be the "ambiguous entity / wrong round" mistake CONTEXT.md warns
  about, so dropped rather than guessed.
- **Elad Gil's 2026 deal flow** (Cognition, Saronic, Applied Compute, Odyssey,
  NavigateAI, Socket, Crosby) is real and well-documented by PitchBook/Seedtable,
  but every dated entry falls March–June 2026 — well outside this week's
  lookback. Flagging Elad Gil as a name to re-check weekly going forward
  (currently 0 events on file per the context pack, so his whole 2026 history
  is still a gap for the engine, just not one this run's window covers).
- **Varda Space Industries' $251M Series D** (Sept 30 2026, inside the window)
  is real, but the named backers (Lux Capital, Natural Capital, Khosla
  Ventures, General Catalyst, Founders Fund, Caffeinated Capital) are all
  firms, and Delian Asparouhov is the company's co-founder (capital recipient),
  not an outside allocator — this belongs to the VC agent's beat, not
  individuals, per individuals.md's explicit "Founders Fund deploying is the
  VC side" rule.
- **Leopold Aschenbrenner's Situational Awareness Partners** — Patrick
  Collison, John Collison, Daniel Gross and Nat Friedman are reported as
  original anchor LPs, but that commitment dates to the fund's 2024 launch,
  not this week, and the fund's current news (a reported drawdown from ~$45B
  to ~$10B AUM after margin calls) is a public-market P&L event, not a new
  capital-allocation event in scope.
- Checked without any usable hit at all: Peter Thiel, Alexandr Wang, Marc
  Andreessen, Keith Rabois, Reid Hoffman, Garry Tan, Josh Kushner, Palmer
  Luckey, Lucy Guo, Austin Russell, Laura Deming, Joe Lonsdale, Trae Stephens,
  Vinod Khosla, Philippe Laffont, Eric Schmidt, Patrick/John Collison, Neil
  Mehta, Dylan Field, Stanley Druckenmiller, Larry Ellison, Masayoshi Son
  (SoftBank's OpenAI/Stargate moves are corporate, not personal — correctly
  out of scope per the class brief).
- Not reached before the session's web-search budget was exhausted: Sam
  Altman, Ray Dalio, Bill Ackman, David Tepper, Ben Horowitz, Hemant Taneja,
  Bill Janeway, Peter Barrett, Mike Maples Jr., Bill Gurley, Ali Ghodsi. These
  should be the first stop next run.

## Discovered allocators
None — no new, not-yet-tracked individual surfaced co-investing alongside a
watchlist name this week (there were no qualifying events to surface one
from).

## What to watch next week
- Re-run Bezos Expeditions, Elad Gil, and the NFDG/Meta situation specifically
  for anything dated after this window closes.
- Retry the SEC EDGAR / Form-D path once the sandbox's network access to
  sec.gov is restored — this run had zero Tier-1 capability, which is the
  single biggest confidence drag on this class.
- Mercor's pending Nvidia-led round and Thinking Machines Lab's reported
  $5–6B round are both close to closing per press talk; worth checking for a
  close announcement and a fresh, correctly-dated angel/backer list.
