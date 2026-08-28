"""The fast layer — what keeps the section alive between 13F prints.

13F is the backbone and it is 1.5 to 4.5 months stale on arrival. Waiting for the
next one is not an option, so these are the layers that fill the gap:

  ~T+2   Form 3/4/5   exact-dated trades, once a fund is an insider or >10% owner
  ~T+5   13D + /A     activist stake >5% WITH stated intent (Item 4)
  ~T+5   13G + /A     passive >5% crossings
  live   8-K          board changes, activist settlements, standstills

For an activist the 13F is not the signal at all — Item 4 is. So Item 4 is stored
VERBATIM as `intent_excerpt` next to a short structured `intent_summary`. The
excerpt is the evidence; the summary is our reading of it, and keeping the two in
separate columns is what stops a paraphrase from quietly becoming the record.

Modern 13D/G filings (post-2024) are structured XML and parse exactly. Older ones
are HTML, so there is a text fallback — labelled as such, because a regex over
prose is a weaker claim than a parsed field and the audit should be able to tell
them apart.
"""

import re
import xml.etree.ElementTree as ET

from . import fund, fund_ident, fund_ingest, fund_sec

_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\xa0]+")
# Item 4 in an HTML 13D: everything between the Item 4 heading and Item 5.
_ITEM4_TEXT = re.compile(
    r"item\s*4\.?\s*[—:\-]?\s*purpose\s+of\s+(?:the\s+)?transaction(.{80,20000}?)"
    r"item\s*5\.?\s*[—:\-]?\s*interest", re.I | re.S)

# Vocabulary that separates a real campaign from boilerplate. Every 13D says the
# filer "may engage with management"; what matters is which levers get named.
_INTENT_MARKERS = [
    ("board representation", r"board (?:representation|seat|nominee|designee)|nominat\w+ .{0,40}director"),
    ("proxy contest", r"proxy (?:contest|solicitation|fight)|consent solicitation"),
    ("strategic alternatives", r"strategic alternatives|review of alternatives|explore .{0,30}sale"),
    ("sale of the company", r"sale of the (?:company|issuer)|business combination|merger"),
    ("capital return", r"(?:share|stock) repurchase|return of capital|special dividend"),
    ("management change", r"replace .{0,30}(?:ceo|chief executive|management)|leadership change"),
    ("cost reduction", r"cost (?:reduction|structure)|operating margin|expense"),
    ("settlement / standstill", r"standstill|cooperation agreement|settlement agreement"),
    ("opposition to a transaction", r"oppose|vote against|inadequate consideration"),
    ("engagement with management", r"engage .{0,40}(?:management|board)|discussions with"),
]


def _text(html: str) -> str:
    if not html:
        return ""
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    s = _TAGS.sub(" ", s)
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#8217;", "'")
          .replace("&#8220;", '"').replace("&#8221;", '"').replace("&#146;", "'")
          .replace("&rsquo;", "'").replace("&ldquo;", '"').replace("&rdquo;", '"'))
    return _WS.sub(" ", s).strip()


def _tag(el) -> str:
    return el.tag.rsplit("}", 1)[-1]


def _find(root, name):
    # None-safe: these are chained (_txt(_find(x, a), b)) and an optional block —
    # a Form 4 line with no postTransactionAmounts, say — legitimately yields None
    # halfway down the chain. Crashing there kills the whole stage over one
    # perfectly valid filing.
    if root is None:
        return None
    for el in root.iter():
        if _tag(el) == name:
            return el
    return None


def _txt(root, name, default=None):
    el = _find(root, name)
    return (el.text or "").strip() if el is not None and el.text else default


def summarize_intent(item4: str) -> str:
    """A short structured read of Item 4 — never a replacement for the excerpt."""
    if not item4:
        return None
    low = item4.lower()
    hits = [label for label, pat in _INTENT_MARKERS if re.search(pat, low)]
    return "; ".join(hits) if hits else "engagement stated without a named lever"


# ── 13D / 13G ────────────────────────────────────────────────────────────────
def parse_stake(cik, accession: str, primary_doc: str) -> dict:
    """Cover-page facts + Item 4. XML path first, HTML fallback second."""
    out = {"parse_path": None}
    xml_url = fund_sec.doc_url(cik, accession, "primary_doc.xml")
    try:
        xml = fund_sec.get_text(xml_url)
    except fund_sec.SECError:
        xml = None

    # 13G shares the structured format under its own namespace — matching only
    # the 13D one would silently push every modern 13G onto the weaker HTML path.
    if xml and "edgarSubmission" in xml and "schedule13" in xml.lower():
        root = ET.fromstring(xml.encode("utf-8", "replace"))
        cover = _find(root, "coverPageHeader")
        issuer_el = _find(cover, "issuerInfo") if cover is not None else None
        # Several reporting persons file jointly; the group's stake is the largest
        # aggregate reported, not the sum — summing double-counts the same shares
        # through each affiliated entity that also reports them.
        # 13D and 13G use different tag names for the same cover-page numbers
        # (percentOfClass vs classPercent), and only the 13D wraps them in a
        # reportingPersonInfo element. Collecting by tag name across the whole
        # document handles both without a per-form branch.
        pcts = _all_numbers(root, ("percentOfClass", "classPercent"))
        shares = _all_numbers(root, ("aggregateAmountOwned",
                                     "reportingPersonBeneficiallyOwnedAggregate"
                                     "NumberOfShares"))
        item4 = _find(root, "item4") if "schedule13D" in xml else None
        item4_txt = " ".join(t.strip() for t in (item4.itertext() if item4 is not None
                                                 else []) if t.strip()) or None
        out.update({
            "parse_path": "xml",
            "issuer": _first(root, ("issuerName",)),
            "issuer_cik": (_first(root, ("issuerCIK", "issuerCik")) or "").zfill(10) or None,
            "cusip": _first(root, ("issuerCusipNumber",)),
            "event_date": _norm_date(
                _first(root, ("dateOfEvent", "eventDateRequiresFilingThisStatement"))),
            "amendment_no": _txt(cover, "amendmentNo") if cover is not None else None,
            "pct_of_class": max(pcts) if pcts else None,
            "shares": max(shares) if shares else None,
            "intent_excerpt": (item4_txt or "")[:6000] or None,
            "source_url": xml_url,
        })
        return out

    # Pre-2025 filings are prose. Weaker, and labelled weaker.
    url = fund_sec.doc_url(cik, accession, primary_doc)
    html = fund_sec.get_text(url)
    if not html:
        return out
    body = _text(html)
    m = _ITEM4_TEXT.search(html) or _ITEM4_TEXT.search(body)
    pct = re.search(r"percent\s+of\s+class[^0-9]{0,80}?([0-9]{1,2}(?:\.[0-9]{1,2})?)\s*%",
                    body, re.I)
    cusip = re.search(r"\b([0-9A-Z]{6}[0-9A-Z]{2}[0-9])\b\s*(?:\(cusip|cusip)", body, re.I)
    subj = subject_company(cik, accession)
    out.update({
        "parse_path": "html",
        "issuer": subj.get("name"),
        "issuer_cik": subj.get("cik"),
        "cusip": cusip.group(1) if cusip else None,
        "pct_of_class": float(pct.group(1)) if pct else None,
        "intent_excerpt": _text(m.group(1))[:6000] if m else None,
        "source_url": url,
    })
    return out


_SUBJ = re.compile(
    r"SUBJECT COMPANY.*?COMPANY CONFORMED NAME:\s*(.+?)\s*\n.*?"
    r"CENTRAL INDEX KEY:\s*(\d+)", re.S | re.I)


def subject_company(cik, accession: str) -> dict:
    """Who the 13D/G is ABOUT. The filer's submissions JSON never says — it only
    lists what the fund filed — so on the HTML path the subject comes from the
    submission header, where EDGAR records it explicitly. Without this an older
    13G lands with no issuer at all and is unusable."""
    url = (fund_sec.ARCHIVE_DIR.format(cik=int(str(cik)),
                                       accn=fund_sec.accn_nodash(accession))
           + f"{accession}-index-headers.html")
    try:
        html = fund_sec.get_text(url)
    except fund_sec.SECError:
        return {}
    m = _SUBJ.search(_text(html).replace("  ", "\n") if html else "") or \
        (_SUBJ.search(html) if html else None)
    if not m:
        return {}
    return {"name": m.group(1).strip(), "cik": m.group(2).zfill(10)}


def _all_numbers(root, names) -> list:
    """Every numeric value carried by any of `names`, anywhere in the document."""
    out = []
    for el in root.iter():
        if _tag(el) in names and (el.text or "").strip():
            try:
                out.append(float(el.text.strip().replace(",", "")))
            except ValueError:
                pass
    return out


def _first(root, names):
    for el in root.iter():
        if _tag(el) in names and (el.text or "").strip():
            return el.text.strip()
    return None


def _norm_date(s):
    if not s:
        return None
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s.strip())
    return f"{m.group(3)}-{m.group(1)}-{m.group(2)}" if m else s.strip()[:10]


def ingest_stakes(con, run_id: str, limit: int = None) -> dict:
    stats = {"filings": 0, "stakes": 0, "events": 0, "failures": [], "html_path": 0}
    rows = fund_ingest.pending(con, forms=sorted(fund.STAKE_FORMS), limit=limit)
    cache = fund_ident.load_map(con)
    for f in rows:
        stats["filings"] += 1
        if stats["filings"] % 50 == 0:
            # A backfill can walk a thousand filings. Committing only at the end
            # means one bad row throws away an hour of rate-limited fetching.
            con.commit()
        try:
            p = parse_stake(f["cik"], f["accession_no"], f["primary_doc"])
        except (fund_sec.SECError, ET.ParseError, ValueError, AttributeError) as exc:
            fund_ingest.mark(con, f["accession_no"], "error", f"13D/G parse: {exc}")
            stats["failures"].append(f"{f['slug']} {f['accession_no']}: {exc}")
            continue
        if not p.get("parse_path"):
            fund_ingest.mark(con, f["accession_no"], "error", "no readable document")
            stats["failures"].append(f"{f['slug']} {f['accession_no']}: no document")
            continue
        if p["parse_path"] == "html":
            stats["html_path"] += 1

        is_d = f["form_type"].startswith("SC 13D")
        issuer = p.get("issuer") or f["accession_no"]
        ticker = None
        if p.get("cusip"):
            ticker = fund_ident.resolve(con, p["cusip"], issuer,
                                        accession=f["accession_no"],
                                        cache=cache)["ticker"]
        intent = p.get("intent_excerpt")
        intent_from = f["accession_no"] if intent else None
        if is_d and not intent:
            prior = con.execute(
                """SELECT intent_excerpt, COALESCE(intent_source_accession, accession_no) src,
                          amendment_no
                   FROM fund_stakes
                   WHERE parent_cik IS ? AND issuer = ? AND intent_excerpt IS NOT NULL
                   ORDER BY filed_at DESC LIMIT 1""",
                (f["parent_cik"], issuer)).fetchone()
            if prior:
                intent, intent_from = prior["intent_excerpt"], prior["src"]
        con.execute(
            """INSERT OR REPLACE INTO fund_stakes
                 (accession_no, cik, parent_cik, form_type, issuer, issuer_cik,
                  cusip, ticker, pct_of_class, shares, event_date, filed_at,
                  is_activist, intent_summary, intent_excerpt,
                  intent_source_accession, amendment_no, source_url)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f["accession_no"], f["cik"], f["parent_cik"], f["form_type"], issuer,
             p.get("issuer_cik"), p.get("cusip"), ticker, p.get("pct_of_class"),
             p.get("shares"), p.get("event_date") or f["filed_at"], f["filed_at"],
             int(is_d),
             (summarize_intent(intent)
              + ("" if intent_from == f["accession_no"] else " [carried forward from "
                 f"{intent_from}]")) if (is_d and intent) else None,
             intent, intent_from, p.get("amendment_no"), p["source_url"]))
        stats["stakes"] += 1

        pct = p.get("pct_of_class")
        head = (f"{'13D' if is_d else '13G'}"
                f"{' amendment ' + p['amendment_no'] if p.get('amendment_no') else ''}"
                f" on {ticker or issuer}"
                + (f" — {pct:.1f}% of class" if pct else "")
                + (f" — intent: {summarize_intent(intent)}" if is_d and intent else ""))
        stats["events"] += fund.add_event(
            con, parent_cik=f["parent_cik"], cik=f["cik"],
            event_date=p.get("event_date") or f["filed_at"],
            disclosed_date=f["filed_at"],
            event_type=("stake_13d_amend" if is_d and p.get("amendment_no")
                        else "stake_13d" if is_d else "stake_13g"),
            headline=head, issuer=issuer, ticker=ticker, cusip=p.get("cusip"),
            magnitude=pct, magnitude_unit="pct_of_class",
            source_form=f["form_type"], accession_no=f["accession_no"],
            source_url=p["source_url"])
        fund_ingest.mark(con, f["accession_no"], "ok",
                         f"{p['parse_path']} path"
                         + (", Item 4 captured" if intent else ", no Item 4 in this filing"))
    con.commit()
    fund.log_run(con, run_id, "stakes", "warn" if stats["failures"] else "ok",
                 f"{stats['stakes']} stakes", stats)
    return stats


# ── Form 3 / 4 / 5 ───────────────────────────────────────────────────────────
def parse_ownership(cik, accession: str, primary_doc: str) -> dict:
    """Ownership XML: the only layer in this system with EXACT trade dates."""
    url = fund_sec.doc_url(cik, accession, primary_doc)
    xml = fund_sec.get_text(url)
    if not xml or "ownershipDocument" not in xml:
        # The primary document is usually the rendered XSL view; the raw XML sits
        # beside it under the same stem.
        alt = re.sub(r"^xsl[^/]*/", "", primary_doc or "")
        url = fund_sec.doc_url(cik, accession, alt)
        xml = fund_sec.get_text(url)
    if not xml or "ownershipDocument" not in xml:
        return {}
    root = ET.fromstring(xml.encode("utf-8", "replace"))
    issuer = _find(root, "issuer")
    rel = _find(root, "reportingOwnerRelationship")
    out = {
        "issuer": _txt(issuer, "issuerName"),
        "issuer_cik": (_txt(issuer, "issuerCik") or "").zfill(10) or None,
        "ticker": _txt(issuer, "issuerTradingSymbol"),
        "is_ten_pct_owner": int((_txt(rel, "isTenPercentOwner", "0") or "0")
                                in ("1", "true")),
        "is_director": int((_txt(rel, "isDirector", "0") or "0") in ("1", "true")),
        "source_url": url, "txns": [],
    }
    for el in root.iter():
        t = _tag(el)
        if t not in ("nonDerivativeTransaction", "derivativeTransaction"):
            continue
        coding = _find(el, "transactionCoding")
        amounts = _find(el, "transactionAmounts")
        post = _find(el, "postTransactionAmounts")
        out["txns"].append({
            "derivative": int(t.startswith("derivative")),
            "security_title": _txt(_find(el, "securityTitle"), "value"),
            "txn_date": (_txt(_find(el, "transactionDate"), "value") or "")[:10] or None,
            "txn_code": _txt(coding, "transactionCode"),
            "shares": _num(_txt(_find(amounts, "transactionShares"), "value")),
            "price": _num(_txt(_find(amounts, "transactionPricePerShare"), "value")),
            "acquired_disposed": _txt(_find(amounts, "transactionAcquiredDisposedCode"),
                                      "value"),
            "post_txn_shares": _num(_txt(
                _find(post, "sharesOwnedFollowingTransaction"), "value")) if post is not None else None,
        })
    return out


def _num(s):
    try:
        return float(str(s).replace(",", ""))
    except (TypeError, ValueError):
        return None


def ingest_insider(con, run_id: str, limit: int = None) -> dict:
    stats = {"filings": 0, "txns": 0, "events": 0, "failures": []}
    rows = fund_ingest.pending(con, forms=sorted(fund.INSIDER_FORMS), limit=limit)
    for f in rows:
        stats["filings"] += 1
        if stats["filings"] % 50 == 0:
            con.commit()
        try:
            p = parse_ownership(f["cik"], f["accession_no"], f["primary_doc"])
        except (fund_sec.SECError, ET.ParseError, ValueError, AttributeError) as exc:
            fund_ingest.mark(con, f["accession_no"], "error", f"ownership parse: {exc}")
            stats["failures"].append(f"{f['slug']} {f['accession_no']}: {exc}")
            continue
        if not p:
            fund_ingest.mark(con, f["accession_no"], "unsupported",
                             "no ownership XML in filing")
            continue
        for t in p["txns"]:
            con.execute(
                """INSERT OR IGNORE INTO fund_insider_txns
                     (accession_no, cik, parent_cik, issuer, issuer_cik, ticker,
                      txn_date, txn_code, acquired_disposed, security_title,
                      derivative, shares, price, post_txn_shares,
                      is_ten_pct_owner, is_director, filed_at, source_url)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (f["accession_no"], f["cik"], f["parent_cik"], p["issuer"],
                 p["issuer_cik"], p["ticker"], t["txn_date"], t["txn_code"],
                 t["acquired_disposed"], t["security_title"], t["derivative"],
                 t["shares"], t["price"], t["post_txn_shares"],
                 p["is_ten_pct_owner"], p["is_director"], f["filed_at"],
                 p["source_url"]))
            stats["txns"] += 1
            if t["txn_code"] in ("P", "S") and t["shares"]:
                verb = "bought" if t["acquired_disposed"] == "A" else "sold"
                stats["events"] += fund.add_event(
                    con, parent_cik=f["parent_cik"], cik=f["cik"],
                    event_date=t["txn_date"] or f["filed_at"],
                    disclosed_date=f["filed_at"], event_type="insider_txn",
                    headline=(f"{verb} {t['shares']:,.0f} {p['ticker'] or p['issuer']}"
                              + (f" at ${t['price']:,.2f}" if t["price"] else "")
                              + " — exact-dated (Form 4)"),
                    issuer=p["issuer"], ticker=p["ticker"],
                    magnitude=(t["shares"] * t["price"]) if t["price"] else None,
                    magnitude_unit="usd" if t["price"] else None,
                    source_form=f["form_type"], accession_no=f["accession_no"],
                    source_url=p["source_url"])
        fund_ingest.mark(con, f["accession_no"], "ok", f"{len(p['txns'])} transactions")
    con.commit()
    fund.log_run(con, run_id, "insider", "warn" if stats["failures"] else "ok",
                 f"{stats['txns']} insider transactions", stats)
    return stats


# ── 8-K ──────────────────────────────────────────────────────────────────────
# Only the items that can carry an activist outcome. An 8-K is mostly earnings
# and officer appointments; storing all of them would bury the ones that matter.
ITEMS_OF_INTEREST = {
    "1.01": "material definitive agreement (may be a settlement or standstill)",
    "5.02": "director/officer change (may be an activist board seat)",
    "8.01": "other events",
    "5.07": "shareholder vote results",
    "2.01": "completion of an acquisition or disposition",
}


def ingest_8k(con, run_id: str, limit: int = None) -> dict:
    stats = {"filings": 0, "events": 0}
    for f in fund_ingest.pending(con, forms=["8-K"], limit=limit):
        stats["filings"] += 1
        items = [i.strip() for i in (f["items"] or "").split(",") if i.strip()]
        hits = [i for i in items if i in ITEMS_OF_INTEREST]
        if not hits:
            fund_ingest.mark(con, f["accession_no"], "skipped",
                             f"8-K items {items or '—'} carry no activist signal")
            continue
        stats["events"] += fund.add_event(
            con, parent_cik=f["parent_cik"], cik=f["cik"],
            event_date=f["period_of_report"] or f["filed_at"],
            disclosed_date=f["filed_at"], event_type="material_8k",
            headline="8-K: " + "; ".join(ITEMS_OF_INTEREST[i] for i in hits),
            source_form="8-K", accession_no=f["accession_no"],
            source_url=f["source_url"])
        fund_ingest.mark(con, f["accession_no"], "ok", f"items {','.join(hits)}")
    con.commit()
    fund.log_run(con, run_id, "8k", "ok", f"{stats['events']} material 8-K events", stats)
    return stats
