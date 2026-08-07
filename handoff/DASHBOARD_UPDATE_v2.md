# Capital Flow Map — Update v2 (delta brief)
### Hand this whole file to the ab-investment Claude Code session.

The Capital Flow engine has shipped a major upgrade. **`src/data/capitalMap.json` in this
repo already contains the new data** (it's deployed and current) — but the dashboard code
consumes **none** of it yet. This brief is the delta: four new capabilities to render.

Nothing about the existing contract changed — all previous fields behave exactly as before.
Everything here is **additive**, so nothing you already built should break.

⚠️ Before starting: this repo has **uncommitted work** in `CapitalFlowMap.jsx`,
`FlowGraph.jsx`, `Legend.jsx`, `layout.js`, `PortfolioDeep.jsx`. Commit or stash it first
so this change doesn't tangle with it.

---

## 1. Confidence grades on every flow (NEW)

Every flow now carries a two-axis intelligence grade (Admiralty/NATO style: source
reliability × information credibility) plus a 0–100 score.

```jsonc
{
  "source": "alloc:BlackRock", "target": "target:Aligned Data Centers",
  "sector": "datacenters", "event_type": "acquisition", "amount": 40000000000.0,
  "status": "verified", "date": "2026-07-21", "tier": 1,
  "confidence": 100,        // NEW — 0–100 score
  "grade": "A1"             // NEW — letter = source reliability A(best)–E, digit = credibility 1(best)–5
}
```

**Live distribution right now:** `A1`×11, `C3`×13, `C4`×10, `B3`×1, `B4`×1.

**What to build:**
- Show `grade` + `confidence` in the flow-detail card and the entity panel
  (e.g. `A1 · 100` with a tooltip: *A = primary/official source, 1 = confirmed by primary*).
- Use `confidence` for visual weight — high-confidence flows should read stronger
  (opacity/saturation). Keep `status` styling as-is; this is an additional axis, not a
  replacement.
- Let users **sort/filter by confidence**. This is the "can I act on this?" signal.

Grade key (for tooltips/legend):
`A` primary/official (SEC, IR, gov) · `B` top data platform · `C` quality press ·
`D` specialist/analyst · `E` social/rumor.
`1` confirmed by primary · `2` ≥2 independent sources · `3` single credible source ·
`4` uncorroborated · `5` doubtful.

## 2. `confidence_threshold` — main map vs Watch (NEW, top level)

```jsonc
{ "confidence_threshold": 60, ... }
```

This is the engine's declared floor. **Flows scoring ≥ 60 belong on the main map; below 60
belong behind the "Watch" toggle.** Right now that's **26 of 36 flows** on the main map.

**What to build:** read the value from the file (do NOT hardcode 60 — the engine may tune
it) and use it as the default split, in addition to your existing status-based inclusion
rule. A node reaches the main map if it has ≥1 flow at or above the threshold.

## 3. `themes` — a second dimension alongside sectors (NEW, top level)

Themes are **cross-cutting narratives, orthogonal to sectors**. A deal has one structural
`sector` (where it sits in the stack) *and* one `theme` (which narrative it belongs to).
Signals form around both.

```jsonc
"themes": {
  "ai_infrastructure": {
    "deals": 13, "capital": 105497000000.0, "allocators": 10,
    "signals": [ { "theme": "ai_infrastructure: 5 key allocators converge (30d)",
                   "rule": "theme_swarm", "strength": 5.0 } ]
  },
  "ai_applications": { "deals": 5, "capital": 13240000000.0, "allocators": 3, "signals": [] }
}
```

Same shape as the existing `sectors` map, so it can reuse that rendering.
The 10 canonical themes: `frontier_ai`, `ai_infrastructure`, `ai_applications`,
`defense_ai`, `energy_for_ai`, `robotics_embodiment`, `sovereign_ai`, `biotech_ai`,
`space`, `crypto_ai`.

**What to build:** a **theme filter/toggle** alongside the sector filter — ideally a view
switch ("group by sector" ⇄ "group by theme"), or at minimum theme chips in the filter bar
plus theme totals somewhere visible. Themes with non-empty `signals` get the same
highlight treatment sectors do.

**Note:** flows themselves don't carry a `theme` field — theme lives at the aggregate level
in `themes{}`. If you need per-flow theming, map via the flow's `sector` (ai-labs→frontier_ai,
datacenters/ai-compute/semiconductors/neocloud/networking/cloud-hyperscale/fab-equipment→
ai_infrastructure, power-energy/nuclear→energy_for_ai, robotics→robotics_embodiment,
defense-tech→defense_ai, ai-applications/ai-data→ai_applications).

## 4. `network` tag on nodes (NEW)

Individual allocators can belong to a tracked elite network:

```jsonc
{ "id": "alloc:Peter Thiel", "label": "Peter Thiel", "kind": "allocator",
  "cls": "individual", "tier": "core",       // NOTE: "core" is a NEW tier value
  "network": "paypal_mafia",                  // NEW — or null
  "deals": 3, "capital": 6164585000.0, ... }
```

Networks: `paypal_mafia`, `thiel_extended`, `thiel_fellowship` (currently only
`paypal_mafia` has live events; build for all three).

**What to build:** a visual treatment for networked allocators (badge/outline/color accent)
and a **filter by network**. Also handle the new `tier` value **`core`** — tiers are now
`core` (highest) | `key` | `watch` | `null`. Treat `core` at least as strongly as `key`.

## 5. New signal rules appearing in `signals[]`

`sectors[x].signals` and `themes[x].signals` now carry more rule types. Same
`{theme, rule, strength}` shape — but render the `rule` so users know *why* something lit up:

| `rule` | meaning |
|---|---|
| `sector_swarm` | N key allocators into one sector in a window |
| `theme_swarm` | N key allocators converge on one theme (cross-sector) |
| `smart_money_follow` | a key allocator led, others followed shortly after |
| `beneficiary_concentration` | N private flows converge on one **public ticker** |
| `stealth_accumulation` | repeated stakes into one target |
| `repeat_conviction` / `network_convergence` / `defense_network_convergence` | network-level patterns |

**`beneficiary_concentration` is the highest-value one** — it names a public ticker the
private capital points at (e.g. *"NVDA (NVIDIA): 9 private flows converge"*). Consider
surfacing these prominently; they're the actionable public read-through.

---

## Definition of done
- Flow detail shows `grade` + `confidence`; confidence affects visual weight; user can
  filter/sort by it.
- Main-map vs Watch split uses `confidence_threshold` read from the file.
- Theme dimension is browsable (filter or view switch) with signal highlighting.
- Networked allocators are visually distinct and filterable; `tier: "core"` handled.
- Signal `rule` types are rendered/legended, with `beneficiary_concentration` surfaced well.
- Nothing hardcoded — next week's file changes everything with no code edit.
- `npm run build` passes. Dark mode only.
