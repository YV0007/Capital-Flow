"""Замкнутые контуры — главный аргумент этой карты.

Цепочка поставок контуров не имеет: она идёт снизу вверх и заканчивается. Экосистема
их имеет, и именно они отвечают на вопрос «почему это держится»: якорь финансирует
лабораторию, лаборатория платит облаку, облако платит якорю.

Направление берётся ТАКИМ, КАК ЗАПИСАНО В РЕБРЕ, без разворотов. Это возможно потому,
что таксономия v2 содержит типы обеих ориентаций сразу: `customer_of` пишется от
покупателя к продавцу (денежное направление), `invests_in` — от инвестора к объекту,
`supplies` — от поставщика к потребителю (товарное). Контур из блюпринта
(`nvidia → openai → coreweave → nvidia`) складывается из типов денежного направления
и находится как есть.

Классификация — из config/nveco_edges.yaml, порядок проверки важен:
  lockin    если есть хоть одно ребро хребта moat    (замок объясняет контур лучше денег)
  financing если есть хоть одно ребро хребта capital (деньги объясняют лучше поставки)
  sales     во всех остальных случаях
"""

import json
import sys

from . import i18n, nveco

MIN_LEN, MAX_LEN = 3, 5
DFS_CAP = 400000        # предохранитель от разрастания, а не проектный предел


def _graph(con):
    adj, meta, names = {}, {}, {}
    for r in con.execute(
            """SELECT e.id, e.type, e.spine, e.strength, e.status,
                      e.source_id AS s, e.target_id AS t,
                      a.name AS sname, b.name AS tname
               FROM nveco_edge e
               JOIN nveco_entity a ON a.id = e.source_id
               JOIN nveco_entity b ON b.id = e.target_id"""):
        cand = {"id": r["id"], "type": r["type"], "spine": r["spine"],
                "strength": r["strength"], "status": r["status"]}
        cur = meta.get((r["s"], r["t"]))
        # Две сущности могут быть соединены несколькими рёбрами в одну сторону
        # (Microsoft и вкладывается в лабораторию, и лицензирует её модели). Одно
        # должно представлять пару в контуре; выбираем детерминированно — сильнейшее,
        # при равенстве по алфавиту, чтобы одни и те же данные давали одни контуры.
        if cur is None:
            adj.setdefault(r["s"], []).append(r["t"])
            meta[(r["s"], r["t"])] = cand
        elif (-cand["strength"], cand["id"]) < (-cur["strength"], cur["id"]):
            meta[(r["s"], r["t"])] = cand
        names[r["s"]], names[r["t"]] = r["sname"], r["tname"]
    return adj, meta, names


def find_cycles(adj, min_len=MIN_LEN, max_len=MAX_LEN, cap=DFS_CAP):
    """Простые ориентированные контуры длиной min_len..max_len.

    Контур выпускается только из лексикографически наименьшего участника, и обход
    никогда не заходит на узел меньше стартового — стандартный приём, который не даёт
    найти один контур по разу на каждый его поворот.
    """
    found, steps = {}, 0
    for start in sorted(adj):
        stack = [(start, [start])]
        while stack:
            node, path = stack.pop()
            steps += 1
            if steps > cap:
                return list(found.values())
            for nxt in adj.get(node, ()):
                if nxt == start and len(path) >= min_len:
                    key = frozenset(path)
                    if key not in found:
                        found[key] = list(path)
                    continue
                if len(path) >= max_len or nxt <= start or nxt in path:
                    continue
                stack.append((nxt, path + [nxt]))
    return list(found.values())


def classify(pairs) -> str:
    """pairs — [(spine, type), …] по всем рёбрам контура.

    `except_types` в правиле снимает с рассмотрения конкретные типы: контур из одних
    закупок идёт по хребту capital, но это сбыт, а не финансирование.
    """
    cfg = nveco.load_edge_types().get("cycle_classification", {})
    for rule in cfg.get("rules", []):
        skip = set(rule.get("except_types") or ())
        if any(sp in rule["if_any_spine"] and ty not in skip for sp, ty in pairs):
            return rule["type"]
    return cfg.get("fallback", "sales")


# Подпись контура строится из ГЛАГОЛОВ типов связей, а не пишется руками, —
# поэтому второй язык не требует перевода: он собирается из verb_en, который
# лежит рядом с verb в той же таксономии. Имена компаний не переводятся ни в
# одной версии: они одинаковы в обеих.
_CYCLE_HEAD = {
    "sales":     ("Контур сбыта", "Sales loop"),
    "financing": ("Контур финансирования", "Financing loop"),
    "lockin":    ("Контур замка", "Lock-in loop"),
}


def _note(path, meta, names, kind):
    """(ru, en) — две параллельные подписи одного контура."""
    types = nveco.edge_types()
    ru_parts, en_parts = [], []
    for a, b in zip(path, path[1:] + [path[0]]):
        etype = meta[(a, b)]["type"]
        spec = types.get(etype, {})
        na, nb = names.get(a, a), names.get(b, b)
        ru_parts.append(f"{na} —{spec.get('verb', etype)}→ {nb}")
        en_parts.append(f"{na} —{spec.get('verb_en', etype)}→ {nb}")
    ru_head, en_head = _CYCLE_HEAD[kind]
    return (f"{ru_head}: " + "; ".join(ru_parts),
            f"{en_head}: " + "; ".join(en_parts))


def run(month: str, anchor: str = None) -> dict:
    acfg = nveco.anchor_cfg(anchor)
    con = nveco.connect()
    i18n.ensure(con)
    adj, meta, names = _graph(con)
    cycles = find_cycles(adj)

    def strength(path):
        return sum(meta[(a, b)]["strength"] for a, b in zip(path, path[1:] + [path[0]]))

    # Детерминированный порядок: сначала короткие, потом сильные, потом по алфавиту —
    # чтобы id c1, c2 … были стабильны между прогонами одних и тех же данных.
    cycles.sort(key=lambda p: (len(p), -strength(p), p))

    con.execute("DELETE FROM nveco_cycle_edge WHERE run_month=?", (month,))
    con.execute("DELETE FROM nveco_cycle WHERE run_month=?", (month,))
    out = []
    for i, path in enumerate(cycles, start=1):
        pairs = list(zip(path, path[1:] + [path[0]]))
        kind = classify([(meta[p]["spine"], meta[p]["type"]) for p in pairs])
        edge_ids = [meta[p]["id"] for p in pairs]
        weakest = min(meta[p]["status"] for p in pairs)   # 'confirmed'<'high…'<'signal'
        note_ru, note_en = _note(path, meta, names, kind)
        rec = {"id": f"c{i}", "type": kind, "path": path + [path[0]],
               "edges": edge_ids, "note": note_ru, "noteEn": note_en,
               "weakest": weakest, "anchored": acfg["id"] in path}
        con.execute(
            """INSERT OR IGNORE INTO nveco_cycle
                 (id,run_month,anchor,cycle_type,path_json,members,note)
               VALUES (?,?,?,?,?,?,?)""",
            (rec["id"], month, acfg["id"], kind, json.dumps(rec["path"]),
             "|".join(sorted(path)), rec["note"]))
        i18n.put(con, "nveco", "cycle", rec["id"], "note", "ru",
                 note_ru, source="generated")
        i18n.put(con, "nveco", "cycle", rec["id"], "note", "en",
                 note_en, source="generated")
        for pos, eid in enumerate(edge_ids):
            con.execute("INSERT OR IGNORE INTO nveco_cycle_edge "
                        "(run_month,cycle_id,position,edge_id) VALUES (?,?,?,?)",
                        (month, rec["id"], pos, eid))
        out.append(rec)
    con.commit()
    con.close()
    return {"cycles": len(out),
            "by_type": {k: sum(1 for c in out if c["type"] == k)
                        for k in ("sales", "financing", "lockin")},
            "anchored": sum(1 for c in out if c["anchored"]),
            "detail": out}


if __name__ == "__main__":
    r = run(sys.argv[1] if len(sys.argv) > 1 else nveco.current_month())
    print(f"{r['cycles']} контуров: {r['by_type']}")
    for c in r["detail"][:10]:
        print(" ", c["id"], c["type"], " -> ".join(c["path"]))
