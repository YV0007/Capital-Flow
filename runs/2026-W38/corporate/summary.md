# Corporate agent — 2026-W38 summary

## Environment note (read first)
This run's sandbox has no outbound network access to `data.sec.gov`, `www.sec.gov`,
or almost any other domain via Bash/WebFetch (org egress policy — every direct
CONNECT and every WebFetch call was rejected with 403/EGRESS_BLOCKED, confirmed
across sec.gov, techcrunch.com, cnbc.com, blogs.nvidia.com, cloverleafinfra.com,
and even example.com). `python -m engine.edgar cik/filings` therefore cannot reach
SEC this week. Only WebSearch (routed through Anthropic's own infra, not the local
proxy) worked. `python -m engine.edgar exists` still works — it's a local DB
lookup — and was used before writing every row.

## What moved this week
Checked the local event DB (via `engine.edgar exists`) against the full corporate
watchlist first. Contrary to `context.json`, which showed `last_event_date: null`
and `events_on_file: 0` for every entity (stale), the DB already holds 33 corporate
events through 2026-W37, including nearly everything a fresh WebSearch sweep of the
last 30 days turned up: NVIDIA's Hugging Face acquisition ($12.93B, Sept 3), NVIDIA's
$105B Ohio data-center guarantee + $1.5B SB Energy stake (Aug 17), NVIDIA's $3.5B
MediaTek convertible-bond buy and Alphabet's undisclosed-amount participation in the
same bond (Aug 31), and NVIDIA's Cloverleaf Infrastructure minority stake (Aug 21).
All of these were re-confirmed as already on file at equal-or-better source quality
and were NOT re-filed.

Two genuinely new items surfaced this run:

1. **NVIDIA -> Mistral AI, follow_on, verified.** NVIDIA is named as a returning
   investor in Mistral's EUR3B (~$3.5B) Series D, led by Samsung Electronics at a
   post-money valuation >EUR21B (~$24B) — confirmed via Mistral's own announcement
   plus TechCrunch/Sifted/HPCwire. Per-investor cheque size is undisclosed, so
   `amount_usd` is left blank rather than assigning the round total to NVIDIA
   (round total captured in `round_total_usd` instead, per the CSV contract's
   measurement-corruption rule).
2. **NVIDIA -> Thinking Machines Lab, minority_stake, candidate.** Reported
   ~$2.5B as roughly half a $5-6B round valuing Mira Murati's lab at ~$40B. Ran the
   escalation loop: traced to a single origin (The Information), confirmed every
   other outlet is syndicating that same story (circular-reporting guard — counted
   as one source, not several), and re-checked through 2026-09-14 for a close —
   none reported. Filed as `candidate`, not dropped.

## Biggest findings
- **NVIDIA's corporate-VC pace has not slowed**: five NVIDIA-allocator events
  landed in a single 30-day window before this run even started (Hugging Face,
  MediaTek, Cloverleaf, SB Energy, the Ohio $105B guarantee), plus the two new
  ones here — NVIDIA is now investing in the entity that just raised money that
  props up its own compute demand (MediaTek bond -> NVLink Fusion; Mistral ->
  more GPU consumption), a circular-financing pattern flagged by press covering
  the MediaTek deal.
- **Alphabet is a quiet participant, not a lead investor**, in the AI-financing
  wave (MediaTek bond, undisclosed amount) — worth a follow-up next week to see
  if Alphabet's slice gets disclosed in a 10-Q/8-K once SEC access is restored.
- **Microsoft, Amazon, Meta, and Oracle show no new *allocator*-side capital
  events since their last filed dates** (Microsoft: 2026-07-28, Amazon:
  2026-08-26, Meta: 2026-07-28, Oracle: none on file, ever). Their September
  headlines this week are all capex/spending-plan or debt-raise stories (Alphabet's
  $80B equity raise, Amazon's GBP4.25B sterling bond, Oracle's own AI capex) —
  i.e. them raising or spending capital as a target/issuer, not deploying it into
  a target, so correctly excluded from this file.

## Rows written
- `verified_events.csv`: 1 row (NVIDIA / Mistral AI)
- `candidate_events.csv`: 1 row (NVIDIA / Thinking Machines Lab)
- `discovered_allocators.csv`: 3 rows (Samsung Electronics, ASML, Grand Duchy of
  Luxembourg — all seen co-investing with NVIDIA in Mistral's Series D)

## Watch next week
- Re-run EDGAR sweeps once SEC egress is available — Alphabet's MediaTek-bond
  slice and any 8-K on the NVIDIA/Mistral follow-on would likely upgrade both to
  a firmer figure.
- Chase whether the NVIDIA/Thinking Machines Lab talks close (would flip the
  candidate row to verified/verified_alpha with a real amount).
- Oracle has zero corporate-allocator events on file. Worth confirming with the
  user whether that's correct (Oracle mostly raises/spends rather than deploys)
  or whether Oracle's Stargate-related SPV commitments should be modeled as an
  Oracle-as-allocator event rather than purely as capex.
