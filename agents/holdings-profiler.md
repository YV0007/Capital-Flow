# Holdings Profiler — a fund's PORTFOLIO (the companies it deploys into)

You research a BATCH of funds/firms and collect the companies each one backs —
the layer BELOW the Capital Flow map. The map shows LP money flowing INTO a fund
vehicle; this shows where that fund then deploys it. Users drill in here to follow
smart money to the exact companies and bets.

Read `agents/CONTEXT.md` for the source-tier ladder. Your batch input file
(`batch_entities.json`, in your batch directory) lists each entity with its kind
(`firm` = the manager, e.g. Andreessen Horowitz; `vehicle` = a specific fund,
e.g. Coatue Growth Fund VI), its `parent_hint`, capital, and deal URLs. For a
`vehicle` whose own holdings aren't disclosed, cross-reference its PARENT manager's
portfolio (a feeder fund deploys into the manager's deals).

## Output contract

Write `holdings.json` into your batch directory: a JSON **array**, one object per
entity, exactly this shape:

```json
{
  "entity": "Andreessen Horowitz",          // EXACT entity string from batch_entities.json
  "portfolio_url": "https://a16z.com/portfolio/",  // DIRECT link to the portfolio LISTING, not the homepage
  "holdings_count": 42,                       // TRUE total known holdings (may exceed the array below)
  "as_of": "2026-08-10",
  "holdings": [
    {
      "name": "Whatnot",                      // portfolio company (REQUIRED)
      "sector": "ai-applications",            // your canonical sector slug (config/rules.yaml)
      "subsector": "live-commerce-marketplace", // per-deal subsector slug (optional)
      "note": "Live shopping marketplace for collectibles and fashion.", // <=120 chars: what it IS
      "stake": null,                          // '12%' or '$50M' if disclosed, else null
      "lead": false,                          // did the fund LEAD the round?
      "as_of": "2026-08-10",
      "source_url": "https://..."             // where THIS holding is sourced (REQUIRED)
    }
  ]
}
```

## What counts as a HOLDING

"Holding" means **an equity stake the fund still owns.** The panel exists so a
reader can follow conviction — what this fund owns and believes in right now. A
list that mixes in things it used to own, lent to, or merely announced answers a
different question and quietly makes the whole block untrustworthy.

**Include:**
- an equity stake the fund still holds, public or private
- a stake still held THROUGH an IPO — going public does not end ownership
- a stake whose size was never disclosed → keep it, with `stake: null`

**Exclude:**
- **realised exits** — the company IPO'd or was acquired and the fund SOLD. That
  is history, not a holding.
- **LP commitments into another fund** — an allocation, not a portfolio company,
  and it is already on the map as a flow. Putting it here double-counts it.
- **debt, credit facilities and venture-debt lines** — a lender is not an owner.
- **announced-but-unclosed deals** — "in talks to invest" is not a holding.
- **SPV participation where the fund is a pass-through** rather than the owner.

## Rules — same zero-fabrication discipline as the rest of the engine

- **Every holding needs a `source_url`.** No source → do not emit that holding
  (the audit gate treats an unsourced holding as a violation).
- **`portfolio_url`** = the actual portfolio listing (`.../portfolio/`, a
  fund-filtered view, or an SEC/registry page that enumerates positions). NOT the
  marketing homepage. Deep-link/filter to the specific fund when the site allows.
  If no portfolio page exists, omit the field.
- **Rank most-notable / largest-stake first** (array order = rank). The UI shows
  top 5, then top 25, then all — ship **at least the top 25** per entity; more is
  better. The ingest now ENFORCES this floor: a portfolio that comes back under 25
  while its own `holdings_count` says more exist is recorded as an under-delivery
  and the entity is re-queued on the next run.
- **For a portfolio too large to enumerate, relevance beats completeness.** a16z
  has ~1,458 holdings; nobody wants all of them, and 49 arbitrary ones are worse
  than 50 chosen ones. Rank first by relevance to THIS map — the sectors in your
  batch input's `rank_by` field: AI, semiconductors, infrastructure, energy,
  data — then by stake size and notability. `holdings_count` stays the true total
  so the UI can honestly say "top 50 of 1458".
- **`holdings_count`** is the true total even if you cap the array (UI shows
  "top 25 of 42"). If you truly listed them all, it equals the array length.
- **`sector`/`subsector`** must match the canonical taxonomy in `config/rules.yaml`
  so the dashboard can color/group them.
- **If a holding is also a tracked entity on the map**, keep `name` byte-identical
  to that node's label so the dashboard links the row straight through. (Skim the
  targets you know are on the map; when unsure, use the company's common name.)
- `note` ≤120 chars, factual — what the company IS, no hype.

## Where to source (public only)
- **SEC EDGAR** — Form ADV / Form D (the fund's own filings).
- **Not 13F.** Form 13F covers US-listed equity only. A venture manager's book —
  OpenAI, Stripe, SpaceX, Anthropic — appears in no 13F, ever, so pointing one at
  Thrive or Sequoia returns nothing and reads as a bug. The engine already pulls
  13F separately for the firms that file one, and attaches it as a SECOND book
  (`public_book`) that is never merged into this one.
- **Fund website portfolio pages**, press releases, the fund's own announcements.
- Cross-reference the **parent manager** for feeder/vehicle entities.

## Operating loop
1. For each entity: find its portfolio page + primary filings. Pull the companies.
2. For each holding, capture the source that names THAT position; map its sector.
3. Rank; set `holdings_count` to the true total; write `holdings.json`.
4. Double-check: every holding has a `source_url`; `portfolio_url` is a listing,
   not a homepage; sectors are canonical; array is ranked, ≥25 where available.
