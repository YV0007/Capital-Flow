# Alt-Managers — 2026-W42 summary

## What moved this week
Four verified capital-allocation events, clustered right at the start of October 2026,
all driven by closings rather than new-fund launches:

1. **SoftBank -> OpenAI** ($10.0B, follow_on, verified): final tranche of SBVF2's
   $30B OpenAI follow-on, executed Oct 1 2026. Cumulative SoftBank stake in OpenAI
   now $64.6B / ~13%. Notably debt-funded -- SoftBank issued $11.1B of bonds on
   Sept 24 2026 specifically to cover it, so this is leveraged balance-sheet
   capital, not fund dry powder.
2. **SoftBank -> DigitalBridge** (acquisition, verified): SoftBank completed its
   take-private of DigitalBridge Group on Sept 30 2026 at $16.00/share, closing
   the loop on a deal first announced Jan 2026. DigitalBridge (one of our own
   watchlist names) is now a SoftBank-controlled subsidiary under Marc Ganzi.
   Deal value is cited inconsistently across sources (~$3.0-3.1B vs ~$4B) --
   left blank rather than guessed.
3. **Blackstone -> Falcata** (TSC + ASEI combination, acquisition, verified_alpha):
   new defense-tech interceptor-guidance platform, announced Oct 1 2026. Terms
   undisclosed; Goldman Sachs advised Blackstone on the deal. Outside the usual
   infra/datacenter lane but squarely a capital-allocation event for a key name.
4. **KKR + Singtel -> STT GDC** (acquisition, verified): KKR-led consortium closed
   its buyout of ST Telemedia's remaining 82% of STT GDC on Sept 2 2026 for
   S$6.6B (~US$5.1B cash), EV ~S$13.8B (~US$10.9B), KKR ending at 75% ownership.

## Biggest signals
- **SoftBank is the standout this run** -- two separate, large, debt-leveraged
  moves (OpenAI tranche + DigitalBridge take-private) in the same week, both
  tied to its Sept 24 bond raise. It's visibly consolidating both the AI-labs
  side (OpenAI equity) and the digital-infra manager side (DigitalBridge) of
  its own stack.
- **KKR's STT GDC close is the quietest big number** -- a ~$10.9B EV APAC
  data-center platform going fully private, financed with ~S$5B of fresh debt.
  Singtel (25% co-owner) and Temasek/ADNOC (seen partnering with GIP on a
  separate $30B Gulf/Central Asia program) are flagged to `discovered_allocators.csv`.
- **Blackstone keeping a hand in defense-tech**, not just datacenters/power --
  Falcata is its second interceptor-adjacent platform build this year.

## Checked, no new activity found (Sept 12 - Oct 12 2026 window)
Apollo, Goldman Sachs (asset-management side), Brookfield, BlackRock/GIP and
Blue Owl all had mandatory Tier-1 IR/press pages and Tier-2/3 trade press
checked, but their most relevant recent items (Apollo Aldar hybrid notes, GS
WSIP V first close, Brookfield's $100B AI program and Oaktree buyout, GIP's
sixth-flagship-fund prep, Blue Owl's Stack Melbourne loan search) all predate
Sept 12 2026 and nothing newer surfaced. Logged in `source_log.csv` as
checked-but-not-yielding rather than dropped silently.

## Watch next week
- **Blue Owl / Stack Infrastructure**: ~$5.9B Melbourne data-center loan was
  still "seeking" as of late July -- watch for a close.
- **GIP VI**: sixth flagship infra fund fundraising reportedly starting "back
  end of this year" -- watch for a first close announcement.
- **DigitalBridge under SoftBank**: now a controlled subsidiary -- future deals
  may start appearing under SoftBank rather than DigitalBridge as allocator.

## Blocked / environment notes
WebFetch could not resolve any domain this run (DNS failures on sec.gov,
businesswire.com, blackstone.com, group.softbank, even example.com), so all
sourcing here relied on WebSearch's own fetch-and-synthesize path rather than
a direct second-pass fetch of each URL. `engine.edgar filings` also failed
(proxy tunnel 403) -- only `engine.edgar exists` (local DB, no network) worked
and was used to confirm none of these four events were already on file.
