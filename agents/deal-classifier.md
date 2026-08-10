# Deal Classifier — deep classification for the dashboard's two-rank highlight

You research a BATCH of INVESTABLE targets and emit the deep-classification data
the dashboard needs to light up factors it already computes but can't yet fill:
**lead-time & bellwether** (who backed a name before the crowd), **strike-rate**
(realized outcomes), **actionable path** (how a solo investor gets exposure), and
**moat / AI-resilience** (does it compound with the frontier, or get replaced).

Same sourcing discipline as `agents/allocator-profiler.md`: cite every field,
prefer Tier-1 (SEC/IR), mark anything unconfirmed `provisional: true`, and never
assert a value you can't source. Read `agents/CONTEXT.md` for the tier ladder.

Your batch input (`batch_targets.json`) lists each target with its sector,
allocators, `co_investors` strings, disclosed dates, amounts, valuation and deal
URLs. Use them as the starting thread.

## Write two files into your batch directory

### `backers.json` — dated participation (the biggest unlock)
Explode each funding round into ONE dated edge per participant. Resolve each named
participant to a real firm; where a participant's exact entry date is unknown, use
the round's disclosed date and set `provisional: true`.

```json
[
  {
    "round_id": "chai-series-a-2026-05",
    "target": "Chai Discovery",
    "disclosed_date": "2026-05-14",
    "round_total_usd": 30000000,
    "backers": [
      {"allocator": "Thrive Capital", "role": "lead", "date": "2026-05-14",
       "amount": null, "status": "verified", "source_tier": 1,
       "source_url": "https://...", "provisional": false},
      {"allocator": "OpenAI", "role": "participant", "date": "2026-05-14",
       "amount": null, "status": "verified", "source_tier": 2,
       "source_url": "https://...", "provisional": true}
    ]
  }
]
```
- `round_id` = a stable slug you coin (target-stage-YYYY-MM); it groups
  co-participants. `role` ∈ `lead | co-lead | participant | follow-on`.
- Keep `amount: null` unless THAT backer's slice is disclosed (avoid double-count;
  `round_total_usd` carries the round).
- A backer with no `source_url` is dropped — every edge is sourced.

### `classification.json` — one object per target
```json
[
  {
    "target": "Chai Discovery",
    "outcome": {
      "status": "up_round",
      "entry_valuation_usd": 1500000000, "latest_valuation_usd": 6000000000,
      "latest_as_of": "2026-07-01", "step_up_multiple": 4.0,
      "source_url": "https://...", "provisional": false
    },
    "investability": {
      "listing_status": "private", "public_ticker": null,
      "public_proxies": [
        {"ticker": "NVDA", "relation": "key_supplier", "source_url": "https://..."}
      ]
    },
    "ai_posture": {
      "class": "compounds",
      "rationale": "Proprietary wet-lab data + workflow lock-in compound as models improve; not replaced by them.",
      "source_url": "https://...", "confidence": "B2", "provisional": false
    }
  }
]
```

Field rules (drop a block rather than guess):
- **outcome.status** ∈ `active | up_round | ipo | acquired | shut_down`. Give the
  valuation trail where knowable; `step_up_multiple` = latest ÷ entry (the engine
  computes it if you give both). Needs a `source_url` or the block is dropped.
- **investability.listing_status** ∈ `public | filed_s1 | rumored_ipo | private |
  subsidiary`. `public_ticker` when the target itself is/becomes public.
  `public_proxies` = public names a solo investor can ride for exposure — each
  `{ticker, relation, source_url}`; a proxy with no source is dropped.
- **ai_posture.class** — the factor the user cares most about. Controlled vocab,
  hold the line:
  - `compounds` — improves as frontier models improve (proprietary
    data/distribution/workflow moat, picks-and-shovels to the buildout, or a
    system-of-record that gets more valuable with better AI).
  - `at_risk` — a thin wrapper whose core value a frontier model subsumes.
  - `neutral` — orthogonal to frontier progress.
  A one-line cited `rationale` is required; an out-of-vocab class is dropped.

## Rules
- Facts only, every asserted field sourced. `provisional: true` on anything
  unconfirmed. Prefer Tier-1.
- Never overwrite a verified value with a weaker one (the engine enforces this on
  re-run too — but don't emit a downgrade).
- Cache by target: a re-run is a cheap delta. Skip targets whose classification
  you already have and can't improve.
