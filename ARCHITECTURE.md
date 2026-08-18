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
│   ├── schema_eco.sql    # monthly schema: eco_nodes / edges / evidence / scores / cycles
│   └── capital.db        # SQLite master DB — BOTH pipelines (shared entity identity)
├── config/
│   ├── allocators.yaml   # watchlist: 6 allocator classes, who each weekly agent tracks
│   ├── aliases.yaml      # entity resolution — shared by both pipelines
│   ├── sources.yaml      # Tier 1-5 source registry
│   ├── rules.yaml        # weekly signal rules
│   ├── eco_layers.yaml   # the 12-layer stack + sectors + tech nodes (FROZEN taxonomy)
│   ├── eco_watchlist.yaml# anchors, emerging names, capital spine, agent -> layer map
│   └── eco_rules.yaml    # criticality rubric, source tiers, thresholds, R1-R5
├── agents/               # Claude Code research agent briefs (the autonomous layer)
│   ├── CONTEXT.md        # shared context for the WEEKLY agents
│   ├── corporate.md  vc.md  individuals.md  alt-managers.md  sovereigns.md  filings.md
│   ├── eco-CONTEXT.md    # shared context for the MONTHLY ecosystem agents
│   ├── eco-silicon.md  eco-systems.md  eco-power.md  eco-infra.md  eco-models.md
│   └── eco-capital.md    # the cross-cutting ownership / financing spine
├── engine/               # Python — the deterministic layer
│   ├── ingest.py         # weekly: agent CSVs -> validate -> dedupe -> SQLite
│   ├── themes.py  beneficiaries.py  report.py  handoff.py      # weekly
│   ├── eco.py            # monthly: shared vocabulary + slug identity
│   └── eco_ingest.py  eco_verify.py  eco_score.py  eco_cycles.py  eco_handoff.py
├── tools/
│   └── eco_validate.py   # asserts handoff/ecosystem_map.json against the frozen contract
├── runs/                 # per-period raw agent outputs, kept as the audit trail
│   ├── 2026-W32/<agent>/    verified_events.csv, candidate_events.csv, source_log.csv
│   └── 2026-08/eco-<agent>/ nodes.csv, edges.csv, source_log.csv, summary.md
│                            (+ runs/<month>/rejects.csv — fed back to agents next run)
├── handoff/              # what the dashboard side consumes
│   ├── capital_map.json  ECOSYSTEM-CHANGELOG.md  ecosystem_map.json
│   └── ECOSYSTEM-BUILD-LOG.md   # decisions, deviations, what did not add up
├── run_week.py           # WEEKLY orchestrator: flows map
└── run_month.py          # MONTHLY orchestrator: ecosystem map
```

## Two pipelines, one database
The repo runs **two** pipelines against the same `db/capital.db`, because entity identity
is shared — NVIDIA has to be one NVIDIA on both maps, and that is what `config/aliases.yaml`
+ `entity_aliases` guarantee.

| | Weekly — **Потоки** | Monthly — **Экосистема** |
|---|---|---|
| Question | Where did money go this week | How is the industry built, who holds it |
| Unit | A dated capital-allocation **event** | An undated standing **dependency** |
| Node | Allocator / target | **Company** in a layer of the stack |
| Node size | Capital | **Criticality** (4-factor rubric) |
| Tables | `events`, `allocators`, … | `eco_*` (schema in `db/schema_eco.sql`) |
| Agents | 6 by allocator class (`agents/*.md`) | 6 by stack layer (`agents/eco-*.md`) |
| Orchestrator | `run_week.py` | `run_month.py` |
| Handoff | `handoff/capital_map.json` | `handoff/ecosystem_map.json` |

Shared: entity resolution, the source registry, the `runs/<period>/<agent>/` pattern, the
handoff pattern. Separate: tables, agents, rules, schedule. On the dashboard they are two
unconnected maps sharing only the shell.

## Monthly pipeline (ecosystem map)
```
6 agents (agents/eco-*.md) -> runs/<YYYY-MM>/eco-*/{nodes,edges,source_log}.csv
  -> engine/eco_ingest.py   validate, resolve names to permanent slugs, dedupe, load
                            (rejects -> runs/<month>/rejects.csv, handed back next month)
  -> engine/eco_verify.py   re-fetch EVERY citation, look for its own quote, expire the dead
  -> engine/eco_score.py    criticality rubric, gravity, per-layer HHI + concentration
  -> engine/eco_cycles.py   closed loops of length 3–5, sales vs financing
  -> engine/eco_handoff.py  handoff/ecosystem_map.json + handoff/ECOSYSTEM-CHANGELOG.md
```
Validate the output against the frozen contract with `python tools/eco_validate.py`.

**The load-bearing rule:** an edge exists only if a **verbatim quote** from a resolved
document states the relationship. Evidence is its own table (`eco_evidence`, many rows per
edge), which is where the two-source rule, the effective source tier and the monthly
liveness recheck all come from for free. `eco_verify` re-fetches every URL each month, so
the map shows its own decay rather than quietly going stale.

**Criticality is not a judgement call:** agents supply four 0–5 factors with a sourced
`share_note`; `eco_score` does the arithmetic (`config/eco_rules.yaml` holds the weights).
ASML 5/5/5/5 → 100; a commodity ODM 2/1/1/1 → 26.

**Cycles are searched in the MONEY direction.** Edges are stored supplier → consumer, so
`eco_cycles` reverses the physical spine before searching: NVIDIA funds OpenAI, OpenAI pays
CoreWeave, CoreWeave pays NVIDIA. In goods direction those three edges are a chain and
nothing closes.

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
