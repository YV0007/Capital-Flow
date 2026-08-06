# Alternative Managers — ISO Week 2026-W32 (disclosures ~2026-07-06 to 2026-08-06)

**Coverage:** 5 verified/verified_alpha events, 4 candidates. Allocator class: `alt_manager`.

## What moved this week
The alt-manager balance sheet behind the AI buildout kept deploying at record scale, splitting cleanly into **equity closes** (confirmed, Tier-1) and **debt being tied up** (in-flight, candidate).

### Biggest signals
1. **BlackRock/GIP is the week's dominant allocator.** Two Tier-1 confirmed deals inside ~7 days: (a) the AIP + MGX + GIP consortium **closed the ~$40B Aligned Data Centers acquisition** (2026-07-21) — AIP's first investment, +$5B growth capital; and (b) Meta's **$14B El Paso ~1GW AI campus** where BlackRock takes **80% for ~$4.9B equity + $12.5B debt** (2026-07-28). BlackRock is now simultaneously an operator-scale owner and a debt arranger of the buildout.
2. **KKR closed its largest-ever infra fund — $19.2B Global Infrastructure Investors V** (2026-08-03, Tier-1). Already >$9B committed incl. Gulf Data Hub and Global Technical Realty (data centers) plus power (EDF, Sempra). Fresh dry powder aimed at digital/energy infra.
3. **The debt binge is visible in real time.** Three separate ~$3–5.9B data-center loans were being *tied up / marketed* in-window — Blackstone AirTrunk SYD3 (~US$3B), Blackstone/QTS–Microsoft ($5.4B, Goldman pitching), Blue Owl/Stack ($5.9B). All logged as candidates because none had closed; together they signal the financing layer is straining but still clearing.

### Committed vs. target (per brief)
- **Committed / closed:** Aligned ($40B EV), Meta El Paso (BlackRock $4.9B equity), KKR Fund V ($19.2B final close). `amount_estimated=0`.
- **Program targets, not single closes:** Brookfield–Bloom Energy on-site power "up to $25B" (`amount_estimated=1`); AirTrunk A$4.3B loan is a press estimate (`amount_estimated=1`).
- **SoftBank** in-window activity was the **$40B OpenAI bridge-loan syndication** (21 new lenders, ~$7B allocated, 2026-07-27) — the *debt behind* an already-committed equity stake, marked `verified_alpha` (Tier-3 only).

## Confidence & limitations
Confidence is **high on the verified rows** (all Tier-1 fund/company PRs, cross-checked). The candidate loans rest on Tier-3 (Bloomberg) reporting of deals still being arranged — directionally reliable, amounts approximate. The Brookfield–Bloom $25B expansion disclosed 2026-06-30 sits ~5 weeks back, marginally outside the 30-day window; included for buildout weight and flagged. SEC EDGAR full-text was not directly queried this run (Tier-1 PRs sufficed); worth a confirming pass on the BAM 8-K and any BX/OWL 8-Ks next week.

## Coverage gaps / watch next week
- **DigitalBridge:** no clean in-window capital deployment found; the firm is mid-acquisition by SoftBank (~$4B, expected 2H26 close) and comparatively quiet. Watch for the SoftBank deal close and any Switch/Vantage/DataBank raises.
- **Watch the three in-flight loans** (AirTrunk, QTS/Microsoft, Stack) to convert candidate → verified once priced/closed.
- **SoftBank** direct equity into OpenAI/Stargate vehicles (vs. loan mechanics) and any new Stargate SPV.
- **Brookfield BAIIF / Radiant** deployments and the NAVER–NVIDIA Korea sovereign-AI expansion (proposed; no firm Brookfield $ yet, so not recorded).
