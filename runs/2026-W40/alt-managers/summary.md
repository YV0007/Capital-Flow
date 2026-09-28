# Alt-Managers — 2026-W40

## What moved
- **SoftBank agrees to buy DigitalBridge outright.** The $4B take-private (agreed Dec 2025, $16.00/share
  cash) cleared its last regulatory hurdles this week — FERC, CFIUS and antitrust all signed off as of
  2026-09-22, per DigitalBridge's own IR release, with closing expected within five business days. This
  wasn't on file for either name yet: SoftBank folds a NYSE-listed digital-infrastructure asset manager
  (data centers, towers, fiber, the ArcLight power deal in the pipe) straight into its balance sheet —
  arguably the single biggest AI-infra-buildout M&A event of the week across the whole watchlist.
- **Goldman Sachs Alternatives sole-funds a $400M extension into Cyera's Series G**, at a flat $12B
  valuation, for an AI-agent identity/data-security "trust layer." Clean Tier-1 corroboration from both
  am.gs.com and Cyera's own site.
- **SoftBank keeps buying into physical AI/robotics**: a $225M investment in Utah's Autonomous Solutions
  (ASI) plus a newly-capitalized JV for autonomous construction equipment (BusinessWire, 2026-09-24), and
  a reported (not yet officially confirmed) agreement to acquire Hyundai's Robotics and AI Institute —
  filed as a candidate since SoftBank/RAI haven't put out a joint statement and terms are undisclosed.

## Biggest signals
1. SoftBank's evident strategy this quarter is roll-up-by-acquisition into AI-adjacent infrastructure and
   robotics (DigitalBridge + ASI + RAI + the already-closed ABB Robotics deal), rather than only writing
   LP checks into third-party vehicles.
2. NVIDIA keeps stacking anchor LP commitments into alt-manager AI-infra vehicles beyond its own balance
   sheet — a reported $2B into Brookfield's ~$10B-target AI Infrastructure Fund (alongside Kuwait
   Investment Authority) surfaced via Bloomberg this week, filed as candidate pending Tier-1 confirmation
   (this session's outbound fetches to SEC/Brookfield/Bloomberg were blocked by the network egress proxy —
   flagged to re-confirm next run).
3. Private credit continues absorbing the AI capex bill: Apollo/Blackstone's Broadcom-Anthropic financing
   is reportedly scaling from $35B toward $70-100B in debt (still candidate, unclosed, already on file from
   the prior run — no new confirmation this week).

## What we checked but didn't file
KKR's new Akrapoint equipment-finance platform ($350M, 2026-09-22) and Apollo's $585M Executive Centre
financing / Bayer capital solution are real, well-sourced Tier-1 events but off-thesis (no AI/datacenter/
power nexus) — logged in source_log.csv, not filed as rows. BlackRock/GIP's Aligned Data Centers $40B deal
and the KKR-ECP $50B power/data-center partnership are both older (2025 vintage) and already reflected in
prior runs.

## Watch next week
- DigitalBridge/SoftBank closing (expected on/around 2026-09-29) — confirm via 8-K once filed.
- Whether the Brookfield/NVIDIA $2B fund commitment gets a Tier-1 filing or Brookfield PR; add Kuwait
  Investment Authority to the sovereigns watchlist (see discovered_allocators.csv).
- SoftBank/RAI — watch for an official joint announcement and disclosed deal value.
- The Broadcom debt raise (Apollo/Blackstone) for a definitive-agreement close.

## Environment note
Outbound WebFetch/HTTP to essentially all external domains (including sec.gov, bloomberg.com,
businesswire.com, bam.brookfield.com) was blocked by the network egress proxy this run; all research relied
on WebSearch's own fetch+summarize path. `python -m engine.edgar` also could not reach sec.gov directly
(same proxy block) — `exists` checks (local, no network) worked fine and were run before every row.
