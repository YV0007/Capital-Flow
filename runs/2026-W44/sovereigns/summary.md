# Sovereigns — Week 2026-W44

## Headline
No sovereign allocator in this class (MGX, Mubadala, Saudi PIF, US Government) made a
*brand-new* disclosed capital commitment inside the strict 30-day window (26 Sep –
26 Oct 2026). The one event that lands squarely in-window is a US Government CHIPS
grant reallocation. Everything else genuinely new this week was either a recap of
already-announced deals (MGX's own board confirming prior rounds) or an unconfirmed
press lead. Rather than force recency, this run reaches back to the most recent
*actually disclosed* events (mid-Jul through mid-Oct) since the engine has zero
sovereign events on file (last_event_date: null for all three key names) — every row
below is clearly dated so staleness is visible, not hidden.

## Biggest signals
1. **US Government is the most active disclosed allocator this cycle, not the Gulf
   funds.** Three real, Tier-1-sourced actions in six weeks: a $1.9B DOE loan to
   restart NextEra's Duane Arnold nuclear plant for Google's AI load (8 Sep), a
   finalized $1B CHIPS R&D award to IBM's new Anderon quantum-foundry subsidiary
   (16 Sep), and — the only event inside the 30-day window — a $955M CHIPS award
   amendment steering GlobalFoundries toward silicon photonics/advanced packaging
   for AI datacenter networking (14 Oct, GlobalFoundries matching with a $5B capital
   commitment). Power and chips, not direct equity, is where US sovereign capital is
   visibly moving.
2. **MGX's $49B Fund I (closed 1 Jul) is still the dominant vehicle and the one
   structural fact this class is missing from its records** — it is the capital base
   behind MGX's Anthropic, OpenAI, xAI and Databricks stakes, confirmed again at its
   19 Oct board meeting (official UAE/WAM coverage). Recommend treating this as the
   priority backfill: `known_vehicles` for MGX is currently empty.
3. **Three large Gulf/Saudi commitments are all still non-binding or "in talks,"** not
   events: MGX weighing a takeover of Singapore's DayOne (unchanged since June), MGX
   /Mubadala weighing a ~$6.3–12.6B AI data center in Akita, Japan, and HUMAIN's
   (PIF) ~$5.3B Riyadh data-center financing via Goldman Sachs. All three are filed
   as candidates with amount_estimated=1; none should be read as committed capital
   yet.

## What to watch next week
- Whether Commerce/NIST issues a primary release distinguishing the $955M GlobalFoundries
  reallocation from the separate $300M photonics LOI (1% equity stake) — currently
  ambiguous across secondary sources.
- A DOE-primary confirmation (or denial) of the $200M Oklo/X-Energy/Microsoft/Nvidia
  nuclear-AI program — X-Energy's own release lists different partners (INL/Nvidia/AWS)
  than the Bloomberg report that started this lead.
- Progress (or collapse) of the MGX–DayOne talks and the Mubadala/Akita data center —
  both are the kind of deal that can convert from candidate to verified with one press
  release.
- HUMAIN/PIF: whether the Goldman-advised ~SAR20bn financing or the BSF Capital-managed
  $2.5B fund actually closes; also whether the Oct 2025 Aramco–HUMAIN minority-stake
  term sheet has moved to a definitive agreement (still non-binding as of the latest
  reporting found).

## Coverage note
verified_events.csv: 5 rows. candidate_events.csv: 4 rows. discovered_allocators.csv:
2 rows (Saudi National Infrastructure Fund / "Infra", and BSF Capital). No fabricated
amounts or URLs — every source_url is a resolved article or official government page
actually consulted (via WebSearch; WebFetch was unavailable in this environment for
direct verification, so figures rely on cross-checking multiple independent outlets
per claim per the escalation loop in agents/CONTEXT.md).
