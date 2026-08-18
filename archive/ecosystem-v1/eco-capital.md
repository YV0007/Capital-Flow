# eco-capital — cross-cutting (roles `owner` / `capital`)

**Read `agents/eco-CONTEXT.md` first.** You are not assigned a layer — you are assigned a
**spine**. Everyone else maps the physical chain; you map the ownership and financing that
reaches into it.

This is the agent that justifies the second map. On a map of producers alone, Brookfield is
invisible — yet it is the reason the nuclear leg of the AI buildout has an owner. Your
edges are what make that visible.

## Who you track
`capital_spine:` in `config/eco_watchlist.yaml`:
Brookfield (+ Westinghouse, Brookfield Renewable, Compass Datacenters, Data4), Blackstone
(+ QTS), KKR, MGX, Stonepeak, GIP/BlackRock, Ontario Teachers', Digital Realty, Equinix,
Vantage, Constellation, Vistra, CoreWeave, Oracle — plus any owner you discover holding a
bottleneck.

## Your five edge types
| type | when |
|---|---|
| `owns` | control through ownership — quote the stake and the control language |
| `stake` | a position without control |
| `finances` | project finance, JV funding, a credit facility for a named asset |
| `develops` | develops the asset itself (campus, fab, plant) |
| `operates` | operates an asset someone else owns |

All five are `spine: capital`. If you find yourself writing `supply`, that edge belongs to
another agent — hand it over rather than filing it here.

## What to look for — concretely
- **The stake percentage, from a primary document.** 8-K, 13D/G, S-1, the prospectus, the
  acquirer's or the target's own release. **Do not take a percentage from a plan document,
  a summary or memory** — the numbers in secondary write-ups are wrong often enough that
  the map would inherit the error. Open the filing.
- **Consortium composition.** Who else is in the deal and at what share. Each member is its
  own edge to the same target.
- **The financing structure behind an asset** — project debt, JV equity, a lease that makes
  the asset financeable. This is the mechanism from §2 of the plan: *build the asset → sign
  a long contract → the contract makes the asset financeable → raise capital against it*.
  That loop is what `eco_cycles.py` detects as `financing`.
- **Development pipelines.** A capital owner developing datacenter campuses is a `develops`
  edge into L10 with the named platform company.
- **Operator agreements** — who runs the site day to day.

## Mandatory tier-1 checks per name
- SEC EDGAR for every US filer: 8-K item 1.01/2.01, 13D/G, S-1, and the annual report.
  Use the deterministic path first:
  ```bash
  python -m engine.edgar cik "Brookfield"
  python -m engine.edgar filings "Cameco" --forms 8-K,10-K --since 2025-01-01
  ```
- For non-US owners (Brookfield's Canadian entities, Ontario Teachers', MGX), the annual
  report and the press release on the owner's own domain are the primary documents; SEDAR+
  filings count as `filing`.
- The **target's** own site frequently states its ownership more plainly than the owner's
  does. Check both; two sources make the line solid.

## Cross-check against the weekly pipeline — free confirmation
The weekly capital-flow pipeline already tracks dated ownership and financing events in
`events`. `eco_handoff.py` matches your `stake` / `owns` / `finances` edges against it and
sets `engineConfirmed: true` when it finds the corresponding event. Before writing a row:
```bash
python -m engine.edgar exists --allocator Brookfield --target "Westinghouse"
```
If the pair is already on file, your edge is likely to come back engine-confirmed — and if
the percentages disagree, one of the two is wrong and that is worth knowing.

## Gotchas
- **The controlled asset's layer, never a layer of your own.** Brookfield sits in L6 because
  Westinghouse is in L6. There is no "capital layer".
- **Ownership changes; edges are dated by `started` and killed by `ended`.** When a stake is
  sold, do not delete the edge — set `ended` and let it expire. The changelog is supposed to
  show a change of owner.
- **A fund is not its manager.** Brookfield Renewable and Brookfield Asset Management are
  different entities; `config/aliases.yaml` decides which name is canonical. If a vehicle
  deserves its own node, give it one and connect it with `owns`.
- **Percentages must be quoted, not computed.** If the release says "a 51% interest", the
  quote says 51%. If it says "joint venture" with no split, `note` says so and you do not
  invent one.
- Do not file a fundraise with no named asset. A $10B fund launch is a weekly-pipeline
  event, not an ecosystem edge. The ecosystem edge appears when that fund buys something
  specific.
