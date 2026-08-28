"""EDGAR client for the Fund Tracker — one door, one rate limiter.

Fair access is not optional here: the SEC asks for a declared User-Agent with a
real contact address and <=10 requests/second, and getting the IP blocked kills
the entire section, not one call. So:

  * the limiter is a module-level token bucket, shared by EVERY caller. Per-caller
    limiting is the classic way to end up at 4x the published rate the moment two
    stages run in the same process.
  * the User-Agent is REQUIRED. With none configured the client refuses to make a
    request instead of sending a plausible-looking fake header. Set
    FUND_SEC_USER_AGENT="Your Name <you@example.com>" or sec.user_agent in
    config/fund_managers.yaml.

Everything returned is a RESOLVED document URL. A full-text-search query URL is
not a citation — Section 2's audit already rejects those and this section holds
the same line.
"""

import gzip
import io
import json
import os
import threading
import time
import urllib.error
import urllib.request

from . import fund

SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
SUBMISSIONS_PAGE = "https://data.sec.gov/submissions/{name}"
INDEX_JSON = "https://www.sec.gov/Archives/edgar/data/{cik}/{accn}/index.json"
ARCHIVE_DIR = "https://www.sec.gov/Archives/edgar/data/{cik}/{accn}/"
COMPANY_TICKERS = "https://www.sec.gov/files/company_tickers.json"
COMPANY_FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
# One fact instead of the entire XBRL history. companyfacts is megabytes per
# issuer; across a thousand issuers that is gigabytes of transfer to read a single
# number, which is both slow and rude to a free public API.
COMPANY_CONCEPT = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{tag}.json"
# Tried in order. dei/EntityCommonStockSharesOutstanding is the cover-page figure
# and the one we want, but companyconcept does not serve it for every registrant,
# so there are two us-gaap fallbacks. Which one answered is recorded in the stored
# source_url — a share count from `SharesIssued` is a slightly different quantity
# from one taken off the cover page, and the row should say which it is.
SHARE_CONCEPTS = (("dei", "EntityCommonStockSharesOutstanding"),
                  ("us-gaap", "CommonStockSharesOutstanding"),
                  ("us-gaap", "CommonStockSharesIssued"))
FULL_TEXT = "https://efts.sec.gov/LATEST/search-index?q={q}&forms={forms}"

MAX_RETRIES = 4
TIMEOUT = 45


class SECError(RuntimeError):
    """A network/transport failure. Callers log it loudly; nothing falls back."""


class SECConfigError(RuntimeError):
    """No usable User-Agent. We do not send a fake one."""


# ── the one limiter ──────────────────────────────────────────────────────────
class _Limiter:
    """Token bucket, thread-safe. Shared across the process by construction."""

    def __init__(self, rate_per_sec: float):
        self.rate = max(0.5, float(rate_per_sec))
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self):
        with self._lock:
            now = time.monotonic()
            due = max(now, self._next)
            self._next = due + 1.0 / self.rate
        delay = due - time.monotonic()
        if delay > 0:
            time.sleep(delay)


_limiter = None
_ua = None
_stats = {"requests": 0, "retries": 0, "errors": 0, "bytes": 0}


def _cfg():
    return (fund.load_managers().get("sec") or {})


def user_agent() -> str:
    """The declared contact header. Raises rather than fabricate one."""
    global _ua
    if _ua:
        return _ua
    ua = os.environ.get("FUND_SEC_USER_AGENT") or _cfg().get("user_agent")
    if not ua or "@" not in str(ua):
        raise SECConfigError(
            "No SEC User-Agent configured. EDGAR requires a declared contact "
            "address (https://www.sec.gov/os/webmaster-faq#developers). Set\n"
            '  export FUND_SEC_USER_AGENT="Your Name <you@example.com>"\n'
            "or fill sec.user_agent in config/fund_managers.yaml. Refusing to "
            "send a fabricated header — a block here takes down the whole section.")
    _ua = str(ua)
    return _ua


def limiter() -> _Limiter:
    global _limiter
    if _limiter is None:
        _limiter = _Limiter(_cfg().get("max_requests_per_second", 8))
    return _limiter


def stats() -> dict:
    return dict(_stats)


def _raw(url: str) -> bytes:
    """One rate-limited GET with backoff. 404 is returned as None (a filing that
    genuinely has no such document); everything else that survives the retries
    raises, because a swallowed error is how a book silently goes half-missing."""
    req = urllib.request.Request(url, headers={
        "User-Agent": user_agent(),
        "Accept-Encoding": "gzip, deflate",
        "Host": url.split("//", 1)[1].split("/", 1)[0],
    })
    last = None
    for attempt in range(MAX_RETRIES):
        limiter().wait()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                _stats["requests"] += 1
                _stats["bytes"] += len(raw)
                return raw
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 404:
                _stats["requests"] += 1
                return None
            if e.code in (403, 429, 500, 502, 503, 504):
                _stats["retries"] += 1
                time.sleep(1.5 * (2 ** attempt))
                continue
            break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            _stats["retries"] += 1
            time.sleep(1.5 * (2 ** attempt))
    _stats["errors"] += 1
    raise SECError(f"{url}: {last}")


def get_json(url: str):
    raw = _raw(url)
    return None if raw is None else json.loads(raw)


def get_text(url: str):
    raw = _raw(url)
    return None if raw is None else raw.decode("utf-8", "replace")


# ── shapes ───────────────────────────────────────────────────────────────────
def accn_nodash(accession: str) -> str:
    return (accession or "").replace("-", "")


def doc_url(cik, accession: str, doc: str) -> str:
    """A resolved filing-document URL — the only citable EDGAR shape."""
    return (ARCHIVE_DIR.format(cik=int(str(cik)), accn=accn_nodash(accession))
            + (doc or ""))


def filing_index(cik, accession: str) -> dict:
    """The filing directory listing — how we find the information table inside a
    13F without guessing its filename (it is not stable across filers)."""
    d = get_json(INDEX_JSON.format(cik=int(str(cik)), accn=accn_nodash(accession)))
    return d or {}


def submissions(cik: str, all_history: bool = False) -> dict:
    """Submissions JSON, flattened to a list of filings.

    `recent` holds roughly the last 1000 filings / 1 year. For the 8-quarter
    backfill that is usually enough, but not always — a quiet filer's 13F history
    can fall off the end. all_history=True walks filings.files[] as well, because
    "we backfilled 8 quarters" must mean 8 quarters, not 8 quarters if convenient.
    """
    cik = str(cik).zfill(10)
    d = get_json(SUBMISSIONS.format(cik=cik))
    if not d:
        raise SECError(f"submissions for CIK{cik}: not found")
    out = {"cik": cik, "name": d.get("name"), "sic": d.get("sicDescription"),
           # The NUMERIC code as well as the label: the sector rules key on the
           # 4-digit code, and sicDescription is free text that EDGAR rewords.
           "sicCode": (d.get("sic") or "").strip() or None,
           "tickers": d.get("tickers") or [], "filings": []}
    pages = [(d.get("filings") or {}).get("recent") or {}]
    if all_history:
        for f in ((d.get("filings") or {}).get("files") or []):
            extra = get_json(SUBMISSIONS_PAGE.format(name=f["name"]))
            if extra:
                pages.append(extra)
    for page in pages:
        forms = page.get("form") or []
        for i, form in enumerate(forms):
            out["filings"].append({
                "cik": cik,
                "form": form,
                "accession": (page.get("accessionNumber") or [None] * len(forms))[i],
                "filed_at": (page.get("filingDate") or [None] * len(forms))[i],
                "period": (page.get("reportDate") or [None] * len(forms))[i] or None,
                "items": (page.get("items") or [None] * len(forms))[i] or None,
                "primary_doc": (page.get("primaryDocument") or [None] * len(forms))[i],
            })
    for f in out["filings"]:
        f["url"] = doc_url(cik, f["accession"], f["primary_doc"])
    out["filings"].sort(key=lambda f: (f["filed_at"] or "", f["accession"] or ""),
                        reverse=True)
    return out


def entity_name(cik: str):
    """EDGAR's own name for a CIK — the seed's verification probe."""
    d = get_json(SUBMISSIONS.format(cik=str(cik).zfill(10)))
    return (d or {}).get("name")


def company_tickers() -> dict:
    """{ticker: {cik, title}} from SEC's own file. The auditable half of the
    CUSIP->ticker map: it gives issuer name -> ticker/CIK, which is what we match
    a 13F `nameOfIssuer` against."""
    d = get_json(COMPANY_TICKERS) or {}
    return {str(v["ticker"]).upper(): {"cik": str(v["cik_str"]).zfill(10),
                                       "title": v["title"]}
            for v in d.values() if v.get("ticker")}


def shares_outstanding(cik: str):
    """Latest common shares outstanding from XBRL company facts. This is the field
    that turns a raw share count into a % of the company — without it a holder row
    is uninterpretable (§8b.5)."""
    for taxonomy, tag in SHARE_CONCEPTS:
        url = COMPANY_CONCEPT.format(cik=str(cik).zfill(10), taxonomy=taxonomy, tag=tag)
        d = get_json(url)
        if not d:
            continue
        best = None
        for unit_rows in (d.get("units") or {}).values():
            for r in unit_rows:
                if r.get("val") and r.get("end") and (best is None or r["end"] > best["end"]):
                    best = r
        if best:
            return {"shares": float(best["val"]), "as_of": best["end"],
                    "source_url": url}
    return None


def full_text_search(query: str, forms: str = None, limit: int = 100) -> list:
    """Cross-reference a fund's name in filings it did NOT file (S-1 Principal
    Stockholders, DEF 14A holder tables). Returns filings, each with a resolved
    document URL — the query URL itself is never emitted as a citation."""
    import urllib.parse
    url = FULL_TEXT.format(q=urllib.parse.quote(f'"{query}"'),
                           forms=urllib.parse.quote(forms or ""))
    d = get_json(url) or {}
    out = []
    for h in (d.get("hits") or {}).get("hits", [])[:limit]:
        s = h.get("_source") or {}
        _id = h.get("_id") or ""
        accn, _, doc = _id.partition(":")
        ciks = s.get("ciks") or []
        out.append({
            "accession": accn, "primary_doc": doc, "form": s.get("root_form"),
            "filed_at": s.get("file_date"),
            "filer_ciks": [str(c).zfill(10) for c in ciks],
            "display_names": s.get("display_names") or [],
            "url": doc_url(ciks[0], accn, doc) if ciks else None,
        })
    return out
