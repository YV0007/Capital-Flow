# Handoff reconstruction rules (v1 — tunable)

The dashboard (ab-investment) is a **separate repo**. The connection is a handoff,
not a live feed: the engine writes `handoff/capital_map.json` + `handoff/CHANGELOG.md`,
and a Claude session on the dashboard side reads them to **reconstruct / update the
Capital Flow Map** — add new entities, retire stale ones, adjust visuals.

These are the rules that session follows. They are deliberately conservative for v1;
tune the thresholds as the data grows.

## What the dashboard session receives
- `capital_map.json` — full current map state:
  - `nodes[]` — allocators + targets, each with `kind`, `cls`, `tier`, `sector`,
    `deals`, `capital`, `first_seen`, `last_activity`, `stale`.
  - `flows[]` — edges (allocator → target) with `amount`, `event_type`, `status`,
    `date`, `tier`, `sector`.
  - `sectors{}` — per-sector totals + fired `signals`.
- `CHANGELOG.md` — new and stale entities since the previous handoff.

## Inclusion — when to put an entity on the visual map
- Include a node if it has **≥1 `verified` or `verified_alpha` flow**. Do not surface
  `candidate`-only entities on the public map (they can live in a "watch" list).
- Always include an entity that a **fired signal** points at (sector with a
  sector_swarm / acceleration / first_entry theme), even if small.

## Emphasis — how prominent
- Node size ∝ `capital`. Key-tier allocators and Tier-1-sourced flows read strongest.
- Highlight sectors carrying a fired signal this cycle (`sectors[].signals`).

## Staleness — when to retire content
- A node with `stale: true` (no activity in 180 days — see `STALE_DAYS`) should be
  **de-emphasized**, not deleted: move to a muted state or a "cooling" tier.
- Only fully drop a node when it has been stale for **two consecutive handoffs** AND
  carries no verified flow. Keep history; the map is cumulative memory, not a snapshot.

## Change handling each cycle
- New entities (from `CHANGELOG.md`): add them, sized by capital, placed in their
  sector zone.
- Existing entities: update size/last_activity; promote to highlighted if newly
  carrying a signal.
- Never silently remove an entity that was visible last cycle — if dropped, note it.

## Finalized decisions (see handoff/DASHBOARD_BRIEF.md §5)
- **Node-drop policy:** de-emphasize on first stale (180d); drop from the visual only
  after two consecutive weekly updates stale + no verified flow; keep in data always.
- **Visual latitude:** the dashboard session owns visuals completely; zero data latitude
  (never invent or override entities/flows/amounts/status).
- **Delivery — auto-push:** the engine auto-commits `capital_map.json` →
  `ab-investment/src/data/capitalMap.json` directly to `main` and pushes (only that file);
  Vercel deploys. No review gate. A user-uploaded file overwrites the same path identically.

The full consumer specification lives in **handoff/DASHBOARD_BRIEF.md** — hand that entire
file to an ab-investment Claude Code session to rebuild the map.

## New payload blocks (v3 — spec §4/§5/§6, added 2026-08-09)
- `aggregates.top_sector` / `aggregates.top_company` / `aggregates.thesis_shares` —
  derived views computed by the engine (each carries a `basis` string). Render them
  as-is; NEVER recompute derived numbers on the dashboard side.
- `allocators` — the canonical allocator summary (one per allocator): event-derived
  rollup (deals, capital, sectors, thesis_shares, recency) + `profile` (background,
  focus, style, thesis, latest_investments_summary, strategy + `strategy_source_url`
  attribution, `sources`) + `track_record` (per fiscal year; each row has
  `provisional` and `source_url`). Use for BOTH aggregate views and the detail
  panel. Always show a "provisional / unaudited" marker when `provisional: true`,
  and keep source attribution visible or one tap away.
- `nodes[].country` — allocator national affiliation for flag rendering.
- `audit` — the §6 verification verdict shipped with the data (`passed`,
  `error_count`, `warning_count`, `stats.source_url_coverage`). The engine blocks
  its own delivery when the audit fails, so a payload you receive always passed.

## Target references on nodes (v3.1, added 2026-08-09)
- Target nodes may now carry `description` (1–3 sentences: what the entity is),
  `links` (`kind: website` and `kind: read_more` — ONE good article, labeled with
  its publication), and `reference_as_of`.
- These are engine-researched and engine-owned. Where present, they take
  precedence over the dashboard's local `entityReference.json` (as that file's
  own `_note` anticipates). The local file remains only a fallback for nodes the
  engine has not referenced yet; do not hand-curate entries for nodes that
  already carry engine data.
- Render `description` in the "About / what this is" card and `links` beneath it
  (website chip + read-more chip), as in the existing Atoms-style layout.

## Flow "read" ownership (v3.2, 2026-08-10) — engine=facts, dashboard=words
The per-deal "read"/angle write-up is NARRATIVE, not fact, and is owned by the
DASHBOARD, generated on its scheduled run. The engine never writes read prose —
keeping its payload 100% auditable fact. To let the dashboard word a read for
EVERY flow without fetching anything itself, each flow now carries the full fact
set needed:
- `id` — stable, deterministic per flow (sha1 of allocator|target|event_type|date).
  Cache generated reads against this id; a flow's id only changes if the flow is
  genuinely new/changed, so unchanged flows are never re-worded.
- `source_url`, `amount`, `amount_estimated`, `round_total`, `co_investors`,
  `capital_role`, `instrument`, `stage`, `status`, `confidence`, `grade`,
  `sector`, `subsector`, `event_type`, `date`.
- Plus the joinable context already in the payload: `allocators[source].profile`
  (thesis/style), the target node's `description`, and `sectors[].signals`.
The dashboard writes `{angle, read}` from THIS payload only — no external search.
`flowNotes.json` therefore becomes generated-and-cached, not hand-curated, and
covers 100% of flows instead of ~23%. Boundary rule: engine searches + sources +
derives facts; dashboard words + visualizes. Neither does the other's job.

## Fund holdings on nodes (v3.3, 2026-08-10) — the layer below LP flows
Fund + firm nodes (any node whose entity has collected holdings — `cls:"fund"`
targets and VC/alt-manager allocators) may now carry:
- `portfolio_url` — DIRECT link to that entity's portfolio listing (not homepage);
  absent when no portfolio page exists (fall back to the website link).
- `holdings[]` — the companies the fund deploys into, ranked most-notable first;
  each `{name, sector, subsector, note, stake, lead, as_of, source_url}`. Every
  holding is sourced. When a holding's `name` matches a map node label, link the
  row straight through.
- `holdings_count` — the TRUE total (may exceed the array; show "top N of count").
- `holdings_as_of` — research date.
Cumulative like the map; the audit flags (W7) any ≥$1B fund/firm with zero
holdings. This is the "follow smart money into the exact companies" layer — the
map shows LP money into a fund; holdings show where the fund then deploys it.

## Deep classification (v3.4, 2026-08-10) — lights up the two-rank highlight
The deal-classifier fills factors the dashboard already computes but couldn't feed.
All additive & back-compatible (a missing block leaves that factor "pending").

Flows gain dated-backer fields (unlocks lead-time + bellwether):
- `round_id` — groups co-participants of one round; `role` ∈ lead|co-lead|
  participant|follow-on; `provisional` — true when the date is the round's, not
  the backer's. Some flows are `backer_edge:true` — a participation edge with no
  capital event of its own (amount may be null; it's not a sourced capital move).

Investable target nodes gain (each block sourced; absent when unknown):
- `outcome` — {status ∈ active|up_round|ipo|acquired|shut_down, entry/latest
  valuation, step_up_multiple, source_url, provisional} → strike-rate.
- `investability` — {listing_status ∈ public|filed_s1|rumored_ipo|private|
  subsidiary, public_ticker, public_proxies:[{ticker,relation,source_url}]} →
  actionable path.
- `ai_posture` — {class ∈ compounds|neutral|at_risk, rationale, source_url,
  confidence, provisional} → the moat / AI-resilience factor (NEW). Out-of-vocab
  classes are dropped by the engine, so the dashboard can weight the tag safely.
Audit W8 flags any >=$1B investable target with no ai_posture.

## Sub-sector trends (v3.5, 2026-08-11) — named, grounded narratives per window
New top-level `trends` block, keyed to the dashboard's window ids: `{week, month,
all}`, each a ranked list of the top 1-3 sub-sector clusters. Additive; nothing
else changes. Per entry:
- `title`, `sector`, `subsector`, `deals`, `capital_usd`, `date_range`,
  `allocators[]` (named), `evidence[]` (event ids) — all SQL-derived from real
  confirmed flows (numbers + named investors, not adjectives).
- `narrative` — the grounded "why + who" paragraph (Stage-A trend-writer agent);
  `null` until written. `confidence` (high|low) + `provisional`: a borderline
  cluster surfaced in a quiet window is flagged `low`/provisional, never asserted
  equal to one that cleared the bar. A window with no clusters ships `[]`.
Also: `sectors[].signals[]` now carries `evidence` (event ids), and both the
signals and theme-aggregate exports are bound to the current run week (were
unfiltered — would have mixed stale signals next week).
