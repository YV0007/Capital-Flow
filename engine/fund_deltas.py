"""Period-over-period deltas — computed on SHARE COUNT, never on value.

This is the rule the whole section stands on. A position's dollar value rises when
the price rises without a single share being bought; a value-based delta therefore
manufactures "adds" that never happened, and it does it most enthusiastically in
exactly the names that ran hardest — which is to say, it lies about momentum in
the direction that looks most like insight. Every quantity here derives from
`shares`. Value appears only as context, and as the input to weights.

Amendments are MERGED, not substituted. A 13F-HR/A is sometimes a full restatement
and sometimes a partial one adding a single confidentially-treated holding.
Replacing the period's book with the amendment would, in the second case, delete
the entire rest of the book — so the original is the base and the amendment
overlays it position by position.
"""

from . import fund, fund_13f, fund_conviction

POSITION_FORMS = ("13F-HR", "13F-HR/A")
# ARK publishes daily, so its book has to be diffed on the same machinery rather
# than sitting there with no deltas at all — the day-over-day move IS the product
# for a daily-disclosure manager.
DAILY_FORMS = ("ARK-CSV",)
# A delta small enough to be filing noise (rounding, share-count restatement)
# rather than a decision.
MIN_ACTION_DELTA_PCT = 0.01


def _book(con, parent_cik: str, period: str, forms=POSITION_FORMS) -> dict:
    """The merged book for one period: {(cusip, instrument): row}."""
    rows = con.execute(
        f"""SELECT * FROM fund_positions
            WHERE parent_cik=? AND period=? AND source_form IN
                  ({','.join('?' * len(forms))})
            ORDER BY CASE source_form WHEN '13F-HR' THEN 0 ELSE 1 END,
                     accession_no""",
        (parent_cik, period) + tuple(forms)).fetchall()
    book = {}
    for r in rows:
        # Ordering puts the original first and every amendment after it, so a later
        # row legitimately overwrites an earlier one for the same security.
        book[(r["cusip"], r["instrument"])] = dict(r)
    return book


def _periods(con, parent_cik: str, forms=POSITION_FORMS) -> list:
    return [r[0] for r in con.execute(
        f"""SELECT DISTINCT period FROM fund_positions
            WHERE parent_cik=? AND source_form IN ({','.join('?' * len(forms))})
            ORDER BY period""", (parent_cik,) + tuple(forms))]


def quarter_of(period: str) -> str:
    """The calendar quarter-end a period falls in.

    Cross-fund crowding has to be counted on a common clock. 13F periods are
    quarter-ends and ARK's are trading days, so keying the count on the raw period
    string would put ARK in a bucket of its own and make every ARK position look
    like a lone differentiated bet — inverting the one thing the term measures.

    A quarter-end maps to itself; any other date maps BACK to the last completed
    quarter-end, which is the most recent cohort there is 13F data for. Rounding
    forward would file a day in August against a quarter nobody has reported yet.
    """
    ends = ("03-31", "06-30", "09-30", "12-31")
    y, md = int(period[:4]), period[5:10]
    if md in ends:
        return period[:10]
    for e in reversed(ends):
        if md > e:
            return f"{y}-{e}"
    return f"{y - 1}-12-31"


def _cross_fund_counts(con) -> dict:
    """{(period, cusip): how many tracked managers held it}. Distinguishes a
    differentiated bet from a crowded one — same position size, different meaning.
    Watch-only managers are absent from fund_positions by construction, so this
    count is never inflated by market-making inventory."""
    out = {}
    seen = {}
    for r in con.execute(
            """SELECT period, cusip, parent_cik FROM fund_positions
               WHERE instrument='common'"""):
        seen.setdefault((quarter_of(r["period"]), r["cusip"]), set()).add(r["parent_cik"])
    for k, v in seen.items():
        out[k] = len(v)
    return out


def _classify(prev_shares, shares) -> str:
    if prev_shares in (None, 0) and shares:
        return "NEW"
    if shares in (None, 0) and prev_shares:
        return "EXIT"
    if not prev_shares:
        return "NEW"
    change = (shares - prev_shares) / prev_shares
    if change > MIN_ACTION_DELTA_PCT:
        return "ADD"
    if change < -MIN_ACTION_DELTA_PCT:
        return "TRIM"
    return "HOLD"


def _implied_price(row):
    if not row:
        return None
    sh, val = row.get("shares") or 0, row.get("value_usd") or 0
    return (val / sh) if sh > 0 and val > 0 else None


def _persistence(history, key, upto_idx) -> int:
    """Consecutive periods, ending at upto_idx, in which the position was held."""
    n = 0
    for i in range(upto_idx, -1, -1):
        if key in history[i] and (history[i][key].get("shares") or 0) > 0:
            n += 1
        else:
            break
    return n


def compute_for_manager(con, manager: dict, cross: dict,
                        forms=POSITION_FORMS) -> dict:
    parent = manager["cik"]
    periods = _periods(con, parent, forms)
    stats = {"periods": 0, "deltas": 0, "events": 0}
    if not periods:
        return stats
    history = [_book(con, parent, p, forms) for p in periods]

    for i, period in enumerate(periods):
        cur, prev = history[i], (history[i - 1] if i else {})
        prev_period = periods[i - 1] if i else None

        # The book is what the fund OWNS. Options are reported at the notional
        # value of the underlying, so including one does not just add a wrong line
        # — it inflates the denominator and silently rescales every weight in the
        # book. Bonds, warrants and units are excluded for the same reason.
        longs = sorted(((k, r) for k, r in cur.items()
                        if fund_13f.is_owned(r["instrument"])),
                       key=lambda kr: -(kr[1]["value_usd"] or 0))
        book_value = sum((r["value_usd"] or 0) for _, r in longs)
        ranks = {k: n + 1 for n, (k, _) in enumerate(longs)}
        top10 = (sum((r["value_usd"] or 0) for _, r in longs[:10]) / book_value
                 if book_value else None)
        prev_longs_value = sum((r["value_usd"] or 0) for k, r in prev.items()
                               if fund_13f.is_owned(r["instrument"]))

        # Turnover, share-based: shares that moved as a fraction of shares held.
        moved = held = 0.0
        for k in set(cur) | set(prev):
            a = (prev.get(k, {}).get("shares") or 0)
            b = (cur.get(k, {}).get("shares") or 0)
            moved += abs(b - a)
            held += max(a, b)
        turnover = (moved / held) if held else None

        if forms == POSITION_FORMS:
            filed = con.execute(
                """SELECT MAX(filed_at) f FROM fund_filings
                   WHERE parent_cik=? AND period_of_report=? AND form_type IN (?,?)""",
                (parent, period) + POSITION_FORMS).fetchone()["f"]
        else:
            filed = period          # a daily book is disclosed the day it is as of
        latency = fund.latency_days(period, filed) if filed else None

        book_ctx = {"top10_share": top10, "book_value_usd": book_value}
        conviction_adds = 0

        for key in set(cur) | set(prev):
            cusip, instrument = key
            c_row, p_row = cur.get(key), prev.get(key)
            base = c_row or p_row
            shares = (c_row or {}).get("shares") or 0
            prev_shares = (p_row or {}).get("shares") or 0
            action = _classify(prev_shares, shares)
            if action == "HOLD" and not c_row:
                continue

            share_delta = shares - prev_shares
            share_delta_pct = (share_delta / prev_shares) if prev_shares else None
            value = (c_row or {}).get("value_usd") or 0
            # A weight is a share OF THE OWNED BOOK. A derivative has no place in
            # that fraction in either direction, so it simply has no weight.
            weight = (value / book_value) if (book_value and c_row
                                              and fund_13f.is_owned(instrument)) else None
            prev_value = (p_row or {}).get("value_usd") or 0
            prev_weight = (prev_value / prev_longs_value) if prev_longs_value else None

            # conviction_add: bought MORE while the position was DOWN over the
            # period. Adding into weakness is the strongest single tell in the
            # data — it is the one action that cannot be explained by drift,
            # index-tracking or a rising price carrying the weight up on its own.
            price_now, price_then = _implied_price(c_row), _implied_price(p_row)
            price_chg = ((price_now - price_then) / price_then
                         if price_now and price_then else None)
            conv_add = bool(share_delta > 0 and price_chg is not None
                            and price_chg < 0 and fund_13f.is_owned(instrument))
            if conv_add:
                conviction_adds += 1

            persistence = _persistence(history, key, i) if c_row else 0
            xcount = cross.get((quarter_of(period), cusip), 1)

            d = {
                "instrument": instrument, "action": action, "weight": weight,
                "weight_rank": ranks.get(key), "share_delta_pct": share_delta_pct,
                "persistence_quarters": persistence,
                "conviction_add_flag": int(conv_add), "cross_fund_count": xcount,
            }
            scored = fund_conviction.score(d, book_ctx, manager)

            con.execute(
                """INSERT INTO fund_position_deltas
                     (parent_cik, period, prev_period, cusip, ticker, issuer,
                      instrument, action, shares, prev_shares, share_delta,
                      share_delta_pct, value_usd, weight, prev_weight, weight_delta,
                      weight_rank, in_top10, persistence_quarters,
                      conviction_add_flag, period_price_change_pct,
                      cross_fund_count, conviction_score, conviction_components,
                      pct_change_displayable, source_form, accession_no, source_url)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(parent_cik, period, cusip, instrument) DO UPDATE SET
                     -- ticker/issuer are denormalised from fund_positions. Leaving
                     -- them out of the update means a row written before the CUSIP
                     -- map improved keeps its stale ticker forever — which is how
                     -- both Alphabet share classes ended up labelled GOOG in the
                     -- delta feed while the positions themselves were correct.
                     ticker=excluded.ticker, issuer=excluded.issuer,
                     action=excluded.action, shares=excluded.shares,
                     prev_shares=excluded.prev_shares, share_delta=excluded.share_delta,
                     share_delta_pct=excluded.share_delta_pct,
                     value_usd=excluded.value_usd, weight=excluded.weight,
                     prev_weight=excluded.prev_weight, weight_delta=excluded.weight_delta,
                     weight_rank=excluded.weight_rank, in_top10=excluded.in_top10,
                     persistence_quarters=excluded.persistence_quarters,
                     conviction_add_flag=excluded.conviction_add_flag,
                     period_price_change_pct=excluded.period_price_change_pct,
                     cross_fund_count=excluded.cross_fund_count,
                     conviction_score=excluded.conviction_score,
                     conviction_components=excluded.conviction_components,
                     pct_change_displayable=excluded.pct_change_displayable""",
                (parent, period, prev_period, cusip, base["ticker"], base["issuer"],
                 instrument, action, shares, prev_shares, share_delta,
                 share_delta_pct, value, weight, prev_weight,
                 (weight - prev_weight) if (weight is not None
                                            and prev_weight is not None) else None,
                 ranks.get(key), int(bool(ranks.get(key) and ranks[key] <= 10)),
                 persistence, int(conv_add), price_chg, xcount,
                 scored["score"], fund_conviction.dump_components(scored["components"]),
                 int(fund_conviction.displayable_pct(weight or prev_weight,
                                                     value or prev_value)),
                 base["source_form"], base["accession_no"], base["source_url"]))
            stats["deltas"] += 1

            # On the FIRST period we hold for a manager, every position classifies
            # as NEW because there is nothing to compare against. Emitting those to
            # the timeline would announce that a fund "opened" a position it has
            # held for years — a claim about the fund made out of a fact about our
            # own coverage. The delta rows stand (the book snapshot needs them);
            # the timeline stays quiet.
            if i and action in ("NEW", "ADD", "TRIM", "EXIT") and filed:
                stats["events"] += _emit_event(
                    con, parent, period, filed, action, base, d, scored,
                    value or prev_value, latency)

        con.execute(
            """INSERT INTO fund_book_stats
                 (parent_cik, period, source_form, positions, book_value_usd,
                  top10_share, turnover_pct, avg_persistence, put_value_usd,
                  call_value_usd, conviction_add_count, as_of, disclosed_at,
                  latency_days)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(parent_cik, period, source_form) DO UPDATE SET
                 positions=excluded.positions, book_value_usd=excluded.book_value_usd,
                 top10_share=excluded.top10_share, turnover_pct=excluded.turnover_pct,
                 avg_persistence=excluded.avg_persistence,
                 put_value_usd=excluded.put_value_usd,
                 call_value_usd=excluded.call_value_usd,
                 conviction_add_count=excluded.conviction_add_count,
                 disclosed_at=excluded.disclosed_at, latency_days=excluded.latency_days""",
            (parent, period, forms[0], len(cur), book_value, top10, turnover,
             (sum(_persistence(history, k, i) for k in cur) / len(cur)) if cur else None,
             sum((r["value_usd"] or 0) for r in cur.values() if r["instrument"] == "put"),
             sum((r["value_usd"] or 0) for r in cur.values() if r["instrument"] == "call"),
             conviction_adds, period, filed, latency))
        stats["periods"] += 1

    con.commit()
    return stats


_HEADLINE = {"NEW": "opened", "ADD": "added to", "TRIM": "trimmed", "EXIT": "exited"}


def _emit_event(con, parent, period, filed, action, base, d, scored, value, latency):
    name = base["ticker"] or base["issuer"]
    pct = d["share_delta_pct"]
    show_pct = fund_conviction.displayable_pct(d["weight"], value)
    # The % is only spoken aloud when it clears the materiality floor — a 200%
    # increase in a rounding-error line is not information (§8b.6).
    size = (f" ({pct:+.0%} of shares)" if pct is not None and show_pct else "")
    stale = fund_conviction.staleness(latency)
    return fund.add_event(
        con, parent_cik=parent, event_date=period, disclosed_date=filed,
        event_type=f"13f_{action.lower()}",
        headline=(f"{_HEADLINE[action]} {name}{size}"
                  + (" — position as of the period end, disclosed "
                     f"{latency}d later" if stale != "fresh" else "")),
        issuer=base["issuer"], ticker=base["ticker"], cusip=base["cusip"],
        magnitude=value, magnitude_unit="usd",
        conviction_score=scored["score"],
        is_flagged=int(stale == "very_stale"),
        flag_reason=("disclosure lag exceeds 100 days — this position may already "
                     "be closed" if stale == "very_stale" else None),
        source_form=base["source_form"], accession_no=base["accession_no"],
        source_url=base["source_url"])


def compute(con, run_id: str, parent_cik: str = None) -> dict:
    """Recompute deltas for every tracked manager (or one)."""
    cross = _cross_fund_counts(con)
    mans = [m for m in fund.managers(con)
            if m["manager_class"] != "watch_only"
            and (not parent_cik or m["cik"] == parent_cik)]
    total = {"managers": 0, "periods": 0, "deltas": 0, "events": 0}
    per_manager = {}
    for m in mans:
        s = compute_for_manager(con, m, cross)
        if m["style_tag"] == "daily_disclosure":
            daily = compute_for_manager(con, m, cross, forms=DAILY_FORMS)
            for k in s:
                s[k] += daily[k]
        per_manager[m["slug"]] = s
        total["managers"] += 1
        for k in ("periods", "deltas", "events"):
            total[k] += s[k]
    total["per_manager"] = per_manager
    fund.log_run(con, run_id, "deltas", "ok",
                 f"{total['deltas']} deltas over {total['periods']} periods", total)
    return total
