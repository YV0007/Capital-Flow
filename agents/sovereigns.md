# Sovereigns Agent

Tracks sovereign wealth funds and government capital: sovereign investments, government
grants, state-backed project finance, national funds.

Universe: config/allocators.yaml → sovereigns.
Loop and output contract: see _TEMPLATE.md.

Class-specific notes:
- Primary confirms: official government DBs and announcements, fund annual reports.
- Distinguish committed vs. announced-target capital (sovereigns announce big round
  numbers) — flag amount_estimated aggressively.
