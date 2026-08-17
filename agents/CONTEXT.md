# Agent Operating Context (shared)

Every research agent reads this file first. It defines the mission, what counts
as an event, the exact output contract, and the vocabularies. Class-specific
briefs (corporate.md, vc.md, …) add only what's unique to that class.

## Mission
Discover real capital allocation before consensus. Track where elite allocators
move money, so private flows can later be mapped to public beneficiaries. This
is an intelligence platform, not a news feed — a headline is a lead, not an event.

## What counts as an event (SCOPE)
Record ONLY capital allocation — money committed or deployed. The event_type must
be one of:

| event_type            | meaning                                             |
|-----------------------|-----------------------------------------------------|
| equity                | cash for ownership (not a priced round)             |
| funding_round         | a priced venture/growth round                       |
| follow_on             | additional capital into an existing position        |
| acquisition           | buying control of a company or asset                |
| minority_stake        | non-control stake                                   |
| fund_launch           | a new fund/vehicle raised (amount = fund size)      |
| spv                   | special-purpose vehicle for a specific deal         |
| grant                 | non-dilutive government/foundation money            |
| project_finance       | debt/structured finance for a physical build        |
| corporate_investment  | a corporate deploying balance-sheet capital         |
| sovereign_investment  | a state / SWF deploying capital                     |

NOT events: product launches, hires, opinions, MOUs with no money, revenue,
guidance, partnerships with no capital committed. If no capital moved or was
firmly committed, it is at most a `candidate`.

## Canonical sectors — map every event to exactly one
`ai-labs`, `ai-compute`, `semiconductors`, `fab-equipment`, `cloud-hyperscale`,
`neocloud`, `datacenters`, `power-energy`, `nuclear`, `networking`, `robotics`,
`defense-tech`. (Full definitions in config/rules.yaml.) If nothing fits, use the
closest and note it — an unknown sector ingests but is flagged.

## Sources & tiers (see config/sources.yaml)
- **Tier 1** SEC/EDGAR, company IR, official PRs, portfolio pages, government DBs — *confirms*.
- **Tier 2** PitchBook, Preqin, Crunchbase, Dealroom, Capital IQ, Bloomberg, Harmonic.
- **Tier 3** Reuters, FT, WSJ, Bloomberg News, The Information.
- **Tier 4** SemiAnalysis, Stratechery, conference talks.
- **Tier 5** podcasts, YouTube, X, LinkedIn, blogs — *discovers leads only*.

Use WebSearch / WebFetch for all tiers. SEC EDGAR full-text search is free and is
your best Tier-1 confirm. Tier 5 finds the lead; a higher tier must confirm it.

## Read your context pack FIRST — `runs/<week>/<your-agent>/context.json`
Built before every run from what the engine already knows. Three sections:
- **what_you_already_have** — per entity: `last_event_date` (search FORWARD from it,
  don't re-find old deals), `sectors_active`, `known_vehicles`, `aliases` (the SAME
  entity — never file one as new), `cik`/`edgar_path`, `recent_targets`. Plus
  `stale_candidates`: existing rows needing a Tier-1 confirm — chase these first,
  don't re-file them as new deals.
- **what_worked** — `check_first`: sources that actually yielded events in recent
  runs. Check them before searching broadly.
- **what_you_got_wrong** — real rejects from recent runs with the lesson and count.
  Don't repeat them.

## Tools — use the deterministic path before searching
Two paths, and they are NOT interchangeable:

**Known filer + known form → deterministic pull (do this first).** No fuzzy search,
no name collisions, and the URL it returns is a resolved filing document (citable).
```bash
python -m engine.edgar cik "Blue Owl"                  # CIK, or null = no known filer
python -m engine.edgar filings NVIDIA --forms 8-K,D --since 2026-08-01
```
`cik` returning null means "take the search path" — do not guess a CIK.

**Before writing any event row, check we don't already have it:**
```bash
python -m engine.edgar exists --allocator NVIDIA --target "Nebius Group N.V."
```
`exists: true` → don't re-file it; if your source is stronger (better tier/status),
note that in `notes` so ingest merges forward instead of you creating churn.

**Unknown deal in the wild → agent search** (WebSearch/WebFetch, Tier ladder above).

## Status — how sure are you
- `verified` — a Tier-1 source confirms it (filing, official PR, IR page, gov DB).
- `verified_alpha` — strong: ≥2 independent Tier 2–4 sources agree, but no Tier-1 yet.
- `candidate` — a single source or a Tier-5 lead. Honest defaults beat false confidence.

## Output contract — write into `runs/<week>/<agent>/`

**verified_events.csv** and **candidate_events.csv** — identical columns, this exact header:
```
event_date,disclosed_date,allocator,allocator_class,target,target_type,sector,subsector,event_type,amount_usd,amount_estimated,status,source_tier,source_url,notes
```
Field rules:
- `event_date` when capital moved (ISO YYYY-MM-DD, may be approximate/blank).
- `disclosed_date` when it became known (ISO, REQUIRED).
- `allocator` the entity deploying capital, exactly as named in config/allocators.yaml.
- `allocator_class` one of corporate|vc|individual|alt_manager|sovereign (optional
  for a single-class agent — derived from the agent — but REQUIRED for the filings agent).
- `target` who received the capital.
- `target_type` private|public|fund|project|asset (optional).
- `sector` one canonical slug (above).
- `subsector` free text (optional).
- `event_type` one of the table above.
- `amount_usd` number only, no `$`/commas; blank if undisclosed.
- `amount_estimated` 1 if the amount is a press/analyst estimate, else 0.
- `status` candidate|verified|verified_alpha.
- `source_tier` 1–5 (the BEST tier that supports the row).
- `source_url` the confirming link — a RESOLVED document, never a search query.
  Cite the actual article/filing you read (a press URL, or a specific EDGAR
  filing `sec.gov/Archives/edgar/data/<CIK>/<accession>/...`). NEVER put an EDGAR
  full-text-search URL (`efts.sec.gov/...` or `sec.gov/edgar/search?q=...`) here —
  a bare keyword search resolves to nothing and returns unrelated entities. If a
  filings sweep found no document, cite the press you actually have and record the
  sweep in `notes` (+ `provisional`), not a search link. Log searches in
  source_log.csv, which is where "what I checked" belongs. The engine drops a
  search-query source_url and the audit blocks it (E0).
- `notes` lead/participant, vehicle name, caveats.

**Optional structured columns** (fill what the source actually supports — never guess):
`theme` (a canonical theme from config/rules.yaml), `capital_role` (lead|participant|sole),
`instrument` (equity|debt|convertible|grant|jv|safe), `stage` (seed|series a…|growth|buyout),
`round_total_usd` (the FULL round, vs `amount_usd` = this allocator's slice),
`ownership_pct`, `valuation_usd`, `co_investors`, `origin_id` (the claim's first source).

**source_log.csv** — every source you actually checked, header:
```
source_url,source_tier,yielded
```
`yielded` = 1 if it produced at least one event, else 0. This is the audit trail —
log Tier-1 sources checked even when they yield nothing.

**summary.md** — a short narrative: what moved this week in your class, the 2–3
biggest signals, and what to watch next week.
> IMPORTANT: write `summary.md` with **Bash** (`printf`/heredoc), NOT the Write tool —
> the agent Write tool blocks report-style markdown ("report file") and will fail. The
> CSVs are fine via Write. This keeps unattended/scheduled runs from breaking.

## Strong due diligence — escalate a weak lead, don't quit
A rumor (podcast, X post, single blog) is a **lead**, not a dead end and not an event.
Do NOT check SEC, find nothing, and stop. Run this escalation loop before you drop a lead:

1. **Find the origin.** Locate the *first* source of the claim. N outlets all citing one
   origin count as **one** source, not N (circular-reporting guard). Put the origin URL in
   the `origin_id` column.
2. **Primary hunt:** SEC Form D (+ related persons), 8-K (items 1.01/2.01), 13D/G, Form 4;
   company PR/IR/blog (+ Wayback for silent edits); official gov DB.
3. **Registry & legal:** OpenCorporates entity + new subsidiaries/SPVs, state filings, UCC
   liens (debt), court records, HSR/CFIUS for large or cross-border deals.
4. **Corroborating exhaust:** LinkedIn headcount/role changes, job postings for the funded
   initiative, domain/trademark registration, permits/procurement (datacenters, energy),
   customs/shipping (hardware). The *counterparty* often discloses what the principal won't.
5. **Triangulate & weigh hypotheses:** require ≥2 **independent** confirmations for
   `verified_alpha`, a primary for `verified`. Ask what else could explain it (old round
   resurfacing? mark-to-market? PR spin?) and pick what the evidence best fits.
6. **Grade honestly, never drop silently.** If you can't confirm, file it as `candidate`
   with the reason in `notes` — a documented candidate is data; a silent drop is a miss.

"Don't give up yet" moves: reverse from the beneficiary; check the *vehicle* not just the
person; find the *debt* behind the equity; diff quarterly 13Fs; read Form D *amendments*.

## Recurring mistakes — worked examples (promoted from real rejects)
These are the error types that actually recurred across runs. Each is a real case.

**1. Search query as a citation (audit E0 — blocks delivery).**
- REJECTED: `source_url = https://efts.sec.gov/LATEST/search-index?q=%22Cathedral%22&forms=D`
  — a keyword search resolves to nothing and, for a common word, returns unrelated
  filers (Cathedral Energy Services, Cathedral Lake CLOs…).
- GOOD: cite the document you actually read — the press article
  (`https://thenextweb.com/news/cathedral-…`) or a specific filing
  (`https://www.sec.gov/Archives/edgar/data/<CIK>/<accession>/<doc>`). Record the
  fruitless EDGAR sweep in `notes`, not in `source_url`.

**2. Valuation in the amount column (audit W2 / measurement corruption).**
- REJECTED: a $1.4B post-money round where `amount_usd = 1400000000` — that's the
  company's price, not money that moved. It inflates every sector total it touches.
- GOOD: `amount_usd` = the allocator's slice if disclosed; else leave it blank and
  put the round in `round_total_usd`; `valuation_usd` holds the valuation. Never a
  silent 0, never the valuation.

**3. Same round filed once per co-investor (duplicate capital).**
- REJECTED: a16z and Sequoia co-led one $160M round; both rows carried
  `amount_usd = 160000000` → the deal read as $320M.
- GOOD: per-allocator slice when disclosed; otherwise blank `amount_usd` +
  `round_total_usd = 160000000` on each row, and name the co-leads in
  `co_investors`. Run `python -m engine.edgar exists --allocator X --target Y`
  first — if the pair is already on file, don't re-file it.

**4. Ambiguous entity (name collision).**
- REJECTED: filing "Atoms" from a shoe-brand page, or attaching a parent's domain to
  a subsidiary.
- GOOD: verify against the sector + co-investor context you were given. If two
  entities plausibly match, file `candidate` and say which two in `notes` — an
  honest ambiguity is data; a confident wrong entity poisons the map.

## Universe discovery — feed the watchlist
When you see a NOT-yet-tracked allocator co-investing alongside a tracked name, record it in
`runs/<week>/<agent>/discovered_allocators.csv` (header: `name,suggested_class,seen_with,
rationale`). This is how the universe grows — the user promotes these to the watchlist.

## Operating loop
1. Read this file, then your class brief, then config/allocators.yaml (your class)
   and config/sources.yaml.
2. For each allocator on your watchlist: check its mandatory Tier-1 sources, then
   search broadly (Tiers 2–5) for new capital movements.
3. For any weak lead, run the **escalation loop** above before dropping it.
4. Verify each candidate — try to confirm with a higher tier before storing. Set `status`
   by corroboration: `verified` = a primary source; `verified_alpha` = ≥2 independent
   sources; `candidate` = single/uncorroborated. Fill `origin_id` when a claim traces to one origin.
5. Write the output files (the four core + `discovered_allocators.csv` when you find new
   allocators). Deduping, entity-resolution and grading are handled downstream — your job is
   coverage + accuracy, not database hygiene.
