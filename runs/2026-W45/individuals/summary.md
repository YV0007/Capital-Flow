# Individuals — 2026-W45 summary

## What moved this week
Nothing met the bar for `verified`, `verified_alpha`, or even a well-dated
`candidate` row this run. ~40 searches across the full watchlist (key-tier
Silicon Valley investors, PayPal Mafia / Thiel-extended / Thiel Fellowship
network cores, founder-investors, and macro names) turned up almost no
personal-capital news dated inside the ~45-day window (2026-09-18 to
2026-11-02). The large majority of what surfaces for these names is either:
- old news re-dated by SEO/aggregator sites (Jan–Aug 2026 rounds re-served
  with a 2026 timestamp banner),
- firm-level activity that belongs to the VC or corporate agent (e.g. Craft
  Ventures' $1B Fund V filing, Coatue's new tech fund, Altimeter Form Ds),
  or
- unconfirmed "in talks" reporting with no closed capital (Blue Origin's
  reported $10B outside round with a ~$2B personal Bezos commitment; Thinking
  Machines Lab's reported $5–6B round; Mercor's reported $20B round; a new
  SSI round) — per CONTEXT.md scope, talk-stage rounds aren't events until
  money is committed, so none were filed even as `candidate`.

No EDGAR confirms were possible this run: `python -m engine.edgar filings`
failed in this container with a proxy tunnel 403 against `data.sec.gov` (and
direct `curl`/`WebFetch` to sec.gov are blocked the same way), so the Tier-1
Form D related-person path this class leans on (per `agents/individuals.md`)
was unavailable end-to-end. `cik` lookups only resolve for entities already
seeded in the local alias table (works for NVIDIA; returns null for every
personal/vehicle name tried: Thiel, Founders Fund, 8VC, Craft Ventures, NFDG,
Mithril, Hydrazine, Greylock, Khosla Ventures, Bezos Expeditions).

## Near-miss leads (NOT filed — outside window or unconfirmed, logged for
context only)
- **Jeff Bezos / Blue Origin**: reported July 8 2026 that Blue Origin is
  raising ~$10B at a $130B pre-money, Coatue leading ~$4B, Bezos adding ~$2B
  personally — still unconfirmed as closed per a July 10 follow-up, and well
  outside the window regardless. Worth rechecking for a close announcement.
- **Peter Thiel / Stark Defence**: Thiel Capital (sub-10% stake) in a €500M
  round led by Sequoia + Founders Fund — closed June 2026, outside window.
- **Eric Schmidt / Bill Ackman — Kela Technologies**: $200M round at ~$1.2B,
  both as new investors — closed ~May 6 2026, outside window. An Oct 26 2026
  Ackman comment piece about Kela is commentary, not a new capital event.
  Reid Hoffman / Manas AI ($24.6M, cancer-research AI) is dated to mid-May
  2026 reporting, also outside window and with investor participants
  undisclosed.
- **Daniel Gross / Nat Friedman**: still inactive for *new* NFDG checks per
  every source found — Meta's buyout of NFDG and the two joining Meta
  (Gross now described as co-leading "Meta Compute") dates to mid-2025;
  nothing suggests fresh personal angel activity since.

## What to watch next week
- Blue Origin's outside round (Bezos's personal $2B slice) closing —
  highest-confidence upcoming event for this class.
- Thinking Machines Lab's ~$5–6B round and Mercor's ~$20B round, if either
  closes with a named personal check from a watchlist individual (Thiel,
  Gil, Friedman/Gross have been named in earlier rounds of both).
  Also worth rechecking Fei-Fei Li's World Labs and a potential SSI follow-on.
- Fix the EDGAR network path (data.sec.gov is proxy-blocked in this
  container) so Form D related-person pulls — this class's best Tier-1
  confirm per `agents/individuals.md` — are actually reachable next run.

## Bottom line
Zero rows this week is the honest read, not a coverage gap: this is
consistent with `agents/individuals.md`'s own framing of this class as the
hardest to verify, and the brief's preference for a few solid rows over many
shaky ones. Every watchlist entity's `last_event_date` was already null
going in (no prior events on file for any of the ~26 entities in
context.json), so there was no stale-candidate backlog to chase either.
