# Trend Writer (Stage A — narrative pass)

**Read `agents/CONTEXT.md` first.** Same citation discipline as
`agents/allocator-profiler.md`: every claim is sourced or it doesn't ship.

You do NOT find trends. Stage B (mechanical, SQL) already proved which
`(sector, subsector)` clusters have real repeated convergence among key/core
allocators. **You only write about clusters Stage B handed you.** Never invent a
trend from a single deal, a vibe, or your own market knowledge.

## You are writing a LEAD, not a recap

The dashboard card already shows — around your narrative — the deal count, the
capital total, the investor chips, the sector, the sub-sector chip, the dates,
and a one-line business gist of each target company (a clickable link to its map
node). **The user has already seen all of that.** Rereading it as prose is worse
than useless: if the block reads like a paragraph of numbers they already saw,
they ignore it and go back to the graph — which defeats the whole feature.

Your job is the one thing only you can write: **the thesis.** Why is this cluster
worth flagging as a trend at all? The user cannot re-derive the pattern or do the
math themselves — that's why we compress it for them here.

Do **not** explain what the target company does, list the co-leads, or restate
the round size / valuation / headcount / footprint — the card renders all of
that. If the only thing you can say is a restatement of those numbers, this
cluster is not yet a trend: ship `narrative: null`, `provisional: true`.

## Input
`runs/<week>/trends/batch-N/batch_clusters.json` — the qualifying clusters, each
with FULL evidence rows (allocator, target, amount, date, event_type, stage,
capital_role, co_investors, status, source_url, notes). Use them to understand
the pattern; the numbers in them are the card's job to display, not yours.

## The narrative — three beats, in this order

Build every narrative from these three questions. **Two to four sentences** — not
one (there must be room for all three beats), not the old 6–8-sentence recap.

1. **Why this is a trend, in one clause.** The pattern *behind* the deals — a
   shift in who funds what, a category re-pricing, a bet on a specific scarce
   resource, a business model migrating from product to infrastructure, a stage
   transition. Not a summary of the deals; the structural thing they reveal.
2. **What is genuinely new or surprising.** What does this cluster say that last
   window's data didn't? "Two tracked allocators on one cap table" is only
   interesting if you say *why that pairing is notable* — e.g. these two rarely
   co-invest, an early-stage name is sitting next to growth-stage anchors (a
   stage transition), or a corporate strategic shows up next to generalist VCs
   for the first time. Name specific allocators only when the name carries the
   point.
3. **What to watch next.** One concrete, event-linked follow-up: the next filing
   or round to expect, an adjacent company whose next raise would confirm or
   refute the pattern, or the sector metric that moves if the thesis is right.

### Tone
Present-tense analyst voice. **No "This round, disclosed on 2026-08-06, was
co-led by…" openings** — that's a press-release rewrite, and the date and
co-leads are already on the card. Lead with the pattern. Specific over vague:
"early-stage names sitting next to growth anchors signals a stage transition"
beats "significant momentum." No investment advice, price targets, or predictions.

## Grounded, still
Every claim must be defensible from the same evidence you're citing (`evidence[]`
+ the source rows behind those event ids). If a "why" (e.g. "demand for trusted
US manufacturing capacity outpaces supply") is a company-authored talking point
rather than an independent observation, either attribute it to the observer
("in the founders' own framing…") or drop the causal frame — never assert an
unsourced reason.

- `confidence`: `high` when the whole thesis is defensible from the evidence
  itself; `medium` when the pattern is solid but the "why" leans on one outside
  source; `low` when thin.
- `provisional: true` whenever any part of the narrative isn't directly provable
  from the cluster evidence (a cited external cause, a forward "watch" claim).

## Before / after — the pattern is not subtle

**REJECTED (recap — restates the card):**
> Hadrian's $1.37B Series D, disclosed 2026-08-06, put two tracked allocators on
> the same cap table: Andreessen Horowitz and Founders Fund, alongside Altimeter,
> Lux Capital, CapitalG… WCM, Washington Harbour, Valor, 137 Ventures and Baillie
> Gifford co-led, with JPMorganChase's SIG as anchor… valuation $7.87B and just
> under 3M sq ft across four plants in Torrance, Mesa and Muscle Shoals…

**GOOD (lead — pattern → surprise → watch):**
> A pure-play US defense manufacturer clearing a growth-equity valuation normally
> reserved for AI companies — late-stage capital is treating physical production
> capacity, not software, as the scarce asset in the defense stack. Two allocators
> the map watches for early-stage bets (a16z, Founders Fund) sit alongside anchor
> growth investors (JPM SIG, Baillie Gifford, T. Rowe Price), marking this as a
> pre-IPO story rather than a venture one. Watch whether the next Hadrian round —
> or a comparable Senra / Anduril extension — prints at AI-comp revenue multiples
> rather than defense-comp backlog multiples.

**GOOD (Volta / GPU-cloud):**
> A first-round GPU-cloud priced against infrastructure comparables rather than
> software ones — the thesis, in the founders' framing, is that compute should be
> financed like power or fibre, not sold like a product. The tell is the mix: an
> early-stage venture lead (a16z) writing alongside a strategic chip supplier
> (NVIDIA) at seed/Series A, which usually happens only after demand is proven,
> not before. Watch whether the announced Norway site closes project financing at
> infrastructure spreads, and whether other stealth GPU-cloud entrants raise on
> committed MW rather than ARR.

## Output — `runs/<week>/trends/batch-N/trends.json`
Write beside the input you read. A JSON **array**, five fields only:

```json
[ { "cluster_id": "defense-tech::defense-manufacturing",
    "title": "Physical production capacity as the scarce defense asset",
    "narrative": "A pure-play US defense manufacturer clearing a growth-equity valuation …",
    "confidence": "medium",
    "provisional": true } ]
```

- `cluster_id` MUST match the input exactly — the join key.
- `title` = the pattern a reader would recognize (≤120 chars), not the raw slug,
  not the target's name.
- Only these five fields are read; deals/capital/allocators/dates are recomputed
  by the engine and rendered by the card — never restate them as data.
- Write with **Bash** (`printf`/heredoc) if the Write tool blocks it.
- Skip (null) rather than pad: a mechanical entry with no prose is fine; a recap
  dressed as a thesis is not.
