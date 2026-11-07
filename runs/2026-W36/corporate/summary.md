# Corporate — 2026-W36 summary

## Filed
- **4 verified rows**, **1 candidate row**. No new untracked co-investors this run
  (SB Energy's other backers, SoftBank and Blackstone, are already on the alt_manager
  watchlist), so no `discovered_allocators.csv` this week.

## The big signal: NVIDIA's Ohio Stargate stake finally has real numbers
The stale candidate we've been chasing since 2026-W32 ("NVIDIA-OpenAI discussing
$500B Ohio data center") resolved into something much more specific and Tier-1
confirmed via NVIDIA's own 8-K (filed 2026-08-17): NVIDIA is putting **$1.5B in
direct equity** into SB Energy (the SoftBank-backed developer of the PORTS-Pike
Technology Campus in Pike County, Ohio, on the old Portsmouth Gaseous Diffusion
Plant site), while separately guaranteeing OpenAI's 20-year lease there via a
**residual-value guaranty capped at $105B**. That guaranty is a contingent
obligation, not cash out the door — it's what let SB Energy line up project
financing, and press coverage collapsing it into "NVIDIA backs $105B in Ohio"
was conflating the two mechanisms. Filed as two separate rows (equity vs.
guaranty) with explicit "don't sum these" notes, since a reader summing
amount_usd across both would double an already-huge number.

## Second signal: two more stale candidates moved, one didn't
- **Lancium** — upgraded candidate → verified. Lancium's own PRNewswire release
  (2026-08-24) confirms NVIDIA "making a strategic investment" as part of a tech
  partnership across its 15+GW land portfolio. Company still won't confirm the
  amount, so the $2B figure carries forward from The Information as
  `amount_estimated=1`.
- **Hugging Face** — new lead, filed candidate, NOT an upgrade of anything on
  file. NVIDIA is reportedly close to buying Hugging Face for $12.9B (The
  Information, 2026-08-27, relayed by CNBC/TechCrunch/Yahoo/Futurum/TechTimes —
  all one origin, circular-reporting guard applied). CNBC is explicit that no
  signed agreement exists yet and the deal "could still fall apart," so this
  stays candidate pending a PR or 8-K.

## Amazon: one quiet but real acquisition
AWS signed a definitive agreement to acquire **DuckLabs** (Amsterdam, makers of
the open-source DuckDB analytics engine), announced 2026-08-26 on the AWS Big
Data Blog and aboutamazon.com — Tier 1, terms undisclosed. DuckDB itself stays
independent/open-source. Sector doesn't cleanly map to the canonical list
(embedded analytics database, not physical AI infra); filed under `ai-data` /
`data-platform` as the closest fit and flagged in notes per CONTEXT.md's
unmapped-sector guidance.

## Checked, nothing new to file
- **Alphabet**: no new third-party capital allocation since the 2026-08-12
  Blacksmith follow-on already on file. The $9B Virginia buildout and the $80B
  equity raise are Alphabet spending on its own infrastructure/balance sheet,
  not capital allocated to a third-party target, so out of scope. (Aside, not
  filed: Alphabet's ~$40B Anthropic commitment from April 2026 does not appear
  to be on file at all under any run — well outside this week's 30-day sweep
  window so not backfilled here, but worth a look if the filings agent hasn't
  already captured it.)
- **Meta**: no new deal since the 2026-07-28 BlackRock/El Paso row. Checked
  investor.atmeta.com and recent nuclear/Nebius coverage — all older than the
  30-day window.
- **Microsoft**: no new deal since 2026-07-28 (Mate Security/M12). M12's most
  recent portfolio move was an exit (LoginRadius, 2026-08-20), not an
  investment.
- **Oracle**: still zero events on file. Its 2026 activity (the $45-50B
  debt+equity raise, ~$35B capex) is balance-sheet buildout for Oracle's own
  cloud capacity, not capital allocated to a third party, so it doesn't produce
  an event under this agent's scope even though Oracle is a Stargate equity
  funder in principle — no new Oracle-as-allocator news surfaced this run.

## Operating note: EDGAR and WebFetch were blocked this session
Both `python -m engine.edgar filings/cik` (which calls `data.sec.gov`) and
WebFetch to essentially every publisher domain tried (sec.gov, nvidianews,
globenewswire, hpcwire, finance.yahoo.com, even en.wikipedia.org) returned
`EGRESS_BLOCKED` / proxy 403s this run — a session-level network-egress policy,
not a data problem. `engine.edgar exists` (local DB only, no network) worked
fine and was used for every dedupe check. All research this week relied on
WebSearch result snippets, cross-corroborated across multiple independent
outlets per claim, with resolved (non-search-query) URLs cited as source_url.
Full-content WebFetch verification of the exact 8-K text and press releases
was not possible — flagged here so a future run with EDGAR access re-confirms
the two 8-K-sourced rows (SB Energy equity + the $105B guaranty) directly
against the filing.

## Watch next week
- Hugging Face: does NVIDIA sign, and does an HSR/antitrust filing surface
  (TechTimes is already framing this as the one recent NVIDIA "structured deal"
  that can't dodge merger review)?
- Lancium: still no official dollar figure — chase Lancium's or Blackstone's
  IR pages if the network egress block lifts.
- Oracle: genuinely quiet as an *allocator* this quarter despite being one of
  Stargate's four founding equity partners — worth checking whether that
  original Stargate equity check ever got filed by any agent, since it
  predates this tracker's window.
