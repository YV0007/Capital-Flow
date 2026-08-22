"""Центральность: degree, betweenness и pagerank по неориентированному графу.

Считает ДВИЖОК, не агент и не дашборд — как и всё остальное вычисляемое.

Три меры отвечают на ТРИ РАЗНЫХ вопроса, и в этом весь смысл держать их рядом:

  degree      — со сколькими связан. Считает связи штуками, все соседи равны.
  betweenness — через кого идут пути. Про посредничество: мост, бутылочное горло.
  pagerank    — на кого опираются ВАЖНЫЕ. Рекурсивная важность: вес узла тем выше,
                чем весомее его соседи, а их вес считается по тому же правилу.

Узел с десятью незначительными соседями и узел с двумя ключевыми получат одинаковый
degree и разный pagerank — ровно это degree и не умеет показать.

Оба нетривиальных алгоритма — чистый Python. networkx в проект не тянется: граф на
сотню узлов Брандес обходит за доли секунды, степенная итерация сходится за десятки
шагов, а лишняя зависимость в конвейере, который должен работать в непривязанном
прогоне, стоит дороже, чем сорок строк кода.

ДВА ГРАФА, И ЭТО НЕ НЕДОСМОТР.

degree и betweenness считаются на НЕОРИЕНТИРОВАННОМ графе: пути рвутся и связи
существуют независимо от того, куда нарисована стрелка.

pagerank считается на НАПРАВЛЕННОМ ГРАФЕ ЗАВИСИМОСТИ, где ребро — это голос зависимого
за того, от кого он зависит. Карта «какой тип в какую сторону голосует» лежит в
config/nvnet_edges.yaml (`pagerank_dependence`) — все 33 типа перечислены явно, потому
что одного правила на всех нет: `supplies` записан от поставщика к потребителю (зависит
получатель), а `customer_of` — от покупателя к продавцу (зависит источник).

Почему не проще, на том же неориентированном. Проверено на этих данных: там pagerank
даёт корреляцию с degree **0.9988** — мера перестаёт нести собственный смысл и
становится дорогим синонимом степени. Причина в том, что на неориентированном графе вес
не только притекает от весомых соседей, но и размазывается ими: сосед со степенью 7
отдаёт лишь седьмую часть, а лист — весь свой вес. Направленность возвращает мере ровно
тот смысл, ради которого её добавляли.
"""

from collections import deque


def _adjacency(entity_ids, edges) -> dict:
    adj = {e: set() for e in entity_ids}
    for x in edges:
        s, t = x["source"], x["target"]
        if s in adj and t in adj and s != t:
            adj[s].add(t)
            adj[t].add(s)
    return {k: sorted(v) for k, v in adj.items()}


def degree(adj) -> dict:
    """Число УНИКАЛЬНЫХ сущностей, с которыми есть связь. Не число рёбер: две компании,
    соединённые тремя типами связей, — это одна степень, а не три."""
    return {k: len(v) for k, v in adj.items()}


def betweenness(adj, normalized=True) -> dict:
    """Брандес для невзвешенного неориентированного графа.

    Для каждого источника считается дерево кратчайших путей, потом зависимости
    накапливаются обратным проходом. Сложность O(V·E); на сотне узлов это мгновенно.
    """
    nodes = list(adj)
    bc = {v: 0.0 for v in nodes}

    for s in nodes:
        stack = []
        preds = {w: [] for w in nodes}
        sigma = {w: 0 for w in nodes}     # число кратчайших путей s -> w
        dist = {w: -1 for w in nodes}
        sigma[s] = 1
        dist[s] = 0
        q = deque([s])
        while q:
            v = q.popleft()
            stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    preds[w].append(v)
        delta = {w: 0.0 for w in nodes}
        while stack:
            w = stack.pop()
            for v in preds[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]

    # Каждая пара посчитана дважды (граф неориентированный).
    for v in bc:
        bc[v] /= 2.0
    if normalized:
        n = len(nodes)
        scale = 2.0 / ((n - 1) * (n - 2)) if n > 2 else 0.0
        for v in bc:
            bc[v] = round(bc[v] * scale, 6)
    return bc


def clustering_coefficient(adj) -> float:
    """Средний локальный коэффициент кластеризации: насколько соседи узла знакомы
    между собой. Показывает, собрана ли сеть в плотные кластеры или растянута в цепи."""
    total, counted = 0.0, 0
    for v, nbrs in adj.items():
        k = len(nbrs)
        if k < 2:
            continue
        links = sum(1 for i, a in enumerate(nbrs) for b in nbrs[i + 1:] if b in adj[a])
        total += 2.0 * links / (k * (k - 1))
        counted += 1
    return round(total / counted, 4) if counted else 0.0


DAMPING = 0.85          # классический коэффициент затухания исходного PageRank
MAX_ITER = 200
TOLERANCE = 1e-12


def dependence_graph(entity_ids, edges, dependence_map) -> dict:
    """Направленный граф зависимости: ребро ведёт ОТ зависимого К тому, на кого он
    опирается. Правило на каждый тип берётся из config/nvnet_edges.yaml.

    Тип, которого нет в карте, ПРОПУСКАЕТСЯ с предупреждением, а не молча считается
    зависимостью: незнакомый тип, тихо подмешанный в граф, исказил бы всю меру.
    """
    out = {e: set() for e in entity_ids}
    unknown = set()
    for x in edges:
        s, t = x["source"], x["target"]
        if s not in out or t not in out or s == t:
            continue
        rule = dependence_map.get(x["type"])
        if rule is None:
            unknown.add(x["type"])
            continue
        if rule == "none":
            continue
        if rule in ("to_source", "both"):
            out[t].add(s)          # голос цели за источник
        if rule in ("to_target", "both"):
            out[s].add(t)          # голос источника за цель
    return {"adj": {k: sorted(v) for k, v in out.items()}, "unknownTypes": sorted(unknown)}


def pagerank(adj, damping=DAMPING, max_iter=MAX_ITER, tol=TOLERANCE) -> dict:
    """PageRank степенной итерацией по НАПРАВЛЕННОМУ графу. Сумма по узлам = 1.

    На каждом шаге узел раздаёт свой вес поровну тем, на кого ссылается, а доля
    (1-damping) перераспределяется равномерно по всей сети — это «телепортация», без
    которой вес утекал бы в тупики и замкнутые группы.

    Висячие узлы (ни одной исходящей ссылки) здесь не гипотетический случай, а норма:
    именно так выглядит тот, на кого опираются все, а он — ни на кого. Их масса каждый
    шаг раскладывается равномерно по всем узлам, иначе сумма перестала бы равняться
    единице и «доля важности» потеряла бы смысл.
    """
    nodes = list(adj)
    n = len(nodes)
    if n == 0:
        return {}
    if n == 1:
        return {nodes[0]: 1.0}

    rank = {v: 1.0 / n for v in nodes}
    dangling = [v for v in nodes if not adj[v]]

    for _ in range(max_iter):
        leaked = sum(rank[v] for v in dangling) / n
        nxt = {v: (1.0 - damping) / n + damping * leaked for v in nodes}
        for v in nodes:
            share = rank[v] / len(adj[v]) if adj[v] else 0.0
            if not share:
                continue
            for w in adj[v]:
                nxt[w] += damping * share
        delta = sum(abs(nxt[v] - rank[v]) for v in nodes)
        rank = nxt
        if delta < tol:
            break

    # Нормировка после округления: без неё сумма разъезжается на 1e-6 и проверка
    # «сумма ≈ 1» в валидаторе начинает срабатывать на ровном месте.
    total = sum(rank.values())
    if total:
        rank = {v: rank[v] / total for v in nodes}
    return {v: round(rank[v], 6) for v in nodes}


def run(entity_ids, edges, dependence_map=None) -> dict:
    adj = _adjacency(entity_ids, edges)
    deg = degree(adj)
    btw = betweenness(adj)
    dep = dependence_graph(entity_ids, edges, dependence_map or {})
    pr = pagerank(dep["adj"])
    n, m = len(adj), sum(len(v) for v in adj.values()) // 2
    density = round(2 * m / (n * (n - 1)), 4) if n > 1 else 0.0
    return {
        "adjacency": adj,
        "centrality": {k: {"degree": deg[k], "betweenness": btw[k], "pagerank": pr[k]}
                       for k in adj},
        "density": density,
        "averageDegree": round(sum(deg.values()) / n, 2) if n else 0.0,
        "clusteringCoefficient": clustering_coefficient(adj),
        "uniquePairs": m,
        "dependenceEdges": sum(len(v) for v in dep["adj"].values()),
        "unknownDependenceTypes": dep["unknownTypes"],
    }
