# VC Agent

**Read `agents/CONTEXT.md` first.** Then read the `vc:` block of
`config/allocators.yaml` — your watchlist.

## Who you track
Sequoia, Andreessen Horowitz (a16z), Thrive Capital, Founders Fund, Khosla Ventures,
Coatue, Altimeter — plus new venture allocators discovered leading AI-buildout rounds.

## What to look for
- `funding_round`, `follow_on`, `fund_launch`, `spv`, `equity`, `minority_stake`.
- New fund closes are events: `event_type: fund_launch`, `amount_usd` = fund size.

## Mandatory checks per name
- The firm's portfolio / news page (Tier 1 when it lists the deal).
- Tier 2: Crunchbase, Dealroom, PitchBook for round detail and participants.
- Tier 3 press (Reuters/FT/The Information) for rounds not yet on platforms.

## Class gotchas
- Participation ≠ leading. Record lead vs. participant, and round stage, in `notes`.
- A single round often has many watchlist VCs — record one event per allocator so the
  sector_swarm signal counts distinct investors correctly.
- Tier 2 is usually the confirm here; upgrade to `verified` only with a Tier-1 portfolio
  page or official PR.
