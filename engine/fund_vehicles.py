"""Phase 6 — listed vehicles, Form ADV, track records, and the N-PORT hook.

Three different jobs, joined by one theme: sources that BEAT the 13F.

FORM ADV (automated). What makes the style tagging defensible rather than
arbitrary. Pulling the adviser's own registration record — CRD, legal name, SEC
number, registration status, disciplinary flag — means "Coatue is a crossover
tech manager" is anchored to a public record rather than to an opinion. A manager
with NO ADV record is itself a finding, not an error: the Dodd-Frank family-office
exemption lets a single-family office avoid registration entirely (§8b.3), and
Duquesne is exactly that case.

LISTED VEHICLES (assisted). PSH, TPOU, Greenlight Re and Berkshire publish a full
portfolio and a NAV, and for Greenlight Re that includes actual SHORTS — which no
13F can ever show. These live in investor-relations PDFs and factsheets whose
layout changes without notice. Parsing them blind is how a system starts printing
confidently wrong numbers, so this layer ingests a validated CSV drop under
runs/<period>/fund-vehicles/ instead, refuses any row without a resolvable
source_doc, and — when nothing has been dropped — DECLARES the gap in the payload
rather than letting a 13F fallback quietly stand in for the primary source.

N-PORT (automated, unwired by default). §8b.1: any manager running a registered
fund discloses monthly rather than quarterly, which is why fund complexes carry
filing dates weeks fresher than hedge funds stuck at quarter-end. The parser is
here and runs for any CIK listed under `nport_ciks` in the manager config. None of
the fourteen has one mapped today — ARK is the only registered-fund case and its
daily CSV is strictly better — so the list is empty on purpose, not by omission.
"""

import csv
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

from . import db, fund, fund_sec

ADV_SEARCH = "https://api.adviserinfo.sec.gov/search/firm?query={q}&start=0&hl=true&nrows=5"
ADV_REPORT = "https://reports.adviserinfo.sec.gov/reports/ADV/{crd}/PDF/{crd}.pdf"
UA = "Capital Flow research (fund tracker)"

VEHICLE_COLUMNS = ["vehicle", "as_of", "name", "ticker", "weight", "direction",
                   "source_doc", "note"]
NAV_COLUMNS = ["vehicle", "as_of", "nav_per_share", "currency", "mtd_pct",
               "ytd_pct", "source_doc"]
TRACK_COLUMNS = ["manager", "fiscal_year", "return_pct", "metric", "scope",
                 "source_url", "note"]


# ── Form ADV ─────────────────────────────────────────────────────────────────
_ADV_SUFFIX = re.compile(
    r"[,.]|\b(l\.?l\.?c|l\.?p|llp|inc|ltd|plc|corp|corporation|limited|"
    r"partners|lp)\b", re.I)


def _adv_query(name: str) -> str:
    """IAPD's firm search is literal: it returns nothing for "Coatue Management LLC"
    and the right firm for "Coatue Management". Entity suffixes have to come off the
    QUERY; the match is then verified against the returned names, so loosening the
    search does not loosen what we accept."""
    return " ".join(_ADV_SUFFIX.sub(" ", name or "").split())


def _adv_search(name: str):
    url = ADV_SEARCH.format(q=urllib.parse.quote(_adv_query(name)))
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def pull_adv(con, run_id: str) -> dict:
    """One ADV record per manager. Refresh quarterly; cheap and stable."""
    stats = {"matched": 0, "no_record": [], "errors": []}
    for m in fund.managers(con):
        try:
            d = _adv_search(m["name"])
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                OSError, ValueError) as exc:
            stats["errors"].append(f"{m['slug']}: {exc}")
            continue
        hits = (d.get("hits") or {}).get("hits") or []
        best = None
        for h in hits:
            s = h.get("_source") or {}
            names = [s.get("firm_name")] + list(s.get("firm_other_names") or [])
            if any(fund._name_agrees(m["name"], n) for n in names if n):
                best = s
                break
        if not best:
            # Not a failure. An unregistered manager is a disclosure FACT, and the
            # UI has to say "no ADV on file" rather than leave the card blank as
            # though we simply had not looked.
            stats["no_record"].append(m["slug"])
            con.execute(
                """UPDATE fund_managers SET adv_strategy=?, adv_pulled_at=date('now')
                   WHERE cik=?""",
                ("No Form ADV on file. A single-family office can rely on the "
                 "Dodd-Frank family-office exemption and never register as an "
                 "adviser — absence of a record is not absence of activity.",
                 m["cik"]))
            continue
        crd = str(best.get("firm_source_id") or "")
        con.execute(
            """UPDATE fund_managers SET adv_crd=?, adv_strategy=?, adv_source_url=?,
                 adv_pulled_at=date('now') WHERE cik=?""",
            (crd,
             f"Registered investment adviser {best.get('firm_ia_full_sec_number')}; "
             f"status {best.get('firm_ia_scope')}; "
             f"disclosure events on file: "
             f"{'yes' if best.get('firm_ia_disclosure_fl') == 'Y' else 'no'}.",
             ADV_REPORT.format(crd=crd) if crd else None, m["cik"]))
        stats["matched"] += 1
    con.commit()
    fund.mark_source(con, "form_adv", ok=not stats["errors"],
                     error="; ".join(stats["errors"])[:400] or None)
    fund.log_run(con, run_id, "adv", "warn" if stats["errors"] else "ok",
                 f"{stats['matched']} ADV records, "
                 f"{len(stats['no_record'])} with none on file", stats)
    return stats


# ── listed vehicles (validated CSV drop) ─────────────────────────────────────
def _rows(path, required):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for i, r in enumerate(csv.DictReader(fh), start=2):
            row = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
            missing = [c for c in required if not row.get(c)]
            yield i, row, missing


def ingest_vehicles(con, run_id: str, period: str) -> dict:
    """runs/<period>/fund-vehicles/{holdings,nav,track_record}.csv -> DB.

    Every row must carry a source document URL. A holding without one is rejected
    with its line number, exactly as an unsourced flow is rejected in Section 2 —
    an unsourced position is a claim, not a record.
    """
    d = db.RUNS_DIR / period / "fund-vehicles"
    stats = {"holdings": 0, "nav": 0, "track": 0, "rejected": [], "present": d.is_dir()}
    cfg_vehicles = fund.load_sources_cfg().get("vehicles") or {}
    slug_by_vehicle = {k: v.get("manager") for k, v in cfg_vehicles.items()}
    cik_by_slug = {m["slug"]: m["cik"] for m in fund.managers(con)}

    if not d.is_dir():
        fund.log_run(con, run_id, "vehicles", "skipped",
                     f"no {d} — listed-vehicle layer not supplied this period; "
                     f"the payload declares this as a coverage gap", stats)
        return stats

    h = d / "holdings.csv"
    if h.exists():
        for line, r, missing in _rows(h, ["vehicle", "as_of", "name", "source_doc"]):
            if missing:
                stats["rejected"].append(f"holdings.csv:{line} missing {missing}")
                continue
            if not r["source_doc"].startswith("http"):
                stats["rejected"].append(
                    f"holdings.csv:{line} source_doc is not a resolvable URL")
                continue
            direction = (r.get("direction") or "long").lower()
            if direction not in ("long", "short"):
                stats["rejected"].append(f"holdings.csv:{line} direction={direction}")
                continue
            parent = cik_by_slug.get(slug_by_vehicle.get(r["vehicle"]))
            con.execute(
                """INSERT OR REPLACE INTO fund_vehicle_holdings
                     (parent_cik, vehicle, as_of, name, ticker, weight, direction,
                      source_doc, note)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (parent, r["vehicle"], r["as_of"], r["name"], r.get("ticker") or None,
                 float(r["weight"]) if r.get("weight") else None, direction,
                 r["source_doc"], r.get("note") or None))
            stats["holdings"] += 1
            if direction == "short":
                # The reason these vehicles are the primary source: a disclosed
                # short is information the 13F cannot carry at all.
                fund.add_event(
                    con, parent_cik=parent, event_date=r["as_of"],
                    disclosed_date=r["as_of"], event_type="vehicle_update",
                    headline=f"{r['vehicle']} discloses a SHORT in {r['name']}"
                             + (f" ({float(r['weight']):.1f}% of the book)"
                                if r.get("weight") else ""),
                    issuer=r["name"], ticker=r.get("ticker") or None,
                    source_form=r["vehicle"], source_url=r["source_doc"])

    n = d / "nav.csv"
    if n.exists():
        for line, r, missing in _rows(n, ["vehicle", "as_of", "source_doc"]):
            if missing:
                stats["rejected"].append(f"nav.csv:{line} missing {missing}")
                continue
            con.execute(
                """INSERT OR REPLACE INTO fund_vehicle_nav
                     (vehicle, as_of, nav_per_share, currency, mtd_pct, ytd_pct,
                      source_doc) VALUES (?,?,?,?,?,?,?)""",
                (r["vehicle"], r["as_of"],
                 float(r["nav_per_share"]) if r.get("nav_per_share") else None,
                 r.get("currency") or None,
                 float(r["mtd_pct"]) if r.get("mtd_pct") else None,
                 float(r["ytd_pct"]) if r.get("ytd_pct") else None, r["source_doc"]))
            stats["nav"] += 1

    t = d / "track_record.csv"
    if t.exists():
        cur_fy = str(date.today().year)
        for line, r, missing in _rows(t, ["manager", "fiscal_year", "source_url"]):
            if missing:
                stats["rejected"].append(f"track_record.csv:{line} missing {missing}")
                continue
            parent = cik_by_slug.get(r["manager"])
            if not parent:
                stats["rejected"].append(
                    f"track_record.csv:{line} unknown manager '{r['manager']}'")
                continue
            fy = r["fiscal_year"]
            # Same convention as the Section-2 allocator panel: a YTD or
            # current-year figure is provisional, always, no exceptions.
            provisional = int(fy.upper().startswith("YTD") or fy == cur_fy)
            con.execute(
                """INSERT INTO fund_track_record
                     (parent_cik, fiscal_year, metric, scope, return_pct,
                      is_provisional, source_url, note)
                   VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(parent_cik, fiscal_year, metric, scope) DO UPDATE SET
                     return_pct=excluded.return_pct,
                     is_provisional=excluded.is_provisional,
                     source_url=excluded.source_url, note=excluded.note""",
                (parent, fy, r.get("metric") or "net_return_pct", r.get("scope") or "",
                 float(r["return_pct"]) if r.get("return_pct") else None,
                 provisional, r["source_url"], r.get("note") or None))
            stats["track"] += 1

    con.commit()
    fund.log_run(con, run_id, "vehicles",
                 "warn" if stats["rejected"] else "ok",
                 f"{stats['holdings']} holdings, {stats['nav']} NAV, "
                 f"{stats['track']} track-record rows", stats)
    return stats


def coverage_gaps(con) -> list:
    """What this section knows it is NOT seeing. Emitted with the payload so the
    dashboard can state the gap instead of implying completeness."""
    gaps = []
    src = fund.load_sources_cfg()
    for name, v in (src.get("vehicles") or {}).items():
        have = con.execute("SELECT COUNT(*) c FROM fund_vehicle_holdings WHERE vehicle=?",
                           (name,)).fetchone()["c"]
        if not have:
            gaps.append({
                "layer": f"vehicle:{name}", "manager": v.get("manager"),
                "status": "no data",
                "why": ("published as investor-relations documents whose layout is "
                        "not machine-stable; supply runs/<period>/fund-vehicles/"
                        "holdings.csv to fill it"),
                "effect": ("this manager falls back to the 13F, which is up to 4.5 "
                           "months stale and cannot show shorts or non-US names"),
                "source": v.get("site")})
    for name, r in (src.get("short_registers") or {}).items():
        if not r.get("enabled"):
            gaps.append({"layer": f"short_register:{name}", "status": "disabled",
                         "why": r.get("note"), "effect":
                         "named shorts in this jurisdiction are not visible",
                         "source": r.get("url")})
    for name, r in (src.get("non_us_registers") or {}).items():
        if not r.get("enabled"):
            gaps.append({"layer": f"non_us:{name}", "status": "not built",
                         "why": f"threshold {r.get('threshold_pct')} via {r.get('source')}",
                         "effect": ("holdings in this market are invisible — EDGAR "
                                    "only sees US-listed securities"),
                         "source": None})
    gaps.append({"layer": "form_pf", "status": "inaccessible",
                 "why": (src.get("dead_ends") or {}).get("form_pf", {}).get("note"),
                 "effect": "no path exists; not a gap to close", "source": None})
    return gaps


# ── N-PORT-P (§8b.1) ─────────────────────────────────────────────────────────
def parse_nport(cik, accession: str) -> list:
    """Monthly registered-fund holdings. Same shape as a 13F line but weeks fresher."""
    url = fund_sec.doc_url(cik, accession, "primary_doc.xml")
    xml = fund_sec.get_text(url)
    if not xml or "invstOrSec" not in xml:
        return []
    root = ET.fromstring(xml.encode("utf-8", "replace"))
    out = []
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] != "invstOrSec":
            continue
        g = {c.tag.rsplit("}", 1)[-1]: (c.text or "").strip() for c in el}
        try:
            out.append({"issuer": g.get("name"), "cusip": (g.get("cusip") or "").upper(),
                        "shares": float(g.get("balance") or 0),
                        "value_usd": float(g.get("valUSD") or 0),
                        "pct": float(g.get("pctVal") or 0), "source_url": url})
        except ValueError:
            continue
    return out
