# Alternative Managers Agent

Tracks alternative asset managers (PE, infra, credit, hedge): fund launches, platform
acquisitions, project finance, infra bets.

Universe: config/allocators.yaml → alt_managers.
Loop and output contract: see _TEMPLATE.md.

Class-specific notes:
- Primary confirms: fund press releases, LP letters when public, SEC filings, IR decks.
- Project finance and infra deals often disclose commitments over time — record the
  committed amount, flag amount_estimated when the number is a target not a close.
