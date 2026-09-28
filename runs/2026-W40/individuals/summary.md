# Individuals — 2026-W40 summary

## What moved
One new, well-sourced event this cycle: **Elad Gil** followed on into **Harvey**'s
$550M round (co-led by Diffusion and Lightspeed) at a $15.5-15.6B valuation,
disclosed 2026-09-09. Five independent outlets (Bloomberg, Unite.AI, Benzinga,
ABA Journal, TheSaaSNews) all name him among the existing investors in the
syndicate, so it's filed `verified_alpha` even without a Form D — Gil isn't
a Form D related-person type of check here, he's participating in a large
priced round alongside institutional co-investors. This pushes his on-file
last_event_date from 2026-09-07 to 2026-09-09.

## What didn't move (re-checked, not re-filed)
Chased every stale_candidate in the context pack forward through 2026-09-28
looking for a Tier-1 upgrade: Thiel/Panthalassa (already verified via a prior
PR Newswire pickup — no action needed), Thiel/Etched and Dylan Field/Etched
(still only the single TechCrunch "other backers include" line — no second
independent source found), Patrick Collison/Radical Numerics, Bezos/Flourish,
Bezos/Prometheus, Bezos/Generalist AI, Reid Hoffman/Prentis (still "in talks,"
no close confirmed), Schmidt/Gradium, Druckenmiller/Etched, and Palmer
Luckey/Erebor (the $1.5B-at-$8B raise Axios flagged 2026-08-10 is still
reported as "in talks" / "nearing" as of the latest coverage found — no outlet
has it as closed 7 weeks later). None of these got a corroborating primary
source this week, so none were re-filed (would just create churn against
existing rows) and none were upgraded.

## Biggest signals
1. **Harvey/Elad Gil** — the cleanest new personal-capital signal this class
   produced all week; a $550M legal-AI round is a large, well-covered event
   and Gil's participation is corroborated well past the circular-reporting
   threshold.
2. **The Erebor raise is the one to watch** — Palmer Luckey (personal,
   co-founder) at $8-9.5B pre/post money has been "weeks away" since early
   August; if/when it closes it should immediately confirm as `verified` (an
   OCC-chartered bank's capital raise usually generates an 8-K-adjacent
   disclosure or at minimum a hard press close, unlike a typical seed round).
3. **Coverage gap on core-tier network names with 0 events on file** —
   Alexandr Wang, Daniel Gross, Joe Lonsdale, Keith Rabois, Laura Deming, Lucy
   Guo, Luke Nosek, Nat Friedman, Roelof Botha, Trae Stephens, Austin Russell
   all show `events_on_file: 0` despite core/key tier. Swept hard for each
   this week (Crunchbase/Tracxn/PitchBook profile pages, direct name+"personal
   investment 2026" searches) and came up empty on anything datable/sourceable
   inside the 45-day window — these profile aggregators are stale/unreliable
   (dates off by a year, no primary link) and were used only to generate leads,
   never as citations. This looks like a genuine "this class rarely surfaces
   cleanly" gap rather than a search-effort gap.

## Discovered (not yet tracked)
**Andrej Karpathy** — turned up as a personal angel co-investor alongside
tracked names in two separate marquee deals this window (Etched Series C with
Thiel/Field, and Yann LeCun's AMI Labs $1.03B seed with Bezos/Schmidt/Cuban).
Recurring pattern with core/key watchlist members; filed to
discovered_allocators.csv for consideration.

## Watch next week
- Erebor close (Luckey, personal check size once disclosed).
- Harvey Series H Form D, if Diffusion/Lightspeed's co-lead triggers one
  naming Gil as a related person — would upgrade Harvey/Gil to `verified`.
- Prentis: still "in talks" as of 2026-07-24; two months on, either it closes
  (upgrade Reid Hoffman's `funding_round` candidate) or the story goes cold.
