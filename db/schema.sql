-- Capital Flow — master schema (SQLite)
-- The events table is the heart of the platform. Everything else hangs off it.

PRAGMA foreign_keys = ON;

-- Who allocates capital. Populated from config/allocators.yaml + discovered along the way.
CREATE TABLE IF NOT EXISTS allocators (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    class         TEXT NOT NULL CHECK (class IN
                    ('corporate','vc','individual','alt_manager','sovereign')),
    tier          TEXT NOT NULL DEFAULT 'watch' CHECK (tier IN ('core','key','watch')),
    network       TEXT,   -- elite-network tag for individuals (paypal_mafia, thiel_extended, …)
    country       TEXT,
    notes         TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One row = one verified or candidate capital allocation event.
CREATE TABLE IF NOT EXISTS events (
    id               INTEGER PRIMARY KEY,
    event_date       TEXT,                -- when the allocation happened (may be approximate)
    disclosed_date   TEXT NOT NULL,       -- when it became known
    allocator_id     INTEGER NOT NULL REFERENCES allocators(id),
    target           TEXT NOT NULL,       -- company/asset/fund receiving capital
    target_type      TEXT CHECK (target_type IN ('private','public','fund','project','asset')),
    sector           TEXT NOT NULL,       -- canonical sector slug (see config/rules.yaml)
    subsector        TEXT,
    event_type       TEXT NOT NULL CHECK (event_type IN
                       ('equity','funding_round','follow_on','acquisition','minority_stake',
                        'fund_launch','spv','grant','project_finance','corporate_investment',
                        'sovereign_investment')),
    amount_usd       REAL,                -- NULL if undisclosed
    amount_estimated INTEGER NOT NULL DEFAULT 0,  -- 1 if amount is an estimate
    status           TEXT NOT NULL DEFAULT 'candidate' CHECK (status IN
                       ('candidate','verified','verified_alpha')),
    source_tier      INTEGER NOT NULL CHECK (source_tier BETWEEN 1 AND 5),
    source_url       TEXT,
    run_week         TEXT NOT NULL,       -- e.g. '2026-W32', which run ingested it
    agent            TEXT NOT NULL,       -- which research agent found it
    notes            TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (allocator_id, target, event_type, disclosed_date)  -- dedupe guard
);

CREATE INDEX IF NOT EXISTS idx_events_sector_date ON events (sector, disclosed_date);
CREATE INDEX IF NOT EXISTS idx_events_allocator   ON events (allocator_id, disclosed_date);
CREATE INDEX IF NOT EXISTS idx_events_status      ON events (status);

-- Source log: every source consulted per run, whether or not it yielded events.
CREATE TABLE IF NOT EXISTS source_log (
    id          INTEGER PRIMARY KEY,
    run_week    TEXT NOT NULL,
    agent       TEXT NOT NULL,
    source_url  TEXT NOT NULL,
    source_tier INTEGER CHECK (source_tier BETWEEN 1 AND 5),
    yielded     INTEGER NOT NULL DEFAULT 0,   -- 1 if it produced at least one event
    checked_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Public-market beneficiaries mapped from private flows.
CREATE TABLE IF NOT EXISTS beneficiaries (
    id          INTEGER PRIMARY KEY,
    event_id    INTEGER NOT NULL REFERENCES events(id),
    ticker      TEXT NOT NULL,
    company     TEXT NOT NULL,
    rationale   TEXT NOT NULL,        -- why this public name benefits from the private flow
    confidence  TEXT NOT NULL DEFAULT 'medium' CHECK (confidence IN ('low','medium','high')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Detected themes: output of the theme engine, one row per (theme, run_week).
CREATE TABLE IF NOT EXISTS themes (
    id          INTEGER PRIMARY KEY,
    run_week    TEXT NOT NULL,
    theme       TEXT NOT NULL,        -- e.g. 'photonics acceleration'
    sector      TEXT NOT NULL,
    rule        TEXT NOT NULL,        -- which rule from config/rules.yaml fired
    evidence    TEXT NOT NULL,        -- JSON array of event ids
    strength    REAL,                 -- rule-defined score
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
