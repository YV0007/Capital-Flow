# Prompt for the ab-investment session — flip on the pending classification factors

Paste into a Claude Code session in `ab-investment`. The engine now ships the data
that four already-wired factors in `classification.js` were waiting on. These are
additive — turn them on; no ranker rewrite needed (only one CONFIG addition for the
new moat factor).

## What arrived in `capital_map.json`

**Flows now carry dated-backer fields** (`round_id`, `role`, `provisional`, and some
flows are `backer_edge:true`):
- **Lead-time** (Players rank): for each target, order its backers by flow `date`;
  a player who appears earlier than others on the same `round_id`/target entered
  before the crowd.
- **Bellwether pull** (Players rank): for a player's entry into a target, count the
  quality backers whose edges into that same target are dated *after* theirs.
- `backer_edge:true` flows are participation edges with no capital event of their
  own — use them for ordering/counts, but they carry no `amount` for capital sums.

**Investable target nodes now carry three blocks** (each may be absent → factor
stays "pending" for that node; never fabricate a fallback):
- `outcome` → **strike-rate**: `status`, `entry/latest_valuation_usd`,
  `step_up_multiple`. Fold step-ups into the realized-track-record factor. Show a
  "provisional" marker when `outcome.provisional`.
- `investability` → **actionable path**: `listing_status` `public` → full;
  `filed_s1`/`rumored_ipo` or a non-empty `public_proxies[]` → partial; else base.
  Render `public_proxies` ({ticker, relation, source_url}) as the "how to ride it"
  chips.
- `ai_posture` → **NEW moat / AI-resilience factor**: `class` ∈ `compounds |
  neutral | at_risk` + a cited `rationale`. Add this to the Rank-1 (Interesting
  deals) factor set and give it a CONFIG weight. Suggested: `compounds` positive,
  `at_risk` negative, `neutral` zero — this is the "grows with the frontier vs gets
  replaced" signal the user cares most about. The engine guarantees the class is in
  vocab, so you can switch on it directly.

## Rules for the dashboard side (unchanged boundary)
- Consume these as facts; don't recompute or fetch. `source_url` on each block is
  for the "not engine data? — sourced here" affordance.
- Keep the provisional markers visible where `provisional:true`.
- If an investable target renders with the moat factor dark, that's an engine
  coverage gap (its audit flags W8 for ≥$1B such targets) — report the name back,
  don't hand-tag it.

## Verify
- A well-known round (e.g. Chai Discovery / a named Series) shows ordered backers
  and a lead-time signal for its early backer.
- A target with a valuation trail shows a step-up and a strike-rate contribution.
- The moat factor lights up on `compounds`/`at_risk` targets with the rationale
  tooltip; `neutral`/absent stays quiet.
