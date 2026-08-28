# Capital Flow — AI Autonomous Capital Platform

Mission: discover real capital allocation before consensus, and map private flows to public beneficiaries.

This repo is the **autonomous research engine**. It is fully separate from the dashboard
(`ab-investment`). The two meet only at one contract point: the **handoff file** (see below).

## Design philosophy
- Capital Allocation Intelligence Platform, not a news aggregator.
- Search is autonomous (Claude Code agents). Output is deterministic (Python + SQL).
- The database is the single source of truth.
- Track ONLY capital allocation events: equity, funding rounds, follow-ons, acquisitions,
  minority stakes, fund launches, SPVs, government grants, project finance, corporate and
  sovereign investments.

## Layout

```
Capital Flow/
├── db/
│   ├── schema.sql        # weekly schema: events, allocators, beneficiaries, themes
│   ├── schema_nveco.sql  # monthly schema: nveco_entity / edge / source / cycle …
│   └── capital.db        # SQLite master DB — BOTH pipelines (shared entity identity)
├── config/
│   ├── allocators.yaml   # watchlist: 6 allocator classes, who each weekly agent tracks
│   ├── aliases.yaml      # entity resolution — shared by both pipelines
│   ├── sources.yaml      # Tier 1-5 source registry
│   ├── rules.yaml        # weekly signal rules
│   ├── nveco_layers.yaml # 16 layers + sectors + tech nodes (FROZEN taxonomy)
│   ├── nveco_edges.yaml  # 31 edge types -> 5 spines (FROZEN taxonomy)
│   ├── nveco_anchors.yaml# anchor registry — the centre of each ecosystem
│   └── nveco_watchlist.yaml # seed entities per agent
├── agents/               # Claude Code research agent briefs (the autonomous layer)
│   ├── CONTEXT.md        # shared context for the WEEKLY agents
│   ├── corporate.md  vc.md  individuals.md  alt-managers.md  sovereigns.md  filings.md
│   ├── nveco-CONTEXT.md  # shared context for the MONTHLY ecosystem agents
│   ├── nveco-geo.md  nveco-silicon.md  nveco-systems.md  nveco-power.md
│   ├── nveco-software.md  nveco-models.md  nveco-capital.md
│   └── nveco-strategic.md # runs LAST; finds cycles, moats, hedges — no new entities
├── engine/               # Python — the deterministic layer
│   ├── ingest.py         # weekly: agent CSVs -> validate -> dedupe -> SQLite
│   ├── themes.py  beneficiaries.py  report.py  handoff.py      # weekly
│   ├── nveco.py          # monthly: shared vocabulary + stable ids
│   └── nveco_ingest.py  nveco_verify.py  nveco_score.py  nveco_cycles.py  nveco_handoff.py
├── tools/
│   └── nveco_corrupt_test.py # proves the handoff validator rejects broken files
├── runs/                 # per-period raw agent outputs, kept as the audit trail
│   ├── 2026-W32/<agent>/    verified_events.csv, candidate_events.csv, source_log.csv
│   └── 2026-08/nveco-<agent>/ entities.csv, factors.csv, edges.csv, sources.csv
│                            (+ runs/<month>/_rejected/ — fed back to agents next run)
├── handoff/              # what the dashboard side consumes
│   ├── capital_map.json  nvidia_ecosystem.json  ECOSYSTEM-V2-CHANGELOG.md
│   └── NVIDIA-ECOSYSTEM-BUILD-LOG.md  # decisions, deviations, what did not add up
├── archive/ecosystem-v1/ # the retired 12-layer supply-chain map, frozen 2026-08-18
├── run_week.py           # WEEKLY orchestrator: flows map
└── run_nvidia.py         # MONTHLY orchestrator: NVIDIA ecosystem map
```

## Three pipelines, one database
The repo runs **three** pipelines against the same `db/capital.db`, because entity identity
is shared — NVIDIA has to be one NVIDIA on every map, and that is what `config/aliases.yaml`
+ `entity_aliases` guarantee.

The third — the **Fund Tracker** (`run_funds.py`, tables `fund_*`) — is shaped unlike the
other two. Weekly is discovery-shaped (agents hunt leads → dated `events`); monthly is
dependency-shaped (an anchor and its orbit). Section 3 is **registry-shaped**: a closed,
curated list of 14 managers whose *positions, stakes and deltas* are held as a standing
book. It has no research agents at all — every row traces to a mandated filing or an
official register download. See its own section below.

| | Weekly — **Потоки** | Monthly — **Экосистема NVIDIA** |
|---|---|---|
| Question | Where did money go this week | Who makes NVIDIA irreplaceable, who is locked into its orbit, who gates it, what does it hedge with |
| Unit | A dated capital-allocation **event** | An undated standing **dependency** |
| Node | Allocator / target | **Entity** in the orbit of an anchor |
| Node size | Capital | **Criticality** (4-factor rubric, 0–100 each) |
| Centre | none | **anchor** — nothing further than 2 hops from it exists |
| Tables | `events`, `allocators`, … | `nveco_*` (schema in `db/schema_nveco.sql`) |
| Agents | 6 by allocator class (`agents/*.md`) | 8 by stack layer (`agents/nveco-*.md`) |
| Orchestrator | `run_week.py` | `run_nvidia.py` |
| Handoff | `handoff/capital_map.json` | `handoff/nvidia_ecosystem.json` |

Shared: entity resolution, the source registry, the `runs/<period>/<agent>/` pattern, the
handoff pattern. Separate: tables, agents, rules, schedule. On the dashboard they are two
unconnected maps sharing only the shell.

## Monthly pipeline (NVIDIA ecosystem map, v2)
```
8 agents (agents/nveco-*.md) -> runs/<YYYY-MM>/nveco-*/{entities,factors,edges,sources}.csv
  -> engine/nveco_ingest.py   validate against the frozen configs, resolve ids, 2-hop rule
                              (rejects -> runs/<month>/_rejected/<agent>.csv)
  -> engine/nveco_verify.py   re-fetch EVERY link; a dead one costs the edge a confirmation
  -> engine/nveco_score.py    rubric, spine from type, status from tiers, gravity, HHI, clamps
  -> engine/nveco_cycles.py   closed loops 3–5 long: sales / financing / lockin
  -> engine/nveco_score.py    again — gravity counts the cycles an entity stands on
  -> engine/nveco_handoff.py  handoff/nvidia_ecosystem.json + ECOSYSTEM-V2-CHANGELOG.md
```
Prove the validator still bites with `python tools/nveco_corrupt_test.py`.

**The map has a centre.** `anchor` (`config/nveco_anchors.yaml`) is the question the map
answers. An entity more than 2 hops from it is rejected at ingest with a reason — that is
the line between "NVIDIA's orbit" and "the world semiconductor industry". A second anchor
costs one config entry and one run; nothing else in the engine is anchor-aware.

**Five spines, not two.** `physical` · `capital` · `moat` · `control` · `rivalry`. A moat
and a gate are not kinds of supply and not kinds of money — they are separate mechanics of
power, and they must not read in one colour with a delivery. The spine is DERIVED from the
edge type (`config/nveco_edges.yaml`); neither the agent nor the dashboard computes it.

**The iron rule:** an edge exists only if a verbatim quote of **15 words or fewer** from a
resolved document states the relationship. Sources for entities and edges live in one
table, so `nveco_verify` walks every link in a single pass.

**Nothing is written unless it validates.** `nveco_handoff` runs the contract's hard rules
before writing and refuses to overwrite a good file with a broken one — yesterday's truth
beats today's lie.

**No DC-AI references.** The map carries its own taxonomy; the field `dcNode` does not
exist and the validator rejects a payload that reintroduces it.

## Weekly pipeline
Scheduler → 6 research agents (CSV outputs into `runs/<week>/`) → `ingest.py` validates into
`capital.db` → `themes.py` + `beneficiaries.py` run SQL rules → `report.py` → `handoff.py`
regenerates the handoff file.

## Database: SQLite
- One file (`db/capital.db`), zero infrastructure, full SQL for signal rules, native in Python.
- Agent CSVs are the interchange format; ingest validates and loads them. The DB is truth.
- Upgrade path if ever needed: Postgres / Turso (hosted SQLite). Not needed at current scale.

## Source policy
- Tier 1: SEC, IR, official PRs, portfolio pages, government DBs — confirms.
- Tier 2: PitchBook, Preqin, AlphaSense, FactSet, Capital IQ, Bloomberg, Dealroom, Crunchbase, Harmonic.
- Tier 3: Reuters, FT, WSJ, Bloomberg News, The Information.
- Tier 4: SemiAnalysis, Stratechery, conferences.
- Tier 5: podcasts, YouTube, X, LinkedIn, blogs — discovers leads.
- Tier 5 discovers; Tier 1 confirms when possible; otherwise mark Candidate / Verified Alpha.

## Handoff contract (dashboard connection) — DECISION PENDING, defined later
The dashboard is NOT a passive consumer of a data feed. The handoff is a self-contained file
(or small set) that a Claude session in `ab-investment` reads to **reconstruct** the Capital
Flow Map — adding new entities, retiring stale ones, adjusting visuals.

Shape (implemented by `engine/handoff.py`, rules in `handoff/RULES.md` v1):
- `handoff/capital_map.json` — current map state: nodes (allocators + targets) with
  first_seen / last_activity / capital / stale, flows (edges), sector aggregates + signals.
- `handoff/CHANGELOG.md` — new and stale entities since the last handoff.
- `handoff/RULES.md` — reconstruction rules for the consuming Claude session: inclusion,
  emphasis, staleness/removal, change handling. v1 written; thresholds tunable.

Still to finalize with the user: exact node-drop policy, visual-adjustment latitude for
the consuming session, delivery mechanism (manual drop vs. committed artifact pulled).

## Build plan
1. Structure ✅  2. Database + schema ✅  3. Scheduler ⏳ (B2)  4. Research agent briefs ✅
5. Validation/ingest ✅  6. Theme engine ✅  7. Beneficiary engine ✅ (loader + mapper brief)
8. Weekly report ✅  9. Handoff contract + rules ✅ (v1)  10. Dashboard reconstruction
workflow ⏳ (dashboard side)  11. Automation ⏳ (B2)
12. Derived aggregates (§4: top sector / top company / thesis shares) ✅ engine/aggregates.py
13. Allocator intelligence (§5, Cluster C) ✅ agents/allocator-profiler.md +
    engine/profiles.py → allocator_profiles + track_records (provisional-flagged, sourced)
14. Audit gate (§6) ✅ engine/audit.py — every run; errors block --deliver/--push
15. Fund holdings ✅ agents/holdings-profiler.md + engine/holdings.py → portfolios +
    holdings tables; emitted on fund/firm nodes (portfolio_url + holdings[] +
    holdings_count). The "follow smart money into the exact companies" layer.
16. Deep classification ✅ agents/deal-classifier.md + engine/classify.py →
    round_backers (dated per-allocator edges: lead-time + bellwether) +
    target_classification (outcome/valuation trail, investability + public proxies,
    ai_posture moat tag). Lights up the dashboard's two-rank highlight. Audit W8.
17. Sub-sector trends ✅ Stage B (engine/themes.py subsector_swarm + engine/trends.py
    windowed clustering) finds real (sector,subsector) convergence; Stage A
    (agents/trend-writer.md) writes the grounded narrative. Ships trends{week,month,all}.

Remaining: scheduling (B2) and the dashboard-side consumer of the v3 blocks.


## Fund Tracker (Section 3) — the registry pipeline

| | Daily — **Фонды** |
|---|---|
| Question | What are the ~14 funds we respect doing with their book, right now |
| Unit | A **position / stake / delta**, not an event |
| Universe | **Closed and curated** (`config/fund_managers.yaml`) — never auto-extended |
| Sources | Mandated filings and official registers ONLY. No news, socials or aggregators. |
| Tables | `fund_*` (schema in `db/schema_fund.sql`) |
| Agents | **none** — fully deterministic |
| Orchestrator | `run_funds.py` |
| Handoff | `handoff/fund_tracker.json` + `FUND-TRACKER-CHANGELOG.md` |

```
config/fund_managers.yaml  -> fund.seed()          every CIK re-verified against EDGAR's
                                                   own name for it; a mismatch HALTS the run
  -> fund_ingest.poll      diff each CIK's submissions JSON; new accession = ingest now
  -> fund_13f              information table -> positions; value UNITS DETECTED per filing
  -> fund_fast             13D/G + verbatim Item 4, Form 3/4/5, material 8-K
  -> fund_ark              the daily full book — zero disclosure lag
  -> fund_shorts           NAMED shorts, FCA/EU registers (the only attributed shorts)
  -> fund_watch            §B3 triggers for the four multi-strats (no standing book)
  -> fund_deltas           SHARE-based deltas + conviction scores
  -> fund_audit            §7 — errors block delivery
  -> fund_handoff          payload, with a contract validator that refuses a broken write
```

**Two problems define the design.**

*Latency.* A 13F is up to 4.5 months stale, so it is the backbone and never the heartbeat.
A ladder of faster layers (ARK daily · registers daily · Form 4 ~T+2 · 13D ~T+5 · 8-K live)
fills the gap, and `latency_days` is a first-class field on every dated row. The handoff
**refuses to write** an event that lacks it — a "new position" without its latency is
actively misleading.

*Conviction vs noise.* A 13F is a legal aggregation, not a statement of belief. Handled
structurally by `style_tag` / `conviction_weight` (multi-strat 0.0, quant never ingested)
and analytically by the 0–100 model in `docs/conviction-model.md`, every constant
`[PROPOSED]` and tunable in `config/fund_conviction.yaml`. **Deltas are computed on share
count, never on value** — a value-based delta invents adds that never happened.

**The multi-strat carve-out.** There is no separate CIK for a "conviction sleeve" inside
Citadel, and the 13F carries no strategy attribution — so the conviction desk cannot be
parsed out of the filing. Citadel, Millennium, Point72 and Balyasny are `watch_only`:
their 13F is never read, and they surface only on a 13D, a >5% 13G, a Form 3/4, a named
short-register entry, or a cap-table appearance.

**Entity resolution is mandatory, not optional.** Point72 files under six CIKs and
Greenlight under three (its live 13F filer is *DME Capital Management*, not "Greenlight").
`fund_manager_entities` rolls children to a parent; without it the same fund appears three
times at a third of its real size and every conviction score is wrong.


## Fund portfolios — the layer below the map's flows

The map shows LP money flowing INTO a fund. `holdings[]` and `public_book` show
where that fund then deploys it. Run monthly by `run_holdings.py`; scheduled with
`tools/install_holdings_schedule.sh`.

```
make_holdings_batches   funds with no portfolio, OR below the 25-holding floor,
                        OR below the 50 coverage target — capital-ordered, so a
                        partial run loses the tail rather than a slice of everything
  -> holdings_agents    ONE AGENT PER BATCH, launched and awaited. This step never
                        existed; it was a line in the runbook addressed to a person,
                        skipped in two of three weeks, and the reason 36 funds were
                        empty. No launcher => the run FAILS, never ships green.
  -> holdings.ingest    unchanged, plus a depth check and a request ledger
  -> public_book        13F for allocators that file one (config/allocator_ciks.yaml)
  -> audit -> handoff -> build gate -> deploy
```

**Two books, never summed.** `holdings[]` is researched from a fund's own portfolio
page — the only possible source for a venture manager, since Form 13F covers
US-listed equity only and Thrive's book (OpenAI, Stripe, SpaceX) appears in no 13F
ever. `public_book` is the 13F. Coatue has both, naming two disjoint sets of
companies; adding them would double-count.

**`positions[]` is what a fund OWNS, not what it traded.** Only `common` and `adr`
count as ownership; puts, calls, warrants, rights, units, convertibles and `PRN`
debt are split into `derivatives[]` and excluded from every weight and total. This
is correctness, not taste: 13F reports an option at the NOTIONAL value of the
underlying, so one index put outweighs every real holding and rescales the whole
book. Before the split, Elliott's largest "holding" was a $2.5bn put on QQQ — a bet
the Nasdaq falls, rendered as its top conviction. Exited zero-share rows are
likewise not holdings; the trade flow lives in `activity[]`.

**A skipped run is loud.** `holdings_requests` records what each run asked for, so
"no result" is provably a step that did not run rather than a quiet month, and a
≥$5B fund missed twice becomes audit error E6 instead of a warning nobody reads.
