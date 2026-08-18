# eco-silicon — L1–L4

**Read `agents/eco-CONTEXT.md` first** (what an edge is, the ten types, tiers, the CSV
contract, the iron rule). Then read the `L1`–`L4` blocks of `config/eco_layers.yaml`.

You own the narrow end of the funnel: materials → tools → chips → memory. This is where
the map's highest criticality scores live, and where a single company genuinely has no
substitute. Get this layer wrong and the whole map is decorative.

## Who you track
- **L1 СЫРЬЁ** — photoresist (JSR, Shin-Etsu, TOK, Fujifilm), specialty chemicals, GOES
  steel, InP/GaAs substrates, titanium alloys, HBM materials (Ajinomoto ABF film).
- **L2 ОБОРУДОВАНИЕ** — ASML, Applied Materials, Lam Research, Tokyo Electron, KLA;
  Zeiss SMT (ASML's optics); EDA — Synopsys, Cadence, Siemens EDA; Arm (IP).
- **L3 ЧИПЫ** — NVIDIA, AMD, Broadcom, Marvell; **foundries — TSMC, Samsung Foundry,
  Intel Foundry (they belong to L3, not a layer of their own)**; custom-ASIC design houses
  (Alchip, GUC, Socionext); wide-bandgap power silicon.
- **L4 ПАМЯТЬ** — SK Hynix, Samsung, Micron; HBM specifically, plus DRAM and NAND.

## What to look for — concretely
- **Supplier / customer concentration in the 10-K or 20-F.** The single most productive
  read on the whole map. Look for "customer A accounted for X% of net revenue", "we
  depend on a limited number of suppliers", "sole source". These sentences are edges with
  a `strength` number attached, handed to you.
- **Foundry dependence.** Fabless designers state in their annual report that they own no
  fabs. That sentence is the `supply` edge from the foundry, and it is a filing-tier quote.
- **HBM qualification and supply agreements.** Memory makers announce qualification and
  volume supply for a named accelerator generation — `supply`, `tech_node: hbm`.
- **Advanced-packaging capacity.** CoWoS is the classic bottleneck; the edge is
  foundry → chip designer with `tech_node: cowos`.
- **EUV.** ASML is the only maker of EUV scanners. That claim must still be sourced —
  ASML's own annual report or IR page states it; quote it, do not assert it.
- **EDA and IP as `platform` edges.** Synopsys/Cadence tools and Arm's ISA sit *inside*
  someone else's product. Direction: tool owner → chip designer.
- **Market share** from TrendForce / Omdia → `estimate` tier, and only to justify
  `f_share` / `share_note`. Never as the sole proof a relationship exists.

## Mandatory tier-1 checks per anchor
- ASML, TSMC, NVIDIA, Broadcom, SK Hynix, Micron: latest 10-K or 20-F, then the most
  recent quarterly, then the IR newsroom. TSMC and SK Hynix file 20-F / local annual
  reports — the English annual report on the IR site is the citable document.
- For each: read the risk-factor section for the words *sole*, *single source*, *limited
  number of suppliers*, *concentration*.

## Layer gotchas
- **Foundry ≠ layer.** TSMC is an L3 node with an L5 (packaging) row when its packaging is
  the dependency. It is still ONE node.
- **Samsung is three things** (memory L4, foundry L3, and more). One node, several layers,
  `:primary` on memory — that is where its criticality is highest.
- **Broadcom is two things** (custom ASIC L3, network silicon L8). One node, two layers.
- Do not confuse *designing* a custom chip with *making* it. Alchip and Broadcom design;
  TSMC makes. Two different edges with two different sources.
- A materials supplier with 90% share of a $200M niche still scores 5 on `f_share` — the
  rubric is share **of its function**, not of the industry. That is the point: small
  companies with no substitute are exactly what this map exists to surface.
