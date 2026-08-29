"""Общий словарь и помощники конвейера экосистемы (nveco_*, контракт v4).

Строится ПОВЕРХ engine/db.py, а не рядом с ним: та же база, тот же путь подключения,
тот же резолвинг имён через config/aliases.yaml. Одна компания обязана быть одной
компанией на всех картах репозитория.

Префикс `nveco_` остался от пилота, который был картой одной орбиты. Имя историческое
и переименованию не подлежит: 18 таблиц и 13 модулей посреди миграции контракта — это
чистый риск без выигрыша.

Здесь нет ни одного решения — только чтение замороженных словарей. Слои живут в
config/nveco_layers.yaml, типы связей в config/nveco_edges.yaml, тиры в
config/sources.yaml, реестр издателей в config/entity_domains.yaml, границы карты в
config/nveco_scope.yaml. Ни один идентификатор слоя и ни один тип связи не должен
появиться в Python-коде литералом: добавление семнадцатого слоя обязано быть правкой
YAML, а не правкой движка.
"""

import re
import unicodedata
from datetime import date

import yaml

from . import db

SCHEMA_VERSION = "nvidia-ecosystem/4"
# Идентификатор карты. Стоит в прогоне и в контуре на месте, где до v4 стоял id центра.
SCOPE_ID = "ai-infrastructure"

# Закрытые перечисления контракта. Они дублируют CHECK-констрейнты схемы намеренно:
# ingest обязан отвергнуть строку С ПРИЧИНОЙ, а не уронить транзакцию на констрейнте.
# Акторы решают и отвечают; вещи — принимают на вооружение. Тип отвечает на
# ОДИН вопрос: это действующее лицо или предмет?
ACTOR_TYPES = {"company", "geopolitical", "agency", "research_org", "standards_body"}
THING_TYPES = {"technology", "regulation"}
ENTITY_TYPES = ACTOR_TYPES | THING_TYPES
ROLES = {"producer", "platform", "operator", "demand", "capital", "state"}
PHASES = {"emerging", "scaling", "mature", "at_risk", "declining"}
PUBLIC_PRIVATE = {"public", "private", "government", "academic"}
DIRECTIONS = {"upstream", "downstream", "lateral", "bidirectional"}
# Лестница доказательства. `bilateral` — новый максимум v4: связь, которую в
# СОБСТВЕННЫХ документах утверждают ОБА конца. `disputed` — не ошибка данных, а
# находка: один конец утверждает, второй в своих документах опровергает. Ни то,
# ни другое движок не «решает» сам — он только называет то, что видит.
STATUSES = ("bilateral", "confirmed", "high_confidence", "signal", "disputed")
SIDEDNESS = ("bilateral", "single", "disputed")
RISK_LEVELS = {"critical", "high", "medium", "low"}
RISK_TYPES = {"geopolitical", "substitution", "market", "regulatory", "technical", "none"}
RISK_TIMELINES = {"immediate", "1-2y", "2-5y", "5y+", "ongoing", "none"}
SOURCE_TYPES = {"sec_filing", "earnings_call", "company_pr", "partner_pr", "product_doc",
                "white_paper", "patent", "interview", "conference", "testimony",
                "research", "analyst", "database", "press", "social"}
# Четвёртый фактор сменился. Прежний спрашивал, какой рычаг есть у компании в центре
# карты над этим узлом, и выброшен вместе с самим центром. На его месте
# `concentration` — какую долю СВОЕЙ ФУНКЦИИ узел держит. Это не переименование:
# старая цифра измеряла отношение узла к центру, новая — его положение на собственном
# рынке, и механически одна в другую не переводится.
FACTORS = ("irreplaceability", "lock_in_depth", "time_to_replace", "concentration")

# Веса рубрики. МЕНЯТЬ НЕЛЬЗЯ — они заморожены контрактом.
#   criticality = 0.30·irreplaceability + 0.30·lockInDepth
#               + 0.25·timeToReplace   + 0.15·concentration
FACTOR_WEIGHTS = {"irreplaceability": 0.30, "lock_in_depth": 0.30,
                  "time_to_replace": 0.25, "concentration": 0.15}

# Факторы, без которых критичность не считается ВООБЩЕ. `concentration` в этот
# список не входит: он приезжает досье (Фаза 1), а до тех пор его нет ни у кого, и
# требовать его значило бы обнулить критичность всей карты. См. `criticality()`.
REQUIRED_FACTORS = ("irreplaceability", "lock_in_depth", "time_to_replace")

# Пределы длины русских полей. Это тоже контракт: длинный текст ломает панель.
TEXT_LIMITS = {"one_liner": 110, "why_irreplaceable": 280, "what_breaks_it": 110,
               "note": 200, "risk_mitigation": 160, "why": 120, "geo_risk_note": 200}
MAX_QUOTE_WORDS = 15

_CFG = {}


def _load(name: str) -> dict:
    if name not in _CFG:
        p = db.CONFIG_DIR / name
        _CFG[name] = (yaml.safe_load(p.read_text()) if p.exists() else {}) or {}
    return _CFG[name]


def load_layers() -> dict:
    return _load("nveco_layers.yaml")


def load_edge_types() -> dict:
    return _load("nveco_edges.yaml")


def load_scope() -> dict:
    return _load("nveco_scope.yaml")


def load_entity_domains() -> dict:
    return _load("entity_domains.yaml")


def load_gaps() -> dict:
    """Правила охоты за пропущенными связями. См. engine/nveco_gaps.py."""
    return _load("nveco_gaps.yaml")


def load_watchlist() -> dict:
    return _load("nveco_watchlist.yaml")


def load_sources_cfg() -> dict:
    return _load("sources.yaml")


def connect():
    """Та же база и тот же путь, что у остальных конвейеров."""
    return db.connect()


# ── словари ──────────────────────────────────────────────────────────────────
def layers() -> list:
    return load_layers().get("layers", [])


def layer_ids() -> list:
    return [l["id"] for l in layers()]


def layer_index() -> dict:
    return {l["id"]: l for l in layers()}


def sectors() -> list:
    return load_layers().get("sectors", [])


def sector_index() -> dict:
    return {s["key"]: s for s in sectors()}


def tech_nodes() -> list:
    return load_layers().get("tech_nodes", [])


def criticality_bands() -> list:
    return load_layers().get("criticality_bands", [])


def edge_types() -> dict:
    return load_edge_types().get("types", {})


def spine_of(edge_type: str):
    """Хребет ВЫВОДИТСЯ из типа. Агент его не пишет, дашборд не вычисляет."""
    t = edge_types().get(edge_type)
    return t["spine"] if t else None


def default_direction(edge_type: str):
    t = edge_types().get(edge_type)
    return t.get("default_direction") if t else None


def scope_cfg() -> dict:
    """Границы карты: охват, три проверки членства, правило ядра, пути доставки."""
    cfg = load_scope()
    if not cfg.get("scope") or not cfg.get("membership"):
        raise KeyError("config/nveco_scope.yaml неполон: нужны блоки scope и membership")
    return cfg


def scope_layers() -> list:
    """Слои охвата. Сверяются со списком слоёв: разойдясь, они молча сузили бы карту."""
    return list(scope_cfg()["scope"].get("layers") or [])


def membership_cfg() -> dict:
    return scope_cfg()["membership"]


_ROTATION_DEFAULTS = {"basis": "best_of_two", "core_n": 30, "mid_share": 0.33,
                      "core_cadence_months": 1, "mid_cadence_months": 3,
                      "tail_stale_months": 6, "batch_size": 8, "monthly_budget": 40}


def rotation_cfg() -> dict:
    """Правила ротации. Пороги в конфиге, а не в коде: как часто исследовать узел —
    это решение, и оно должно быть видно в YAML, а не в диффе Python."""
    return {**_ROTATION_DEFAULTS, **(scope_cfg().get("rotation") or {})}


def core_n() -> int:
    return int((scope_cfg().get("core") or {}).get("n", 30))


# ── чей это URL ──────────────────────────────────────────────────────────────
# Реестр издателей разворачивается в два индекса: домен -> {сущности} и CIK ->
# {сущности}. Множество, а не одно значение, потому что один домен законно
# принадлежит нескольким сущностям сразу: developer.nvidia.com — это и NVIDIA, и
# CUDA, и NIM. Побеждает САМОЕ ДЛИННОЕ совпадение, поэтому `developer.nvidia.com/cuda`
# отбирает URL у общего `nvidia.com`, а не наоборот.
_OWNERS = None


def _owner_index() -> dict:
    global _OWNERS
    if _OWNERS is None:
        by_domain, by_cik = {}, {}
        for eid, cfg in (load_entity_domains().get("entities") or {}).items():
            for d in (cfg or {}).get("domains") or []:
                by_domain.setdefault(d.strip().lower().lstrip("."), set()).add(eid)
            cik = (cfg or {}).get("cik")
            if cik:
                by_cik.setdefault(str(cik).lstrip("0"), set()).add(eid)
        _OWNERS = {"domain": by_domain, "cik": by_cik}
    return _OWNERS


def _url_parts(url: str):
    """(host, host+path) в нижнем регистре, без схемы и без www."""
    u = (url or "").strip().lower()
    u = re.sub(r"^[a-z]+://", "", u)
    u = u.split("#", 1)[0].split("?", 1)[0]
    host = u.split("/", 1)[0]
    if host.startswith("www."):
        host, u = host[4:], u[4:]
    return host, u


def url_owners(url: str) -> set:
    """Кто издал этот URL. Пустое множество, если издатель не значится в реестре.

    Домен без «/» матчится по хосту с поддоменами (`nvidia.com` покрывает
    `blogs.nvidia.com`); домен со «/» — по префиксу «хост+путь» (`github.com/pytorch/`
    отбирает у общего хоста ровно репозитории PyTorch). Отдельно проверяется CIK в
    пути EDGAR: sec.gov один на всех, и только номер эмитента говорит, чья это
    отчётность.
    """
    host, hostpath = _url_parts(url)
    if not host:
        return set()
    idx = _owner_index()
    best_len, best = 0, set()
    for d, owners in idx["domain"].items():
        if "/" in d:
            ok = hostpath.startswith(d) or hostpath.startswith(d.rstrip("/"))
        else:
            ok = host == d or host.endswith("." + d)
        if ok and len(d) > best_len:
            best_len, best = len(d), set(owners)
        elif ok and len(d) == best_len:
            best |= set(owners)
    m = re.search(r"/edgar/data/(\d+)", hostpath)
    if m:
        cik_owners = idx["cik"].get(m.group(1).lstrip("0"))
        if cik_owners:
            # Отчётность перебивает домен: sec.gov сам по себе ничей.
            return set(cik_owners)
    return best


def entity_domains(entity_id: str) -> list:
    cfg = (load_entity_domains().get("entities") or {}).get(entity_id) or {}
    return list(cfg.get("domains") or [])


def entity_cik(entity_id: str):
    cfg = (load_entity_domains().get("entities") or {}).get(entity_id) or {}
    return cfg.get("cik")


def has_own_publisher(entity_id: str) -> bool:
    """Есть ли у сущности собственный издатель ВООБЩЕ.

    У закона его нет: текст публикует законодатель. Правило `min_self_sources` для
    такой сущности снимается ровно этим фактом, а не исключением в коде.
    """
    return bool(entity_domains(entity_id) or entity_cik(entity_id))


def publisher_tier(url: str):
    """(tier, type) по ОБЩЕЙ таблице издателей из config/sources.yaml.

    Таблица отвечает на вопрос «что это за издатель по роду», а не «насколько он
    близок к кому-то»: принципал, данные, пресса, третичное. Ни одной строки под
    конкретную компанию в ней больше нет — компании живут в entity_domains.yaml.
    Правила проверяются сверху вниз, побеждает первое совпадение.
    """
    u = (url or "").lower()
    for rule in load_sources_cfg().get("nveco_domain_tiers", []) or []:
        if rule["match"].lower() in u:
            return rule["tier"], rule.get("type")
    return None, None


def source_tier(url: str, subject_id: str = None, counterparty_id: str = None):
    """(tier, type) ОТНОСИТЕЛЬНО ПРЕДМЕТА. Главная функция правки 2.

    Лестница осталась шестиступенчатой, точка отсчёта переехала с одной компании на
    предмет утверждения:

      1  SELF          — издал сам предмет (его домен или его CIK)
      2  COUNTERPARTY  — издал второй конец связи
      2  OTHER         — издала любая ДРУГАЯ сущность, стоящая на карте
      3..6             — общая таблица по роду издателя: принципал, данные,
                         пресса, третичное

    Именно здесь умирает «шкала близости к NVIDIA»: 10-K NVIDIA остаётся тиром 1 там,
    где предмет — сама NVIDIA, и становится тиром 2 везде, где предмет кто-то другой.
    """
    owners = url_owners(url)
    _, ptype = publisher_tier(url)
    if owners:
        if subject_id and subject_id in owners:
            return 1, ptype or _kind_of(url)
        if counterparty_id and counterparty_id in owners:
            return 2, ptype or _kind_of(url)
        return 2, ptype or _kind_of(url)
    tier, t = publisher_tier(url)
    return (tier, t) if tier else (None, None)


def _kind_of(url: str) -> str:
    """Род документа для URL, чей издатель известен по реестру, а таблица издателей
    молчит. Нужен только чтобы не отдавать пустой `type`."""
    u = (url or "").lower()
    if "/edgar/data/" in u:
        return "sec_filing"
    for frag, kind in (("github", "product_doc"), ("/docs", "product_doc"),
                       ("/news", "company_pr"), ("/press", "company_pr"),
                       ("/blog", "company_pr"), ("investor", "earnings_call")):
        if frag in u:
            return kind
    return "company_pr"


def is_self_source(url: str, entity_id: str) -> bool:
    """Издала ли эту ссылку сама сущность. Вход правила `min_self_sources`."""
    return bool(entity_id) and entity_id in url_owners(url)


def tier_confidence(tier: int) -> float:
    """Середина диапазона доверия тира из config/sources.yaml."""
    t = (load_sources_cfg().get("nveco_tiers") or {}).get(tier)
    if not t:
        return 0.5
    lo, hi = t["confidence"]
    return round((lo + hi) / 2, 3)


# ── идентичность ─────────────────────────────────────────────────────────────
def slugify(name: str) -> str:
    """Постоянный ASCII-slug. Переименование = потеря истории, поэтому функция
    обязана остаться детерминированной навсегда."""
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s)


_SEED_IDS = None


def seed_ids() -> dict:
    """{нормализованное имя: id} из config/nveco_watchlist.yaml. Затравка задаёт
    постоянные id: если сущность там есть, агент обязан взять id оттуда."""
    global _SEED_IDS
    if _SEED_IDS is not None:
        return _SEED_IDS
    out = {}
    for cfg in (load_watchlist().get("agents") or {}).values():
        for s in (cfg.get("seeds") or []):
            out[_norm(s["name"])] = s["id"]
            out[_norm(s["id"])] = s["id"]
    _SEED_IDS = out
    return out


def _norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def entity_id(name_or_id: str) -> str:
    """Разрешить имя в постоянный id: сначала алиасы репозитория, потом затравка,
    потом slug."""
    canonical = db.resolve_name(name_or_id)
    seeds = seed_ids()
    for cand in (canonical, name_or_id):
        if _norm(cand) in seeds:
            return seeds[_norm(cand)]
    return slugify(canonical)


def edge_id(source_id: str, target_id: str, edge_type: str) -> str:
    return f"{source_id}__{target_id}__{edge_type}"


# ── даты ─────────────────────────────────────────────────────────────────────
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def current_month() -> str:
    t = date.today()
    return f"{t.year}-{t.month:02d}"


def month_ok(m: str) -> bool:
    return bool(MONTH_RE.match(m or ""))


def months_between(a: str, b: str) -> int:
    if not (month_ok(a) and month_ok(b)):
        return 0
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


def word_count(s: str) -> int:
    return len((s or "").split())


def criticality(factors: dict):
    """0..100 по рубрике. None, если не хватает одного из ТРЁХ обязательных факторов —
    молча подставлять ноль значит соврать про незаполненную оценку.

    `concentration` необязателен и обрабатывается ПЕРЕНОРМИРОВКОЙ, а не нулём.
    Причина: подставить ноль за отсутствующий фактор — это утверждение «доля функции
    у этого узла нулевая», то есть выдуманная цифра с весом 0.15 в каждой оценке
    карты. Перенормировка, наоборот, ничего не выдумывает: она честно говорит, что
    оценка построена на трёх факторах из четырёх.

    Пока `concentration` не заполнен ни у кого (Фаза 0), веса трёх оставшихся
    становятся 0.353 / 0.353 / 0.294 — те же 0.30 / 0.30 / 0.25, делённые на 0.85.
    Как только досье принесёт цифру с цитатой, узел вернётся к четырёхфакторной
    формуле сам, без правки кода. Веса контракта при этом не менялись.
    """
    if any(factors.get(f) is None for f in REQUIRED_FACTORS):
        return None
    have = [f for f in FACTORS if factors.get(f) is not None]
    total = sum(FACTOR_WEIGHTS[f] for f in have)
    if not total:
        return None
    return round(sum(FACTOR_WEIGHTS[f] * factors[f] for f in have) / total)
