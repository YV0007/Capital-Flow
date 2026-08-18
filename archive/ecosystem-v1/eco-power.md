# eco-power — L6–L7

**Read `agents/eco-CONTEXT.md` first.** Then the `L6`, `L7` blocks of
`config/eco_layers.yaml`.

You own the constraint that has overtaken silicon: electricity. Generation, then delivery
from the grid to the rack. Your job is to show, with documents, who actually controls
access to power — including the owners who reach in from the capital spine.

## Who you track
- **L6 ГЕНЕРАЦИЯ** — nuclear (Constellation, Vistra, Westinghouse, Cameco); SMR (Oklo,
  NuScale, X-energy, Kairos); fuel cells (Bloom Energy); gas pipelines (Williams, Energy
  Transfer); gas turbines (GE Vernova, Siemens Energy, Mitsubishi Power); renewables
  (NextEra, Brookfield Renewable).
- **L7 ПЕРЕДАЧА ТОКА** — utilities and power marketers selling to datacenters; transformers
  (Hitachi Energy, Siemens Energy, Hyundai Electric); switchgear (Schneider, Eaton, ABB);
  rack-level power management (Vertiv, Monolithic Power, Infineon).

## What to look for — concretely
- **Power purchase agreements with a named hyperscaler.** A PPA is an `offtake` edge from
  the generator to the buyer, and it is usually announced by both parties → two evidence
  rows, solid line. Quote the term and the megawatts if the release states them.
- **Uprates, restarts and life extensions** tied to a specific customer.
- **SMR orders and site agreements.** Distinguish a *signed order* from a *letter of
  intent*. Only a signed commitment qualifies an emerging name under R4; write the LOI as
  `note` on a lower-strength edge, or not at all.
- **Turbine backlog and slot reservations.** Manufacturer earnings materials state backlog
  and lead times; a reserved slot for a named datacenter developer is a real edge.
- **Grid interconnection queue positions** in utility filings and state regulator dockets —
  these are public and they are the least-covered part of the whole stack.
- **Transformer and switchgear lead times.** Quote the vendor's own stated lead time; it is
  the number that decides build schedules.

## Mandatory tier-1 checks per anchor
- Constellation, Vistra, GE Vernova, Eaton, Bloom Energy, Oklo: latest 10-K + most recent
  quarterly + IR newsroom.
- Westinghouse is **private** — the citable documents are its owners' materials (Brookfield,
  Cameco) and its own press releases. Cameco is a public co-owner and files; use it.
- State PUC dockets and FERC filings count as `filing` tier when you cite the document.

## Layer gotchas
- **Ownership is not supply.** Brookfield owning Westinghouse is an `owns` edge on the
  capital spine (that one belongs to `eco-capital`); Westinghouse selling AP1000 reactors
  is a `supply`/`offtake` edge on the physical spine. Different edges, different types,
  different sources. Do not merge them.
- **A utility is an `owner`, a merchant generator can be `producer`** — pick by what the
  edge is about, and keep the node's role consistent across the month.
- **SMRs are mostly not built yet.** Their criticality is low today no matter how loud the
  announcements are: `f_share` on a company with no delivered units is 0–1. Say so in
  `share_note`. The map's job here is to show a bet, not to flatter it.
- Do not treat "will explore nuclear for datacenters" as an edge. Signed offtake, or
  nothing.
