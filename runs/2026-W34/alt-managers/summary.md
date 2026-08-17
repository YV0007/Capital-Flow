# Alternative Managers — Week 2026-W34

**Window:** disclosed ~2026-07-18 → 2026-08-17 (30 days trailing today, 2026-08-17), with
emphasis on the tail end (2026-08-10 → 2026-08-17) not yet covered by 2026-W33, whose window
closed at 2026-08-10.
**Watchlist:** SoftBank, Blackstone, BlackRock/GIP, DigitalBridge, Brookfield, KKR, Blue Owl,
Apollo, Goldman Sachs.

**Result: 1 verified event, 0 candidates.** A quiet week for this class specifically on the
AI-buildout thesis — most of the class's attention in the window was consumed by Q2 earnings
season (Blackstone Aug 4, KKR Jul 30, Apollo Aug 4, Brookfield Aug 13, SoftBank Aug 6, Blue Owl
Jul 30) rather than new deal announcements, and the one genuinely new large-scale event
(NVIDIA's $500bn six-manager AI-compute financing consortium) was already captured as
candidate rows across all six allocators in last week's 2026-W33 run and is not re-logged here
to avoid duplication (see "Continuity" below).

## Operational note: WebFetch was again fully blocked this session

Every WebFetch call this run returned `EGRESS_BLOCKED` — including control tests against
`example.com` and `en.wikipedia.org` — confirming this is a proxy/policy-level block for the
session, not a per-domain issue (the `__agentproxy/status` endpoint shows 403 "policy denial"
on every recent relay attempt, e.g. `efts.sec.gov`, `www.finsmes.com`). This is the same
condition 2026-W33 hit. As before, every finding below comes from `WebSearch`'s own retrieval
and synthesis of the cited URLs rather than a page I fetched and re-read myself — the URLs in
`verified_events.csv` are real, resolved, primary documents (Boralex's, La Caisse's, and
Brookfield Renewable's own press-release pages, cross-confirmed by GlobeNewswire), but I could
not independently pull the raw HTML/filing text the way a fully-working session would. This
session's `WebSearch` budget was also exhausted before I could run a final verification pass
on one promising lead (Apollo/Athene's reported "$11.2bn for 49% of an Intel Ireland fab JV") —
flagged below as almost certainly a stale/misdated recirculation of Apollo's well-known
February 2024 Fab 34 (Leixlip) transaction, not a new 2026 event, but not independently
re-confirmed before the budget ran out.

## The one verified event

**Brookfield and La Caisse completed the take-private of Boralex (2026-08-14) — a ~$9.0bn
enterprise-value renewables platform, Brookfield taking 70%.** Boralex is a TSX-listed
Canadian developer/operator of 3.8GW of solar, wind, hydro and battery storage across Canada,
the US, France and the UK. Consideration was $37.25 cash/share (~$3.8bn equity value, ~$9.0bn
EV, ~$9.7bn "combined basis" including project and corporate debt — sources are inconsistent
on CAD vs USD labeling, so exact dollar fields are left blank rather than force a conversion).
La Caisse increased its stake from 15% to a pro forma 30% and rolled a post-closing
investment; Brookfield is the 70% control sponsor. Confirmed by four independent primary
releases (Boralex, La Caisse, Brookfield Renewable, GlobeNewswire). Like several prior weeks'
renewables rows (EDF power solutions, Aypa Power, Summit Ridge Energy), this is **general
power/renewables capital, not datacenter-specific** — tagged `power-energy` per the class
mandate on load-growth logic, not because Boralex itself sells to AI/hyperscale customers.

## Continuity: NVIDIA's $500bn six-manager consortium, not re-logged

2026-W33 already logged candidate rows (single Tier-3 X/Twitter source at the time) for
Apollo, BlackRock, Blackstone, Brookfield, Goldman Sachs and KKR all joining NVIDIA's
announced push to mobilize "over $500 billion of third-party capital" via independent AI
compute-financing platforms. This week's search surfaced the actual NVIDIA Newsroom press
release confirming the same Aug 10 announcement (a Tier-1 upgrade in principle), but
`nvidianews.nvidia.com` is on this session's WebFetch block list, so I could not pull its full
text to confirm whether it adds anything beyond the $500bn **aggregate target** already on
file — no per-manager commitment or closed vehicle size is reported anywhere I could find.
Left as-is in last week's file rather than re-logged; **next week should re-fetch the NVIDIA
release directly once WebFetch is unblocked** to see if it upgrades past target-stage language.

## What did not confirm to a loggable event

- **KKR + Energy Capital Partners' ~$7.7bn (£5.75bn) agreed take-private of DCC Energy plc**
  (announced 2026-07-27, KKR's largest European public-to-private in over a decade) —
  excluded as a row. DCC Energy is a Dublin/London-listed LPG and fuel-oil distributor with no
  power-generation or datacenter-adjacent mandate; unlike July's three-way Kuwait pipeline
  consortium (kept last week specifically because three watchlist names co-underwrote it),
  this is a single tracked name (KKR) paired with an untracked one (ECP), so it doesn't carry
  the same cross-manager signal value and sits further outside the AI-buildout thesis than the
  Kuwait deal did. ECP is logged in `discovered_allocators.csv` instead.
- **Meta/Pimco/Blue Owl "$29bn" Louisiana financing headline** — traced this back and it
  appears to be aggregator recirculation of the original October 2025 Hyperion JV terms
  (Blue Owl ~80%/Meta ~20%, ~$27bn total, PIMCO as bond anchor investor), not a new
  incremental raise. Not logged; the real open question remains last week's still-unconfirmed
  5GW/"$50bn+" scale-up scope (still a W33 candidate, not restated by any primary source this
  window).
- **Apollo/Athene "$11.2bn for 49% of an Intel Ireland fab JV"** — a WebSearch synthesis
  surfaced this dated ambiguously as "mid-August 2026," but it is almost certainly Apollo's
  well-documented February 2024 Fab 34 (Leixlip, Ireland) transaction being restated without a
  clear date by an aggregator. Session's WebSearch budget was exhausted before I could
  independently re-date it — flagged here rather than logged, and worth a clean re-check next
  week rather than being silently dropped.
- **Blue Owl's $750m senior notes pricing (2026-08-12)** and **Goldman Sachs's role arranging
  a reported $5.4bn bond+loan package for a Blackstone/QTS data center leased to Microsoft**
  (Goldman gauging investor demand as of 2026-07-29) — both excluded on the same "wrong
  direction" logic as SoftBank's margin loan last week: Blue Owl is the *borrower* in the
  first, and Goldman is acting as *underwriter/arranger* raising other investors' capital in
  the second, not deploying its own balance sheet as the allocator our schema tracks.
- **DigitalBridge/SoftBank $4.0bn take-private** — shareholder-approved (Apr 23, 2026) but
  still not confirmed closed as of this window; nothing new to log until closing is announced.

## Watch next week

1. **Re-fetch `nvidianews.nvidia.com`'s Aug 10 six-manager release directly** once WebFetch is
   restored, to see whether the $500bn figure firms up into anything with a real committed
   vehicle size — this is the single biggest number hanging over the class right now.
2. **DigitalBridge/SoftBank closing** — still pending as of Aug 17; the actual close (expected
   "second half of 2026") will be a real acquisition event when it lands.
3. **Re-verify the Apollo/Intel-Ireland "$11.2bn" item's true date** — confirm it is 2024
   noise, not missed 2026 news, once search budget resets.
4. **Blue Owl Digital Infrastructure Fund IV** — management guided this "to return to market
   in 2026" on the Q2 call; watch for a first close.
5. **SoftBank's OpenAI equity tranche 3** ($10bn, due 2026-10-01 per SoftBank's own schedule)
   and the **$5bn Arm-backed term loan** flagged as "in market" last week — still ahead of us,
   not yet events.
