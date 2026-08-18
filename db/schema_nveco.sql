-- Capital Flow — ЭКОСИСТЕМА NVIDIA (v2). SQLite, тот же db/capital.db.
--
-- Вопрос карты: кто делает NVIDIA незаменимой, кто заперт в её орбите, кто её шлюзует
-- и чем она хеджируется. Это НЕ цепочка поставок — это карта взаимной зависимости
-- с центром (якорем), пятью хребтами связей и политическими шлюзами.
--
-- Всё здесь с префиксом nveco_. Таблицы v1 (eco_*) не тронуты и не удалены: они лежат
-- в той же базе как история, новый конвейер с ними не пересекается.
--
-- ВАЖНО про словари. Списки слоёв и типов связей живут в config/nveco_layers.yaml и
-- config/nveco_edges.yaml — это их единственный дом. CHECK-констрейнты ниже дублируют
-- ЗАКРЫТЫЕ перечисления (роли, фазы, статусы, хребты, типы связей), потому что дешёвая
-- защита на уровне БД ловит половину мусора без единой строки Python. Идентификаторы
-- СЛОЁВ намеренно НЕ захардкожены: layer_id — свободный текст, его валидирует ingest
-- против YAML. Иначе добавление семнадцатого слоя означало бы миграцию схемы.

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────────────────────
-- Сущность. Компания, государство, агентство, стандарт — всё, что может стоять
-- в орбите якоря.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nveco_entity (
    id             TEXT PRIMARY KEY,        -- slug ('tsmc'); СТАБИЛЕН между прогонами
    name           TEXT NOT NULL,
    aliases        TEXT,                    -- '|'-список; резолвинг идёт через entity_aliases
    type           TEXT NOT NULL CHECK (type IN
                     ('company','geopolitical','agency','research_org','standards_body')),
    role           TEXT NOT NULL CHECK (role IN
                     ('producer','platform','operator','demand','capital','state')),
    sector         TEXT,                    -- sectors[].key из config/nveco_layers.yaml
    primary_layer  TEXT NOT NULL,           -- валидируется ingest'ом против YAML
    phase          TEXT NOT NULL DEFAULT 'mature' CHECK (phase IN
                     ('emerging','scaling','mature','at_risk','declining')),
    ticker         TEXT,
    public_private TEXT CHECK (public_private IN
                     ('public','private','government','academic')),
    geo            TEXT,                    -- ISO-2 штаб-квартиры
    founded        TEXT,
    revenue_usd_b  REAL,
    one_liner      TEXT,                    -- <=110 знаков, по-русски
    why_irreplaceable TEXT,                 -- <=280 знаков
    what_breaks_it TEXT,                    -- <=110 знаков
    criticality    INTEGER CHECK (criticality BETWEEN 0 AND 100),  -- считает nveco_score
    hops           INTEGER,                 -- расстояние до якоря в шагах; считает score
    first_seen     TEXT,                    -- YYYY-MM, пишется один раз
    last_confirmed TEXT,
    stale          INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_nveco_entity_layer ON nveco_entity (primary_layer);
CREATE INDEX IF NOT EXISTS idx_nveco_entity_role  ON nveco_entity (role);

-- Сущность в нескольких слоях — несколько строк, не массив в колонке.
CREATE TABLE IF NOT EXISTS nveco_entity_layer (
    entity_id   TEXT NOT NULL REFERENCES nveco_entity(id) ON DELETE CASCADE,
    layer_id    TEXT NOT NULL,
    is_primary  INTEGER NOT NULL DEFAULT 0,
    criticality INTEGER CHECK (criticality BETWEEN 0 AND 100),
    UNIQUE (entity_id, layer_id)
);

-- Четыре строки на сущность. Фактор и его обоснование живут вместе — так
-- criticalityWhy собирается без отдельной таблицы, и невозможно записать оценку,
-- забыв объяснить её.
CREATE TABLE IF NOT EXISTS nveco_entity_factor (
    entity_id TEXT NOT NULL REFERENCES nveco_entity(id) ON DELETE CASCADE,
    factor    TEXT NOT NULL CHECK (factor IN
                ('irreplaceability','lock_in_depth','time_to_replace','strategic_control')),
    value     INTEGER NOT NULL CHECK (value BETWEEN 0 AND 100),
    why       TEXT,                       -- <=120 знаков, по-русски
    UNIQUE (entity_id, factor)
);

CREATE TABLE IF NOT EXISTS nveco_entity_risk (
    entity_id     TEXT PRIMARY KEY REFERENCES nveco_entity(id) ON DELETE CASCADE,
    geopolitical  TEXT NOT NULL CHECK (geopolitical IN ('critical','high','medium','low')),
    note          TEXT,                   -- <=200 знаков
    export_regime TEXT,                   -- NULL если неприменимо
    concentration INTEGER CHECK (concentration BETWEEN 0 AND 100)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Связь. 31 тип на пяти хребтах; хребет выводит движок из типа.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nveco_edge (
    id              TEXT PRIMARY KEY,      -- '<source>__<target>__<type>'
    source_id       TEXT NOT NULL REFERENCES nveco_entity(id) ON DELETE CASCADE,
    target_id       TEXT NOT NULL REFERENCES nveco_entity(id) ON DELETE CASCADE,
    type            TEXT NOT NULL CHECK (type IN (
                      -- physical
                      'manufactures','supplies','packages','integrates','delivers_to',
                      'enables','co_designs','optimizes_for',
                      -- capital
                      'invests_in','funded_by','board_seat','strategic_partner',
                      'hedges_against','diversifies_supply','customer_of',
                      -- moat
                      'validates_demand','proves_roi','proves_use_case',
                      'locks_in_developers','locks_in_platforms','path_dependent_on',
                      'standardizes_on','sets_benchmark','defines_category',
                      -- control
                      'controls_access_to','subject_to_restriction',
                      'export_controlled_by','geopolitically_dependent',
                      -- rivalry
                      'competes_with','threatens','could_disrupt')),
    spine           TEXT NOT NULL CHECK (spine IN
                      ('physical','capital','moat','control','rivalry')),
    direction       TEXT NOT NULL CHECK (direction IN
                      ('upstream','downstream','lateral','bidirectional')),
    strength        INTEGER NOT NULL CHECK (strength BETWEEN 0 AND 100),
    lock_in_depth   INTEGER CHECK (lock_in_depth BETWEEN 0 AND 100),
    substitutability INTEGER CHECK (substitutability BETWEEN 0 AND 100),  -- ОБРАТНАЯ шкала
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
    risk_mitigation TEXT,                  -- <=160 знаков; NULL если крыть нечем
    tech_node       TEXT,                  -- nveco_tech_node.id или NULL
    formed          TEXT,
    strengthened    TEXT,
    last_confirmed  TEXT,
    note            TEXT,                  -- <=200 знаков
    clamped         TEXT,                  -- почему движок обрезал strength/risk; NULL если нет
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source_id, target_id, type)
);

CREATE INDEX IF NOT EXISTS idx_nveco_edge_source ON nveco_edge (source_id);
CREATE INDEX IF NOT EXISTS idx_nveco_edge_target ON nveco_edge (target_id);
CREATE INDEX IF NOT EXISTS idx_nveco_edge_spine  ON nveco_edge (spine);

-- ─────────────────────────────────────────────────────────────────────────────
-- Источники. ОДНА таблица на сущности и рёбра — чтобы nveco_verify обходил ссылки
-- одним проходом, а не двумя разными кодовыми путями.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nveco_source (
    id         INTEGER PRIMARY KEY,
    owner_kind TEXT NOT NULL CHECK (owner_kind IN ('entity','edge')),
    owner_id   TEXT NOT NULL,              -- nveco_entity.id или nveco_edge.id
    tier       INTEGER NOT NULL CHECK (tier BETWEEN 1 AND 6),
    type       TEXT NOT NULL CHECK (type IN
                 ('sec_filing','earnings_call','company_pr','partner_pr','product_doc',
                  'white_paper','patent','interview','conference','testimony','research',
                  'analyst','database','press','social')),
    title      TEXT,
    url        TEXT NOT NULL,
    published  TEXT,
    fetched    TEXT,
    alive      INTEGER NOT NULL DEFAULT 1,
    http_note  TEXT,                       -- что ответила ссылка при последней проверке
    quote      TEXT NOT NULL,              -- ДОСЛОВНО, <= 15 слов
    confidence REAL CHECK (confidence BETWEEN 0 AND 1),
    UNIQUE (owner_kind, owner_id, url, quote)
);

CREATE INDEX IF NOT EXISTS idx_nveco_source_owner ON nveco_source (owner_kind, owner_id);

-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nveco_tech_node (
    id         TEXT PRIMARY KEY,           -- 'cuda', 'n3'
    label      TEXT NOT NULL,
    owner_id   TEXT REFERENCES nveco_entity(id),
    note       TEXT,
    importance TEXT CHECK (importance IN ('critical','high','medium','low'))
);

CREATE TABLE IF NOT EXISTS nveco_cycle (
    id         TEXT NOT NULL,              -- 'c1', уникален внутри прогона
    run_month  TEXT NOT NULL,
    anchor     TEXT NOT NULL,
    cycle_type TEXT NOT NULL CHECK (cycle_type IN ('sales','financing','lockin')),
    path_json  TEXT NOT NULL,              -- JSON-массив id сущностей, первый повторён последним
    members    TEXT NOT NULL,              -- отсортированный '|'-набор участников — ключ дедупа
    note       TEXT,
    PRIMARY KEY (run_month, id),
    UNIQUE (run_month, members)
);

CREATE TABLE IF NOT EXISTS nveco_cycle_edge (
    run_month TEXT NOT NULL,
    cycle_id  TEXT NOT NULL,
    position  INTEGER NOT NULL,
    edge_id   TEXT NOT NULL REFERENCES nveco_edge(id) ON DELETE CASCADE,
    UNIQUE (run_month, cycle_id, position)
);

-- Прогон. anchor живёт ЗДЕСЬ, а не в сущности: сущность может входить в орбиту двух
-- якорей, а прогон всегда ровно про один. Это всё, что нужно для второго якоря.
CREATE TABLE IF NOT EXISTS nveco_run (
    id         INTEGER PRIMARY KEY,
    month      TEXT NOT NULL,
    anchor     TEXT NOT NULL,
    agent      TEXT NOT NULL,
    rows_in    INTEGER NOT NULL DEFAULT 0,
    rows_kept  INTEGER NOT NULL DEFAULT 0,
    rejected   INTEGER NOT NULL DEFAULT 0,
    notes      TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (month, anchor, agent)
);
