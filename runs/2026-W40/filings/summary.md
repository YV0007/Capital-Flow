# Filings Agent — 2026-W40

## What moved
This was a confirm-heavy week: no qualifying brand-new capital-allocation event surfaced
directly from a filing that the five class agents hadn't already caught, but three real
Tier-1 documents turned up that upgrade six-week-old and two-month-old `candidate` rows to
`verified`:

1. **NVIDIA's six-way AI infrastructure financing MOUs (Apollo, BlackRock, Blackstone,
   Brookfield, Goldman Sachs, KKR).** The `fund_launch` rows dated 2026-08-11 were sitting on
   file sourced only to a Jensen Huang X/Twitter post. NVIDIA's own newsroom press release
   (nvidianews.nvidia.com, 2026-08-10) documents the same >$500B MOU program in full —
   re-filed all six as `verified`/tier 1 so downstream entity resolution can merge them with
   the already-tier-1 "AI Compute Infrastructure Financing Platform" rows from the same date
   that were filed under a slightly different target name.
2. **Apollo & Blackstone's $35B Broadcom "AI XPV Platform" financing for Anthropic's chip
   buildout.** Apollo's own investor-relations press release (2026-06-09) is the primary
   document behind the CNBC "deal scaling toward $70-100B" story both firms had on file as
   tier-3 candidates. Confirmed the $35B facility structure (chip-backed SPV, $6B+$24B notes
   backed by a Broadcom residual-value guarantee, plus a $4.5B unguaranteed tranche) at tier 1;
   left `amount_usd` blank and used `round_total_usd` for both allocator rows since neither
   firm's individual slice of the $35B is broken out (avoids the double-counting mistake
   flagged in CONTEXT.md). The CNBC-reported scale-up to $70-100B remains unconfirmed by any
   primary source found this week — not reflected in the numbers filed.
3. **NVIDIA-Hugging Face ($11.9B acquisition, 8-K filed 2026-09-03)** was checked via
   `engine.edgar exists` and found already `verified` on file since W37/W39 (sourced to
   NVIDIA's own blog) — correctly not re-filed.

## Chased, not confirmed
- **SoftBank / Robotics and AI Institute (RAI) acquisition** — still no joint press release or
  filing as of 2026-09-28; The Robot Report / Dealroom / Black Scarab all trace to one
  unconfirmed trade-press origin. Left as-is (already on file as candidate from alt-managers).
- **SoftBank / 1X Technologies** — still reported as "in talks" (~$6B valuation), no
  definitive agreement or 6-K found.
- **NVIDIA / Thinking Machines Lab** ($2.5-3B reported investment) — as of the most recent
  reporting found, still undisclosed/in-talks; the only Tier-1 NVIDIA-TML document
  (blogs.nvidia.com, March 2026) covers an earlier, separate gigawatt-compute partnership, not
  this investment figure. Not upgraded.
- **Blue Owl Data Center REIT** — still "planned" per The Real Deal (2026-09-08); no S-11 or
  other registration statement found yet.
- **DigitalBridge/SoftBank closing** — all regulatory approvals in hand as of 2026-09-22 per
  DigitalBridge's own IR release (already verified on file); close expected ~2026-09-29 but no
  closing 8-K exists yet as of this run.
- **Alphabet / MediaTek** — could not locate any SEC filing, 13D/G, or resolved press
  document corroborating a direct Alphabet-MediaTek capital investment; EDGAR full-text search
  itself is blocked in this environment (see Environment note). Left unconfirmed.

## Environment note
Direct network egress to sec.gov / data.sec.gov (and to most other external domains via
WebFetch, including nvidianews.nvidia.com and blogs.nvidia.com) was blocked by the proxy this
run, consistent with prior weeks. `python -m engine.edgar cik`/`exists` (local, no network)
worked normally and were run before every row. All source documents above were located and
their content summarized via WebSearch's own fetch path, which was not blocked, and every
`source_url` filed is a specific resolved document (company IR page, NVIDIA newsroom release,
or SEC filing URL) that WebSearch surfaced — never a bare search-query URL.

## Watch next week
- DigitalBridge/SoftBank closing 8-K (expected on/around 2026-09-29).
- Whether Broadcom/Apollo/Blackstone's Anthropic financing gets a primary-sourced scale-up
  past $35B.
- SoftBank/RAI and SoftBank/1X Technologies — watch for definitive agreements or filings.
- Re-run an EDGAR full-text sweep for Alphabet-MediaTek once/if network access to
  efts.sec.gov is available.
