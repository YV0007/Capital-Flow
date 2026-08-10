# Capital Flow

Autonomous capital-allocation intelligence engine. Discovers where elite allocators
move money before consensus, stores it as structured data, detects signals, and hands
a map-state file to the dashboard. **Separate from the ab-investment dashboard** — this
is the engine; that is the visualization.

See `ARCHITECTURE.md` for the full design and `RUNBOOK.md` for how to run a cycle.

## Two layers
1. **Research (autonomous)** — six Claude Code subagents (`agents/*.md`) research and
   verify capital-allocation events, writing CSVs into `runs/<week>/<agent>/`.
   No API service, no keys — they use Claude Code's built-in web tools.
2. **Deterministic (Python)** — `run_week.py` validates + dedupes into SQLite, fires
   signal rules, writes the weekly report, and exports the dashboard handoff.

```
agents ──CSV──▶ runs/<week>/ ──▶ run_week.py ──▶ db/capital.db
                                      │
                                      ├─▶ runs/<week>/weekly_report.md
                                      └─▶ handoff/capital_map.json + CHANGELOG.md ──▶ dashboard
```

## Layout
| Path | What |
|---|---|
| `agents/CONTEXT.md` | shared operating context — scope, CSV contract, sectors, tiers |
| `agents/*.md` | the six research briefs + `beneficiary-mapper.md` |
| `config/allocators.yaml` | the watchlist (27 allocators, seeded from the Capital Flow Map) |
| `config/sources.yaml` | tiered source registry |
| `config/rules.yaml` | 12-sector taxonomy + signal rules |
| `db/schema.sql` | SQLite schema (events is the source of truth) |
| `engine/*.py` | ingest, themes, beneficiaries, profiles, aggregates, audit, report, handoff |
| `agents/allocator-profiler.md` | Cluster-C brief: canonical allocator summaries + sourced track records |
| `run_week.py` | orchestrates the deterministic pipeline |
| `tools/smoke_test.py` | end-to-end self-test on synthetic data |
| `handoff/RULES.md` | how the dashboard reconstructs the map from the handoff |

## Quickstart
```bash
python tools/smoke_test.py        # prove the pipeline end-to-end (synthetic data)
python run_week.py 2026-W32       # run the deterministic pipeline for a week
```
Requires Python 3.11+ and `pyyaml`. The SQLite DB (`db/capital.db`) is created on first
run and is gitignored (regenerable from CSVs + schema).

## Derived payload (spec §4–§6)
`handoff/capital_map.json` ships, alongside nodes/flows/sectors/themes:
- `aggregates` — top sector (capital-weighted), top company (by distinct tracked
  investors), thesis shares (theme distribution) — each with a `basis` string.
- `allocators` — one canonical summary per allocator: event rollup + researched
  profile (source-attributed) + per-fiscal-year track record with `provisional` flags.
- target nodes carry `description` + `links` (website + one read-more article) —
  the engine-owned "what this is" card, superseding dashboard-side curation.
- fund + firm nodes carry `portfolio_url` + `holdings[]` + `holdings_count` — the
  companies a fund deploys into (the layer below the map's LP flows), each sourced.
- `audit` — the §6 verification verdict; audit errors block delivery.

## Signal rules (config/rules.yaml)
- **sector_swarm** — ≥5 distinct key allocators into one sector within 30 days.
- **capital_acceleration** — a sector's 90-day capital ≥2× the prior 90 days.
- **first_entry** — an established key allocator enters a brand-new sector.
