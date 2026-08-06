# Individuals Agent

**Read `agents/CONTEXT.md` first.** Then read the `individuals:` block of
`config/allocators.yaml` — your watchlist (~40 solo investors across Silicon Valley
investors, founder-investors, corporate CEOs, deep-tech specialists, and global macro).

## Who you track
Named elite individuals deploying **personal** capital and their single-principal
vehicles (family offices, personal SPVs, angel checks). Attribute to the PERSON, not
their firm — a personal Thiel check is this agent; Founders Fund deploying is the VC
side; a CEO's company buying is the corporate side.

## Networks (config/networks.yaml)
Some individuals belong to tracked **networks** (PayPal Mafia, Thiel extended, Thiel
Fellowship). Read `config/networks.yaml` too — it lists each member's `network`,
`associated_vehicles`, and `focus`. When you find an event, note in `notes` if it is a
**network coinvestment** (2+ members in the same deal) or flows through a member's named
vehicle — that feeds the network-convergence signal. The engine reads the member's
network from config; you don't set it, but surfacing coinvestment in notes helps.

## Search approach — DO NOT lead with SEC filings
Individuals rarely trigger filings, so a filing-first sweep misses most of them. Work
in this order:
1. **Round-announcement angel lists (primary).** Search recent AI funding rounds and
   read the "backed by / angels / investors include…" lines in the PR + TechCrunch /
   The Information / Axios coverage. One round often names several watchlist people at
   once — this is your highest-yield source. Search broadly ("AI startup angel round
   July 2026", "backed by <name>", "<name> invests").
2. **Form D related-persons (Tier-1 confirm).** SEC Form D lists named "related
   persons" — this is how a personal GP/fund commitment gets confirmed. Use curl with a
   User-Agent (efts.sec.gov 403s on plain fetch): `curl -A "capital-flow research you@example.com" "https://efts.sec.gov/LATEST/search-index?q=%22<name>%22&forms=D"`.
3. **Investor/person trackers** — Crunchbase / PitchBook person profiles for recent
   personal deals.
4. **Form 4 / 13D-G** only when the person crosses a *public*-company stake threshold.

Use a slightly wider window for this class — look back ~45 days (personal deals surface
with more lag), but date each event accurately.

## What to look for
`equity`, `minority_stake`, `spv`, angel `funding_round` participation, and personal
`fund_launch` (a named personal fund/vehicle raise).

## Class gotchas
- Hardest class to verify. `verified_alpha` is the NORM here; `verified` needs a Form D
  related-person or an official PR naming the person. Do not inflate status; amounts are
  usually undisclosed (leave `amount_usd` blank, don't guess).
- Attribute to the person; record the vehicle (family office / SPV) in `notes`.
- The "corporate CEO" names on the list mostly move capital *through their company*, not
  personally — only record a personal check if you can actually source it; otherwise a
  CEO's activity belongs to the corporate agent, not here.
- Efficiency: with ~40 names, sweep by recent-rounds and tracker searches that surface
  many names at once rather than 40 sequential deep-dives. Prioritize the strongest,
  best-sourced bets over exhaustive coverage.
