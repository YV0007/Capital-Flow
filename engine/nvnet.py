"""Общий слой сети v3 — достройка поверх карты, якорной на NVIDIA.

Строится ПОВЕРХ engine/nveco.py, а не рядом: 16 слоёв, 5 хребтов, рубрика критичности,
тиры и правило подтверждения берутся из v2 без единой копии. Здесь только то, что
добавляет контракт v3:

  * реестр пивотов (config/nvnet_pivots.yaml) вместо одного якоря;
  * два новых типа связи (config/nvnet_edges.yaml) поверх 31 типа v2;
  * правило включения «≤2 шагов от ЛЮБОГО пивота» вместо «от единственного якоря».

Семя — handoff/nvidia_ecosystem.json. Оно НЕ переисследуется и не переписывается: это
первый полный прогон, и сеть его поглощает как есть.
"""

import json

import yaml

from . import db, nveco

SCHEMA_VERSION = "ai-ecosystem-network/1"
NETWORK_ID = "ai-infrastructure-complete"

_CFG = {}


def _load(name: str) -> dict:
    if name not in _CFG:
        p = db.CONFIG_DIR / name
        _CFG[name] = (yaml.safe_load(p.read_text()) if p.exists() else {}) or {}
    return _CFG[name]


def load_pivots_cfg() -> dict:
    return _load("nvnet_pivots.yaml")


def pivot_ids() -> list:
    return [p["id"] for p in load_pivots_cfg().get("pivots", [])]


def pivot_groups() -> dict:
    return {p["id"]: p.get("group") for p in load_pivots_cfg().get("pivots", [])}


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
    return db.ROOT / load_pivots_cfg().get("seed", "handoff/nvidia_ecosystem.json")


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


def hops_limit() -> int:
    return int(load_pivots_cfg().get("hops", 2))


def hops_from_pivots(pivots, edges) -> dict:
    """Кратчайшее расстояние до БЛИЖАЙШЕГО пивота по неориентированному графу.

    В v2 точка отсчёта была одна; здесь их 26, и обход стартует сразу со всех — это и
    есть «коллективная мера» вместо одноточечной. Ненаправленность сохранена по той же
    причине, что и в v2: «поставляет» и «покупает у» одинаково делают сущность частью
    сети.
    """
    from collections import deque
    adj = {}
    for e in edges:
        adj.setdefault(e["source"], set()).add(e["target"])
        adj.setdefault(e["target"], set()).add(e["source"])
    dist = {p: 0 for p in pivots}
    q = deque(pivots)
    while q:
        cur = q.popleft()
        for nxt in adj.get(cur, ()):
            if nxt not in dist:
                dist[nxt] = dist[cur] + 1
                q.append(nxt)
    return dist


def release_version(month: str, major: int = None, minor: int = None) -> str:
    """vX.Y-YYYY-MM. X растёт при перестройке формы, Y — при выпуске без ломки формы.

    Номер лежит в config/nvnet_pivots.yaml, а не литералом в коде: выпуск — это решение,
    и оно должно быть видно в конфиге, а не в диффе Python.
    """
    cfg = load_pivots_cfg().get("release", {}) or {}
    return f"v{major or cfg.get('major', 1)}.{minor if minor is not None else cfg.get('minor', 0)}-{month}"


# 10 категорий изменений блюпринта. Первый выпуск заполняет только первые две и
# `newSources`; остальные пусты — это не пробел, а отсутствие предыдущей версии.
CHANGE_CATEGORIES = [
    "newNodes", "removedNodes", "relationshipsAdded", "relationshipsRemoved",
    "relationshipsUpdated", "criticalityShifts", "phaseChanges", "riskEscalations",
    "newSources", "layerChanges",
]
