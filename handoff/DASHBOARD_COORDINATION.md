# Capital Flow ⇄ Dashboard — how the two systems coordinate

Paste this into a Claude Code session in the `ab-investment` repo. It defines the
boundary between the two systems and the concrete work now on the dashboard side.

## The two systems and the one rule

There are two separate repos with one contract point (`src/data/capitalMap.json`,
auto-delivered each cycle):

- **The engine** (`Capital Flow` repo) — the **data collector and source of
  truth**. It searches, sources, verifies, and derives. Everything it emits is
  auditable FACT (every number traces to a source; an audit gate blocks delivery
  on any violation).
- **The dashboard** (this repo) — **wording and visualization**. It renders the
  engine payload and writes the human-facing NARRATIVE. It does NOT collect data
  and must NEVER fetch external sources.

**The rule, and the reason it exists:** the collector owns facts + rules; the
dashboard owns arithmetic-display + wording. No single number is owned by both.
Keeping interpretation OUT of the engine is what keeps the engine's output 100%
verifiable — which is the whole product (trust). So:

| Kind of thing | Owner |
|---|---|
| What happened, sourced (amount, who, when, valuation, source URL) | **Engine** |
| Derived facts (sector totals, signals, thesis shares, rankings) | **Engine** |
| Entity "what this is" description + links + country | **Engine** |
| Allocator profile + track record | **Engine** |
| The deal "read" / angle (interpretive prose) | **Dashboard** |
| Chart layout, colors, labels, RU copy, node placement | **Dashboard** |

## What the engine now delivers (consume these; don't recompute or re-fetch)

Every cycle `capitalMap.json` ships the FULL cumulative map (not a weekly delta):
- `nodes[]` — allocators + targets. Targets carry `description` + `links`
  (website + one read-more). Allocators carry `country`.
- `flows[]` — each carries `id` (stable), `source_url`, `amount`,
  `amount_estimated`, `round_total`, `co_investors`, `capital_role`,
  `instrument`, `stage`, `sector`, `subsector`, `status`, `confidence`, `grade`.
- `allocators{}` — canonical per-allocator summary: rollup + `profile` +
  `track_record` (each row `provisional` + `source_url`).
- `aggregates` — top_sector / top_company / thesis_shares, each with a `basis`
  string. Render as-is; NEVER recompute.
- `sectors{}.signals`, `themes{}` — fired signals.
- `audit` — the verification verdict for this payload (always `passed:true`; the
  engine blocks its own delivery otherwise).

## Dashboard tasks — do these

### 1. Generate the deal "read" on your scheduled run (retires hand-curation)
The read/angle is yours to WRITE, from the payload ONLY — no web search, because
every fact you need is already in the flow + its joined nodes.

- For each flow, you have: the flow's facts (above), `allocators[source].profile`
  (thesis/style/latest logic), the target node's `description`, and the sector's
  fired `signals`. That is enough to write a grounded angle + read.
- **Cache against `flow.id`.** It's a stable hash; a flow's id only changes when
  the flow is genuinely new/changed. So generate a read once per id, store it,
  and only (re)generate for ids you haven't seen. This makes coverage 100% of
  flows (was ~23%) with no re-wording of unchanged deals each week.
- `flowNotes.json` becomes your generated+cached store, not a hand-written file.
- Keep the UI label honest ("наша трактовка · не данные движка") — it's true
  precisely because the engine never wrote it.

### 2. Retire the redundant hand files (the engine now supplies these)
- **`subsectors.js`** (keyword guesser) → read `flow.subsector` from the payload.
- **`capital_map.archive.json`** stopgap + the cumulative-merge logic → the engine
  now ships the full cumulative map, guarded against collapse. Render the delivery
  directly; drop the archive union.
- **`allocatorProfiles.json`** → empty and superseded by `allocators{}.profile`;
  delete it and the legacy fallback branch.
- **`entityReference.json`** → keep ONLY as a fallback for nodes the engine hasn't
  described yet, plus `displayName` overrides (see below). Stop hand-adding
  description/links/country for engine-covered nodes; the engine wins there.

### 3. The one field the engine intentionally does NOT own
- **`displayName`** overrides (e.g. "Andreessen Horowitz" → "a16z") stay in your
  reference file — they're presentation, not fact. This is by design.

## Boundaries — do NOT
- Do not fetch external data for anything. If a card renders blank (e.g. a new
  ≥$1B target with no description), that's an engine coverage gap — report it back;
  the engine's audit already flags it (W6). Don't hand-fill it.
- Do not edit or override engine-delivered facts (amounts, status, sources,
  profiles, track records, aggregates). Zero data latitude.
- Do not recompute aggregates/signals; render the engine's numbers so the two
  systems can never disagree on screen.

## Quick verification after wiring
- A flow's "read" is generated (not hand-written) and persists across a re-run
  without regenerating (id cache working).
- "OpenAI southern Ohio 10GW data center" shows an engine description + link.
- Blackstone's detail panel shows profile + segment track-record rows with
  provisional markers.
- Map shows the full ~166-node cumulative graph without the archive stopgap.
