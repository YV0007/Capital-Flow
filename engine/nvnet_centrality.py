"""Центральность: degree и betweenness по неориентированному графу.

Считает ДВИЖОК, не агент и не дашборд — как и всё остальное вычисляемое.

Betweenness — алгоритм Брандеса, чистый Python. networkx в проект не тянется: граф на
сотню узлов Брандес обходит за доли секунды, а лишняя зависимость в конвейере, который
должен работать в непривязанном прогоне, стоит дороже, чем двадцать строк кода.

Направление рёбер намеренно игнорируется. Betweenness отвечает на вопрос «сколько
кратчайших путей рвётся, если убрать этот узел», а рвутся они независимо от того, в
какую сторону нарисована стрелка: поставка и закупка одинаково соединяют две компании.
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


def run(entity_ids, edges) -> dict:
    adj = _adjacency(entity_ids, edges)
    deg = degree(adj)
    btw = betweenness(adj)
    n, m = len(adj), sum(len(v) for v in adj.values()) // 2
    density = round(2 * m / (n * (n - 1)), 4) if n > 1 else 0.0
    return {
        "adjacency": adj,
        "centrality": {k: {"degree": deg[k], "betweenness": btw[k]} for k in adj},
        "density": density,
        "averageDegree": round(sum(deg.values()) / n, 2) if n else 0.0,
        "clusteringCoefficient": clustering_coefficient(adj),
        "uniquePairs": m,
    }
