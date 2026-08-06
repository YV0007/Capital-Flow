# Sovereigns — ISO week 2026-W32 (disclosures ~2026-07-06 → 2026-08-06)

## What moved
Two clean sovereign capital-allocation events landed this cycle, plus one softer government program.

1. **MGX final-closes Fund I at $49B (2026-07-01).** Abu Dhabi's MGX (Mubadala + G42) closed its debut fund $4B above a $45B target — one of the largest dedicated AI vehicles ever raised. Capital spans the full AI stack (semiconductors → infrastructure → labs), with 14 portfolio companies already including OpenAI, Anthropic, xAI, TikTok US and Aligned Data Centers. This is the dominant sovereign signal of the week: it institutionalizes a $49B standing pool of Gulf capital pointed at the AI buildout. Recorded as `fund_launch`, mapped to `datacenters` (dominant infra theme) but flagged cross-stack. `verified_alpha` (>=3 independent Tier-3; no MGX Tier-1 PR URL captured).

2. **US Government -> GlobalFoundries, $300M CHIPS silicon-photonics award (2026-07-29).** Dept of Commerce signed a Letter of Intent for a $300M R&D grant for next-gen silicon photonics / co-packaged optics — the optical interconnect layer for AI data centers. Notably, Commerce also takes a ~1% equity stake in GF as part of the deal. Tier-1 (official GF PR + Commerce Secretary quote) -> `verified`, `grant`, sector `networking`. GF is majority-owned by Mubadala, so this is US public money reinforcing a UAE-owned foundry's US footprint.

3. **DOE nuclear-for-AI $200M program, Oklo / X-Energy tapped (2026-07-21).** A federal push to speed SMRs for AI data centers; ~two dozen companies selected, ~$60M over 3 years to national labs/universities. Per-target committed amounts not disclosed, so held as a `candidate` (`grant`, sector `nuclear`, amount_estimated=1).

## Biggest signals
- **Gulf capital is now a $49B standing fund, not a series of one-off deals** — MGX Fund I is the structural story; watch its deployment pace into named targets.
- **Washington is deploying industrial-policy capital into the AI supply chain's physical layers** — photonics (GF grant) and nuclear (DOE program) — and increasingly taking equity (GF ~1%) in exchange.

## Excluded / out of window (logged, yielded=0)
- **Humain (PIF) $3B into xAI** (Feb 2026) and **Humain–Infra $1.2B data-center financing** (Davos, Jan 2026) — real but pre-window; Humain is largely a capital *recipient* here.
- **MGX ups Anthropic pre-IPO stake** — disclosed ~2026-06-01, tied to the $65B round; outside the ~30-day window (captured indirectly by the Fund I portfolio note).
- **DOE/Brookfield Paducah $100B** and **NNSA/Amentum Savannah River** — government provides *land/site*, private capital does the building; belongs to the alt-managers class, not a sovereign capital outlay.
- **Mubadala Capital $4.65B into credit platform** and **CoolIT $4.75B exit** — non-AI-sector / divestment, out of scope.

## Confidence & coverage gaps
- Confidence: solid on the two verified rows (one Tier-1, one multi-source Tier-3). The MGX row would upgrade to `verified` with MGX's own press release (mgx.ae was un-fetchable — page too large).
- Gaps: no direct read of Saudi PIF's own newsroom or Mubadala's official news feed this cycle beyond search snippets; DOE per-company nuclear award amounts remain undisclosed. Next week: watch for MGX's first named Fund-I deployments, PIF/Humain compute-capex disclosures, and DOE AI-energy-summit follow-through converting the $200M program headline into named awards.
