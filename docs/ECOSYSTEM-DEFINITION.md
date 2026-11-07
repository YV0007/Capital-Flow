# ECOSYSTEM MAP — DEFINITION AND TARGET

Status: draft v1, 2026-09-18. Owner: Yehor.
This file defines WHAT the ecosystem map is and WHAT IT MUST LOOK LIKE when finished.
It says nothing about how agents research it — that is the next document.
When this is agreed, it supersedes `config/nveco_scope.yaml`, `config/nveco_layers.yaml`
and `config/nveco_edges.yaml` as the source those configs are rewritten from.

---

## 1. The goal

**The map exists to answer one question: where in the AI build-out is value structurally
protected, where is it fragile, and who gets paid when spending moves.**

It is a decision tool for a book of AI and semiconductor positions — not a knowledge base,
not a news feed, not an industry diagram.

It answers four questions, and nothing enters the map that does not serve one of them:

| # | Question | What it produces |
|---|---|---|
| 1 | Where are the chokepoints? | Ranked list of nodes that gate supply, with the reason and the switching time |
| 2 | Who depends on whom, and by how much? | Weighted exposure both ways, in % of revenue and % of supply |
| 3 | Where does money come from and does it loop back? | Financing structure and circular-funding loops, sized in $ |
| 4 | If spending moves, who is hit? | A shock simulation returning a ranked list of public names with an estimated impact |

**The finished state, stated as a test.** The map is done when it can answer, with a source
behind every number: *"If NVIDIA's data-centre revenue falls 20%, which listed companies lose
what share of theirs, and over how many quarters?"* — and the answer can be checked against
what later happens to those companies.

Anything that does not move the map toward that test is out of scope.

---

## 2. What the map is

**The AI compute economy: the companies that turn capital, electricity and data into AI
that someone pays for, connected by documented, sized commercial relationships.**

Three things flow through it:

- **Goods and capacity** flow up: tools → chips → data centres → models → apps.
- **Rights** decide who may use what: data, model access, chip IP.
- **Money** flows back down, plus investment and debt injected from outside.

Not on the map as nodes: countries, regulators, open-source projects, software libraries,
venture funds. They appear as node attributes or belong to the weekly Flows map.

---

## 3. Structure — six chapters

Chapters give the story its order and the graph its layout.

| # | Chapter | Question | Segments |
|---|---|---|---|
| 1 | Silicon | Who makes the chips? | equipment & materials · design tools & IP · chip designers · foundry & packaging · memory |
| 2 | Compute factories | Who builds and powers the data centres? | networking & optics · servers & racks · power & cooling · energy · data-centre builders · clouds |
| 3 | Data | Who owns and prepares what models learn from? | data owners · labelling & expert feedback · enterprise data platforms |
| 4 | Models | Who trains the models? | frontier labs · open-weight labs · in-house big-tech labs |
| 5 | Distribution & apps | Who reaches the users and gets paid? | platforms · AI-native apps · enterprise software |
| 6 | Capital | Who funds it, on what terms? | big-tech capex · lab fundraising · sovereign & private credit · vendor financing |

Capital is a chapter to read, but on the graph it is a thread touching every other chapter.
A company has one home chapter and may hold roles in others — that is how vertical
integration becomes visible (Google: chips, cloud, data, models, distribution).

Target size: 150–200 nodes.

---

## 4. Membership

A node is on the map if it sits in one of the six chapters AND either:

- it is a top-3 player in its segment, or
- it has a material relationship with a node already on the map:
  a disclosed ≥10% customer or supplier, a contract ≥ $1bn, or a sole/primary-source position.

Private companies are allowed and marked as such. Rejections are recorded with a reason.

---

## 5. Connections — six types, three families

| Family | Type | Meaning |
|---|---|---|
| Goods & capacity | `supplies` | A sells a product or service to B |
| | `provides_capacity` | Long-term commitment of compute, power or data-centre space |
| Rights | `licenses` | A grants B use of its data, model or IP |
| | `disputes` | A live legal fight over those rights |
| Money | `invests` | Equity stake |
| | `finances` | Debt, lease, guarantee, vendor financing |

**Competition is not an edge.** Companies in the same segment are competitors by construction;
rivalry is carried by node fields (alternatives, share) and by storylines.

**Control and geography are not edges.** Export-control exposure, production location and
jurisdiction are node attributes.

### Every edge carries a weight

An edge is admissible to the map with a source and a direction. It is admissible **to the
computed metrics** only with at least one measured quantity:

| Unit | Used for |
|---|---|
| `pct_revenue` | share of the seller's revenue coming from the buyer |
| `pct_supply` | share of the buyer's supply coming from the seller |
| `usd` | contract value, investment, financing amount |
| `pct_ownership` | equity stake |
| capacity units (GW, wafers/month, units/yr) | physical volume where it is the real constraint |

Each weight is a fact: `value` · `unit` · `as_of` · `url` · verbatim quote ≤15 words.
The existing `nveco_fact` registry already has this shape; it is 2% populated.

Edges without a measured weight are shown, marked `unweighted`, and excluded from every
computed metric. The agent-authored `strength` / `lock_in_depth` / `substitutability` scores
survive only as a labelled prior — never as an input to a published number.

---

## 6. What a node holds

1. **Identity** — name, ticker or `private`, chapter, segment, HQ, production locations
2. **Role** — one sentence: what it does in the machine
3. **What it controls** — its asset (EUV machines, HBM capacity, CUDA, an archive, a user base)
4. **Depends on** — top suppliers and licensors, weighted
5. **Depended on by** — top customers, weighted
6. **Money** — revenue, AI-linked share, margin: who captures the profit
7. **Chokepoint** — alternatives, time to replace, computed rank
8. **Risk** — geography, export controls, litigation, customer concentration
9. **What's changing** — 1–2 dated lines, the live tension
10. **Coverage** — how much of this node has been researched, and when last confirmed

---

## 7. The finished screen

```
┌──────────────────────────────────────────────────────────────┬──────────────┐
│  LENS: Structure | Chokepoints | Exposure | Money            │              │
│                                                              │   NODE CARD  │
│   ch.5  Distribution & apps   ○ ○ ○ ○ ○                      │              │
│   ch.4  Models                ● ○ ● ○                        │   role       │
│   ch.3  Data                  ○ ● ○ ○ ○            CAPITAL   │   controls   │
│   ch.2  Compute factories     ● ● ○ ● ● ○          (side     │   depends on │
│   ch.1  Silicon               ● ● ● ○ ● ●           band)    │   depended on│
│                                                              │   money      │
│                                                              │   chokepoint │
│                                                              │   risk       │
├──────────────────────────────────────────────────────────────┤   changing   │
│  STORYLINES:  circular money · HBM bottleneck · power ·      │   coverage   │
│               escape from NVIDIA · data wars · who owns user │              │
└──────────────────────────────────────────────────────────────┴──────────────┘
```

**Layout.** Six chapter bands, silicon at the bottom, apps at the top, capital along the side.
Position on the map = position in the chain. Nothing is force-directed into a hairball.

**Visual encoding.**

| Element | Encodes |
|---|---|
| Node size | computed importance (weighted, not authored) |
| Node colour | chapter |
| Node ring | coverage: solid = researched, dashed = thin, grey = queued |
| Node badge | public ticker / private · chokepoint flag |
| Edge colour | family: goods · rights · money |
| Edge thickness | weight ($ or %) |
| Edge style | solid = measured, dotted = unweighted |
| Edge arrow | direction of goods or rights; money is implied in reverse |

**Four lenses over the same graph.**

1. **Structure** (default) — the whole chain, all families visible.
2. **Chokepoints** — only nodes that gate supply, ranked, with their min-cut and switching time.
3. **Exposure** — pick a node, set a shock (e.g. −20% demand); the map shows who is hit,
   in which order, by how much, over how many quarters.
4. **Money** — investment, financing and circular loops only, sized in $.

**Storylines.** A storyline is a curated path through the graph with a short narrative:
a one-sentence thesis, the path, the numbers on that path, what confirms or breaks it, and
the listed names it touches. Selecting one dims the map and walks the path step by step.
Rule: every claim in a storyline must point at an edge or a node figure on the map.

**Time.** The graph is versioned monthly. Every metric is a time series; the map can be
rewound, and changes between versions are the alert surface.

---

## 8. What comes out of it, besides the picture

| Output | Content |
|---|---|
| Chokepoint ranking | min-cut nodes per stage, alternatives, switching time, coverage flag |
| Exposure matrix | for each public ticker, weighted exposure to each demand source |
| Shock report | input-output propagation: "−20% at X" → ranked impact per name |
| Money-loop report | circular financing, sized, with the share of chain revenue that is self-funded |
| Change log | what moved between two monthly versions |
| Storylines | the narrative layer, each tied to paths in the graph |

---

## 9. What it is not

- Not a news feed — no undated relationships, no announcements without money.
- Not a market-share chart — it maps dependency, not size.
- Not an opinion engine — no number ships that is not traceable to a filing.
- Not complete — coverage is stated openly next to every computed figure.

---

## 10. Acceptance criteria

The map is finished when all of the following hold:

1. 150–200 nodes, each in one chapter, each with the ten node fields filled or explicitly blank.
2. ≥80% of edges carry at least one measured weight with a quote and a date.
3. Node importance, chokepoint rank and exposure are computed from weights — not authored.
4. A shock simulation runs end to end and names public companies with estimated impact.
5. Monthly versions exist, and metric time series can be drawn.
6. Every published number shows its coverage flag.
7. Six storylines exist, each fully backed by paths on the map.

---

## 11. Open decisions

- Chapter 5 depth: platforms + top ~10 AI apps by revenue, or enterprise software more broadly?
- Storylines: only hand-approved, or engine-proposed candidates that Yehor approves?
- Thresholds: ≥10% of revenue and ≥$1bn contracts — right cut-off, or tighter?
- Capital chapter: full chapter, or only financiers with a documented tie to a node on the map?
