"""The PUBLIC book — a capital-map allocator's 13F positions.

The map already carries the PRIVATE book: `holdings[]`, researched from a fund's
own portfolio page. That is the right and only source for a venture manager,
because Form 13F covers US-listed equity securities and nothing else. Thrive
Capital holds OpenAI, Stripe, SpaceX and Anthropic; none of them will ever appear
in a 13F, and aiming one at that fund returns an empty result that reads as a bug.

But some firms have both books. Coatue is the proof: `coatue.com/privates-portfolio`
is the venture list, and CIK 0001135730 is the marketable one. Same firm, two
disjoint sets of companies.

So this module adds a SECOND book and keeps it strictly separate:

  * different provenance — a filing, not a web page
  * different cadence — quarterly, filed ~45 days after quarter end
  * different meaning — a marketable position with a share count and a quarter
    stamp, against a venture stake with no exit date

**They are never summed.** They overlap conceptually and adding them would
double-count and state something false.

Two rules that differ from everything else in this pipeline:

**Snapshot, not cumulative.** The map's "upsert, never delete" rule is right for a
researched portfolio, where silence means nobody looked. It is wrong here: a 13F
is a COMPLETE point-in-time list, so a position that vanished was SOLD. Each
quarter replaces that quarter wholesale; earlier quarters are kept so the
action / share_delta / quarters_held derivations still work.

**Polled monthly although the data is quarterly.** Filing dates drift — Q2 2026
was filed 2026-08-12 — so a quarterly tick can land on the wrong side of a filing
and carry a stale book for three more months. A monthly poll picks each filing up
within weeks, and two months in three it is a cheap no-op: compare EDGAR's latest
13F-HR date against what is stored and stop.
"""

import yaml

from . import db, fund_13f, fund_ident, fund_sec

CFG = db.CONFIG_DIR / "allocator_ciks.yaml"

SCHEMA = """
CREATE TABLE IF NOT EXISTS public_book (
    entity          TEXT NOT NULL,
    period          TEXT NOT NULL,      -- quarter end the filing covers
    cik             TEXT NOT NULL,
    filed_at        TEXT NOT NULL,      -- when it hit EDGAR
    source_form     TEXT NOT NULL,
    source_url      TEXT NOT NULL,
    accession_no    TEXT NOT NULL,
    position_count  INTEGER NOT NULL,
    total_value_usd REAL NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (entity, period)
);

CREATE TABLE IF NOT EXISTS public_book_positions (
    id           INTEGER PRIMARY KEY,
    entity       TEXT NOT NULL,
    period       TEXT NOT NULL,
    cusip        TEXT NOT NULL,
    ticker       TEXT,
    issuer       TEXT NOT NULL,
    shares       REAL NOT NULL,
    value_usd    REAL NOT NULL,
    weight       REAL,
    instrument   TEXT NOT NULL DEFAULT 'common',
    action       TEXT,                  -- new | add | hold | trim (vs prior quarter)
    prior_shares REAL,
    share_delta_pct REAL,
    quarters_held INTEGER NOT NULL DEFAULT 1,
    accession_no TEXT,
    source_url   TEXT NOT NULL,
    UNIQUE (entity, period, cusip, instrument)
);
CREATE INDEX IF NOT EXISTS idx_public_book_pos ON public_book_positions (entity, period);
"""


def ensure(con):
    con.executescript(SCHEMA)
    con.commit()


_CFG = None


def config() -> dict:
    global _CFG
    if _CFG is None:
        _CFG = yaml.safe_load(CFG.read_text()) if CFG.exists() else {"allocators": []}
    return _CFG


def filers() -> list:
    return [a for a in (config().get("allocators") or []) if a.get("cik")]


def non_filers() -> list:
    return [a for a in (config().get("allocators") or []) if not a.get("cik")]


def latest_stored(con, entity: str):
    ensure(con)
    return con.execute(
        "SELECT * FROM public_book WHERE entity=? ORDER BY period DESC LIMIT 1",
        (entity,)).fetchone()


def refresh_entity(con, alloc: dict, force: bool = False) -> dict:
    """Pull one allocator's latest 13F if EDGAR has something we do not."""
    entity, cik = alloc["entity"], alloc["cik"]
    out = {"entity": entity, "status": "noop", "positions": 0, "period": None}
    try:
        sub = fund_sec.submissions(cik)
    except (fund_sec.SECError, fund_sec.SECConfigError) as exc:
        out.update(status="error", error=str(exc))
        return out

    # Verify the CIK still IS who the config says it is. A CIK that quietly starts
    # resolving to a different registrant would ingest a stranger's book under our
    # label, and nothing downstream would look wrong.
    expected = alloc.get("filer_name")
    if expected and not _agrees(expected, sub.get("name")):
        out.update(status="error",
                   error=(f"CIK {cik} resolves to '{sub.get('name')}', config says "
                          f"'{expected}' — refusing to ingest"))
        return out

    hr = [f for f in sub["filings"] if f["form"] in ("13F-HR", "13F-HR/A")]
    if not hr:
        out.update(status="no_filing")
        return out
    newest = hr[0]

    have = latest_stored(con, entity)
    if have and not force and have["filed_at"] >= (newest["filed_at"] or ""):
        # The cheap no-op that makes a monthly poll on quarterly data reasonable.
        out.update(status="noop", period=have["period"])
        return out

    filing = {"accession_no": newest["accession"], "cik": cik, "parent_cik": cik,
              "period_of_report": newest["period"], "filed_at": newest["filed_at"],
              "form_type": newest["form"]}
    try:
        url, xml = fund_13f.find_info_table(cik, filing["accession_no"])
    except (fund_sec.SECError, fund_sec.SECConfigError) as exc:
        out.update(status="error", error=str(exc))
        return out
    if not xml:
        out.update(status="no_table",
                   error="13F-HR with no information table (holdings reported by "
                         "another manager)")
        return out
    rows = fund_13f.parse_info_table(xml)
    if not any((r["shares"] or 0) > 0 or (r["value_raw"] or 0) > 0 for r in rows):
        # A filed-but-empty 13F is a real state and must stay distinguishable from
        # "not a filer" — the contract says an empty positions array with a real
        # filed date means "filed, held nothing reportable".
        _write_meta(con, entity, cik, filing, url, 0, 0.0)
        con.execute("DELETE FROM public_book_positions WHERE entity=? AND period=?",
                    (entity, filing["period_of_report"]))
        con.commit()
        out.update(status="empty", period=filing["period_of_report"])
        return out

    scale, mult, _ = fund_13f.detect_value_scale(rows)
    if scale == "unknown":
        out.update(status="error", error="could not determine value units")
        return out

    period = filing["period_of_report"]
    prior = con.execute(
        """SELECT cusip, shares, quarters_held FROM public_book_positions
           WHERE entity=? AND period=(SELECT MAX(period) FROM public_book_positions
                                      WHERE entity=? AND period < ?)""",
        (entity, entity, period)).fetchall()
    prior_map = {r["cusip"]: r for r in prior}

    cache = fund_ident.load_map(con)
    # Snapshot semantics: this quarter is replaced whole. A line that is gone was sold.
    con.execute("DELETE FROM public_book_positions WHERE entity=? AND period=?",
                (entity, period))

    # A 13F lists the same security once per sub-manager or discretion category —
    # BlackRock files ~50,000 lines covering a few thousand securities. The fund's
    # actual position is the SUM of those lines, so they are aggregated here.
    # Writing them row by row against a UNIQUE(cusip, instrument) key silently kept
    # only the last one and understated the biggest books by orders of magnitude.
    agg = {}
    for r in rows:
        inst = fund_13f.instrument_of(r)
        key = (r["cusip"], inst)
        a = agg.get(key)
        if a is None:
            agg[key] = {"row": r, "shares": r["shares"] or 0,
                        "value": (r["value_raw"] or 0) * mult, "lines": 1}
        else:
            a["shares"] += r["shares"] or 0
            a["value"] += (r["value_raw"] or 0) * mult
            a["lines"] += 1
    priced = [(a["row"], inst, a["value"], a["shares"])
              for (cusip, inst), a in agg.items()]
    # total_value_usd and every weight derived from it are computed over OWNED
    # shares only. 13F reports an option at the notional value of the underlying,
    # so a single index put can exceed every real holding in the file; leaving it
    # in the denominator would rescale the entire book to make room for money the
    # fund never put at risk.
    book = sum(v for _, inst, v, _sh in priced if fund_13f.is_owned(inst))

    # With no prior quarter stored, EVERY line classifies as "new" — which is a
    # fact about our coverage, not about the fund. Saying a manager opened a
    # position it has held for years is a claim we cannot support, so the action is
    # left unknown until there is something to compare against.
    first_observation = not prior_map

    for r, inst, value, shares in priced:
        got = fund_ident.resolve(con, r["cusip"], r["issuer"],
                                 accession=filing["accession_no"], cache=cache,
                                 class_title=r["class_title"])
        p = prior_map.get(r["cusip"])
        prior_shares = p["shares"] if p else None
        delta_pct = ((shares - prior_shares) / prior_shares
                     if prior_shares else None)
        if first_observation:
            action = None
        elif prior_shares is None:
            action = "new"
        elif delta_pct is not None and delta_pct > 0.01:
            action = "add"
        elif delta_pct is not None and delta_pct < -0.01:
            action = "trim"
        else:
            action = "hold"
        con.execute(
            """INSERT OR REPLACE INTO public_book_positions
                 (entity, period, cusip, ticker, issuer, shares, value_usd, weight,
                  instrument, action, prior_shares, share_delta_pct, quarters_held,
                  accession_no, source_url)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (entity, period, r["cusip"], got["ticker"], r["issuer"], shares,
             value, (value / book) if book and fund_13f.is_owned(inst) else None,
             inst, action,
             prior_shares, delta_pct,
             (p["quarters_held"] + 1) if p else 1,
             filing["accession_no"], url))
        out["positions"] += 1

    _write_meta(con, entity, cik, filing, url,
                sum(1 for _, inst, _v, _s in priced if fund_13f.is_owned(inst)), book)
    con.commit()
    out.update(status="updated", period=period, filed_at=filing["filed_at"])
    return out


def _write_meta(con, entity, cik, filing, url, count, total):
    con.execute(
        """INSERT INTO public_book
             (entity, period, cik, filed_at, source_form, source_url, accession_no,
              position_count, total_value_usd, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))
           ON CONFLICT(entity, period) DO UPDATE SET
             filed_at=excluded.filed_at, source_url=excluded.source_url,
             accession_no=excluded.accession_no,
             position_count=excluded.position_count,
             total_value_usd=excluded.total_value_usd, updated_at=datetime('now')""",
        (entity, filing["period_of_report"], cik, filing["filed_at"],
         filing["form_type"], url, filing["accession_no"], count, total))


_NOISE = {"inc", "inc.", "corp", "corporation", "co", "co.", "llc", "l.l.c.",
          "lp", "l.p.", "ltd", "ltd.", "the", "group", "holdings", "capital",
          "management", "on", "de"}


def _agrees(a: str, b: str) -> bool:
    def toks(s):
        s = (s or "").lower().replace(",", " ").replace("/", " ").replace(".", " ")
        return {t for t in s.split() if t not in _NOISE and len(t) > 1}
    ta, tb = toks(a), toks(b)
    if not ta or not tb:
        return False
    small, big = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return small.issubset(big)


def refresh(con, force: bool = False, limit: int = None) -> dict:
    """Poll every mapped filer. Cheap when nothing new has landed."""
    ensure(con)
    stats = {"checked": 0, "updated": [], "noop": 0, "empty": [], "errors": []}
    targets = filers()[:limit] if limit else filers()
    for a in targets:
        stats["checked"] += 1
        r = refresh_entity(con, a, force=force)
        if r["status"] == "updated":
            stats["updated"].append(f"{r['entity']} {r['period']} "
                                    f"({r['positions']} positions)")
        elif r["status"] == "noop":
            stats["noop"] += 1
        elif r["status"] == "empty":
            stats["empty"].append(r["entity"])
        elif r["status"] in ("error", "no_table", "no_filing"):
            stats["errors"].append(f"{r['entity']}: {r.get('error', r['status'])}")
    return stats


def payload(con, entity: str, top_n: int = 40, sectors: dict = None) -> dict:
    """The `public_book` block for one node, or None.

    None — not the empty dict — when the allocator has no filing at all. The
    contract draws a real distinction: absent means "not a filer / not mapped",
    while an empty `positions` array with a real `filed` date means "filed, held
    nothing reportable". Emitting a placeholder object would collapse two
    different facts into one.

    `positions` answers one question: what does this fund own right now. So it
    carries OWNED shares only, every row with shares > 0, ranked by weight —
    because size is the conviction signal and a 27% position and a 0.1% position
    are not the same claim. Derivatives go to `derivatives`, never counted in any
    weight or total. What was sold goes to `activity`, because a position the fund
    exited is by definition not a holding.
    """
    from datetime import date

    from .fund import latency_days

    ensure(con)
    meta = latest_stored(con, entity)
    if not meta:
        return None
    sectors = sectors or {}
    period = meta["period"]
    alloc = next((a for a in filers() if a["entity"] == entity), {})

    rows = con.execute(
        """SELECT * FROM public_book_positions
           WHERE entity=? AND period=? AND shares > 0
           ORDER BY weight DESC, value_usd DESC""", (entity, period)).fetchall()

    positions, derivatives = [], []
    for r in rows:
        if fund_13f.is_owned(r["instrument"]):
            sec = sectors.get(r["cusip"]) or {}
            positions.append({
                "ticker": r["ticker"], "issuer": r["issuer"], "cusip": r["cusip"],
                "weight": round(r["weight"], 6) if r["weight"] is not None else None,
                "shares": r["shares"], "value_usd": r["value_usd"],
                "instrument": r["instrument"],
                # Context on a position that is STILL HELD — adjectives, never the
                # subject of the row.
                "action": r["action"], "share_delta_pct": r["share_delta_pct"],
                "prior_shares": r["prior_shares"],
                "quarters_held": r["quarters_held"],
                "sector": sec.get("sector"),
            })
        else:
            derivatives.append({
                "ticker": r["ticker"], "issuer": r["issuer"], "cusip": r["cusip"],
                "instrument": r["instrument"],
                "put_call": r["instrument"] if r["instrument"] in ("put", "call") else None,
                # Named notional, not value: 13F reports the underlying, not the
                # premium. Calling this value_usd would invite it to be summed.
                "notional_usd": r["value_usd"],
                "shares_underlying": r["shares"], "as_of": period,
            })

    # What was sold. Derived by diffing against the prior stored quarter rather
    # than kept as zero-share rows, because a zero-share row in a holdings list is
    # the thing this whole section exists to stop.
    prior_period = con.execute(
        """SELECT MAX(period) p FROM public_book_positions
           WHERE entity=? AND period < ?""", (entity, period)).fetchone()["p"]
    activity = []
    if prior_period:
        held = {r["cusip"] for r in rows}
        for r in con.execute(
                """SELECT cusip, ticker, issuer, shares, value_usd, instrument
                   FROM public_book_positions
                   WHERE entity=? AND period=? AND shares > 0
                   ORDER BY value_usd DESC""", (entity, prior_period)):
            if r["cusip"] not in held:
                activity.append({
                    "ticker": r["ticker"], "issuer": r["issuer"],
                    "cusip": r["cusip"], "action": "exited",
                    "prior_shares": r["shares"], "prior_value_usd": r["value_usd"],
                    "instrument": r["instrument"], "as_of": period,
                })
    for p_ in positions:
        if p_["action"] in ("new", "add", "trim"):
            activity.append({
                "ticker": p_["ticker"], "issuer": p_["issuer"], "cusip": p_["cusip"],
                "action": p_["action"], "shares": p_["shares"],
                "prior_shares": p_["prior_shares"],
                "share_delta_pct": p_["share_delta_pct"], "as_of": period,
            })

    owned_total = sum(p_["value_usd"] for p_ in positions)
    today = date.today().isoformat()
    first_observation = not con.execute(
        """SELECT 1 FROM public_book_positions WHERE entity=? AND period < ?
           LIMIT 1""", (entity, period)).fetchone()
    out = {
        "cik": meta["cik"],
        "as_of": period,
        "filed": meta["filed_at"],
        # as_of -> today, not as_of -> filed: what the reader needs is how far
        # backwards they are looking RIGHT NOW, and that keeps growing after the
        # filing lands. A 13F is always a look backwards; hiding that would
        # misrepresent it as current.
        "latency_days": latency_days(period, today),
        "source_form": meta["source_form"],
        "source_url": meta["source_url"],
        "position_count": len(positions),
        "total_value_usd": owned_total,
        "positions": positions[:top_n],
        # True total of OWNED positions; the array above may be a ranked subset.
        "is_first_observation": bool(first_observation),
        "first_observation_note": (
            "First quarter of this filer we hold, so no position carries an action "
            "— there is nothing to compare against. It does not mean the fund "
            "opened them." if first_observation else None),
        "activity": sorted(
            activity, key=lambda a: -(a.get("prior_value_usd") or a.get("shares") or 0)
        )[:top_n],
    }
    if derivatives:
        out["derivatives"] = sorted(
            derivatives, key=lambda d_: -(d_["notional_usd"] or 0))[:top_n]
        out["derivatives_notional_usd"] = sum(d_["notional_usd"] or 0
                                              for d_ in derivatives)
        out["derivatives_note"] = (
            "Notional value of the underlying, NOT money at risk. Excluded from "
            "total_value_usd and from every weight.")
    if alloc.get("flow_driven"):
        # Task C-2: a book this large is index and flow, not conviction. Say so
        # rather than let the reader infer belief from a 50,000-line filing.
        out["flow_driven"] = True
        out["flow_driven_note"] = alloc.get("flow_note")
    return out
