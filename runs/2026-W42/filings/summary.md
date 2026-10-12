# Filings agent — 2026-W42 — summary

## Degraded run: EDGAR/HTTPS blocked
Confirmed by direct testing before this run started: outbound HTTPS via WebFetch and
direct `engine.edgar` network calls (data.sec.gov) are blocked 403 by this session's
egress proxy, identically across sec.gov, efts.sec.gov, data.sec.gov, and general news
domains. This is a session-wide policy block, not a bug and not domain-specific — no
amount of retrying changes it. `engine.edgar exists` and `engine.edgar cik` (local
SQLite, no network) worked fine throughout. WebSearch was the only usable discovery
tool this run; its citations are resolved article/document URLs even though the
underlying raw-filing fetch path is blocked.

Given this, every finding below is WebSearch-sourced secondary confirmation (or
disconfirmation), **not** a raw EDGAR filing read. No row in this run's CSVs is
marked `verified` on the strength of a filing we actually opened ourselves this week.

## Five flagged candidate leads — all remain unresolved, none touched
Ran the escalation/confirm search for each. No SEC filing (8-K/13D/G/Form 4/Form D)
or unambiguous official primary source was found for any of them — all five are still
at the same "talks" / "reported" / "fundraising target" stage their originating agent
left them at, sometimes with newer-dated secondary reporting repeating the same
unconfirmed figures with no close:
- **NVIDIA → Figure AI (~$1B):** still "discussed/considered," no deal terms, no company
  confirmation. Original candidate row left as-is (corporate agent's file).
- **NVIDIA → Thinking Machines Lab (~$2.5B):** still "in talks," no closing reported, no
  October follow-up. Left as-is (corporate agent's file).
- **Altimeter → Thrive Holdings (~$2B):** no Form D or wire naming Altimeter;
  investor-list conflicts persist across outlets. Left as-is (vc agent's file).
- **Mubadala → Akita AI Data Center JV (~$6.3B):** still "considering"/"in talks" per
  every source found, including the most recent (Aug 2026); no newer signing found.
  Left as-is (sovereigns agent's file).
- **Saudi PIF/HUMAIN → $2.5B data-center fund:** still a fundraising target pending
  Capital Market Authority approval, not committed capital. Left as-is (sovereigns
  agent's file).

Per instructions, since none resolved to a citable filing or primary source, none of
these rows were re-emitted here — they stay exactly as their originating agents filed
them.

## New events discovered this run: 0
Swept broadly across all five allocator classes for filings-driven events in the last
~30 days (8-K, Form D, 13D/G, Form 4, S-1) via WebSearch. Nothing surfaced that was both
(a) inside the lookback window, (b) backed by a real resolved source_url, and (c) not
already on file. Notable non-events found and checked against the local DB with
`engine.edgar exists` before being discarded as not-new:
- **SoftBank → OpenAI, final $10B tranche (Oct 1, 2026):** real, dated, well-sourced —
  but already on file as `verified`, run_week 2026-W41 (id 369), via SoftBank's own PR.
  No action needed.
- **xAI Series E ($20B, Jan 2026)** and **NVIDIA → CoreWeave ($2B private placement,
  Jan 2026 8-K)**: both real SEC-filing-backed events but well outside the 30-day
  lookback and almost certainly already captured in earlier runs.
- SoftBank's reported $100B Gulf-investor fundraising push (Oct 9, 2026 FT/Reuters) is a
  fundraising *target*, not committed capital — correctly out of scope per CONTEXT.md.
- No new Form D, 13D/G, or 8-K specifically naming an AI-compute/datacenter capital
  allocation inside the window turned up in any of ~15 targeted sweeps (corporate 8-Ks,
  Form D AI-startup raises, 13G sovereign stakes in semis/AI names, Form 4 insider buys
  at chip/power names, Anthropic/Amazon, DOE nuclear loans, SPV project-finance Form Ds).

## What to watch next week
- Re-check the five flagged leads again — Thinking Machines Lab and Thrive Holdings in
  particular are active, material, and could close any week.
- Re-run this sweep with real EDGAR full-text search once network access is restored;
  this week's WebSearch-only pass is a materially weaker substitute and likely missed
  filings that don't get press pickup (Form D amendments, smaller 13D/G stakes).

## Files
- `verified_events.csv`, `candidate_events.csv` — header-only, 0 rows (nothing met the
  bar for a new row this run).
- `source_log.csv` — ~36 sources checked, 2 yielded (SoftBank/OpenAI completion piece,
  CoreWeave/NVIDIA 8-K) but both were duplicates of events already on file, not new rows.
- No `discovered_allocators.csv` — no new, not-yet-tracked allocator was seen
  co-investing with a tracked name this run.
