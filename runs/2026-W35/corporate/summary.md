# Corporate Agent — Week 2026-W35 Summary

## Environment note
Both the deterministic path (`python -m engine.edgar` -> data.sec.gov) and the
WebFetch tool were blocked all run by the session's egress proxy (403 policy
denial on data.sec.gov; WebFetch returned EGRESS_BLOCKED on every domain
tried, including sec.gov, businesswire.com, prnewswire.com, cnbc.com, and even
en.wikipedia.org). Research this week relied entirely on WebSearch, citing the
specific resolved article/press-release URLs it surfaced rather than a
raw filing pull. `engine.edgar exists` (local, no network) still worked and
was used to confirm no duplicate rows before filing. Flag for the operator:
EDGAR/WebFetch access needs to be restored for future corporate runs to reach
primary filings directly.

## What moved this week
Five verified balance-sheet/CVC events across four of six watchlist names,
all in the last ~4 weeks:

- **Meta x BlackRock** — new $14B strategic venture to build a 1GW AI data
  center campus in El Paso, TX (online 2028, Meta sole tenant). BlackRock/GIP
  funds 80% (~$4.9B cash + $12.5B debt); Meta keeps 20%, contributing ~$2.3B
  of land/construction assets against a ~$1B cash distribution to balance
  stakes. (2026-07-28, verified, Tier 1 — Meta's own press release.)
- **NVIDIA x Poolside** — a $1B minority equity check at a $12B pre-money
  valuation, bundled with a separate $6B non-exclusive license of Poolside's
  "Model Factory" and an acquihire of 109 staff. Structured explicitly to
  avoid acquisition-style antitrust review — only the $1B equity slice is
  filed as a capital-allocation event. (2026-08-20, verified_alpha — Bloomberg
  + The Information both independently confirmed the Newcomer-origin leak.)
- **NVIDIA (NVentures) x Point2 Technology** — follow-on participation in a
  $136M Series B extension for an AI-datacenter RF-interconnect chipmaker,
  alongside new entrant Arm. (2026-08-10, verified, Tier 1 company release.)
- **Alphabet (GV) x Blacksmith** — follow-on into a $45M Series B (led by
  Peak XV) for an AI-code-validation/CI cloud; GV was the 2025 seed backer.
  (2026-08-12, verified, Tier 1 company blog.)
- **Microsoft (M12) x Mate Security** — participation in a $35M Series A
  (led by Canaan Partners) for an agentic-SOC/AI-security-operations startup.
  (2026-07-28, verified_alpha — SecurityWeek + Calcalist Tech independently
  confirmed.)

No candidate (unconfirmed) leads were strong enough to file this week — every
lead chased either resolved to a confirmable source or was outside the
~30-day window (notably Amazon's $25B Anthropic tranche, Microsoft's $5B
Anthropic stake, and Alphabet/GV's Proxima Fusion round all predate the
window and are presumably already on file or out of scope for this run).

Amazon and Oracle produced no confirmed new allocator-side events this
window — both were highly active as capital *targets*/spenders (Oracle's
CY2026 $45-50B financing plan, Amazon's up-to-$50B GovCloud buildout,
Amazon-Oracle's AWS/Exadata cloud partnership) rather than as deployers of
capital into third parties, which is out of scope for this agent.

## Discovered allocators
Three untracked co-investors flagged in `discovered_allocators.csv`: **Arm**
(corporate — co-invested alongside NVentures in Point2), **Peak XV Partners**
(vc — led the Blacksmith round GV re-upped into), and **Canaan Partners**
(vc — led the Mate Security round M12 joined).

## Watch next week
- Poolside: watch for NVIDIA's official 8-K/PR confirmation of the $1B/$12B
  terms (currently sourced to leak + 2 Tier-3 confirms, not yet Tier-1).
- M12/Mate Security and GV/Blacksmith: both undisclosed per-investor amounts —
  worth a Tier-1 recheck if either startup's own funding page adds a number.
- Meta-BlackRock El Paso JV: watch for the formal SEC 8-K/10-Q disclosure of
  the venture (financials should show up in Meta's next quarterly filing).
- Retry EDGAR/WebFetch access next run — several leads (Oracle debt/equity
  financing docs, Amazon 8-Ks) could only be triangulated via search snippets
  this week.
