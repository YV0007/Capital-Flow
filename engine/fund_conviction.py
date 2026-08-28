"""Position-level conviction scoring (spec §B2).

The problem this solves: a 13F is a legal aggregation, not a statement of belief.
For a multi-strat it is market-making inventory; for a quant it is model output;
for Druckenmiller's top five it is the whole thesis. Treating those alike is the
single worst failure mode available to this section — so conviction is attacked
from two directions at once.

STRUCTURAL (§B1): `conviction_weight`, set per manager in config from the style
tag. multistrat_mm is 0.0 and quant is never ingested. That multiplier is applied
last, so a market maker cannot score high no matter how the analytics land.

ANALYTICAL (§B2): the blend below. Every constant lives in
config/fund_conviction.yaml tagged [PROPOSED] and every term is written back into
`conviction_components` as JSON, so any score on the dashboard can be taken apart
and argued with. A score you cannot decompose is a number people either trust
blindly or ignore entirely; neither is useful.

Two rules that are not negotiable:
  * deltas come from SHARE COUNT. Never value. Handled upstream in fund_deltas.py,
    relied on here.
  * a PUT is a hedge or a short expression. It is never folded into long
    conviction — it is scored on its own track and surfaced separately.
"""

import json

from . import fund

_CFG = None


def cfg() -> dict:
    global _CFG
    if _CFG is None:
        _CFG = fund.load_conviction_cfg()
    return _CFG


def _clamp01(x) -> float:
    return 0.0 if x is None else max(0.0, min(1.0, float(x)))


def _term_position_weight(weight, c) -> float:
    return _clamp01((weight or 0) / c["position_weight"]["full_credit_at"])


def _term_weight_rank(rank, c) -> float:
    k = c["weight_rank"]
    if not rank:
        return 0.0
    lo, hi = k["full_credit_rank"], k["zero_credit_rank"]
    if rank <= lo:
        return 1.0
    if rank >= hi:
        return 0.0
    return 1.0 - (rank - lo) / float(hi - lo)


def _term_action(action, share_delta_pct, c) -> float:
    k = c["action"]
    base = k.get(action, 0.0)
    if action == "ADD" and share_delta_pct:
        full = k["add_full_credit_delta_pct"]
        return base + (1.0 - base) * _clamp01(share_delta_pct / full)
    return base


def _term_persistence(quarters, c) -> float:
    full = c["persistence"]["full_credit_quarters"]
    return _clamp01(((quarters or 1) - 1) / float(max(1, full - 1)))


def _term_concentration(top10_share, c) -> float:
    k = c["book_concentration"]
    lo, hi = k["floor"], k["ceiling"]
    if top10_share is None:
        return 0.0
    return _clamp01((top10_share - lo) / float(hi - lo))


def _term_differentiation(cross_fund_count, c) -> float:
    """A name one tracked fund owns is a differentiated bet; a name six of them own
    is a crowded trade. Same weight, very different information."""
    crowded = max(2, c["differentiation"]["crowded_at"])
    n = max(1, cross_fund_count or 1)
    return _clamp01(1.0 - (n - 1) / float(crowded - 1))


def score(delta: dict, book: dict, manager: dict) -> dict:
    """Score one position-period. Returns {'score', 'components', 'track'}.

    track is 'long' or 'hedge'. A put returns score=None on the long track: it is
    deliberately absent from the conviction feed rather than present with a low
    number, because a low long-conviction score and a hedge are different claims.
    """
    c = cfg()
    w = c["weights"]
    inst = delta.get("instrument") or "common"
    mult = c["instrument_multiplier"].get(inst, c["instrument_multiplier"]["other"])

    terms = {
        "position_weight": _term_position_weight(delta.get("weight"), c),
        "weight_rank": _term_weight_rank(delta.get("weight_rank"), c),
        "action": _term_action(delta.get("action"), delta.get("share_delta_pct"), c),
        "persistence": _term_persistence(delta.get("persistence_quarters"), c),
        "conviction_add": 1.0 if delta.get("conviction_add_flag") else 0.0,
        "book_concentration": _term_concentration(book.get("top10_share"), c),
        "differentiation": _term_differentiation(delta.get("cross_fund_count"), c),
    }
    raw = sum(terms[k] * w[k] for k in w) * 100.0
    cw = float(manager.get("conviction_weight", 1.0))

    components = {
        "version": c["version"],
        "terms": {k: round(v, 4) for k, v in terms.items()},
        "weights": w,
        "raw_0_100": round(raw, 2),
        "instrument": inst,
        "instrument_multiplier": mult,
        "conviction_weight": cw,
        "style_tag": manager.get("style_tag"),
    }

    if mult is None:
        components["excluded_from_long_conviction"] = (
            "not an ownership instrument — a derivative or debt line is not a long "
            "conviction bet, and 13F reports it at notional rather than at risk")
        components["hedge_score_0_100"] = round(raw * cw, 2)
        return {"score": None, "components": components, "track": "hedge"}

    final = raw * float(mult) * cw
    components["final_0_100"] = round(final, 2)
    return {"score": round(final, 2), "components": components, "track": "long"}


def displayable_pct(weight, value_usd) -> bool:
    """§8b.6 guard 1. An 89% cut in a $2m line reads as dramatic and signifies
    nothing. Below the floor the percentage is not displayable and the dashboard
    must suppress or de-emphasise it — enforced here so it cannot be forgotten
    downstream."""
    g = cfg()["display_guards"]
    return bool((weight or 0) >= g["min_weight_for_pct_change"]
                or (value_usd or 0) >= g["min_value_for_pct_change_usd"])


def staleness(latency: int) -> str:
    """§8b.6 guard 2. A 13F 'new position' can be 4.5 months old and already
    exited. The label travels with the flag, always."""
    g = cfg()["display_guards"]
    if latency is None:
        return "unknown"
    if latency >= g["very_stale_position_days"]:
        return "very_stale"
    if latency >= g["stale_position_days"]:
        return "stale"
    return "fresh"


def dump_components(components: dict) -> str:
    return json.dumps(components, separators=(",", ":"))
