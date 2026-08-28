# Conviction model — Fund Tracker (Section 3)

**Status: every constant below is `[PROPOSED]`.** They live in
`config/fund_conviction.yaml`, not in Python, so tuning is a config edit and never
a code change. The version string in that file is stamped onto every score, so any
number on the dashboard can be traced back to the constants that produced it.

---

## 1. The problem this model exists to solve

A 13F is a legal aggregation, not a statement of belief. Read literally it says the
same thing about a market maker's inventory line and about the position a
concentrated manager has built their year around. Treating those alike is the
single worst failure available to this section — it would put thousands of
meaningless rows in front of the reader wearing the same clothes as the handful
that matter.

So conviction is attacked twice, from different directions.

### Structural — who is even allowed to score

`style_tag` and its `conviction_weight` multiplier, set per manager in
`config/fund_managers.yaml`:

| style_tag | weight | why |
|---|---|---|
| `concentrated` | 1.0 | the long book *is* the thesis |
| `activist` | 1.0 | 13D Item 4 is the signal; the 13F is a footnote |
| `crossover_tech` | 0.9 | trust the direction, discount for turnover |
| `full_disclosure` | 1.0 | the vehicle or letter beats the 13F |
| `daily_disclosure` | 1.0 | ARK — the whole book, every day |
| `multistrat_mm` | **0.0** | 13F is inventory and hedges. Not conviction. |
| `quant` | **0.0** | model output. Not ingested at all. |

The multiplier is applied **last**, so no combination of analytics can lift a
market maker's inventory line into the conviction feed.

### Analytical — how much conviction a position actually shows

The blend in §3, computed per position per period.

---

## 2. The rule everything rests on: deltas are SHARE-based

> `share_delta = shares_t − shares_{t−1}`

Never value. A position's dollar value rises when the price rises without a single
share being bought. A value-based delta therefore manufactures "adds" that never
happened — and it does so most enthusiastically in whatever ran hardest, which is
to say it fabricates conviction in exactly the names where a reader is most primed
to believe it.

This is enforced in `engine/fund_deltas.py`; value enters the model only as the
input to *weights*, never to *changes*.

A second consequence: `value_usd` units are **detected per filing**, not assumed.
Before the 2023 amendment 13F values were reported in thousands, after it in whole
dollars, and filers did not all switch — a live 2026 filing in this universe still
reports thousands. `engine/fund_13f.detect_value_scale` takes the median implied
price (`value / shares`) across SH lines and scales accordingly. Get this wrong and
a whole book is off by 1000×, along with every weight and rank derived from it.

---

## 3. The blend

`conviction_score = Σ(term × weight) × 100 × instrument_multiplier × conviction_weight`

| term | weight `[PROPOSED]` | shape |
|---|---|---|
| `position_weight` | **0.28** | `min(1, weight / 0.15)` — a 15% line is already maximum conviction; 30% should not score double |
| `weight_rank` | **0.12** | 1.0 at rank 1, linear to 0 at rank 20 |
| `action` | **0.22** | NEW 0.85 · ADD 0.70→1.0 · HOLD 0.45 · TRIM 0.15 · EXIT 0.0 |
| `persistence` | **0.12** | `(quarters − 1) / 7`, full credit at 8 quarters |
| `conviction_add` | **0.14** | 1.0 when shares rose while the position was down |
| `book_concentration` | **0.07** | fund top-10 share rescaled 0.30 → 0, 0.90 → 1 |
| `differentiation` | **0.05** | 1.0 when one tracked fund holds it, 0 at six |

Weights sum to 1.0; `engine/fund.load_conviction_cfg` refuses to load a file where
they do not.

### Notes on the individual terms

**`action`, ADD.** Scaled by how much was added:
`0.70 + 0.30 × min(1, share_delta_pct / 0.50)`. A +50% share increase earns full
credit; a +2% drift does not.

**`conviction_add` — adding into weakness.** The strongest single tell in the data,
and the reason it carries more weight than book concentration. It is the one action
that cannot be explained by drift, index-tracking, or a rising price carrying the
weight up on its own. Computed from the fund's *own* implied price
(`value / shares`) across the two periods, so it needs no external price feed:
shares up **and** implied price down.

**`differentiation`.** A name one tracked fund owns and a name six of them own are
the same position size carrying completely different information. Same weight,
different meaning — the model says so rather than leaving the reader to notice.

**`EXIT` scores 0.** `conviction_score` measures *long conviction*, and an exit has
none by definition. This is why the payload sorts the `exited` and `trimmed`
buckets by the **value of what left**, not by score — otherwise the largest exits
would sort to the bottom of the feed.

### Instruments

| instrument | multiplier `[PROPOSED]` | treatment |
|---|---|---|
| `common` | 1.00 | the long book |
| `call` | 0.60 | a levered long expression, but not shares |
| `other` | 0.50 | PRN / convertible lines |
| `put` | **excluded** | a hedge or a short expression |

A put is never folded into long conviction. It is scored on its own track, returned
with `score = None` and `track = "hedge"`, and lands in a separate `hedges[]` list
in the payload. The distinction matters: *a low long-conviction score* and *a hedge*
are different claims, and collapsing them inverts the meaning of the position.

---

## 4. Interpretation guards (§8b.6) — enforced, not advisory

**Guard 1 — a big % on a small line is noise.** An 89% cut in a $2m position reads
as dramatic and signifies nothing. A percentage is emitted only when the position
clears **0.5% of book** `[PROPOSED]` **or** **$25m** `[PROPOSED]`. Below that the
payload sets `shareDeltaPct: null` and `pctChangeSuppressed: true` — the number is
*withheld*, not flagged, because shipping it alongside a "please don't show this"
hint is an invitation to show it anyway.

**Guard 2 — a 13F "new position" is up to 4.5 months old.** A name opened at a June
30 period end and disclosed in mid-August may already be gone. Every event carries
`latencyDays` and a `staleness` label — `fresh` / `stale` (≥45d) / `very_stale`
(≥100d) `[PROPOSED]` — and the handoff contract **refuses to write the file** if any
event lacks either. A new-position flag without its latency is not incomplete, it is
misleading.

---

## 5. Validation against known conviction bets

Run against the live 8-quarter backfill. The test is not whether the numbers are
"right" — there is no ground truth for conviction — but whether the model ranks
positions the way someone who knows these books would.

| case | what the model should say | what it says |
|---|---|---|
| Duquesne / Natera — top position, ~20% of book, held 9 straight quarters, added into | near the top of the scale | **92.7** on the +22% add, **75.5** on a later +4% add |
| Duquesne / Insmed — mid-weight, added +23% while the position was down | high, driven by `conviction_add` | **68.7** with `convictionAdd = true` |
| A rounding-error line trimmed 89% | near zero, and the % withheld | **6.1**, `pctChangeSuppressed = true` |
| The same maximal add booked at a multi-strat | exactly zero | **0.0** |
| A put with otherwise maximal analytics | absent from long conviction | `score = None`, `track = "hedge"`, hedge score 95.6 |

The ordering is the point: a concentrated manager's long-held, added-into top line
outranks everything, size-without-persistence sits mid-table, and inventory noise
and hedges cannot enter the feed at all.

---

## 6. What this model does not claim

- **It does not know why.** It reads position mechanics. A manager may have added
  into weakness for a risk-model reason and not a thesis reason; the score cannot
  tell.
- **It cannot see a short** except where a named EU/UK register or a full-disclosure
  vehicle shows one. A fund can look long a theme on its 13F while running a large
  short against it, and EDGAR would never say so.
- **It cannot separate a multi-strat's conviction desk from its inventory.** No
  scoring change fixes that, because the filing does not contain the distinction.
  Hence the §B3 carve-out: those managers have no standing book here at all.
- **It is calibrated against a handful of cases, not fitted.** Every constant is
  `[PROPOSED]` for that reason. Treat the ranking as informative and the absolute
  number as a working scale.

---

## 7. Tuning

Edit `config/fund_conviction.yaml`, bump `version`, re-run:

```bash
python run_funds.py --offline
```

Deltas and scores are recomputed from stored positions with no network calls, and
the new `version` is stamped onto every `conviction_components` blob — so scores
from two different constant sets are always distinguishable after the fact.
