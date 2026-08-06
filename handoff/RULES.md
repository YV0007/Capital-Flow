# Handoff reconstruction rules (v1 — tunable)

The dashboard (ab-investment) is a **separate repo**. The connection is a handoff,
not a live feed: the engine writes `handoff/capital_map.json` + `handoff/CHANGELOG.md`,
and a Claude session on the dashboard side reads them to **reconstruct / update the
Capital Flow Map** — add new entities, retire stale ones, adjust visuals.

These are the rules that session follows. They are deliberately conservative for v1;
tune the thresholds as the data grows.

## What the dashboard session receives
- `capital_map.json` — full current map state:
  - `nodes[]` — allocators + targets, each with `kind`, `cls`, `tier`, `sector`,
    `deals`, `capital`, `first_seen`, `last_activity`, `stale`.
  - `flows[]` — edges (allocator → target) with `amount`, `event_type`, `status`,
    `date`, `tier`, `sector`.
  - `sectors{}` — per-sector totals + fired `signals`.
- `CHANGELOG.md` — new and stale entities since the previous handoff.

## Inclusion — when to put an entity on the visual map
- Include a node if it has **≥1 `verified` or `verified_alpha` flow**. Do not surface
  `candidate`-only entities on the public map (they can live in a "watch" list).
- Always include an entity that a **fired signal** points at (sector with a
  sector_swarm / acceleration / first_entry theme), even if small.

## Emphasis — how prominent
- Node size ∝ `capital`. Key-tier allocators and Tier-1-sourced flows read strongest.
- Highlight sectors carrying a fired signal this cycle (`sectors[].signals`).

## Staleness — when to retire content
- A node with `stale: true` (no activity in 180 days — see `STALE_DAYS`) should be
  **de-emphasized**, not deleted: move to a muted state or a "cooling" tier.
- Only fully drop a node when it has been stale for **two consecutive handoffs** AND
  carries no verified flow. Keep history; the map is cumulative memory, not a snapshot.

## Change handling each cycle
- New entities (from `CHANGELOG.md`): add them, sized by capital, placed in their
  sector zone.
- Existing entities: update size/last_activity; promote to highlighted if newly
  carrying a signal.
- Never silently remove an entity that was visible last cycle — if dropped, note it.

## Finalized decisions (see handoff/DASHBOARD_BRIEF.md §5)
- **Node-drop policy:** de-emphasize on first stale (180d); drop from the visual only
  after two consecutive weekly updates stale + no verified flow; keep in data always.
- **Visual latitude:** the dashboard session owns visuals completely; zero data latitude
  (never invent or override entities/flows/amounts/status).
- **Delivery — auto-push:** the engine auto-commits `capital_map.json` →
  `ab-investment/src/data/capitalMap.json` directly to `main` and pushes (only that file);
  Vercel deploys. No review gate. A user-uploaded file overwrites the same path identically.

The full consumer specification lives in **handoff/DASHBOARD_BRIEF.md** — hand that entire
file to an ab-investment Claude Code session to rebuild the map.
