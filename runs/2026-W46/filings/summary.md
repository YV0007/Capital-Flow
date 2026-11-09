# Filings — 2026-W46 summary

## Mandate this run
No fixed watchlist — swept SEC EDGAR directly to (A) confirm the six candidates
flagged by this week's class agents (VC: Khosla/Sabi, Khosla/Hertha Metals,
Coatue/Lambda, three Abby Care rows; alt-managers: Brookfield Germany pledge;
sovereigns: GlobalFoundries stake, MGX/OpenAI talks, Alpha Dhabi Holding) and
(B) independently discover any filings-only event the class agents might have
missed. Total distinct sources checked: 57 (see source_log.csv).

## Confirmed this run (candidate/verified_alpha -> verified, Tier 1)
1. **Khosla Ventures -> Hertha Metals, follow_on (Series A).** Hertha Metals,
   Inc.'s own SEC Form D (CIK 0002162096, filed 2026-10-27, first-sale-date
   2026-04-07) puts the total amount sold at $133,649,961 — matching the VC
   agent's reported figure almost exactly — and lists Rajesh Swaminathan,
   "c/o Khosla Ventures Seed E, LP," as a company director, confirming Khosla's
   seat/participation at Tier 1. A companion Form D on the same filing date
   covers an earlier ~$17.7M tranche (first-sale-date 2024-05-24), consistent
   with the VC agent's read that this is a follow-on from a returning investor,
   not a fresh Series A relationship. No per-allocator dollar slice disclosed.
2. **US Government -> GlobalFoundries, minority_stake.** GlobalFoundries' own
   press release, filed as Exhibit 99.1 to its Form 6-K (CIK 0001709048, filed
   2026-10-14, same day as the US-Japan $21B Malta/NY fab announcement), states
   directly: "the U.S. Department of Commerce will receive equity in GF of
   approximately four percent." This is a company-filed, Tier-1 confirmation of
   the ~4% new-stake fact the sovereigns agent could only source to press
   (thenationalnews.com / globaltradealert.org). It does NOT resolve the
   disputed 3%->7% baseline claim or Trump's unverified "$2bn+" valuation figure
   — both remain unconfirmed by any primary source — and no dollar amount is
   given, so amount_usd stays blank. Distinct from the already-on-file $955M
   CHIPS reallocation (id 442); this row captures only the equity-stake fact.

## Could not confirm (left as-is, not re-filed)
- **Khosla/Sabi ($50M seed, disputed lead).** Sabi (CEO Rahul Chhabra's
  brain-computer-interface startup) has no Form D on EDGAR under any name
  variant checked (Sabi Inc., SABI Mind Inc. — the latter is an unrelated
  Calgary entity). EDGAR full-text search for "Rahul Chhabra" returns zero
  relevant hits. No Tier-1 document exists yet to resolve the lead-vs-
  participant dispute.
- **Coatue/Lambda ($4B pre-IPO round).** Lambda, Inc./DE (CIK 0001954966,
  confirmed correct entity by SF address match) last filed Form D in Feb 2024.
  No new Form D, no S-1/S-1 draft, nothing on EDGAR reflecting this round —
  consistent with the VC agent's read that no capital has closed yet.
- **Abby Care (Khosla / Thrive / Sequoia, $82M Series C).** No EDGAR company
  match for "Abby Care" under any form type; full-text search returns zero
  hits. Can't confirm or deny the disputed "returning investor" participants.
- **Brookfield Germany pledge.** Checked Brookfield Asset Management Ltd.
  (CIK 1937926) and parent Brookfield Corp (CIK 1001085) 8-K/6-K filings
  bracketing the Oct 19-20 Berlin summit — none mention Germany. The pledge
  lives only in Brookfield's own PDF press release (already Tier-1 per the
  alt-managers agent); no SEC filing adds a specific number, so it stays a
  candidate on vagueness grounds, not source quality.
- **MGX/OpenAI talks, Alpha Dhabi Holding/Alpha Wave III.** OpenAI itself has
  no SEC-registered primary entity filing for this round (only unrelated SPV
  wrappers show up under "OpenAI" on EDGAR). Alpha Dhabi Holding is an
  Abu Dhabi-listed (ADX) entity outside SEC's jurisdiction — no US filing to
  check. Both remain talk-stage leads, not events.

## Independent discovery sweep (job B) — nothing new found
Checked recent 8-K/6-K/13D/13G activity (since ~2026-09-26) for every corporate
and alt-manager watchlist filer with a known CIK (Microsoft, Amazon, Alphabet,
Meta, Oracle, NVIDIA, SoftBank, Blackstone, BlackRock, DigitalBridge, Brookfield,
Goldman Sachs) — no Schedule 13D/13G stake filings by any of them in the window,
and no 8-K disclosing a capital deployment the class agents hadn't already
caught (Blackstone's filings this window were its own debt issuances, not
capital out). Also checked whether Blackstone Energy Transition Partners V (and
its parallel vehicles, CIKs 2112720/2124216/2124132) filed a Form D/A reflecting
the Oct 19 final close at $8.7B — only the original April 2026 Form D is on
file, so the alt-managers agent's verified_alpha grade (Tier 3, pending a
successful Tier-1 fetch) stands; could not upgrade it this run. Ran a broad
EDGAR full-text sweep for "Department of Commerce" + "equity" across 8-K/6-K
filers in the window hoping to catch a fresh government-equity-stake deal
beyond the ones sovereigns already found — all ~15 semiconductor/industrial
names checked individually (Intel, Marvell, Lumentum, Teradyne, Seagate, KLA,
Centrus Energy, etc.) turned out to be false positives: boilerplate
forward-looking-statement language, not a new stake. Checked Meta's three
capital-raise 8-Ks for NVIDIA/AMD by name — public-offering 8-Ks don't name
individual private-placement participants, so nothing to add beyond NVIDIA's
own (already-verified) press release.

## Watch next week
- Whether Hertha Metals' or GlobalFoundries' upgraded facts need any further
  dollar-figure resolution (per-allocator Khosla slice; GF stake dollar value).
- Re-check Blackstone Energy Transition Partners V entities for a Form D/A
  reflecting the final $8.7B close.
- Re-check EDGAR for a Lambda S-1 or new Form D if the Coatue/Blackstone round
  closes, and for an OpenAI primary-entity filing if the MGX-led round closes.
