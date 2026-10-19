# Filings agent — 2026-W43

## Network constraint (read this first)
`python -m engine.edgar filings ...` failed on every call this run: `Tunnel
connection failed: 403` connecting to `data.sec.gov`. WebFetch and raw `curl`
were both completely blocked for this session — not just sec.gov, but every
external host tested (`efts.sec.gov`, `formds.com`, `bullfincher.io`,
`sec.report`, even `en.wikipedia.org` and `reuters.com` failed DNS/CONNECT
through the agent proxy). The only working channel was `WebSearch`, which
returns synthesized snippets, not documents I can independently open and
read. The local, non-network parts of `engine.edgar` (`cik`, `exists`) worked
fine and were used throughout.

Given that, I did not manufacture `verified` status for anything this week —
doing so would mean citing a filing I never actually read. Per the run brief,
this run is "thin by design" rather than papering over the gap.

## Confirm pass — this week's 6 candidates (5 agents)
Checked all six candidate rows from corporate / vc / individuals /
alt-managers / sovereigns against `engine.edgar exists` and WebSearch. None
could be honestly upgraded:

- **NVIDIA — unnamed European targets** (corporate): no target is named yet
  (Huang's forward guidance only), so there's nothing to look up.
- **Elad Gil — Applied Compute** (individuals): confirmed via WebSearch that
  Applied Compute raised $80M led by Kleiner Perkins (Latham & Watkins
  release names Gil as a participant) — but individual angel checks like
  this are not required "related persons" on a Form D, so no SEC filing
  would name Gil even if found. `engine.edgar exists` → false.
- **Elad Gil — Cognition** (individuals): no Form D found at all for
  Cognition under either name; same related-person limitation applies even
  if one existed. `exists` → false.
- **Jeff Bezos — Generalist AI** (individuals): **already on file** at a
  stronger grade than this week's candidate — id 38, `verified_alpha`,
  `source_tier 1`, citing Generalist AI's actual Form D
  (`sec.gov/Archives/edgar/data/2137708/000213770826000003/primary_doc.xml`).
  That filing doesn't name Bezos as a related person either (it's capped at
  `verified_alpha` for exactly that reason), so there is no new evidence to
  push it to full `verified`. Re-filing this week's weaker row would just add
  churn — left as-is; the engine will keep the stronger existing record.
- **Blue Owl — Stack Infrastructure MEL02 (Melbourne)** (alt-managers): this
  is a private syndicated bank loan (A$8.6B / ~$6B), not a Reg D securities
  offering — structurally there is no Form D/8-K to find. Blue Owl Capital
  Corp's (OBDC) own 10-Q unfunded-commitment table doesn't mention Stack
  either. `exists` → false. Left as-is.
- **Saudi PIF — HUMAIN** (sovereigns): HUMAIN/BSF Capital is a Saudi vehicle
  still awaiting CMA approval — no US SEC filing exists or would exist.
  `exists` → false. Left as-is.

## Discover pass
Swept recent activity (trailing ~30 days) for the key/watch allocators in the
context pack via WebSearch: NVIDIA (13D/G, Form 4), Oracle (0 events on file
— still nothing found), Blue Owl, Microsoft (Form D / M12), SoftBank/OpenAI,
Brookfield/BAIIF, KKR, BlackRock/GIP. Three leads turned out to be real but
**already captured** in the DB at the right grade:
- SoftBank's Oct 1 2026 third $10B OpenAI tranche → already id 369, verified.
- Brookfield AI Infrastructure Fund (BAIIF) → already id 373, verified.
- KKR / SK Horizon → already id 240, verified.

No genuinely new filings-sourced event turned up beyond what's on file.
Oracle remains at zero events — nothing filing-worthy found (its $90-95B
FY27 capex guidance is forward commentary, not a committed capital event).

## What to watch next week
- Re-attempt direct EDGAR/WebFetch access once the proxy issue clears —
  several leads here (Stack/Melbourne loan pricing, the HUMAIN CMA approval,
  Nvidia's "~$2B more Europe" follow-up) are close to a real filing or PR and
  worth a second pass with working network tools.
- If EDGAR access returns, specifically re-check Form D amendments for
  Generalist AI and Applied Compute — an amendment sometimes adds named
  investors that the original filing omitted.
