# Corporate agent — week 2026-W37 summary

## What moved
The corporate watchlist (Microsoft, Amazon, Alphabet, Meta, Oracle, NVIDIA) was quiet
this cycle on the balance-sheet side for five of six names — Microsoft, Amazon, Meta
and Oracle threw off enormous capex *guidance* commentary (the ~$600-725B 2026
hyperscaler capex headline keeps recurring) but no NEW discrete capital-allocation
event disclosed since 2026-08-08 that cleared the bar (a headline commitment, not a
re-hash of April/May deals like Amazon-Anthropic $25B, Google-Anthropic $40B, or
Meta-Scale AI). NVIDIA, by contrast, had one of its busiest four-week stretches of
the year and accounts for every row filed this week.

## Biggest signals
1. **NVIDIA → Hugging Face, $12.93B acquisition (Sept 3).** NVIDIA's largest
   acquisition to date, confirmed on NVIDIA's own blog and corroborated across
   TechCrunch/CNBC/Yahoo/The Hill/Tom's Hardware. Buys NVIDIA control of the
   dominant open-model distribution layer (18M+ developers, 3M+ models) — a
   platform play as much as a compute play, and the reason it's filed under
   `ai-labs` with a sector-fit flag rather than a cleaner canonical bucket.
2. **NVIDIA → SB Energy, $1.5B equity + up to $105B in lease guaranties (Aug 17,
   8-K).** NVIDIA joins SoftBank and OpenAI as an anchor backer of SB Energy's
   PORTS-Pike Technology Campus in Ohio (up to 8GW, OpenAI as 20-yr tenant,
   NVIDIA-exclusive compute). Only the $1.5B forward-contract equity check is
   filed as `amount_usd` — the $105B is a residual-value guaranty (contingent
   credit support, not cash deployed) and is called out separately in notes so
   it doesn't inflate the row, mirroring the compute-commitment discipline
   CONTEXT.md asks for with hyperscaler deals.
3. **NVIDIA → MediaTek, $3.5B convertible-bond purchase (Aug 31)**, ~90% of
   MediaTek's record $3.9B offshore convertible bond and NVIDIA's first direct
   investment in a Taiwanese company — deepens the NVLink Fusion tie-up.
   Alphabet also participated in the same bond but did not disclose its slice;
   filed as a separate `candidate` row under Alphabet pending a clean read of
   MediaTek's own press-room page (blocked to WebFetch this run).

## Smaller but real
NVIDIA also took an undisclosed (WSJ: "several hundred million") minority stake
in **Cloverleaf Infrastructure** (Aug 21) — a power-siting/land-packaging
developer that pre-buys utility power for AI campuses — continuing NVIDIA's
pattern of backing the physical build-out layer (Corning plants in May, the
$500B Apollo/BlackRock/Blackstone/Brookfield/Goldman/KKR financing platform in
August) rather than just chips.

## Discovered allocator
**OpenAI** is showing up as a *co-investor* (not just a target) — alongside
NVIDIA and SoftBank in SB Energy — so it's flagged in discovered_allocators.csv
as a candidate addition to the corporate watchlist.

## Watchlist names with nothing new this cycle
- **Microsoft** — checked IR/acquisition-history page, M12 activity, Fairwater
  financing news; nothing new since 2026-08-08 beyond recurring capex/OpenAI
  revenue-share commentary already on record.
- **Amazon** — checked AboutAmazon newsroom, Alexa Fund, Industrial Innovation
  Fund; the Anthropic $5B/$25B and India $13B commitments are all April-June,
  outside the window. (Jeff Bezos's personal Liverpool FC stake is his own
  capital, not Amazon's balance sheet — belongs to the individuals class, not
  filed here.)
- **Alphabet** — no NEW Alphabet-as-allocator event beyond the MediaTek
  candidate row above; the $80B equity raise and Anthropic commitments are
  Alphabet raising/spending capex, already stale relative to last_event_date.
- **Meta** — checked IR, Hyperion/Blue Owl financing, nuclear PPAs; all
  pre-date the window (ARI acquisition May, Scale AI July, nuclear deals Jan).
- **Oracle** — checked IR financing-plan page and Oracle Ventures; only
  Oracle-as-capital-*raiser* news (its own $45-50B financing plan) and
  institutional 13F-style purchases of ORCL stock (not Oracle-as-allocator).

## Tooling note
`python -m engine.edgar` (deterministic CIK/filings path) and direct `WebFetch`
of sec.gov, nvidianews.nvidia.com, techcrunch.com, cnbc.com, wikipedia.org, etc.
were all blocked by this session's network egress policy (403 from the proxy
on data.sec.gov and most press/company domains). All research this run was
done via WebSearch synthesis instead, cross-checking multiple independent
outlets per claim; source_url values still point to specific resolved
articles/filings, never search-query URLs.

## What to watch next week
- Whether Alphabet's MediaTek bond slice gets disclosed (would upgrade the
  candidate row to verified).
- NVIDIA-Thinking Machines Lab — reports of a ~$2.5B investment have been
  circulating since March 2026 without a confirmed close; worth a fresh check
  if it finally lands.
- Whether the NVIDIA SB Energy structure (equity + residual-value guaranty)
  becomes a template other hyperscalers copy for their own Ohio/Midwest
  campuses — a second instance would confirm a new deal pattern worth its own
  sector/subsector tag.
