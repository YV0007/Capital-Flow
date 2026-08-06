# Alternative Managers Agent

**Read `agents/CONTEXT.md` first.** Then read the `alt_managers:` block of
`config/allocators.yaml` — your watchlist.

## Who you track
PE / infra / credit / mega-funds: SoftBank, Blackstone, BlackRock (incl. GIP),
DigitalBridge, Brookfield, KKR, Blue Owl — plus new alt managers financing the buildout.

## What to look for
- `project_finance`, `fund_launch`, `acquisition`, `minority_stake`, `follow_on`, `spv`.
- Infra/energy/datacenter platform deals and the debt behind them.

## Mandatory checks per name
- Fund press releases, IR/investor pages, SEC filings (ADV, 8-K for public parents).
- Tier 2 (Preqin/PitchBook) for fund closes and platform deals.

## Class gotchas
- Distinguish *committed* capital from an announced *target/program size* — flag
  `amount_estimated: 1` when the number is a target, not a close.
- Project finance is often disclosed in tranches over time; record the tranche and the
  total in `notes`.
- These are the buildout's balance sheet — power, datacenters, neocloud debt land here.
