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
| `engine/*.py` | ingest, themes, beneficiaries, report, handoff |
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

## Signal rules (config/rules.yaml)
- **sector_swarm** — ≥5 distinct key allocators into one sector within 30 days.
- **capital_acceleration** — a sector's 90-day capital ≥2× the prior 90 days.
- **first_entry** — an established key allocator enters a brand-new sector.
