# Individuals — ISO Week 2026-W33 (personal capital; ~45-day lookback to ~2026-06-26)

## Headline
This was a thin week for genuinely new personal-capital signal, but it produced one big one:
**Jeff Bezos personally put $2 billion into Blue Origin's first-ever outside funding round**
(announced 2026-07-08, $10B raised at a $130B valuation, Coatue Management leading with $4B).
This is the single largest personal check found for any watchlist individual this window, it
roughly doubles Bezos's historical annual funding pace to his own company, and it was **missed
by last week's (W32) run entirely** — it reads as an aerospace financing story, not an "AI
funding round," so a pure AI-angel-list sweep walked past it. Finding it is this week's main
contribution. Beyond that, an exhaustive sweep of the ~40-name watchlist plus the tracked
networks turned up almost nothing else genuinely new in-window; most trails led back to stories
W32 already filed (Etched, Odyssey, Monogram, SkillBench, Prentis, CuspAI, General Intuition,
GPx TX LP) with no material update.

## Counts
- **verified: 0**
- **verified_alpha: 1** — Jeff Bezos x Blue Origin ($2B personal, $10B round, $130B valuation).
- **candidate: 1** — Jeff Bezos x Generalist AI (Bloomberg 2026-08-04 "boosted its allocation,"
  but single-origin and ambiguous vs. the June round already on file).
- **discovered allocators: 1** — Coatue Management (led the Blue Origin round at $4B).
- **sources logged: 60**, of which 2 yielded events and the rest logged as checked-but-empty
  (the honest shape of this class per the brief: it is supposed to look this way).

## Biggest signals
1. **Bezos / Blue Origin, $2B personal ($10B round, $130B valuation, 2026-07-08).** Blue
   Origin's 26-year run funded exclusively out of Bezos's own pocket (~$30B cumulative, ~$1B/yr)
   just opened to outside capital for the first time, with Coatue Management leading a $4B slice
   and Bezos backstopping with $2B to hold his core equity position. Confirmed same-day by CNBC
   and Bloomberg independently, corroborated by Forbes/TechCrunch/Yahoo, with Blue Origin CEO
   Dave Limp's internal staff memo quoted by press (company-side confirmation, but via a leaked
   memo rather than an official newsroom PR — kept at verified_alpha/Tier-3, not verified). No
   canonical sector fits an orbital-launch company; recorded under `defense-tech` (closest,
   via Blue Origin's National Security Space Launch certification) with `theme=space` carrying
   the more honest structural read. This is the biggest single personal-capital number seen for
   any individual across this run and last week's combined.
2. **Bezos Expeditions remains the most active personal allocator on the entire watchlist by a
   wide margin.** Between the W32 filing (LifeMine, CuspAI, General Intuition) and this week's
   Blue Origin find, Bezos personally is now attached to five figures in eight weeks; trade press
   independently pegs Bezos Expeditions as the most active family office of 2026 with "eight
   direct investments" year to date, of which only five-to-six are named in any single source.
3. **The counter-signal, again:** a fresh EDGAR-style sweep for Form D related-persons across
   the remaining ~38 watchlist names (Sam Altman, Marc Andreessen, Vinod Khosla, Josh Kushner,
   Brad Gerstner, Alexandr Wang, Dylan Field, Bill Gurley, Neil Mehta, Philippe Laffont, Joe
   Lonsdale, Keith Rabois, Austin Russell, Laura Deming, Masayoshi Son, Larry Ellison, and the
   PayPal Mafia / Thiel-extended network names) returned **zero** new sourceable personal checks
   in-window. That is the expected shape of this class, not a coverage gap — see Class gotchas
   in the brief.

## Network coinvestment flags
None found this week. Blue Origin's round is Bezos (unaffiliated with any tracked network) plus
Coatue (a firm, not a tracked individual) — no 2+ tracked-network-member overlap to report. The
Etched (Thiel + Dylan Field) and Khosla Ventures MM SPV (Khosla + Rabois) convergences filed by
W32 remain the most recent network-relevant signals; no new corroboration or contradiction
surfaced for either this week.

## A significant environment limitation this run
Direct EDGAR access (both `curl` to `efts.sec.gov`/`www.sec.gov` and `WebFetch` to `sec.gov`)
was **blocked at the network egress layer** in this session (`connect_rejected`, gateway 403),
along with WebFetch to a long list of other domains (techcrunch.com, bloomberg.com, reuters.com,
news.crunchbase.com, techstartups.com, fool.com, en.wikipedia.org). This meant **no direct
Form D related-person lookups were possible this week** — the primary Tier-1 confirm path this
class relies on most (per the brief, step 2 of the search order) was unavailable. All grading
this week rests on WebSearch-returned snippets/quotes rather than full-page WebFetch review or
raw EDGAR full-text search. This is a meaningful blind spot: several W32 candidates that were
one Form D check away from upgrading (SkillBench/Hoffman, GPx TX LP/Thiel) could not be
re-checked, and the Blue Origin finding itself could not be cross-checked against EDGAR for a
financing-vehicle Form D that might upgrade it from verified_alpha to verified. Flagging this
explicitly rather than silently under-covering the Tier-1 layer.

## Watch next week
1. **Blue Origin financing vehicle** — check EDGAR (once egress is available) for a Form D tied
   to the $10B raise; a related-persons listing naming Bezos would upgrade this to verified.
2. **SkillBench** — still unresolved from W32: chase a public round announcement or amended
   Form D that separates Reid Hoffman's personal position from Greylock's.
3. **Q2-2026 13Fs, due 2026-08-14** — four days after this run closed; the first real chance to
   test the Druckenmiller/Etched candidate and to pick up Ackman, Tepper and Dalio, all silent
   again this window.
4. **Bezos's other ~2-3 undisclosed 2026 direct investments** — trade press pegs Bezos Expeditions
   at "eight direct investments" YTD 2026 but only five-to-six are named in any source found;
   worth another pass once more of them surface.
5. **Re-run the EDGAR-dependent legs of this brief** (Form D related-persons for the full
   watchlist) once sec.gov egress is restored — this week's sweep was WebSearch-only for that
   layer and is the weakest part of this run's coverage.
