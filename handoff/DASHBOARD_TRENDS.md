# Prompt for the ab-investment session — render the sub-sector `trends` block

Paste into a Claude Code session in `ab-investment`. New, additive payload field;
nothing existing changes. The engine went one level below sector/theme signals:
"which specific narrative within a sector, backed by which named investors, with
real numbers."

## What arrived in `capital_map.json`

Top-level **`trends`**, keyed to your existing window ids (`digest.js`:
`week` / `month` / `all`) — a direct lookup, no remapping:

```jsonc
"trends": {
  "month": [
    { "title": "Drug Discovery Ai", "sector": "ai-applications",
      "subsector": "drug-discovery-ai",
      "deals": 3, "capital_usd": 800000000,
      "date_range": ["2026-07-14","2026-08-06"],
      "allocators": ["Jeff Bezos","Sequoia","Thrive Capital"],
      "evidence": [119,121,122],
      "narrative": null,          // grounded paragraph; null until the writer agent runs
      "confidence": "high",       // "low" = borderline (quiet window) — show it as tentative
      "provisional": false }
  ], "week": [...], "all": [...]
}
```

Each window holds the **top 1-3** clusters, ranked by capital then allocator count.

## What to render
- A "Trends" strip/section per window (reuse the 7d/30d/all toggle you already have).
- Per entry: the **title**, the **named `allocators`** (chips — link each to its
  node), and the **numbers** (`deals`, `capital_usd`, `date_range`). That is the
  core value; it's live even before narratives exist.
- **`narrative`** when present: the grounded "why + who" paragraph. When `null`,
  show just the title + numbers + allocators (don't invent prose).
- **`confidence: "low"` or `provisional: true`** → render tentatively (muted /
  "emerging" / a caveat). Never present a borderline cluster with the same
  certainty as a `high` one. The engine flags them so you don't have to judge.
- `evidence` are event ids → resolve to the underlying flows if you want a
  drill-down; it's the same id space as `flows[]`.
- An empty array for a window = no qualifying trend → render nothing (don't
  fabricate a filler).

## Boundary (unchanged)
Consume as facts; don't recompute the numbers or write your own narratives — the
trend narrative is engine-authored (Stage-A research agent), zero data latitude,
same as the rest. If a trend looks wrong, report it back; don't edit it.

## Verify
- The `month` window shows "Drug Discovery Ai" with Jeff Bezos / Sequoia / Thrive
  Capital and $800M; "Grid Storage" and "Defense Manufacturing" alongside.
- A `low`-confidence entry (e.g. a quiet `week`) renders visibly more tentative.
- Once the trend-writer agent runs, the same entries gain a narrative paragraph
  with no dashboard change.
