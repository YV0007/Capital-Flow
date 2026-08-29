"""Сетевой слой карты — достройка и вычисленные меры поверх семени.

Строится ПОВЕРХ engine/nveco.py, а не рядом: 16 слоёв, 5 хребтов, рубрика критичности,
тиры и правило подтверждения берутся оттуда без единой копии. Здесь только то, что
добавляет сетевой контракт:

  * два новых типа связи (config/nvnet_edges.yaml) поверх 31 типа семени;
  * `integration` — вычисленный ранг узла в графе, и выведенное из него ядро.

ЧТО УШЛО В v4. Реестра центров больше нет. До неё членство считалось шагами до
ближайшего из 27 назначенных пивотов, а сам список лежал в конфиге и был ВХОДОМ.
Теперь состав ядра — ВЫХОД: верхние N по integration.score, пересчёт каждый прогон,
список руками не ведётся нигде. Границу карты держат три проверки членства из
config/nveco_scope.yaml, и ни одна из них не называет ни одной компании.

Семя — handoff/nvidia_ecosystem.json. Оно НЕ переисследуется и не переписывается.
"""

import json

import yaml

from . import db, nveco

# /4 — ЛОМАЮЩАЯ правка формы, поэтому major, а не третий аддитивный шаг.
# Ушло: entities[].hops, criticalityFactors.strategicControl, корневой ecosystem.
# Пришло: entities[].integration (основной ранг), .sourcing, .core, .domains, .cik;
#         edges[].sidedness, .claimedBy, .counterEvidence; корневой meta.
# `pivotal` остаётся ровно на этот выпуск зеркалом `core` и удаляется в /5.
SCHEMA_VERSION = "ai-ecosystem-network/4"
NETWORK_ID = "ai-infrastructure-complete"

_CFG = {}


def _load(name: str) -> dict:
    if name not in _CFG:
        p = db.CONFIG_DIR / name
        _CFG[name] = (yaml.safe_load(p.read_text()) if p.exists() else {}) or {}
    return _CFG[name]


def load_release_cfg() -> dict:
    return _load("nvnet_pivots.yaml")


def integration_weights() -> dict:
    """Веса меры интеграции. Правятся конфигом, не кодом — см. nvnet_edges.yaml."""
    w = _load("nvnet_edges.yaml").get("integration_weights") or {}
    if not w:
        raise KeyError("config/nvnet_edges.yaml: нет блока integration_weights")
    total = sum(w.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"integration_weights в сумме дают {total}, а должны 1.0")
    return w


_TYPES = None


def edge_types() -> dict:
    """31 тип v2 ПЛЮС 2 типа v3. Расширение подмешивается только здесь — месячный
    конвейер v2 продолжает видеть ровно свои 31 и остаётся самосогласованным."""
    global _TYPES
    if _TYPES is None:
        _TYPES = dict(nveco.edge_types())
        _TYPES.update(_load("nvnet_edges.yaml").get("types", {}))
    return _TYPES


def spine_of(edge_type: str):
    t = edge_types().get(edge_type)
    return t["spine"] if t else None


def default_direction(edge_type: str):
    t = edge_types().get(edge_type)
    return t.get("default_direction") if t else None


def pagerank_dependence() -> dict:
    """{тип связи: to_source|to_target|both|none} из config/nvnet_edges.yaml.
    Направление голоса зависимости для PageRank; см. комментарий в конфиге."""
    return _load("nvnet_edges.yaml").get("pagerank_dependence", {}) or {}


def seed_path():
    return db.ROOT / load_release_cfg().get("seed", "handoff/nvidia_ecosystem.json")


def load_seed() -> dict:
    p = seed_path()
    if not p.exists():
        raise FileNotFoundError(
            f"нет семени {p} — сначала нужен полный прогон run_nvidia.py")
    d = json.loads(p.read_text())
    if d.get("schema") != nveco.SCHEMA_VERSION:
        raise ValueError(f"семя имеет схему '{d.get('schema')}', ожидалась "
                         f"'{nveco.SCHEMA_VERSION}'")
    return d


def release_version(month: str, major: int = None, minor: int = None) -> str:
    """vX.Y-YYYY-MM. X растёт при перестройке формы, Y — при выпуске без ломки формы.

    Номер лежит в config/nvnet_pivots.yaml, а не литералом в коде: выпуск — это решение,
    и оно должно быть видно в конфиге, а не в диффе Python.
    """
    cfg = load_release_cfg().get("release", {}) or {}
    return f"v{major or cfg.get('major', 1)}.{minor if minor is not None else cfg.get('minor', 0)}-{month}"


# Категории изменений. Первый выпуск заполняет только первые две и `newSources`;
# остальные пусты — это не пробел, а отсутствие предыдущей версии.
#
# `coreChanges` добавлена в /4 и стоит особняком от остальных десяти. Те отвечают на
# «что изменилось в данных»; эта — на «кого карта СТАЛА считать глубже вшитым, чем
# месяц назад». Раньше такой категории и быть не могло: состав центров лежал в
# конфиге, менялся правкой файла и потому не был событием карты. Теперь он выход
# вычисления, и его движение — такая же находка, как новая связь.
CHANGE_CATEGORIES = [
    "newNodes", "removedNodes", "relationshipsAdded", "relationshipsRemoved",
    "relationshipsUpdated", "criticalityShifts", "phaseChanges", "riskEscalations",
    "newSources", "layerChanges", "coreChanges",
]
