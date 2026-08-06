# Capital Flow — Dashboard Consumer Brief
### (Hand this whole file to an ab-investment Claude Code session)

You are working in **ab-investment** (the React/Vite dashboard on Vercel). A separate
autonomous engine called **Capital Flow** produces a data file about where elite
investors are moving money. Your job is to **rebuild the Capital Flow Map section of
the Research area from scratch** so it renders that engine's data instead of the
current hand-authored dataset. This brief is self-contained — it gives you the full
context, the exact data contract, the rules, and the task.

---

## 1. Context — how the whole system works

There are **two separate repos**:

- **Capital Flow** (the engine, not this repo) — six autonomous research agents sweep
  SEC filings, official PRs, VC/press sources every cycle, find real capital-allocation
  events (funding rounds, acquisitions, project finance, sovereign investments, fund
  launches…), verify them against sources, and store them in a SQLite database. A
  deterministic Python pipeline then dedupes them, runs signal rules (e.g. "5+ key
  investors piled into one sector in 30 days"), maps private flows to public-market
  beneficiaries, and **exports one file: `capital_map.json`**.
- **ab-investment** (this repo, the dashboard) — renders that file as the interactive
  Capital Flow Map in the Research section.

```
Capital Flow engine (agents → verify → SQLite → signal rules → beneficiaries)
        │
        ▼
   capital_map.json      ← the ONLY contract between the two sides
        │
        ▼
ab-investment Capital Flow Map  ← YOUR job: build the thing that renders it
```

**Update cadence** (why the file changes over time): the engine runs on a schedule —
**weekly by default**, plus **on-demand** whenever the user asks for a refresh. Each run
regenerates `capital_map.json` with new events, updated totals, and possibly new
entities or fired signals. So your component must render *whatever is in the file today*
— never hard-code entities or numbers. The map is a **cumulative memory** that grows
each week, not a fixed picture.

**How the file reaches you (delivery — DECISION, see §5):** the engine's
`capital_map.json` is placed at a known path in this repo — **`src/data/capitalMap.json`**
— and your component imports it. A scheduled/on-demand engine run updates that file and
pushes; Vercel auto-deploys. The user may also **hand you a `capital_map.json` directly**
(a manual drop / upload) — your component must render that identically, since it is the
same shape. Treat "the file at `src/data/capitalMap.json`" as the source of truth
regardless of how it got there.

---

## 2. The data contract — `capital_map.json`

This is the exact shape the engine emits (real sample values from the first run):

```jsonc
{
  "generated": "2026-08-06",                 // ISO date the file was produced
  "totals": { "nodes": 46, "flows": 33, "sectors": 10 },

  "nodes": [                                  // every entity on the map
    {
      "id": "target:OpenAI",                  // stable unique id — "alloc:<name>" or "target:<name>"
      "label": "OpenAI",                      // display name
      "kind": "allocator" | "target",         // allocator = deploys capital; target = receives it
      "cls": "corporate|vc|individual|alt_manager|sovereign"   // for allocators
             | "private|public|fund|project|asset",            // for targets
      "tier": "key" | "watch" | null,         // allocator importance (null for targets)
      "sector": "ai-labs",                    // canonical sector (targets carry one; allocators null)
      "deals": 2,                             // # flows touching this node
      "capital": 90000000000.0,               // USD summed across its flows
      "first_seen": "2026-07-27",             // earliest activity
      "last_activity": "2026-07-31",          // most recent activity
      "stale": false                          // true = no activity in 180 days
    }
  ],

  "flows": [                                  // every capital movement (the edges)
    {
      "source": "alloc:Amazon",               // node id of the allocator
      "target": "target:OpenAI",              // node id of the target
      "sector": "ai-labs",
      "event_type": "corporate_investment|equity|minority_stake|follow_on|funding_round|
                     acquisition|fund_launch|spv|grant|project_finance|sovereign_investment",
      "amount": 50000000000.0,                // USD, or null if undisclosed
      "status": "verified" | "verified_alpha" | "candidate",   // confidence
      "date": "2026-07-31",                   // disclosed date
      "tier": 1                               // source tier 1..5 (1 = SEC/official)
    }
  ],

  "sectors": {                                // per-sector aggregates
    "ai-labs": {
      "deals": 5,
      "capital": 102500000000.0,
      "allocators": 5,                        // distinct allocators active in the sector
      "signals": [                            // fired signal rules (may be empty)
        { "theme": "ai-labs: 5 key allocators in 30d", "rule": "sector_swarm", "strength": 5.0 }
      ]
    }
  }
}
```

### The 12 canonical sectors
`ai-labs`, `ai-compute`, `semiconductors`, `fab-equipment`, `cloud-hyperscale`,
`neocloud`, `datacenters`, `power-energy`, `nuclear`, `networking`, `robotics`,
`defense-tech`. These are the cluster zones of the map.

### Notes on the data
- **A single deal can appear as multiple flows** (one per allocator) — e.g. a round with
  Sequoia + a16z + Founders Fund is three flows into the same target. This is intentional
  (it's how the engine counts distinct investors). Your map should show them as multiple
  edges into one target node.
- **Status drives confidence styling**: `verified` (Tier-1 confirmed) is strongest;
  `verified_alpha` (strong but no primary source yet) is medium; `candidate` is a lead.
- **Signals are the alpha.** When `sectors[x].signals` is non-empty, that sector is
  "lighting up" — it deserves visual emphasis. Early files may have empty signals (the
  engine needs a few weeks of history for some rules); build for signals appearing later.

---

## 3. The task — rebuild the Capital Flow Map

### 3a. Remove the current build
The existing Capital Flow Map is hand-authored and must be **deleted**, then rebuilt on
the new data contract. Remove:
- `src/data/capitalFlowData.js` (the hand-authored dataset — replaced by `capitalMap.json`)
- `src/components/research/capitalflow/` — `CapitalFlowMap.jsx`, `FlowGraph.jsx`,
  `EntityPanel.jsx`, `Legend.jsx`, `FilterBar.jsx`, `FlowDetailCard.jsx`, `layout.js`,
  `format.js`, `README.md`

First **find where it's mounted** (search the Research section, e.g.
`ResearchDetail.jsx` / `ResearchCovers.jsx`, for the CapitalFlowMap import) so you can
rewire the new component into the same slot.

**Keep the visual language, not the data.** The old build had a strong institutional
look — muted sector-zone clusters, tier stars, per-deal-type edge colors, a side panel.
You may reuse that visual vocabulary; you are replacing the *data source and structure*,
not the aesthetic. (Dark mode only — never add a light/dark toggle; project rule.)

### 3b. Build the new component
Build a new Capital Flow Map that reads `src/data/capitalMap.json` and renders:
- **Nodes** positioned by `sector` (cluster zones), sized by `capital`, styled by
  `kind`/`cls`/`tier`. Allocators on the source side, targets on the sink side.
- **Flows** as edges, colored by `event_type`, weight/opacity by `amount`, and
  **confidence conveyed by `status`** (e.g. solid = verified, dashed = candidate).
- **Sector zones** that visually emphasize any sector with a non-empty `signals` array
  (this is the whole point — surfacing where capital is swarming).
- **A detail panel** on node/flow click showing the underlying flows (allocator → target,
  amount, event_type, date, status, source tier).
- **Filters** by sector, allocator class, status, and event type.
- **A "generated" stamp** somewhere (from `meta.generated`) so the user knows the data date.
- Everything derived from the file — no hard-coded entities. If the next week's file has
  new nodes or a new fired signal, the map must show them with no code change.

Suggested `event_type` → edge-color mapping (adjust freely): equity/minority_stake/
funding_round/corporate_investment → "equity" family; project_finance → "debt"; acquisition
→ "acquisition"; fund_launch → "fund"; grant → "grant"; spv → "SPV". Provide a legend.

Follow project conventions: React 18 + Vite, components under
`src/components/research/`, relative imports, `npm run build` must pass before pushing.

---

## 4. Reconstruction rules (how to treat the data each update)

The engine ships cumulative data; these rules govern what you show and when you retire it.

- **Inclusion:** show a node if it has ≥1 `verified` or `verified_alpha` flow. Do not put
  `candidate`-only entities on the main map — put them in a muted "watch / unconfirmed"
  affordance (a side list or a toggle). Always show any entity in a sector that has a
  fired signal.
- **Emphasis:** node size ∝ `capital`; key-tier allocators and Tier-1 flows read
  strongest; **highlight sectors carrying a fired signal**.
- **Staleness / retire (FINALIZED, see §5):** a node with `"stale": true` is
  **de-emphasized** (cooling state / muted), never deleted on sight. It is **dropped from
  the visual only after it has been stale across two consecutive weekly updates AND has no
  verified flow** — but it stays in the data/history. The map is memory; nothing is
  silently erased.
- **Change handling each update:** new nodes appear in their sector zone sized by capital;
  existing nodes update size/last_activity; a node newly in a signalling sector gets
  promoted to highlighted. If something visible last week is dropped, note it (a small
  "cooled off" area is fine), don't just make it vanish.

The engine also emits a `CHANGELOG.md` next to the JSON listing new/stale entities each
run — you can surface a "what changed this week" note from it if useful (optional).

---

## 5. The three handoff decisions — FINALIZED

1. **Node-drop policy:** de-emphasize on first stale (180d no activity); fully drop from
   the visual only after **two consecutive weekly updates stale + no verified flow**; keep
   in data/history always. (See §4.)
2. **Visual latitude:** you own the visuals **completely** — layout, colors, interactions,
   animation — and should match the dark institutional aesthetic. You have **zero data
   latitude**: never invent entities, flows, amounts, or statuses, and never override a
   status. Render the file faithfully; style it freely.
3. **Delivery mechanism:** the engine writes `capital_map.json` to
   **`src/data/capitalMap.json`** in this repo; the component imports it at build time and
   Vercel redeploys on push. A user-provided file (manual upload) overwrites the same path
   and renders identically. (Future option if data-only updates without redeploys are ever
   wanted: switch to a runtime `fetch()` of the JSON from a static host — not needed now.)

---

## 6. Update timing the user expects
- **Weekly (default):** the engine runs and refreshes `capitalMap.json` automatically.
- **On-demand:** the user can ask for a refresh at any time; same output, same path.
- **Manual upload:** the user can hand over a `capital_map.json` directly and have it
  implemented — just replace `src/data/capitalMap.json` and rebuild. (Low priority, but
  the consumer path is identical, so it comes for free.)

Your build only needs to render the file at that path correctly; the scheduling itself
lives on the engine side.

---

## 7. Definition of done
- Old Capital Flow Map files removed; new component mounted in the same Research slot.
- New map renders `src/data/capitalMap.json` end-to-end: sector-zone nodes, event-typed
  flows, status-based confidence styling, signal-highlighted sectors, click-through detail
  panel, filters, and a generated-date stamp.
- Nothing hard-coded — swapping in next week's file changes the map with no code edits.
- `npm run build` passes. Dark mode only.
