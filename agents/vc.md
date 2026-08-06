# VC Agent

Tracks venture capital: funding rounds, follow-ons, new fund launches, SPVs.

Universe: config/allocators.yaml → vc.
Loop and output contract: see _TEMPLATE.md.

Class-specific notes:
- Round participation ≠ leading — record lead vs. participant in `notes`.
- Fund launches are events too (event_type: fund_launch) — fund size is amount_usd.
- Tier 2 (Crunchbase/Dealroom) is usually the confirm here; Tier 1 when a portfolio
  page or PR exists.
