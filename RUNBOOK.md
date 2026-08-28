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

---

# RUNBOOK — месячный прогон «Экосистема NVIDIA» (v2)

Третий конвейер репозитория. Он **не** продолжение предыдущего месячного: тот отвечал на
вопрос «как устроена цепочка поставок дата-центра» и целиком лежит в
`archive/ecosystem-v1/`. Этот отвечает на другой вопрос — **кто делает NVIDIA
незаменимой, кто заперт в её орбите, кто её шлюзует и чем она хеджируется**.

Не путать файлы: агенты `agents/nveco-*.md`, выдачи `runs/<YYYY-MM>/nveco-<агент>/`,
оркестратор `run_nvidia.py`, файл передачи `handoff/nvidia_ecosystem.json`.

## Шаг 1 — исследование (недетерминированный слой)

Семь слоевых агентов запускаются **параллельно**, восьмой — `nveco-strategic` —
**строго после** них: он читает чужие выдачи и новых сущностей не ищет.

> Ты — исследовательский агент **<АГЕНТ>** карты «Экосистема NVIDIA».
> Прочитай `agents/nveco-CONTEXT.md`, затем `agents/<АГЕНТ>.md`, затем
> `config/nveco_layers.yaml`, `config/nveco_edges.yaml`, свою часть
> `config/nveco_watchlist.yaml` и `runs/<ПРОШЛЫЙ-МЕСЯЦ>/_rejected/<АГЕНТ>.csv`.
> Отработай семишаговый воркфлоу целиком и запиши `entities.csv`, `factors.csv`,
> `edges.csv`, `sources.csv` и `summary.md` в `runs/<YYYY-MM>/<АГЕНТ>/`.
> Железное правило: нет дословной цитаты не длиннее 15 слов — нет связи.

| агент | слои | ориентир |
|---|---|---|
| `nveco-geo` | L0, L15 | 10–14 сущностей |
| `nveco-silicon` | L1–L4 | 18–24 |
| `nveco-systems` | L5, L8, L9 | 16–22 |
| `nveco-power` | L6, L7 | 10–14 |
| `nveco-software` | L10, L11 | 12–16 |
| `nveco-models` | L12, L13 | 14–18 |
| `nveco-capital` | L14 | 10–14 |
| `nveco-strategic` | сквозной, ПОСЛЕ остальных | новых сущностей не заводит |

## Шаг 2 — детерминированный конвейер
```bash
python run_nvidia.py 2026-08
```
ingest → verify → score → cycles → score → handoff. Флаги:

| флаг | что делает |
|---|---|
| `--anchor nvidia` | якорь прогона; по умолчанию из `config/nveco_anchors.yaml` |
| `--offline` | пропустить сетевую проверку ссылок |
| `--verify-limit N` | проверить только первые N ссылок (дымовой прогон) |
| `--deliver` | скопировать файл в `ab-investment/src/data/nvidiaEcosystem.json` |
| `--skip-agents` | принимается ради симметрии; агенты и так вне скрипта |

Оценка гоняется **дважды**: гравитация учитывает число контуров, на которых стоит
сущность, а контуры известны только после `nveco_cycles`. Второй проход дешёвый.

## Шаг 3 — проверка валидатора
```bash
python tools/nveco_corrupt_test.py
```
Портит копию выданного файла тринадцатью способами (висячая ссылка, ребро без
доказательства, цитата в 30 слов, сущность в трёх шагах от якоря, критичность мимо
рубрики, `strength` строкой, поле `dcNode`…) и требует, чтобы валидатор отверг каждый.
Это не декоративный тест: валидатор — единственное, что стоит между битыми данными и
дашбордом.

**Файл, не прошедший валидатор, НЕ ПИШЕТСЯ.** Предыдущий остаётся на месте: вчерашняя
правда лучше сегодняшней лжи. `run_nvidia.py` в этом случае возвращает код 1 и печатает
список нарушений.

## Шаг 4 — прочитать диф
`handoff/ECOSYSTEM-V2-CHANGELOG.md`. Это всё, что требуется от человека: что появилось,
что отвалилось, где связь погасла, какие контуры замкнулись.

## Что значит «сломалось»

| симптом | причина | что делать |
|---|---|---|
| Строки в `runs/<месяц>/_rejected/<агент>.csv` | Агент нарушил контракт | Причина написана в колонке `reason`. Каталог чистится каждый прогон, так что там всегда только свежие отказы. |
| «до якоря N шагов при пределе 2 — вне орбиты» | Сущность не входит в экосистему | Либо найдите ребро, подтягивающее её ближе, либо это правильный отказ. Так из карты честно выпал Carl Zeiss SMT. |
| `[verify] … N мёртвых` | Страница исчезла | Ссылка не удаляет связь, но снимает подтверждение и может уронить статус. Найдите новую или дайте связи упасть. |
| `[score] обрезано N` | Связь без источника тира 1–3 несла `critical` или `strength > 80` | Ожидаемо. Хотите высокую оценку — принесите первичный документ. |
| `КОНТРАКТ НАРУШЕН` | Баг движка или ручная правка БД | Список нарушений печатается; файл не перезаписан. |

## Повторный прогон безопасен
Ключ везде — постоянный id. Второй прогон тех же данных даёт `+0 / -0 / ~0`.
**Переименование id уничтожает историю сущности**, поэтому «причёсывать» их нельзя
никогда.

## Второй якорь
Нужна одна запись в `config/nveco_anchors.yaml` и прогон с `--anchor <id>`. Слои, типы
связей и рубрика от якоря не зависят. Больше в движке ничего «на вырост» нет и делать не
надо.

---

# RUNBOOK — the FUND TRACKER (Section 3, daily)

Different from the other two pipelines: **no research agents.** This section is a
registry, not a discovery loop. Every row traces to a mandated filing or an
official register download, and the whole thing is deterministic Python.

## Required first step — declare yourself to EDGAR

The SEC requires a User-Agent with a real contact address and ≤10 requests/second.
The client **refuses to make a single call without one** rather than send a
fabricated header and get the IP blocked, which would take down the whole section.

```bash
export FUND_SEC_USER_AGENT="Your Name <you@example.com>"
```

Or set `sec.user_agent` in `config/fund_managers.yaml`. The rate limiter is central
(`engine/fund_sec._Limiter`), so every stage shares one budget.

## First run — backfill 8 quarters

Do not stand up an empty system and wait two quarters for it to become useful.
Deltas, persistence and conviction are meaningless on a single period.

```bash
python run_funds.py --backfill
```

Walks full filing history for all 14 managers, parses ~8 quarters of 13F each,
pulls Form ADV, and scans for pre-IPO cap-table mentions. Takes several minutes —
it is rate-limited on purpose. Run it once.

## The normal loop — daily

```bash
python run_funds.py
```

Polls every tracked CIK's submissions JSON, diffs against the last-seen accession,
and ingests anything new **in the same run**. It reacts to disclosures, not to the
calendar. Around the 13F deadlines (~Feb 14 / May 15 / Aug 14 / Nov 14) it widens
its window automatically, because the whole universe files within a few days.

Re-running is always safe: everything keys on accession number.

Useful flags:

| flag | what it does |
|---|---|
| `--offline` | recompute deltas, scores and the payload from what is stored; no network |
| `--adv` | refresh Form ADV records (quarterly is enough) |
| `--crosscheck` | run the 13F vs DEF 14A comparison (network-heavy) |
| `--cap-tables` | full-text search for tracked names in S-1 / DEF 14A holder tables |
| `--deliver` | copy the payload to the dashboard repo — **blocked if the audit fails** |

## What to read after a run

1. `runs/<run-id>/fund_audit_report.md` — errors block delivery, warnings ship listed.
2. `handoff/FUND-TRACKER-CHANGELOG.md` — what is new, what is flagged, what triggered.
3. `handoff/fund_tracker.json` — the payload itself.

Read the **diff**, not the data.

## Listed vehicles — the one assisted step

PSH, TPOU, Greenlight Re and Berkshire publish full portfolios (Greenlight Re
including **shorts**, which no 13F can show) as investor-relations documents whose
layout changes without notice. Rather than parse them blind and print confidently
wrong numbers, drop validated CSVs:

```
runs/<YYYY-MM>/fund-vehicles/holdings.csv       vehicle,as_of,name,ticker,weight,direction,source_doc,note
runs/<YYYY-MM>/fund-vehicles/nav.csv            vehicle,as_of,nav_per_share,currency,mtd_pct,ytd_pct,source_doc
runs/<YYYY-MM>/fund-vehicles/track_record.csv   manager,fiscal_year,return_pct,metric,scope,source_url,note
```

Every row needs a resolvable `source_doc` / `source_url`; rows without one are
rejected by line number. When nothing is supplied the payload **declares the gap**
and states that the manager has fallen back to a 4.5-month-stale 13F.

## What "it broke" looks like

- **`[seed] HALT — CIK mismatches`** — a CIK in `config/fund_managers.yaml` no
  longer resolves to the expected name at EDGAR. Nothing is ingested. Fix the
  config; do not bypass this, it is the guard against silently ingesting a
  stranger's book.
- **`No SEC User-Agent configured`** — see the first step above.
- **`[handoff] CONTRACT VIOLATED — file NOT written`** — the payload broke a hard
  rule (a missing source URL, a missing `latencyDays`, a put in a long feed). The
  previous good file is left in place on purpose.
- **`PARSE FAIL`** lines — a filing that could not be read. It stays visible in
  `fund_filings.parse_status` and in the audit rather than disappearing.
- **Audit `F5`** — a watch-only manager grew a 13F book. The §B3 carve-out has been
  breached and the numbers downstream are wrong.

## Adding a fund

Edit `config/fund_managers.yaml` — that is the only door in. Fill `why_tracked`,
`focus`, `style_tag`, `primary_source` properly; they are stored fields and the
dashboard renders them verbatim. Map every filing CIK under `entities:` or the
manager will read at a fraction of its real size. Then:

```bash
python run_funds.py --backfill
```

Quant managers are refused at seed with an error. That is deliberate.

---

# RUNBOOK — FUND PORTFOLIOS (monthly)

Fills the **ПОРТФЕЛЬ ФОНДА** block on every allocator. Two books, one run.

| | private book | public book |
|---|---|---|
| what | venture / PE stakes the fund owns | 13F marketable positions |
| source | the fund's own portfolio page | SEC EDGAR 13F-HR |
| who | Thrive, Sequoia, Founders Fund, Khosla, MGX | BlackRock, Blackstone, Apollo, Coatue … |
| node key | `holdings[]` | `public_book` |

They are **never merged and never summed**. A firm can have both — Coatue's
privates page and its 13F name two disjoint sets of companies.

## The run

```bash
python run_holdings.py            # current month
python run_holdings.py 2026-08    # a specific month
```

It generates batches, **launches the collection agents itself**, ingests, refreshes
the 13F book, audits and emits. No step waits on a person — that hand-off is what
had never been done, and why 36 funds rendered empty for three weeks.

| flag | effect |
|---|---|
| `--no-agents` | ingest what is already on disk; still fails the run for uncollected batches |
| `--deliver` | copy the payload to the dashboard |
| `--push` | build-gate, then commit and push |

## It needs an agent launcher

The collection step runs a real external program. Resolution order:

1. `$HOLDINGS_AGENT_CMD` — your own runner. Placeholders: `{batch_dir}`,
   `{prompt_file}`, `{brief}`, `{period}`, `{batch}`.
2. the `claude` CLI on PATH, headless `-p` mode.
3. nothing → **the run fails loudly and does not deploy.**

That third case is deliberate. A missing launcher used to be indistinguishable
from a quiet month; both printed `0 portfolios` and shipped green.

## Schedule it

```bash
bash tools/install_holdings_schedule.sh
```

launchd, 22nd of each month at 09:07. The 22nd because 13F filings land ~45 days
after quarter end, so a late-month run also catches the new quarter. launchd rather
than cron because a monthly cron entry silently skips if the machine was asleep,
and a missed fire is a missed month. `--show` prints the plist, `--remove`
uninstalls.

## What makes a run FAIL (rather than ship green)

- a batch input was written and no `holdings.json` came back — a step that did not
  run, reported separately from "0 new holdings"
- no agent launcher available
- `--no-agents` with batches still pending
- audit errors, including **E6**: a ≥$5B fund asked for holdings in two consecutive
  runs and given none

## Depth

`agents/holdings-profiler.md` has always mandated ≥25 holdings per entity. The
pipeline now enforces it: under the floor while the entity's own `holdings_count`
says more exist is an under-delivery — logged as **W9**, and the entity is
re-queued next run. Entities below a **50** coverage target are re-queued too, so
a16z at 49 of 1,458 gets one deeper, relevance-ranked pass rather than counting as
done.

An SPV that genuinely holds one company and discloses it in a single Form D is
**complete at one holding**, not short. And an entity whose batch came back without
it is recorded as `no_disclosure` — researched, nothing public — which never
escalates to E6, because there is nothing to fix.

## Adding an allocator's public book

Edit `config/allocator_ciks.yaml`. `cik: null` with a `reason` is a real answer:
KKR has no current 13F filer (its last was 2013), and recording that stops the
question being reopened every quarter. A node with no filing emits **no**
`public_book` key at all — absent means "not a filer", an empty `positions` array
with a real `filed` date means "filed, held nothing reportable".
