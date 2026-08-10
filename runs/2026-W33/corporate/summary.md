# Corporate — ISO week 2026-W33 (window ~2026-07-11 -> 2026-08-10)

**2 verified (1 verified, 1 verified_alpha) - 1 candidate.** A thin week by row count relative to
W32, for two reasons: (1) the biggest corporate story of the last 30 days - Amazon's completed
$50bn OpenAI position and $10bn Anthropic tranche - was already disclosed and booked in last
week's run (2026-07-31 10-Q), so it is not re-recorded here; (2) this run's network policy
blocked WebFetch/SEC EDGAR to every external domain (see Limitations below), which materially
constrained the mandatory Tier-1 filing sweep this class brief requires. What's here is small
but real.

## What actually moved

**1. Alphabet is bankrolling the startup its own departing chief scientist just founded.**
Jeff Dean (27-year Google veteran, outgoing chief scientist), Sanjay Ghemawat, Oriol Vinyals and
Quoc Le left Google on 2026-08-05 to found Discovery Loop, a public-benefit corporation aimed at
automating the experimental loop of scientific and engineering research. Sundar Pichai's own
company statement confirms Google is a "founding investor and Cloud partner." No dollar amount
is disclosed by anyone - Alphabet, the founders, and co-leads Radical Ventures and Khosla
Ventures all declined to size the round. Two things make this an unusual row: Google is investing
in a company built from its own talent exodus, and the "investment" is part-cash, part-compute
(a cloud partnership), echoing the hyperscaler compute-commitment pattern this brief flags for
balance-sheet deals generally, not just infrastructure ones. Alphabet shares fell ~4% (~$185bn of
market cap) same-day.

**2. NVIDIA's venture arm keeps stacking co-investors alongside other CVCs, not just VCs.**
NVentures put an undisclosed check into Prime Intellect's $130M Series A ($1bn valuation,
2026-07-08, led by Radical Ventures) - sitting on the same cap table as Intel Capital and Dell
Technologies Capital. Three different corporate venture arms (NVIDIA, Intel, Dell) backing one
open-agentic-AI infrastructure startup in a single round is itself a signal: the CVC land-grab
for "compute-independent" AI infrastructure plays is broadening past the usual hyperscaler VCs.

**3. NVIDIA may be about to buy the power layer under Stargate - but it isn't confirmed yet.**
The Information reported (2026-08-08) that NVIDIA plans to invest $2bn now (up to $3bn total) for
a ~20% stake in Lancium, the Blackstone-backed developer of the Abilene, TX site that anchors the
OpenAI/SoftBank/Oracle Stargate build-out, at a ~$10bn valuation. If real, this is NVIDIA moving
one layer further down the stack than the Volta Infra deal from two weeks ago (financing the
compute buyer) - here it would be financing the power/land developer directly. Filed as
`candidate`: neither NVIDIA nor Lancium has confirmed on the record, and every outlet covering it
(Reuters, Seeking Alpha, DCD-adjacent wires, dozens of aggregators) traces to the same Information
scoop - one origin, not many, per the circular-reporting guard.

## Escalation-loop outcomes on weak leads
- **NVIDIA <-> Lancium** -> filed as `candidate`. Origin traced to a single Information article;
  checked for an NVIDIA newsroom release, a Lancium release, and a Blackstone statement - none
  exist yet. Also wanted to run an EDGAR full-text sweep for an 8-K or Schedule 13D/G, but this
  session's network policy blocked SEC EDGAR access outright (see Limitations) - that specific
  check is UNCHECKED, not a checked zero, and is the top item to re-run next week.
- **NVentures <-> Revolut** -> investigated, then DROPPED rather than booked. A UK Companies
  House confirmation statement (surfaced 2026-07-17 to 07-20) shows NVentures LLC holding 141,834
  Revolut shares (~$196M at the November 2025 round price). Two reasons it's excluded rather than
  filed as a row: (a) the capital actually moved in a November 2025 SECONDARY share sale - money
  went to a selling shareholder, not new capital into Revolut, and the event itself is ~9 months
  old, only the disclosure is fresh; (b) fintech/crypto-adjacent Revolut doesn't map to any
  canonical sector this platform tracks (ai-labs through defense-tech) even loosely. Logged in
  source_log, not silently dropped.
- **Intel Capital <-> Zenity** -> investigated (Intel Capital's own newsroom confirms
  participation in a $125M Series C for an AI-agent security platform, 2026-08-03), but not
  booked as a row: Intel's individual check size is undisclosed, Intel is a participant (not
  lead) alongside Norwest and six others, and "AI agent security software" doesn't cleanly fit a
  canonical sector. Recorded Intel Capital in `discovered_allocators.csv` instead, since it keeps
  showing up (also in the Prime Intellect round) and isn't formally on the corporate watchlist.
- **NVIDIA <-> Groq $20bn deal, NVIDIA <-> Poolside up to $1bn, Amazon <-> X-energy SMR $500M,
  Alphabet <-> Proxima Fusion** -> all found, all confirmed OLD (Dec 2025, Oct 2025, Oct
  2024/May 2026 update, and already booked in last week's W32 run respectively) - traced and
  excluded to avoid double-counting or stale-event inflation, not silently skipped.

## Coverage gaps and honest limitations
- **This session's network egress policy blocked WebFetch to every external domain tested**,
  including www.sec.gov, efts.sec.gov (EDGAR full-text search), nvidianews.nvidia.com,
  news.microsoft.com, aboutamazon.com, about.fb.com, investor.oracle.com, blog.google, and
  ordinary press domains (CNBC, TechCrunch, Fool, gurufocus, dealroom, techtimes,
  primeintellect.ai, radical.vc). The `WebSearch` tool's grounded retrieval still worked and is
  the sole basis for every row here, including the one graded `verified` (Alphabet/Discovery
  Loop) - its Tier-1 URL (blog.google) is real and was surfaced with direct quoted text via
  WebSearch, but this agent could not independently render the page. This is a materially weaker
  evidentiary position than a normal run and should be treated as such; the mandatory Tier-1 SEC
  EDGAR sweep for Microsoft, Amazon, Meta, Oracle and NVIDIA (8-K / 10-Q / 13D-G) could NOT be
  executed this week at all. Re-run with EDGAR access before trusting this week's "zero" on those
  five names as a checked zero.
- **Oracle again produced nothing** - consistent with W32, but this week that zero is unchecked
  for EDGAR (see above) and only checked via IR/press search.
- **Two amounts are undisclosed** (Alphabet->Discovery Loop, NVIDIA->Prime Intellect slice) -
  genuinely unsized by every source found, nothing inferred.
- **WebSearch budget was exhausted mid-run** (session cap), cutting short further sweeps of M12
  and additional NVentures/GV deal flow. Treat M12 and GV as under-covered this week, not
  confirmed quiet.

## What to watch next week
1. **NVIDIA/Lancium** - an NVIDIA or Lancium press release, or an EDGAR filing (once reachable),
   would convert the candidate row to verified; also watch for Blackstone comment.
2. **Discovery Loop's seed round close** - founders declined to size it at launch; a later
   TechCrunch/company follow-up disclosing the amount would let this row carry a real amount_usd.
3. **Re-run the SEC EDGAR full-text sweep** for Microsoft, Amazon, Alphabet, Meta, Oracle, NVIDIA
   once network access is restored - this week's brief could not execute the class's mandatory
   Tier-1 check at all.
4. **Intel Capital** - two co-investments alongside watchlist CVCs in five weeks (Prime Intellect,
   and via Zenity's cap table logic) - worth deciding whether to formally add to the watchlist.
