# Public Filings — 2026-W32 (week ending 2026-08-07)

Cross-class sweep of SEC EDGAR (full-text search, company search, `data.sec.gov`
submissions) plus issuer-official press releases, run against the other five
agents' candidate and verified files. Two jobs: upgrade their weak rows to
Tier-1, and pull events straight out of filings that nobody else saw.

**23 verified rows / 14 candidate rows / 8 discovered allocators / 91 sources logged.**

---

## What actually moved

### The most interesting thing this week is a lease, not a round

TeraWulf's Q2 8-K (Ex-99.1, 2026-08-05) discloses a **20-year, ~401MW data
center lease with Anthropic** at the Justified Data Campus in Kentucky —
**~$19bn of contracted revenue over the initial term, up to ~$33bn** if both
five-year extensions are exercised. No agent had this. It matters because the
engine currently models Anthropic only as a *recipient* of capital (Amazon's
$10bn follow-on sits in corporate/). This filing shows Anthropic is also one of
the largest *deployers* of capital into physical infrastructure in the whole
universe — via lease obligations rather than equity, which is precisely the kind
of commitment that never shows up in a funding-round feed.

### Brookfield's Q2 release is the densest single Tier-1 document of the week

BAM's earnings release (Ex-99.1 to an 8-K, 2026-08-05) yielded **five events on
its own**, four of them new to the engine:

- **AI infrastructure strategy held its first close — $5bn of commitments to
  date.** A dedicated AI-infra vehicle, separate from the infrastructure flagship.
- **$1.0bn of incremental construction funding into an unnamed U.S. semiconductor
  fabrication facility.** Counterparty not named in the filing; Brookfield's only
  disclosed US fab vehicle is the Intel Arizona JV, but that attribution is
  inference and is flagged as such in the row.
- **DOE partnership behind Westinghouse reactor deployment, supported by $17.5bn
  of DOE funding** — recorded against US Government, sovereign class, nuclear.
- **France AI infrastructure framework expanded from €20bn to €30bn.** `amount_usd`
  left deliberately blank: it is a EUR framework ceiling, and converting it would
  invent precision the filing does not carry.
- $7.9bn raised in the quarter for the infrastructure flagship (pre-first-close).

Two of these sit inside a "this year" strategic-initiatives block, so the
original announcement may predate Q2 — `event_date` is left blank and the caveat
is written into `notes` rather than papered over.

### a16z has split its AI book in two

Three Form Ds filed the same day, 2026-07-16: **Fund X-B – AI Infrastructure,
L.P.**, **Fund X-B – AI Applications, L.P.**, and **LSV Fund V-B, L.P.** All
indefinite offerings, all zero sold, first sale yet to occur — so these are
vehicle formations, not raises, and every `amount_usd` is blank. The signal is
in the naming, not the number: a16z is now underwriting the physical compute
stack out of a dedicated sleeve instead of the generalist fund.

### Greenoaks quietly raised ~$692m into one position

Form D/As of 2026-07-14: **Greenoaks Prime Radiant Founders LP sold $576,519,835
from eleven investors**, with an offshore sibling adding $115,480,165 from four.
An average ticket above $50m is a concentrated single-asset SPV. Neil Mehta —
already on the individuals watchlist — is a named promoter, but Greenoaks itself
is untracked, so the vehicle holding the money is invisible to the engine today.
Added to `discovered_allocators.csv`. The underlying company is a codename;
"Prime Radiant" appears nowhere else. (A separate `Prime Radiant One-1 LP`
Form D was checked and is unrelated — different GP, zero sold.)

### The Coatue money that did show up is not the money that was reported

Two Form Ds of 2026-07-15 — **Coatue Growth Fund VI Private Investors US, LLC
($778.23m sold, 773 investors)** and its **Cayman sibling ($526.96m, 395
investors)** — together ~$1.31bn. The tell is the related-persons list: **J.P.
Morgan Private Investments Inc. is named as both Executive Officer and Promoter**.
These are private-wealth feeders into Coatue's growth fund, not an institutional
raise. They are explicitly *not* the reported $8bn retail/evergreen fund, which
remains unconfirmed — see below.

---

## Confirms: what upgraded and what did not

**Upgraded to Tier-1 (5):**

| Event | Primary reached |
|---|---|
| Vinod Khosla → Khosla Ventures MM SPV | Form D, fully sold at $60.5m, 7 investors |
| NVIDIA → Volta Infra Holdings | Volta's own launch page (was tier 3, Bloomberg) |
| SoftBank → ABB Robotics | SoftBank + ABB press releases, USD 5.375bn |
| NVIDIA → Nebius | 13G re-emitted with the actual document: 9.3%, pre-funded warrant, exercise barred until 2026-09-11 |
| Jeff Bezos → Generalist AI | Form D proves the round ($363.8m sold of $400m) but **not Bezos** — held at `verified_alpha`, not promoted |

The Bezos row is the honest-grading case worth flagging: a Form D never names
non-control LPs, so a Tier-1 document that confirms the round does *not* confirm
the investor. Tier was raised to 1; status was not.

The SoftBank row splits in two on purpose. The **$1.75bn is a bank syndication**,
not consideration — loan tranches are private credit-market events with no filing
anywhere, so that stays a candidate. The **$5.375bn acquisition underneath it is
Tier-1 confirmed** and is emitted separately. Do not double-count.

**Nine candidates hunted and left standing**, each with the negative result
written into `notes` rather than dropped:

- **NVIDIA/OpenAI Ohio** — NVIDIA's last 8-K is 2026-07-02; nothing since but a
  Form 3, a Form 4 and the Nebius 13G. A guarantee is contingent credit support
  and would not trigger an 8-K anyway. **The FY27 Q2 10-Q, due late August, is the
  real trigger** — an off-balance-sheet guarantee of that size has to appear there.
- **Coatue/Databricks $3bn** — Databricks, Inc. (CIK 1587468) files its own
  Form Ds; the most recent are two dated 2025-12-31. **No 2026 Form D exists.**
  If the round had closed mid-July the filing would be overdue, which is
  consistent with the term-sheet-only status.
- **Khosla 2026 fund family** — the filings partly contradict the headline. All
  four vehicles (IX, Opportunity III, IX Strategic, Seed G) filed Form Ds in
  **2025**, not 2026, and registered offering ceilings sum to ~$3.2bn, not $5.5bn.
- **Coatue retail fund $8bn** — the vehicle exists and is filing actively
  (424B3, SC TO-I, two 40-APPs), but the 2026-07-08 supplement read in full covers
  only a compliance-officer appointment and carries no size figure. The SC TO-I
  structure also means "size" is a moving NAV, not a closed commitment.
- **Cathedral** — zero Form D hits; company-name search returns only unrelated
  filers. Not an EDGAR filer yet. Held at `verified_alpha`.
- **AirTrunk SYD3** — one EDGAR hit, a registration statement that merely names
  the asset. The right primary is Australian (ASIC charge / PPSR security
  interest), not EDGAR — logged as the next escalation step.
- **Blackstone Japan $30bn** — a Nikkei interview stating a three-to-five-year
  intention. Under the scope rules this is guidance, not allocation.
- **Mubadala Akita** — "weighs", spokesperson declined to comment, information
  not public. Nothing committed.
- **Thrive Holdings, P-1 AI, Prentis, KIC, Glow** — no matching filer. The Glow
  and P-1 AI misses are honest *unresolved-issuer* results (names too generic /
  unindexable), not confirmed absences.

---

## Watch next week

1. **NVIDIA's FY27 Q2 10-Q, late August.** The single highest-value pending
   document in the universe: the Ohio guarantee either appears in the
   off-balance-sheet/guarantee footnote or it does not exist yet.
2. **A Databricks, Inc. Form D.** Cleanest possible confirmation trigger for the
   Coatue round, and it is now arguably overdue.
3. **Form D/A amendments on the Khosla vehicles** (CIKs 2074230 / 2074231 /
   2074203) reporting amounts *sold* — that is what would substantiate $5.5bn.
4. **Who "Prime Radiant" is.** ~$692m from fifteen investors into one unnamed
   company is the largest unexplained concentration found this week.
5. **Whether the Anthropic lease pattern repeats.** If frontier labs are
   committing $19bn-scale multi-decade leases, the engine needs to treat AI labs
   as allocators, not just recipients — the TeraWulf filing may be the first of
   several.
