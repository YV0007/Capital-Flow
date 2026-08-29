# Ecosystem engine — how it works

One file, everything: what the map is, what it looks for, where the data comes
from, how it is scored, how it rotates, and what ships.

Two pipelines stacked. **`run_nvidia.py`** builds the seed map — entities, edges,
citations, rubric, cycles. **`run_network.py`** builds the network on top of it —
centrality, integration, subgraphs, points of failure — and ships the payload. The
network reads the seed's output and never rewrites it.

The module prefixes `nveco_` / `nvnet_` and the script name `run_nvidia.py` are
**historical**. The map had a centre once; it does not any more. Renaming 18 tables
and 13 modules mid-migration is pure risk for no gain, so the names stay and this
paragraph explains them. See §12.

---

## 1. The approach

**The question the map answers:** who holds a function the AI stack cannot run
without, how deeply they are wired into it, and what breaks if that node
disappears.

Not "who supplies whom". Four design choices follow:

| choice | why |
|---|---|
| Relationships are typed by **mechanism**, not direction of goods | A supply, a lock-in and an export gate are different kinds of power. One arrow colour would lie. |
| Every edge needs a **verbatim quote** | Without it the map is opinion. See §4. |
| The engine computes scores, agents supply **facts** | An agent that could set its own criticality would set it high. |
| Importance is **two measures, not one** | "Holds a function nothing replaces" and "is wired into everything" are different claims. Merging them hides the interesting nodes. See §5. |

**Membership** — three checks, none of which names a company:

1. `in_scope` — works in at least one of the 16 layers. The subject *is* the
   layers; they are the boundary.
2. `min_sources: 3` and `min_self_sources: 1` — the entity has a dossier of its
   own, at least one document of which it published itself.
3. `min_confirmed_edges: 2` — at least two confirmed links to entities on the map.

Thresholds live in `config/nveco_scope.yaml`, not in Python: moving the boundary of
the map is a decision and must be visible in a config diff.

**Checks 2 and 3 are gated by coverage.** `min_sources` and `min_self_sources`
apply to an entity **only after its dossier has been worked** — that is, after
rotation has reached it (a row in `nveco_dossier_run`). An entity rotation has not
reached yet carries `pendingDossier`, is shown, is marked, and is not retired.
Punishing a node for the absence of *research* rather than the absence of *grounds*
is not strictness, it is a substitution of subject. `in_scope` and
`min_confirmed_edges` apply to everyone at once.

What fails an applicable check is retired **with a reason, never silently**, and the
rejection goes into the ledger and from there into the candidate queue — the node
does not vanish, it comes back up for review. See §7.

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

Putting the USA between "memory" and "systems" would be a lie about the nature of
the relationship — Commerce supplies nobody, it decides who may sell to whom.
Hence the separate `control` plane.

**39 sectors** sit under the layers (`foundry`, `hbm`, `neocloud`,
`export_authority`, …). They are the map's own taxonomy — nothing points at an
external classification.

**10 tech nodes** are technologies, not companies: EUV, N3, CoWoS, HBM, NVLink,
InfiniBand, Spectrum-X, Arm ISA, PCIe. They ride on an edge as a label explaining
*why* a dependency is unbreakable.

---

## 3. Who does the research

Two kinds of agent, and the difference between them is the unit of work.

### The dossier — one node, done properly

`agents/eco-dossier.md`. The unit is **one node**, not a sweep of a layer. First
and second class nodes do not exist: a core entity and a tail entity get the same
treatment. The one hard requirement a layer sweep does not have:

> **≥ 1 source published by the entity itself.** A company described only by
> someone else's filing does not have a dossier — it has a mention.

A dossier answers, from the node's own documents: what it is and how it earns
(`description`, 4–7 sentences, `{ru,en}`); what it depends on and what depends on
it (edges plus a verbatim quote on each); who could replace it and in how long
(`irreplaceability`, `timeToReplace`); what share of its own function it holds
(`concentration`, quote mandatory); and everything it names that is not on the map
yet (`candidates`).

If an entity has no publisher of its own — a statute has no press office — the
rule is waived by the **fact of an empty `domains` list** in
`config/entity_domains.yaml`, not by an exception in code.

Batches are assembled by `tools/make_dossier_batches.py`. Each pack carries: what
we already know (profile, edges from both ends, every source marked with *whose
word it is*); what to reconcile (edges only one end has ever claimed — the cheapest
work in the pack); what membership is missing; and what the ingest rejected.

### The layer sweep — what a dossier cannot see

Eight `agents/nveco-*.md` briefs. Their mandate is narrowed to the one thing a
per-node dossier cannot produce: **entities not on the map yet, inside their
layer.**

| agent | layers |
|---|---|
| `nveco-geo` | L0, L15 |
| `nveco-silicon` | L1–L4 |
| `nveco-systems` | L5, L8, L9 |
| `nveco-power` | L6, L7 |
| `nveco-software` | L10, L11 |
| `nveco-models` | L12, L13 |
| `nveco-capital` | L14 |
| `nveco-strategic` | — reconciliation pass, runs last |

`nveco-strategic` reads the output of `nveco_reconcile`, works through `disputed`
edges, and looks for cross-layer links neither end claimed. It enters no new
entities.

**Who wins when both write the same row.** A dossier overrides a layer sweep; a
sweep never overrides a dossier; between equals the first wins. Divergences do not
go quiet — they land in the run's warnings by name.

**Output per agent** — four CSVs into `runs/<YYYY-MM>/<agent>/`:

```
entities.csv   the nodes
edges.csv      the relationships
factors.csv    the four criticality inputs, with a reason for each
sources.csv    citations, keyed to an entity or edge id
```

A dossier writes `dossier.json` instead, and `tools/dossier_split.py` lays it out
into exactly those CSVs. The splitter is deliberately dumb: it lays out, checks the
shape, names the error, and **guesses nothing**.

---

## 4. Sources: the tier is relative to the subject

**Six tiers, and the point of origin is the entity itself.**

| tier | what |
|---|---|
| 1 | **the subject's own** official statement: its filings, its calls, its PRs, its product docs |
| 2 | **the other end of the edge**, or any other entity on the map, speaking about it |
| 3 | principals speaking directly: conferences, testimony, verified interviews |
| 4 | research and data: papers, leaderboards, analyst reports |
| 5 | secondary press |
| 6 | tertiary and signals |

The tier is computed, never authored. `nveco.source_tier(url, subject_id,
counterparty_id)` resolves it through `config/entity_domains.yaml` — a registry of
`id → {domains, cik}`. A host matches with its subdomains; a `host/path` entry
matches more narrowly and wins over a bare host, which is why
`developer.nvidia.com/cuda` is CUDA and `nvidia.com` is NVIDIA. A CIK in an EDGAR
path is `self` as well, even though `sec.gov` belongs to everyone.

**The iron rule: no quote, no edge.** Every edge carries 1–3 sources, each with a
verbatim quote of **≤15 words**, not reassembled from fragments, not translated.

**The engine sets the status, not the agent:**

| evidence | status |
|---|---|
| a SELF quote from **both** ends | `bilateral` — the top of the ladder |
| 2 sources of tier 1–2, or 1×tier 1 + 1×tier 3 | `confirmed` |
| 1×tier 1, or 2 of tier 2–3 | `high_confidence` |
| anything else | `signal` |
| one end asserts, the other **denies** | `disputed` — ships with **both** quotes |

`bilateral` is strictly stronger than "two tier-1–2 sources": the old bar could be
cleared by one company naming itself twice. `bilateral` requires two *different*
publishers, and specifically the two the edge is about.

`disputed` is never resolved by the engine and never has a side removed. Two
companies describing their own relationship differently is a finding, not a data
error.

**`sidedness`** rides alongside `status` on every edge: `bilateral`, `single` (the
other end is silent — a mark, not a defect), or `disputed`.

**Link verification** re-fetches every URL each run and records `alive` / `fetched`.
A dead link is reported, not hidden.

---

## 5. Two measures of importance

### `criticality` — authored, from the node's own dossier

| factor | weight | the question |
|---|---|---|
| `irreplaceability` | 0.30 | can the **ecosystem** do without it |
| `lockInDepth` | 0.30 | how far up the stack the dependency reaches |
| `timeToReplace` | 0.25 | how long a replacement takes |
| `concentration` | 0.15 | what share of **its own function** it holds |

`concentration` is not "market share" in general — it is the share of the work the
node is on the map for. ASML holds EUV lithography, not "the equipment market".
The number must rest on a quote; a share without a source does not ship, exactly
like every other figure.

An entity whose `concentration` has not been researched yet is scored on **three
factors renormalised**, never on a zero — a zero would be the assertion "this node
holds none of its function", which is a fabricated figure with a weight of 0.15 in
every score on the map. Which basis was used is stated per entity in
`criticalityBasis`, and the validator drops the release if the promised factor
count and the filled factors disagree.

### `integration` — computed, from the graph. The map's primary rank

```
integration = 0.30·degree + 0.25·betweenness + 0.15·pagerank
            + 0.15·layersSpanned + 0.10·edgeTypes + 0.05·cycles
```

Each term normalised against the maximum in the current graph. Weights live in
`config/nvnet_edges.yaml`. `gravity` is kept as it was and untouched;
`integration` stands beside it.

**The two axes are orthogonal, and the interesting nodes are where they diverge.**
High criticality with low integration is a hidden chokepoint — Carl Zeiss SMT
ranks 8th by criticality and last of 108 by integration, because it holds the
optics of every EUV tool on earth and the map has found it exactly one
counterparty. Low criticality with high integration is a hub. Neither is visible
while there is one measure.

**`core` is an output, not an input**: the top 30 by `integration.score`, ties
broken by degree then by id. There is no hand-maintained list anywhere. Entering
and leaving the core is its own changelog category.

**33 edge types on 5 spines** — the taxonomy of power:

| spine | meaning | examples |
|---|---|---|
| `physical` | what moves, who assembles | `supplies`, `manufactures`, `packages` |
| `capital` | who pays, who owns | `invests_in`, `funded_by`, `board_seat` |
| `moat` | what locks and what proves demand | `locks_in_developers`, `standardizes_on` |
| `control` | who gates access | `controls_access_to`, `export_controlled_by` |
| `rivalry` | who takes a bite | `competes_with`, `threatens`, `could_disrupt` |

---

## 6. The pipeline

Agents run first and outside the scripts. Everything after is deterministic Python
over what they wrote — **the same CSVs always produce the same map**.

### Seed

```
runs/<month>/nveco-*/            layer sweeps × 4 CSVs
runs/<month>/nveco-dossier-NN/   dossier.json → tools/dossier_split.py → the same CSVs
  → nveco_ingest     validate against configs, resolve ids, scope and membership,
                     reject with a reason into _rejected/ and into the ledger
  → nveco_verify     re-fetch every URL, alive / fetched
  → nveco_reconcile  tier relative to the subject, sides of each edge, disputes
  → nveco_score      rubric, spine, status, gravity, clamps
  → nveco_cycles     loops of length 3–5, typed sales / financing / lockin
  → nveco_score      second pass — gravity counts cycles, so it runs twice
  → nveco_handoff    handoff/nvidia_ecosystem.json + changelog, validated
```

### Network

```
handoff/nvidia_ecosystem.json    the seed
  + runs/<month>/nvnet-*/        extension: edges and prose
  → nvnet_ingest      merge, sourcing, pendingDossier, membershipFailing
  → nvnet_centrality  degree, betweenness (Brandes), PageRank, integration, core
  → nvnet_subgraphs   12 subgraphs BY RULE — degeneracy is not hidden
  → nvnet_spof        single points of failure, proved by deletion
  → i18n              load translations, ru + en
  → nvnet_handoff     handoff/ai_ecosystem_network.json, validated
```

**Three centrality measures, two graphs.** Degree and betweenness run on the
*undirected* graph — a path breaks regardless of which way the arrow points.
PageRank runs on a *directed dependence* graph, because "who do the important
depend on" is an inherently directional question. Undirected it correlated 0.9988
with degree — an expensive synonym. The direction of dependence per edge type is
declared in `config/nvnet_edges.yaml` and can be argued with without reading
Python.

**Single points of failure are proved, not asserted.** Candidates are the top
decile of betweenness within their own layer; each is then deleted and the engine
counts how many pairs of the remaining entities lose their path.

**Subgraphs come from rules over the data**, never a hand-picked list. A rule may
return a degenerate group — that is a research result, not a bug, and it ships
labelled rather than padded.

---

## 7. Rotation and feedback

### Who gets researched, and when

The tier is stored in `nvnet_integration` and written by every network run.
Cadences and thresholds are in `config/nveco_scope.yaml`, block `rotation`.

| tier | cadence |
|---|---|
| core (top 30) | every month |
| mid (next third) | quarterly |
| tail | on trigger: an edge touching the node was confirmed after its last dossier, or 6 months without confirmation |

Budget ≈40 dossiers a month in batches of 8. What does not fit is **printed**:
silent truncation reads as "we covered everything" when forty of a hundred were
covered.

**The tier is taken from the better of two ranks — integration or criticality —
not from integration alone.** By integration ASML is 52nd and Carl Zeiss SMT is
108th of 108; by criticality they are 6th and 8th. A tier from integration alone
would research least often precisely the nodes the map knows least about — and a
node's low integration is in large part a measure of *our own ignorance*: ASML has
three edges on the map not because it has three, but because nobody looked. Which
axis placed a node in its tier is recorded in `nvnet_integration.rota_basis`.

`core` in the payload stays purely integration-based, because the contract defines
it that way and the dashboard ranks by it. Rotation tier and core membership are
two different questions; merging them would repeat the mistake of a single concept
doing three jobs.

```bash
python tools/make_dossier_batches.py 2026-09 --tier=due
```

### Rejections and the queue — and why they used to be dead

A rejection sitting in a CSV is not feedback, it is an archive entry. This was
proved on `Carl Zeiss SMT`: the step rule threw it out every run, wrote the reason
to `runs/<month>/_rejected/nveco-silicon.csv`, the file sat committed in the
repository — and was never read. The write worked. **Delivery** did not.

Five reasons it could not work, and what stands against each now:

| it was | it is |
|---|---|
| the rejection lived exactly one run — ingest wipes the directory before writing the new set | it lives in `nveco_rejection` until it is fixed or explicitly decided, and remembers how many runs it has repeated |
| the brief sent the agent to `runs/<previous month>/`, ingest wrote to `runs/<current>/` | one path: the database. The CSV stays for a human |
| the eight layer agents had no batcher at all — "returns to the agent" meant "the agent will go and open a file" | a rejection **about an entity** becomes a candidate-queue row, which does have a consumer |
| a rejection about an entity could not be delivered: packs are built by walking the entities in the database, and a rejected entity is by definition not in it | `subject_id` / `subject_name` are columns, and the batcher puts such rejections in **every** pack as a separate "rejected, never reached the map" list |
| nothing ever checked that a rejection was read | `tools/feedback_check.py` fails the run when a row has hung for more than one run |

The rule that follows, worth holding in mind: **silence about a rejection is not a
decision.** A row either stops arriving (it was fixed) or gets a `decision` with a
reason. There is no third state.

The candidate queue is the same loop's other half. A dossier names everything it
does not see in its pack; whatever is not on the map becomes a queue row. It is
worked through **in full**: every row is accepted or rejected **with a reason**.

```bash
python tools/queue_review.py                 # state of the queue
python tools/queue_review.py --rejections    # open rejections with their keys
python tools/feedback_check.py               # exit 1 while anything is unconsumed
```

### The hunt — what the map does not have

Rejections answer "what did we refuse". The candidate queue answers "which **node**
are we missing". Neither could answer the third question, and until it was asked the
map had a hole with a name on it: TSMC, the largest foundry in the world, had six
customers, and every one of them was found because *the customer* named TSMC in its
own filing. Not one was found from TSMC's side.

Three reasons, none of them about research quality:

1. **Edge discovery was a side effect of reading a node.** An edge A–B appeared only
   if a dossier for A happened to meet B's name in A's documents. There was no list
   of pairs that probably exist, and no record of a pair looked for and not found.
2. **For a whole class of relationships the name is on neither side.** Measured, not
   assumed: TSMC writes "Our largest customer … accounted for" with no name; Marvell
   writes "third-party foundries located in Taiwan" with no name; Amazon's 10-K
   contains the words TSMC, foundry, Trainium and Graviton **zero** times in 312,000
   characters. All three describe the relationship. None names the counterparty.
3. **The candidate queue only catches missing nodes.** Amazon and Marvell are both on
   the map, so their missing TSMC link could never be a candidate.

`engine/nveco_gaps.py` generates hunt tasks from what the corpus already holds:

| generator | the reason |
|---|---|
| `disclosed_unnamed` | the node's own quote discloses a counterparty without naming it. Sixty such quotes were already in the corpus across forty-nine objects, and nothing read them: the map had said it was incomplete sixty times. |
| `expected_edge` | the taxonomy says a node of this kind does not work without a counterparty of that kind, and it has none of that class. The rule names **classes**, never companies, so it cannot pre-decide the answer. |

Tasks ride into the dossier pack as `to_hunt` — the only section that tells the agent
what the map does **not** have. For that work any tier is allowed: a named
counterparty from a press report beats an unnamed one from a filing.

A task closes two ways, and both are answers: `found` (the edge is entered, with a
quote) or `not_found` (we looked, we did not find, the reason goes to
`nvnet_not_found` and the pair is not re-asked for six months). `dismissed` is the
third, and it is a finding about the **rule**, not the map. Silence is not a fourth —
`tools/feedback_check.py` fails the run while a task has hung past its threshold.

The counters on rejections and hunt tasks measure **months, not runs**: rebuilding the
same month is not another occasion on which the task was ignored.

### Ageing and retirement

An entity unconfirmed for **6 months** is flagged `stale`. Stale means *shown and
marked*, not removed — being old is not the same as being wrong.

Retirement has two paths and they must not be confused:

* **Agent silence.** The ingest is authoritative for the month it ingests: a row
  that disappears from a CSV is deleted along with its sources, translations and
  place in any cycle. Scoped by `owner_agent`, because a month in which two of
  eight agents ran is a legal run. A missing file means the agent did not work; an
  empty file means it claims nothing and its rows go; a file where *every* row was
  rejected is an output accident and retires nothing — it goes to warnings.
* **Membership.** An entity failing an applicable check is retired with a named
  reason. `on_fail: retire_unheld` (the default) removes it only when no edge holds
  it: a membership failure of node X is not evidence against edge X–Y, which has a
  citation and an owner of its own. A held node stays, is marked
  `membershipFailing`, and is **named** in `runs/<month>/_membership/retired.csv`.
  `on_fail: retire_all` is the strict alternative and is one config value away.

Both paths are covered by `tools/nveco_retire_test.py`, including the case that
proves they are distinguishable from each other.

---

## 8. What ships

`handoff/ai_ecosystem_network.json` → `ab-investment/src/data/aiEcosystemNetwork.json`

Contract **`ai-ecosystem-network/4`**, release `v4.0-2026-08`.

| | current |
|---|---|
| entities | 110 |
| edges | 321 |
| cycles | 225 (lockin 124, financing 73, sales 28) |
| tech nodes | 10 |
| layers / sectors | 16 / 39 |
| edge types | 33 on 5 spines |
| core | 30, computed |
| subgraphs | 12 |
| single points of failure | 9 |
| density / avg degree / clustering | 0.0434 / 4.65 / 0.5165 |
| edge status | confirmed 176 · bilateral 70 · high_confidence 43 · signal 25 · disputed 0 |
| sidedness | single 244 · bilateral 70 · disputed 0 |
| profile source tiers | 1: 445 · 2: 111 · 3: 3 · 4: 2 |
| median sources per profile | 5 |
| profiles with no citation of their own | 10 of 110 |

**Per entity:** id, name, type, role, sector, layers, criticality plus the four
factors plus a reason for each, `criticalityBasis`, `integration` (score and its
six terms), `sourcing` (total, selfSourced, byTier), `domains`, `cik`, `core`,
`pivotal` (a mirror of `core`, deprecated, removed in `/5`), `pendingDossier`,
`membershipFailing`, gravity, oneLiner, description, whyIrreplaceable,
whatBreaksIt, phase, risk, ticker, geo, revenue, techNodes, firstSeen,
lastConfirmed, stale, sources, centrality.

**Per edge:** id, source, target, type, spine, direction, strength, lockInDepth,
substitutability, isReversible, status, `sidedness`, `claimedBy`,
`counterEvidence`, confidence, sourceTier, risk, techNode, formed, note, detail,
evidence.

**`meta`** carries the map's own subject (`scope`), the core rule, and
`membership`: admitted / retired / held / queued, which checks are coverage-gated,
what `on_fail` is set to, and the named lists behind `retired` and `held`.

**Bilingual.** Every prose field is `{"ru": …, "en": …}`, both sides non-empty or
the payload refuses to write. Source quotes stay unwrapped in the language of
their document: a translated quote is not a quote.

**Every figure in prose comes from a quote attached to that object.** The rule
covers `description`, `oneLiner`, `note`, `detail` and all four factor
justifications. A number the reader cannot check is worse than no number.

**Validators refuse to write a broken file.** Four suites, 119 cases:
`nveco_corrupt_test` 42, `nvnet_nosource_test` 53, `nveco_retire_test` 21,
`nvnet_retire_test` 3.

---

## 9. Known gaps

Honest list. None of it is hidden in the payload.

**10 of 108 profiles have no citation of their own.** Two of them —
`cfius`, `chips-act` — never can: they have no publisher, and the SELF rule is
waived for them by that fact. The other eight (`boyd`, `delta-electronics`,
`lite-on`, `mgx`, `quanta`, `sequoia`, `thrive`, `wistron`) are a delivery
problem, not a research one: their own sites answer a machine request with 403 or
a bot-check redirect. They are due in the next rotation with a different fetch
route.

**34 of 108 nodes do not pass `min_confirmed_edges`.** All are held by an edge and
marked. Half of them are simply nodes rotation has not reached, whose edge count
is low because nobody looked. This is a finding about the check, and it is written
down rather than tuned away: a rule that measures how well-connected a node is *on
the map* also measures how much of the map has been built.

**`disputed` is 0 across 314 edges.** The machinery is complete and covered by
tests end to end — the `counter` column in `sources.csv`, `stance: counters` in a
dossier, the transfer into `counterEvidence` on both halves of the map. In 77
dossiers not one case turned up where a party's own documents denied what is
written about it. That is expected: companies do not publish denials of
relationships, they stay silent about them — and silence is `single`, of which
there are 244.

**52 of 314 edges have no `detail`.** These are the edges this campaign added; the
explainer is written by a separate pass (`agents/nvnet-detail`), which runs on its
own cadence.

**The map still has no way to see a node nobody named.** The hunt closes the gap
for *edges* between nodes already present, and the candidate queue closes it for
nodes named by someone present. A layer that no node on the map has ever mentioned
remains invisible: there is nothing to detect it with. §12 of the build log calls
this out at length.

**Two taxonomy defects the hunt exposed on its first run.** There was no sector for
a fabless silicon designer, which is why AMD carries `foundry` while owning no fab —
and why the `fab_needs_equipment` rule immediately issued it a task to find its
equipment supplier. `fabless_silicon` now exists; AMD's own row is the layer agent's
to correct. And `rack_needs_accelerator` expects `supplies` where the taxonomy also
allows `integrates`, which produced one false task against Foxconn.

**NVIDIA's connectivity is 22.5% and is still partly an artefact.** Removing it
costs 1,325 pairs of entities their path. The map grew outward from it, so its
degree is 122 against a network average of 5.84. The figure fell from 37.0% as
edges that touch neither end of it arrived; it will keep falling for the same
reason, and only for that reason.

**Nodes dangling in the dependence graph** depend on nobody *in this dataset*,
because their own dependencies were never collected. Their PageRank is inflated
for the same reason.

---

## 10. Where things live

| | |
|---|---|
| Map scope, membership, rotation | `config/nveco_scope.yaml` |
| Publisher registry (domains, CIK) | `config/entity_domains.yaml` |
| Layer / sector taxonomy | `config/nveco_layers.yaml` |
| Edge taxonomy (31 types) | `config/nveco_edges.yaml` |
| Network extension (2 types, PageRank map, integration weights) | `config/nvnet_edges.yaml` |
| Watchlist per agent | `config/nveco_watchlist.yaml` |
| Publisher-type tiers | `config/sources.yaml` |
| Dossier brief | `agents/eco-dossier.md` |
| Layer briefs | `agents/nveco-*.md` |
| Seed engine | `engine/nveco*.py` |
| Feedback ledger and queue | `engine/nveco_feedback.py` |
| Hunt for missing edges | `engine/nveco_gaps.py`, `config/nveco_gaps.yaml` |
| Network engine | `engine/nvnet*.py` |
| Bilingual store | `engine/i18n.py` |
| Schemas | `db/schema_nveco.sql`, `db/schema_nvnet.sql` |
| Orchestrators | `run_nvidia.py`, `run_network.py` |
| Dossier batches | `tools/make_dossier_batches.py`, `tools/dossier_split.py` |
| Queue, hunt and feedback | `tools/queue_review.py`, `tools/gap_review.py`, `tools/feedback_check.py` |
| Corruption tests | `tools/nveco_corrupt_test.py`, `tools/nvnet_nosource_test.py` |
| Retirement tests | `tools/nveco_retire_test.py`, `tools/nvnet_retire_test.py` |
| Build logs | `handoff/AI-ECOSYSTEM-V4-BUILD-LOG.md` and its predecessors |

---

## 11. Running it

```bash
# 1. what rotation orders this month
python tools/make_dossier_batches.py 2026-09 --tier=due

# 2. the eco-dossier agent writes dossier.json into each batch directory
python tools/dossier_split.py 2026-09          # → the pipeline's CSVs

# 3. the deterministic half
python run_nvidia.py 2026-09                   # seed
python run_network.py 2026-09 --deliver        # network + ship to dashboard

# offline (skip URL re-verification):
python run_nvidia.py 2026-09 --offline

# feedback: the queue, the hunt, the gate
python tools/queue_review.py
python tools/gap_review.py --open
python tools/feedback_check.py

# the suites
python tools/nveco_corrupt_test.py && python tools/nvnet_nosource_test.py 2026-09
python tools/nveco_retire_test.py && python tools/nvnet_retire_test.py
```

Both orchestrators return exit code 1 and write **nothing** if the contract
validator fails. A missing file is better than a wrong one.

---

## 12. Historical section: the anchor

Until `/4` the map had a centre, and one concept — the **anchor** — did three
different jobs at once:

1. **Membership** — who is on the map at all (the "two hops from NVIDIA" rule).
2. **Evidence** — whose word counts for what (tier 1 = NVIDIA said it).
3. **Importance** — how big a node is (`strategicControl` = NVIDIA's leverage over it).

While those three were fused, removing the anchor meant removing the map. The v4
campaign split them into three independent mechanisms, none of which needs a
centre: three coverage checks; a tier relative to the **subject**; and two
measures of importance, `concentration` and `integration`.

What that cost, measured rather than assumed: 41 of 107 entities had **every**
source published by NVIDIA, 75 had no voice of their own at all, the median
sources per profile was exactly one, and `strategicControl` was dropped rather
than converted — leverage over a node and the share of a function it holds do not
translate into each other, and pouring the old number into the new name would have
been two lies at once.

The prefixes `nveco_` / `nvnet_`, the script name `run_nvidia.py`, and the root
`pivots` field survive from that period. They are names, not behaviour. The
behavioural remains — `anchor_cfg`, `load_anchors`, `domain_tier`, `hops_limit`,
`hops_from_pivots`, `pivot_ids`, the `hops` column — were deleted.
