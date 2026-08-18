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

## Two pipelines, one database
The repo runs **two** pipelines against the same `db/capital.db`, because entity identity
is shared — NVIDIA has to be one NVIDIA on both maps, and that is what `config/aliases.yaml`
+ `entity_aliases` guarantee.

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
