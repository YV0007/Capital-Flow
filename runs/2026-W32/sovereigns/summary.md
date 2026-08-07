# Sovereigns — ISO week 2026-W32 (disclosures ~2026-07-08 → 2026-08-07)

**16 verified/verified_alpha rows, 5 candidates.** Watchlist: MGX, Mubadala, Saudi PIF,
US Government. Nine of the sixteen verified rows are Tier-1 primaries read directly
(MGX press release, Aligned/AIP release, NIST/Commerce, energy.gov, NNSA, three SEC filings).

## What actually moved

**Abu Dhabi finished raising and started spending.** MGX closed Fund I at **$49bn** on
1 July, $4bn above target — the largest dedicated AI fund ever raised. Three weeks later
the AIP/MGX/BlackRock-GIP consortium **closed** the $40bn Aligned Data Centers buyout
(largest data-centre M&A on record) and committed a further **$5bn of growth capital** on
top. The two events are the same story: the vehicle filled up, then immediately deployed
into physical AI capacity. MGX's own slice of Aligned is undisclosed in every primary
source, and MGX is *also* a founding partner of AIP — so its exposure is double-counted
across two of the three named buyers. Both Aligned rows therefore carry a blank
`amount_usd` and the headline in `round_total_usd`.

**Washington kept buying equity with grant money.** On 29 July the Commerce CHIPS R&D
Office announced letters of intent with **seven** companies for **$874m** — GlobalFoundries
$300m (silicon photonics / co-packaged optics), Kepler $245m (AI memory), Multibeam $140m,
Extropic $75m, Thintronics $50m, OBSIDIA $34m, Aeluma $30m — and takes a *minority,
non-controlling equity stake in each* as a condition. Commerce disclosed ~1% of
GlobalFoundries. Every one is a **non-binding LOI**: no cash has moved. Separately DOE
announced the first **Genesis Mission** cohort on 22 July (278 awards, ~$293m per the RFA
vs "$250m available" per trade press → `amount_estimated=1`), of which the largest single
award is **$60m over three years** to the AI-for-nuclear *Prometheus* project at Idaho
National Laboratory.

**Riyadh's biggest cheque was not an AI cheque.** The PIF-led **$55bn Electronic Arts
take-private closed 4 August** — the largest LBO on record, ~$36bn of consortium equity
(PIF 93.4%, Silver Lake 5.5%, Affinity 1.1%) plus ~$20bn of JPMorgan-led debt. Confirmed
three ways in EDGAR: EA's 30 July and 4 August 8-Ks and PIF's 5 August 13D/A reporting
zero shares held directly post-close. Off-taxonomy (gaming) and flagged, but it dwarfs
everything else in the class and PIF's ~$33.6bn share is a *derived* number. PIF also drew
**$800m** into Lucid via Ayar Third Investment Co on 6 July (existing facility, not a new
commitment) and anchored Brookfield's **~$2bn** first close of a Middle East PE fund with
its own commitment undisclosed.

## Three signals worth carrying forward

1. **The US Government is now an equity investor, not a grantmaker.** Seven CHIPS LOIs in
   one day, all equity-conditioned, on top of a portfolio press now counts at ~30 companies.
   The interesting flow is that $300m of it lands inside GlobalFoundries — a company ~73%
   owned by Mubadala. US state capital is funding an Abu Dhabi sovereign's asset.
2. **Federal land is becoming the sovereign's contribution instead of federal money.**
   Paducah (Brookfield/NextEra, 1.8GW campus, ">$100bn privately funded") and Savannah River
   (Amentum, 1GW + 2GW generation) are both structured so the government commits *no capital* —
   it commits a site, an interconnection and a lease. Both are filed as candidates for exactly
   that reason. If this becomes the template, US Government "AI investment" will stop showing
   up as dollars entirely.
3. **A fourth sovereign AI pool appeared.** Korea approved a KRW20tn (~$14bn) AI/data-centre
   account inside KIC on 30 July, letting it deploy domestically for the first time, with a
   KRW200tn National Growth Fund reportedly behind it. Operations start 2027 — pure target,
   filed candidate.

## Deliberately not recorded

Mubadala's Akita, Japan data centre (up to ~$6.3–6.8bn, 500MW) is **"weighing"**, not
committed, and every outlet traces to a single Bloomberg report of 6 August — one source,
not five. PIF signed three non-binding MoUs in eight days (US EXIM up to $15bn, IFC/MIGA up
to $9.5bn, I Squared up to $2bn *into* PIF's portfolio); only the EXIM ceiling is filed, as a
candidate, and the I Squared MoU is noted here rather than as a row because PIF is the
*recipient*. Mubadala's 3 August "$170bn / 44% of portfolio in the US" is cumulative
exposure, not a flow. HUMAIN's $1.2bn National Infrastructure Fund framework is January
2026, and the QIA/Brookfield $20bn JV is December 2025 — both out of window.

## Watch next week

- Whether any of the seven CHIPS LOIs converts into a definitive agreement (that is when
  money and the equity stakes actually move).
- The UAE ambassador's mid-August Akita visit — the likeliest trigger for a real Mubadala/MGX
  Japan commitment.
- Where MGX Fund I's remaining dry powder goes now that Aligned has closed; AIP has ~$95bn of
  announced-but-undeployed capacity against its $30bn equity / $100bn total target.
- Korea's National Assembly taking up the KIC amendments in August.
- Any first drawdown under the PIF/US EXIM export-credit MoU.

## Confidence & limitations

High confidence on the US Government and PIF rows (SEC and .gov primaries read directly);
medium on the Gulf rows, where the recurring failure mode is that **sovereigns disclose the
consortium total and never their own slice** — four rows carry a blank `amount_usd` for this
reason. `pif.gov.sa` and `inl.gov` are Cloudflare/403-blocked to automated fetch, so three
rows are graded `verified_alpha` on independent secondaries rather than `verified` even
though an official primary is known to exist. EDGAR full-text search for MGX and Mubadala
across the window returned no direct filings — Gulf sovereigns leave almost no US primary
trail outside their portfolio companies' own disclosures, which is the structural blind spot
for this class.
