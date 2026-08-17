# Corporate — ISO week 2026-W34 (window ~2026-07-18 -> 2026-08-17)

**0 verified/verified_alpha - 1 candidate (continuing).** A genuinely quiet week for the
corporate watchlist (Microsoft, Amazon, Alphabet, Meta, Oracle, NVIDIA) *as allocators*.
This is a checked zero, not an unchecked one, on the press/IR side: every name was swept
individually across balance-sheet deals, CVC vehicles (M12, GV, NVentures, Intel Capital),
and JV/SPV structures. The one open thread from last week — NVIDIA/Lancium — is carried
forward, still unconfirmed. See Limitations for what could not be checked this week.

## What actually moved (and why nothing new got booked)

**1. NVIDIA/Lancium is still a rumor, not a deal — second week running.** The Information's
2026-08-08 scoop (NVIDIA to invest up to $3bn, ~20% stake, in the Blackstone-backed Stargate
power developer) has now been repeated by a dozen more outlets (gurufocus, MarketScreener,
Dealroom, BigGo, Futuriom, TFTC, ForeignPolicyJournal, NewsBytesApp) over the past nine days,
but every one of them still traces to the same single Information article — no NVIDIA
newsroom release, no Lancium press release, no Blackstone statement, and Reuters explicitly
notes neither company responded to requests for comment. Re-filed as `candidate` again this
week under the circular-reporting guard.

**2. A wave of NVIDIA stakes hit the tape this week — all of them stale capital, fresh
disclosure only.** NVIDIA's 13F/13G cycle (filed/covered 2026-08-14) revealed a $21bn stake
in SpaceX and reconfirmed the (already fully depreciated) $30bn Intel position. The SpaceX
stake is not a new event: press coverage is explicit that it "traces back to Nvidia's
investment in xAI, completed in January [2026], shortly before Musk merged the AI lab into
SpaceX" — the capital moved roughly seven months ago; this week only the *disclosure*
(quarter-end 13F/13G reporting) is new. Excluded from verified/candidate for the same reason
last week's Revolut/NVentures lead was excluded: a fresh filing date is not a fresh
capital-allocation event. Logged in source_log for the audit trail.

**3. NVIDIA's $500bn "financing platform" with Apollo/BlackRock/Blackstone/Brookfield/
Goldman/KKR (announced 2026-08-10, Tier-1: NVIDIA's own newsroom + Blackstone's own press
release) is real and large, but it is not a booked event for this class.** Every primary
source is explicit that these are MOUs to mobilize *third-party* capital, structured so
outside investors — not NVIDIA's balance sheet — fund the buildout, using NVIDIA compute as
collateral for SPV-issued debt. NVIDIA is the enabler/collateral-provider here, not the
allocator moving its own cash; the actual capital commitments belong to the six financial
institutions once each platform closes (a lead worth flagging to the alt-managers agent,
not a corporate-class row).

**4. Everything else found this week was either old, self-capex, or backwards.** Checked
and excluded: Amazon's up-to-$25bn Anthropic tranche and Alphabet's up-to-$40bn Anthropic
commitment (both April 2026, already outside any recent window and presumably already
booked); NVIDIA's participation in Volta Infra Holdings' $300M round (2026-08-04, already
booked in runs/2026-W32/corporate and runs/2026-W32/filings — not re-filed here); NVIDIA's
Coherent Corp $2bn stake (SEC 8-K, but dated 2026-03-02 — too old); Meta's Manus unwind
(CNBC, 2026-08-11 — this is Meta *giving back* an old Dec-2025 acquisition after Chinese
regulators forced it, not new capital deployed); Meta's TerraPower/Oklo/Vistra nuclear power
deals (announced 2026-01-09 — power-purchase agreements with no disclosed equity stake, and
old regardless); and the raw capex headlines (Microsoft's ~$190bn FY26 capex, Amazon's ~$220bn,
Meta's $125-145bn) — these are self-funded infrastructure buildouts with no distinct
counterparty "target," not capital-allocation events under this platform's definition.
Berkshire Hathaway's $10bn purchase of Alphabet stock (2026-08-08/14) was checked and
excluded on the class gotcha: Alphabet is the *target* of that capital here, not the
allocator — out of scope for this agent regardless of size.

**5. A near-miss worth flagging: NVIDIA did NOT invest in CodeRabbit's Series C.** Early
search snippets read as if NVIDIA participated in CodeRabbit's 2026-08-12 $143M round at a
$1.5bn valuation; the actual company press release (BusinessWire, Tier-1) lists NVIDIA only
as an *existing backer and customer*, not a participant in this specific round. Chased down
and excluded rather than booked on a loose headline — a good example of the escalation loop
catching a false positive.

## Escalation-loop outcomes on weak leads
- **NVIDIA <-> Lancium** -> `candidate`, carried forward. Origin traced to one Information
  scoop; primary hunt (NVIDIA newsroom, Lancium site, Blackstone statement) came up empty
  again; registry/legal and EDGAR checks are UNCHECKED this week too (network policy, see
  Limitations), not a checked zero.
- **NVIDIA <-> SpaceX ($21bn 13F/13G disclosure)** -> investigated, DROPPED as a row. Traced
  to a January 2026 xAI investment (pre-merger into SpaceX); only this week's quarter-end
  filing is new, the capital itself is ~7 months old. Same pattern as last week's Revolut
  exclusion — filed here in notes, not silently dropped.
- **NVIDIA <-> CodeRabbit** -> investigated, DROPPED. NVIDIA is a returning/existing backer
  and a customer, not a participant in the fresh 2026-08-12 Series C per the company's own
  BusinessWire release (Tier-1) — false positive from aggregator headlines caught and killed.
- **Meta <-> Manus** -> investigated, DROPPED. This week's news (2026-08-11) is the
  *unwinding* of a December-2025 acquisition under Chinese regulatory pressure — a capital
  reversal, not a capital-allocation event.
- **GV <-> LifeMine Therapeutics ($188M Series E, 2026-08-06)** -> investigated, DROPPED.
  GV is a returning (not new) participant with an undisclosed check size in a fungal-derived
  drug-discovery biotech round — doesn't map to any canonical sector (not AI-related, and
  outside the ev-automotive/private-credit/diversified-pe carve-outs too).
- **NVIDIA <-> $500bn Apollo/BlackRock/Blackstone/Brookfield/Goldman/KKR financing MOUs** ->
  investigated in depth via NVIDIA's own newsroom and Blackstone's own press release (both
  Tier-1), DROPPED as a corporate-class row: NVIDIA is structuring *third-party* capital
  (collateralized by its hardware), not deploying its own balance sheet. Worth surfacing to
  the alt-managers agent once individual platform closings disclose each institution's
  commitment.

## Coverage gaps and honest limitations
- **This session's network egress policy again blocked WebFetch to every external domain
  tested**, including www.sec.gov, efts.sec.gov (EDGAR full-text search), and ordinary
  press/IR domains (blogs.microsoft.com, techcrunch.com, www.cnbc.com, www.reuters.com) —
  identical to the W33 run. WebSearch's own grounded retrieval is the sole basis for every
  finding and exclusion in this report. The mandatory Tier-1 SEC EDGAR sweep (8-K, 10-Q/10-K,
  13D/G) for all six watchlist names could not be executed directly this week either; where a
  specific EDGAR document surfaced in search results (e.g. NVIDIA's Coherent 8-K, the Nebius
  13G) its content came from WebSearch's grounded summary, not a page this agent rendered
  itself.
- **Oracle again produced nothing** — third straight week. Searched broadly (IR page,
  acquisitions trackers, general news); found only routine equity/debt capital-raising (Oracle
  as issuer, not allocator) and ordinary 13F filings *into* Oracle by third parties. Treat as
  checked-and-quiet on the press side, unchecked on EDGAR.
- No new corporate allocators were discovered this week worth adding to
  `discovered_allocators.csv` beyond names already tracked from prior weeks (M12, GV, NVentures,
  Intel Capital) — omitted per the instructions when there's nothing new.

## What to watch next week
1. **NVIDIA/Lancium** — third week open. An NVIDIA or Lancium press release, an NVIDIA 10-Q
   footnote, or a reachable EDGAR 8-K/13D-G would convert this to verified.
2. **The $500bn NVIDIA financing-platform MOUs** — watch for the first individual platform to
   actually close and disclose a specific institution's commitment (Apollo, BlackRock,
   Blackstone, Brookfield, Goldman, KKR) — that would be a bookable alt-managers row, and
   worth flagging cross-class.
3. **Re-run the SEC EDGAR full-text sweep** for all six watchlist names once network access is
   restored — three consecutive weeks now without a direct EDGAR read is a material coverage
   gap for a class whose brief makes that check mandatory.
4. **Oracle** — keep checking; a hyperscaler this deep into the Stargate/AI buildout with zero
   allocator-side activity for three weeks running is itself worth a closer look (is it a real
   quiet spell, or is Oracle's capital deployment structured entirely through JVs/SPVs that
   don't surface under Oracle's own name?).
