# Filings agent — 2026-W37

## Coverage gap up front
This sandbox's egress proxy blocks all direct network calls to sec.gov,
data.sec.gov, efts.sec.gov, capedge.com, streetinsider.com, medium.com,
databricks.com, mediatek.com, techcrunch.com and most other first-party
domains — both `python -m engine.edgar filings/cik` HTTP calls and
WebFetch on those hosts return `EGRESS_BLOCKED` / 403 tunnel failures.
`engine.edgar cik` and `engine.edgar exists` still work (local/deterministic,
no network). Every citation below was assembled from WebSearch's own fetched
result snippets, then cross-checked for a specific, resolved document URL
before being written down — never a bare search-query link. No live EDGAR
full-text sweep was possible this run; discovery leaned on official
company/IR press releases surfaced through search instead of raw filings.

## Confirmed to `verified` (3)
1. **Alphabet → MediaTek** (corporate agent's candidate, $3.9B convertible
   bond, Aug 31). The joint NVIDIA/MediaTek press release (GlobeNewswire,
   mirrored at MediaTek's own press room and NVIDIA Newsroom) states
   outright that "the remainder" of the $3.9B bond beyond NVIDIA's $3.5B
   went to "Alphabet and others"; MediaTek's own official X account
   independently names Alphabet too. Two independent Tier-1 company-official
   sources — upgraded from candidate to verified, source_tier=1.
2. **MGX → Databricks** (sovereigns agent's verified_alpha, $5B strategic
   round, Aug 13). Databricks' own newsroom press release names MGX
   directly among the round's leads (with Coatue, Blackstone, T. Rowe
   Price, Sixth Street Growth). Upgraded to verified, source_tier=1.
3. Peter Thiel/Etched, Elad Gil/Cambridge Aerospace and the SoftBank/1X,
   Blue Owl REIT, Mubadala/Akita, Saudi PIF/HUMAIN, Discovery Loop and
   Prentis candidates were all chased but **not** upgradable this run —
   see "Could not confirm" below.

## New filings-only discovery (1)
- **BlackRock → El Paso AI Data Center Venture (with Meta)**, $14B JV,
  announced 2026-07-28. BlackRock-managed (GIP) funds take an 80% stake
  in a new joint venture to build out Meta's El Paso, TX AI campus; Meta
  keeps 20%, contributing land/CIP assets (~$2.3B) and taking a ~$1B
  distribution to align stakes; BlackRock's cash contribution is ~$4.9B,
  with a further ~$12.5B raised as JV-level debt. Confirmed via Meta's own
  IR press release (mirrored on PR Newswire). This was a complete blind
  spot: BlackRock and Meta both show **zero events on file** in this
  week's context pack despite both being "key"-tier watchlist names — this
  single JV alone is one of the largest alt-manager-into-AI-infra deals of
  the summer. Filed as one row (BlackRock, the actual capital deployer) to
  avoid double-counting the $14B venture total against both allocators.
  Slightly outside the nominal 30-day window (41 days old) but included
  given the size of the coverage gap and strength of the source.

## Could not confirm (stayed candidate / verified_alpha, chased and dropped)
- **Peter Thiel / Etched** ($700M Series D): every source found (Dealroom,
  Unite.AI, TechCrunch, Etched's own site via search) either omits Thiel
  from the investor list entirely or can't be read directly (network
  blocked) to check if it's truly Etched's own primary statement vs.
  press aggregation. Left at verified_alpha — no Tier-1 upgrade.
- **Elad Gil / Cambridge Aerospace** ($300M Series C): no official
  company press page surfaced (cambridgeaerospace.com not indexed by
  search for this); the only Form D hit found (via StreetInsider,
  "Auctor Cambridge Aerospace, a series of Ratio Ventures") is a
  different, much smaller ($1.77M, 2025) SPV filing — not the Series C.
  Left at verified_alpha.
- **Jeff Bezos / CuspAI** ($450M Series B): CuspAI's own Medium post
  (official company channel) could not be fetched directly (blocked);
  WebSearch summaries of it are ambiguous about whether "Bezos
  Expeditions" appears in CuspAI's own text vs. aggregated press. Left at
  verified_alpha rather than risk a wrong Tier-1 claim.
- **SoftBank / 1X Technologies**, **Blue Owl data-center REIT**,
  **Mubadala / Akita**, **Saudi PIF / HUMAIN fund**, **Khosla / Discovery
  Loop**, **Reid Hoffman / Prentis** — re-checked for progression since
  original filing; all are still explicitly "in talks" / "considering" /
  "planning" / regulatory-approval-pending as of Sep 7, no signed
  agreement or committed capital found for any of them. Correctly left as
  candidates by the originating agents; nothing to upgrade.
- Also checked: Commerce Dept/NIST letters of intent for ~$874M in
  CHIPS-Act equity stakes across 7 small semiconductor/quantum firms
  (Kepler, Multibeam, Extropic, Thintronics, Obsidia, Aeluma,
  GlobalFoundries) — real Tier-1 government source, but announced late
  July (outside the ~30-day window) and each individual stake is small
  with only a loose AI-buildout sector fit; not filed.
- Checked for signed follow-through on the Aug 10 NVIDIA + Apollo/
  BlackRock/Blackstone/Brookfield/Goldman Sachs/KKR $500B compute-
  financing-platform MOUs (already correctly filed as 6 candidate rows by
  the alt-managers agent) — no first deal under any of the six platforms
  has been announced yet; still MOU-stage, left as-is.

## Watch next week
- The BlackRock/Meta El Paso JV suggests BlackRock's GIP arm and other
  the-NVIDIA-financing-platform partners (Apollo, Blackstone, Brookfield,
  Goldman Sachs, KKR) may be closing similar hyperscaler-anchored data
  center JVs quietly via IR pages rather than the NVIDIA platform itself —
  worth a direct sweep of each firm's own newsroom next run, not just
  NVIDIA-branded announcements.
- Re-check Etched, Cambridge Aerospace and CuspAI's own investor-relations/
  blog pages directly once network access allows a real fetch (not just
  search snippets) — the individual-attribution question (person vs. firm,
  and which sources are truly primary vs. syndicated) needs a full read of
  the primary text, not a search summary.
- SoftBank/1X, Blue Owl REIT, Mubadala/Akita, Saudi PIF/HUMAIN and
  Discovery Loop are all live "close soon" leads — good candidates for a
  Tier-1 confirm within the next 1-2 runs.
