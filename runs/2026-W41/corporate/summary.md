# Corporate — 2026-W41 summary

## Constraint this run
`python -m engine.edgar filings ...` (network path) and WebFetch both failed with
egress/tunnel errors against sec.gov and other domains (`403 Forbidden` on the
proxy tunnel for engine.edgar; `EGRESS_BLOCKED` for WebFetch). The local,
non-network path (`engine.edgar exists`) worked fine and was used to de-dupe every
row before filing it. For everything else this run relied on WebSearch's own
fetch/synthesis of source pages and cited the resolved article/filing URL it
returned — never a bare search-query URL. One NVIDIA 8-K exhibit
(sec.gov/Archives/edgar/data/1045810/000104581026000069/sbeoainvidia-portsrelease.htm)
surfaced in search results but its text was never actually read this run, so it is
flagged in notes rather than cited as a source_url.

## Counts
- verified_events.csv: 6 rows (4 `verified`, 2 `verified_alpha`)
- candidate_events.csv: 2 rows
- discovered_allocators.csv: 3 new names

## Coverage by watchlist name
- **NVIDIA** — 2 events (Nscale follow-on, SB Energy follow-on)
- **Alphabet (GV)** — 2 events (EnduroSat, Snorkel AI)
- **Microsoft (M12)** — 2 verified (HiddenLayer, Gimlet Labs) + 2 candidates (Mantic, Stuut)
- **Amazon** — no new events in window. Its two headline 2026 moves (the $50B OpenAI
  completion, the $5B/$25B Anthropic follow-on) both disclosed well before this
  30-day window (OpenAI: SEC filing 2026-07-31; Anthropic: announced 2026-04-20) —
  checked and excluded as stale, not missed.
- **Meta** — no new events in window. The $14B BlackRock El Paso data-center JV is
  real but disclosed 2026-07-28, outside the window.
- **Oracle** — no new events in window. Its 2026 capital activity (TikTok JV stake,
  $20B ATM equity program, $18B bond) is Oracle raising capital as a *target*, not
  deploying it as an *allocator* — out of scope for this agent by design (see
  corporate.md: "most of these names are also capital targets; you only record
  where they are the allocator").

## Biggest signals
1. **NVIDIA's balance sheet is now funding AI-adjacent infrastructure, not just
   AI labs.** Both NVIDIA rows this week are into physical/compute-adjacent
   infrastructure plays pre-IPO — Nscale (GPU neocloud, $1B into a $3.36B
   convertible round, implied ~$35B IPO valuation) and SB Energy (SoftBank's
   data-center/power developer building OpenAI's Ohio PORTS-Pike campus, NVIDIA's
   commitment there now $3B across two tranches). Both convert to equity at IPO —
   NVIDIA is pre-positioning in the public listings of its own customers/suppliers.
2. **Alphabet and Microsoft's CVC arms (GV, M12) are quietly doing a lot of
   small-to-mid AI-infra financing-round participation** — four separate rounds
   this window (EnduroSat $205M, Snorkel AI $350M, HiddenLayer $100M, Gimlet
   Labs $300M) — none disclosing the corporate's actual check size. This is a
   structural gap: amount_usd is blank on all four rows because the parent
   company's slice is never broken out, only the round total.
3. **A recurring co-investor cluster is forming around the watchlist**: Third
   Point (hedge fund turned growth investor — now in both the Nscale round
   NVIDIA followed into AND the Snorkel AI round GV is in, same week), Prosperity7
   (Saudi Aramco's VC arm — in both the Snorkel AI round with GV and the Gimlet
   Labs round with M12, same week), and Abu Dhabi Investment Council (alongside
   NVIDIA in Nscale). Logged all three to discovered_allocators.csv.

## What to watch next week
- NVIDIA's Nscale $1B tranche is due to fund mid-November — watch for the actual
  wire/closing disclosure, which would upgrade this from a committed-but-pending
  tranche to a completed cash event.
- SB Energy's Nasdaq IPO (ticker SBE, reportedly targeting $5-7B in proceeds) —
  when it prices, NVIDIA's Class N shares convert and the $3B commitment becomes
  a real equity stake with a mark.
- Confirm (with a direct SEC read, not search-indexed) the NVIDIA 8-K exhibit at
  accession 000104581026000069 for the SB Energy tranche — would upgrade that row
  from verified_alpha/tier-3 to verified/tier-1.
- Chase the Mantic Technologies and Stuut candidate rows for a primary source
  (company blog / Form D text) to upgrade them past candidate.
