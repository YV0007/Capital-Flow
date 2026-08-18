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

**Step 3d — fund holdings (the layer below LP flows).** For funds/firms without
collected holdings, generate batch inputs, then launch profiler agents:
```bash
python tools/make_holdings_batches.py <week>   # writes runs/<week>/holdings/batch-N/batch_entities.json
```
Launch one holdings-profiler agent (`agents/holdings-profiler.md`) per batch,
writing `holdings.json` beside each input, then re-run the pipeline to ingest.
The audit warns (W7) on ≥$1B funds/firms with zero holdings.

**Step 3e — deal classification (investable targets).** For investable targets
lacking a moat/outcome tag, generate batch inputs, then launch profiler agents:
```bash
python tools/make_classification_batches.py <week>   # runs/<week>/classification/batch-N/batch_targets.json
```
Launch one deal-classifier agent (`agents/deal-classifier.md`) per batch, writing
`backers.json` + `classification.json` beside each input, then re-run the pipeline.
The audit warns (W8) on ≥$1B investable targets with no `ai_posture`.

**Step 4 — beneficiaries (optional but recommended).** Run the beneficiary-mapper
pass (`agents/beneficiary-mapper.md`) to write `runs/<week>/beneficiaries.csv`, then
re-run `python run_week.py 2026-W32` to link them (idempotent — safe to re-run).

**Step 5 — read the report** at `runs/<week>/weekly_report.md`. Hand
`handoff/capital_map.json` to the dashboard side (see `handoff/RULES.md`).

---

## Fresh clone / new environment — REQUIRED first step
`db/capital.db` is gitignored; `runs/` is the committed source of truth. Before
running any week from a fresh clone or a new machine/agent environment:
```bash
python tools/rebuild_db.py
```
Skipping this produces a handoff containing only the new week's events;
`deliver.py` now BLOCKS such collapsed deliveries (node-count/profile regression
guard) — this rebuild is the fix, not an optional step. (Incident: 2026-W33.)

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

**Step 3f — sub-sector trend narratives (Stage A).** After ingest, generate the
proven-cluster batches, then launch the narrative agents:
```bash
python tools/make_trend_batches.py <week>   # runs/<week>/trends/batch-N/batch_clusters.json
```
Launch one trend-writer agent (`agents/trend-writer.md`) per batch, writing
`trends.json` beside each input, then re-run the pipeline. The mechanical trend
numbers/allocators ship without the agent; the agent adds the grounded narrative.

**Step 0 — build the agent context packs (do this BEFORE launching research agents).**
```bash
python tools/make_research_batches.py <week>
```
Writes `runs/<week>/<agent>/context.json` — the feedback loop: what the engine
already has per entity (search forward from `last_event_date`; `stale_candidates`
needing a Tier-1 confirm), which sources actually yielded recently (`check_first`),
and recent rejects with their lesson. Agents read this first (see agents/CONTEXT.md).

---

# RUNBOOK — running a MONTHLY cycle (the ecosystem map)

Second pipeline, same repo, same database. It answers a different question — *how is the
industry built and who holds it* — and it moves once a month, not once a week. Do not mix
its files with the weekly ones: agents are `agents/eco-*.md`, outputs go to
`runs/<YYYY-MM>/eco-<agent>/`, the orchestrator is `run_month.py`.

## Step 1 — research (the non-deterministic layer)

Launch the six ecosystem agents as subagents from a Claude Code session in this repo.
Same instruction for each, varying only the agent name:

> You are the **<AGENT>** research agent for the Capital Flow **ecosystem** map.
> Read `agents/eco-CONTEXT.md`, then `agents/<AGENT>.md`, then `config/eco_layers.yaml`,
> your slice of `config/eco_watchlist.yaml`, and `config/eco_rules.yaml`.
> Read `runs/<PREVIOUS-MONTH>/rejects.csv` — those rows came back to you for a reason.
> Research standing dependencies for month **<YYYY-MM>** and write `nodes.csv`,
> `edges.csv`, `source_log.csv` and `summary.md` into `runs/<YYYY-MM>/<AGENT>/`.
> Follow the CSV contract in eco-CONTEXT.md exactly. **No verbatim quote, no edge.**

Order does not matter — `eco_ingest` loads every agent's nodes first, then every agent's
edges, so cross-agent references resolve regardless of who ran when.

| agent | layers | goes after |
|---|---|---|
| `eco-silicon` | L1–L4 | materials, tools, EDA, foundries, chips, HBM |
| `eco-systems` | L5, L8–L9 | packaging, boards, networking, optics, servers, cooling, construction |
| `eco-power` | L6–L7 | generation, turbines, nuclear, SMR, transformers, switchgear |
| `eco-infra` | L10 | datacenters, REITs, neoclouds, hyperscalers |
| `eco-models` | L11–L12 | inference, labs, orchestration software, demand |
| `eco-capital` | cross-cutting | `owner` / `capital`: ownership, JVs, project finance, development |

## Step 2 — the deterministic pipeline
```bash
python run_month.py 2026-08
```
Ingest → verify → score → cycles → handoff. Useful flags:

| flag | what it does |
|---|---|
| `--offline` | skip the network verification pass (offline / data-only runs) |
| `--verify-limit=N` | only re-check the first N citations (smoke runs) |
| `--deliver` | copy `handoff/ecosystem_map.json` into `ab-investment/src/data/ecosystemMap.json` |
| `--month=YYYY-MM` | same as the positional argument |

## Step 3 — validate the contract (do this every run)
```bash
python tools/eco_validate.py
```
Exit code 1 on any violation. It checks the things the dashboard cannot defend itself
against: dangling edge endpoints, an edge with empty evidence, `layers` not being exactly
12, an id that does not match `<source>__<target>__<type>`, and every node's `criticality`
reconciling with its own four rubric factors.

## Step 4 — read the diff, not the data
`handoff/ECOSYSTEM-CHANGELOG.md`. That is the whole human step: what appeared, what fell
off, where an owner changed, which edge went dark. If the diff reads fine, the month is
done.

## What "it broke" looks like

| symptom | cause | fix |
|---|---|---|
| Rows in `runs/<month>/rejects.csv` | An agent broke the contract (no quote, search URL, undeclared node, `compete`) | The reason column says exactly which. Hand the file back to that agent next run. |
| `[verify] … N dead` | The page changed or the citation was paraphrased | Open the URL. If the fact still holds, re-quote it verbatim; if not, the edge deserves to die. |
| `[verify] … N blocked/paywalled` | 403/429 — bot wall, not disproof | Nothing to fix. `alive` is left untouched by design. |
| A node shows criticality 0 | Missing rubric factors | Ingest rejects those rows outright, so this means the DB was hand-edited. |
| Cycles count jumps | A new capital edge closed a loop | Expected and interesting — read the note on the cycle. |

## Re-running is safe
`slug` is the key everywhere, so re-running a month updates in place: no duplicate nodes,
no duplicate edges, no duplicate evidence rows. A second identical run reports
`+0 / -0 / ~0` in the changelog. Node ids are permanent — **renaming a slug destroys that
node's history**, so never "tidy" one.
