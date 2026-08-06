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
│   ├── schema.sql        # versioned schema: events, allocators, beneficiaries, themes
│   └── capital.db        # SQLite master DB (created by engine/ingest.py on first run)
├── config/
│   ├── allocators.yaml   # watchlist: 6 allocator classes, who each agent tracks
│   ├── sources.yaml      # Tier 1–5 source registry
│   └── rules.yaml        # signal rules (e.g. ≥5 distinct key investors → sector, 30d)
├── agents/               # Claude Code research agent briefs (the autonomous layer)
│   ├── corporate.md  vc.md  individuals.md  alt-managers.md  sovereigns.md  filings.md
├── engine/               # Python — the deterministic layer
│   ├── ingest.py         # agent CSVs → validate → dedupe → SQLite
│   ├── themes.py         # SQL rules over events → themes, capital rotation
│   ├── beneficiaries.py  # private flows → public beneficiaries
│   ├── report.py         # weekly_report.md
│   └── handoff.py        # SQLite → handoff file for the dashboard
├── runs/                 # per-week raw agent outputs, kept as audit trail
│   └── 2026-W32/<agent>/ (verified_events.csv, candidate_events.csv, source_log.csv, summary.md)
├── handoff/              # what the dashboard side consumes (see Handoff contract)
└── run_week.py           # orchestrator: agents → ingest → themes → beneficiaries → report → handoff
```

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

Remaining: live agent runs (pilot), scheduling (B2), and the dashboard-side consumer.
