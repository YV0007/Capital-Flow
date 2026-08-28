"""handoff/fund_tracker.json + FUND-TRACKER-CHANGELOG.md — the §6 derived views.

Same contract discipline as the ecosystem handoff: the dashboard computes NOTHING.
Weights, ranks, conviction scores, crowding counts, latency and staleness labels
all arrive already calculated, and the consuming side only draws.

And the same hard rule: a payload that violates the contract is NOT WRITTEN.
Yesterday's correct file beats today's broken one — a missing update is visibly
missing, whereas a corrupt one lies quietly.

Contract rules checked before the file is written:
  1  every fund carries style, conviction_weight, why_tracked, focus, primary_source
  2  every position and every event resolves to a source URL
  3  every event carries latency_days, and every 13F-derived one carries a
     staleness label — a "new position" flag without its latency is misleading
  4  no watch-only manager has a standing book
  5  no put appears in a long-conviction feed
  6  a % change is present only where the materiality gate allows it
  7  coverage gaps are declared rather than implied away
  8  camelCase keys, numbers as numbers
  9  holdings[] is OWNED shares only, every row with shares > 0 — no puts, calls,
     warrants, rights, units, convertibles or debt, and no exited positions
"""

import json
from datetime import date, datetime

from . import db, fund, fund_13f, fund_conviction, fund_sectors, fund_vehicles

OUT_JSON = db.HANDOFF_DIR / "fund_tracker.json"
OUT_MD = db.HANDOFF_DIR / "FUND-TRACKER-CHANGELOG.md"
CONTRACT_VERSION = "1.0"
TIMELINE_LIMIT = 400
DELTA_LIMIT_PER_FUND = 40


class ContractError(AssertionError):
    """A hard rule was broken. The file is not written."""


def _latest_period(con, parent_cik: str):
    r = con.execute(
        """SELECT period, source_form, latency_days, book_value_usd, top10_share,
                  positions, turnover_pct, avg_persistence, put_value_usd,
                  call_value_usd, conviction_add_count, disclosed_at
           FROM fund_book_stats WHERE parent_cik=?
           ORDER BY period DESC, CASE source_form WHEN 'ARK-CSV' THEN 0 ELSE 1 END
           LIMIT 1""", (parent_cik,)).fetchone()
    return dict(r) if r else None


_SECTORS = {}


def _sector(cusip):
    """{'sector','sectorLabel'} for a CUSIP, or blanks. NEVER a guess: an issuer
    whose SIC matched no rule ships with a null sector and is listed by the audit."""
    s = _SECTORS.get(cusip)
    return {"sector": (s or {}).get("sector"),
            "sectorLabel": (s or {}).get("sectorLabel"),
            "sicCode": (s or {}).get("sicCode")}


def _book(con, parent_cik: str, period: str, source_form: str) -> dict:
    """{holdings, derivatives} for one period.

    `holdings` answers one question — what does this fund own right now — so it
    carries OWNED shares only, every row with shares > 0, ranked by WEIGHT.
    Size is the conviction signal: a 27% position and a 0.1% position are not the
    same claim, and ranking by weight makes the top of the list the strongest one.

    Derivatives are split out and never counted in a weight or a total. 13F reports
    an option at the notional value of the underlying rather than the premium paid,
    so one index put can exceed every real holding in the file — and a put is a bet
    the stock FALLS, which in a portfolio table states the opposite of the truth.
    Before this split, Elliott's largest "holding" was a $2.5bn put on QQQ.
    """
    rows = con.execute(
        """SELECT p.cusip, p.ticker, p.issuer, p.shares, p.value_usd, p.instrument,
                  p.source_form, p.source_url, p.accession_no,
                  d.weight, d.weight_rank, d.action, d.share_delta,
                  d.share_delta_pct, d.persistence_quarters, d.conviction_add_flag,
                  d.cross_fund_count, d.conviction_score, d.pct_change_displayable
           FROM fund_positions p
           LEFT JOIN fund_position_deltas d
                  ON d.parent_cik=p.parent_cik AND d.period=p.period
                 AND d.cusip=p.cusip AND d.instrument=p.instrument
           WHERE p.parent_cik=? AND p.period=? AND p.source_form LIKE ?
             AND p.shares > 0
           ORDER BY p.value_usd DESC""",
        (parent_cik, period, source_form.split("/")[0] + "%")).fetchall()

    holdings, derivatives = [], []
    for r in rows:
        if fund_13f.is_owned(r["instrument"]):
            holdings.append({
                "cusip": r["cusip"], "ticker": r["ticker"], "issuer": r["issuer"],
                "shares": r["shares"], "valueUsd": r["value_usd"],
                "instrument": r["instrument"],
                "weight": round(r["weight"], 6) if r["weight"] is not None else None,
                "weightRank": r["weight_rank"],
                # Context on a position that is STILL HELD, never the subject.
                "action": r["action"],
                "persistenceQuarters": r["persistence_quarters"],
                "convictionAdd": bool(r["conviction_add_flag"]),
                "crossFundCount": r["cross_fund_count"],
                "convictionScore": r["conviction_score"],
                "sourceForm": r["source_form"], "sourceUrl": r["source_url"],
            })
        else:
            derivatives.append({
                "cusip": r["cusip"], "ticker": r["ticker"], "issuer": r["issuer"],
                "instrument": r["instrument"],
                "putCall": r["instrument"] if r["instrument"] in ("put", "call") else None,
                # Named notional, not value: naming it valueUsd invites summing.
                "notionalUsd": r["value_usd"],
                "sharesUnderlying": r["shares"],
                "sourceForm": r["source_form"], "sourceUrl": r["source_url"],
            })
    holdings.sort(key=lambda h: (-(h["weight"] or 0), -(h["valueUsd"] or 0)))
    derivatives.sort(key=lambda d_: -(d_["notionalUsd"] or 0))
    return {"holdings": holdings, "derivatives": derivatives}


def _deltas(con, parent_cik: str, period: str) -> dict:
    rows = con.execute(
        """SELECT * FROM fund_position_deltas
           WHERE parent_cik=? AND period=? ORDER BY conviction_score DESC""",
        (parent_cik, period)).fetchall()
    buckets = {"new": [], "added": [], "trimmed": [], "exited": [], "hedges": []}
    key = {"NEW": "new", "ADD": "added", "TRIM": "trimmed", "EXIT": "exited"}
    for r in rows:
        item = {
            "cusip": r["cusip"], "ticker": r["ticker"], "issuer": r["issuer"],
            "instrument": r["instrument"], "action": r["action"],
            "shares": r["shares"], "prevShares": r["prev_shares"],
            "shareDelta": r["share_delta"],
            # The percentage is present ONLY when it clears the materiality gate.
            # Emitting it with a "do not show" flag invites the dashboard to show
            # it anyway; withholding the number makes the rule structural.
            "shareDeltaPct": (r["share_delta_pct"]
                              if r["pct_change_displayable"] else None),
            "pctChangeSuppressed": not bool(r["pct_change_displayable"]),
            "valueUsd": r["value_usd"], "weight": r["weight"],
            "weightRank": r["weight_rank"],
            "persistenceQuarters": r["persistence_quarters"],
            "convictionAdd": bool(r["conviction_add_flag"]),
            "crossFundCount": r["cross_fund_count"],
            "convictionScore": r["conviction_score"],
            "convictionComponents": json.loads(r["conviction_components"] or "{}"),
            **_sector(r["cusip"]),
            "sourceForm": r["source_form"], "sourceUrl": r["source_url"],
        }
        if r["instrument"] == "put":
            buckets["hedges"].append(item)
        elif r["action"] in key:
            buckets[key[r["action"]]].append(item)
    for k in buckets:
        # New/added sort by conviction; exits and trims by the size of what left,
        # since a conviction score for an exit is zero by construction and would
        # sort the biggest exits to the bottom.
        buckets[k] = (sorted(buckets[k], key=lambda x: -(x["valueUsd"] or 0))
                      if k in ("exited", "trimmed")
                      else buckets[k])[:DELTA_LIMIT_PER_FUND]
    return buckets


def _profile(con, parent_cik: str) -> dict:
    rows = con.execute(
        """SELECT * FROM fund_book_stats WHERE parent_cik=?
           ORDER BY period DESC LIMIT 8""", (parent_cik,)).fetchall()
    if not rows:
        return {}
    def avg(k):
        v = [r[k] for r in rows if r[k] is not None]
        return round(sum(v) / len(v), 4) if v else None
    return {
        "top10Share": rows[0]["top10_share"],
        "avgTurnover": avg("turnover_pct"),
        "avgPersistence": avg("avg_persistence"),
        "putValueUsd": rows[0]["put_value_usd"],
        "callValueUsd": rows[0]["call_value_usd"],
        "convictionAddCount": rows[0]["conviction_add_count"],
        "periodsHeld": len(rows),
        "history": [{"period": r["period"], "bookValueUsd": r["book_value_usd"],
                     "positions": r["positions"], "top10Share": r["top10_share"],
                     "turnover": r["turnover_pct"], "latencyDays": r["latency_days"]}
                    for r in reversed(rows)],
    }


def _institutional(con) -> dict:
    """{cusip: institutional context} from the §8b.5 reverse lookup.

    This is what turns a share count into something interpretable: how many
    institutions hold the name at all, what share of it our funds represent, and
    where they RANK. "Coatue owns 9.3m shares" means little; "Coatue is the 18th
    largest of 72 institutional holders" is a position in a landscape."""
    latest = con.execute("SELECT MAX(period) p FROM fund_holders").fetchone()
    if not latest or not latest["p"]:
        return {}
    period = latest["p"]
    out = {}
    for r in con.execute(
            """SELECT cusip, COUNT(*) holders, SUM(shares) total,
                      SUM(CASE WHEN is_tracked THEN shares ELSE 0 END) ours,
                      MAX(CASE WHEN is_tracked THEN pct_of_shares_outstanding END) top_pct
               FROM fund_holders WHERE period=? GROUP BY cusip""", (period,)):
        out[r["cusip"]] = {
            "asOf": period, "institutionalHolders": r["holders"],
            "institutionalShares": r["total"],
            "trackedShareOfInstitutional": (r["ours"] / r["total"]) if r["total"] else None,
            "largestTrackedPctOfSharesOutstanding": r["top_pct"],
        }
    for cusip, ctx in out.items():
        ranks = [(i + 1, r["filer_name"]) for i, r in enumerate(con.execute(
            """SELECT filer_name, is_tracked FROM fund_holders
               WHERE cusip=? AND period=? ORDER BY shares DESC""", (cusip, period)))
            if r["is_tracked"]]
        ctx["trackedRanks"] = [{"rank": n, "filerName": nm} for n, nm in ranks[:8]]
    return out


def _crowding(con) -> list:
    """Per security: which tracked funds hold it, aggregate weight, direction.
    Flags both the consensus trade and the lone differentiated bet."""
    latest = {r["parent_cik"]: r["period"] for r in con.execute(
        """SELECT parent_cik, MAX(period) period FROM fund_positions
           WHERE instrument='common' GROUP BY parent_cik""")}
    if not latest:
        return []
    holders = {}
    for cik, period in latest.items():
        for r in con.execute(
                """SELECT p.cusip, p.ticker, p.issuer, p.value_usd, m.slug, m.name,
                          d.weight, d.action, d.share_delta
                   FROM fund_positions p
                   JOIN fund_managers m ON m.cik=p.parent_cik
                   LEFT JOIN fund_position_deltas d
                          ON d.parent_cik=p.parent_cik AND d.period=p.period
                         AND d.cusip=p.cusip AND d.instrument=p.instrument
                   WHERE p.parent_cik=? AND p.period=? AND p.instrument='common'""",
                (cik, period)):
            h = holders.setdefault(r["cusip"], {
                "cusip": r["cusip"], "ticker": r["ticker"], "issuer": r["issuer"],
                "holders": [], "aggregateValueUsd": 0.0})
            h["aggregateValueUsd"] += r["value_usd"] or 0
            h["holders"].append({"slug": r["slug"], "name": r["name"],
                                 "weight": r["weight"], "action": r["action"],
                                 "shareDelta": r["share_delta"],
                                 "period": period})
    inst = _institutional(con)
    out = []
    for h in holders.values():
        h["institutional"] = inst.get(h["cusip"])
        n = len(h["holders"])
        adds = sum(1 for x in h["holders"] if x["action"] in ("NEW", "ADD"))
        cuts = sum(1 for x in h["holders"] if x["action"] in ("TRIM", "EXIT"))
        h["holderCount"] = n
        h["direction"] = ("accumulating" if adds > cuts else
                          "distributing" if cuts > adds else "flat")
        h["crowding"] = ("differentiated" if n == 1 else
                         "shared" if n <= 3 else "consensus")
        h["aggregateWeight"] = round(
            sum(x["weight"] or 0 for x in h["holders"]) / n, 6) if n else None
        out.append(h)
    return sorted(out, key=lambda x: (-x["holderCount"], -x["aggregateValueUsd"]))[:150]


def _timeline(con) -> list:
    rows = con.execute(
        """SELECT e.*, m.slug, m.name AS manager, m.style_tag, m.manager_class
           FROM fund_events e JOIN fund_managers m ON m.cik=e.parent_cik
           ORDER BY e.disclosed_date DESC, e.id DESC LIMIT ?""",
        (TIMELINE_LIMIT,)).fetchall()
    out = []
    for r in rows:
        out.append({
            "fund": r["slug"], "fundName": r["manager"], "styleTag": r["style_tag"],
            "eventType": r["event_type"], "eventDate": r["event_date"],
            "disclosedDate": r["disclosed_date"], "latencyDays": r["latency_days"],
            # The staleness label travels WITH the event, always. A "new position"
            # rendered without it can be four and a half months old and already
            # closed by the time anyone reads it.
            "staleness": fund_conviction.staleness(r["latency_days"]),
            "headline": r["headline"], "issuer": r["issuer"], "ticker": r["ticker"],
            "magnitude": r["magnitude"], "magnitudeUnit": r["magnitude_unit"],
            "convictionScore": r["conviction_score"],
            "isWatchTrigger": bool(r["is_watch_trigger"]),
            "isFlagged": bool(r["is_flagged"]), "flagReason": r["flag_reason"],
            "sourceForm": r["source_form"], "sourceUrl": r["source_url"],
        })
    return out


def _watch_feed(con) -> dict:
    triggers = [{
        "fund": r["slug"], "fundName": r["name"], "triggerType": r["trigger_type"],
        "firedAt": r["fired_at"], "eventDate": r["event_date"],
        "issuer": r["issuer"], "detail": r["detail"], "sourceUrl": r["source_url"],
    } for r in con.execute(
        """SELECT t.*, m.slug, m.name FROM fund_watch_triggers t
           JOIN fund_managers m ON m.cik=t.parent_cik
           ORDER BY t.fired_at DESC LIMIT 120""")]
    return {
        "explainer": (
            "These managers have no standing book here. A multi-strat's 13F is "
            "market-making inventory and hedges, and the filing carries no strategy "
            "attribution — there is no CIK, and no parse, that separates a "
            "conviction desk from inventory. So they appear only on a disclosure "
            "market making cannot produce: a 13D, a >5% 13G, a Form 3/4, a named "
            "entry in a short register, or a pre-IPO cap table."),
        "funds": [{"fund": m["slug"], "name": m["name"], "principal": m["principal"],
                   "whyTracked": m["why_tracked"], "focus": m["focus"]}
                  for m in fund.managers(con, klass="watch_only")],
        "triggers": triggers,
    }


def _identity(con, m: dict) -> dict:
    track = [{"fiscalYear": r["fiscal_year"], "metric": r["metric"],
              "scope": r["scope"], "returnPct": r["return_pct"],
              "isProvisional": bool(r["is_provisional"]), "sourceUrl": r["source_url"]}
             for r in con.execute(
                 """SELECT * FROM fund_track_record WHERE parent_cik=?
                    ORDER BY fiscal_year DESC""", (m["cik"],))]
    entities = [{"cik": r["cik"], "name": r["entity_name"],
                 "relationship": r["relationship"], "rollup": bool(r["rollup"])}
                for r in con.execute(
                    """SELECT * FROM fund_manager_entities WHERE parent_cik=?
                       ORDER BY relationship, cik""", (m["cik"],))]
    return {
        "fund": m["slug"], "name": m["name"], "cik": m["cik"],
        "principal": m["principal"], "styleTag": m["style_tag"],
        "managerClass": m["manager_class"],
        "convictionWeight": m["conviction_weight"],
        "whyTracked": m["why_tracked"], "focus": m["focus"],
        "primarySource": m["primary_source"], "primarySourceUrl": m["primary_source_url"],
        "advStrategy": m["adv_strategy"], "advSourceUrl": m["adv_source_url"],
        "aumUsd": m["aum_usd"],
        # §8b.3: a family office's thin record means "below disclosure thresholds",
        # never "low activity". The flag exists so the UI can say that out loud.
        "sparseCoverage": m["manager_class"] == "sparse_coverage",
        "sparseCoverageNote": (
            "Coverage is intentionally incomplete. A family office surfaces only "
            "when a mandatory threshold is crossed; silence here is not inactivity."
            if m["manager_class"] == "sparse_coverage" else None),
        "trackRecord": track, "entities": entities,
    }


def build(con) -> dict:
    # Загружается ОДИН раз на сборку: сектор — свойство эмитента, а не позиции,
    # и джойн через fund_cusip_map незачем повторять на каждой строке книги.
    global _SECTORS
    _SECTORS = fund_sectors.by_cusip(con)

    funds = []
    for m in fund.managers(con):
        if m["manager_class"] == "watch_only":
            continue
        card = _identity(con, m)
        latest = _latest_period(con, m["cik"])
        if latest:
            first = con.execute(
                """SELECT MIN(period) p FROM fund_book_stats
                   WHERE parent_cik=? AND source_form=?""",
                (m["cik"], latest["source_form"])).fetchone()["p"]
            card["book"] = {
                "period": latest["period"], "sourceForm": latest["source_form"],
                "disclosedAt": latest["disclosed_at"],
                "latencyDays": latest["latency_days"],
                "staleness": fund_conviction.staleness(latest["latency_days"]),
                "bookValueUsd": latest["book_value_usd"],
                "positions": latest["positions"],
                "top10Share": latest["top10_share"],
                # When the newest period is also the oldest one we hold, every line
                # reads NEW for want of a prior — that is a statement about our
                # history, not about the fund's. The UI must not render it as
                # activity.
                "isFirstObservation": first == latest["period"],
                "firstObservationNote": (
                    "This is the first period of this source we hold, so every "
                    "position classifies as NEW for want of anything to compare "
                    "against. It does not mean the fund opened them."
                    if first == latest["period"] else None),
                **_book(con, m["cik"], latest["period"], latest["source_form"]),
            }
            book = card["book"]
            # Recomputed over OWNED rows only, so it can never disagree with the
            # weights beside it.
            book["ownedValueUsd"] = sum(h["valueUsd"] or 0 for h in book["holdings"])
            book["positions"] = len(book["holdings"])
            book["derivativesNotionalUsd"] = sum(
                d_["notionalUsd"] or 0 for d_ in book["derivatives"])
            if book["derivatives"]:
                book["derivativesNote"] = (
                    "Notional value of the underlying, NOT money at risk. Excluded "
                    "from ownedValueUsd and from every weight.")
            card["deltas"] = _deltas(con, m["cik"], latest["period"])
        else:
            card["book"], card["deltas"] = None, None
        card["convictionProfile"] = _profile(con, m["cik"])
        card["shorts"] = [{"issuer": r["issuer"], "pct": r["pct"],
                           "register": r["register"], "asOf": r["as_of_date"],
                           "sourceUrl": r["source_url"]}
                          for r in con.execute(
                              """SELECT * FROM fund_shorts
                                 WHERE parent_cik=? AND is_current=1
                                 ORDER BY pct DESC""", (m["cik"],))]
        card["stakes"] = [{"formType": r["form_type"], "issuer": r["issuer"],
                           "ticker": r["ticker"], "pctOfClass": r["pct_of_class"],
                           "eventDate": r["event_date"], "filedAt": r["filed_at"],
                           "isActivist": bool(r["is_activist"]),
                           "intentSummary": r["intent_summary"],
                           "intentExcerpt": r["intent_excerpt"],
                           "sourceUrl": r["source_url"]}
                          for r in con.execute(
                              """SELECT * FROM fund_stakes WHERE parent_cik=?
                                 ORDER BY filed_at DESC LIMIT 25""", (m["cik"],))]
        card["vehicleHoldings"] = [
            {"vehicle": r["vehicle"], "asOf": r["as_of"], "name": r["name"],
             "ticker": r["ticker"], "weight": r["weight"], "direction": r["direction"],
             "sourceDoc": r["source_doc"]}
            for r in con.execute(
                """SELECT * FROM fund_vehicle_holdings WHERE parent_cik=?
                   ORDER BY as_of DESC, weight DESC LIMIT 60""", (m["cik"],))]
        funds.append(card)

    return {
        "contractVersion": CONTRACT_VERSION,
        "generated": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "section": "fund-tracker",
        "explainer": (
            "A registry, not a feed. Fourteen managers, a closed list, every row "
            "traceable to a mandated filing or an official register. 13F is the "
            "backbone and it is up to 4.5 months stale — the daily and T+2 layers "
            "are the pulse. Every dated item carries latencyDays; nothing here "
            "should be read without it."),
        "latencyLadder": [
            {"latency": "daily", "source": "ARK holdings CSV", "gives": "full position-level book, same day"},
            {"latency": "daily", "source": "FCA / EU short registers", "gives": "NAMED shorts above 0.5%"},
            {"latency": "~T+2", "source": "Form 3/4/5", "gives": "exact-dated trades once a fund is an insider"},
            {"latency": "~T+5", "source": "Schedule 13D + amendments", "gives": "activist stake with stated intent (Item 4)"},
            {"latency": "real-time", "source": "Form 8-K", "gives": "board changes, settlements, standstills"},
            {"latency": "monthly", "source": "listed vehicles (PSH/TPOU/GLRE)", "gives": "full book including shorts and non-US names"},
            {"latency": "quarterly", "source": "13G / 13G-A", "gives": "passive >5% crossings"},
            {"latency": "quarterly +45d", "source": "13F-HR / 13F-HR/A", "gives": "the full long book — the backbone, and the slowest layer"},
        ],
        "convictionModel": {
            "version": fund.load_conviction_cfg()["version"],
            "doc": "docs/conviction-model.md",
            "note": ("Every constant is [PROPOSED] and tunable in "
                     "config/fund_conviction.yaml. Each score ships with its own "
                     "components so it can be taken apart."),
            "deltaBasis": ("SHARE COUNT. Never value — a position's value rises with "
                           "the price without a share being bought, and a "
                           "value-based delta invents adds that never happened."),
        },
        "funds": funds,
        "crowding": _crowding(con),
        "timeline": _timeline(con),
        "watchOnly": _watch_feed(con),
        "coverageGaps": fund_vehicles.coverage_gaps(con),
        "crosschecks": [
            {"fund": r["slug"], "issuer": r["issuer"], "period": r["period"],
             "filedShares": r["filed_shares"], "proxyShares": r["proxy_shares"],
             "proxyPct": r["proxy_pct"], "proxyAsOf": r["proxy_as_of"],
             "deltaPct": r["delta_pct"], "status": r["status"], "note": r["note"],
             "filingUrl": r["filing_url"], "proxyUrl": r["proxy_url"]}
            for r in con.execute(
                """SELECT c.*, m.slug FROM fund_crosschecks c
                   JOIN fund_managers m ON m.cik = c.parent_cik
                   WHERE c.status = 'discrepancy'
                   ORDER BY c.delta_pct DESC LIMIT 60""")],
        "totals": {
            "funds": len(funds),
            "watchOnly": len(fund.managers(con, klass="watch_only")),
            "positions": con.execute("SELECT COUNT(*) c FROM fund_positions").fetchone()["c"],
            "events": con.execute("SELECT COUNT(*) c FROM fund_events").fetchone()["c"],
            "institutionalHolderRows": con.execute(
                "SELECT COUNT(*) c FROM fund_holders").fetchone()["c"],
        },
        "reverseLookupNote": (
            "Institutional holder counts come from SEC's quarterly Form 13F data "
            "sets and are SCOPED to the securities these funds hold — not the whole "
            "market. They also trail the newest filings by about a quarter, which is "
            "why asOf differs from a fund's own book date."),
    }


# ── contract ─────────────────────────────────────────────────────────────────
def validate(payload: dict) -> list:
    errs = []
    seen = set()
    for f in payload["funds"]:
        for req in ("styleTag", "convictionWeight", "whyTracked", "focus",
                    "primarySource"):
            if f.get(req) in (None, ""):
                errs.append(f"1 fund {f['fund']}: missing {req}")
        if f["fund"] in seen:
            errs.append(f"1 duplicate fund id {f['fund']}")
        seen.add(f["fund"])
        if f.get("managerClass") == "watch_only":
            errs.append(f"4 watch-only manager {f['fund']} has a standing book")
        for h in ((f.get("book") or {}).get("holdings") or []):
            if not h.get("sourceUrl"):
                errs.append(f"2 {f['fund']} holding {h.get('issuer')}: no sourceUrl")
            # 9 — holdings are what the fund OWNS. A derivative here inverts the
            # meaning of the row and inflates every weight around it; a zero-share
            # row is a position that was sold.
            if h.get("instrument") not in ("common", "adr"):
                errs.append(f"9 {f['fund']}: {h.get('instrument')} on "
                            f"{h.get('issuer')} in holdings[] — not ownership")
            if not (h.get("shares") or 0) > 0:
                errs.append(f"9 {f['fund']}: {h.get('issuer')} in holdings[] with "
                            f"no shares — an exited position is not a holding")
        for bucket, items in (f.get("deltas") or {}).items():
            for d in items:
                if bucket != "hedges" and d.get("instrument") == "put":
                    errs.append(f"5 {f['fund']}: put on {d.get('issuer')} in the "
                                f"'{bucket}' long feed")
                if d.get("pctChangeSuppressed") and d.get("shareDeltaPct") is not None:
                    errs.append(f"6 {f['fund']} {d.get('issuer')}: % change emitted "
                                f"below the materiality gate")
        if f.get("book") and f["book"].get("latencyDays") is None:
            errs.append(f"3 {f['fund']}: book has no latencyDays")
    for e in payload["timeline"]:
        if e.get("latencyDays") is None:
            errs.append(f"3 timeline event '{e.get('headline')}': no latencyDays")
        if not e.get("sourceUrl"):
            errs.append(f"2 timeline event '{e.get('headline')}': no sourceUrl")
        if not e.get("staleness"):
            errs.append(f"3 timeline event '{e.get('headline')}': no staleness label")
    if payload.get("coverageGaps") is None:
        errs.append("7 coverageGaps missing — gaps must be declared, not implied")
    for k in payload:
        if "_" in k:
            errs.append(f"8 payload key '{k}' is not camelCase")
    return errs


def run(con, run_id: str, audit_verdict: dict = None) -> dict:
    db.HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    prev = json.loads(OUT_JSON.read_text()) if OUT_JSON.exists() else None
    payload = build(con)
    if audit_verdict:
        payload["audit"] = {
            "generated": audit_verdict["generated"], "passed": audit_verdict["passed"],
            "errorCount": len(audit_verdict["errors"]),
            "warningCount": len(audit_verdict["warnings"]),
            "warnings": audit_verdict["warnings"][:30],
            "stats": audit_verdict["stats"],
        }
    errs = validate(payload)
    if errs:
        fund.log_run(con, run_id, "handoff", "error",
                     f"contract violated ({len(errs)}) — file NOT written",
                     {"errors": errs[:40]})
        return {"ok": False, "errors": errs, "path": None}

    OUT_JSON.write_text(json.dumps(payload, indent=2))
    OUT_MD.write_text(_changelog(prev, payload))
    fund.log_run(con, run_id, "handoff", "ok",
                 f"{payload['totals']['funds']} funds, "
                 f"{payload['totals']['events']} events -> {OUT_JSON}",
                 payload["totals"])
    return {"ok": True, "errors": [], "path": str(OUT_JSON),
            "totals": payload["totals"]}


def _changelog(prev, cur) -> str:
    prev_events = {(e["fund"], e["eventType"], e["eventDate"], e.get("issuer"))
                   for e in (prev or {}).get("timeline", [])}
    new = [e for e in cur["timeline"]
           if (e["fund"], e["eventType"], e["eventDate"], e.get("issuer")) not in prev_events]
    L = [f"# Fund Tracker changelog — {cur['generated']}", "",
         f"- funds: {cur['totals']['funds']}  watch-only: {cur['totals']['watchOnly']}"
         f"  positions: {cur['totals']['positions']}  events: {cur['totals']['events']}",
         ""]
    L += [f"## New since the last handoff ({len(new)})", ""]
    for e in new[:60]:
        L.append(f"- **{e['fundName']}** — {e['headline']} "
                 f"_(event {e['eventDate']}, disclosed {e['disclosedDate']}, "
                 f"+{e['latencyDays']}d, {e['staleness']})_")
    if not new:
        L.append("_none_")
    flagged = [e for e in cur["timeline"] if e["isFlagged"]]
    L += ["", f"## Flagged ({len(flagged)})", ""]
    L += [f"- **{e['fundName']}** — {e['headline']} — _{e['flagReason']}_"
          for e in flagged[:30]] or ["_none_"]
    trig = cur["watchOnly"]["triggers"]
    L += ["", f"## Watch-only triggers ({len(trig)})", ""]
    L += [f"- **{t['fundName']}** {t['firedAt']} — {t['detail']}" for t in trig[:25]] \
        or ["_none_"]
    L += ["", f"## Declared coverage gaps ({len(cur['coverageGaps'])})", ""]
    L += [f"- `{g['layer']}` — {g['status']}: {g.get('effect')}"
          for g in cur["coverageGaps"]]
    return "\n".join(L) + "\n"
