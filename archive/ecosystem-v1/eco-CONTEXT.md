# Ecosystem Agent Operating Context (shared)

Every **monthly** ecosystem agent reads this file first, then its own brief
(`agents/eco-*.md`), then `config/eco_layers.yaml` + `config/eco_watchlist.yaml` +
`config/eco_rules.yaml`.

This is the twin of `agents/CONTEXT.md`, which drives the **weekly** capital-flow
pipeline. Do not mix them up:

| | Weekly (`agents/CONTEXT.md`) | Monthly (this file) |
|---|---|---|
| Unit | A capital-allocation **event**, dated | A **standing dependency**, undated |
| Question | Where did money go this week | How is the industry built, who holds it |
| Output | `verified_events.csv` | `edges.csv` + `nodes.csv` |
| Cadence | Weekly | Monthly |

Entity identity is **shared** between the two. NVIDIA is one NVIDIA. Names resolve
through `config/aliases.yaml` — use the canonical name there when one exists.

## Mission
Build the map of how the AI / datacenter industry is actually assembled: who supplies
whom, who owns the bottleneck, who cannot be replaced. The map's value is that every
single line on it traces back to a document a human can open. A plausible-sounding
dependency with no citation is worse than a missing one — it is a lie the map tells
confidently.

## What an EDGE is
A **standing structural dependency between two companies**, direction always up the
stack (supplier → consumer). Not a news item, not a deal announcement, not a date.

> NOT an edge: "NVIDIA and X announced a strategic collaboration to explore…" —
> exploration is not a dependency. "X is expected to supply…" — expectation is not a
> dependency. "Analysts believe X relies on Y" — belief is not a dependency.

### The ten types
| type | spine | meaning | example |
|---|---|---|---|
| `supply` | physical | critical physical input | SK Hynix → NVIDIA (HBM) |
| `offtake` | physical | capacity purchase, sole-source contract | OpenAI → Oracle |
| `platform` | physical | IP / software / standard inside someone else's product | Arm → SoCs |
| `partner` | physical | JV, co-design | NVIDIA ↔ Foxconn |
| `compete` | physical | **NOT COLLECTED IN v1** — a judgement, not a fact from a release |
| `owns` | capital | control through ownership | Brookfield → Westinghouse |
| `stake` | capital | position without control | NVIDIA → OpenAI |
| `finances` | capital | project finance, JV funding | Brookfield ↔ an Intel fab |
| `develops` | capital | develops the asset | Brookfield → Compass, Data4 |
| `operates` | capital | operates someone else's asset | a DC operator |

### `strength` 0–100 — materiality **FOR THE RECEIVER**
Not size, not revenue, not importance in the abstract. "If this went away tomorrow, how
badly is the *target* hurt?"

- **90–100** sole source, no substitute inside a year (ASML → TSMC).
- **70–89** dominant source; a substitute exists but is worse or slower.
- **40–69** material but second-sourced.
- **20–39** real but replaceable.
- **0–19** marginal. Still write it — the DB keeps everything; the map's default
  threshold is 20 and the slider goes to 0.

## Roles
| role | who |
|---|---|
| `producer` | makes the thing — most of the DC-AI coverage |
| `owner` | owns / operates the asset — Equinix, Digital Realty, Constellation |
| `capital` | capital that **creates** assets — Brookfield, Blackstone, KKR, MGX |
| `demand` | end demand — hyperscalers as buyers, labs |
| `platform` | tech node holder — CUDA, EUV, CoWoS |

`capital` and `owner` nodes sit in the layer where the **controlled asset** stands, never
in a layer of their own.

## The 12 layers — FROZEN
Full table with sectors and dc_node ids: `config/eco_layers.yaml`. Short form:

| id | label | what |
|---|---|---|
| L1 | СЫРЬЁ | materials, chemistry |
| L2 | ОБОРУДОВАНИЕ | tools, EDA, test |
| L3 | ЧИПЫ | logic, power, custom — **foundries live here** |
| L4 | ПАМЯТЬ | HBM, DRAM, NAND |
| L5 | СБОРКА | advanced packaging, PCB |
| L6 | ГЕНЕРАЦИЯ | nuclear, SMR, gas, renewables |
| L7 | ПЕРЕДАЧА ТОКА | grid → rack |
| L8 | СВЯЗЬ | photonics, network silicon, optics, fiber |
| L9 | СИСТЕМЫ | servers, cooling, MEP, construction |
| L10 | ВЫЧИСЛЕНИЯ | **clouds, neoclouds, DC REITs** |
| L11 | ИНФЕРЕНС | serving, orchestration software |
| L12 | РЕЗУЛЬТАТ | frontier labs, AI for business |

A company in several layers is **one node with several layers**, never two nodes.
Write it as `L3:primary|L10|L12`.

## Source tiers — FROZEN
| tier | what counts |
|---|---|
| `filing` | 10-K / 20-F / 8-K / prospectus / 13D-G / S-1 |
| `company_pr` | press release from one of the two parties |
| `transcript` | a statement on an earnings call |
| `press` | Reuters / Bloomberg / FT / WSJ |
| `estimate` | TrendForce / Omdia / SemiAnalysis market-share work — **share numbers only** |

`estimate` is admissible for a *share* claim (it feeds `f_share`), never as the sole
proof that a relationship exists.

Two independent evidence rows → solid line on the map. One → dashed, whatever the tier.
So: **when you have a second source, write a second row.** That is the cheapest quality
gain in the whole pipeline.

## THE IRON RULE — no verbatim quote, no edge
Every edge row carries `evidence_quote`: a **verbatim** sentence from the source in which
the relationship is stated. Copy it; do not paraphrase, do not stitch two fragments
together, do not translate it.

- The quote must name the relationship. "NVIDIA is a leader in AI" does not prove
  NVIDIA→anything.
- The quote must be findable on the page at `source_url`. `eco_verify.py` re-fetches
  every URL monthly and looks for the quote; if it is gone, the edge is marked
  `unverified` and dims on the map. A stitched or reworded quote fails this check and
  makes the edge look dead — so quoting sloppily costs you the edge later.
- `source_url` must be a **resolved document**, never a search query. An EDGAR full-text
  search URL (`efts.sec.gov/...`, `sec.gov/edgar/search?q=...`) is rejected at ingest.
- Judgement phrasing is banned: "probably supplies", "is believed to", "industry sources
  suggest". If that is all you have, do not write the row.

## What to actually go read
1. **10-K / 20-F** — supplier and customer concentration ("customer A accounted for X% of
   net revenue"), single-source dependency, supply-chain risk factors. This is the richest
   vein on the whole map and it is free.
2. **8-K / prospectuses / 13D-G / S-1** — ownership, stakes, JVs, project finance.
3. **Company press releases from either side** — contracts, capacity purchases, co-design,
   volumes, terms. The counterparty often discloses what the principal will not.
4. **Earnings-call transcripts** — the dependency admitted in management's own words.
5. **TrendForce / Omdia / SemiAnalysis** — market share, and only as `estimate`.

Useful deterministic path (already in the repo):
```bash
python -m engine.edgar cik "Vertiv"        # CIK, or null = take the search path
python -m engine.edgar filings NVIDIA --forms 10-K,8-K --since 2025-01-01
```

## Criticality — you supply four numbers, the engine does the arithmetic
Never write a criticality score. Write the four factors (0–5) and a **sourced**
`share_note`. `eco_score.py` computes the score; the node panel then shows *why* it is 98.

| factor | column | 5 | 4 | 3 | 2 | 1 | 0 |
|---|---|---|---|---|---|---|---|
| Share of its function | `f_share` | >90% | 70–90% | 50–70% | 30–50% | 15–30% | <15% |
| Real alternatives | `f_alternatives` | none | one | two | three-four | many | commodity |
| Time to replace | `f_switch_time` | >5y | 3–5y | 1–3y | 6–12m | <6m | instant |
| Barrier to entry | `f_barrier` | prohibitive | very high | high | medium | low | none |

Sanity check: ASML 5/5/5/5 → 100. A commodity ODM assembler 2/1/1/1 → 26. If your
factors give a no-name vendor a 90, they are wrong.

## Who gets on the map — R1–R5 (at least one)
- **R1** top-3 by share of its function.
- **R2** sole / near-sole supplier of a critical input (criticality ≥ 70).
- **R3** a **named** counterparty in a contract or partnership with an anchor.
- **R4** an emerging name with a **signed** contract or design win — not a promising idea.
- **R5** controls a bottleneck **through ownership or financing**.

## Output contract — write into `runs/<YYYY-MM>/<agent>/`

**edges.csv** — this exact header:
```
source,target,edge_type,spine,strength,tech_node,started,evidence_quote,source_url,source_tier,published_date,note
```
- `source` / `target` — company names (canonical where `config/aliases.yaml` has one).
  The engine slugifies and resolves them; you write human names.
- `edge_type` — one of the ten (never `compete` in v1).
- `spine` — `physical` for supply/offtake/platform/partner; `capital` for
  owns/stake/finances/develops/operates. The engine enforces the pairing.
- `strength` — 0–100 per the scale above.
- `tech_node` — a slug from `config/eco_layers.yaml` (`euv`, `cuda`, `cowos`, `hbm`,
  `nvlink`, `infiniband`, `arm-isa`, `ap1000`) or blank.
- `started` — year or ISO date when the relationship began; blank if unknown.
- `evidence_quote` — VERBATIM. Quote commas are fine, the file is proper CSV.
- `source_url` — resolved document.
- `source_tier` — `filing|company_pr|transcript|press|estimate`.
- `published_date` — ISO date of the document.
- `note` — one line of context that a reader would want on the edge label.

**Two sources for one edge = two rows** with the same source/target/edge_type and
different `source_url` + `evidence_quote`. The engine merges them into one edge with two
evidence rows. This is how you turn a dashed line solid.

**nodes.csv** — this exact header:
```
name,layers,sector,role,tier,ticker,public_private,geo,f_share,f_alternatives,f_switch_time,f_barrier,share_note,one_liner,what_breaks_it,dc_node
```
- `layers` — `L3:primary|L10|L12`. Exactly one `:primary`.
- `sector` — a `key` from `config/eco_layers.yaml` (must belong to one of the node's layers).
- `role` — producer|owner|capital|demand|platform.
- `tier` — anchor|core|emerging.
- `public_private` — `Pub` / `Pvt`. `ticker` in the `AMS: ASML` / `NASDAQ: NVDA` style
  used by `dc-companies.json`.
- `share_note` — the sourced sentence behind `f_share`. Cite the number.
- `one_liner` — what this company IS, in one sentence, no marketing.
- `what_breaks_it` — the single event that would end the position. This is the most useful
  field in the node panel; do not leave it blank on anchors.
- `dc_node` — the Roadmap.jsx node id for its sector (see `config/eco_layers.yaml`), so the
  node links back into the DC-AI thesis. Blank if none fits.

**source_log.csv** — `source_url,source_tier,yielded` — every source you actually opened,
including the ones that yielded nothing. Same contract as the weekly agents.

**summary.md** — a short narrative: what the layer looks like this month, the 2–3 real
bottlenecks you found, what changed, what you could not confirm and why.
> Write `summary.md` with **Bash** (`printf` / heredoc), NOT the Write tool — the agent
> Write tool blocks report-style markdown and will fail an unattended run. CSVs are fine
> via Write.

## Read the rejects before you start
`runs/<previous-month>/rejects.csv` holds every row the engine refused, with the reason.
Those rows came back to you for a reason — fix or drop them, don't re-file them unchanged.

## Recurring mistakes — worked examples
**1. Paraphrased quote (kills the edge on next month's verify).**
- REJECTED: `evidence_quote = "TSMC makes almost all of NVIDIA's chips"` — not on the page.
- GOOD: the sentence as printed, e.g. a 10-K's own wording about outsourcing all
  manufacturing to third-party foundries.

**2. A deal announcement filed as a dependency.**
- REJECTED: `partner` edge from "the two companies announced an intent to collaborate".
- GOOD: wait for the contract, the design win or the shipped product; or write it with
  `strength` low and the caveat in `note` — but only if the quote states a real relationship.

**3. The same company entered twice for two layers.**
- REJECTED: `Alphabet (TPU)` and `Alphabet (Cloud)` as two rows in nodes.csv.
- GOOD: one row, `layers = L3|L10:primary|L12`.

**4. `estimate` used to prove a relationship exists.**
- REJECTED: an `offtake` edge whose only source is a TrendForce share table.
- GOOD: `estimate` supports `f_share` / `share_note`. The relationship itself needs a
  filing, a PR, a transcript or the press.

**5. Direction inverted.**
- REJECTED: `NVIDIA → SK Hynix` as `supply`. NVIDIA does not supply HBM to SK Hynix.
- GOOD: `SK Hynix → NVIDIA`, `supply`. Direction is supplier → consumer, always up the stack.

## Operating loop
1. Read this file, your brief, `config/eco_layers.yaml`, your slice of
   `config/eco_watchlist.yaml`, and last month's `rejects.csv`.
2. For each name in your slice: pull its latest annual report and read the concentration
   and risk-factor sections FIRST. That is where the map's spine comes from.
3. For every dependency you find, get the verbatim sentence and the resolved URL. Then go
   find a **second** independent source for the important ones.
4. Fill the four criticality factors from what you read, with the share number cited.
5. Write the four files. Deduping, entity resolution, scoring, cycles and the map file are
   the engine's job — yours is coverage and truth.
