"""Ingest: agent CSVs -> validate -> dedupe -> SQLite.

Reads runs/<week>/<agent>/{verified,candidate}_events.csv + source_log.csv,
validates rows against the schema (sector slug, event_type, tiers), resolves
allocator names to allocators.id (creating watch-tier entries for new names),
and upserts into db/capital.db. The UNIQUE constraint on events is the dedupe
guard; duplicates across agents are merged keeping the highest status/tier.
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "capital.db"
SCHEMA_PATH = ROOT / "db" / "schema.sql"
RUNS_DIR = ROOT / "runs"


def connect() -> sqlite3.Connection:
    """Open the master DB, applying the schema if the file is new."""
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA_PATH.read_text())
    return con


def ingest_week(week: str) -> None:
    """Load all agent outputs for a run week (e.g. '2026-W32') into the DB."""
    raise NotImplementedError("Build step 5: validation")


if __name__ == "__main__":
    import sys
    ingest_week(sys.argv[1])
