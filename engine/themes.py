"""Theme engine: SQL signal rules over events -> themes table.

Rules are declared in config/rules.yaml; each rule id maps to a SQL query here.
Example — sector_swarm (N distinct key allocators into one sector in a window):

    SELECT sector, COUNT(DISTINCT e.allocator_id) AS investors, SUM(amount_usd) AS total
    FROM events e JOIN allocators a ON a.id = e.allocator_id
    WHERE e.disclosed_date >= date('now', ?) AND a.tier = 'key'
    GROUP BY sector
    HAVING investors >= ?;

Fired rules are written to the themes table with their evidence event ids.
"""


def run(week: str) -> None:
    """Evaluate all rules for a run week and persist fired themes."""
    raise NotImplementedError("Build step 6: theme engine")
