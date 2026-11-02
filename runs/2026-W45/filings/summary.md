# Filings agent — 2026-W45

## Network path
`python -m engine.edgar` (data.sec.gov) and direct `WebFetch` to www.sec.gov were
both confirmed network-blocked in this run: the CLI raised `Tunnel connection
failed: 403 Forbidden`, direct WebFetch raised `getaddrinfo ENOTFOUND www.sec.gov`,
and `python -m engine.edgar sweep 2026-W45` returned `{"entities":14,"leads_new":0,
"errors":14}` — confirming the block, not absence of filings. The agent-proxy status
endpoint showed repeated `connect_rejected` / gateway-403 entries for
`data.sec.gov:443`. **WebSearch was the only working path**, and — usefully — its
own internal fetch *did* resolve and quote the text of several `sec.gov/Archives/
edgar/...` documents directly (Meta's FWP/424B5), even though the standalone
WebFetch tool could not reach the same host. For small/thin filings (Form D on
General Intuition, Kalshi, Serval) WebSearch could only surface third-party
aggregator summaries (vcbeast.com, formds.com) of the filing, not the primary
document text itself — those are logged but not used to upgrade status, per the
"never invent a URL you haven't actually read" rule. `engine.edgar exists` (local
DB lookup, no network) worked fine throughout and was used before considering any
new row.

## Part A — confirming/upgrading the other five agents' rows

**Upgraded (verified_alpha -> verified, Tier 3 -> Tier 1):**
- **NVIDIA -> Meta Platforms** ($3B, corporate/verified_events.csv row 1). Found
  Meta's own SEC Free Writing Prospectus (filed 2026-10-26 alongside its ~$22.5B
  Class A common stock shelf take-down) naming NVIDIA, AMD and Broadcom as
  "Cornerstone Investors." **Important nuance, not a clean confirm of the $3B
  figure**: Meta's filing gives only a non-binding **$5.0B aggregate across all
  three companies**, with no per-company breakdown, and explicitly says the
  indications of interest are not binding commitments. So the Tier-1 filing
  confirms NVIDIA's SEC-documented participation (upgrading that fact to
  `verified`), but does **not** corroborate the press-reported $3B NVIDIA-specific
  slice — amount_usd is left blank in my upgrade row rather than restating an
  unconfirmed number (CONTEXT.md mistake #2 guard). Filed as a new row in my
  `verified_events.csv` with `notes` explaining the upgrade and the caveat, so
  ingest can merge it onto the corporate agent's original row.

**Checked, no upgrade found (left as the originating agent filed them):**
- **NVIDIA UK stakes** (Prima Mente, Boltz, Foresight, Hiverge, Riverlane) and
  **French stakes** (Genesis AI, Pigment, Entalpic) — all foreign private
  companies; no SEC filing exists or would be expected (not material to NVIDIA,
  no US Reg D offering). No Tier-1 path available.
- **Khosla Ventures -> General Intuition** — found real evidence of a Form D
  (General Intuition Holding B.V., CIK 2157282, accession 0002157282-26-000002,
  filed 2026-10-02, first sale 2026-09-18, ~$175.2M sold of a ~$220.5M offering,
  32 investors) via a third-party aggregator (vcbeast.com), which corroborates the
  round's existence/size but not Khosla's participation by name (Form D doesn't
  list all investors), and WebSearch could not resolve the actual primary EDGAR
  document for this small filer. Did not force an upgrade on an unresolved URL.
- **Sequoia / a16z -> Kalshi** ($1B Series G, $40B valuation) — found Kalshi's
  most recent indexed Form D, but it corresponds to the **prior Series F** round
  (filed 2026-08-25, $1.12B sold, first sale 2026-04-03, tied to the May 2026
  $22B-valuation round per a company spokesperson quote in press). No Form D for
  the Oct 29 Series G/$40B round surfaced. No upgrade.
- **Sequoia -> Serval** ($150M Series C, $3B valuation) — no Form D found at all
  for Serval under any search variant. No upgrade.
- **NVIDIA -> Figure AI (candidate)** — could not confirm or rule out. No Form D
  amendment for Figure AI/Figure Technology Solutions turned up; all press as of
  Nov 2 2026 still describes the ~$1B reinvestment as "in talks"/"discussed," not
  closed. Left as `candidate`, unchanged.
- **Amazon -> Grand Ming (HK datacenters)** — this is an HKEX disclosure matter,
  not SEC; no Amazon 8-K exists or would be expected for an acquisition this size.
  No Tier-1 US-filing path available. (Noted in passing: one secondary source
  gives a slightly different price, HK$2.45bn/~$312.2M vs the corporate agent's
  $277.88M — flagging for their awareness, not correcting their row myself.)

## Part B — independent sweep (full watchlist, 8-K/Form D/13D/13G/Form 4, ~30d)

Checked Microsoft, Alphabet, MGX, Mubadala, Saudi PIF, Blue Owl, KKR, Brookfield,
Blackstone, Apollo, Goldman Sachs, Thrive Capital, Founders Fund, Coatue, and ran
a CoreWeave 13D/13G scan for watchlist names. Nothing new and inside the ~30-day
window (since ~Oct 3) survived:
- MGX's $49B Fund I close (Jul 1) and the MGX/AIP/BlackRock-GIP $40B Aligned Data
  Centers buyout (Jul 21) are both real but too old for this week.
- Apollo-led $35B Broadcom AI XPV financing is real but dated June 9 2026 — old.
- Berkshire Hathaway's $10B Alphabet private placement is real (part of
  Alphabet's $80-84.75B June 2026 raise) but Berkshire isn't a tracked allocator
  and Alphabet is the target, not the allocator, here — out of scope either way.
- CoreWeave's current 13G/13G-A filers are all passive (Vanguard, Magnetar, Jane
  Street, Goldman <5%) — none are watchlist allocators making a new allocation.
- **Rejected, not even filed as candidate**: a single low-quality aggregator
  (af.net) claims "Saudi PIF acquired Chinese AI startup DeepSeed for $2.3B" on
  2026-10-02. No independent corroboration (no Reuters/Bloomberg/PIF primary) was
  found anywhere; "DeepSeed" is suspiciously close to the well-known "DeepSeek,"
  and the source itself reads as unreliable. Per the CONTEXT.md ambiguous-entity
  guard, this was checked and dropped rather than filed as a candidate.

No new allocators discovered this run beyond what corporate already flagged
(AMD/Broadcom) — `discovered_allocators.csv` omitted.

## Bottom line
One real Tier-1 upgrade (NVIDIA-Meta, with an important amount caveat); five
other verified_alpha/candidate rows checked and left unchanged for lack of a
resolvable primary filing; independent sweep across the full watchlist turned up
nothing both new and inside the 30-day window. WebSearch (not engine.edgar, not
direct WebFetch) was the only path that worked, and even then only for
well-indexed, large-cap filings (Meta/NVIDIA) — small private-company Form Ds
stayed out of reach as resolvable primary documents.
