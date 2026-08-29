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
-- Сущность. Компания, государство, агентство, стандарт — всё, что работает хотя бы
-- в одном слое охвата (config/nveco_scope.yaml).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS nveco_entity (
    id             TEXT PRIMARY KEY,        -- slug ('tsmc'); СТАБИЛЕН между прогонами
    name           TEXT NOT NULL,
    aliases        TEXT,                    -- '|'-список; резолвинг идёт через entity_aliases
    -- ДЕЙСТВУЮЩИЕ ЛИЦА против ВЕЩЕЙ. Актор может решать, покупать, судиться и
    -- отвечать; вещь только принимают на вооружение или применяют. CUDA рядом с
    -- NVIDIA в одном типе читалась как компания — отсюда разделение.
    type           TEXT NOT NULL CHECK (type IN
                     ('company','geopolitical','agency','research_org','standards_body',
                      'technology','regulation')),
    role           TEXT NOT NULL CHECK (role IN
                     ('producer','platform','operator','demand','capital','state')),
    -- Официальный домен сущности. Заполняется ТОЛЬКО когда проверен: гадать
    -- нельзя — oracle.ai проходит проверку по имени, не будучи Oracle.
    -- Пусто лучше, чем неверно: дашборд просто не рисует ссылку.
    domain         TEXT,
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
    first_seen     TEXT,                    -- YYYY-MM, пишется один раз
    last_confirmed TEXT,
    -- Какой агент написал эту строку в последний раз. Нужен для правила
    -- «молчание — не свидетельство»: строку имеет право снять с карты
    -- только тот агент, который в этом месяце реально выдал файл.
    owner_agent    TEXT,
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

-- До четырёх строк на сущность. Фактор и его обоснование живут вместе — так
-- criticalityWhy собирается без отдельной таблицы, и невозможно записать оценку,
-- забыв объяснить её.
--
-- v4: `strategic_control` («рычаг якоря над узлом») выброшен вместе с якорем;
-- на его месте `concentration` («какую долю СВОЕЙ ФУНКЦИИ узел держит»). Строк
-- может быть три: `concentration` приезжает досье, и до тех пор критичность
-- считается перенормировкой по трём — см. nveco.criticality().
CREATE TABLE IF NOT EXISTS nveco_entity_factor (
    entity_id TEXT NOT NULL REFERENCES nveco_entity(id) ON DELETE CASCADE,
    factor    TEXT NOT NULL CHECK (factor IN
                ('irreplaceability','lock_in_depth','time_to_replace','concentration')),
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
    -- v4: два новых значения. `bilateral` — оба конца утверждают связь в СВОИХ
    -- документах (строго сильнее прежнего «два источника тира 1–2»). `disputed` —
    -- один конец утверждает, второй в своих документах опровергает; это находка,
    -- а не ошибка, и движок её не «решает».
    status          TEXT NOT NULL DEFAULT 'signal' CHECK (status IN
                      ('bilateral','confirmed','high_confidence','signal','disputed')),
    -- Сколько сторон подтвердило связь СОБСТВЕННЫМИ документами. Считается по
    -- config/entity_domains.yaml, агент назначить его не может.
    sidedness       TEXT CHECK (sidedness IN ('bilateral','single','disputed')),
    claimed_by      TEXT,                  -- '|'-набор id концов, издавших свою цитату
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
    -- См. nveco_entity.owner_agent — то же правило для связей.
    owner_agent     TEXT,
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
    -- v4: чьё это слово. self_of — id конца, издавшего ссылку (NULL, если издатель
    -- не сторона утверждения); counter — цитата ПРОТИВОПОЛОЖНОЙ стороны, из-за
    -- которой связь получает статус `disputed`. Обе колонки считает движок по
    -- config/entity_domains.yaml, агент их не пишет.
    self_of    TEXT,
    counter    INTEGER NOT NULL DEFAULT 0,
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
    scope_id   TEXT NOT NULL,              -- какая карта; v4: network_id охвата
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

-- Прогон. scope_id живёт ЗДЕСЬ, а не в сущности: сущность может стоять на нескольких
-- картах, а прогон всегда ровно про одну.
CREATE TABLE IF NOT EXISTS nveco_run (
    id         INTEGER PRIMARY KEY,
    month      TEXT NOT NULL,
    scope_id   TEXT NOT NULL,
    agent      TEXT NOT NULL,
    rows_in    INTEGER NOT NULL DEFAULT 0,
    rows_kept  INTEGER NOT NULL DEFAULT 0,
    rejected   INTEGER NOT NULL DEFAULT 0,
    notes      TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (month, scope_id, agent)
);

-- ── ОБРАТНАЯ СВЯЗЬ ПО ОТКАЗАМ ────────────────────────────────────────────────
-- Отказ, лежащий в CSV, — это не обратная связь, а запись в архиве. Фаза 0 доказала
-- это на Carl Zeiss SMT: правило шагов выбрасывало его каждый прогон, писало причину
-- в runs/<месяц>/_rejected/nveco-silicon.csv, файл лежал в репозитории закоммиченным
-- и не был прочитан ни разу. Механика писала — не читал никто.
--
-- Три причины, по которым файл не мог сработать, и что тут против каждой:
--   1. Файл жил ровно один прогон: ingest чистит каталог перед записью нового.
--      Здесь — строка живёт, пока её не сняли, и помнит, сколько прогонов подряд
--      повторялась (`times`).
--   2. Отказ ПО СУЩНОСТИ невозможно было доставить: пакетчик собирает пакет по
--      сущностям базы, а отклонённой сущности в базе по определению нет.
--      Здесь — `subject_id`/`subject_name` стоят отдельными колонками, и пакетчик
--      отдаёт такие отказы вне пакета, списком «отклонено, на карту не попало».
--   3. Никто не проверял, что отказ прочитан. Здесь — `status` и `decided_month`:
--      строка обязана быть либо снята исправлением, либо решена явно.
CREATE TABLE IF NOT EXISTS nveco_rejection (
    key           TEXT PRIMARY KEY,        -- agent|file|subject|reason, без номера строки
    agent         TEXT NOT NULL,
    file          TEXT NOT NULL,           -- entities.csv | edges.csv | sources.csv
    reason        TEXT NOT NULL,
    row           TEXT NOT NULL,           -- отклонённая строка как её видел ingest
    subject_kind  TEXT NOT NULL CHECK (subject_kind IN ('entity','edge','source','?')),
    subject_id    TEXT,                    -- id сущности/связи, если он в строке был
    subject_name  TEXT,                    -- имя: отклонённая сущность в базу не попала
    first_seen    TEXT NOT NULL,           -- месяц первого отказа
    last_seen     TEXT NOT NULL,           -- месяц последнего
    times         INTEGER NOT NULL DEFAULT 1,
    status        TEXT NOT NULL DEFAULT 'open'
                  CHECK (status IN ('open','resolved','admitted','dismissed','queued')),
    decision      TEXT,                    -- чем решено, если решено
    decided_month TEXT
);

-- Очередь кандидатов. Живёт в базе, а не только в runs/<месяц>/_queue/candidates.csv:
-- CSV перезаписывается каждым прогоном dossier_split, и нерешённый кандидат исчезал бы
-- вместе с месяцем, который его назвал. Каждая строка обязана получить решение с
-- причиной — это критерий приёмки Фазы 2, и проверяет его tools/feedback_check.py.
CREATE TABLE IF NOT EXISTS nveco_candidate (
    key           TEXT PRIMARY KEY,        -- нормализованное имя кандидата
    name          TEXT NOT NULL,
    named_by      TEXT NOT NULL,           -- id узла, чьё досье его назвало
    why           TEXT,
    url           TEXT,
    quote         TEXT,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    times         INTEGER NOT NULL DEFAULT 1,
    origin        TEXT NOT NULL DEFAULT 'dossier'
                  CHECK (origin IN ('dossier','rejection')),
    status        TEXT NOT NULL DEFAULT 'open'
                  CHECK (status IN ('open','accepted','rejected','on_map')),
    decision      TEXT,                    -- ПРИЧИНА. Молча не решается ничего.
    decided_month TEXT,
    entity_id     TEXT                     -- id на карте, если принят или уже стоит
);
