"""Shared DB + config helpers for the engine.

Paths are repo-relative but overridable via env for testing:
  CAPITAL_DB    -> path to the SQLite file (default db/capital.db)
"""

import os
import sqlite3
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("CAPITAL_DB", ROOT / "db" / "capital.db"))
SCHEMA_PATH = ROOT / "db" / "schema.sql"
# The monthly ecosystem pipeline lives in the SAME database file — entity identity
# is shared (NVIDIA must be one NVIDIA on every map). Its tables are all nveco_*.
# The v1 eco_* tables stay in the file as history; their schema now lives in
# archive/ecosystem-v1/ and is no longer applied on connect.
ECO_SCHEMA_PATH = ROOT / "db" / "schema_nveco.sql"
CONFIG_DIR = ROOT / "config"
RUNS_DIR = ROOT / "runs"
HANDOFF_DIR = ROOT / "handoff"

# CSV interchange contract (see agents/_TEMPLATE.md). allocator_class is optional.
EVENT_COLUMNS = [
    "event_date", "disclosed_date", "allocator", "allocator_class", "target",
    "target_type", "sector", "subsector", "event_type", "amount_usd",
    "amount_estimated", "status", "source_tier", "source_url", "origin_id", "theme",
    # C3 structured detail (optional — fill what the source supports)
    "capital_role", "instrument", "stage", "round_total_usd", "ownership_pct",
    "valuation_usd", "co_investors", "notes",
]

EVENT_TYPES = {
    "equity", "funding_round", "follow_on", "acquisition", "minority_stake",
    "fund_launch", "spv", "grant", "project_finance", "corporate_investment",
    "sovereign_investment",
}
TARGET_TYPES = {"private", "public", "fund", "project", "asset"}
STATUSES = {"candidate", "verified", "verified_alpha"}
STATUS_RANK = {"candidate": 0, "verified_alpha": 1, "verified": 2}
CLASSES = {"corporate", "vc", "individual", "alt_manager", "sovereign"}

# runs/<week>/<agent>/ dir name -> allocator class. filings has no fixed class.
AGENT_CLASS = {
    "corporate": "corporate", "vc": "vc", "individuals": "individual",
    "alt-managers": "alt_manager", "alt_managers": "alt_manager",
    "sovereigns": "sovereign", "filings": None,
}


def connect() -> sqlite3.Connection:
    """Open the master DB, applying the schema if the file is new."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA_PATH.read_text())
    if ECO_SCHEMA_PATH.exists():
        con.executescript(ECO_SCHEMA_PATH.read_text())
    _migrate(con)
    return con


def _migrate(con: sqlite3.Connection) -> None:
    """Add columns to existing tables that CREATE TABLE IF NOT EXISTS can't (the
    file predates them). Idempotent — only adds what's missing."""
    uc = {r[1] for r in con.execute("PRAGMA table_info(universe_candidates)")}
    if "status" not in uc:
        con.execute("ALTER TABLE universe_candidates ADD COLUMN status TEXT "
                    "NOT NULL DEFAULT 'new'")
    if "decided_at" not in uc:
        con.execute("ALTER TABLE universe_candidates ADD COLUMN decided_at TEXT")
    # Structured entity anchor on signals (target:/ticker:/alloc:) so a signal can
    # be pinned to a company node, not just a sector zone.
    th = {r[1] for r in con.execute("PRAGMA table_info(themes)")}
    if "entity_id" not in th:
        con.execute("ALTER TABLE themes ADD COLUMN entity_id TEXT")
    con.commit()


def load_config() -> dict:
    """Load the three config YAMLs into one dict."""
    def _load(name):
        p = CONFIG_DIR / name
        return yaml.safe_load(p.read_text()) or {} if p.exists() else {}
    rules = _load("rules.yaml")
    return {
        "allocators": _load("allocators.yaml"),
        "sources": _load("sources.yaml"),
        "rules": rules.get("rules", []),
        "sectors": set(rules.get("sectors") or []),
        "themes": set(rules.get("themes") or []),
        "theme_defaults": rules.get("theme_defaults") or {},
        "subsectors": rules.get("subsectors") or {},
        "subsector_aliases": rules.get("subsector_aliases") or {},
    }


def _normalize(name: str) -> str:
    return " ".join((name or "").lower().split())


_ALIAS_CACHE = None


def load_aliases() -> dict:
    """{normalized_alias: canonical_name} from config/aliases.yaml (cached)."""
    global _ALIAS_CACHE
    if _ALIAS_CACHE is not None:
        return _ALIAS_CACHE
    p = CONFIG_DIR / "aliases.yaml"
    out = {}
    if p.exists():
        for canonical, aliases in (yaml.safe_load(p.read_text()) or {}).items():
            for a in (aliases or []):
                out[_normalize(a)] = canonical
            out[_normalize(canonical)] = canonical  # canonical maps to itself
    _ALIAS_CACHE = out
    return out


def resolve_name(name: str) -> str:
    """Route an alias to its canonical allocator name; passthrough if unknown."""
    return load_aliases().get(_normalize(name), name)


def load_promoted() -> list:
    """config/promoted.yaml → [{name, class, tier, country, promoted_on}] (the
    candidates the user accepted in the weekly review)."""
    p = CONFIG_DIR / "promoted.yaml"
    if not p.exists():
        return []
    return (yaml.safe_load(p.read_text()) or {}).get("promoted") or []


def load_external_ids() -> dict:
    """config/external_ids.yaml → {allocator_name: {cik, ticker}} (SEC-resolved by
    tools/enrich_ids.py). Committed so a DB rebuild restores CIKs offline — without
    this the EDGAR tool loses its deterministic pull-by-CIK path after every rebuild."""
    p = CONFIG_DIR / "external_ids.yaml"
    if not p.exists():
        return {}
    return (yaml.safe_load(p.read_text()) or {}).get("external_ids") or {}


def load_networks() -> dict:
    """Load config/networks.yaml → {members: [...], rules: [...]}."""
    p = CONFIG_DIR / "networks.yaml"
    if not p.exists():
        return {"members": [], "rules": []}
    d = yaml.safe_load(p.read_text()) or {}
    return {"members": d.get("members") or [], "rules": d.get("network_signal_rules") or []}


def _upsert_allocator(con, name, cls, tier, country, network):
    con.execute(
        """INSERT INTO allocators (name, class, tier, country, network) VALUES (?,?,?,?,?)
           ON CONFLICT(name) DO UPDATE SET
             class=excluded.class, tier=excluded.tier, country=excluded.country,
             network=COALESCE(excluded.network, allocators.network)""",
        (name, cls, tier, country, network),
    )


def sync_allocators(con: sqlite3.Connection, cfg: dict) -> None:
    """Upsert the config watchlist into the allocators table (name is the key).
    allocators.yaml first, then networks.yaml members (which enrich individuals
    with a network tag and win on tier)."""
    key_map = {"corporate": "corporate", "vc": "vc", "individuals": "individual",
               "alt_managers": "alt_manager", "sovereigns": "sovereign"}
    allocs = cfg.get("allocators") or {}
    for cfg_class, rows in allocs.items():
        cls = key_map.get(cfg_class)
        if not cls or not rows:
            continue
        for r in rows:
            _upsert_allocator(con, r["name"], cls, r.get("tier", "watch"),
                              r.get("country"), None)
    members = load_networks()["members"]
    for m in members:
        _upsert_allocator(con, m["name"], "individual", m.get("tier", "watch"),
                          m.get("country"), m.get("network"))
    # Promoted candidates (accepted in the weekly Monday review). Tracked from the
    # next run, exactly like a seed-watchlist name — never auto-promoted.
    for r in (load_promoted() or []):
        if r.get("class") in CLASSES:
            _upsert_allocator(con, r["name"], r["class"], r.get("tier", "watch"),
                              r.get("country"), None)
    # Restore SEC-resolved external ids (CIK/ticker) offline, so a rebuilt DB keeps
    # the EDGAR tool's deterministic pull-by-CIK path.
    for ename, ids in load_external_ids().items():
        row = con.execute("SELECT id FROM allocators WHERE name = ?", (ename,)).fetchone()
        if not row:
            continue
        for kind in ("cik", "ticker"):
            if ids.get(kind):
                con.execute(
                    """INSERT OR IGNORE INTO entity_external_ids (allocator_id, kind, value)
                       VALUES (?,?,?)""", (row["id"], kind, str(ids[kind])))
    # Persist aliases (for inspection/audit) and seed principal -> vehicle links.
    for norm_alias, canonical in load_aliases().items():
        con.execute("INSERT OR REPLACE INTO entity_aliases (alias, canonical_name) VALUES (?,?)",
                    (norm_alias, canonical))
    for m in members:
        vehicles = m.get("associated_vehicles") or []
        if not vehicles:
            continue
        row = con.execute("SELECT id FROM allocators WHERE name = ?", (m["name"],)).fetchone()
        if not row:
            continue
        for v in vehicles:
            if v in ("personal_investments", "affiliated_corporate_vehicle",
                     "personal_or_new_vehicle"):
                continue
            con.execute(
                """INSERT OR IGNORE INTO entity_relationships (parent_id, child_name, kind)
                   VALUES (?,?,?)""", (row["id"], v, "vehicle"))
    con.commit()


def get_or_create_allocator(con, name: str, cls: str, tier: str = "watch") -> int:
    """Resolve an allocator name (through aliases) to an id, inserting if unseen."""
    name = resolve_name(name)
    row = con.execute("SELECT id FROM allocators WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = con.execute(
        "INSERT INTO allocators (name, class, tier) VALUES (?,?,?)", (name, cls, tier)
    )
    return cur.lastrowid
