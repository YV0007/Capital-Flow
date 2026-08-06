"""Handoff: DB -> handoff/ files for the dashboard side.

The dashboard (ab-investment) is a separate repo. The connection is NOT a live
data feed: this module exports a self-contained map-state file that a Claude
session on the dashboard side consumes to RECONSTRUCT the Capital Flow Map —
adding new entities, retiring stale ones, adjusting visuals per handoff/RULES.md.

Planned outputs (contract pending, see ARCHITECTURE.md):
- handoff/capital_map.json   current map state: entities, flows, aggregates,
                             per-entity first_seen / last_activity / signal strength
- handoff/CHANGELOG.md       delta since last handoff (new / updated / stale)
"""


def run(week: str) -> None:
    raise NotImplementedError("Build step 9: handoff contract")
