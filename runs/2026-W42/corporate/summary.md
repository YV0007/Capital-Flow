# Corporate — ISO Week 2026-W42 (run date 2026-10-12)

## Environment note
SEC EDGAR was unreachable all run: `engine.edgar` gets a 403 from the egress
proxy hitting `data.sec.gov`, and `WebFetch` cannot resolve `sec.gov` at all
(and, as it turned out, could not resolve most other domains either —
`reuters.com`, `f4.fund`, `mezha.ua`, `feedbagel.com` all failed the same way).
All research this week ran through `WebSearch` only, citing the specific
resolved article/filing URLs it surfaced rather than search-query URLs. This
should be flagged to the operator — the corporate agent's two mandated
Tier-1 paths (EDGAR deterministic pull, direct IR/newsroom fetch) were both
degraded to "search and read the snippet" for the whole run.

## What moved
Thin week for genuinely new, in-window (disclosed since ~2026-09-12) capital
allocation from the six watchlist names as *allocators*. Most of what's
circulating in the press right now is capex/guidance noise (Alphabet,
Amazon, Meta, Microsoft, Oracle all reaffirming 2026 infrastructure spend in
the $150–220B range) or deals that closed well before the window
(Amazon→Anthropic $25B, Microsoft/Amazon/NVIDIA→OpenAI's $122B round, the
TikTok USDS JV) — none of that is new money moving this week, so none of it
is filed.

**1. NVIDIA → Hugging Face, $11.9B acquisition (verified).** Definitive
agreement signed 2026-09-02, confirmed via NVIDIA's own 8-K — NVIDIA's
largest outright acquisition to date, plus up to ~$1.0B in employee
retention. Closing isn't expected until H1 2027. This is 10 days earlier
than the nominal 30-day lookback, but with zero prior NVIDIA events on file
for this agent, it's the one rock-solid, Tier-1-confirmable row worth
banking this week rather than leaving the entity empty-handed.

**2. NVIDIA's AI-model-investing pipeline keeps running hot, but nothing
closed.** Two live, single-origin (The Information) leads are sitting in
`candidate_events.csv`: a reported ~$2.5B slug of a $5–6B Thinking Machines
Lab round (talks reported 2026-09-03, still unconfirmed), and a reported
~$1B follow-on into Figure AI's humanoid-robotics business (talks reported
2026-10-07, also unconfirmed). Both are classic "NVIDIA half-funds the
foundation-model/robotics stack it also sells chips into" plays, and both
should be rechecked next run for a close.

**3. Microsoft, Amazon, Alphabet, Meta, Oracle — no new allocator events
found.** Checked each company's newsroom/IR via search, M12, GV, and
NVentures' recent activity, and the obvious OpenAI/Anthropic-adjacent angles
(all already-old deals from Feb–Aug 2026). Nothing new disclosed in the
window where one of these five is deploying capital.

## What to watch next week
- Whether the Thinking Machines Lab and/or Figure AI rounds close, and at
  what NVIDIA ticket size — re-run the search, don't re-file the open
  candidates as new leads.
- Microsoft's and Amazon's fiscal Q1/Q3 earnings (both land in late October,
  just after this window) commonly carry OpenAI/Anthropic equity-method
  gain/loss disclosures that can surface new stake or commitment detail.
- Whether SEC/EDGAR access gets un-blocked in this sandbox — worth a direct
  ask to the operator, since it knocks out the agent's primary confirm path
  for 8-K/Form D sweeps every week it stays down.

## Discovered allocators
None worth promoting this week — Accel, a16z, GIC, Coatue, SoftBank, MGX
etc. all surfaced as co-investors are VC/alt-manager/sovereign names
presumably already tracked under other classes, not new corporate
strategics.
