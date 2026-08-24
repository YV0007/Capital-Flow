# Alt-Managers — ISO Week 2026-W35 (as of 2026-08-24)

## Headline
The AI buildout's balance sheet took a visible step toward standardization this
week: NVIDIA formalized MOUs with six of our nine tracked allocators (Apollo,
BlackRock, Blackstone, Brookfield, Goldman Sachs, KKR) on August 10 to build
independent "AI Compute Infrastructure Financing Platforms" aiming to mobilize
over $500B of third-party capital — with NVIDIA itself backstopping up to $125B.
No per-firm commitment is disclosed yet, so this is filed once per allocator as
a `fund_launch` with `amount_estimated:1` on the $500B program total, not a close.

## Biggest signals
1. **BlackRock (GIP) + AIP + MGX closed the $40B Aligned Data Centers buyout**
   (July 21) — 100% equity from Macquarie Asset Management, plus a fresh $5B
   growth-capital commitment. AIP's first deal, and one of the largest single
   digital-infrastructure private-market transactions on record.
2. **Brookfield unveiled the Paducah, Kentucky DOE-site AI campus** (July 29)
   with NextEra Energy — a >$100B privately-funded data-center + 4.6GW dedicated
   power project on a former Cold War uranium-enrichment site. Brookfield's CEO
   called it the "seed" of the firm's earlier-announced $100B AI-infra program;
   Brookfield's own equity slice isn't broken out from NextEra's power spend.
3. **KKR closed its largest-ever infrastructure fund**, Global Infrastructure
   Investors V, at $19.2B (Aug 3), already >$9B committed across a mixed
   energy/digital-infra/logistics book (Global Technical Realty, Gulf Data Hub,
   Sempra Infrastructure, FiberCop, Metronet, and others).
4. **SoftBank wrote a clean $200M robotics check** — Series A into Gravis
   Robotics (autonomous excavator retrofits), reportedly the largest
   construction-robotics investment on record, sole investor.

## What didn't clear the bar
- Apollo's $20B Mexico private-credit "target" (July 16) is a stated program
  size with no finalized pipeline or single transaction behind it yet — filed
  as `candidate`, single Bloomberg origin despite wide pickup.
- Blue Owl's Stack Infrastructure is shopping an A$8.5B (~$5.9B) loan for a
  third Melbourne data center — early-stage bank talks, and the capital would
  come from a bank syndicate rather than Blue Owl directly. Filed as a weak
  `candidate`, not counted as a Blue Owl deployment.
- DigitalBridge had no new capital-allocation event this week (Q2 earnings and
  a token dividend only); its pending $4B SoftBank acquisition was announced
  back in December 2025 and remains unclosed.
- Goldman Sachs' new "AlphaAI" investing platform (announced July 30) has no
  disclosed AUM, capital commitment, or fund structure — a product launch, not
  an event under scope.

## Data note
This run had no network access to `data.sec.gov` / `www.sec.gov` (blocked at
the egress proxy for this session — logged in `source_log.csv`), so the
deterministic `engine.edgar` filings path could not be used; all rows here are
sourced via WebSearch against company press/IR pages and Tier-2/3 press, with
Tier-1 company-hosted URLs cited wherever the underlying press release could be
identified. `engine.edgar exists` (local, no network) was used to confirm none
of this week's pairs were already on file.

## Discovered allocator
NextEra Energy — utility self-funding the power side of Brookfield's Paducah
campus; not currently tracked. See `discovered_allocators.csv`.

## Watch next week
- Whether AIP/BlackRock or Apollo/BlackRock name a first concrete platform
  deal under the NVIDIA $500B MOU umbrella (a specific vehicle + first close).
- Apollo Mexico: whether the $20B target firms up into a named fund or first
  transaction.
- Blue Owl Stack Melbourne loan progressing from "seeking" to priced/closed.
- DigitalBridge/SoftBank $4B acquisition closing conditions and timeline.
