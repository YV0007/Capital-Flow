# Ecosystem engine — how it works

One file, everything. Covers what the map is, what it looks for, where the data
comes from, how it is scored, how it updates, and what ships.

Two pipelines stacked. **v2** builds the anchor map around NVIDIA
(`run_nvidia.py`). **v3** builds the network on top of it from 27 equal pivots
(`run_network.py`). v3 reads v2's output as a seed and never rewrites it.

---

## 1. The approach

**The question the map answers:** who cannot be replaced in AI infrastructure,
and what breaks if they disappear.

Not "who supplies whom". Three design choices follow from that:

| choice | why |
|---|---|
| Relationships are typed by **mechanism**, not by direction of goods | A supply, a lock-in and an export gate are different kinds of power. One arrow colour would lie. |
| Every edge needs a **verbatim quote** | Without it the map is opinion. See §4. |
| The engine computes scores, agents supply **facts** | An agent that could set its own criticality would set it high. |

**Inclusion rule:** an entity must be within **2 hops** of a pivot. One hop is a
direct relationship; two is a relationship with someone who has one. Three hops
is "the global semiconductor industry", not one company's orbit. The ingest
rejects anything further, with a reason — it never drops silently.

---

## 2. What it covers

**16 layers on 3 planes.** The plane is the geometry of the map, not decoration.

| plane | layers | meaning |
|---|---|---|
| `orbit` | L1–L13 | the stack itself, a ring |
| `nucleus` | L14 Capital | owns and funds the stack without standing in it |
| `control` | L0 Geopolitics, L15 Regulation | gates the stack from outside |

```
L0  Geopolitics     jurisdictions, access control
L1  Inputs & tools   materials, fab equipment
L2  Chip design      EDA software, IP licences
L3  Fabs             lithography, process
L4  Memory           HBM, DRAM, storage
L5  Systems          assembly, servers, racks
L6  Power            generation, transmission
L7  Cooling          heat, water, liquid
L8  Networking       fabric, optics, switching
L9  Infrastructure   sites, clouds
L10 GPU software     CUDA, frameworks
L11 Inference        serving, orchestration
L12 Frontier labs    models, training
L13 Applications     AI in business, verticals
L14 Capital          who owns and funds it
L15 Regulation       rules, subsidies, standards
```

Putting the USA between "memory" and "systems" would be a lie about the nature
of the relationship — Commerce supplies NVIDIA nothing, it decides who NVIDIA
may sell to. Hence the separate `control` plane.

**38 sectors** sit under the layers (`foundry`, `hbm`, `neocloud`,
`export_authority`, …). They are the map's own taxonomy — nothing points at an
external classification.

**10 tech nodes** are technologies, not companies: EUV, N3, CoWoS, HBM, NVLink,
InfiniBand, Spectrum-X, Arm ISA, PCIe. They ride on an edge as a label
explaining *why* a dependency is unbreakable.

---

## 3. The agents

Eight Claude Code subagents. Seven cover layers, one synthesises. They are the
only non-deterministic part of the system and they run **before** any Python.

| agent | layers | target size |
|---|---|---|
| `nveco-geo` | L0, L15 | 10–14 entities |
| `nveco-silicon` | L1–L4 | 18–24 |
| `nveco-systems` | L5, L8, L9 | 16–22 |
| `nveco-power` | L6, L7 | 10–14 |
| `nveco-software` | L10, L11 | 12–16 |
| `nveco-models` | L12, L13 | 14–18 |
| `nveco-capital` | L14 | 10–14 |
| `nveco-strategic` | — | cross-cutting, runs **last** |

Each reads `agents/nveco-CONTEXT.md`, then its own brief, then its slice of
`config/nveco_watchlist.yaml` (a seeded list of names per agent — 13 to 29 each
for the seven layer agents, 136 in total; `nveco-strategic` gets no name list
at all, only a written mandate — it works from the other seven agents' output).
The watchlist is a starting point, not a limit.

`nveco-strategic` is different: it runs after the other seven, reads their
output, and **finds no new entities**. It only writes edges that no single-layer
agent could see — a cloud that buys from NVIDIA, co-designs with it, and builds
a replacement chip is three real edges that only a cross-cutting pass finds. If
it needs a missing entity it writes it up as a gap for next month rather than
inventing it.

**Output per agent** — four CSVs into `runs/<YYYY-MM>/<agent>/`:

```
entities.csv   the nodes
edges.csv      the relationships
factors.csv    the four criticality inputs, with a reason for each
sources.csv    citations, keyed to an entity or edge id
```

---

## 4. Sources and the confirmation rule

**Six tiers.** Tier is a property of the domain, not the agent's opinion —
`config/sources.yaml` maps domain → tier and the engine checks the claim.

| tier | what |
|---|---|
| 1 | NVIDIA's own: 10-K/10-Q, earnings calls, PRs, whitepapers, patents |
| 2 | The counterparty's own: their PRs about NVIDIA, their calls, product docs |
| 3 | Principals speaking directly: GTC, Davos, Congressional testimony, verified interviews |
| 4 | Research and data: papers, leaderboards, analyst reports, Crunchbase |
| 5 | Secondary press: Bloomberg, Reuters, WSJ, The Information |
| 6 | Tertiary: podcasts without principals, social, forums, blogs |

**The iron rule: no quote, no edge.** Every edge carries 1–3 sources, each with a
verbatim quote of **≤15 words**, not reassembled from fragments, not translated.
A deliberate corruption test proves the pipeline rejects a sourceless edge
(`tools/nvnet_nosource_test.py`, 12/12 corruption types caught).

**The engine sets the status, not the agent:**

| evidence | status |
|---|---|
| 2 sources of tier 1–2, or 1×tier 1 + 1×tier 3 | `confirmed` |
| 1×tier 1, or 2 of tier 2–3 | `high_confidence` |
| anything else | `signal` |

**Clamp:** an edge with no tier 1–3 source anywhere has its strength capped at
80 and is demoted to `signal`. Current mix: 228 confirmed, 9 high_confidence,
25 signal.

**Link verification** re-fetches every URL each run and records `alive` /
`fetched`. A dead link is reported, not hidden.

---

## 5. What it is looking for

Per entity, the agent must answer four questions with a number **and a reason**:

| factor | weight | the question |
|---|---|---|
| `irreplaceability` | 0.30 | how many others could do this |
| `lockInDepth` | 0.30 | how far up the stack the dependency reaches |
| `timeToReplace` | 0.25 | how long a replacement takes |
| `strategicControl` | 0.15 | what leverage the anchor has over it |

```
criticality = 0.30·irreplaceability + 0.30·lockInDepth
            + 0.25·timeToReplace   + 0.15·strategicControl
```

Weights are frozen by contract. ASML scores 95 on irreplaceability because there
is one EUV maker on earth; a16z scores 31 because several venture funds of that
class exist.

**Gravity** is a separate, computed measure of how far an entity's influence
spreads — it is never authored:

```
gravity = 0.45·reach + 0.25·layers + 0.20·edgeTypes + 0.10·cycles
```

**33 edge types on 5 spines** — the taxonomy of power:

| spine | meaning | examples |
|---|---|---|
| `physical` | what moves, who assembles | `supplies`, `manufactures`, `packages` |
| `capital` | who pays, who owns | `invests_in`, `funded_by`, `board_seat` |
| `moat` | what locks and what proves demand | `locks_in_developers`, `standardizes_on` |
| `control` | who gates access | `controls_access_to`, `export_controlled_by` |
| `rivalry` | who takes a bite | `competes_with`, `threatens`, `could_disrupt` |

Text length is contract too: one-liner ≤110 chars, whyIrreplaceable ≤280,
note ≤200. Long text breaks the panel.

---

## 6. The pipeline

Agents run first and outside the scripts. Everything after is deterministic
Python over what they wrote — **the same CSVs always produce the same map**.

### v2 — the anchor map

```
runs/<month>/nveco-*/            8 agents × 4 CSVs
  → nveco_ingest    validate against configs, resolve ids, 2-hop rule,
                    reject with a reason into _rejected/
  → nveco_verify    re-fetch every URL, alive / fetched
  → nveco_score     rubric, spine, status, gravity, concentration, clamps
  → nveco_cycles    loops of length 3–5, typed sales / financing / lockin
  → nveco_score     second pass — gravity counts cycles, so it runs twice
  → nveco_handoff   handoff/nvidia_ecosystem.json + changelog, validated
```

### v3 — the network

```
handoff/nvidia_ecosystem.json    seed: 106 entities, 243 edges
  + runs/<month>/nvnet-*/        extension: pivot↔pivot edges
  → nvnet_ingest      pivotal flag, hops from nearest pivot
  → nvnet_centrality  degree, betweenness (Brandes), PageRank
  → nvnet_subgraphs   12 subgraphs BY RULE — degeneracy is not hidden
  → nvnet_spof        single points of failure, proved by deletion
  → i18n              load translations, ru + en
  → nvnet_handoff     handoff/ai_ecosystem_network.json, validated
```

**Three centrality measures, two graphs.** Degree and betweenness run on the
*undirected* graph — a path breaks regardless of which way the arrow points.
PageRank runs on a *directed dependence* graph, because "who do the important
depend on" is an inherently directional question. Computing it undirected gave a
0.9988 correlation with degree — an expensive synonym. Directed, it is 0.9341,
and it surfaces Taiwan at rank 2 with a degree of only 3.

**Single points of failure are proved, not asserted.** Candidates are the top
decile of betweenness *within their own layer*; each is then deleted from the
graph and the engine counts how many pairs of the remaining entities lose their
path. Removing NVIDIA breaks 2,078 pairs and splits the network into 22 pieces.

**Subgraphs come from rules over the data**, never a hand-picked list. A rule may
return a degenerate group — that is a research result, not a bug, and it ships
labelled rather than padded.

---

## 7. How it updates

**Cadence:** monthly, triggered by agents producing fresh CSVs. Nothing is on a
timer. A month where only 2 of 8 agents ran is a legal run.

**Per row on ingest:**

| situation | result |
|---|---|
| new id | inserted, `first_seen` = this month |
| existing id | fields updated, `last_confirmed` = this month |
| id gone from the CSV | ⚠ **nothing happens — see §9** |

**Ageing:** an entity unconfirmed for **6 months** is flagged `stale`. Stale
means *shown and marked*, not removed — being old is not the same as being
wrong.

**Changelog** is computed by diffing the new payload against the previous one,
across 10 categories: new/removed nodes, relationships added/removed/updated,
criticality shifts, phase changes, risk escalations, new sources, layer changes.

---

## 8. What ships

`handoff/ai_ecosystem_network.json` → `ab-investment/src/data/aiEcosystemNetwork.json`

Contract **`ai-ecosystem-network/2`**, release `v2.0-2026-08`.

| | current |
|---|---|
| entities | 107 |
| edges | 262 |
| cycles | 146 |
| tech nodes | 10 |
| layers / sectors | 16 / 38 |
| pivots | 27 (hardware 7, labs 6, software 5, infra 4, enablers 3, policy 2) |
| subgraphs | 12, none degenerate |
| single points of failure | 10 |
| density / avg degree / clustering | 0.0358 / 3.79 / 0.5066 |

**Per entity:** id, name, type, role, sector, layers, criticality + the four
factors + a reason for each, gravity, oneLiner, whyIrreplaceable, whatBreaksIt,
phase, risk, ticker, geo, revenue, techNodes, hops, firstSeen, lastConfirmed,
stale, sources, pivotal, centrality (degree / betweenness / pagerank).

**Per edge:** id, source, target, type, spine, direction, strength, lockInDepth,
substitutability, isReversible, status, confidence, sourceTier, risk, techNode,
formed, note, evidence.

**Bilingual.** Every prose field is `{"ru": …, "en": …}` — 1,515 fields, both
sides always non-empty or the payload refuses to write. Source quotes stay
unwrapped in the language of their document: a translated quote is not a quote.

**Validators refuse to write a broken file.** Two corruption suites prove it:
`nveco_corrupt_test` 13/13, `nvnet_nosource_test` 12/12.

---

## 9. Known gaps

Honest list. None of these are hidden in the payload.

**The ingest never deletes.** `INSERT … ON CONFLICT DO UPDATE` handles new and
changed rows; a row that disappears from a CSV stays in the database forever.
There is no `DELETE` for `nveco_edge` anywhere in the engine. Consequence: a
correction cannot be published, and because edge ids are derived from their ends
(`source__target__type`), a direction fix *renames* rather than edits — leaving
both versions active and mutually contradictory. This happened during the v1.2
direction normalisation: 250 edges instead of 243, cleaned by hand.
`owner_agent` was added as the foundation for a fix; retirement itself is not
built yet.

**NVIDIA's 37% connectivity is partly an artefact.** The map grew outward from
NVIDIA, so it has degree 74 against a network average of 3.79. It is genuinely
central, but 37% is an upper bound.

**37 of 107 nodes are dangling** in the dependence graph — they depend on nobody
*in this dataset*, because their own dependencies were never collected. Their
PageRank is inflated for the same reason.

**Carl Zeiss SMT is missing.** The sole optics supplier for EUV tools, rejected
by v2's single-anchor 3-hop rule. Under v3's pivot rule it would be one hop from
ASML — but the network is built from the seed, and it never entered the seed.
Fixing it needs a v2 re-run, not a network change.

---

## 10. Where things live

| | |
|---|---|
| Layer / sector taxonomy | `config/nveco_layers.yaml` |
| Edge taxonomy (31 types) | `config/nveco_edges.yaml` |
| Network extension (2 types, PageRank map) | `config/nvnet_edges.yaml` |
| Pivot registry, hops, release number | `config/nvnet_pivots.yaml` |
| Watchlist per agent | `config/nveco_watchlist.yaml` |
| Domain → tier | `config/sources.yaml` |
| Agent briefs | `agents/nveco-*.md` |
| v2 engine | `engine/nveco*.py` |
| v3 engine | `engine/nvnet*.py` |
| Bilingual store | `engine/i18n.py` |
| Schemas | `db/schema_nveco.sql`, `db/schema_nvnet.sql` |
| Orchestrators | `run_nvidia.py`, `run_network.py` |
| Corruption tests | `tools/nveco_corrupt_test.py`, `tools/nvnet_nosource_test.py` |
| Build logs | `handoff/NVIDIA-ECOSYSTEM-BUILD-LOG.md`, `handoff/AI-ECOSYSTEM-NETWORK-BUILD-LOG.md` |

---

## 11. Running it

```bash
# 1. agents write CSVs into runs/<YYYY-MM>/nveco-*/  (Claude Code, not a script)
# 2. deterministic half:
python run_nvidia.py 2026-08              # anchor map
python run_network.py 2026-08 --deliver   # network + ship to dashboard

# offline (skip URL re-verification):
python run_nvidia.py 2026-08 --offline

# corruption suites:
python tools/nveco_corrupt_test.py
python tools/nvnet_nosource_test.py
```

Both orchestrators return exit code 1 and write **nothing** if the contract
validator fails. A missing file is better than a wrong one.
