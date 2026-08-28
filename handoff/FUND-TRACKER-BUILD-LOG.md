# Fund Tracker (Section 3) — build log

Decisions, deviations, and the things that did not add up. Written the same way as
`NVIDIA-ECOSYSTEM-BUILD-LOG.md`: what was built, what was refused, and where the
data is thinner than it looks.

---

## What this section is, and why it is shaped differently

Section 2 is **discovery-shaped** — agents hunt leads and triangulate them into
dated `events`. Section 3 is **registry-shaped**: a closed list of fourteen
managers whose positions, stakes and deltas are held as a standing book.

Concretely, that meant:

- **Its own tables**, all `fund_*`. Nothing here writes to `events`. A position and
  an event are different objects; forcing one into the other's table would have
  cost both.
- **No agents.** No news, no socials, no aggregators. Every row traces to an
  accession number or an official register download. There is no research CSV in
  the normal loop except the listed-vehicle drop (see *Gaps*).
- **A closed universe.** `config/fund_managers.yaml` is the only door in.
  `engine/fund_ingest` logs an unrecognised CIK to `fund_unmapped_ciks` rather than
  adopting it.

---

## Sequencing note

The build order in the brief (spine → 13F → conviction → fast layer) was followed,
with one inversion: **CUSIP identity was built before the conviction model**, not
after. Deltas key on CUSIP, and the cross-fund crowding count — a conviction input
— is a count over CUSIPs. Scoring first would have meant scoring against a book
whose identity layer was still moving.

---

## The two hard problems

### Latency — solved by the ladder, and by admitting the lag

`13F` is the backbone and it is 1.5–4.5 months stale on arrival, so it is never the
heartbeat. Built and live: **ARK daily CSVs** (zero lag, full position-level book),
**FCA short register** (daily, named), **Form 3/4/5** (~T+2, exact trade dates),
**13D/G with Item 4** (~T+5), **8-K** (real-time), **13F-HR/A** flagged loudly.

The honesty mechanism is `latency_days`, and it is not decorative: the handoff
contract **refuses to write the payload** if any timeline event lacks it or lacks
its `staleness` label. A "new position" flag without its latency is worse than no
flag — the trade may be four months old and already closed.

**Run-now was honoured.** First run backfills 8 quarters of 13F for all fourteen,
so deltas, persistence and conviction are meaningful on day one.

### Conviction vs noise — solved twice over

Structurally by `style_tag` / `conviction_weight` (multi-strat 0.0, quant not
ingested at all), analytically by the blend in `docs/conviction-model.md`. The rule
that matters most: **deltas are computed on share count, never on value.** A
value-based delta invents adds that never happened, most enthusiastically in
whatever ran hardest.

---

## The Citadel question, answered directly

There is **no separate CIK for a conviction sleeve** inside Citadel. Citadel
Advisors LLC files one combined 13F for the whole firm and the filing carries no
strategy attribution whatsoever. Nothing in it separates the conviction desk from
market-making inventory, and no parser recovers a distinction that was never
disclosed. Anyone claiming a clean split is guessing.

So the answer is not a better parser but **event-triggered inclusion**. Citadel,
Millennium, Point72 and Balyasny are `watch_only`: **their 13F is never ingested**
(enforced at seed, again at parse time, and again as audit error `F5`). They enter
only on a disclosure market making cannot produce — 13D, >5% 13G, Form 3/4, a named
short-register entry, or an S-1 / DEF 14A cap-table appearance.

This already fires on live data. The FCA register names **Citadel Advisors LLC** and
**Millennium International Management** in dozens of UK shorts; those became watch
triggers on the first run, and neither manager has a single position row.

---

## Things that did not add up

**1. 13F values are still reported in thousands — in 2026.**
The 2023 amendment moved `value` to whole dollars. Duquesne's June 2026 filing
reports 10X Genomics at `15455` for 403,100 shares — an implied price of $0.04. So
the units are **detected per filing** from the median implied price across SH lines,
never inferred from the period. Assuming the rule had been adopted would have scaled
a real book by 1000× and silently corrupted every weight, rank and score built on
it. PRN lines are excluded from the estimate; a bond's principal amount would drag
the median into the thousands band and mis-scale an entire equity book.

**2. Greenlight's live 13F filer is not "Greenlight".**
`GREENLIGHT CAPITAL INC` stopped filing 13F-HR in 2024. The live filer is **DME
Capital Management, LP** (CIK 0001489933); **DME Advisors, LP** files 13F-NT. All
three roll up to one manager. Without that, Einhorn's book reads at a fraction of
its real size — which is exactly the failure §8b.4 warns about, found in the wild on
the second name checked.

**3. Point72 files under six CIKs.** Asset Management LP plus Hong Kong, Singapore,
London and DIFC entities, each filing separately. Mapped in `fund_manager_entities`
with an explicit `relationship`, aggregated to parent, child detail retained.

**4. Coatue's funds file ~40 separate 13F-NTs.** A 13F-NT is a *notice* that holdings
are reported by another filer — it contains no positions. Only the adviser CIK
(0001135730) rolls up; the notice entities are correctly ignored rather than counted
as forty empty books.

**5. Duquesne has no Form ADV.** Not a bug — a family office can rely on the
Dodd-Frank exemption and never register. It is recorded as a stated fact on the
identity card, and Duquesne carries `manager_class = sparse_coverage` so the UI
renders its coverage as intentionally incomplete. **A thin record here means "below
disclosure thresholds", never "low activity"**, and that inference error would be
worse than not tracking them at all.

**6. EDGAR renamed the Schedule 13D/G forms mid-history.** The same filing arrives
as `SC 13G` on older rows and `SCHEDULE 13G` on newer ones. Normalised at the door
(`fund.norm_form`); without it the stake feed looks fine and is half empty.

**7. Modern 13D/G is structured XML — and 13G uses different tag names.**
Post-2024 filings parse exactly. But 13D uses `percentOfClass` / `aggregateAmountOwned`
and 13G uses `classPercent` /
`reportingPersonBeneficiallyOwnedAggregateNumberOfShares`. Matching only the 13D
names produced a register of 13Gs at 0.0%. Older filings fall back to a labelled
HTML path so the audit can tell a parsed field from a regex over prose.

**8. An amendment that does not amend Item 4 carries no Item 4 at all.**
Most 13D/As amend one item. The stated intent from the live filing in that chain
still stands, so it is carried forward — and `intent_source_accession` records which
filing it actually came from, so inherited intent is never read as a fresh statement.

**9. `INSERT OR IGNORE` swallows NOT NULL violations as quietly as duplicates.**
Cost a silent zero-event timeline until it was found. `fund.add_event` now defaults
the NOT NULL flag columns rather than trusting callers.

**10. A short register is a log of disclosure events, not a position list.**
The FCA file contains rows from 2013. A holder that last disclosed 1.5% three years
ago has almost certainly moved on without a further notification landing in the
file. Current = at or above 0.5% **and** disclosed within 120 days; everything else
is kept as history.

**11. Three managers came back with an empty 8-quarter history.**
Altimeter, Third Point and Situational Awareness namespace-PREFIX their information
tables (`<ns1:infoTable>`). The parser was namespace-agnostic; the sniff that
*found* the table was not, and matched the bare `<infoTable` literal. The three
books silently did not exist until the sniff was fixed to match either form. This
is why `--reparse` exists: a fixed parser has to be able to retry what the old one
refused, and `pending()` alone would never revisit them.

**12. Warrants were being counted as common stock.**
The audit caught Greenlight holding "KATAPULT HOLDINGS INC" at an implied $0.0023 a
share and flagged it as a units error. It was not — `titleOfClass` read
`*W EXP 06/09/202`. They are **warrants**, and a warrant on a beaten-down microcap
really does trade at a fifth of a cent. `putCall` is blank for warrants, rights and
units, so on that field alone they all read as common. They are now detected from
`titleOfClass` and classified `other`, and the audit's implied-price band applies
to common only — a check that cries wolf on legitimate data teaches the reader to
ignore it.

**13. An options-only 13F broke unit detection.**
Excluding derivatives from the units estimate went one step too far: Elliott has
filed a **single-line 13F** holding nothing but PepsiCo puts. A put's `value` is the
value of the underlying shares, so its implied price is an ordinary equity price and
belongs in the estimate; only PRN and warrant/right/unit lines do not.

**14. A denormalised ticker went stale and never corrected itself.**
`fund_position_deltas` carries `ticker` for display, but `ticker` was missing from
the upsert's `DO UPDATE SET` list. Rows written before the CUSIP map improved kept
their old value forever — so both Alphabet share classes showed as `GOOG` in the
delta feed while `fund_positions` had GOOGL and GOOG correctly. Anything
denormalised has to be refreshed on conflict, or it is a cache with no invalidation.

**15. The cross-check invented disagreements before it found any.**
The first implementation slid a character window past the manager's name in the
proxy text and took the first number and percentage it found. It confidently
reported "Berkshire holds 100,000 shares (16.9%)". It now parses actual `<tr>`
structure, requires a share count AND a percentage as whole cell values, refuses
ambiguity, and applies a consistency gate: both sides must imply the same shares
outstanding within 2x. A genuine disagreement — the stake moved between the filing
date and the record date — leaves that implied total roughly unchanged; a mis-parse
does not. That took 67 "discrepancies" down to 28 real ones. **A cross-check that
fabricates disagreements is worse than no cross-check: it trains the reader to
ignore the flag.**

**16. The reverse lookup handed the watch-only managers a book through the back
door.** Citadel and Millennium file 13Fs, so they appear in the institutional data
like everyone else. Flagging them `is_tracked` would have rendered them
prominently — reinstating exactly the standing book §B3 refuses them. `is_tracked`
now means "one of our books" and nothing else; they remain in the background, which
is honest, because that is what they are.

**17. IAPD's firm search is literal.** It returns nothing for "Coatue Management
LLC" and the right firm for "Coatue Management". Entity suffixes come off the
*query*; the match is still verified against the returned names, so loosening the
search did not loosen what is accepted. Berkshire and Duquesne genuinely have no
ADV record — one is an operating company, the other a family office — and that is
recorded as a stated fact rather than an empty field.

**18. `companyfacts` is the wrong endpoint for one number.** Reading shares
outstanding from it meant downloading each issuer's entire XBRL history — megabytes
apiece, gigabytes across 729 issuers, to extract a single figure. `companyconcept`
serves the one fact in a few KB. It does not expose the `dei` cover-page tag for
every registrant, so there are two `us-gaap` fallbacks and the stored `source_url`
records which one answered — `SharesIssued` is not quite the same quantity as the
cover-page count, and the row should say which it is.

---

## Identifier policy

CUSIP is a commercial identifier and the SEC publishes no public crosswalk, so the
map is **derived** — and every mapping records its method and confidence:

| method | confidence | share of Duquesne's book |
|---|---|---|
| `config` (override file) | high | — |
| `ark_csv` (the fund's own CUSIP↔ticker pairing) | high | seeds ~230 names |
| `name_match:exact` | high | 59 / 95 |
| `name_match:class` / `:primary` | medium | 8 / 95 |
| `name_match:prefix` / `:subset` | low | 10 / 95 |
| unmapped | — | 14 / 95, all logged |

**Ambiguity always loses.** Alphabet class A refuses to map: GOOGL and GOOG encode
classes A and C without spelling either, so there is no rule that picks correctly
and a coin flip would attribute a class-A stake to the class-C line. Those go to
`config/fund_cusip_map.yaml` for a human to pin. An unmapped CUSIP keeps its
position with a blank ticker and is logged — **a missing ticker is a display gap; a
dropped position is a lie about the size of the book.**

---

## Gaps — declared, not implied

These ship inside the payload as `coverageGaps[]`, so the dashboard can state them
rather than imply completeness.

- **Listed vehicles (PSH / TPOU / GLRE / BRK) are not auto-fetched.** They publish
  as investor-relations PDFs and factsheets whose layout changes without notice.
  Parsing them blind is how a system starts printing confidently wrong numbers, so
  the layer ingests a validated CSV drop at
  `runs/<YYYY-MM>/fund-vehicles/{holdings,nav,track_record}.csv` — every row
  requires a resolvable `source_doc` — and when nothing is supplied it declares the
  gap and says explicitly that the manager has fallen back to a 4.5-month-stale
  13F that cannot show shorts or non-US names. **This is the one deviation from
  "no manual step in the normal loop", and it is deliberate: the alternative was
  fabricating the highest-quality data on the list.**
- **ESMA / BaFin / AMF short registers are disabled**, pending an official file URL
  that can be cited. FCA is live. A declared gap beats a scraped mirror.
- **Non-US registers (§8b.2 — UK TR-1, EU TD, Japan 5%, SEDAR+, ASX) are scoped, not
  built.** Each needs its own parser and endpoint. Listed in
  `config/fund_sources.yaml` with thresholds so the gap is visible.
- **N-PORT (§8b.1) — parser built, no CIK wired.** ARK is the only registered-fund
  case among the fourteen and its daily CSV is strictly better. The list is empty
  on purpose, not by omission.
- **Reverse lookup (§8b.5) — BUILT and run**, on SEC's own quarterly Form 13F data
  sets. One deliberate narrowing: the raw information table is ~400MB a quarter and
  covers every security every institution holds. Storing all of it would multiply
  this database to answer questions about names nobody here tracks, so the ingest
  keeps only rows for CUSIPs our funds actually hold (~1,000 securities, ~116k
  holder rows) and streams the rest past. The tail beyond the top 60 holders per
  security is also dropped — logged, not silent. The data set trails the newest
  filings by about a quarter, and each row records its own period rather than being
  smoothed onto the fund's book date.
- **Form PF is a wall, not a gap.** Filed confidentially to the SEC/FSOC. No access
  path exists.
- **Elliott's credit and distressed book is invisible.** It surfaces in PACER
  dockets, not EDGAR. Noted on the manager record so the 13F is not mistaken for
  the whole firm.

---

## Trust mechanisms

- Every row carries a source URL resolving to an actual document. A full-text-search
  query is **not** a citation and the audit rejects one (`F0`).
- **13F vs DEF 14A cross-check** (`engine/fund_crosscheck.py`) compares our stake
  against the company's own verified >5% holder table. A mismatch is **flagged with
  both numbers and both URLs** — never resolved by quietly preferring one side.
- Parse failures are stored on the filing (`parse_status` + `parse_note`) and
  surfaced by the audit. **A silently skipped filing is worse than a visible error.**
- The audit gates delivery: errors block `--deliver`, warnings ship listed. The
  handoff runs its own contract check and **refuses to overwrite a good file with a
  broken one**.
- Aggregate sources (FINRA short interest, CFTC COT) are configured
  `aggregate_only` and audit rule `F6` rejects any non-named register appearing in
  `fund_shorts`.
