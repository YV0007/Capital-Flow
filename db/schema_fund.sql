-- Capital Flow — FUND TRACKER (Section 3). SQLite, same db/capital.db.
--
-- Question this section answers: what are the ~14 funds we respect doing with
-- their book, RIGHT NOW. That is registry-shaped, not event-shaped: it stores
-- positions, stakes and deltas, not "X gave Y $Z on date D". So it gets its own
-- tables and never writes into `events`.
--
-- Everything here is prefixed fund_. Sections 1 (nveco_*/nvnet_*) and 2
-- (events/allocators/...) are untouched; the only thing shared is the file.
--
-- Two hard rules encoded in the shapes below:
--   1  Every row traces to a mandated filing or an official register download.
--      accession_no / source_url are NOT optional decoration — the audit fails
--      the run without them.
--   2  Deltas are computed on SHARE COUNT, never on value. A position's dollar
--      value rises when the price rises without a share being bought; a
--      value-based delta fabricates adds that never happened. fund_position_deltas
--      therefore has share_delta / share_delta_pct as the primary quantities and
--      carries value only as context.

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────────────────────
-- WHO WE TRACK. Closed, curated universe (config/fund_managers.yaml). A manager
-- is added by a deliberate config change, never by discovery.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fund_managers (
    cik            TEXT PRIMARY KEY,        -- zero-padded 10, the PARENT filer
    slug           TEXT NOT NULL UNIQUE,    -- stable id used in the payload
    name           TEXT NOT NULL,
    principal      TEXT,
    -- style_tag drives HOW a filing is read (spec §B1). quant is present in the
    -- enum only so the config can name an excluded manager; ingest refuses it.
    style_tag      TEXT NOT NULL CHECK (style_tag IN
                     ('concentrated','activist','crossover_tech','full_disclosure',
                      'daily_disclosure','multistrat_mm','quant')),
    -- manager_class drives WHETHER we ingest at all.
    --   tracked         standing book, 13F backbone + fast layer
    --   watch_only      §B3 — no 13F ingestion, event triggers only
    --   sparse_coverage §8b.3 — tracked, but disclosure is structurally partial
    --                   and the UI must SAY so (thin record != low activity)
    --   excluded        named in config with a rationale, never ingested
    manager_class  TEXT NOT NULL DEFAULT 'tracked' CHECK (manager_class IN
                     ('tracked','watch_only','sparse_coverage','excluded')),
    conviction_weight REAL NOT NULL,        -- multiplier on conviction_score (0.0 = 13F ignored)
    aum_usd        REAL,
    aum_as_of      TEXT,
    adv_crd        TEXT,                    -- Form ADV / IAPD id
    adv_strategy   TEXT,
    adv_source_url TEXT,
    adv_pulled_at  TEXT,
    why_tracked    TEXT NOT NULL,           -- rendered verbatim on the identity card
    focus          TEXT NOT NULL,           -- rendered verbatim on the identity card
    primary_source TEXT NOT NULL,           -- the layer that BEATS the 13F for this manager
    primary_source_url TEXT,
    ingest_13f     INTEGER NOT NULL DEFAULT 1,
    country        TEXT,
    active         INTEGER NOT NULL DEFAULT 1,
    notes          TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- §8b.4 ENTITY RESOLUTION — required, not optional. One manager files under many
-- CIKs (Point72 files under 6, Coatue's funds under 40). Without this table the
-- same fund appears three times at a third of its real size and every conviction
-- score is wrong. Positions are aggregated to parent_cik; child detail is kept.
CREATE TABLE IF NOT EXISTS fund_manager_entities (
    cik          TEXT PRIMARY KEY,          -- the CHILD filer CIK (may equal parent)
    parent_cik   TEXT NOT NULL REFERENCES fund_managers(cik),
    entity_name  TEXT NOT NULL,
    relationship TEXT NOT NULL CHECK (relationship IN
                   ('self','subsidiary','regional_entity','fund_vehicle',
                    'related_adviser','general_partner','listed_vehicle',
                    'registered_fund','predecessor')),
    rollup       INTEGER NOT NULL DEFAULT 1,   -- 0 = tracked for filings but not summed
    poll         INTEGER NOT NULL DEFAULT 1,   -- 0 = known but not polled daily
    source_url   TEXT,
    notes        TEXT
);
CREATE INDEX IF NOT EXISTS idx_fund_entities_parent ON fund_manager_entities (parent_cik);

-- CIKs we met in a filing but cannot attribute. Logged for review, never dropped.
CREATE TABLE IF NOT EXISTS fund_unmapped_ciks (
    cik         TEXT PRIMARY KEY,
    entity_name TEXT,
    seen_in     TEXT,                        -- accession no / register that surfaced it
    first_seen  TEXT NOT NULL DEFAULT (datetime('now')),
    note        TEXT
);

-- ─────────────────────────────────────────────────────────────────────────────
-- FILINGS. The idempotency spine: accession_no is the primary key, so re-running
-- the poller can never double-count.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fund_filings (
    accession_no     TEXT PRIMARY KEY,
    cik              TEXT NOT NULL,          -- the filer (child)
    parent_cik       TEXT,                   -- rolled-up manager, NULL if unmapped
    form_type        TEXT NOT NULL,
    filed_at         TEXT NOT NULL,
    period_of_report TEXT,
    items            TEXT,                   -- 8-K items, comma list
    primary_doc      TEXT,
    source_url       TEXT NOT NULL,          -- RESOLVED document URL, never a search query
    parsed_at        TEXT,
    parse_status     TEXT NOT NULL DEFAULT 'pending' CHECK (parse_status IN
                       ('pending','ok','skipped','unsupported','error')),
    parse_note       TEXT,                   -- WHY it was skipped/failed — surfaced, not hidden
    first_seen       TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_fund_filings_cik  ON fund_filings (cik, filed_at);
CREATE INDEX IF NOT EXISTS idx_fund_filings_form ON fund_filings (form_type, filed_at);
CREATE INDEX IF NOT EXISTS idx_fund_filings_st   ON fund_filings (parse_status);

-- Where the daily poller got to per CIK. Diffed against submissions JSON.
CREATE TABLE IF NOT EXISTS fund_poller_state (
    cik              TEXT PRIMARY KEY,
    last_accession   TEXT,
    last_filed_date  TEXT,
    last_checked_at  TEXT,
    consecutive_errors INTEGER NOT NULL DEFAULT 0,
    last_error       TEXT
);

-- §9: "if a source is unavailable, fail loudly and log it". This is the log.
-- The audit reads it; a dead source becomes a visible payload warning, never a
-- silent fallback to something weaker.
CREATE TABLE IF NOT EXISTS fund_source_health (
    source          TEXT PRIMARY KEY,        -- 'edgar' | 'ark' | 'esma' | 'fca' | ...
    last_ok_at      TEXT,
    last_error_at   TEXT,
    last_error      TEXT,
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    checked_at      TEXT
);

-- ─────────────────────────────────────────────────────────────────────────────
-- POSITIONS. One row = one line of one fund's book at one period, from one layer.
-- source_form records WHICH layer the number came from (§8b.1) so a monthly
-- N-PORT position is never silently mixed with a 45-day-stale 13F line.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fund_positions (
    id           INTEGER PRIMARY KEY,
    cik          TEXT NOT NULL,              -- filer (child)
    parent_cik   TEXT NOT NULL,              -- rollup key; conviction is computed on this
    period       TEXT NOT NULL,              -- period_of_report (13F) or as-of date (daily)
    cusip        TEXT NOT NULL,
    ticker       TEXT,                       -- via fund_cusip_map; NULL is allowed, never fatal
    issuer       TEXT NOT NULL,
    class_title  TEXT,
    shares       REAL NOT NULL,
    share_type   TEXT,                       -- SH | PRN (13F sshPrnamtType)
    value_usd    REAL NOT NULL,
    value_scale  TEXT,                       -- 'dollars' | 'thousands_x1000' — the units we DETECTED
    -- ONLY 'common' and 'adr' are ownership. Everything else is a derivative or a
    -- debt instrument, and 13F reports an option at the NOTIONAL value of the
    -- underlying shares — so folding one into a holdings list does not merely add
    -- a wrong row, it inflates the fund's total and therefore every weight
    -- computed from it. A put is worse still: it is a bet the stock FALLS, and in
    -- a portfolio table it states the opposite of the truth.
    instrument   TEXT NOT NULL DEFAULT 'common' CHECK (instrument IN
                   ('common','adr','call','put','warrant','right','unit',
                    'convertible','prn','other')),
    put_call     TEXT,
    discretion   TEXT,                       -- SOLE | DFND | OTR
    other_managers TEXT,
    source_form  TEXT NOT NULL,              -- '13F-HR' | '13F-HR/A' | 'N-PORT-P' | 'ARK-CSV' | 'PSH' | ...
    accession_no TEXT,
    source_url   TEXT NOT NULL,
    as_of        TEXT,                       -- true as-of when it differs from period
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (parent_cik, cik, period, cusip, instrument, source_form)
);
CREATE INDEX IF NOT EXISTS idx_fund_pos_book   ON fund_positions (parent_cik, period);
CREATE INDEX IF NOT EXISTS idx_fund_pos_cusip  ON fund_positions (cusip, period);

-- Per-position, per-period movement. share_delta is the truth; value is context.
CREATE TABLE IF NOT EXISTS fund_position_deltas (
    id              INTEGER PRIMARY KEY,
    parent_cik      TEXT NOT NULL,
    period          TEXT NOT NULL,
    prev_period     TEXT,
    cusip           TEXT NOT NULL,
    ticker          TEXT,
    issuer          TEXT NOT NULL,
    instrument      TEXT NOT NULL,
    action          TEXT NOT NULL CHECK (action IN ('NEW','ADD','HOLD','TRIM','EXIT')),
    shares          REAL,
    prev_shares     REAL,
    share_delta     REAL,
    share_delta_pct REAL,                    -- NULL on NEW (no prior base)
    value_usd       REAL,
    weight          REAL,                    -- position value / total book value
    prev_weight     REAL,
    weight_delta    REAL,
    weight_rank     INTEGER,
    in_top10        INTEGER NOT NULL DEFAULT 0,
    persistence_quarters INTEGER NOT NULL DEFAULT 1,
    -- added while the position was DOWN over the period: the strongest single tell
    conviction_add_flag INTEGER NOT NULL DEFAULT 0,
    period_price_change_pct REAL,            -- implied, from the fund's own value/shares
    cross_fund_count INTEGER NOT NULL DEFAULT 0,   -- how many tracked funds held it that period
    conviction_score REAL,                   -- 0-100, already multiplied by conviction_weight
    conviction_components TEXT,              -- JSON: every term, so a score is auditable
    -- §8b.6 guard 1: a big % change on a tiny line is noise. When this is 0 the
    -- dashboard must suppress or de-emphasise the % figure.
    pct_change_displayable INTEGER NOT NULL DEFAULT 1,
    source_form     TEXT NOT NULL,
    accession_no    TEXT,
    source_url      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (parent_cik, period, cusip, instrument)
);
CREATE INDEX IF NOT EXISTS idx_fund_delta_book ON fund_position_deltas (parent_cik, period);
CREATE INDEX IF NOT EXISTS idx_fund_delta_conv ON fund_position_deltas (conviction_score);

-- Fund-level context for a period: computed once, read by the scorer and the payload.
CREATE TABLE IF NOT EXISTS fund_book_stats (
    parent_cik   TEXT NOT NULL,
    period       TEXT NOT NULL,
    source_form  TEXT NOT NULL,
    positions    INTEGER NOT NULL,
    book_value_usd REAL NOT NULL,
    top10_share  REAL,                       -- book_concentration
    turnover_pct REAL,                       -- share-based, vs previous period
    avg_persistence REAL,
    put_value_usd REAL NOT NULL DEFAULT 0,
    call_value_usd REAL NOT NULL DEFAULT 0,
    conviction_add_count INTEGER NOT NULL DEFAULT 0,
    as_of        TEXT,
    disclosed_at TEXT,
    latency_days INTEGER,
    PRIMARY KEY (parent_cik, period, source_form)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- THE FAST LAYER (§A). These are what keep the UI alive between 13F prints.
-- ─────────────────────────────────────────────────────────────────────────────

-- 13D / 13G. For an activist the 13F is not the signal — Item 4 is.
CREATE TABLE IF NOT EXISTS fund_stakes (
    accession_no   TEXT PRIMARY KEY,
    cik            TEXT NOT NULL,
    parent_cik     TEXT,
    form_type      TEXT NOT NULL,            -- SC 13D | SC 13D/A | SC 13G | SC 13G/A
    issuer         TEXT NOT NULL,
    issuer_cik     TEXT,
    cusip          TEXT,
    ticker         TEXT,
    pct_of_class   REAL,
    shares         REAL,
    event_date     TEXT,                     -- date of event requiring filing (cover page)
    filed_at       TEXT NOT NULL,
    is_activist    INTEGER NOT NULL DEFAULT 0,   -- 13D => 1; 13G => 0
    intent_summary TEXT,                     -- short structured read of Item 4
    intent_excerpt TEXT,                     -- VERBATIM Item 4 excerpt — the evidence
    -- An amendment that does not amend Item 4 carries no Item 4 text at all. The
    -- intent from the live filing in that 13D chain still stands, so it is carried
    -- forward — and this column records which filing it actually came from, so an
    -- inherited intent is never mistaken for a fresh statement.
    intent_source_accession TEXT,
    amendment_no   TEXT,
    source_url     TEXT NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_fund_stakes_parent ON fund_stakes (parent_cik, filed_at);

-- Form 3/4/5 — the only layer with EXACT transaction dates. ~T+2.
CREATE TABLE IF NOT EXISTS fund_insider_txns (
    id             INTEGER PRIMARY KEY,
    accession_no   TEXT NOT NULL,
    cik            TEXT NOT NULL,            -- the reporting owner (our fund)
    parent_cik     TEXT,
    issuer         TEXT NOT NULL,
    issuer_cik     TEXT,
    ticker         TEXT,
    txn_date       TEXT,                     -- the ACTUAL trade date
    txn_code       TEXT,                     -- P purchase, S sale, A award, ...
    acquired_disposed TEXT,                  -- A | D
    security_title TEXT,
    derivative     INTEGER NOT NULL DEFAULT 0,
    shares         REAL,
    price          REAL,
    post_txn_shares REAL,
    is_ten_pct_owner INTEGER NOT NULL DEFAULT 0,
    is_director    INTEGER NOT NULL DEFAULT 0,
    filed_at       TEXT NOT NULL,
    source_url     TEXT NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (accession_no, issuer_cik, txn_date, txn_code, security_title, shares, price)
);
CREATE INDEX IF NOT EXISTS idx_fund_insider_parent ON fund_insider_txns (parent_cik, txn_date);

-- NAMED shorts from the EU/UK registers. This is the only place a short position
-- is attributed to a fund by name. FINRA/exchange short interest and CFTC COT are
-- AGGREGATE and must never be written here (audit rule A6).
CREATE TABLE IF NOT EXISTS fund_shorts (
    id            INTEGER PRIMARY KEY,
    parent_cik    TEXT,                      -- NULL when the register name is unmatched
    fund_name     TEXT NOT NULL,             -- verbatim register string
    issuer        TEXT NOT NULL,
    isin          TEXT,
    pct           REAL NOT NULL,
    register      TEXT NOT NULL,             -- 'ESMA' | 'BaFin' | 'AMF' | 'FCA'
    as_of_date    TEXT NOT NULL,
    is_current    INTEGER NOT NULL DEFAULT 1,
    source_url    TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (register, fund_name, isin, as_of_date)
);
CREATE INDEX IF NOT EXISTS idx_fund_shorts_parent ON fund_shorts (parent_cik, as_of_date);

-- Listed / full-disclosure vehicles: PSH, TPOU, Greenlight Re, Berkshire.
-- These BEAT the 13F for their manager (longs AND shorts, non-US names included).
CREATE TABLE IF NOT EXISTS fund_vehicle_holdings (
    id          INTEGER PRIMARY KEY,
    parent_cik  TEXT,
    vehicle     TEXT NOT NULL,               -- 'PSH' | 'TPOU' | 'GLRE' | 'BRK'
    as_of       TEXT NOT NULL,
    name        TEXT NOT NULL,
    ticker      TEXT,
    weight      REAL,                        -- % of portfolio when disclosed
    direction   TEXT NOT NULL DEFAULT 'long' CHECK (direction IN ('long','short')),
    source_doc  TEXT NOT NULL,               -- resolved URL of the report/factsheet
    note        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (vehicle, as_of, name, direction)
);

-- NAV / performance series from the same vehicles.
CREATE TABLE IF NOT EXISTS fund_vehicle_nav (
    vehicle    TEXT NOT NULL,
    as_of      TEXT NOT NULL,
    nav_per_share REAL,
    currency   TEXT,
    mtd_pct    REAL,
    ytd_pct    REAL,
    source_doc TEXT NOT NULL,
    PRIMARY KEY (vehicle, as_of)
);

-- Track record. Same convention as the Section-2 allocator panel: a current-year
-- or YTD figure MUST be flagged provisional, and no row exists without a source.
CREATE TABLE IF NOT EXISTS fund_track_record (
    id           INTEGER PRIMARY KEY,
    parent_cik   TEXT NOT NULL,
    fiscal_year  TEXT NOT NULL,              -- '2021'..'2025' or 'YTD2026'
    metric       TEXT NOT NULL DEFAULT 'net_return_pct',
    scope        TEXT NOT NULL DEFAULT '',   -- fund/vehicle when several series exist
    return_pct   REAL,
    is_provisional INTEGER NOT NULL DEFAULT 0,
    source_url   TEXT NOT NULL,
    note         TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (parent_cik, fiscal_year, metric, scope)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- THE UNIFIED TIMELINE. Everything the dashboard reads chronologically.
-- latency_days = disclosed_date - event_date is FIRST-CLASS: it is the honesty
-- mechanism for Problem A. A 13F "new position" without its latency is actively
-- misleading (§8b.6 guard 2), so the payload never emits one without it.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fund_events (
    id             INTEGER PRIMARY KEY,
    parent_cik     TEXT NOT NULL,
    cik            TEXT,
    event_date     TEXT NOT NULL,            -- when it actually happened / as-of
    disclosed_date TEXT NOT NULL,            -- when it became public
    latency_days   INTEGER NOT NULL,
    event_type     TEXT NOT NULL CHECK (event_type IN
                     ('13f_new','13f_add','13f_trim','13f_exit','13f_amendment',
                      'stake_13d','stake_13d_amend','stake_13g','insider_txn',
                      'material_8k','short_open','short_change','short_close',
                      'vehicle_update','nport_update','daily_holdings',
                      'watch_trigger','ipo_cap_table','parse_failure')),
    headline       TEXT NOT NULL,
    issuer         TEXT,
    ticker         TEXT,
    cusip          TEXT,
    magnitude      REAL,                     -- USD when known, else NULL
    magnitude_unit TEXT,                     -- 'usd' | 'pct_of_class' | 'pct_of_book'
    conviction_score REAL,
    is_watch_trigger INTEGER NOT NULL DEFAULT 0,
    is_flagged     INTEGER NOT NULL DEFAULT 0,   -- e.g. 13F-HR/A confidential release
    flag_reason    TEXT,
    source_form    TEXT,
    accession_no   TEXT,
    source_url     TEXT NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Idempotency key as an expression index: an event may legitimately lack a cusip,
-- an accession or an issuer, and NULLs never collide in a plain UNIQUE constraint —
-- which would let a re-run duplicate exactly the rows we most need deduped.
CREATE UNIQUE INDEX IF NOT EXISTS idx_fund_events_key ON fund_events (
    parent_cik, event_type, event_date, COALESCE(cusip,''),
    COALESCE(accession_no,''), COALESCE(issuer,''));
CREATE INDEX IF NOT EXISTS idx_fund_events_date ON fund_events (disclosed_date DESC);
CREATE INDEX IF NOT EXISTS idx_fund_events_parent ON fund_events (parent_cik, disclosed_date);

-- ─────────────────────────────────────────────────────────────────────────────
-- IDENTIFIERS. CUSIP -> ticker must be auditable and versioned; an unmapped CUSIP
-- is LOGGED, never dropped (§7).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fund_cusip_map (
    cusip        TEXT PRIMARY KEY,
    ticker       TEXT,
    issuer_name  TEXT,
    issuer_cik   TEXT,
    method       TEXT NOT NULL,              -- 'config' | 'name_match' | 'sec_13f_list' | 'manual'
    confidence   TEXT NOT NULL DEFAULT 'medium' CHECK (confidence IN ('high','medium','low')),
    map_version  TEXT NOT NULL,              -- config/fund_cusip_map.yaml version that produced it
    source_url   TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS fund_cusip_unmapped (
    cusip       TEXT PRIMARY KEY,
    issuer_name TEXT,
    seen_count  INTEGER NOT NULL DEFAULT 1,
    first_seen  TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen   TEXT NOT NULL DEFAULT (datetime('now')),
    example_accession TEXT
);

-- §8b.5: shares outstanding, from the XBRL company-facts API. This is what turns
-- a raw share count into a % of the company — the only interpretable form.
CREATE TABLE IF NOT EXISTS fund_shares_outstanding (
    issuer_cik  TEXT NOT NULL,
    as_of       TEXT NOT NULL,
    shares      REAL NOT NULL,
    ticker      TEXT,
    source_url  TEXT NOT NULL,
    PRIMARY KEY (issuer_cik, as_of)
);

-- §8b.5 REVERSE LOOKUP: security -> all holders (the terminal HDS view). Filled by
-- a wider 13F sweep than the 14; tracked funds render prominently, the rest are
-- the institutional background that says whether our fund is early or late.
CREATE TABLE IF NOT EXISTS fund_holders (
    id          INTEGER PRIMARY KEY,
    cusip       TEXT NOT NULL,
    ticker      TEXT,
    issuer      TEXT NOT NULL,
    period      TEXT NOT NULL,
    filer_cik   TEXT NOT NULL,
    filer_name  TEXT NOT NULL,
    shares      REAL NOT NULL,
    value_usd   REAL,
    prev_shares REAL,
    share_delta REAL,
    pct_of_shares_outstanding REAL,
    is_tracked  INTEGER NOT NULL DEFAULT 0,
    accession_no TEXT,
    source_url  TEXT NOT NULL,
    UNIQUE (cusip, period, filer_cik)
);
CREATE INDEX IF NOT EXISTS idx_fund_holders_sec ON fund_holders (cusip, period);

-- ─────────────────────────────────────────────────────────────────────────────
-- §B3 WATCH-ONLY TRIGGERS. Citadel/Millennium/Point72/Balyasny have no standing
-- book here. There is NO separate CIK for a "conviction sleeve" inside a
-- multi-strat and the 13F carries no strategy attribution, so the conviction desk
-- cannot be parsed out of the filing. Instead they surface only on a disclosure
-- that market-making mechanically cannot produce.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fund_watch_triggers (
    id           INTEGER PRIMARY KEY,
    parent_cik   TEXT NOT NULL,
    trigger_type TEXT NOT NULL CHECK (trigger_type IN
                   ('13d','13g_crossing','form_4','insider_3','short_register',
                    'ipo_cap_table','private_round')),
    fired_at     TEXT NOT NULL,              -- disclosure date
    event_date   TEXT,
    issuer       TEXT,
    detail       TEXT NOT NULL,
    accession_no TEXT,
    source_url   TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_fund_watch_key ON fund_watch_triggers (
    parent_cik, trigger_type, COALESCE(accession_no,''), COALESCE(issuer,''), fired_at);

-- Cross-check ledger (§7): 13F vs DEF 14A >5% holder table. A discrepancy is
-- FLAGGED, never silently resolved by picking one side.
CREATE TABLE IF NOT EXISTS fund_crosschecks (
    id            INTEGER PRIMARY KEY,
    parent_cik    TEXT NOT NULL,
    issuer        TEXT NOT NULL,
    issuer_cik    TEXT,
    period        TEXT,
    filed_shares  REAL,                      -- what the 13F says
    proxy_shares  REAL,                      -- what the DEF 14A holder table says
    proxy_pct     REAL,
    proxy_as_of   TEXT,
    delta_pct     REAL,
    status        TEXT NOT NULL CHECK (status IN ('match','discrepancy','unresolved')),
    note          TEXT,
    filing_url    TEXT,
    proxy_url     TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (parent_cik, issuer, period)
);

-- Run ledger — what each pipeline stage did, per run. Read by the audit.
CREATE TABLE IF NOT EXISTS fund_run_log (
    id         INTEGER PRIMARY KEY,
    run_id     TEXT NOT NULL,
    stage      TEXT NOT NULL,
    status     TEXT NOT NULL CHECK (status IN ('ok','warn','error','skipped')),
    detail     TEXT,
    stats      TEXT,                         -- JSON
    started_at TEXT,
    ended_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_fund_run_log ON fund_run_log (run_id, stage);
