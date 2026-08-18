-- Capital Flow — СЕТЬ ИИ-инфраструктуры (v3). Тот же db/capital.db.
--
-- Здесь лежит ТОЛЬКО ДОСТРОЙКА поверх v2, а не копия сети. 106 сущностей и 243 связи
-- пилота остаются в nveco_* и в handoff/nvidia_ecosystem.json; сетевой слой читает их
-- как семя и не дублирует. Дублирование означало бы два места правды на одну сущность,
-- и через месяц они разъехались бы.
--
-- В этих таблицах: новые сущности (одна — google-cloud), новые связи пивот↔пивот, их
-- источники, зафиксированные пары БЕЗ связи и выпуски сети.

PRAGMA foreign_keys = ON;

-- Новые сущности достройки. Колонки повторяют nveco_entity: сетевой слой отдаёт их в
-- том же виде, что и семенные, и различать их по форме дашборд не должен.
CREATE TABLE IF NOT EXISTS nvnet_entity (
    id             TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    aliases        TEXT,
    type           TEXT NOT NULL CHECK (type IN
                     ('company','geopolitical','agency','research_org','standards_body')),
    role           TEXT NOT NULL CHECK (role IN
                     ('producer','platform','operator','demand','capital','state')),
    sector         TEXT,
    primary_layer  TEXT NOT NULL,
    layers         TEXT NOT NULL,          -- '|'-список
    phase          TEXT NOT NULL DEFAULT 'mature' CHECK (phase IN
                     ('emerging','scaling','mature','at_risk','declining')),
    ticker         TEXT,
    public_private TEXT CHECK (public_private IN
                     ('public','private','government','academic')),
    geo            TEXT,
    founded        TEXT,
    revenue_usd_b  REAL,
    one_liner      TEXT,
    why_irreplaceable TEXT,
    what_breaks_it TEXT,
    geo_risk       TEXT NOT NULL CHECK (geo_risk IN ('critical','high','medium','low')),
    geo_risk_note  TEXT,
    export_regime  TEXT,
    concentration  INTEGER CHECK (concentration BETWEEN 0 AND 100),
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS nvnet_entity_factor (
    entity_id TEXT NOT NULL REFERENCES nvnet_entity(id) ON DELETE CASCADE,
    factor    TEXT NOT NULL CHECK (factor IN
                ('irreplaceability','lock_in_depth','time_to_replace','strategic_control')),
    value     INTEGER NOT NULL CHECK (value BETWEEN 0 AND 100),
    why       TEXT,
    UNIQUE (entity_id, factor)
);

-- Связи достройки. Тот же список типов, что в v2, ПЛЮС два новых из
-- config/nvnet_edges.yaml. Схема v2 не тронута: там свой CHECK на 31 значение.
CREATE TABLE IF NOT EXISTS nvnet_edge (
    id              TEXT PRIMARY KEY,      -- '<source>__<target>__<type>'
    source_id       TEXT NOT NULL,
    target_id       TEXT NOT NULL,
    type            TEXT NOT NULL CHECK (type IN (
                      'manufactures','supplies','packages','integrates','delivers_to',
                      'enables','co_designs','optimizes_for',
                      'invests_in','funded_by','board_seat','strategic_partner',
                      'hedges_against','diversifies_supply','customer_of',
                      'validates_demand','proves_roi','proves_use_case',
                      'locks_in_developers','locks_in_platforms','path_dependent_on',
                      'standardizes_on','sets_benchmark','defines_category',
                      'controls_access_to','subject_to_restriction',
                      'export_controlled_by','geopolitically_dependent',
                      'competes_with','threatens','could_disrupt',
                      -- добавлено контрактом v3
                      'is_alternative_to','enables_interop')),
    spine           TEXT NOT NULL CHECK (spine IN
                      ('physical','capital','moat','control','rivalry')),
    direction       TEXT NOT NULL CHECK (direction IN
                      ('upstream','downstream','lateral','bidirectional')),
    strength        INTEGER NOT NULL CHECK (strength BETWEEN 0 AND 100),
    lock_in_depth   INTEGER CHECK (lock_in_depth BETWEEN 0 AND 100),
    substitutability INTEGER CHECK (substitutability BETWEEN 0 AND 100),
    is_reversible   INTEGER NOT NULL DEFAULT 1,
    status          TEXT NOT NULL DEFAULT 'signal' CHECK (status IN
                      ('confirmed','high_confidence','signal')),
    confidence      REAL CHECK (confidence BETWEEN 0 AND 1),
    source_tier     INTEGER CHECK (source_tier BETWEEN 1 AND 6),
    confirmed_sources INTEGER NOT NULL DEFAULT 0,
    risk_level      TEXT CHECK (risk_level IN ('critical','high','medium','low')),
    risk_type       TEXT CHECK (risk_type IN
                      ('geopolitical','substitution','market','regulatory','technical','none')),
    risk_timeline   TEXT CHECK (risk_timeline IN
                      ('immediate','1-2y','2-5y','5y+','ongoing','none')),
    risk_mitigation TEXT,
    tech_node       TEXT,
    formed          TEXT,
    strengthened    TEXT,
    last_confirmed  TEXT,
    note            TEXT,
    clamped         TEXT,
    origin          TEXT,                  -- 'A1'…'A11' | 'B-<пивот>' | 'GC'
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source_id, target_id, type)
);

CREATE TABLE IF NOT EXISTS nvnet_source (
    id         INTEGER PRIMARY KEY,
    owner_kind TEXT NOT NULL CHECK (owner_kind IN ('entity','edge')),
    owner_id   TEXT NOT NULL,
    tier       INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 6),
    type       TEXT NOT NULL,
    title      TEXT,
    url        TEXT NOT NULL,
    published  TEXT,
    fetched    TEXT,
    alive      INTEGER NOT NULL DEFAULT 1,
    http_note  TEXT,
    quote      TEXT NOT NULL,
    confidence REAL CHECK (confidence BETWEEN 0 AND 1),
    UNIQUE (owner_kind, owner_id, url, quote)
);

-- Пары, где добросовестный поиск НЕ нашёл связи. Отдельная таблица, потому что это
-- такой же результат исследования, как найденное ребро: без неё через месяц никто не
-- вспомнит, проверялась пара или её просто пропустили.
CREATE TABLE IF NOT EXISTS nvnet_not_found (
    pair_id     TEXT PRIMARY KEY,
    entity_a    TEXT NOT NULL,
    entity_b    TEXT NOT NULL,
    expected    TEXT,                      -- какой тип связи предполагался
    reason      TEXT NOT NULL,
    checked_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Выпуски сети. Версия vX.Y-YYYY-MM; история сохраняется, чтобы diff между выпусками
-- был возможен без внешнего хранилища.
CREATE TABLE IF NOT EXISTS nvnet_release (
    version     TEXT PRIMARY KEY,          -- 'v1.0-2026-08'
    as_of       TEXT NOT NULL,
    nodes       INTEGER NOT NULL,
    edges       INTEGER NOT NULL,
    pivotal     INTEGER NOT NULL,
    density     REAL,
    avg_degree  REAL,
    clustering  REAL,
    notes       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
