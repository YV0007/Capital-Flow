# Corporate strategics — 2026-W46 (week of 2026-11-09)

## What moved
Activity among the six tracked strategics (Microsoft, Amazon, Alphabet, Meta, Oracle,
NVIDIA) was almost entirely one-sided this cycle: NVIDIA was the only name that
*deployed* capital into a new target disclosed in the last ~30 days. The other five
spent October raising their *own* capital (debt and equity) to fund 2026 AI capex,
not allocating it outward — see "Checked and excluded" below.

## Biggest signals
1. **NVIDIA -> Meta, $3B, corporate_investment (verified, Tier 1).** NVIDIA will invest
   $3B into Meta's October 26 equity offering, paired with an expanded Muse-model
   partnership (Vera Rubin GPUs, Vera CPU, Spectrum-X, BlueField-4). Confirmed via
   NVIDIA's own newsroom release. AMD committed $1B to the *same* offering (flagged in
   discovered_allocators.csv — AMD isn't on this watchlist but is now co-investing
   alongside a tracked strategic in hyperscaler raises); Broadcom only expressed
   non-binding interest. NVIDIA's release notes the investment is subject to customary
   closing conditions, so treat as announced-not-yet-closed.
2. **NVIDIA -> 5 UK startups (Boltz, Foresight, Hiverge, Prima Mente, Riverlane),
   minority_stake (upgraded to verified, Tier 1).** These five rows were already on file
   from W45 at verified_alpha, sourced to sifted.eu. This run found NVIDIA's own blog
   post (2026-10-13) independently confirming the same investments at Tier 1 — so these
   get a status upgrade, not new rows (see notes column for merge instructions). No
   dollar amount is disclosed by NVIDIA for any of the five, individually or in
   aggregate. A $1.16B aggregate figure circulates widely (NewsBytesApp) but traces to a
   single uncorroborated source — kept out of amount_usd.
3. **Nothing new from Microsoft, Amazon, Alphabet, or Oracle as allocators.** Every 8-K
   each filed in the window (Oct 13 – Nov 9) was checked: all were debt/equity capital
   raises, earnings 8-Ks, an investor-day FD disclosure, a segment recast, or a director
   departure — not capital deployed into a target. Broad web search for each name
   (minority stakes, corporate-VC vehicles, AI-startup checks) surfaced only deals from
   outside the window (e.g. Amazon-Anthropic Series H, Amazon-OpenAI $50B, Google-
   Anthropic $40B, Microsoft/Nvidia-Anthropic $15B — all Jan–May 2026, already old news
   by this run's forward-search window and not re-filed).

## Checked and excluded (documented, not silently dropped)
- **Alphabet / Google <-> Constellation Energy nuclear PPA (announced 2026-10-06).**
  Reported as a "$4.3B deal," but that capital is Constellation's own investment to
  uprate 11 reactors it already owns — Alphabet is the power *off-taker* under a
  20-year PPA, not the capital allocator. No Alphabet spend is disclosed. Excluded as
  out of scope per CONTEXT.md (partnership/commercial contract with no capital
  committed by the allocator), not filed as a candidate.
- Five Microsoft, Meta, Oracle, Alphabet, Amazon 8-Ks dated 2026-10-21 through 2026-11-05
  were individually opened and read in full (see source_log.csv) — all capital *raises*
  (notes, mandatory convertible preferred, common stock, forward sales) or disclosure-
  only items (earnings, investor day, segment recast, director departure). None describe
  the filer deploying capital into a target, so none qualify as events for this class.

## Watch next week
- Whether NVIDIA's $3B Meta investment and the five UK stakes actually close (both are
  still "planned"/"subject to closing conditions" as of 2026-11-09).
- Whether AMD's $1B Meta commitment and Broadcom's non-binding interest firm up —
  AMD is now a repeat co-investor alongside tracked corporates and is a reasonable
  watchlist-promotion candidate.
- Microsoft, Amazon, Alphabet and Oracle all just raised large amounts of fresh capital
  (debt + equity, ~$10-25B each) in late October/early November — worth watching for
  where that capital gets deployed outward in the next few weeks.
