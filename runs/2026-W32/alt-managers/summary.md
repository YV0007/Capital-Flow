# Alternative Managers — Week 2026-W32

**Window:** disclosed ~2026-07-08 → 2026-08-07 (a handful of Jun 30 / Jul 1 flagships kept
for continuity, each flagged in `notes`).
**Watchlist:** SoftBank, Blackstone, BlackRock/GIP, DigitalBridge, Brookfield, KKR, Blue Owl.

**Result: 18 verified / verified_alpha events, 5 candidates.** Fourteen of the eighteen carry
a Tier-1 primary (fund or counterparty press release, or an SEC filing). Coverage is up from
the prior pass largely because two primaries were located that had previously been read only
through the press — Meta's own El Paso investor release and SoftBank's own OpenAI tranche
release — and because SEC Form D and 8-K exhibits were swept directly.

---

## The three biggest signals

**1. The financing bottleneck moved from megawatts to *dedicated* megawatts.**
Four separate deals this window bought generation that never touches an interconnect queue.
Blackstone led $5.34bn of *committed* capital (with Apollo and KKR) for 49% of Williams'
five **behind-the-meter** gas projects — confirmed in Williams' own 8-K, not just the press.
Brookfield was selected by DOE to develop the **Paducah** campus in Kentucky where NextEra
builds up to 2GW of gas plus 2.6GW of storage *dedicated to the site*. Brookfield's Bloom
Energy framework sits at $25bn for onsite fuel cells. Brookfield then bought **Aypa Power**,
North America's largest standalone battery developer, out of Blackstone for ~$7bn EV / $3bn
equity. Read together: the alt managers have concluded that the grid will not arrive in time
and are buying the workaround. That is the cleanest cross-sector `energy_for_ai` convergence
in the dataset.

**2. AI debt repriced in public, mid-deal.**
BlackRock's El Paso JV (Project Sopaipilla, 80/20 with Meta, ~$14bn total cost, ~$4.9bn of
BlackRock cash) is structurally identical to the Meta–Blue Owl Hyperion deal from nine months
earlier. The pricing is not: Sopaipilla's ~$12bn bond cleared at **yields above 7%**, where
Hyperion's $27bn package had priced into an open market. Same sponsor quality, same
hyperscaler lease, materially worse terms. Corroborating exhaust in the same window points
the same way — Blue Owl's two flagship private-credit funds gate-capped withdrawals at 5%
against $4.7bn of redemption requests (Jul 2), Blue Owl reported a fundraising slowdown
(Jul 30), and Blackstone sold three Northern Virginia data centres to Digital Realty for
$3.5bn while refinancing QTS. The template still works; the cost of capital inside it moved.

**3. Alt managers are becoming the operators, not just the owners.**
SoftBank incorporated **SB Neo** in Delaware (Jul 2) to sell training and inference compute
directly to US enterprises and hyperscalers off "the SoftBank Group's 10-gigawatt-scale energy
and AI infrastructure currently under development" — a manager becoming a merchant neocloud.
Blue Owl launched **Kirkwood Infrastructure Group** to own conduit and fiber itself.
DigitalBridge and JEXI stood up **Nippon Gateway Infrastructure** on ex-NEC assets. KKR closed
**Global Infrastructure Investors V at $19.2bn** (final close, its largest ever, >$9bn already
committed including Global Technical Realty and Gulf Data Hub). Ownership of the physical
layer is being internalised rather than financed at arm's length.

---

## Committed vs. announced — the distinction that matters this week

Five of the largest headline numbers in the window are **not** committed capital and are
flagged `amount_estimated=1`:

| Headline | What it actually is |
|---|---|
| Brookfield / Paducah — $100bn | Total privately funded programme cost to 2032; Brookfield's own equity undisclosed |
| Brookfield / NAVER Korea — $9bn | **Nonbinding term sheet**, "up to"; $10bn total programme with NVIDIA at $1bn |
| Brookfield / Bloom — $25bn | Financing *framework*, 5x expanded from $5bn; not a close |
| Blackstone / Japan — $30bn | A stated 3–5 year *intention* in one Nikkei interview → candidate |
| KKR / SK Korea — $1.3bn | Platform value, not KKR's cheque |

Genuinely committed and closed this window: Aligned ($40bn, closed Jul 21), Williams
($5.34bn committed), KKR Fund V ($19.2bn final close), EDF power solutions NA ($4.2bn),
Aypa ($3bn equity), SoftBank/OpenAI tranche two ($10.0bn drawn Jul 1), QTS ($3.25bn priced).

---

## Escalation loop — what it produced

- **DigitalBridge Credit II** was found only in EDGAR. No press release exists. Form D/A filed
  2026-07-15 shows **$711.35m sold, 9 investors**, against $650m / 7 investors in the May 2025
  amendment — a quiet ~$61m of new digital-infrastructure credit commitments, invisible to the
  news cycle. This is the single best argument for sweeping Form D amendments every week.
- **Williams / Blackstone** was upgraded from press to Tier-1 by pulling the 8-K EX-99.1
  directly, which is also where the $4.4bn-capex + $0.9bn-consideration split and the year-7-to-14
  buyout right are stated.
- **Circular-reporting guard bit twice.** The AirTrunk SYD3 loan looked like six sources
  (TFTC, TradingView, Yahoo, FreeMalaysiaToday, The Star, Mingtiandi) and is one Bloomberg
  report. Same for the SoftBank ABB robotics loan. Both graded `candidate`, not `verified_alpha`.
- **Out-of-box angle that worked:** the DOE site-reuse route. Paducah surfaced through a
  government-selection announcement, not a fund PR, and is the template to watch — federal
  brownfield plus purpose-built generation, no queue.
- **Dead ends, logged honestly:** the Eversource 8-K mentioning GIP is a 2024 offshore-wind
  contingency, not a new deal; Blackstone Infrastructure Strategies' Form D/A ($4.66bn sold,
  17k+ investors) is a diversified evergreen vehicle, not an AI allocation, so it was
  deliberately excluded rather than padded in.

---

## Deliberately excluded (documented, not dropped)

- **Apollo/Blackstone $35bn Broadcom "AI XPV" SPV for Anthropic** — the largest private
  financing on record ($6bn A1 at T+100, ~$24–25bn A2 at 5.75%, $4.5bn B at 8.5%, Broadcom
  residual-value guarantee, Atlas SP $800m equity). Finalised **Jun 5–9, 2026**, outside the
  window. The in-window development — the paper beginning to trade on Jul 9 — is a syndication
  milestone, not new capital. Blackstone is a co-lead; this belongs in next week's baseline.
- **KKR Helix Digital Infrastructure** ($10bn+, with KIA, NVIDIA, Vistra; Adam Selipsky) —
  launched Jun 10–12. Still no disclosed site or first deployment.
- **Blackstone Digital Infrastructure Trust (BXDC)** $1.75bn IPO — May 2026.
- **Blackstone / Eurowind** up to €2bn — Apr 29, 2026.
- **Blackstone → Digital Realty $3.5bn Virginia sale** and **SoftBank → Hyundai Boston Dynamics
  exit** — divestments, not allocations; noted as context only.

---

## Confidence & limitations

Confidence is high on the verified set: 14 of 18 rows rest on a primary (issuer PR, counterparty
IR, or SEC filing), and the two largest — Aligned and El Paso — are confirmed by the recipients'
own disclosures. The soft spots are honest and marked: three amounts are programme or framework
sizes rather than commitments; the Williams consortium total is attributed to the lead because
Apollo's and KKR's slices are undisclosed (the KKR row deliberately carries a blank amount so
the $5.34bn is counted once); AUD-to-USD conversions on the two Australian loans are
approximations. Bloomberg, Benzinga, PitchBook and DataCenterDynamics blocked direct fetches
(403/paywall) — every finding sourced through them was cross-read via an accessible outlet, and
where the origin was a single Bloomberg report the row was graded `candidate` rather than
inflated by re-reporting. The Aligned deal is also logged by the sovereign agent from the MGX
side; dedupe downstream.

## Watch next week

1. Whether the **7%+ Sopaipilla clearing yield** repeats on the next hyperscaler carve-out — that
   number, not deal count, is now the leading indicator for this class.
2. **SB Neo**'s first capital raise, and whether SoftBank funds it on balance sheet or syndicates it.
3. First deployments out of **KKR Helix** and **Brookfield's AI Infrastructure Fund**, and whether
   KKR Fund V's remaining ~$10bn goes digital.
4. Closing of the **SoftBank / DigitalBridge $4bn take-private** (approved by DBRG holders, 2H26)
   — it converts a tracked alt manager into a SoftBank subsidiary and changes how this class is counted.
5. **STACK Melbourne (A$8.5bn)** and **AirTrunk SYD3 (A$4.3bn)** — whether either converts from
   bank talks to a signed facility, and at what spread.
6. **Apollo** promotion. It appears in the Williams JV, the $35bn Anthropic SPV and the xAI GPU
   lease; leaving it off the watchlist is now the largest coverage gap in this class.
