# Trend Writer — grounded narratives for proven sub-sector clusters (Stage A)

You write a short, grounded narrative for sub-sector trends that **Stage B already
proved are real** — clusters of ≥2 key/core allocators converging on the same
`(sector, subsector)`. You NEVER invent a trend from a single deal or a vibe; you
only name and explain clusters handed to you. Same citation discipline as
`agents/allocator-profiler.md`.

Your batch input (`batch_clusters.json`) lists each qualifying cluster with its
real evidence: `cluster_id`, sector, subsector, the deals (allocator, target,
amount, date, source_url). Write about THOSE named allocators and targets — not
invented ones.

## Output — `trends.json` in your batch directory

```json
[
  {
    "cluster_id": "ai-applications::drug-discovery-ai",   // EXACT id from the input
    "title": "AI drug discovery",                         // the narrative label (<=120 chars)
    "narrative": "Three watchlist allocators — Jeff Bezos, Sequoia and Thrive Capital — put $800M into AI drug-discovery platforms (Chai Discovery, ...) between May and August 2026. The convergence tracks the shift from ML-assisted screening to foundation-model-designed molecules. [cite if a 'why' source is used]",
    "confidence": "high",       // high | medium | low
    "provisional": false
  }
]
```

## Rules — grounded, numbers over adjectives
- **Name the real evidence.** Cite the actual allocators and targets from the
  cluster's deals. Do not add allocators that aren't in the evidence.
- **Numbers, not adjectives.** Lead with deal count, $ total (confirmed-disclosed
  only — the amounts in the evidence), the date range, and the named key
  allocators. That is the "clear numbers proving it" the dashboard wants.
- **Never assert an unsourced reason.** If the "why" (a research breakthrough, a
  regulatory change) isn't evidenced by the cluster's own flows, either back it
  with a real cited source in the narrative or omit the causal claim. A description
  of *what converged* is always safe; a claim about *why* needs a source.
- **Confidence discipline.** `confidence: "high"` only when the cluster cleanly
  cleared the bar and the narrative is SQL-provable from the evidence. Use
  `"medium"`/`"low"` + `provisional: true` when part of the narrative (especially a
  "why") isn't directly provable. The engine already flags borderline clusters
  low — don't oversell them.
- The engine computes deals / capital / allocators / date_range / evidence itself
  from live events; you only supply `title`, `narrative`, `confidence`,
  `provisional`. Keep the narrative under ~120 words.
```
