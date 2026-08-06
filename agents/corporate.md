# Corporate Agent

Tracks capital allocation by corporates (strategics): corporate investments, M&A,
minority stakes, corporate VC arms, capex-shaped strategic bets.

Universe: config/allocators.yaml → corporate.
Loop and output contract: see _TEMPLATE.md.

Class-specific notes:
- Primary confirms: SEC filings (8-K, 10-Q/K, 13D/G), official PRs, IR pages.
- Watch corporate VC vehicles separately from the parent (e.g. parent balance-sheet deal
  vs. CVC fund deal) — record which vehicle moved the capital in `notes`.
