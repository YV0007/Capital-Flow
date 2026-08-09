# RUNBOOK — running a weekly cycle

The engine has two layers:
- **Research (autonomous):** six Claude Code subagents driven by `agents/*.md`.
- **Deterministic (Python):** `run_week.py` — ingest → themes → beneficiaries → report → handoff.

There is **no API service and no per-token billing to manage** — the agents run
inside Claude Code using its built-in WebSearch / WebFetch / file tools.

---

## Mode B1 — human-in-the-loop (use this first, and for the pilot)

Run this from a Claude Code session in this repo. Pick the ISO week, e.g. `2026-W32`.

**Step 1 — research.** Launch the six research agents as subagents. Each gets the
same instruction, varying only the agent name:

> You are the **<AGENT>** research agent for the Capital Flow engine.
> Read `agents/CONTEXT.md`, then `agents/<AGENT>.md`, then your slice of
> `config/allocators.yaml` and `config/sources.yaml`.
> Research capital-allocation events for ISO week **<WEEK>**, verify them, and write
> `verified_events.csv`, `candidate_events.csv`, `source_log.csv`, and `summary.md`
> into `runs/<WEEK>/<AGENT>/`. Follow the CSV contract in CONTEXT.md exactly.

Run the five single-class agents first (corporate, vc, individuals, alt-managers,
sovereigns), then **filings last** so it can confirm the others' candidates.

**Step 2 — pilot check (first runs only).** Open a couple of `verified_events.csv`
rows and click the `source_url`. Confirm the capital movement is real and correctly
sectored. This is the accuracy gate — do it manually until you trust the loop.

**Step 3 — deterministic pipeline.**
```bash
python run_week.py 2026-W32
```
This validates + dedupes into `db/capital.db`, fires the signal rules, writes
`runs/<week>/weekly_report.md`, and regenerates `handoff/capital_map.json` +
`handoff/CHANGELOG.md`.

**Step 3b — allocator profiles (Cluster C, refresh periodically).** Launch
allocator-profiler batches (`agents/allocator-profiler.md`) writing
`runs/<week>/profiles/<batch>/profiles.json`, then re-run `python run_week.py <week>`
to ingest them (idempotent). The audit pass warns on key allocators with events but
no profile; audit ERRORS block `--deliver`/`--push`.

**Step 3c — target references (new entities each cycle).** For map targets without
a reference, generate batch inputs (target + sector + allocators + deal URLs) under
`runs/<week>/references/batch-N/batch_targets.json`, launch target-profiler agents
(`agents/target-profiler.md`) writing `references.json` beside them, then re-run the
pipeline to ingest. The audit warns (W6) on ≥$1B targets without a reference.

**Step 4 — beneficiaries (optional but recommended).** Run the beneficiary-mapper
pass (`agents/beneficiary-mapper.md`) to write `runs/<week>/beneficiaries.csv`, then
re-run `python run_week.py 2026-W32` to link them (idempotent — safe to re-run).

**Step 5 — read the report** at `runs/<week>/weekly_report.md`. Hand
`handoff/capital_map.json` to the dashboard side (see `handoff/RULES.md`).

---

## Mode B2 — scheduled / autonomous (after B1 is trusted)

Wrap the exact B1 sequence in a scheduled cloud agent (the `/schedule` skill or cron)
that fires weekly: launch the six agents → `run_week.py` → beneficiary pass →
`run_week.py` → commit `handoff/`. No human present. Only move to B2 once the pilot
has shown the verified output is reliably real.

---

## Just the deterministic half
If `runs/<week>/` already has agent CSVs, you can run the Python pipeline alone:
```bash
python run_week.py <week>      # full deterministic pipeline
python tools/smoke_test.py     # end-to-end self-test on synthetic data
```
