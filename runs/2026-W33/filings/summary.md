# Public Filings Agent — 2026-W33 Summary

## Environment constraint (read first)
This run's network egress gateway returned `EGRESS_BLOCKED` for every direct WebFetch/curl
attempt this session — including `sec.gov`, `efts.sec.gov`, `www.war.gov`, and
`www.anthropic.com` (all tested directly). All findings below rest on WebSearch's indexed
retrieval of primary-source text, not a direct page load by this agent. Per this run's
operating instructions, primary text surfaced this way is treated as best-available Tier-1
evidence and graded accordingly, with the caveat noted on every row.

## Job 2 — confirming the other five agents' candidates
Reviewed all five `candidate_events.csv` files. Ran the escalation loop (find the dedicated
primary, not just the aggregate/secondary write-up) on each:

1. **CONFIRMED / UPGRADED — US Government -> Strategic Bauxite USA, LLC ($85.5M, sovereign).**
   The sovereigns agent had only the aggregate White House fact sheet and explicitly flagged
   that no dedicated war.gov release could be found. This run located the dedicated Department
   of War primary release and re-emits the row as `verified`, `source_tier=1`. Two corrections
   surfaced in the process: the entity is "Strategic Bauxite USA, LLC (SBX)", not "Standard
   Bauxite" (a garbled name in the fact sheet), and the instrument is an **equity** investment
   via the Industrial Base Analysis and Sustainment (IBAS) program — not a loan like the Sila /
   Sunrise / Niron rows filed the same day via the separate Office of Strategic Capital vehicle.
   Amount is now exact ($85.5M, DoW side; $150M with the $64.5M private co-investment) rather
   than "over $85 million."
2. **NOT CONFIRMED — NVIDIA -> Lancium ($2-3B, corporate).** No NVIDIA or Lancium statement,
   no 8-K, no press release found anywhere. Every result traces to the same single Information
   scoop the corporate agent already flagged. Left as-is; not re-emitted.
3. **NOT CONFIRMED — Sequoia -> Anthropic ($10B cumulative, vc).** Found Anthropic's own
   official Series H press release (anthropic.com/news/series-h), which does name Sequoia as
   one of the round's leads — but that confirms Sequoia's participation in the $65B Series H
   itself (closed 2026-05-28, already outside this window per the vc agent's own note), not the
   specific "~$10B cumulative" aggregate figure, which remains a single-origin Bloomberg number
   with no primary behind it. Not re-emitted; the underlying claim being graded is the
   aggregate, which still isn't a filing-verifiable fact.
4. **NOT CONFIRMED — Jeff Bezos -> Generalist AI (follow-on top-up, individual).** No source
   found beyond the same Bloomberg family-office piece the individuals agent already used; no
   new check size, date, or SEC/Form D signal located.
5. **NOT CONFIRMED — Blue Owl -> Meta Hyperion ($50B scale-up, alt_manager).** No SEC filing or
   Blue Owl statement found sizing a new capital raise to the 5GW/$50B scope. Additional detail
   surfaced ($7bn Blue Owl cash contribution, $3bn one-time Meta distribution, PIMCO bond
   financing) belongs to the original Oct-2025 $27bn JV, not a new tranche for this window — not
   a material upgrade, not re-emitted.

## Job 1 — discovery sweep
Swept broadly for 8-K, 13D/G, Form 4, Form D, and S-1 activity across all five allocator
classes and the corporate/alt-manager/sovereign names not fully covered this window
(Microsoft, Amazon, Oracle, SoftBank, QIA/ADIA/GIC/Temasek, Apollo/Ares/Fortress, Thiel/
Founders Fund, Musk/xAI). Nothing cleared the bar for a new verified or candidate row:
several leads were either stale (>30 days, e.g. Meta's $9.17B Alberta data center, announced
2026-07-06/08, and itself a self-build with no external capital partner rather than a clean
allocator->target flow), still at the "in talks" stage (SoftBank/7-Eleven, Founders Fund's
possible new Anduril round), off-canonical-sector with only secondary sourcing, or simple
duplicates of deals the other five agents already logged. No new allocators were identified
this run — nothing recorded in `discovered_allocators.csv` (file omitted).

## Totals this run
- verified_events.csv: 1 row (US Government / Strategic Bauxite USA — a confirmed upgrade of
  the sovereigns agent's candidate)
- candidate_events.csv: 0 rows (header only)
- Confirmed to verified: 1 of 5 candidates reviewed (Standard/Strategic Bauxite)
- New standalone discoveries: 0

## Watch next week
- NVIDIA/Lancium: watch for an NVIDIA 8-K, a Lancium press release, or NVIDIA's next 10-Q.
- Sequoia/Anthropic: watch for a Sequoia-side confirmation of the ~$10B cumulative figure, or
  an Anthropic S-1 (IPO reportedly being weighed) that would itemize major shareholders.
- Blue Owl/Meta Hyperion: watch for a follow-on JV recapitalization or new SPV bond issue sized
  to the $50B/5GW scope.
- Re-test WebFetch access to sec.gov/war.gov/anthropic.com next run — if the egress block
  lifts, several of this week's `verified_alpha` rows across other agents (Blue Origin,
  Moove, MOZN, the OSC loans) could be re-verified against their raw primary text directly.
