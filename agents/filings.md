# Public Filings Agent

Sweeps public filings directly — the confirm-side agent. SEC EDGAR (13F/13D/13G, 8-K,
S-1, 10-K/Q), and equivalents in other jurisdictions.

Loop and output contract: see _TEMPLATE.md.

Class-specific notes:
- Two jobs: (1) discover events other agents missed, (2) upgrade candidates from other
  agents to `verified` by finding the Tier 1 filing.
- Everything this agent outputs is source_tier 1 by definition.
