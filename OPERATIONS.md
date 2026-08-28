# OPERATIONS — how this system actually works

**What this file is.** The one place that explains *how the whole thing operates*:
where every number originates, what has to be true before it is allowed to exist,
who computes it, how often, and which rules govern it. Not an index of other
files — the explanation itself.

**How it stays current.** A weekly scheduled pass reconciles this file against
reality (§11). Between passes, anyone changing a source, cadence, contract,
ownership boundary or rule appends a dated line to the Changelog (§12). A rule
that lives only in a chat is a rule that will be broken next month.

**Scope.** Both repos. The engine is the source of truth for most data, but the
dashboard owns some content outright, and splitting the registry would defeat the
purpose.

---

## 1. The shape of the system in one page

```
                    RESEARCH (autonomous, non-deterministic)
   Claude Code agents ── read the web under a source-tier ladder
        │                write CSV/JSON into runs/<period>/<agent>/
        ▼
                    ENGINE (deterministic, Python + SQL)
   validate → resolve entity ids → dedupe → SQLite (db/capital.db)
   → verify every link → score → run signal rules → audit gate
        │
        ▼
                    HANDOFF (one file per map, a contract)
   handoff/*.json ── validated before write; refuses to overwrite good with broken
        │           deliver.py copies into ab-investment/src/data/
        ▼
                    DASHBOARD (render only)
   adapters reshape the payload → React components → Vercel on push to main
```

**The division that matters:** *search is autonomous, output is deterministic.*
Agents may be creative about finding things. Nothing they find becomes a fact
until Python and SQL have validated it. **The database is the single source of
truth** — not the agent output, not the payload, not the dashboard.

### The two repos

| | Engine | Dashboard |
|---|---|---|
| Path | `~/Desktop/Capital Flow` | `~/Desktop/BASE/Code/ab-investment` |
| Repo | `github.com/YV0007/Capital-Flow` | `github.com/YV0007/ab-investment` |
| Job | research, verify, compute, deliver | render |
| Stack | Python + SQLite + agent briefs | React 18 + Vite 5 |
| Output | `handoff/*.json` | Vercel deploy on push to `main` |

**The connection is a handoff, not a live feed.** There is no API between them.
The engine writes a file; `deliver.py` copies it in.

### The zero-latitude rule

**The dashboard computes nothing the engine can compute.** Criticality, gravity,
centrality, concentration, cycles, spine, staleness, SPOF, classification scores
and every aggregate arrive already calculated. The dashboard styles what the file
says; it never overrides a status or invents an entity. Where the dashboard *does*
own content it is named explicitly in §6, and that is the exception.

---

## 2. Four pipelines, one database

`db/capital.db` is shared because **entity identity is shared** — NVIDIA must be
one NVIDIA on every map. `config/aliases.yaml` plus the `entity_aliases` table
guarantee that.

| | **Weekly — Потоки** | **Monthly — Экосистема** | **Registry — Фонды** | **Dashboard-owned** |
|---|---|---|---|---|
| Question | Where did money go this week | Who is structurally irreplaceable, who is locked in, who gates whom | What do the ~14 funds we respect hold right now | Interpretation, and the sections with no engine |
| Unit | A dated **event** | An undated standing **dependency** | A **position / stake / delta** | A read, a news item, a price |
| Universe | Discovery-shaped — agents hunt leads | Anchor-shaped — nothing >2 hops from the anchor | **Closed and curated**, never auto-extended | Fixed list |
| Agents | 6, by allocator class | 8, by stack layer | **none** — fully deterministic | 2 skills |
| Orchestrator | `run_week.py` | `run_network.py` (v3) · `run_nvidia.py` (v2) | `run_funds.py` | npm scripts + skills |
| Tables | `events`, `allocators`, … | `nveco_*` | `fund_*` | — |
| Handoff | `handoff/capital_map.json` | `handoff/ai_ecosystem_network.json` | `handoff/fund_tracker.json` | — |

Shared across all: entity resolution, the source registry, the
`runs/<period>/<agent>/` audit-trail pattern, the handoff pattern, the audit gate.
Separate: tables, agents, rules, schedule. On the dashboard they are unconnected
sections sharing only the shell.

---

## 3. How a claim becomes a fact

The core mechanic of the whole system. Nothing skips it.

### Step 1 — the source-tier ladder

**Two different ladders. Do not confuse them.**

**Weekly pipeline (`config/sources.yaml`) — ranks by officialness:**

| Tier | What | Role |
|---|---|---|
| 1 | SEC EDGAR, company IR, official PRs, portfolio pages, government DBs | **Confirms.** Mandatory to check. |
| 2 | PitchBook, Preqin, AlphaSense, FactSet, Capital IQ, Bloomberg, Dealroom, Crunchbase, Harmonic | Data platforms |
| 3 | Reuters, FT, WSJ, Bloomberg News, The Information | Quality press |
| 4 | SemiAnalysis, Stratechery, conference talks | Specialist analysis |
| 5 | Podcasts, YouTube, X, LinkedIn, blogs | **Lead discovery only.** Never stored as verified. |

**Ecosystem pipeline (`nveco_tiers`) — ranks by closeness to the anchor.** A
partner's press release about NVIDIA is **tier 2 here, not tier 1**, because it is
not NVIDIA speaking about NVIDIA. Same document, different ladder.

*Tier 5 discovers; Tier 1 confirms.*

### Step 2 — the status ladder

Every event carries an honest confidence grade:

| Status | Bar |
|---|---|
| `verified` | A primary source states it. |
| `verified_alpha` | ≥2 **independent** Tier 2–4 sources agree, no Tier 1 yet. |
| `candidate` | A single source, or a Tier-5 lead. |

**Grade honestly, never drop silently.** An unconfirmable item is filed as
`candidate` with the reason in `notes`. *A documented candidate is data; a silent
drop is a miss.* Money that is not firmly committed is at most a `candidate`.

### Step 3 — what the map is allowed to show

Only nodes with **≥1 `verified` or `verified_alpha` flow** reach the visual map;
candidate-only entities live in a watch list. One exception: an entity a fired
signal points at is always included, however small.

### Step 4 — the iron rule (ecosystem map)

An edge exists **only if a verbatim quote of ≤15 words from a resolved document
states the relationship.** No quote, no edge. `nveco_verify` re-fetches *every*
link each run; a dead link costs the edge a confirmation.

### Step 5 — the audit gate

`engine/audit.py` runs on every pass. **Errors block `--deliver` and `--push`.**
Warnings do not — a known weakness: W7 (funds with no holdings) warned for weeks
while runs shipped green. See §10.

### Step 6 — the handoff validator

`*_handoff.py` runs the contract's hard rules before writing and **refuses to
overwrite a good file with a broken one.** Yesterday's truth beats today's lie.
`tools/nveco_corrupt_test.py` proves the validator still bites.

---

## 4. What each pipeline actually does

### 4a. Weekly — Потоки (`run_week.py`, `run.sh`)

Tracks **only capital-allocation events**: equity, funding rounds, follow-ons,
acquisitions, minority stakes, fund launches, SPVs, government grants, project
finance, corporate and sovereign investments. Not news.

```
6 agents by allocator class      corporate · vc · individuals ·
(agents/*.md + CONTEXT.md)       alt-managers · sovereigns · filings
   → runs/<week>/<agent>/{verified_events,candidate_events,source_log}.csv
   → engine/ingest.py        validate → resolve ids → dedupe → SQLite
   → engine/themes.py        signal rules (below)
   → engine/trends.py        windowed sub-sector clustering
   → engine/beneficiaries.py private flows → public tickers
   → engine/classify.py      round_backers + target_classification
   → engine/profiles.py      allocator profiles + track records
   → engine/holdings.py      fund portfolios (the layer below LP flows)
   → engine/aggregates.py    top sector / top company / thesis shares
   → engine/audit.py         gate
   → engine/handoff.py       handoff/capital_map.json + CHANGELOG.md
```

`run.sh` runs the deterministic half only and **build-gates the deploy**: if the
dashboard does not compile, nothing is pushed.

**The signal rules** (`config/rules.yaml`) — what makes a week interesting:

| Rule | Fires when |
|---|---|
| `sector_swarm` | ≥3 distinct **key** allocators put confirmed capital into one sector within 30d. Candidates don't count. |
| `subsector_swarm` | ≥2 key/core allocators converge on one (sector, subsector) — lower bar, 400d lookback, re-checked per window |
| `theme_swarm` | ≥4 key allocators converge on one **theme** across sectors within 30d |
| `capital_acceleration` | A sector's rolling 90d capital ≥2× the prior 90d |
| `first_entry` | A key allocator enters a sector it had no events in for 365d |
| `smart_money_follow` | A key/core allocator enters, then ≥2 others follow within 21d |
| `stealth_accumulation` | ≥3 stakes into one target within 90d |
| `beneficiary_concentration` | ≥3 private flows map to one public ticker |

### 4b. Monthly — Экосистема (`run_network.py`)

Answers a structural question, not a dated one: who is irreplaceable, who is
locked in, who gates whom, what hedges what.

```
8 agents by stack layer     geo · silicon · systems · power ·
(agents/nveco-*.md)         software · models · capital · strategic (runs LAST)
   → runs/<YYYY-MM>/nveco-*/{entities,factors,edges,sources}.csv
   → nveco_ingest.py   validate against FROZEN configs, resolve ids, 2-hop rule
                       (rejects → runs/<month>/_rejected/ — fed back next run)
   → nveco_verify.py   re-fetch EVERY link
   → nveco_score.py    4-factor rubric, spine, status, gravity, HHI
   → nveco_cycles.py   closed loops 3–5 long: sales / financing / lockin
   → nveco_score.py    again — gravity counts the cycles an entity stands on
   → nveco_handoff.py  handoff/ai_ecosystem_network.json + changelog
```

**The map has a centre.** An entity more than **2 hops** from the anchor is
rejected at ingest with a reason. That is the line between "NVIDIA's orbit" and
"the world semiconductor industry". A second anchor costs one config entry and one
run; nothing else in the engine is anchor-aware.

**Five spines, not two:** `physical` · `capital` · `moat` · `control` · `rivalry`.
A moat and a gate are not kinds of supply and not kinds of money — they are
separate mechanics of power. The spine is **derived from the edge type**; neither
the agent nor the dashboard computes it.

**Criticality** is a 4-factor rubric with frozen weights, computed by the engine:
irreplaceability 0.30 · lock-in depth 0.30 · time-to-replace 0.25 · strategic
control 0.15. The engine also ships one line of reasoning per factor
(`criticalityWhy`) — a bare "95" nobody can argue with is the opposite of useful.

**Taxonomy is frozen and single-sourced.** 16 layers, 31 edge types → 5 spines,
6 roles, tiers and statuses live in `config/nveco_*.yaml`, and on the dashboard in
`nvidiaEcosystem.js`, re-exported by the network adapter and never re-typed.
Layers are variable-length; nothing is hard-coded. **That is the acceptance
test** — drop in a new payload and the map changes with no code edit.

### 4c. Registry — Фонды (`run_funds.py`)

Shaped unlike the others: a **closed, curated** list of ~14 managers whose
positions are held as a standing book. **No research agents at all** — every row
traces to a mandated filing or an official register download. No news, no
socials, no aggregators.

```
config/fund_managers.yaml → fund.seed()   every CIK re-verified against EDGAR's own
                                          name for it; a mismatch HALTS the run
   → fund_ingest.poll   diff each CIK's submissions JSON; new accession = ingest
   → fund_13f           information table → positions; value units detected per filing
   → fund_fast          13D/G + verbatim Item 4, Form 3/4/5, material 8-K
   → fund_ark           the daily full book — zero disclosure lag
   → fund_shorts        NAMED shorts from FCA/EU registers (the only attributed shorts)
   → fund_watch         triggers for the four multi-strats (no standing book)
   → fund_deltas        SHARE-based deltas + conviction scores
   → fund_audit         errors block delivery
   → fund_handoff       payload + contract validator
```

**Two problems define this design.**

*Latency.* A 13F is up to 4.5 months stale, so **it is the backbone, never the
heartbeat**. A ladder of faster layers fills the gap — ARK daily · registers
daily · Form 4 ~T+2 · 13D ~T+5 · 8-K live — and `latency_days` is a first-class
field on every dated row. The handoff **refuses to write** an event that lacks it;
a "new position" without its latency is actively misleading.

*Conviction vs noise.* A 13F is a legal aggregation, not a statement of belief.
Handled structurally (`style_tag` / `conviction_weight`; multi-strat 0.0, quant
never ingested) and analytically (`config/fund_conviction.yaml`). **Deltas are
computed on share count, never on value** — a value-based delta invents adds that
never happened.

**The multi-strat carve-out.** There is no separate CIK for a "conviction sleeve"
inside Citadel, and a 13F carries no strategy attribution. Citadel, Millennium,
Point72 and Balyasny are `watch_only`: their 13F is never read. They surface only
on a 13D, a >5% 13G, a Form 3/4, a named short-register entry, or a cap-table
appearance.

**Entity resolution is mandatory, not optional.** Point72 files under six CIKs;
Greenlight under three (its live 13F filer is *DME Capital Management*).
`fund_manager_entities` rolls children to a parent — without it one fund appears
three times at a third of its real size and every conviction score is wrong.

---

## 5. Goals — what each surface is for

Worth stating, because it decides what belongs in each and what does not.

| Surface | The question it answers | Deliberately NOT |
|---|---|---|
| **Потоки** (flow map) | Where did money actually go, who moved first, who followed | A news feed. Only dated allocation events. |
| **Экосистема** (network) | Who is structurally irreplaceable; what breaks if one node fails | A market-share chart. Dependencies, not revenue. |
| **Трекер фондов** | What do respected managers hold with conviction, right now | A trade tape. No churn, no derivatives. |
| **Холдинги** | What is in the portfolio, what moved this week | A recommendation engine. |
| **Fund portfolios** (in the flow map) | Follow smart money down to the exact companies | An index of everything a fund ever touched. |
| **Reads** | Why this deal matters, in one paragraph | New facts. Interpretation of the payload only. |

Platform mission, from `ARCHITECTURE.md`: *discover real capital allocation before
consensus, and map private flows to public beneficiaries.* A Capital Allocation
Intelligence Platform, not a news aggregator.

---

## 6. Data provenance — every feature, every source

### Engine-owned

| Feature | File in dashboard | Contract | Ultimate source | Cadence |
|---|---|---|---|---|
| Capital Flow map | `src/data/capitalMap.json` | — | Agent research over the tier ladder | Weekly |
| Ecosystem map | `src/data/aiEcosystemNetwork.json` | `ai-ecosystem-network/2` | 8 `nveco_*` agents, anchor-relative tiers | Monthly |
| Fund Tracker | `src/data/fundTracker.json` | `fund-tracker/1` | SEC EDGAR 13F-HR / 13D / 13G, FCA/EU short registers | Per filing |
| NVIDIA ecosystem (reserve) | `src/data/nvidiaEcosystem.json` | `nvidia-ecosystem/2` | v2 pilot; **also the frozen taxonomy source** | Frozen |
| Fund portfolios (private book) | `capitalMap.json` → `nodes[].holdings[]` | `agents/holdings-profiler.md` | Fund portfolio pages, Form D, ADV, press releases | **Monthly (planned)** |

> `fundTracker.json` currently carries `fixture: true` — a shape-accurate
> stand-in, not delivered data. **Do not cite its numbers.**

### Dashboard-owned (no engine upstream)

| Feature | File | Source | Cadence | Command |
|---|---|---|---|---|
| Holdings — **news** | `src/data/holdings-v2/<id>.json` → `news[]` | Web, every item with a fetched URL | Weekly | skill `holdings-news-refresh` |
| Holdings — **prices** | same files → `priceChart` | **Yahoo Finance**, 1-year weekly series | Weekly | `node scripts/refresh_prices.mjs` |
| Deal "reads" | `src/data/flowNotes.json` | **The payload only — never the web** | Weekly | skill `capital-flow-reads` |
| Allocator notes | `src/data/allocatorNotes.json` | Dashboard-authored | Ad hoc | — |
| Entity references | `src/data/entityReference.json` | Dashboard-authored | Ad hoc | — |
| Russian overlay | `src/data/capitalMapRu.json` | Hand-maintained over the English payload | Weekly gap check | `npm run cf:ru` |
| Brand logos | `src/data/logoManifest.json` | unavatar / favicon by domain | After each new map | `npm run logos` |

**Two mirror-image rules worth remembering:**

1. **Reads are payload-only.** `capital-flow-reads` writes interpretation from
   facts already in the payload and is *forbidden* from touching the web. Cached
   against the engine's stable `flow.id`, so a read is written once and never
   re-worded.
2. **Holdings news is web-only.** Its exact opposite: every fact must come from a
   page actually fetched. This matters extra because the dataset runs on a forward
   timeline past the model's training cutoff — the live web is the only ground
   truth.

---

## 7. Standing mandates

1. **No fabrication, ever.** Every fact carries a source that was actually
   fetched. No source → it does not ship. An honest gap beats an invented figure.
2. **Quotes are verbatim and ≤15 words.**
3. **IDs are stable across runs.** Renaming an id loses history.
4. **The map is cumulative memory, not a snapshot.** Stale entities are
   de-emphasised, not deleted; two consecutive stale handoffs with no verified
   flow before anything drops.
5. **Empty ≠ zero.** A field that did not arrive is not drawn at all — no label,
   no em dash. An empty block reads as "we found nothing" when it usually means
   "this field does not apply".
6. **`npm run build` gates every deploy.** If it fails, nothing is pushed.
7. **Never read a full data JSON into context** — 200 KB to 2 MB each. Grep
   first, then read with offset/limit.
8. **Prices are computed, never typed.** A price a model wrote is a fabricated
   figure even when it happens to be right.
9. **Never commit `index_slim.html`** — the gitignored source monolith.
10. **Bilingual UI:** strings go through `t(ru, en)`. **Never call `t()` at module
    scope** — it runs at import time before any component supplies it, throws a
    `ReferenceError`, and takes the whole bundle down (blank page, 2026-08-24).

---

## 8. Feature-specific rules

### Fund portfolios — conviction holdings only

The block answers one question: **what does this fund own and believe in right
now?**

- **Not trades.** `shares > 0` is a hard gate; an `exited` position is not a
  holding. Trade flow, if wanted, gets its own array.
- **Not derivatives.** Owned shares only — no puts, calls, warrants, rights,
  convertible notes, SPAC units, or anything reported as `PRN`. ADRs count as real
  ownership. 13F reports options at the **notional value of the underlying**, so
  one call can poison `total_value_usd` and every weight derived from it.
- **Ranked by weight** — size is the conviction signal.
- **13F cannot serve VC funds.** Thrive, Sequoia, Founders Fund and Khosla hold
  private companies that appear in no 13F. Portfolio pages are the source.
- **Depth floor:** ≥25 holdings where the true total exceeds 25.

### Holdings prices

`current`, `change` and `points[]` are **one coupled object** — `change` is
measured from the first weekly close to the displayed price, and the chart's last
point *is* that price. Editing one by hand desyncs all three. Only
`scripts/refresh_prices.mjs` touches them. Symbols are pinned in its `SYMBOLS` map
so the figure stays comparable week to week: Brookfield tracks **BN** not BAM;
SoftBank the **US ADR** so the card stays in dollars; Pershing the **USD line**
because `PSH.L` quotes in pence. Series are split-adjusted, so occasional large
but correct jumps against old hand-entered values are expected.

### Signals and prose

The engine owns Russian signal prose, structured `rule_params` and resolved
evidence. Route signal-shape requests upstream rather than reshaping them in the
dashboard.

---

## 9. Cadences at a glance

| When | What | Trigger |
|---|---|---|
| Weekly | Capital Flow map — agents, ingest, signals, handoff, deploy | Cloud routine + `run.sh` |
| Weekly | Holdings news + prices; deal reads; RU gap check | Skills, Mon 08:00 UTC |
| Weekly | **This file** — reconcile against reality (§11) | Scheduled ops pass |
| Monthly | Ecosystem map | `run_network.py` |
| Monthly (planned) | Fund portfolios | `run_holdings.py`, 20th or later |
| Per filing | Fund Tracker — poll EDGAR submissions, ingest on new accession | `run_funds.py` |
| After each new map | Logo pipeline for new entities | `npm run logos` |

---

## 10. Known gaps

| Gap | Detail | Owner |
|---|---|---|
| Fund portfolios: 36 of 43 empty | Collection step is manual and was skipped — batches generated W33 (0 run), W34 (3 of 4), W35 none. See `CAPITAL-FLOW-FUND-PORTFOLIOS.md` | Engine |
| Fund portfolios: the 7 that work are thin | Coatue 16/250, a16z 49/1458 — below the mandated 25 | Engine |
| **Warnings do not block** | The audit gate blocks on errors only. W7 warned for weeks while runs shipped green — that is how the above stayed invisible | Engine |
| `fundTracker.json` is a fixture | Real payload pending | Engine |
| i18n incomplete | ~1,400 untranslated string sites across ~68 files; ecosystem map, funds, holdings, YC tracker, DC roadmap largely Russian-only | Dashboard |
| Holdings news is Russian-only | `news[].title/text` are data, not UI — needs translated fields or a translation step | Both |
| Ecosystem cycle-lens camera | Lit circuit can land off-screen on lens open; «Восстановить вид» fixes it | Dashboard |

---

## 11. How this file stays accurate

**Weekly, not per-change.** Updating after every edit would be noise; a week is
short enough that nothing important goes unrecorded and long enough to be worth a
pass.

**Weekly is accurate enough only because the pass is evidence-derived, not
recalled.** The sections split into two kinds:

- **Machine-checkable** — §6 provenance (contract, source, fixture flag,
  generated date), §9 cadences, §10 gaps. `python tools/ops_check.py` reads the
  real payload headers, the real audit warnings and both repos' git logs, and
  prints any line in this file that no longer matches reality. The weekly pass
  fixes exactly what it flags.
- **Judgement** — §3 the fact ladder, §5 goals, §7 mandates, §8 rules. These
  change only when a person decides they change. The weekly pass never rewrites
  them; it *proposes* a diff from the week's commits and asks.

**The changelog is append-only.** The pass never edits a past entry — a wrong old
line is corrected by a new line saying so, so the history of how we operated stays
readable.

---

## 12. Changelog

Append a dated line for every change to a source, cadence, contract, ownership
boundary or rule. Newest last. Never edit a past entry.

- **2026-08-24** — Fixed a site-wide blank page: `t()` called in module-level
  constants ran at import time and threw. Mandate 10 added.
- **2026-08-25** — Holdings prices moved from hand-maintained to
  `scripts/refresh_prices.mjs` (Yahoo Finance, 1-year weekly). Promoted from
  "optional, leave alone" to a required weekly step.
- **2026-08-25** — Copy: «миноритарная доля» → «доля без контроля» in
  `capitalMap.js` `EVENT_TYPE_META` and the home-page labels.
- **2026-08-25** — Fund portfolios: diagnosed why 36 of 43 allocators are empty.
  Specified a monthly `run_holdings.py` that launches the profiler agents itself.
  Added the conviction-holdings and no-derivatives mandates. Handoff:
  `CAPITAL-FLOW-FUND-PORTFOLIOS.md`.
- **2026-08-27** — Rewritten from an index of pointers into an explanation of the
  operating model: the six-step "how a claim becomes a fact" ladder, all four
  pipelines with their real stages, the signal-rule table, the goals table, and
  the two source ladders and why they differ. Added §11 and a weekly reconcile
  pass backed by `tools/ops_check.py`.
