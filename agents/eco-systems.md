# eco-systems — L5, L8–L9

**Read `agents/eco-CONTEXT.md` first.** Then the `L5`, `L8`, `L9` blocks of
`config/eco_layers.yaml`.

You own everything between the chip and the building: packaging, boards, the network that
makes thousands of GPUs behave as one machine, the servers, the cooling, and the people
who physically build the site. This is where the industry's real, current bottlenecks sit —
not in the chip.

## Who you track
- **L5 СБОРКА** — advanced packaging (TSMC CoWoS, ASE, Amkor, BESI hybrid bonding), PCB
  and substrates (Ibiden, Shinko, Unimicron, TTM).
- **L8 СВЯЗЬ** — photonics; network silicon (Broadcom Tomahawk/Jericho, Marvell, Astera
  Labs, Credo); interconnect fabric (NVLink, InfiniBand, Ultra Ethernet); optical modules
  (Innolight, Eoptolink, Coherent, Lumentum); dark fiber and cable (Corning, Prysmian).
- **L9 СИСТЕМЫ** — server ODM/OEM (Foxconn/Hon Hai, Quanta, Wistron, Dell, Supermicro);
  liquid cooling (Vertiv, Boyd, CoolIT, nVent); MEP and contracting (Comfort Systems, EMCOR,
  Quanta Services).

## What to look for — concretely
- **Named manufacturing partners for a named platform.** "X will manufacture the Y system"
  in a press release from either side → `partner` or `supply` with the platform in `note`.
- **Customer concentration at the ODM/component level.** The supplier's own 10-K/20-F
  saying one customer is >10% of revenue is the cleanest possible `strength` evidence, and
  it points the edge the right way round.
- **Design wins with a named platform generation.** Retimer, optical DSP and cooling
  vendors announce these; that is an R4 qualification for an emerging name.
- **Rack-level integration contracts** — who assembles the rack, who supplies the busbar,
  who supplies the CDU.
- **Cooling as the new gate.** Rack power density statements in vendor PRs and in
  hyperscaler filings; quote the number.
- **Construction capacity.** Contractor backlog language in a 10-Q/10-K — "our backlog
  attributable to data center customers…" is a real edge into L10.

## Mandatory tier-1 checks per anchor
- Foxconn (Hon Hai): annual report + MOPS announcements; the English investor-relations
  release is citable.
- Vertiv, Amkor, Astera Labs, Credo, Coherent, Comfort Systems: latest 10-K, then the most
  recent quarterly, then the IR newsroom.
- For the optical/module names, the customer is often named only in the *customer's*
  materials — check both sides.

## Layer gotchas
- **Packaging is TSMC's, but it is a separate dependency.** Give TSMC an L5 row when the
  edge you are writing is about CoWoS, and put `tech_node: cowos` on that edge. Still one
  TSMC node.
- **Fabric is a protocol, not a box.** NVLink and InfiniBand are `tech_node`s owned by
  NVIDIA; the edge they label is usually NVIDIA → the system integrator or the cloud.
- **ODMs are low-criticality by design.** An assembler with many alternatives scores in the
  20s. Resist inflating it because the revenue is big — the rubric measures
  replaceability, not size. Foxconn's score comes from scale-plus-qualification, and it
  should still be nowhere near ASML's.
- Optical-module makers are often Chinese and not US-listed; the citable document is then
  the customer's filing or a Tier-`press` piece. Say so in `note`.
