"""Точки отказа — структурные, а не «топ по важности».

Критичность у сети уже есть: она в `criticality` каждой сущности и отвечает на вопрос
«насколько эта компания незаменима сама по себе». Точка отказа отвечает на другой вопрос:
**через кого проходят пути**. Это разные вещи, и совпадение списков было бы подозрительным,
а не подтверждающим.

Отбор: betweenness в верхнем дециле ОТНОСИТЕЛЬНО СВОЕГО СЛОЯ. Сравнивать юрисдикцию с
поставщиком питания бессмысленно — у них разная роль в топологии; сравнение внутри слоя
находит того, кто необычно централен для своего места в стеке.

Обоснование не сочиняется: узел удаляется из графа, и считается, сколько пар сущностей
после этого теряют связь вовсе. Это проверяемое число, а не эпитет.
"""

from collections import deque

DECILE = 0.90          # верхний дециль внутри слоя
MIN_BETWEENNESS = 0.01  # ниже этого узел структурно незначим, каким бы ни был его слой
MAX_REPORTED = 12


def _components(adj):
    seen, comps = set(), []
    for start in adj:
        if start in seen:
            continue
        comp, q = set(), deque([start])
        seen.add(start)
        while q:
            v = q.popleft()
            comp.add(v)
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    q.append(w)
        comps.append(comp)
    return comps


def _connected_pairs(adj, exclude=None):
    """Число связных пар среди узлов, ИСКЛЮЧАЯ `exclude`.

    Исключение обязательно: если считать пары вместе с удаляемым узлом, его собственные
    связи попадут в «потерянные», и любой узел будет выглядеть точкой отказа. Сравнивать
    надо одно и то же множество узлов до и после.
    """
    total = 0
    for c in _components(adj):
        k = len(c - {exclude}) if exclude else len(c)
        total += k * (k - 1) // 2
    return total


def _plural(n, one, few, many):
    m10, m100 = n % 10, n % 100
    if m10 == 1 and m100 != 11:
        return one
    if 2 <= m10 <= 4 and not 10 <= m100 < 20:
        return few
    return many


def run(entities, adj, centrality) -> list:
    by_layer = {}
    for e in entities:
        by_layer.setdefault(e["primaryLayer"], []).append(e["id"])

    candidates = []
    for layer, ids in by_layer.items():
        vals = sorted(centrality[i]["betweenness"] for i in ids if i in centrality)
        if not vals:
            continue
        idx = min(len(vals) - 1, int(len(vals) * DECILE))
        threshold = vals[idx]
        for i in ids:
            b = centrality.get(i, {}).get("betweenness", 0.0)
            if b >= max(threshold, MIN_BETWEENNESS) and b > 0:
                candidates.append((i, layer, b))

    candidates.sort(key=lambda x: -x[2])
    names = {e["id"]: e["name"] for e in entities}
    out = []
    for eid, layer, b in candidates[:MAX_REPORTED]:
        # Убрать узел и посчитать, сколько пар теряет связь. Число проверяемое.
        cut = {k: [x for x in v if x != eid] for k, v in adj.items() if k != eid}
        # База считается по ТОМУ ЖЕ множеству узлов, что и после удаления.
        base_pairs = _connected_pairs(adj, exclude=eid)
        lost = base_pairs - _connected_pairs(cut)
        parts = len(_components(cut))
        share = round(100 * lost / base_pairs, 1) if base_pairs else 0.0
        # Обе формулировки строятся из ОДНИХ И ТЕХ ЖЕ посчитанных чисел. Это не
        # перевод: английская фраза собирается своим шаблоном со своим
        # множественным числом, а не подстрочником с русского.
        if lost > 0:
            reason_ru = (f"убрать — и {lost} пар сущностей ({share}% связных пар) теряют "
                         f"путь друг к другу; сеть распадается на {parts} "
                         f"{_plural(parts, 'часть', 'части', 'частей')}")
            reason_en = (f"remove it and {lost} pairs of entities ({share}% of connected "
                         f"pairs) lose their path to each other; the network breaks into "
                         f"{parts} component{'' if parts == 1 else 's'}")
        else:
            reason_ru = (f"через узел проходит больше путей, чем через любого другого в "
                         f"слое {layer} (betweenness {b}), но обходные маршруты "
                         f"сохраняются — связность сети он не держит")
            reason_en = (f"more paths run through this node than through any other in "
                         f"layer {layer} (betweenness {b}), but detours survive — it does "
                         f"not hold the network together")
        out.append({"id": eid, "name": names.get(eid, eid), "layer": layer,
                    "betweenness": b, "pairsLost": lost,
                    "reason": reason_ru, "reasonEn": reason_en})
    return out
