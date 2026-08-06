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
CONFIG_DIR = ROOT / "config"
RUNS_DIR = ROOT / "runs"
HANDOFF_DIR = ROOT / "handoff"

# CSV interchange contract (see agents/_TEMPLATE.md). allocator_class is optional.
EVENT_COLUMNS = [
    "event_date", "disclosed_date", "allocator", "allocator_class", "target",
    "target_type", "sector", "subsector", "event_type", "amount_usd",
    "amount_estimated", "status", "source_tier", "source_url", "notes",
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
    return con


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
    }


def sync_allocators(con: sqlite3.Connection, cfg: dict) -> None:
    """Upsert the config watchlist into the allocators table (name is the key)."""
    key_map = {"corporate": "corporate", "vc": "vc", "individuals": "individual",
               "alt_managers": "alt_manager", "sovereigns": "sovereign"}
    allocs = cfg.get("allocators") or {}
    for cfg_class, rows in allocs.items():
        cls = key_map.get(cfg_class)
        if not cls or not rows:
            continue
        for r in rows:
            con.execute(
                """INSERT INTO allocators (name, class, tier, country) VALUES (?,?,?,?)
                   ON CONFLICT(name) DO UPDATE SET
                     class=excluded.class, tier=excluded.tier, country=excluded.country""",
                (r["name"], cls, r.get("tier", "watch"), r.get("country")),
            )
    con.commit()


def get_or_create_allocator(con, name: str, cls: str, tier: str = "watch") -> int:
    """Resolve an allocator name to id, inserting a watch-tier row if unseen."""
    row = con.execute("SELECT id FROM allocators WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = con.execute(
        "INSERT INTO allocators (name, class, tier) VALUES (?,?,?)", (name, cls, tier)
    )
    return cur.lastrowid
