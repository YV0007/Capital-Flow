# Alt-Managers Weekly Research — 2026-W44 (window: ~2026-09-26 to 2026-10-26)

## Headline
Mega-fund/AI-infra financing stayed busy, but most of the headline-grabbing numbers this
week (Blackstone's $200B data-center portfolio valuation, Blue Owl's IREN GPU package,
Apollo/Blackstone/Broadcom's $35B AI XPV platform, KKR's $19.2B infra fund close, Goldman's
WSIP V first close, Brookfield's Kentucky/Bloom Energy deals) were confirmed **before**
this window and are background, not new events — they're omitted from the CSVs to avoid
re-filing old deals as new. Two rows made it to `verified_events.csv`, two weaker leads to
`candidate_events.csv`.

## Biggest signals
1. **SoftBank closes out its $30B OpenAI follow-on program** (2026-10-01, verified,
   Tier 1 — SoftBank's own press release). The $10B third tranche, funded from the
   $11.1B foreign-currency senior-note issuance (reportedly the largest high-yield
   corporate bond ever), takes cumulative SoftBank investment in OpenAI to $64.6B for a
   ~13% stake. This was pre-scheduled (not accelerated for an IPO, per Altman's September
   comments) and closes a program that's been running since February — the real news is
   that it landed on schedule and the bridge loan is fully repaid, not that it's a new
   commitment.
2. **Goldman Sachs syndicates a $200M project-finance commitment for Digi Power X's
   Columbiana, AL AI data center** (2026-10-13, verified_alpha). Small in absolute terms,
   but a clean example of the class brief's "debt behind the buildout" thesis: a
   project-SPV-level loan backed by an unsecured parent guarantee, anchored by Cerebras's
   $1.1–2.5B 10-year capacity deal. Caveat flagged in the row: Goldman is confirmed as
   arranger/syndicator, not confirmed as the principal lender (the press release names
   only "a major lending institution").
3. **Watch: the AI-debt market is starting to show friction, not just growth.** Blue Owl's
   Stack Infrastructure is out marketing a ~$6B loan for a third Melbourne campus — a loan
   one Bloomberg source explicitly frames as "a test of investor sentiment toward AI debt"
   — and Apollo is reportedly leading a $40B financing for SpaceX's Nvidia GPU order with
   closing not expected before 2027 and no public confirmation from any party. Both are
   single-origin (Bloomberg / FT) leads filed as candidates; neither has a primary
   confirm yet and both deserve a Tier-1 check next week once (if) documentation signs.

## Rejected / discarded leads worth noting
- A widely-indexed "Brookfield buys 30-acre Navi Mumbai data-center land for Rs 550 crore"
  story is the **2021** K Raheja Corp deal; a crawl/aggregator date of "October 20, 2026"
  on one mirror made it look current. Confirmed stale via cross-source dating and dropped
  — not filed anywhere.
- KKR/CPP's $10B Sempra Infrastructure Partners stake (announced Sept 2025, expected to
  close Q2–Q3 2026) has no confirmed closing yet as of this run; nothing new to file.
  Worth a forward check once a closing 8-K/press release lands.

## What to watch next week
- Does Stack Infrastructure's Melbourne loan or the Apollo/SpaceX financing get a term
  sheet or signed facility? Either would move from candidate to verified.
- Sempra Infrastructure Partners (KKR/CPP) closing — due within the Q2–Q3 2026 window,
  now overdue; check Sempra's 8-K filings and KKR's press room directly.
- Digi Power X's $200M commitment is due to close within ~90 days of 2026-10-13 —
  worth a forward check for the definitive documentation / actual lender name.
- Note for the engine: EDGAR live lookups (`engine.edgar filings`) returned a 403 from
  this session's network sandbox (data.sec.gov blocked by the egress policy here); only
  the local `cik`/`exists` lookups worked. Flagging in case this is session-specific and
  not expected — it blocks the deterministic Tier-1 path this brief calls for first.

## Counts
- verified_events.csv: 2 rows
- candidate_events.csv: 2 rows
- discovered_allocators.csv: 2 rows (PIMCO, CPP Investments)
- source_log.csv: 25 sources checked
