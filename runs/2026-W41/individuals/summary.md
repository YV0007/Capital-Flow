# Individuals — 2026-W41 summary

## Coverage
Swept the ~44-name watchlist (SV investors, founder-investors, corporate CEOs,
deep-tech specialists, global macro) via round-announcement angel-list searches
and targeted per-person searches, prioritizing the highest-yield pattern for
this class: who gets named as a backer in recent AI/deep-tech funding PR.
4 rows filed, all to `verified_events.csv` (3x verified_alpha, 1x verified).
`candidate_events.csv` is header-only this week — several leads (Musk/Paramount
"weighing" an investment, Thiel Macro's rebuilt 13F, older Bezos Expeditions and
Delian Asparouhov/Trae Stephens checks) were chased but either had no committed
capital, fell outside the 45-day window, or had no new disclosure this week; see
`source_log.csv` for what was checked and came up empty.

## Biggest signals
1. **Jeff Bezos — $2B personal check into Blue Origin's first-ever outside
   funding round** (disclosed 2026-09-30). The $10B round (oversubscribed, not
   yet closed per CEO Dave Limp) values Blue Origin at $140B and is led by
   Coatue Management (~$4B) — a 26-year run of being solely Bezos-funded now
   opening to outside capital. Largest and cleanest personal-capital signal of
   the week for this class.
2. **Peter Thiel + Dylan Field co-invest in Pilgrim's $25M biodefense seed**
   (disclosed 2026-09-23, $150M valuation, led by Buckley Ventures). A genuine
   network-adjacent convergence: Thiel (PayPal Mafia) and Dylan Field (Thiel
   Fellowship network) both appear as named backers in the same round, alongside
   Anthropic staff (Logan Graham, Sholto Douglas) and Coinbase's Brian
   Armstrong/Fred Ehrsam — worth watching as biodefense/dual-use national-security
   tech keeps pulling in this investor cluster.
3. **Elad Gil in Harvey's $550M growth round** (2026-09-09, $15.5B valuation,
   co-led by Diffusion and Lightspeed) — Gil named directly on Harvey's own
   company blog as a participating existing investor, our strongest-sourced
   (Tier-1, company PR) row this week.

## Discovered allocators
- **Coatue Management** (alt_manager) — led the Blue Origin round with ~$4B,
  the week's single largest check; not on the current alt_managers watchlist.
- **Buckley Ventures** (vc) — led Pilgrim's seed, pulled in two tracked
  individuals as co-investors.
- **Diffusion** (vc) — co-led Harvey's $550M round alongside Lightspeed.

## Constraints hit
Per this run's known issue, direct WebFetch calls to harvey.ai, the WSJ, and
CNBC were blocked by the session's egress policy (EGRESS_BLOCKED). All four
rows were sourced by reading the resolved page text WebSearch itself returned
and citing the actual article/blog URL it resolved — never a bare search-query
URL. `python -m engine.edgar` calls for Thiel, Bezos, Blue Origin and Harvey all
returned no known CIK (search path), consistent with individuals rarely
triggering EDGAR filings directly; no Form D related-person hits were found for
this week's leads.

## Watch next week
- Whether Blue Origin's oversubscribed round closes above $10B and whether any
  other tracked individuals (besides Coatue/Bezos) join as the round firms up.
- Follow-on disclosure for Pilgrim's cap table (a priced seed with this many
  named angels often gets a fuller breakdown in trade press within weeks).
- Thiel Macro's rebuilt 13F (power/nuclear/Amazon-heavy, ~$419M, Q2 2026) — not
  filed this week since it's outside the window/not a new commitment, but worth
  a Tier-1 EDGAR pull on next quarter's 13F-HR for position-level deltas.
