"""Общий словарь и помощники конвейера «Экосистема NVIDIA» (v2).

Строится ПОВЕРХ engine/db.py, а не рядом с ним: та же база, тот же путь подключения,
тот же резолвинг имён через config/aliases.yaml. NVIDIA обязана быть одной NVIDIA на
всех картах репозитория.

Здесь нет ни одного решения — только чтение замороженных словарей. Слои живут в
config/nveco_layers.yaml, типы связей в config/nveco_edges.yaml, тиры в
config/sources.yaml. Ни один идентификатор слоя и ни один тип связи не должен
появиться в Python-коде литералом: добавление семнадцатого слоя обязано быть правкой
YAML, а не правкой движка.
"""

import re
import unicodedata
from datetime import date

import yaml

from . import db

SCHEMA_VERSION = "nvidia-ecosystem/2"

# Закрытые перечисления контракта. Они дублируют CHECK-констрейнты схемы намеренно:
# ingest обязан отвергнуть строку С ПРИЧИНОЙ, а не уронить транзакцию на констрейнте.
ENTITY_TYPES = {"company", "geopolitical", "agency", "research_org", "standards_body"}
ROLES = {"producer", "platform", "operator", "demand", "capital", "state"}
PHASES = {"emerging", "scaling", "mature", "at_risk", "declining"}
PUBLIC_PRIVATE = {"public", "private", "government", "academic"}
DIRECTIONS = {"upstream", "downstream", "lateral", "bidirectional"}
STATUSES = ("confirmed", "high_confidence", "signal")
RISK_LEVELS = {"critical", "high", "medium", "low"}
RISK_TYPES = {"geopolitical", "substitution", "market", "regulatory", "technical", "none"}
RISK_TIMELINES = {"immediate", "1-2y", "2-5y", "5y+", "ongoing", "none"}
SOURCE_TYPES = {"sec_filing", "earnings_call", "company_pr", "partner_pr", "product_doc",
                "white_paper", "patent", "interview", "conference", "testimony",
                "research", "analyst", "database", "press", "social"}
FACTORS = ("irreplaceability", "lock_in_depth", "time_to_replace", "strategic_control")

# Веса рубрики. МЕНЯТЬ НЕЛЬЗЯ — они заморожены контрактом.
#   criticality = 0.30·irreplaceability + 0.30·lockInDepth
#               + 0.25·timeToReplace   + 0.15·strategicControl
FACTOR_WEIGHTS = {"irreplaceability": 0.30, "lock_in_depth": 0.30,
                  "time_to_replace": 0.25, "strategic_control": 0.15}

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


def load_anchors() -> dict:
    return _load("nveco_anchors.yaml")


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


def anchor_cfg(anchor: str = None) -> dict:
    cfg = load_anchors()
    key = anchor or cfg.get("default")
    a = (cfg.get("anchors") or {}).get(key)
    if not a:
        raise KeyError(f"якорь '{key}' не найден в config/nveco_anchors.yaml")
    return a


def domain_tier(url: str):
    """(tier, type) по карте доменов из config/sources.yaml, или (None, None).

    Тир — свойство источника, а не мнение агента, поэтому ingest сверяет заявленный
    тир с этой картой и предупреждает при расхождении. Правила проверяются сверху вниз,
    побеждает первое совпадение.
    """
    u = (url or "").lower()
    for rule in load_sources_cfg().get("nveco_domain_tiers", []) or []:
        if rule["match"].lower() in u:
            return rule["tier"], rule.get("type")
    return None, None


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
    """0..100 из четырёх факторов. None, если хоть одного не хватает — молча
    подставлять ноль значит соврать про незаполненную оценку."""
    if any(factors.get(f) is None for f in FACTORS):
        return None
    return round(sum(FACTOR_WEIGHTS[f] * factors[f] for f in FACTORS))
