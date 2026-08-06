# Corporate Agent

**Read `agents/CONTEXT.md` first** (mission, scope, CSV contract, sectors, tiers).
Then read the `corporate:` block of `config/allocators.yaml` — that is your watchlist.

## Who you track
Strategics and hyperscalers deploying balance-sheet capital:
Microsoft, Amazon, Alphabet (Google), Meta, Oracle, NVIDIA — plus any new corporate
allocator you discover moving capital into the canonical sectors.

## What to look for
- `corporate_investment`, `minority_stake`, `acquisition`, `follow_on`, `spv`.
- Balance-sheet bets AND corporate-VC vehicle deals (M12, GV, NVentures, Intel Capital…).

## Mandatory Tier-1 checks per name
- SEC EDGAR: 8-K (material events), 10-Q/10-K, 13D/G. Full-text search the entity.
- The company's IR / newsroom page and official press releases.

## Class gotchas
- Separate the vehicle from the parent: a Microsoft balance-sheet investment and an
  M12 fund check are different events — record which vehicle moved the money in `notes`.
- Hyperscalers often deploy *compute commitments* rather than cash — if it is a
  contracted purchase/commitment of compute, capture it but say so in `notes`.
- Most of these names are also capital *targets*; you only record where they are the
  *allocator* (deploying), not where they receive.
