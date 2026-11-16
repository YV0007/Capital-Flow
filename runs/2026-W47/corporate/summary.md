# Corporate allocators — week 2026-W47 (Microsoft, Amazon, Alphabet, Meta, Oracle, NVIDIA)

## What moved this week
No new, well-sourced capital-ALLOCATION event closed in the last ~30 days that
isn't already on file. The six Tier-1 mandatory checks (SEC EDGAR full-text
8-K/10-Q/10-K/13D-G sweep + IR/newsroom pages per entity) turned up a wall of
**capital-raising**, not capital-deploying, filings: Microsoft ($25B senior
notes, filed 2026-11-04), Alphabet (€6B senior notes, closed 2026-11-05), Meta
(€9B senior notes, closed 2026-11-12, plus the Class C recapitalization /
Zuckerberg Founder Alignment Agreement, 8-K 2026-10-21), and Oracle ($10B
common stock + $10B notes, closed 2026-11-04) collectively raised roughly
**$54B+** in the last three weeks alone. None of these 8-Ks name a specific
acquisition or investment target — Oracle's explicitly says proceeds are for
undifferentiated "general corporate purposes." They are financing, not
allocation, so none is filed as an event, but they are the clearest signal of
the quarter: the hyperscalers are pre-funding balance sheets for a further
leg of AI-infrastructure spend, on top of what they already deployed.
NVIDIA's own 8-K this week (2026-11-11/12) was a leadership change — Jensen
Huang's resignation and Colette Kress's appointment as interim CEO — not a
capital event.

The two biggest NVIDIA-as-allocator stories that *did* close inside the
window — the $3B NVIDIA commitment into Meta's equity offering (NVIDIA
newsroom, 2026-10-26) and the $1B NVIDIA payment completing a 4.13% stake in
Naver (payment finalized 2026-11-06, per Korean press) — were both already
captured on file by earlier runs (ids 459 and 26 in the DB) under the correct
amounts and sources, so this run did not re-file them; `engine.edgar exists`
confirmed both before any row was drafted.

## Biggest signals
1. **Debt-and-equity war chest, not new deals.** ~$54B raised across four of
   the six tracked allocators in a three-week span (MSFT, GOOGL, META, ORCL)
   is the real story this week — it's dry powder for AI buildout, not
   allocation itself. Watch where it gets deployed next.
2. **NVIDIA–Naver closed.** The $1B / 4.13% stake announced in July finally
   paid out on 2026-11-06, confirming NVIDIA is still executing on its
   balance-sheet-stake playbook even as its own leadership is in flux.
3. **Leadership risk at NVIDIA.** Jensen Huang's resignation (8-K,
   2026-11-11) with Colette Kress stepping in as interim CEO is not a capital
   event but is a material context flag for every NVIDIA-linked deal next
   week — approvals, pace, and board composition (new Chair: Harvey Jones)
   bear watching.

## Candidate (unconfirmed) lead
- **NVIDIA → d-Matrix**: The Information reported (Oct 2026, anonymous
  sources) that NVIDIA plans a stake in inference-chip rival d-Matrix,
  layered on their Sept 10 NVLink Fusion partnership. No amount, valuation,
  or timing confirmed by either side as of 2026-11-16; filed as `candidate`
  with the full escalation trail in `candidate_events.csv`.

## Discovered allocators
- **AMD** — co-committed $1B alongside NVIDIA's $3B in Meta's Oct 2026 equity
  offering. Same balance-sheet-stake pattern as the existing corporate
  watchlist; not currently tracked.
- **Third Point** — led Nscale's $3.36B pre-IPO convertible financing
  (NVIDIA's $1B tranche within it is already on file); recurring lead in
  AI-neocloud pre-IPO rounds.

## What to watch next week
- Does NVIDIA's $1B Nscale tranche (expected "mid-November") actually close?
- Any confirmation (or denial) of the NVIDIA/d-Matrix stake.
- Where Microsoft/Alphabet/Meta/Oracle deploy the ~$54B just raised —
  likely candidates are further hyperscaler compute buildout, GPU
  prepayments, or a new wave of AI-lab follow-ons (Anthropic/OpenAI-adjacent).
- NVIDIA board/leadership stability post-Huang resignation and any effect on
  pending equity commitments (Meta, Naver listing 2026-11-27, Nscale).
