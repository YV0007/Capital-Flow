# Filings Agent — 2026-W39 Summary

## Environment constraint (confirmed, same as prior five agents)
`python -m engine.edgar filings ...` (data.sec.gov) and direct WebFetch to
`www.sec.gov`, `streetinsider.com`, `tryprofound.com`, `aiweekly.co` all failed
with `EGRESS_BLOCKED` / `403 Tunnel connection failed` this session — the org
egress proxy policy, confirmed as a deliberate denial per `/root/.ccr/README.md`,
not retried or routed around. `engine.edgar cik`/`exists` (local, no network)
worked fine and were used for every dedup check below. All filing-content work
this run came from WebSearch's own synthesis of indexed SEC pages and press
describing filings — never a direct fetch of a resolved document.

## What moved this week (biggest signal)
The single largest finding is not from this week's news cycle but a **major
gap-fill**: Amazon had **zero** events on file (context.json: `events_on_file: 0`,
`last_event_date: null` for every watchlist entity) despite being one of the six
corporate allocators tracked. A search for AI-related 8-Ks with Item 1.01 surfaced
Amazon's actual 8-K (CIK 1018724, filed 2026-02-27) committing up to **$50B** to
OpenAI Series C Preferred Stock via subsidiary Amazon.com NV Investment Holdings
LLC: **$15B** funded at initial close (2026-03-31) plus a **$35B** equity
commitment letter (Exhibit 10.1) that Amazon drew down early — $13.7B in Q2, the
final $21.3B after 2026-06-30, per a 2026-07-31 completion filing described
consistently by PYMNTS, The Information, GeekWire, citybiz and mediapost (not
circular — each independently describes the SEC filing, not each other). Filed as
two rows: the initial $15B leg **verified/tier-1** (WebSearch actually surfaced
and quoted 8-K/Exhibit-10.1 text — deal terms, trigger conditions, termination
date), the $35B completion leg **verified_alpha/tier-3** (press describes the
filing; this run could not resolve the completion 8-K's own URL to read it
directly — flagged in notes to re-check next run for the upgrade).

Everything else chased this run stayed exactly where the other five agents left
it — genuinely in-talks, not yet filed/closed as of 2026-09-21:
- NVIDIA–Thinking Machines Lab ($2.5B) and NVIDIA–Perplexity ($30B+) — still
  reported as discussions (The Information origin), no close, no Form D/8-K found.
- Meta–Stilla.ai — no 8-K exists for this (immaterial-size acquisition for Meta);
  Axios's scoop remains the best available source, unchanged.
- Reid Hoffman/Mark Pincus–Prentis ($100M) — still "in talks," no close.
- Blackstone Green Private Credit Fund IV ($8B target) — still fundraising,
  no first-close amount disclosed.
- Apollo–Mercor — Mercor's most recent *closed* round on record is the Oct-2025
  $350M Series C (Felicis-led); the reported $500M/$20B round Apollo may have
  joined has not shown a close or an Apollo-specific SEC 13D/13G.
- Mubadala–Ansaldo Energia — still exploratory talks per Bloomberg/Corriere della
  Sera; no CIK (Italian company, not EDGAR-registered), no signed term sheet found.

## VC agent's 18 verified_alpha rows — could not upgrade any
Ran targeted searches for Form D filings (or company-blog primary sources) for
Crusoe, Harvey, Profound, Savvy Wealth (checked SEC IAPD/Form ADV directly —
registered as an RIA but its Form ADV doesn't carry funding-round data), Mazama
Energy, and Factory. None surfaced a resolved SEC Form D or company-domain page
(WebFetch blocked for tryprofound.com and streetinsider.com specifically). This
matches the environment note's expectation: private-company Form Ds are not
well-indexed by general web search the way large-cap 8-Ks are, and are the
hardest category to confirm under this session's WebFetch block. None of the 18
rows are re-filed here (per instructions, don't re-file what you can't get past).

## What to watch next week
- Try again for the Amazon–OpenAI completion 8-K's own accession/document URL to
  upgrade that row from verified_alpha to verified.
- Re-check NVIDIA–TML and NVIDIA–Perplexity for a close; both are large enough
  ($2.5B, $30B+) to plausibly generate an 8-K or Form D once signed.
- If WebFetch to sec.gov/company domains ever opens back up, the VC agent's 18
  verified_alpha rows are the highest-value confirmation backlog — all have
  round total, date and named lead already established; only the primary
  document is missing.
