# Sovereigns — Week 2026-W40

## What moved
The watchlist (MGX, Mubadala, Saudi PIF, US Government) was quiet on genuinely
new capital allocation this week; most of the activity found on searches
forward from each entity's `last_event_date` turned out to be either the
already-filed events themselves (Mubadala/Ansaldo Energia still just "in
talks" as of 2026-09-20/21, no signed deal; Saudi PIF's HUMAIN $2.5B data
center fund still awaiting Capital Market Authority approval, no first close)
or entirely out of scope for our sector taxonomy (PIF's Pimco fixed-income
allocation, Mubadala/EBRD backing Egyptian fintech Paymob).

The one solid new row is **US Government / DOE's SPARK initiative**
(2026-09-24): the Department of Energy's Office of Electricity selected 31
grid-reconductoring and transmission-upgrade projects across 26 states,
committing $1.9B in federal funding (recipients add $3.35B in cost-share, for
a combined $5.25B) to add roughly 23GW of grid capacity. The official DOE
release frames this explicitly around AI-driven electricity demand growth.
Filed `verified` (Tier-1 DOE press release; corroborated independently by
Bloomberg and TD World/Daily Energy Insider on the same $1.9B/$5.25B figures).
Note: like the Savannah River and Paducah federal-land data-center deals filed
in prior weeks, DOE funding-opportunity "selections" typically still require
negotiated award agreements before cash moves — treat this as a firm
allocation decision, not yet fully disbursed cash.

## Escalation attempts that didn't clear the bar
- Mubadala/Ansaldo Energia (15–35% stake in the Italian gas-turbine maker):
  still reported as "talks" / "frontrunner" as of 2026-09-20/21 (Bloomberg,
  Finimize, briefs.co). No signed agreement — matches what's already on file,
  not re-filed to avoid churn.
- Saudi PIF/HUMAIN $2.5B data-center fund (BSF Capital): still pending Capital
  Markets Authority approval (2-3 month timeline quoted in early September);
  no first close or signed vehicle found. Not re-filed.
- PIF/US EXIM $15bn export-credit MoU: confirmed still a non-binding MoU with
  no drawn facility; unchanged since 2026-07-24. Not re-filed.
- No new MGX-specific event found forward of the 2026-08-13 Databricks
  investment already on file (Campus AI France expansion, AI Infrastructure
  Partnership, Anthropic Series H participation, etc. all predate the search
  window).

## Universe discovery
Four untracked sovereign/state vehicles were flagged in
`discovered_allocators.csv`, all active in AI infrastructure and co-investing
alongside tracked names: **Qatar Investment Authority** (via its Qai vehicle's
~$20B Brookfield AI-infra JV), **Kuwait Investment Authority** (anchor
investor in the MGX/BlackRock/Microsoft AI Infrastructure Partnership),
**GIC**, and **Temasek** (both anchored Anthropic's $65B Series H alongside
MGX/Mubadala peers, and Temasek is explicitly raising its AI/infrastructure
exposure target).

## What to watch next week
- Whether Mubadala's Ansaldo Energia talks convert to a signed stake (CDP
  Equity is reportedly deciding among several Gulf bidders).
- Saudi PIF/HUMAIN data-center fund's Capital Markets Authority approval,
  expected roughly Nov–Dec 2026.
- Whether DOE's SPARK-selected projects move from selection to signed
  cooperative agreements (same pattern to check for Savannah River/Paducah).
- Whether QIA, KIA, GIC or Temasek should be formally promoted to the
  sovereigns watchlist given their recurring co-investment alongside MGX/
  Mubadala in AI infrastructure vehicles.

## Environment note
`WebFetch` was fully egress-blocked in this session for every domain tried
(including energy.gov, mgx.ae, pif.gov.sa, wikipedia.org, reuters.com,
fortune.com, and several local-news outlets) — every citation above comes
from a resolved article/press-release URL surfaced and read via `WebSearch`
rather than a direct fetch. `data.sec.gov` was also rejected by the egress
proxy (403 on CONNECT) in the raw network log, though `engine.edgar`'s own
CLI calls (`cik`, `exists`) completed normally, suggesting it reads from a
local index rather than live EDGAR in this environment.
