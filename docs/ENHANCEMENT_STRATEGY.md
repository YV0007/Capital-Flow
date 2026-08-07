# Capital Flow — Enhancement Strategy & Roadmap
*How we turn a working prototype into a professional-grade capital-flow tracker that
doesn't miss flows, produces credible actionable data, and runs strong due diligence
from weak leads.*

---

## 0. The north star (read this first)

We are building **an intelligence platform, not a news scraper**. The bar is the one
professional desks hold: **coverage** (we don't miss material flows), **credibility**
(every claim carries a defensible confidence grade and a primary trail), and
**timeliness** (we see allocation before consensus prices it).

Three properties define "done well," and everything below serves them:

1. **Don't miss flows** → systematic coverage, not opportunistic search.
2. **Credible, actionable data** → a real confidence model + entity resolution, so a row
   can be traded on, not just read.
3. **Strong due diligence from a weak lead** → agents that escalate a rumor to a verdict
   instead of checking one filing and quitting.

**The strategy vector in one line:** move from *opportunistic per-name web search with a
3-tier status* → to *a systematic, source-complete, entity-resolved capital-flow graph
with a graded confidence model and an investigative escalation loop.*

---

## 1. Where we are today — honest audit

**What's genuinely good:** the separation of concerns (autonomous research → deterministic
pipeline), the CSV contract, dedupe-on-ingest, the tiered-source discipline, the
signal-rule pattern, the network layer, and the handoff/deploy loop. The foundation is
sound and extensible.

**The seven structural gaps** (each maps to a workstream in §3):

| # | Gap | Symptom today |
|---|-----|---------------|
| G1 | **Universe is hand-curated & partial** | We track who we listed; we miss allocators we never named. |
| G2 | **Coverage is opportunistic, not systematic** | Agents search per-name and stop; no "expected vs found" reconciliation, so a missed 8-K is invisible. |
| G3 | **Detection is prose-driven, not structured** | Amounts/roles/instruments are captured ad hoc; no lead/participant, instrument, stage, currency normalization. |
| G4 | **Entity resolution = string equality** | `allocators.name UNIQUE`. "BlackRock" ≠ "BlackRock / GIP" ≠ "GIP"; a person ≠ their fund. Flows fragment or collide. |
| G5 | **Classification too coarse** | 12 buildout sectors, no theme layer, no sub-industry — real deals fall outside (we saw `ai-applications` warnings). |
| G6 | **Confidence is a 3-value label** | `candidate/verified_alpha/verified` has no axes, no score, no corroboration logic — can't rank or defend. |
| G7 | **Agents quit early** | "Checked SEC, found nothing → done." No escalation from weak lead, no alt-data, no out-of-box moves. |

---

## 2. What the professionals do — techniques worth stealing

Distilled from how the category operates (PitchBook, AlphaSense/Sentieo, CB Insights,
Crunchbase, Harmonic, Dealroom, Diffbot, Kensho, Fintel/WhaleWisdom, OpenCorporates/GLEIF)
and from intelligence/OSINT tradecraft:

- **Systematic ingestion beats search.** The leaders pull *every* filing/feed and extract,
  rather than searching per-entity. Coverage is a pipeline property, not an agent's luck.
  → **EDGAR full-text + submissions APIs, Form D, 13D/G, Form 4, 8-K feeds as a standing net.**
- **A canonical entity graph with external IDs.** They resolve every name to a stable ID and
  attach LEI / CIK / ticker / registry IDs, then link parents↔subsidiaries↔vehicles.
  → **GLEIF LEI ↔ OpenCorporates mapping is free and open** and solves most of G4.
- **Event/relation extraction into a fixed schema**, not free text — deal, parties, role,
  instrument, amount, stage, date — so records are comparable and queryable.
- **Two-axis, graded confidence.** Intelligence orgs use the **Admiralty/NATO AJP-2.1**
  scale: **source reliability A–F** × **information credibility 1–6**, kept independent
  (a reliable source can carry a bad report; a shaky source can be later confirmed).
  → We map this to a numeric score and derive status from it.
- **Corroboration, not repetition.** They discount *circular reporting* (ten outlets citing
  one origin) and reward **independent** confirmation, primary over secondary.
- **Structured analytic techniques.** Analysis of Competing Hypotheses (ACH) and a
  key-assumptions check turn "sounds real" into a defensible verdict.
- **Alt-data front-runs disclosure.** Hiring surges, datacenter permits & power-interconnect
  queues, domain/trademark registrations, GitHub/website changes, shipping/customs, patents —
  these move *before* the capital is disclosed.
- **Completeness guarantees.** Pros measure and alarm on coverage gaps (expected filings not
  seen, entities not refreshed) — the opposite of hoping search caught everything.

*Sources for the current specifics used below:*
[SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) ·
[EDGAR full-text search](https://www.sec.gov/edgar/search/) ·
[NATO AJP-2.1 / Admiralty scale (SANS)](https://www.sans.org/blog/enhance-your-cyber-threat-intelligence-with-the-admiralty-system) ·
[GLEIF ↔ OpenCorporates LEI mapping](https://www.gleif.org/en/lei-data/lei-mapping/download-oc-to-lei-relationship-files)

---

## 3. The enhancement workstreams

Each workstream: **target state → concrete plan → data changes → owner-split**.
Owner is **[C] Claude-executable** (I can build it; prompt in the appendix) or
**[D] Decision-required** (your call before I build).

### WS1 — Addressable universe expansion (fixes G1)
**Target:** the watchlist is a living, self-extending set, not a static list.
**Plan:**
- **Discovery loop:** every run, agents propose *new* allocators seen co-investing with
  tracked names → they land in a `candidates` universe → you promote to the watchlist. This
  is how the universe grows without manual curation. **[C]**
- **Structured universe by class + role + geography**, with explicit inclusion criteria per
  class (e.g. "any fund that led ≥1 AI round >$50M in 12 mo"). **[D]** (criteria are yours)
- **Vehicles, not just principals:** track a principal *and* their vehicles (Thiel → Founders
  Fund, Thiel Capital, Mithril) as linked entities so personal vs firm capital both count. **[C]**

### WS2 — Source coverage & "never-miss" (fixes G2)
**Target:** coverage is systematic and *measured*; a missed material filing raises a flag.
**Plan:**
- **Standing EDGAR net:** poll `data.sec.gov/submissions/{CIK}.json` per tracked public
  entity and the **EDGAR full-text search** for private-side signals (Form D, 8-K item 1.01/
  2.01, 13D/G, Form 4), on the **10 req/s** fair-access limit with a User-Agent. This is a
  deterministic sweep the agents *augment*, not replace. **[C]**
- **Expected-vs-found reconciliation:** for each allocator, define the source checklist it
  *should* have been checked against; `source_log` already records what *was* checked; compute
  a **coverage score** and list unchecked mandatory sources as gaps in the weekly report. **[C]**
- **Feed layer:** add RSS/streaming (EDGAR filing feeds, PR wires, gov grant DBs) so new
  disclosures are caught on arrival, not on next weekly search. **[C]**
- **Non-US registries:** UK Companies House, EU registries via OpenCorporates, for sovereign
  and cross-border flows. **[C]** (API access = **[D]** if paid tiers needed)

### WS3 — Capital detection & extraction exactness (fixes G3)
**Target:** every event is a fully-structured record, not a sentence.
**Plan — extend the event schema** with: `capital_role` (lead/participant/sole),
`instrument` (equity/SAFE/convertible/debt/grant/JV), `stage` (seed…series X/growth/PE),
`round_total_usd` (vs this allocator's slice), `currency` + `amount_usd_normalized`,
`committed_vs_announced`, `ownership_pct`, `valuation`, `co_investors[]`. **[C]**
- **Extraction discipline in the briefs:** agents fill the structured fields explicitly and
  quote the source snippet that supports the amount. **[C]**
- **FX normalization** in the pipeline (store native + USD). **[C]**

### WS4 — Entity resolution & the capital graph (fixes G4)
**Target:** one canonical entity per real-world actor, with external IDs and relationships.
**Plan:**
- **Canonical entity table + alias table + external-ID table** (`lei`, `cik`, `ticker`,
  `opencorporates_id`). Resolve on ingest via alias match → external-ID match → fuzzy. **[C]**
- **GLEIF↔OpenCorporates mapping** (free, bi-weekly CSV) to attach LEIs and parent/subsidiary
  links; `data.sec.gov` for CIK↔ticker. **[C]**
- **Relationship edges:** principal→vehicle, parent→subsidiary, fund→GP, so "BlackRock",
  "GIP", "BlackRock/GIP" collapse correctly and personal-vs-firm stays distinct-but-linked. **[C]**

### WS5 — Classification taxonomy (fixes G5)
**Target:** a deal is placed on the right sector *and* theme *and* sub-industry.
**Plan:**
- **Two dimensions, not one:** keep `sector` (structural, ~15 slugs incl. an
  `ai-applications` / `ai-infrastructure` split) **and add `theme`** (cross-cutting:
  frontier_ai, defense_ai, energy_for_ai, robotics, sovereign_ai…), because network signals
  and consensus form around *themes*, not just sectors. **[D]** (taxonomy is a judgment call)
- **Canonical taxonomy file** the agents map to, with a controlled "unknown→closest + flag"
  path (already partly there). **[C]**

### WS6 — Due-diligence & the confidence model (fixes G6 + G7 core)
**Target:** every row carries a **graded, defensible confidence**, produced by an
**escalation loop** that can start from a weak lead. This is the heart of "strong DD."
**Plan — adopt an Admiralty-style two-axis model, implemented in code:**

- **Source reliability (A–E)** ← derived from our source tiers:
  A = primary/official (SEC, IR, gov DB); B = top data platform / regulator-adjacent;
  C = quality press; D = specialist/analyst; E = social/rumor.
- **Information credibility (1–5)** ← corroboration logic:
  1 = confirmed by independent primary; 2 = corroborated by ≥2 **independent** sources;
  3 = single credible source, plausible; 4 = uncorroborated, not implausible; 5 = doubtful/
  contradicted.
- **Combined → status + score:** e.g. A1/A2/B1 → `verified`; B2/C1/C2 → `verified_alpha`;
  else `candidate`. Store the letter-number grade **and** a 0–100 score for ranking. **[C]**
- **Circular-reporting guard:** agents must identify the *origin* of a claim; N outlets citing
  one origin = one source, not N. **[C]** (brief rule) / **[C]** (store `origin_id`)
- **The escalation loop (the "don't quit" engine):** a lead enters at E/4–5 and the agent runs
  the **verification playbook** (§6) to climb the grade, or documents why it can't and files it
  as `candidate` with the grade — never a silent drop. **[C]**

### WS7 — Signal & detection intelligence (extends the alpha)
**Target:** more, and smarter, pre-consensus signals.
**Plan — add rules** (pattern already supports it): `smart_money_follow` (tier-1 enters →
others follow within N days), `stealth_accumulation` (multiple small stakes → one target),
`beneficiary_concentration` (many private flows → one public supplier), `cross_network_coinvest`,
`theme_rotation` (capital shifting between themes), plus finishing the declared network rules
(repeat_conviction, defense_convergence, private_to_public_spillover). **[C]**
- **Alt-data early-warning inputs (WS2 feeds these):** hiring surges, datacenter permits /
  power-interconnect queues, domain/trademark filings → a `pre_signal` that front-runs
  disclosed capital. **[C]** build / **[D]** which alt-data sources to buy vs scrape.

### WS8 — Agent methodology / out-of-box playbooks (fixes G7)
**Target:** agents that investigate, not agents that look up. Covered in depth in §6.

---

## 4. Database expansion plan (what to add & why)

| New table / column | Why (which gap) |
|---|---|
| `entities` (canonical) + `entity_aliases` + `entity_external_ids` (lei/cik/ticker/oc_id) | G4 — one actor = one node; kill fragmentation & collisions |
| `entity_relationships` (principal→vehicle, parent→sub, fund→GP) | G4/WS1 — personal vs firm capital both counted, correctly linked |
| events: `capital_role, instrument, stage, round_total_usd, currency, amount_usd_normalized, ownership_pct, valuation, committed_vs_announced` | G3 — structured, comparable, queryable deals |
| events: `source_reliability (A–E), info_credibility (1–5), confidence_score (0–100), origin_id` | G6 — graded, defensible, rankable confidence + circular-reporting guard |
| `themes_taxonomy` + events.`theme` | G5 — signals form around themes |
| `coverage` (allocator × source × run × checked/found) | G2 — measure completeness, alarm on gaps |
| `universe_candidates` (discovered allocators awaiting promotion) | G1 — self-extending universe |
| `pre_signals` (alt-data early warnings) | WS7 — front-run disclosure |
| `leads` (raw weak leads + escalation trail) | G7 — nothing dropped silently; DD is auditable |

All additive and backward-compatible with the current pipeline.

---

## 5. Per-agent expanded playbooks (the "dig deeper per agent" ask)

Common upgrade for **every** agent: (1) work a **source checklist** and log checked-vs-found
(WS2); (2) fill the **structured fields** (WS3); (3) grade every row on the **two-axis model**
(WS6); (4) run the **escalation loop** before dropping a lead (§6); (5) propose **new
allocators** seen co-investing (WS1).

- **Corporate** — beyond 8-K/10-Q/IR: CVC arm sites (M12, GV, NVentures, Intel Capital), HSR/
  antitrust filings for M&A, earnings-call transcripts (capex→named projects), and *compute-
  commitment* contracts (a corporate's real "allocation" is often contracted capacity). Separate
  parent vs CVC vehicle. Out-of-box: reverse a *beneficiary's* customer list into who's funding it.
- **VC** — round-announcement angel/lead lists, portfolio pages, **Form D** for the issuer,
  fund-close filings, and secondary sources (The Information, Axios Pro). One row per participant.
  Out-of-box: new-fund SEC Form D + LP press → future dry powder; job-post surges at portfolio cos.
- **Individuals** — already upgraded (round-angel-lists first, Form D related-persons, ~45d
  window, `verified_alpha` norm). Add: single-principal family-office vehicles, personal SPVs,
  and **network coinvestment** flags feeding convergence. Out-of-box: a member's *vehicle* moving
  is a personal-conviction proxy even when the personal check isn't disclosed.
- **Alt-managers** — fund PRs, IR decks, LP letters (when public), ADV, and the **debt** behind
  infra deals (project-finance notes, 8-Ks, rating-agency actions). Committed-vs-target flagged.
  Out-of-box: power-interconnect queues & datacenter permits reveal the deal before the close PR.
- **Sovereigns** — official gov/fund releases, annual reports, CHIPS/DoE/DoD programs, grant DBs.
  Separate headline pledge from committed capital. Out-of-box: co-investment vehicles (MGX+fund),
  and foreign-registry filings for the SPV.
- **Filings** — the systematic net (WS2): sweep EDGAR feeds for *all* tracked entities, upgrade
  other agents' candidates to `verified` with the primary filing, and discover missed events.
  Out-of-box: 13F deltas quarter-over-quarter, Form 4 clusters, S-1 "use of proceeds".
- **Beneficiary-mapper** — add supplier-graph reasoning (target → named suppliers → public
  tickers), confidence per hop, and `beneficiary_concentration` detection.

---

## 6. The verification playbook (weak lead → verdict) — the DD core

Give every agent this escalation loop, run *before* a lead is dropped:

1. **Locate the origin.** Find the *first* source of the claim. Multiple outlets citing it =
   still one source (circular-reporting guard).
2. **Primary-source hunt.** Try in order: SEC **Form D** (+ related persons), **8-K/13D-G/Form 4**,
   company PR/IR/blog (+ **Wayback** for silent edits), official gov DB.
3. **Registry & legal.** OpenCorporates entity + new subsidiaries/SPVs, state business filings,
   **UCC** liens (debt), court/PACER, HSR/CFIUS for large/foreign deals.
4. **Corroborating exhaust.** LinkedIn headcount/role changes, **job postings** (hiring for the
   funded initiative), domain/trademark registration, GitHub/website changes, permits/procurement
   (datacenters/energy), customs/shipping (hardware).
5. **Triangulate.** Require ≥2 **independent** confirmations for `verified_alpha`; a primary for
   `verified`. Note contradictions.
6. **ACH check.** For a material claim, list competing explanations ("real new capital" vs "old
   round resurfaced" vs "mark-to-market" vs "PR spin") and pick the one the evidence best fits.
7. **Grade & record.** Assign source-reliability × info-credibility, compute score, set status.
   **If it can't be confirmed, file it as `candidate` with the grade and the reason — never a
   silent drop.**

**"Don't give up yet" moves:** reverse from the beneficiary; check the *vehicle* not just the
person; look for the *debt* behind the equity; diff quarterly 13Fs; read the Form D *amendments*;
check the counterparty's filings (the other side often discloses); use Wayback on a deleted page.

---

## 6a. EXECUTION STATUS (updated 2026-08-07)

**Shipped:**
- ✅ **C1** two-axis confidence (A–E × 1–5 + 0–100 score) on every event — `257c599`
- ✅ **C2** entity resolution v1 (alias collapse, principal→vehicle links, ID enrichment) — `10a7fdf`
- ✅ **C4** agent DD upgrade (escalation loop, circular-reporting guard, universe discovery) — `7812b37`
- ✅ **C6** three new signals (smart-money-follow, stealth-accumulation, beneficiary-concentration) — `93f35ad`
- ✅ **WS5** theme dimension + `theme_swarm`; **C5** coverage reconciliation; taxonomy closed (0 warnings) — `2bbd126`
- ✅ **D2** theme taxonomy set (10 themes); **D3** map confidence floor = 60

**Effect on 2026-W32:** signals went **2 → 12**; every event classified on sector *and*
theme; coverage now measured (16/46 key+core produced events, 30 silent and listed).

- ✅ **WS2+C7** standing EDGAR net (`engine/edgar.py`) + `leads` & `coverage` tables — `a8cb909`
- ✅ **C3** structured deal fields; **network rules** repeat_conviction + defense_convergence — `e34ab26`

**Everything in the Now/Next roadmap is shipped.** Remaining (Later phase, deliberately
deferred): WS7 alt-data pre-signals (hiring, permits, power-interconnect queues), GLEIF/LEI
bulk enrichment, non-US registries, `fellowship_breakout` (needs alumni-round modeling),
and C5-full per-allocator expected-vs-found (needs agents to log allocators checked — the
`coverage` table and EDGAR half already do this; the agent half lands on the next run).

## 7. Roadmap — Now / Next / Later

**Now (highest leverage, low regret):**
1. **Confidence model** (WS6) — two-axis grade + score + status mapping. *Biggest credibility jump.*
2. **Entity resolution v1** (WS4) — canonical entities + aliases + LEI/CIK/ticker via GLEIF/EDGAR.
3. **Structured event fields** (WS3) — role/instrument/stage/round-total/currency.
4. **Verification playbook** into all briefs (WS6/§6) + **new-allocator discovery** (WS1).

**Next (systematic coverage):**
5. **Standing EDGAR net + coverage reconciliation** (WS2) — the "never-miss" layer.
6. **Theme dimension + taxonomy** (WS5).
7. **New signals** (WS7): smart-money-follow, stealth-accumulation, beneficiary-concentration.

**Later (edge & moat):**
8. **Alt-data pre-signals** (WS7/WS2) — hiring, permits, power queues.
9. **Non-US registries & feeds** (WS2).
10. Finish the declared network rules and the capital graph (WS4).

---

## 8. Action register — owner split

### [C] Claude can build now (prompts in §9)
- C1 Confidence model (two-axis grade, score, status mapping) + schema cols
- C2 Entity resolution v1 (entities/aliases/external-ids tables + resolver + GLEIF/EDGAR IDs)
- C3 Structured event fields + FX normalization
- C4 Verification-playbook + new-allocator-discovery into all agent briefs
- C5 Standing EDGAR net + coverage reconciliation (deterministic sweep)
- C6 New signal rules (smart-money-follow, stealth-accumulation, beneficiary-concentration)
- C7 `leads` + `universe_candidates` tables and the promotion flow

### [D] Decisions only you can make
- D1 **Universe inclusion criteria** per class (the rule that admits a new allocator)
- D2 **Theme taxonomy** — the canonical theme list (frontier_ai, defense_ai, energy_for_ai…)
- D3 **Confidence thresholds** — exact grade→status cutoffs and the min-score to surface on the map
- D4 **Alt-data sourcing** — which feeds to buy (PitchBook/Harmonic/permits data) vs scrape free
- D5 **Non-US scope** — how far beyond US filings to go now
- D6 **Cadence per class** — continuous vs weekly vs event-driven (your `tracking_mode` field)

---

## 9. Ready-to-run prompts (paste to a Claude Code session in the repo)

**C1 — Confidence model**
> In the Capital Flow repo, implement an Admiralty-style two-axis confidence model. Add
> `source_reliability` (A–E), `info_credibility` (1–5), `confidence_score` (0–100) and
> `origin_id` to the events schema. Derive reliability from source tier and credibility from
> corroboration count (independent sources). Map grade→status (A1/A2/B1→verified; B2/C1/C2→
> verified_alpha; else candidate). Update ingest.py to compute and store these, update the
> report and handoff to show the grade+score, and add tests. Keep it backward-compatible.

**C2 — Entity resolution v1**
> Add canonical entity resolution to Capital Flow. Create `entities`, `entity_aliases`, and
> `entity_external_ids` (lei, cik, ticker, opencorporates_id) tables and a resolver used at
> ingest (alias → external-id → fuzzy). Load the free GLEIF↔OpenCorporates LEI mapping and
> data.sec.gov CIK↔ticker to attach IDs. Add `entity_relationships` (principal→vehicle,
> parent→subsidiary) so "BlackRock"/"GIP"/"BlackRock/GIP" collapse and personal-vs-firm stay
> linked-but-distinct. Migrate existing allocators. Tests + smoke test must pass.

**C3 — Structured event fields**
> Extend the Capital Flow events schema with capital_role, instrument, stage, round_total_usd,
> currency, amount_usd_normalized, ownership_pct, valuation, committed_vs_announced, co_investors.
> Add FX normalization in the pipeline. Update the CSV contract in agents/CONTEXT.md and all six
> briefs to fill these explicitly and quote the source snippet supporting each amount. Tests.

**C4 — Agent DD upgrade**
> Rewrite each agents/*.md brief to include the verification playbook (weak-lead → verdict) from
> docs/ENHANCEMENT_STRATEGY.md §6, the two-axis grading step, the circular-reporting guard, and a
> "propose new allocators seen co-investing" step. Keep CONTEXT.md as the shared spec; make each
> brief's class-specific source checklist and out-of-box moves concrete.

**C5 — Standing EDGAR net + coverage**
> Build a deterministic EDGAR sweep in engine/: poll data.sec.gov/submissions/{CIK}.json for
> tracked public entities and efts.sec.gov full-text for Form D / 8-K(1.01,2.01) / 13D-G / Form 4,
> respecting the 10 req/s limit with a User-Agent. Write found events into the run as a `filings-
> auto` source. Add a `coverage` table + expected-vs-found reconciliation and surface gaps in the
> weekly report. Tests.

**C6 — New signals**
> Add these signal rules to engine/themes.py + config: smart_money_follow (a key/core allocator
> enters a sector, then ≥2 others within N days), stealth_accumulation (≥3 small stakes into one
> target in a window), beneficiary_concentration (≥N private flows mapping to one public ticker).
> Store as themes with evidence + strength. Tests + update the report/handoff.

---

*This document is the plan of record. Update it as workstreams land. Start point recommended:
C1 (confidence) → C2 (entities) → C4 (agent DD) — that trio moves credibility, correctness, and
coverage the most for the least risk.*
