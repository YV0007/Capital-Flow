-- Capital Flow — ECOSYSTEM MAP schema (SQLite, same db/capital.db as the weekly pipeline).
--
-- The weekly pipeline answers "where did money go this week" (events, dated).
-- This one answers "how is the industry built and who holds it" (standing positions,
-- undated). Different question, different tables — but the SAME database file, because
-- entity identity is shared: NVIDIA must be one NVIDIA in both pipelines
-- (config/aliases.yaml + entity_aliases route names for both).
--
-- Everything here is prefixed eco_. Nothing in the weekly tables is touched.
--
-- The load-bearing design decision is eco_evidence being its OWN table rather than a
-- column on the edge: the two-source rule, the effective source tier, and the monthly
-- link-liveness recheck all fall out of it for free.

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────────────────────
-- Nodes — a COMPANY, never a layer. A company in several layers stays ONE row
-- here and gets several eco_node_layers rows (§3.4 of the plan: radial capsule,
-- никаких дублей).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS eco_nodes (
    id              INTEGER PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,   -- stable map id ('asml'); NEVER renamed
    name            TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN
                      ('producer','owner','capital','demand','platform')),
    sector          TEXT,                   -- one of the 44 Roadmap.jsx sectors
    tier            TEXT NOT NULL DEFAULT 'core' CHECK (tier IN ('anchor','core','emerging')),
    ticker          TEXT,
    public_private  TEXT CHECK (public_private IN ('Pub','Pvt')),
    geo             TEXT,
    one_liner       TEXT,
    what_breaks_it  TEXT,
    dc_node         TEXT,                   -- id in Roadmap.jsx / dc-details.json, or NULL
    -- Criticality rubric inputs, 0..5 each. Stored, never re-derived by hand: the
    -- panel shows WHY the score is 98, not just "98".
    f_share         INTEGER CHECK (f_share BETWEEN 0 AND 5),
    f_alternatives  INTEGER CHECK (f_alternatives BETWEEN 0 AND 5),
    f_switch_time   INTEGER CHECK (f_switch_time BETWEEN 0 AND 5),
    f_barrier       INTEGER CHECK (f_barrier BETWEEN 0 AND 5),
    share_note      TEXT,                   -- the sourced share claim behind f_share
    criticality     INTEGER CHECK (criticality BETWEEN 0 AND 100),  -- computed by eco_score
    first_seen      TEXT,                   -- YYYY-MM, set once, never overwritten
    last_confirmed  TEXT,                   -- YYYY-MM, newest evidence touching this node
    stale           INTEGER NOT NULL DEFAULT 0,   -- 1 when last_confirmed older than 6 months
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_eco_nodes_role   ON eco_nodes (role);
CREATE INDEX IF NOT EXISTS idx_eco_nodes_sector ON eco_nodes (sector);

-- One row per (company, layer). Several rows = the capsule stretched across layers.
-- A second eco_nodes row for the same company is a BUG, not a modelling choice.
CREATE TABLE IF NOT EXISTS eco_node_layers (
    node_id              INTEGER NOT NULL REFERENCES eco_nodes(id) ON DELETE CASCADE,
    layer                TEXT NOT NULL CHECK (layer IN
                           ('L1','L2','L3','L4','L5','L6','L7','L8','L9','L10','L11','L12')),
    is_primary           INTEGER NOT NULL DEFAULT 0,   -- exactly one per node
    criticality_in_layer INTEGER CHECK (criticality_in_layer BETWEEN 0 AND 100),
    UNIQUE (node_id, layer)
);

-- ~12 tech nodes (EUV, CUDA, CoWoS, HBM, NVLink…). Each has an owner company;
-- drawn as a satellite next to it, and as the label on an edge.
CREATE TABLE IF NOT EXISTS eco_tech_nodes (
    id            INTEGER PRIMARY KEY,
    slug          TEXT NOT NULL UNIQUE,     -- 'euv'
    label         TEXT NOT NULL,            -- 'EUV'
    owner_node_id INTEGER REFERENCES eco_nodes(id),
    note          TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Edges — a standing dependency, not a dated event. Direction is always up the
-- stack (supplier → consumer). strength is materiality FOR THE RECEIVER.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS eco_edges (
    id             INTEGER PRIMARY KEY,
    slug           TEXT NOT NULL UNIQUE,    -- '<source>__<target>__<type>', stable
    source_id      INTEGER NOT NULL REFERENCES eco_nodes(id) ON DELETE CASCADE,
    target_id      INTEGER NOT NULL REFERENCES eco_nodes(id) ON DELETE CASCADE,
    edge_type      TEXT NOT NULL CHECK (edge_type IN
                     ('supply','offtake','platform','partner','compete',
                      'owns','stake','finances','develops','operates')),
    spine          TEXT NOT NULL CHECK (spine IN ('physical','capital')),
    strength       INTEGER NOT NULL CHECK (strength BETWEEN 0 AND 100),
    tech_node_id   INTEGER REFERENCES eco_tech_nodes(id),
    status         TEXT NOT NULL DEFAULT 'active'
                     CHECK (status IN ('active','expired','unverified')),
    started        TEXT,
    ended          TEXT,
    last_confirmed TEXT,                    -- YYYY-MM, newest live evidence
    engine_confirmed INTEGER NOT NULL DEFAULT 0,  -- cross-checked vs the weekly events table
    note           TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source_id, target_id, edge_type)
);

CREATE INDEX IF NOT EXISTS idx_eco_edges_source ON eco_edges (source_id);
CREATE INDEX IF NOT EXISTS idx_eco_edges_target ON eco_edges (target_id);
CREATE INDEX IF NOT EXISTS idx_eco_edges_type   ON eco_edges (edge_type);

-- MANY rows per edge. No row here → no edge (enforced on ingest AND on handoff).
-- confirmed_sources, the effective tier and the monthly liveness recheck all read
-- from this table.
CREATE TABLE IF NOT EXISTS eco_evidence (
    id             INTEGER PRIMARY KEY,
    edge_id        INTEGER NOT NULL REFERENCES eco_edges(id) ON DELETE CASCADE,
    source_url     TEXT NOT NULL,
    source_tier    TEXT NOT NULL CHECK (source_tier IN
                     ('filing','company_pr','transcript','press','estimate')),
    quote          TEXT NOT NULL,           -- VERBATIM. No quote → no edge.
    published_date TEXT,
    fetched_date   TEXT,
    alive          INTEGER NOT NULL DEFAULT 1,   -- eco_verify: URL 200 + quote still present
    last_checked   TEXT,
    check_note     TEXT,                    -- why alive=0 (404 / quote gone / network)
    UNIQUE (edge_id, source_url, quote)
);

CREATE INDEX IF NOT EXISTS idx_eco_evidence_edge ON eco_evidence (edge_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- Computed per run — pure arithmetic over the stored factors. No judgement here.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS eco_scores (
    node_id            INTEGER NOT NULL REFERENCES eco_nodes(id) ON DELETE CASCADE,
    run_id             TEXT NOT NULL,       -- YYYY-MM
    criticality        INTEGER,
    gravity_nodes      INTEGER,             -- distinct counterparties touched
    gravity_layers     INTEGER,             -- distinct layers reached
    gravity_edge_types INTEGER,             -- distinct edge types used
    gravity_score      INTEGER,
    UNIQUE (node_id, run_id)
);

CREATE TABLE IF NOT EXISTS eco_layer_stats (
    run_id   TEXT NOT NULL,
    layer    TEXT NOT NULL CHECK (layer IN
               ('L1','L2','L3','L4','L5','L6','L7','L8','L9','L10','L11','L12')),
    hhi      REAL,                          -- 0..1, over criticality_in_layer shares
    level    TEXT CHECK (level IN ('monopoly','oligopoly','competitive')),
    top_json TEXT,                          -- JSON array of node slugs, strongest first
    UNIQUE (run_id, layer)
);

-- Closed loops of length 3..5. The only lens with no judgement in it — a cycle is
-- a property of the graph.
CREATE TABLE IF NOT EXISTS eco_cycles (
    id         INTEGER PRIMARY KEY,
    run_id     TEXT NOT NULL,
    slug       TEXT NOT NULL,               -- stable within a run ('c1')
    cycle_type TEXT NOT NULL CHECK (cycle_type IN ('sales','financing')),
    path_json  TEXT NOT NULL,               -- JSON array of node slugs, first repeated last
    edges_json TEXT NOT NULL,               -- JSON array of edge slugs
    members    TEXT NOT NULL,               -- sorted '|'-joined member set — the dedupe key
    note       TEXT,
    UNIQUE (run_id, members)
);

-- Provenance of every monthly run, per agent (mirrors the weekly pipeline's audit trail).
CREATE TABLE IF NOT EXISTS eco_runs (
    id            INTEGER PRIMARY KEY,
    month         TEXT NOT NULL,            -- YYYY-MM
    agent         TEXT NOT NULL,
    rows_in       INTEGER NOT NULL DEFAULT 0,
    rows_rejected INTEGER NOT NULL DEFAULT 0,
    notes         TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (month, agent)
);
