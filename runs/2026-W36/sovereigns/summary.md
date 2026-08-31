# Sovereigns — 2026-W36

## Filed
- **1 verified event.** 0 candidates filed this week.
- **Mubadala → Arrive Logistics** (acquisition, majority equity, 2026-08-27, terms
  undisclosed, source_tier 1). Mubadala Capital signed a definitive agreement to
  take majority control of Austin-based truckload brokerage Arrive Logistics;
  ATL Partners and Lead Edge Capital keep minority stakes, close expected Q4 2026.
  Filed with `sector = diversified-pe` (closest fit — freight/logistics-tech
  doesn't map to the canonical AI-infra taxonomy; flagged in notes per the "closest
  and note it" rule).

## Why so thin
This was mostly a **confirmation week, not a discovery week**. Every other
capital-allocation signal turned up for MGX, Mubadala, Saudi PIF and US
Government this run was already on file:
- MGX: Databricks (8/13), Aligned Data Centers $5B growth capital + the $40B
  Aligned acquisition close (7/21), MGX Fund I close at $49B (7/1), Anthropic
  Series G/H, Isomorphic Labs — all pre-date `last_event_date` or duplicate
  `recent_targets` already on file. No new MGX capital deployment surfaced past
  8/13.
- Saudi PIF: EA acquisition completion (8/4), PIF FY2025 results (8/17) and the
  2026-2030 strategy publication (8/12) are performance/strategy news, not new
  capital events. No new named-target deal surfaced past 8/14.
- US Government: the $874M Commerce/CHIPS equity-stake round (GlobalFoundries,
  Kepler, Multibeam, Extropic, Thintronics, Obsidia, Aeluma — 7/29) and the
  Sila/Sunrise/Niron/Strategic Bauxite USA OSC loans (8/7) are already filed,
  several under duplicate event_type/target-name variants (a downstream dedup
  issue, not something re-filed here). The OSC's 8/20 National Security Fund
  NOFO is a program vehicle, not a committed deal to a named target — excluded
  per scope.

## Stale candidates chased, no status change
- **Strategic Bauxite USA / "Standard Bauxite"** — confirmed via the war.gov
  IBAS release ($85.5M DoW equity + $64.5M private, ~$150M combined) that this
  is **already verified on file** (id 220) under the correct entity name; the
  "Standard Bauxite" candidate row (id 152, from the White House fact sheet) is
  a name-variant duplicate of that same verified event, not a separate deal.
  Left for downstream entity resolution to merge — did not re-file.
- **Savannah River Site (Amentum)**, **Paducah (Brookfield)**, **PIF–EXIM $15B
  MoU** — no material update found; all remain exactly where they were
  (negotiations / non-binding), still correctly `candidate`.
- **Mubadala Akita (Japan, BitGrid/S2)** — more press volume (UAE ambassador
  visited Akita 8/19) but still "in talks" / "weighing," no commitment. Stays
  `candidate`; not re-filed.
- **Korea Investment Corporation** — still no SEC/EDGAR trace; KIC's ¥20T/$14B
  strategic account needs National Assembly legal amendments (in progress
  August) before it can even launch (targeted 2027). Stays `candidate`.

## Biggest signals
1. **Mubadala keeps diversifying outside AI infra.** Arrive Logistics (this
   week) follows Moove (robotics/autonomous mobility, 8/5) and the $170B/44%-
   of-portfolio US commitment (8/3) — a pattern of large, US-directed,
   non-AI-infra sovereign capital that the current sector taxonomy doesn't
   cleanly capture. Worth a taxonomy conversation if this keeps recurring.
2. **US Government equity-stake strategy is now systemic, not episodic.** Per
   Forbes/Cato tracking, the government's corporate-stake portfolio is up to
   ~30 companies (Intel, GlobalFoundries, MP Materials, Kepler, etc.), funded
   through CHIPS Act conversion and OSC conditional loans. Most of this is
   already captured in our data but split across duplicate event_type rows
   (equity/sovereign_investment/grant all filed for the same disclosure) —
   flagging for dedup, not re-filing.
3. **Two more sovereign co-investors surfaced in AI-lab cap tables**: Qatar
   Investment Authority (Anthropic Series G) and the UK Sovereign AI Fund
   (Isomorphic Labs Series B), both riding alongside MGX. Filed to
   `discovered_allocators.csv` — worth adding to the watchlist if they keep
   appearing.

## Watch next week
- Mubadala Capital / Arrive Logistics close (targeted Q4 2026) — watch for
  disclosed deal value.
- Any movement on the Savannah River / Paducah negotiations converting to
  signed leases.
- KIC's National Assembly legal amendments — first Tier-1-checkable trace once
  passed.
