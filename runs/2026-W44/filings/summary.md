# Filings agent -- 2026-W44

## Environment note
Direct fetches to data.sec.gov / sec.gov (and, it turned out, to other primary
domains like inl.gov and investors.x-energy.com) were blocked in this sandbox
for both `engine.edgar` and WebFetch (confirmed: `engine.edgar filings NVIDIA`
hit a 403 at the egress proxy; WebFetch returned `ENOTFOUND` for every
.gov/.sec.gov/IR host tried). All confirmations below rest on WebSearch, which
resolves server-side, cross-checked across multiple independent queries where
a single search snippet wasn't conclusive on its own.

## Confirmed / upgraded this week: 1

**Goldman Sachs -> Digi Power X, $200M Columbiana AL data-center debt commitment**
(alt-managers' 2026-W44 verified_alpha row). The alt-managers agent had already
found this at source_tier 1 via a PR newswire (via.tt.se) copy of the Oct 13
2026 release. The same release is also filed as Exhibit 99.1 to Digi Power X's
own Form 8-K on EDGAR (CIK 0001854368); three independent WebSearch queries all
surfaced the identical URL
(`sec.gov/Archives/edgar/data/0001854368/000121390026089450/ea030173001ex99-1.htm`)
tied to that exact content, which is as close to a direct EDGAR confirm as this
sandbox allows. Re-emitted as `status=verified`, `source_tier=1`, pointing at
the SEC exhibit instead of the newswire. Terms unchanged -- still a commitment
letter, not a closed loan.

## Chased but could NOT confirm (left alone, not re-filed)

- **NVIDIA -> Pigment / Entalpic** (corporate verified_alpha, Paris minority
  stakes). No SEC filing exists or would be expected -- both targets are
  private French companies, and press coverage says Nvidia hasn't even
  finalized or disclosed terms. No non-US registry document found either.
- **Amazon -> Grand Ming Group Holdings (HK data centers)** (corporate
  verified_alpha). Confirmed the underlying HKEX disclosure happened (Sept 18
  2026, per a brokerage summary matching the corporate agent's numbers almost
  exactly), but could not resolve the actual hkexnews.hk announcement URL
  through WebSearch -- only secondary aggregator pages (itiger.com,
  mingtiandi.com) came back. Left the row alone rather than cite a
  non-primary summary as Tier 1.
- **MGX -> Databricks, $5B round** (sovereigns, filed as status=verified /
  source_tier=3 -- effectively a verified_alpha in substance despite the
  label). Databricks did file a real SEC Form D for this round on/around Aug
  27 2026 (per a third-party Form D tracker that quotes exact filing figures:
  $4,999,997,255 sold to 136 investors under Rule 506(c)) -- but a Form D by
  design does not disclose purchaser identities, valuation, or use of
  proceeds, so even if resolved it could not confirm MGX's specific
  participation. No resolved sec.gov accession URL for the 2026 filing turned
  up despite several targeted searches (only 2021/2023 Form Ds for Databricks'
  CIK 0001587468 resolved). MGX has no SEC filing obligation as a foreign SWF.
  Left the row alone -- the existing WAM/UAE state-news corroboration already
  in its notes is the best available, and it isn't a registry document.
- **Blue Owl/Stack Infrastructure -> Melbourne A$8.6B loan** (alt-managers
  candidate). Still at the "mandated lead arrangers" stage as of Oct 15 2026
  reporting -- no close, no company filing or PR beyond what's already cited.
- **Apollo -> SpaceX, ~$40B debt financing** (alt-managers candidate). Still
  an unconfirmed FT-origin report; SpaceX, Apollo and PIMCO have not
  commented; no filing exists since SpaceX is private and nothing has closed.
- **MGX -> DayOne**, **Mubadala -> Akita data center**, **Saudi PIF/HUMAIN ->
  data centers + GPUs** (all sovereigns candidates). Re-checked for an October
  update; all three are still at the "considering / early-stage talks /
  declined to comment" stage reported originally -- no new development, no
  capital committed, nothing to confirm.

## New filings-only find: 1 (also corrects an existing candidate)

**US Government (DOE Genesis Mission) -> Idaho National Laboratory-led
"Project Prometheus", $60M grant, 2026-07-22.** While chasing the sovereigns
candidate "US Government -> Oklo/X-Energy, $200M, Genesis Mission" (itself
flagged by the sovereigns agent as having an unconfirmed participant list),
I went to the primary sources directly: INL's own July 22 2026 press release
and X-Energy's own IR release the same day. Both agree on a $60M, 3-year DOE
Phase II grant (subject to appropriations) to a 32-partner INL-led AI-for-
nuclear-fuel-qualification consortium, with X-Energy as the named Tier-1
industry partner (board seat, $10M private capital, Xe-100/TRISO-X as the
technical platform) alongside NVIDIA and AWS. Neither primary release names
Oklo or Microsoft. INL's release separately mentions the broader Genesis
Mission effort has raised ">$200M in industry cost-share" -- a non-federal,
non-grant figure that looks like the likely source of the $200M number in the
Bloomberg-origin report the sovereigns agent relied on. Filed as its own
verified row (not a re-file of the candidate, since the amount, target framing
and participant list all differ from what's on file) with a note recommending
the sovereigns agent drop or correct that candidate next week rather than
re-escalate the $200M/Oklo framing.

Also flagged **X-Energy** in `discovered_allocators.csv` as a corporate
allocator worth tracking -- it's deploying its own $10M of private capital
into this consortium, not just receiving grant money.

## Broader filings-only sweep (8-K / Form D / 13D/G, last ~30 days)

Searched broadly across the canonical sectors (SoftBank, Brookfield,
DigitalBridge, Blackstone, plus generic "Form D AI data center October 2026"
and "13D/13G AI chip October 2026" queries) for anything the five class
agents missed. Nothing new and in-scope turned up:
- SoftBank's Oct 1 2026 $10B third-tranche OpenAI follow-on (via SBVF2) is
  real and Tier-1-sourced, but it's already on file as `verified` in
  alt-managers' output -- no action needed.
- The Brookfield/DigitalBridge "Compass Datacenters" bidding war that surfaced
  is a 2023 deal (Brookfield + Ontario Teachers won), not a 2026-W44 event.
- A handful of October 2026 8-Ks turned up for smaller-cap names (AIB Data
  Centers/Nebius capacity deal, PowerCompute's Mississippi power contract,
  Solaris Energy Infrastructure) -- these are customer/capacity agreements,
  not capital allocation by a tracked allocator class into a target, so they
  don't fit SCOPE and weren't filed.
- No October 2026 13D/13G on AI-chip or data-center names surfaced beyond
  NVIDIA's already-old (July 2026) Nebius 13G.

## Counts
- `verified_events.csv`: 2 rows (1 confirm/upgrade of an existing alt-managers
  row; 1 new independent filings find that also corrects a sovereigns
  candidate).
- `candidate_events.csv`: 0 rows (header only) -- everything found this run
  cleared to Tier-1/verified or didn't clear at all.
- `discovered_allocators.csv`: 1 row (X-Energy).

## Watch next week
- Digi Power X's $200M Columbiana commitment is due to close within ~90 days
  of Oct 13 -- worth a Tier-1 recheck for the actual closing 8-K around
  mid-January 2027.
- If this sandbox's SEC/.gov network restriction lifts, re-run the Databricks
  CIK 0001587468 Form D lookup directly -- the 2026 filing almost certainly
  exists (secondary trackers quote it precisely) but I could not resolve its
  accession number this week.
- Sovereigns agent: recommend swapping the Oklo/X-Energy $200M candidate for
  the corrected $60M Project Prometheus figures from this run, or dropping it.
