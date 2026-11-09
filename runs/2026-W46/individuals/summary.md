# Individuals — Week 2026-W46 summary

## Bottom line
Zero verified and zero candidate rows this week. A deliberately broad sweep
(roughly 30 of the ~41 watchlisted individuals plus all 20 named network
members in config/networks.yaml) turned up no disclosed personal-capital
event — equity, angel round, SPV, personal fund_launch — inside the
~45-day lookback (late Sept through Nov 9, 2026) that could be sourced to
anything better than a stale or contradicted lead. This is consistent with
agents/individuals.md's own warning that this is the hardest class to
verify and that personal deals surface with lag; it does not mean nothing
moved, only that nothing surfaced yet with a citable source.

## What was checked
- **Round-announcement angel sweep (primary approach per the brief):** broad
  searches across recent (Oct–Nov 2026) AI/defense-tech funding roundups
  (aifunding.me weekly digests for Oct 19–23 and Oct 26–30) returned zero
  rounds naming any watchlist individual as an investor — every round in
  those digests lists either a VC firm or "undisclosed."
- **Per-person sweeps:** Peter Thiel, Elon Musk, Jeff Bezos, Eric Schmidt,
  Sam Altman, Elad Gil, Nat Friedman, Daniel Gross, Joe Lonsdale, Keith
  Rabois, David Sacks, Reid Hoffman, Alexandr Wang, Palmer Luckey, Trae
  Stephens, Delian Asparouhov, Lucy Guo, Max Levchin, Luke Nosek, Vinod
  Khosla, Masayoshi Son, Austin Russell, Dylan Field, Laura Deming, Patrick
  & John Collison, Garry Tan, Ali Ghodsi, Stanley Druckenmiller, Bill
  Ackman, David Tepper, Ray Dalio, Brad Gerstner, Josh Kushner, Jensen
  Huang, Larry Ellison. All turned up only (a) events older than the
  lookback window, (b) firm-level activity that belongs to the VC/corporate
  agents (e.g. Founders Fund's $6B fund close, 8VC's $1.5B Fund VII,
  Thrive Capital's $10B raise), or (c) routine executive-comp mechanics
  (Musk's June 2026 Tesla option exercise — not a discretionary allocation).
- **EDGAR deterministic path:** `engine.edgar filings` run for Thiel, Musk,
  Bezos, Schmidt, Hoffman, Khosla, Andreessen, Son, Altman — all return "no
  CIK on file, take the search path," confirming the brief's note that
  individuals rarely trigger filings directly.
- **Escalation loop run on one real lead:** Crunchbase's profile for Palmer
  Luckey lists "Pilgrim" as his latest investment dated Sept 23, 2026.
  Traced to origin and cross-checked against the primary WSJ article
  (`wsj.com/tech/ai/anthropic-leaders-back-startup-developing-system-to-
  detect-biological-threats-88ef9f0a`), Dealroom's deal record, and a
  secondary (runtimewire) writeup: all three name the round's investors as
  Buckley Ventures (lead) plus two Anthropic researchers, Logan Graham and
  Sholto Douglas, investing personally — Luckey is not named anywhere in
  the actual reporting. Graded as a refuted lead (likely a Crunchbase data
  artifact bleeding over from Pilgrim's 2025 rounds, which also did not
  include Luckey) rather than filed as a candidate, since the stronger
  sources actively contradict it. Logged in source_log.csv; not written as
  an event row for either Luckey or the two researchers (neither is on the
  watchlist and neither triggers a tracked-individual event).
- **13F/insider angle:** Thiel Macro's most recent 13F (Q2 2026, filed Aug
  14) added Amazon/Vista Energy/Vistra — outside the lookback window and,
  with Q3 2026 13Fs due ~Nov 14, too early to see this quarter's filings.
  Druckenmiller (Duquesne), Ackman (Pershing Square) and Tepper (Appaloosa)
  13F coverage in the results is all Q1–Q2 2026 vintage for the same reason.

## Network-convergence signal
None detected this week — no sector saw 3+ members of paypal_mafia,
thiel_extended or thiel_fellowship putting confirmed capital in within the
window, because no confirmed capital events were found at all for network
members.

## Newly discovered allocators
Two, both soft/exploratory (see discovered_allocators.csv): Logan Graham
and Sholto Douglas, Anthropic researchers who personally backed Pilgrim's
$25M biothreat-detection seed per WSJ. Not tied to any currently tracked
name, but worth a watch-tier add if frontier-lab researchers continue
writing personal checks into adjacent defense/biosecurity startups.

## Weak leads flagged, not confirmed
- Palmer Luckey / Pilgrim (Sept 2026) — see escalation section above;
  treated as refuted, not filed.
- Jensen Huang / "Ineffable Intelligence" $1.1B seed (reported April 2026)
  — low-quality aggregator sourcing, unclear if personal vs. NVIDIA
  corporate capital, and outside the lookback window regardless. Not
  pursued further this week; worth a primary-source check if it recurs.

## What to watch next week
- Q3 2026 13Fs land ~Nov 14 — re-check Thiel Macro, Duquesne, Pershing
  Square, Appaloosa for new AI-infra / power positions once filed.
- Re-run the round-announcement sweep with a tighter net on defense-tech
  (Anduril-adjacent, Castelion, Saronic-adjacent spinouts) where
  thiel_extended members most often cluster.
- NFDG (Friedman/Gross) appears to have gone quiet on new investments
  since both joined Meta in 2025 — worth confirming whether the vehicle is
  formally wound down or just dormant, since it's a "known_vehicle" on file
  for both.
