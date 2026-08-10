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

-- Entity resolution (docs/ENHANCEMENT_STRATEGY.md WS4). allocators is the canonical
-- entity table; these satellites route aliases to it, attach external IDs, and link
-- principals to their vehicles / parents to subsidiaries.
CREATE TABLE IF NOT EXISTS entity_aliases (
    alias          TEXT PRIMARY KEY,        -- normalized (lower, single-spaced) alias
    canonical_name TEXT NOT NULL            -- the allocators.name it resolves to
);

CREATE TABLE IF NOT EXISTS entity_external_ids (
    allocator_id INTEGER NOT NULL REFERENCES allocators(id),
    kind         TEXT NOT NULL CHECK (kind IN ('lei','cik','ticker','opencorporates')),
    value        TEXT NOT NULL,
    UNIQUE (allocator_id, kind, value)
);

CREATE TABLE IF NOT EXISTS entity_relationships (
    parent_id  INTEGER NOT NULL REFERENCES allocators(id),
    child_name TEXT NOT NULL,               -- vehicle / subsidiary (may not be its own allocator)
    kind       TEXT NOT NULL,               -- 'vehicle' | 'subsidiary' | 'fund'
    UNIQUE (parent_id, child_name, kind)
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
    theme            TEXT,                -- cross-cutting theme, orthogonal to sector (WS5)
    event_type       TEXT NOT NULL CHECK (event_type IN
                       ('equity','funding_round','follow_on','acquisition','minority_stake',
                        'fund_launch','spv','grant','project_finance','corporate_investment',
                        'sovereign_investment')),
    amount_usd       REAL,                -- NULL if undisclosed
    amount_estimated INTEGER NOT NULL DEFAULT 0,  -- 1 if amount is an estimate
    -- Structured deal detail (C3/WS3) — makes events comparable, not just readable.
    capital_role     TEXT,                -- lead | participant | sole
    instrument       TEXT,                -- equity | debt | convertible | grant | jv | safe
    stage            TEXT,                -- seed | series a..x | growth | buyout
    round_total_usd  REAL,                -- the full round (vs this allocator's slice)
    ownership_pct    REAL,
    valuation_usd    REAL,
    co_investors     TEXT,                -- free text / comma list
    status           TEXT NOT NULL DEFAULT 'candidate' CHECK (status IN
                       ('candidate','verified','verified_alpha')),
    source_tier      INTEGER NOT NULL CHECK (source_tier BETWEEN 1 AND 5),
    source_url       TEXT,
    -- Admiralty-style two-axis confidence (see docs/ENHANCEMENT_STRATEGY.md §6).
    -- reliability A–E ← source tier; credibility 1–5 ← status/corroboration; score 0–100.
    source_reliability TEXT CHECK (source_reliability IN ('A','B','C','D','E')),
    info_credibility   INTEGER CHECK (info_credibility BETWEEN 1 AND 5),
    confidence_score   INTEGER,
    origin_id          TEXT,               -- claim origin (circular-reporting guard; agent-set later)
    run_week         TEXT NOT NULL,       -- e.g. '2026-W32', which run ingested it
    agent            TEXT NOT NULL,       -- which research agent found it
    notes            TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (allocator_id, target, event_type, disclosed_date)  -- dedupe guard
);

CREATE INDEX IF NOT EXISTS idx_events_sector_date ON events (sector, disclosed_date);
CREATE INDEX IF NOT EXISTS idx_events_allocator   ON events (allocator_id, disclosed_date);
CREATE INDEX IF NOT EXISTS idx_events_status      ON events (status);

-- New allocators discovered co-investing with tracked names — the self-extending
-- universe (docs/ENHANCEMENT_STRATEGY.md WS1). You promote these to the watchlist.
CREATE TABLE IF NOT EXISTS universe_candidates (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    suggested_class TEXT,
    seen_with       TEXT,               -- the tracked allocator it co-invested with
    rationale       TEXT,
    run_week        TEXT NOT NULL,
    agent           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (name, run_week)
);

-- Leads (WS2/C7): raw signals — a filing hit, a rumor — that an agent should chase.
-- Nothing is dropped silently; a lead is either promoted to an event or dismissed
-- with a reason, so due diligence is auditable.
CREATE TABLE IF NOT EXISTS leads (
    id          INTEGER PRIMARY KEY,
    source      TEXT NOT NULL,          -- 'edgar' | 'agent' | 'manual'
    entity      TEXT,                   -- allocator/company the lead concerns
    form_type   TEXT,                   -- 8-K, D, 13D/G, 4 ... when from a filing
    title       TEXT,
    url         TEXT,
    filed_date  TEXT,
    status      TEXT NOT NULL DEFAULT 'new'
                  CHECK (status IN ('new','investigating','promoted','dismissed')),
    resolution  TEXT,                   -- why dismissed / which event it became
    run_week    TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (url, entity)
);

-- Coverage (C5/WS2): what each agent actually checked per allocator, per run —
-- the expected-vs-found reconciliation that makes "we didn't miss it" measurable.
CREATE TABLE IF NOT EXISTS coverage (
    run_week     TEXT NOT NULL,
    agent        TEXT NOT NULL,
    allocator    TEXT NOT NULL,
    sources_checked INTEGER DEFAULT 0,
    events_found INTEGER DEFAULT 0,
    checked_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (run_week, agent, allocator)
);

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

-- Canonical allocator intelligence (spec §5, Cluster C). One row per allocator —
-- reused by the dashboard's aggregates AND its detail panel. Researched by the
-- allocator-profiler agent; ingested by engine/profiles.py. Text fields are
-- source-attributed via sources (JSON array of URLs) + strategy_source_url.
CREATE TABLE IF NOT EXISTS allocator_profiles (
    allocator_id        INTEGER PRIMARY KEY REFERENCES allocators(id),
    background          TEXT,     -- who they are: history, scale, position
    focus               TEXT,     -- what they invest in
    style               TEXT,     -- how they invest (concentration, stage, pace)
    thesis              TEXT,     -- their stated worldview / rationale
    latest_summary      TEXT,     -- the logic behind recent decisions
    strategy            TEXT,     -- strategy from their own site / public statements
    strategy_source_url TEXT,     -- where strategy was scraped from (attribution)
    sources             TEXT,     -- JSON array of source URLs backing the profile
    track_record_note   TEXT,     -- honesty note when return data is sparse/absent
    as_of               TEXT NOT NULL,   -- research date
    run_week            TEXT NOT NULL,   -- which run produced/refreshed it
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Track record per allocator per fiscal year (spec §5). Never invented: rows exist
-- only where a source supports them. provisional=1 for YTD / unaudited / estimates.
CREATE TABLE IF NOT EXISTS track_records (
    id           INTEGER PRIMARY KEY,
    allocator_id INTEGER NOT NULL REFERENCES allocators(id),
    fiscal_year  TEXT NOT NULL,    -- '2021'..'2025', or 'YTD2026'
    metric       TEXT NOT NULL,    -- stock_total_return_pct | fund_net_return_pct |
                                   -- fund_gross_return_pct | fund_irr_pct | tvpi |
                                   -- reported_return_pct | aum_usd_bn | hit_rate_pct | moic
    scope        TEXT NOT NULL DEFAULT '',  -- segment/fund/program when one allocator
                                   -- reports several series (e.g. 'Infrastructure',
                                   -- 'BREIT', 'CHIPS Act'); '' = the allocator overall
    value        REAL,
    unit         TEXT,             -- 'pct' | 'x' | 'usd_bn'
    provisional  INTEGER NOT NULL DEFAULT 0,  -- 1 = YTD / unaudited / estimate
    source_tier  INTEGER CHECK (source_tier BETWEEN 1 AND 5),
    source_url   TEXT,
    notes        TEXT,
    run_week     TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (allocator_id, fiscal_year, metric, scope)
);

-- Target references (spec §5 extension): what each TARGET entity is — the
-- engine-owned replacement for the dashboard's hand-curated entityReference.json.
-- Researched by agents/target-profiler.md; ingested by engine/references.py;
-- emitted as description/links on target nodes in the handoff (which the
-- dashboard treats as taking precedence over its local file).
CREATE TABLE IF NOT EXISTS target_references (
    target        TEXT PRIMARY KEY,   -- exact events.target string
    description   TEXT NOT NULL,      -- 1-3 sentences: what it is, who's behind it
    website       TEXT,               -- official site (null for projects with none)
    read_more_url TEXT,               -- ONE good article to read about it
    read_more_label TEXT,             -- publication name for the link
    sources       TEXT,               -- JSON array of URLs consulted
    as_of         TEXT NOT NULL,
    run_week      TEXT NOT NULL,
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Fund / firm PORTFOLIOS (holdings task). The map shows LP money flowing INTO a
-- fund vehicle; this is the layer BELOW — the companies the fund itself deploys
-- into. Researched by agents/holdings-profiler.md, ingested by engine/holdings.py,
-- emitted on fund + firm nodes in the handoff. Cumulative (upsert, never drop).
CREATE TABLE IF NOT EXISTS portfolios (
    entity         TEXT PRIMARY KEY,   -- fund/firm name; matches an allocator name or a target label
    portfolio_url  TEXT,               -- DIRECT link to this entity's portfolio listing (not homepage)
    holdings_count INTEGER,            -- TRUE total known holdings (may exceed stored rows if capped)
    as_of          TEXT NOT NULL,
    run_week       TEXT NOT NULL,
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One row = one portfolio company a fund/firm backs. Facts only, every one sourced
-- (audit treats an unsourced holding as a violation, like an unsourced flow).
CREATE TABLE IF NOT EXISTS holdings (
    id          INTEGER PRIMARY KEY,
    entity      TEXT NOT NULL,        -- the fund/firm that holds it
    name        TEXT NOT NULL,        -- portfolio company (byte-identical to a node label when tracked)
    sector      TEXT,                 -- canonical sector slug (for dashboard color/grouping)
    subsector   TEXT,                 -- per-deal subsector slug
    note        TEXT,                 -- <=120 chars: what the company IS
    stake       TEXT,                 -- '% or $' if disclosed, kept verbatim; else NULL
    lead        INTEGER NOT NULL DEFAULT 0,  -- 1 if the fund led the round
    rank        INTEGER,              -- display order, most-notable/largest first (1 = top)
    as_of       TEXT,
    source_url  TEXT NOT NULL,        -- every holding is sourced
    run_week    TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (entity, name)
);
CREATE INDEX IF NOT EXISTS idx_holdings_entity ON holdings (entity, rank);

-- Dated backers (deal-classifier). Explodes a funding round into ONE dated edge
-- per participating allocator — the data the dashboard needs for lead-time (who
-- entered before the crowd) and bellwether pull (how many quality backers
-- followed). Kept SEPARATE from events so the capital ledger stays pristine:
-- events = capital actually moved (research agents); round_backers = participation
-- metadata (classifier). handoff merges both into dated flow edges.
CREATE TABLE IF NOT EXISTS round_backers (
    id          INTEGER PRIMARY KEY,
    round_id    TEXT NOT NULL,        -- groups co-participants of one round
    target      TEXT NOT NULL,        -- the company raising (matches an events.target / node label)
    allocator   TEXT NOT NULL,        -- canonical allocator name (resolved through aliases)
    role        TEXT CHECK (role IN ('lead','co-lead','participant','follow-on')),
    entry_date  TEXT,                 -- that allocator's entry (round's disclosed date if unknown)
    amount_usd  REAL,                 -- this backer's slice, NULL if undisclosed (no double-count)
    status      TEXT NOT NULL DEFAULT 'candidate',
    source_tier INTEGER CHECK (source_tier BETWEEN 1 AND 5),
    source_url  TEXT,
    provisional INTEGER NOT NULL DEFAULT 0,  -- 1 when entry_date is the round date, not the backer's
    run_week    TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (round_id, allocator)      -- one edge per allocator per round
);
CREATE INDEX IF NOT EXISTS idx_round_backers_target ON round_backers (target);

-- Per-target deep classification (deal-classifier). Lights up the dashboard's
-- Rank-1 (Interesting deals) factors: realized outcome / valuation trail
-- (strike-rate), listing status + public proxies (actionable path), and
-- ai_posture (moat / AI-resilience). Facts only, every asserted block sourced.
CREATE TABLE IF NOT EXISTS target_classification (
    target               TEXT PRIMARY KEY,   -- matches events.target / node label
    -- outcome / valuation trail
    outcome_status       TEXT CHECK (outcome_status IN
                           ('active','up_round','ipo','acquired','shut_down')),
    entry_valuation_usd  REAL,               -- earliest tracked round post-money
    latest_valuation_usd REAL,               -- latest post-money / market cap / deal price
    latest_as_of         TEXT,
    step_up_multiple     REAL,               -- latest / entry, when both known
    outcome_source_url   TEXT,
    outcome_provisional  INTEGER NOT NULL DEFAULT 0,
    -- investability / actionable path
    listing_status       TEXT CHECK (listing_status IN
                           ('public','filed_s1','rumored_ipo','private','subsidiary')),
    public_ticker        TEXT,               -- set when the target itself is/becomes public
    public_proxies       TEXT,               -- JSON [{ticker, relation, source_url}]
    -- ai_posture / moat (controlled vocabulary)
    ai_class             TEXT CHECK (ai_class IN ('compounds','neutral','at_risk')),
    ai_rationale         TEXT,
    ai_source_url        TEXT,
    ai_confidence        TEXT,               -- Admiralty-style grade, e.g. 'B2'
    ai_provisional       INTEGER NOT NULL DEFAULT 0,
    as_of                TEXT NOT NULL,
    run_week             TEXT NOT NULL,
    updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
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
