# Corporate — Week 2026-W39 Summary

## Environment note (read first)
Direct network egress to external domains was blocked for the whole run — both
`python -m engine.edgar filings/cik` (data.sec.gov) and WebFetch/curl to any
outside host (www.sec.gov, nvidianews.nvidia.com, reuters.com, cnbc.com, etc.)
returned `EGRESS_BLOCKED` / `403 CONNECT` from the sandbox's egress proxy. The
deterministic EDGAR filings pull and direct page fetches were therefore
unavailable; `python -m engine.edgar exists` (local DB, no network) worked
fine and was used before every row. All research this week relied on
WebSearch, citing the specific resolved article/PR URL it returned rather than
a search query. Where a source domain is normally Tier 1 (company PR, EDGAR)
but I could not independently re-open it myself, that is flagged in the row's
`notes`. Treat this week's `verified` grading as slightly more conditional
than usual until direct fetch access is restored.

## Headline count
- **Verified: 2**
- **Verified_alpha (filed in candidate_events.csv): 1**
- **Candidate: 2**
- Discovered allocators: 0

## What moved
1. **NVIDIA → Hugging Face, $12.93B acquisition (verified).** NVIDIA's
   largest deal of the year: ~$11.9B cash + up to $1B in employee equity
   retention, definitive agreement 2026-09-02, close targeted H1 2027 pending
   regulatory approval. This is a balance-sheet acquisition, not an NVentures
   check — the biggest single signal in the corporate class this week.
2. **Alphabet (via GV) → EnduroSat, $205M Series B (verified, participant).**
   Google Ventures backed the satellite manufacturer's Series B (co-led by
   Riot Ventures/Atreides Management) funding a new US plant and the EU's
   largest space-and-defense manufacturing hub. Alphabet's own slice of the
   $205M isn't disclosed. Filed under sector `defense-tech` — flag for review
   if a dedicated space/aerospace sector gets added later.
3. **Meta → Stilla.ai acquisition (verified_alpha, terms undisclosed).**
   Small but notable: an eight-month-old Stockholm AI-agent startup, folded
   into Meta Business Agent (WhatsApp/Messenger/Instagram commerce). No
   purchase price from either side; graded verified_alpha on Axios's scoop
   plus Stilla's founders independently confirming the deal.

Two more NVIDIA leads are real but not closed, so they're in
`candidate_events.csv`, not verified: a reported ~$2.5B check into Mira
Murati's **Thinking Machines Lab** (~$40B pre-money) and discussions to take
an equity stake in **Perplexity** at a $30B+ valuation. Both trace to single
Information-origin reporting (circular-reporting guard applied) and NVIDIA
has not confirmed either — worth re-checking next run for a close or a Form D.

## Per-company coverage (honest, including quiet weeks)
| Company   | Result this week |
|-----------|-------------------|
| NVIDIA    | 3 items — 1 verified (Hugging Face), 2 candidate (Thinking Machines Lab, Perplexity) |
| Alphabet  | 1 verified (EnduroSat, via GV) |
| Meta      | 1 verified_alpha (Stilla.ai) |
| Microsoft | Quiet week — no qualifying capital-allocation event found in the last ~30 days. Checked M12 portfolio (last new deals in April 2026), the Qcells "explore" grid-capacity alliance (2026-08-31, no committed dollar figure, MOU-stage — not an event per CONTEXT.md), and general IR/acquisition-history pages. |
| Amazon    | Quiet week — no qualifying event. The Anthropic $5B/Series G/Series H threads are all outside the 30-day window (Apr/Feb/May 2026); the OpenAI $50B round was Feb 2026; nuclear SMR/PPA deals (Talen, X-energy, Energy Northwest) are power procurement, not equity into a target, so out of scope. |
| Oracle    | Quiet week — no qualifying event. "Oracle Ventures" search hits were low-quality/unrelated sites; Stargate/OpenAI news this run was all 2025-vintage; the one September item (Ellison cancelling a 10b5-1 stock-sale plan) isn't a capital-allocation event. |

## What to watch next week
- Whether NVIDIA–Thinking Machines Lab or NVIDIA–Perplexity actually close
  (would upgrade both candidates to verified/verified_alpha).
- NVIDIA–Hugging Face regulatory review progress (HSR/antitrust) ahead of the
  H1 2027 close.
- Whether Microsoft, Amazon or Oracle re-enter with a fresh balance-sheet or
  CVC (M12 / Alexa Fund / Industrial Innovation Fund) deal — all three were
  genuinely quiet this run, not under-searched.
- Re-run EDGAR deterministic pulls (`engine.edgar filings/cik`) once network
  egress to data.sec.gov/sec.gov is restored, to get real Tier-1 filing
  confirms rather than press-mediated ones for this week's rows.
