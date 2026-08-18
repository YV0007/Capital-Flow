"""Ecosystem verification: is the citation still there?

Once a month every evidence URL is re-fetched and searched for its own quote. This is the
mechanism from §7.4 of the plan — the map shows its own decay instead of quietly lying.

  200 + quote found        -> alive = 1, edge confirmed for this month
  200 + quote NOT found    -> alive = 0 ("the page changed under the citation")
  404 / 410 / DNS failure  -> alive = 0 ("the source is gone")
  403 / 429 / timeout      -> alive UNCHANGED, noted ("we were blocked, not disproved")

The 403/429 carve-out matters: paywalls and bot walls are extremely common on exactly the
Tier-`press` sources this map cites, and treating "blocked" as "false" would dim half the
map for a reason that has nothing to do with the truth of the claim.

An edge with no live evidence left goes `status='unverified'` and dims. Network problems
never crash the run — an offline run simply verifies nothing and says so.
"""

import re
import sys
from datetime import date
from html import unescape

from . import eco

try:
    import requests
except ImportError:                                   # offline / minimal environment
    requests = None

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
# SEC's fair-access policy requires a declaring User-Agent with contact info and rejects
# browser strings outright (https://www.sec.gov/about/developer-resources). Since filings
# are the highest tier of evidence on this map, sending the wrong header would 403 exactly
# the citations that matter most. Same UA as engine/edgar.py.
SEC_UA = "capital-flow research contact@example.com"
SEC_HOSTS = ("sec.gov", "data.sec.gov")


def _ua_for(url: str) -> str:
    host = (url or "").split("//", 1)[-1].split("/", 1)[0].lower()
    return SEC_UA if any(host == h or host.endswith("." + h) for h in SEC_HOSTS) else UA
TIMEOUT = 20
BLOCKED_CODES = {401, 402, 403, 405, 406, 408, 429, 500, 502, 503, 504}
DEAD_CODES = {400, 404, 410, 451}

_TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
_ANYTAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def page_text(html: str) -> str:
    """Strip a page down to comparable text. Deliberately crude — we are looking for one
    sentence, not parsing the document."""
    s = _TAG.sub(" ", html or "")
    s = _ANYTAG.sub(" ", s)
    s = unescape(s)
    return _WS.sub(" ", s).strip()


def normalize(s: str) -> str:
    """Fold the differences that are NOT the citation changing: curly quotes, dashes,
    non-breaking spaces, case, runs of whitespace."""
    s = (s or "").lower()
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("–", "-"), ("—", "-"), ("−", "-"), (" ", " "),
                 ("​", "")):
        s = s.replace(a, b)
    return _WS.sub(" ", re.sub(r"[^\w\s'\"%.,$-]", " ", s)).strip()


def quote_present(text: str, quote: str) -> bool:
    """Exact (normalized) containment first; then a degraded check for a long shared
    prefix, so a page that reflows one sentence does not kill an otherwise good citation.
    Anything looser than this would defeat the purpose of the check."""
    t, q = normalize(text), normalize(quote)
    if not q:
        return False
    if q in t:
        return True
    words = q.split()
    if len(words) >= 12:
        head = " ".join(words[:10])
        tail = " ".join(words[-10:])
        return head in t and tail in t
    return False


def _fetch(url: str):
    """Returns (verdict, note) where verdict is 'ok' | 'dead' | 'blocked' and, when ok,
    note holds the page text."""
    if requests is None:
        return "blocked", "requests not installed"
    try:
        r = requests.get(url, headers={"User-Agent": _ua_for(url), "Accept": "*/*"},
                         timeout=TIMEOUT, allow_redirects=True)
    except Exception as exc:                          # network never crashes the run
        return "blocked", f"{type(exc).__name__}: {str(exc)[:120]}"
    if r.status_code in DEAD_CODES:
        return "dead", f"HTTP {r.status_code}"
    if r.status_code in BLOCKED_CODES or r.status_code >= 400:
        return "blocked", f"HTTP {r.status_code}"
    return "ok", r.text


def run(month: str, offline: bool = False, limit: int = None) -> dict:
    con = eco.connect()
    rules = eco.load_rules()
    stale_months = int((rules.get("staleness") or {}).get("months", 6))
    today = date.today().isoformat()

    rows = con.execute(
        """SELECT id, edge_id, source_url, quote, alive FROM eco_evidence
           ORDER BY id""").fetchall()
    if limit:
        rows = rows[:limit]

    stats = {"checked": 0, "alive": 0, "dead": 0, "blocked": 0, "skipped": 0,
             "unverified_edges": 0, "expired_edges": 0, "stale_nodes": 0}
    seen_cache = {}

    if offline:
        stats["skipped"] = len(rows)
    else:
        for r in rows:
            url = r["source_url"]
            if url not in seen_cache:
                seen_cache[url] = _fetch(url)
            verdict, payload = seen_cache[url]
            stats["checked"] += 1
            if verdict == "ok":
                found = quote_present(page_text(payload), r["quote"])
                con.execute(
                    """UPDATE eco_evidence SET alive=?, last_checked=?, check_note=?
                       WHERE id=?""",
                    (1 if found else 0, today,
                     None if found else "quote not found on the page (200 OK)", r["id"]))
                stats["alive" if found else "dead"] += 1
            elif verdict == "dead":
                con.execute(
                    """UPDATE eco_evidence SET alive=0, last_checked=?, check_note=?
                       WHERE id=?""", (today, payload, r["id"]))
                stats["dead"] += 1
            else:  # blocked — leave `alive` as it was; being walled off is not disproof
                con.execute(
                    """UPDATE eco_evidence SET last_checked=?, check_note=? WHERE id=?""",
                    (today, f"not checked: {payload}", r["id"]))
                stats["blocked"] += 1
        con.commit()

    # Edge status follows its evidence. An edge whose citations are all dead can no
    # longer be proved -> `unverified`, and it dims on the map.
    for e in con.execute("SELECT id, slug, status, ended FROM eco_edges").fetchall():
        live = con.execute(
            "SELECT COUNT(*) c FROM eco_evidence WHERE edge_id=? AND alive=1",
            (e["id"],)).fetchone()["c"]
        total = con.execute(
            "SELECT COUNT(*) c FROM eco_evidence WHERE edge_id=?", (e["id"],)).fetchone()["c"]
        if e["ended"]:
            status = "expired"
        elif total and live == 0:
            status = "unverified"
        else:
            status = "active"
        if status != e["status"]:
            con.execute("UPDATE eco_edges SET status=? WHERE id=?", (status, e["id"]))
        if status == "unverified":
            stats["unverified_edges"] += 1
        if status == "expired":
            stats["expired_edges"] += 1
        if status == "active" and live:
            con.execute("UPDATE eco_edges SET last_confirmed=? WHERE id=?",
                        (month, e["id"]))

    # Node staleness: nothing has confirmed it for N months.
    for n in con.execute("SELECT id FROM eco_nodes").fetchall():
        newest = con.execute(
            """SELECT MAX(last_confirmed) m FROM eco_edges
               WHERE (source_id=? OR target_id=?) AND status='active'""",
            (n["id"], n["id"])).fetchone()["m"]
        stale = 1 if (not newest or eco.months_between(newest, month) > stale_months) else 0
        con.execute("UPDATE eco_nodes SET last_confirmed=?, stale=? WHERE id=?",
                    (newest, stale, n["id"]))
        stats["stale_nodes"] += stale
    con.commit()
    con.close()
    return stats


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    print(run(args[0] if args else eco.current_month(), offline="--offline" in sys.argv))
