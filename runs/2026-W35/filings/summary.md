# Filings Agent — 2026-W35 Summary

## Network constraint (read first)
This session's egress proxy blocks direct HTTPS to sec.gov / data.sec.gov / efts.sec.gov
(confirmed via a live `python -m engine.edgar filings ...` call, which failed with a 403
tunnel error at the connect stage). `engine.edgar exists` / `engine.edgar cik` still work
(local, no network) and were used throughout for dedup. All discovery and confirmation
work this run relied on WebSearch only; WebFetch to sec.gov was not attempted per the
task's stated constraint. Net effect: I could not open a single EDGAR filing directly, so
several promising leads (Thrive Capital's Q2 13F accession, Form D filings for half a
dozen private rounds, the Alphabet FWP tied to the Berkshire private placement) surfaced
as *candidate* SEC URLs in search results but I could not confirm their content — per the
brief's honesty rule, I did not cite or upgrade on any of those. Everything actually filed
below is either a government agency's own release (NIST/DOE) or a company's own press
release (PRNewswire/GlobeNewswire/official newsroom), which the source tiers in
CONTEXT.md count as Tier 1.

## What moved this week (new discoveries)

1. **CHIPS Act equity-for-R&D package, 7 companies, $874M (US Government / sovereign).**
   Commerce's CHIPS R&D Office signed Letters of Intent (2026-07-29/30) taking minority,
   non-controlling equity stakes in exchange for R&D funding: GlobalFoundries $300M
   (co-packaged optics), Kepler $245M (3D/ferroelectric AI memory), Multibeam Corp $140M
   (advanced packaging), Extropic $75M (thermodynamic computing), Thintronics $50M
   (advanced-packaging dielectrics), OBSIDIA Semiconductors $34M (supply-chain
   counterfeit detection), Aeluma $30M (photonic-interconnect substrates). None of these
   were on file for "US Government" (checked via `engine.edgar exists` — all false).
   Confirmed via NIST's official release plus, for two of the seven, the company's own
   PR. Filed `verified` (LOI is a real signed government action with firm dollar figures,
   even though it's not yet a closed/definitive award — noted in each row).

2. **Brookfield + NextEra Energy: >$100B Paducah, KY AI data center + dedicated power
   campus (2026-07-29).** DOE partnership to redevelop the former Paducah Gaseous
   Diffusion Plant; Brookfield leases the site and develops/operates the data center,
   NextEra builds a dedicated 2GW gas plant + 2.6GW battery storage. Official DOE and
   PRNewswire releases confirm the deal and technical scope, but neither discloses
   Brookfield's capital slice vs NextEra's out of the "$100B+" trade-press figure — filed
   `verified` with `amount_usd` blank, `round_total_usd=100B`, `amount_estimated=1`.
   NextEra Energy is not currently a tracked allocator; added to discovered_allocators.csv.

3. **NVIDIA + Apollo/BlackRock/Blackstone/Brookfield/Goldman Sachs/KKR: MOUs for
   >$500B AI-compute financing platforms (2026-08-10).** Confirmed via NVIDIA's own
   newsroom and each of the six partners' own press pages — genuinely Tier-1 and about
   as high-profile a signal as this class gets. But per SCOPE, an MOU with no capital
   committed and no per-partner allocation is explicitly "at most a candidate" — filed as
   6 candidate rows (one per partner) rather than verified/verified_alpha. Worth
   re-checking in coming weeks for the first platform to actually close.

## Confirmation attempts on other agents' candidates/verified_alpha (no upgrades found)
Tried and failed to find a genuine, openable Tier-1 primary for: NVIDIA/Poolside
(no official PR exists yet — still sourced only to a leaked investor letter via
Newcomer), Microsoft(M12)/Mate Security (no dedicated Microsoft/M12 blog post found),
Apollo/Mexico private-credit target (still "in talks," Bloomberg-only), Blue Owl/Stack
Melbourne loan (still "early-stage talks"), Mubadala/Akita Japan data center (UAE
ambassador confirms only that Mubadala "could" invest — no final commitment), and Form D
searches for Corma, Valar Atomics, Rillet, Etched, CuspAI, Volta AI Infra Holdings (Volta
is a Singapore Pte Ltd, so likely exempt from a US Form D anyway). None of these moved
off their existing status this run — left as-is for the originating agents.

## Discovered allocators
- **NextEra Energy** (corporate) — co-committing with Brookfield on the Paducah campus.
- **Berkshire Hathaway** (alt_manager) — ~$36.6B+ Alphabet stake (a $10B private
  placement in June plus ~$17B added per its Q2 13F); flagged but NOT filed as an event
  since I could not confirm a genuinely openable Tier-1 filing for it this run (the FWP
  URL surfaced in search likely belongs to Alphabet's broader $80B public offering, not
  specifically the Berkshire private placement, and I have no way to verify its content
  under the network constraint).

## Watch next week
- Whether any of the six NVIDIA financing-platform MOUs convert into an actual closed
  vehicle with disclosed capital.
- Whether the CHIPS Act LOIs above convert to definitive/closed awards (historically some
  terms shift between LOI and final agreement).
- Berkshire's Alphabet stake and NextEra's AI-power capex — worth a proper primary-source
  pass once EDGAR access is restored.
