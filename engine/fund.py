"""Fund Tracker (Section 3) — shared vocabulary, config and DB access.

Section 2 is discovery-shaped: agents hunt leads and triangulate them into dated
`events`. This section is REGISTRY-shaped: a closed universe of managers whose
positions, stakes and deltas we hold as a standing book. Different question,
different shape, therefore its own tables (all `fund_*`) — nothing here is ever
forced into `events`.

Three invariants this module exists to protect:

  1  The universe is CLOSED. `config/fund_managers.yaml` is the only door in.
     A CIK that is not in the config is logged to fund_unmapped_ciks; it is never
     adopted, never guessed at.
  2  Entity resolution happens HERE, before anything is counted. Point72 files
     under six CIKs and Greenlight under three; without the rollup the same book
     appears three times at a third of its real size and every conviction score
     downstream is wrong.
  3  Quant managers are refused at seed, not filtered later. Their filings are
     model output; letting them in would poison the cross-fund crowding counts
     that the conviction model depends on.
"""

import json
import sqlite3
from datetime import date, datetime, timedelta

import yaml

from . import db

FUND_SCHEMA_PATH = db.ROOT / "db" / "schema_fund.sql"
MANAGERS_CFG = db.CONFIG_DIR / "fund_managers.yaml"
CONVICTION_CFG = db.CONFIG_DIR / "fund_conviction.yaml"
SOURCES_CFG = db.CONFIG_DIR / "fund_sources.yaml"
CUSIP_CFG = db.CONFIG_DIR / "fund_cusip_map.yaml"

# spec §B1. The multiplier is authoritative in config; these are the defaults the
# seed falls back to, and the set the validator checks a config value against.
STYLE_WEIGHT_DEFAULTS = {
    "concentrated": 1.0,      # full trust — the long book IS the conviction
    "activist": 1.0,          # 13D Item 4 is the signal, not the 13F
    "crossover_tech": 0.9,    # trust, but flag the turnover
    "full_disclosure": 1.0,   # the vehicle/letter beats the 13F
    "daily_disclosure": 1.0,  # ARK — the whole book, every day
    "multistrat_mm": 0.0,     # 13F is inventory and hedges. Not conviction.
    "quant": 0.0,             # model output. Not ingested at all.
}
REFUSED_STYLES = {"quant"}

# Forms this section reads, and what each one buys us on the latency ladder.
FORM_LATENCY = {
    "13F-HR":    "quarterly, +45d — the backbone, and the slowest layer",
    "13F-HR/A":  "amendment — often a CONFIDENTIAL-TREATMENT RELEASE. Highest signal.",
    "13F-NT":    "notice: holdings reported by another filer (rollup hint, no positions)",
    "SC 13D":    "~T+5 — activist stake >5% WITH stated intent (Item 4)",
    "SC 13D/A":  "~T+5 — amendment to an activist stake",
    "SC 13G":    "passive >5% crossing",
    "SC 13G/A":  "passive >5% amendment",
    "3":         "became an insider / >10% owner",
    "4":         "~T+2 — exact-dated trade once a fund is an insider or >10% owner",
    "5":         "annual insider true-up",
    "8-K":       "real-time — board changes, activist settlements, standstills",
    "N-PORT-P":  "monthly registered-fund holdings — weeks fresher than a 13F",
    "S-1":       "pre-IPO cap table (Principal Stockholders)",
    "424B4":     "IPO pricing supplement — cap table",
    "DEF 14A":   "annual verified >5% holder table — the 13F cross-check",
}
# EDGAR relabelled the Schedule 13D/G family part-way through its history, so the
# same filing type arrives as "SC 13G" on old rows and "SCHEDULE 13G" on new ones.
# Normalising at the door is the difference between a stake feed and a half-empty
# one that looks fine.
FORM_ALIASES = {
    "SCHEDULE 13D": "SC 13D", "SCHEDULE 13D/A": "SC 13D/A",
    "SCHEDULE 13G": "SC 13G", "SCHEDULE 13G/A": "SC 13G/A",
    "13F-HR/A": "13F-HR/A", "NPORT-P": "N-PORT-P", "NPORT-P/A": "N-PORT-P/A",
}


def norm_form(form: str) -> str:
    f = (form or "").strip().upper()
    return FORM_ALIASES.get(f, f)


POSITION_FORMS = {"13F-HR", "13F-HR/A"}
STAKE_FORMS = {"SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"}
INSIDER_FORMS = {"3", "4", "5", "3/A", "4/A", "5/A"}

# §B3: the disclosures a market maker mechanically cannot produce. A watch-only
# manager enters the section ONLY on one of these.
WATCH_TRIGGER_FORMS = {
    "SC 13D": "13d", "SC 13D/A": "13d", "SC 13G": "13g_crossing",
    "SC 13G/A": "13g_crossing", "4": "form_4", "3": "insider_3",
}


class FundConfigError(RuntimeError):
    """Config is wrong in a way that would produce silently wrong data."""


# ── config ───────────────────────────────────────────────────────────────────
_CFG = None


def load_managers() -> dict:
    """config/fund_managers.yaml, validated. Raises rather than degrade."""
    global _CFG
    if _CFG is not None:
        return _CFG
    if not MANAGERS_CFG.exists():
        raise FundConfigError(f"missing {MANAGERS_CFG}")
    cfg = yaml.safe_load(MANAGERS_CFG.read_text()) or {}
    managers = cfg.get("managers") or []
    watch = cfg.get("watch_only") or []
    if not managers:
        raise FundConfigError("fund_managers.yaml has no managers")
    seen_cik, seen_slug = {}, {}
    for m in managers + watch:
        for f in ("slug", "name", "cik", "style_tag", "focus", "why_tracked",
                  "primary_source"):
            if not m.get(f):
                raise FundConfigError(f"manager {m.get('slug') or m.get('name')}: "
                                      f"missing required field '{f}'")
        if m["style_tag"] not in STYLE_WEIGHT_DEFAULTS:
            raise FundConfigError(f"{m['slug']}: unknown style_tag {m['style_tag']}")
        if m["style_tag"] in REFUSED_STYLES:
            raise FundConfigError(
                f"{m['slug']}: style_tag '{m['style_tag']}' is refused — quant "
                f"filings are model output and must not be ingested (spec §2)")
        cik = str(m["cik"]).zfill(10)
        if cik in seen_cik:
            raise FundConfigError(f"CIK {cik} claimed by both {seen_cik[cik]} and {m['slug']}")
        if m["slug"] in seen_slug:
            raise FundConfigError(f"duplicate slug {m['slug']}")
        seen_cik[cik], seen_slug[m["slug"]] = m["slug"], True
        m["cik"] = cik
    if len(managers) + len(watch) > 20:
        raise FundConfigError("universe over 20 names — this section is deliberately small")
    _CFG = cfg
    return cfg


def load_conviction_cfg() -> dict:
    cfg = yaml.safe_load(CONVICTION_CFG.read_text()) or {}
    total = sum((cfg.get("weights") or {}).values())
    if abs(total - 1.0) > 1e-6:
        raise FundConfigError(f"conviction weights sum to {total}, must be 1.0")
    return cfg


def load_sources_cfg() -> dict:
    return yaml.safe_load(SOURCES_CFG.read_text()) or {}


# ── db ───────────────────────────────────────────────────────────────────────
# Columns added to fund_* tables after the file already existed. CREATE TABLE IF
# NOT EXISTS cannot add them, and a live capital.db is never rebuilt from scratch,
# so they are applied here. Idempotent: only what is missing gets added.
_MIGRATIONS = [
    ("fund_stakes", "intent_source_accession", "TEXT"),
]


def connect() -> sqlite3.Connection:
    """Master DB with the fund schema applied on top. Same file as Sections 1-2;
    entity identity is shared, tables are not."""
    con = db.connect()
    # Stages run long (a backfill walks thousands of rate-limited fetches) and an
    # inspection query or a second stage can overlap one. Without a busy timeout
    # SQLite gives up instantly with "database is locked" and throws away the whole
    # stage's work; 30s of patience costs nothing and avoids that entirely.
    con.execute("PRAGMA busy_timeout = 30000")
    con.executescript(FUND_SCHEMA_PATH.read_text())
    for table, column, decl in _MIGRATIONS:
        have = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
        if have and column not in have:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
    con.commit()
    return con


def log_run(con, run_id: str, stage: str, status: str, detail: str = None,
            stats: dict = None) -> None:
    con.execute(
        """INSERT INTO fund_run_log (run_id, stage, status, detail, stats)
           VALUES (?,?,?,?,?)""",
        (run_id, stage, status, detail, json.dumps(stats or {})))
    con.commit()


def mark_source(con, source: str, ok: bool, error: str = None) -> None:
    """§9: a source that fails must be LOUD and logged, never silently swapped for
    something weaker. The audit turns consecutive failures into a payload warning."""
    now = datetime.utcnow().isoformat(timespec="seconds")
    if ok:
        con.execute(
            """INSERT INTO fund_source_health (source, last_ok_at, checked_at,
                                               consecutive_failures)
               VALUES (?,?,?,0)
               ON CONFLICT(source) DO UPDATE SET last_ok_at=excluded.last_ok_at,
                 checked_at=excluded.checked_at, consecutive_failures=0""",
            (source, now, now))
    else:
        con.execute(
            """INSERT INTO fund_source_health (source, last_error_at, last_error,
                                               checked_at, consecutive_failures)
               VALUES (?,?,?,?,1)
               ON CONFLICT(source) DO UPDATE SET last_error_at=excluded.last_error_at,
                 last_error=excluded.last_error, checked_at=excluded.checked_at,
                 consecutive_failures=fund_source_health.consecutive_failures+1""",
            (source, now, (error or "")[:500], now))
    con.commit()


# ── seed ─────────────────────────────────────────────────────────────────────
def seed(con, verify_names=None) -> dict:
    """Write the config universe into fund_managers + fund_manager_entities.

    verify_names: optional callable cik -> EDGAR name. When supplied, every CIK is
    checked against EDGAR's own name for it and a mismatch is a hard error. A
    transposed digit in a CIK does not fail loudly on its own — it quietly ingests
    a stranger's book — so this check is the difference between a typo and a lie.
    """
    cfg = load_managers()
    stats = {"managers": 0, "watch_only": 0, "entities": 0, "verified": 0,
             "mismatches": []}
    rows = [(m, False) for m in cfg["managers"]] + \
           [(m, True) for m in (cfg.get("watch_only") or [])]

    for m, is_watch in rows:
        cik = m["cik"]
        style = m["style_tag"]
        weight = m.get("conviction_weight", STYLE_WEIGHT_DEFAULTS[style])
        klass = m.get("manager_class") or ("watch_only" if is_watch else "tracked")
        # A watch-only manager's 13F is never ingested — that is the entire point
        # of the carve-out, so it is enforced here rather than trusted downstream.
        ingest_13f = 0 if klass == "watch_only" else int(m.get("ingest_13f", 1))
        con.execute(
            """INSERT INTO fund_managers
                 (cik, slug, name, principal, style_tag, manager_class,
                  conviction_weight, why_tracked, focus, primary_source,
                  primary_source_url, ingest_13f, country, notes, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
               ON CONFLICT(cik) DO UPDATE SET
                 slug=excluded.slug, name=excluded.name, principal=excluded.principal,
                 style_tag=excluded.style_tag, manager_class=excluded.manager_class,
                 conviction_weight=excluded.conviction_weight,
                 why_tracked=excluded.why_tracked, focus=excluded.focus,
                 primary_source=excluded.primary_source,
                 primary_source_url=excluded.primary_source_url,
                 ingest_13f=excluded.ingest_13f, country=excluded.country,
                 notes=excluded.notes, updated_at=datetime('now')""",
            (cik, m["slug"], m["name"], m.get("principal"), style, klass, weight,
             " ".join((m["why_tracked"] or "").split()),
             " ".join((m["focus"] or "").split()), m["primary_source"],
             m.get("primary_source_url"), ingest_13f, m.get("country"),
             " ".join((m.get("notes") or "").split()) or None))
        stats["watch_only" if is_watch else "managers"] += 1

        ents = m.get("entities") or [{"cik": cik, "name": m["name"],
                                      "relationship": "self"}]
        if not any(str(e["cik"]).zfill(10) == cik for e in ents):
            ents = [{"cik": cik, "name": m["name"], "relationship": "self"}] + ents
        for e in ents:
            con.execute(
                """INSERT INTO fund_manager_entities
                     (cik, parent_cik, entity_name, relationship, rollup, poll,
                      source_url, notes)
                   VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(cik) DO UPDATE SET
                     parent_cik=excluded.parent_cik, entity_name=excluded.entity_name,
                     relationship=excluded.relationship, rollup=excluded.rollup,
                     poll=excluded.poll""",
                (str(e["cik"]).zfill(10), cik, e["name"], e.get("relationship", "self"),
                 int(e.get("rollup", True)), int(e.get("poll", True)),
                 e.get("source_url"), e.get("notes")))
            stats["entities"] += 1

    con.commit()

    if verify_names:
        for cik, entity_name in con.execute(
                "SELECT cik, entity_name FROM fund_manager_entities ORDER BY cik"):
            try:
                edgar_name = verify_names(cik)
            except Exception as exc:                      # network/transport
                stats["mismatches"].append(f"{cik}: verification failed ({exc})")
                continue
            if not edgar_name:
                stats["mismatches"].append(f"{cik}: EDGAR returned no name")
            elif not _name_agrees(entity_name, edgar_name):
                stats["mismatches"].append(
                    f"{cik}: config says '{entity_name}', EDGAR says '{edgar_name}'")
            else:
                stats["verified"] += 1
    return stats


_NAME_NOISE = {"llc", "lp", "l.p.", "l.p", "inc", "inc.", "ltd", "ltd.", "corp",
               "corporation", "the", "co", "co.", "plc", "pte", "llp", "lc",
               "limited", "partners", "&", "and", "s.r.l.", "l", "p"}


def _name_agrees(a: str, b: str) -> bool:
    """Loose but not blind: the distinctive tokens of the shorter name must all
    appear in the longer. Catches a wrong CIK; tolerates 'L.P.' vs 'LP'."""
    def toks(s):
        s = (s or "").lower().replace(",", " ").replace("(", " ").replace(")", " ")
        return {t.strip(".") for t in s.split() if t.strip(".") not in _NAME_NOISE
                and len(t.strip(".")) > 1}
    ta, tb = toks(a), toks(b)
    if not ta or not tb:
        return False
    small, big = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return small.issubset(big)


# ── lookups ──────────────────────────────────────────────────────────────────
def parent_of(con, cik: str):
    """Child CIK -> parent manager CIK. None means UNKNOWN, and unknown is logged,
    never adopted (the universe is closed)."""
    r = con.execute("SELECT parent_cik FROM fund_manager_entities WHERE cik=?",
                    (str(cik).zfill(10),)).fetchone()
    return r["parent_cik"] if r else None


def note_unmapped(con, cik: str, name: str = None, seen_in: str = None,
                  note: str = None) -> None:
    con.execute(
        """INSERT OR IGNORE INTO fund_unmapped_ciks (cik, entity_name, seen_in, note)
           VALUES (?,?,?,?)""", (str(cik).zfill(10), name, seen_in, note))


def pollable_ciks(con, include_watch=True) -> list:
    """Every CIK the daily poller should diff, with its parent and class."""
    q = """SELECT e.cik, e.parent_cik, e.entity_name, m.slug, m.name AS manager,
                  m.manager_class, m.ingest_13f, m.style_tag
           FROM fund_manager_entities e
           JOIN fund_managers m ON m.cik = e.parent_cik
           WHERE e.poll = 1 AND m.active = 1"""
    if not include_watch:
        q += " AND m.manager_class != 'watch_only'"
    return [dict(r) for r in con.execute(q + " ORDER BY m.slug, e.cik")]


def managers(con, klass=None) -> list:
    q = "SELECT * FROM fund_managers WHERE active=1"
    args = ()
    if klass:
        q += " AND manager_class=?"
        args = (klass,)
    return [dict(r) for r in con.execute(q + " ORDER BY slug", args)]


# ── periods ──────────────────────────────────────────────────────────────────
def quarter_ends(n: int, today: date = None) -> list:
    """The last n calendar-quarter ends, most recent first. Used to size the
    backfill: the run-now principle says day one already has 8 quarters of
    history, not an empty system waiting two quarters to become useful."""
    d = today or date.today()
    q_end = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    y, q = d.year, (d.month - 1) // 3 + 1
    out = []
    while len(out) < n:
        q -= 1
        if q == 0:
            q, y = 4, y - 1
        m, dd = q_end[q]
        out.append(date(y, m, dd).isoformat())
    return out


def latency_days(event_date: str, disclosed_date: str) -> int:
    """disclosed - event, in days. First-class everywhere: it is the honesty
    mechanism for the latency problem. A 13F 'new position' shown without it is
    actively misleading — the trade may be 4.5 months old and already exited."""
    try:
        a = datetime.fromisoformat(str(event_date)[:10]).date()
        b = datetime.fromisoformat(str(disclosed_date)[:10]).date()
    except (TypeError, ValueError):
        return 0
    return max(0, (b - a).days)


def add_event(con, **kw) -> int:
    """Write one row onto the unified timeline. latency_days is DERIVED here so it
    can never be forgotten by a caller."""
    kw["latency_days"] = latency_days(kw["event_date"], kw["disclosed_date"])
    # These are NOT NULL in the schema, and INSERT OR IGNORE swallows a NOT NULL
    # violation as quietly as a duplicate — so a caller passing None for a flag it
    # does not care about would drop the whole event without a word. Default here.
    for flag in ("is_watch_trigger", "is_flagged"):
        kw[flag] = int(kw.get(flag) or 0)
    cols = ("parent_cik", "cik", "event_date", "disclosed_date", "latency_days",
            "event_type", "headline", "issuer", "ticker", "cusip", "magnitude",
            "magnitude_unit", "conviction_score", "is_watch_trigger", "is_flagged",
            "flag_reason", "source_form", "accession_no", "source_url")
    vals = [kw.get(c) for c in cols]
    cur = con.execute(
        f"INSERT OR IGNORE INTO fund_events ({','.join(cols)}) "
        f"VALUES ({','.join('?' * len(cols))})", vals)
    return cur.rowcount
