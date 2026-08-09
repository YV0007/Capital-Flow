# Prompt for the ab-investment (dashboard) Claude Code session

Copy everything below the line into a Claude Code session in the `ab-investment`
repo.

---

The Capital Flow engine (the separate data repo) has taken ownership of entity
reference data — the "what this is" card content. Adjust the dashboard to consume
it. Context and instructions:

## What changed

`src/data/capitalMap.json` (delivered by the engine, auto-pushed to main each
cycle) now carries, on **target nodes** (`nodes[]` where `kind: "target"`):

- `description` — 1–3 researched sentences on what the entity is (company,
  data-center project, fund vehicle), in the same style as the existing Atoms
  card: what it is, who's behind it, scale/context. Source-backed, ≤60 words.
- `links` — array of `{kind, label, url}`:
  - `kind: "website"` — official site, label is the bare domain (e.g. `atoms.co`);
    may be absent for projects/SPVs with no site.
  - `kind: "read_more"` — exactly ONE good article about the entity, label is the
    publication name (e.g. `Reuters`). Always present when a reference exists.
- `reference_as_of` — research date.

Also already present since payload v3 (wire these too if not yet rendered):
- `nodes[].country` on allocator nodes (national affiliation, for flags),
- `aggregates` (top_sector / top_company / thesis_shares, each with a `basis`
  string — render as-is, never recompute),
- `allocators` (canonical per-allocator summary: rollup + profile + track_record
  rows with `provisional` + `source_url` on every row),
- `audit` (the engine's verification verdict for the shipped payload).

## What you must change

1. **Entity detail panel ("WHAT THIS IS" / About card):** when the selected node
   has `description`, render it in the About card with the `website` chip and
   the `read_more` link (publication-labeled). The "No profile on file yet — use
   search below to look it up" fallback should now appear ONLY for nodes without
   engine data.
2. **Precedence:** engine node fields (`description`/`links`) take precedence
   over the local `src/data/entityReference.json` — exactly as that file's own
   `_note` anticipates. Keep the local file solely as a fallback for legacy nodes
   the engine hasn't referenced; do NOT hand-curate new entries for engine-covered
   nodes, and do not edit engine-delivered data (zero data latitude, per
   handoff/RULES.md: visuals are yours, data is the engine's).
3. **Allocator detail panels:** allocator narrative now comes from
   `capitalMap.json → allocators[<name>].profile` (background, focus, style,
   thesis, latest_investments_summary, strategy with `strategy_source_url`
   attribution) and `track_record` (per fiscal year; each row has `provisional`
   and `source_url`). Always show a "provisional / unaudited" marker on
   provisional rows and keep source attribution visible or one tap away.
4. **Ongoing:** every weekly delivery may add new targets that already carry
   references — nothing to do on your side; render what arrives. If you spot a
   target that renders with the empty-state card, that's an engine-side coverage
   gap (its audit flags any ≥$1B target without a reference as W6) — report it
   back rather than hand-filling it.

## Verify after wiring

- Open "OpenAI southern Ohio 10GW data center" — it should show a researched
  description + read-more link instead of "No profile on file yet".
- Open "Atoms" — should render from engine data now (visually identical is fine).
- Spot-check 3–4 random targets and 2 allocators (e.g. Blackstone: segment
  track-record rows carry `scope` labels and provisional flags).
