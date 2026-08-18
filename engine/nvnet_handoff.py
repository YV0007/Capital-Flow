"""Сборка handoff/ai_ecosystem_network.json + валидатор + чейнджлог по 10 категориям.

Контракт v3 РАСШИРЯЕТ v2, а не заменяет: 16 слоёв, 5 хребтов, рубрика, тиры и форма
Source приходят из семени без изменений. Новое здесь — `pivots` вместо `anchor`,
`pivotal` на сущности, `centrality`, блок `network` и версия выпуска.

Как и в v2, файл, не прошедший валидатор, НЕ ПИШЕТСЯ. Предыдущий остаётся: отдать
дашборду битую сеть хуже, чем не отдать новую.
"""

import json
import sys
from datetime import date

from . import db, nveco, nvnet, nvnet_centrality, nvnet_spof, nvnet_subgraphs

OUT_JSON = db.HANDOFF_DIR / "ai_ecosystem_network.json"
OUT_MD = db.HANDOFF_DIR / "AI-ECOSYSTEM-NETWORK-CHANGELOG.md"


class ContractError(AssertionError):
    pass


def build(month: str, net: dict) -> dict:
    seed = net["seed"]
    entities = [net["entities"][k] for k in sorted(net["entities"])]
    edges = [net["edges"][k] for k in sorted(net["edges"])]

    metrics = nvnet_centrality.run([e["id"] for e in entities], edges)
    for e in entities:
        e["centrality"] = metrics["centrality"][e["id"]]

    sub = nvnet_subgraphs.run(entities, edges)
    spof = nvnet_spof.run(entities, metrics["adjacency"], metrics["centrality"])

    pivotal = sum(1 for e in entities if e["pivotal"])
    payload = {
        "schema": nvnet.SCHEMA_VERSION,
        "version": nvnet.release_version(month),
        "generated": date.today().isoformat(),
        "asOf": month,
        "source": "engine",
        "ecosystem": nvnet.NETWORK_ID,
        "pivots": [p for p in nvnet.pivot_ids() if p in net["entities"]],
        "totals": {"entities": len(entities), "edges": len(edges),
                   "layers": len(seed["layers"]), "cycles": len(seed.get("cycles", [])),
                   "techNodes": len(seed.get("techNodes", []))},
        # из семени — дословно, без пересчёта
        "layers": seed["layers"], "sectors": seed["sectors"],
        "techNodes": seed.get("techNodes", []), "cycles": seed.get("cycles", []),
        "entities": entities, "edges": edges,
        "network": {
            "id": nvnet.NETWORK_ID,
            "totalNodes": len(entities), "totalEdges": len(edges),
            "pivotalNodes": pivotal, "secondaryNodes": len(entities) - pivotal,
            "density": metrics["density"],
            "averageDegree": metrics["averageDegree"],
            "clusteringCoefficient": metrics["clusteringCoefficient"],
            "singlePointsOfFailure": spof,
            "subgraphs": sub["subgraphs"],
            "subgraphNotes": sub["notes"],
        },
    }
    return payload


# ── валидатор ────────────────────────────────────────────────────────────────
def validate(payload: dict) -> list:
    errs = []
    if payload.get("schema") != nvnet.SCHEMA_VERSION:
        errs.append(f"schema '{payload.get('schema')}' вместо {nvnet.SCHEMA_VERSION}")
    if "anchor" in payload:
        errs.append("v3: поле anchor заменено на pivots — оба сразу быть не должны")
    if not payload.get("pivots"):
        errs.append("v3: пустой список pivots")

    ids = [e["id"] for e in payload["entities"]]
    if len(ids) != len(set(ids)):
        errs.append("дублирующиеся id сущностей")
    idset = set(ids)
    layer_ids = {l["id"] for l in payload["layers"]}
    tech_ids = {t["id"] for t in payload["techNodes"]}
    types = nvnet.edge_types()

    for p in payload["pivots"]:
        if p not in idset:
            errs.append(f"пивот '{p}' отсутствует среди сущностей")

    hops_limit = nvnet.hops_limit()
    for e in payload["entities"]:
        if "pivotal" not in e or not isinstance(e["pivotal"], bool):
            errs.append(f"сущность {e['id']}: нет булева pivotal")
        c = e.get("centrality") or {}
        if not isinstance(c.get("degree"), int) or c["degree"] < 0:
            errs.append(f"сущность {e['id']}: centrality.degree не целое")
        b = c.get("betweenness")
        if not isinstance(b, (int, float)) or isinstance(b, bool) or not 0 <= b <= 1:
            errs.append(f"сущность {e['id']}: centrality.betweenness вне 0..1")
        if e.get("hops") is None or e["hops"] > hops_limit:
            errs.append(f"сущность {e['id']} в {e.get('hops')} шагах от ближайшего "
                        f"пивота при пределе {hops_limit}")
        if e["role"] not in nveco.ROLES:
            errs.append(f"сущность {e['id']}: role '{e['role']}'")
        if e["phase"] not in nveco.PHASES:
            errs.append(f"сущность {e['id']}: phase '{e['phase']}'")
        if sum(1 for l in e["layers"] if l["primary"]) != 1:
            errs.append(f"сущность {e['id']}: основной слой должен быть ровно один")
        for l in e["layers"]:
            if l["layer"] not in layer_ids:
                errs.append(f"сущность {e['id']}: неизвестный слой {l['layer']}")
        f = e.get("criticalityFactors") or {}
        expect = nveco.criticality({"irreplaceability": f.get("irreplaceability"),
                                    "lock_in_depth": f.get("lockInDepth"),
                                    "time_to_replace": f.get("timeToReplace"),
                                    "strategic_control": f.get("strategicControl")})
        if expect is None:
            errs.append(f"сущность {e['id']}: не все четыре фактора заполнены")
        elif expect != e["criticality"]:
            errs.append(f"сущность {e['id']}: criticality {e['criticality']} "
                        f"не сходится с рубрикой ({expect})")
        if "dcNode" in e:
            errs.append(f"сущность {e['id']}: поле dcNode — ссылка в DC-AI")

    seen = set()
    for x in payload["edges"]:
        for end in ("source", "target"):
            if x[end] not in idset:
                errs.append(f"связь {x['id']}: {end} '{x[end]}' отсутствует в entities[]")
        if x["id"] != f"{x['source']}__{x['target']}__{x['type']}":
            errs.append(f"связь {x['id']}: id не равен <source>__<target>__<type>")
        if x["id"] in seen:
            errs.append(f"дублирующийся id связи {x['id']}")
        seen.add(x["id"])
        if x["type"] not in types:
            errs.append(f"связь {x['id']}: тип '{x['type']}' вне таксономии v2+v3")
        elif x["spine"] != nvnet.spine_of(x["type"]):
            errs.append(f"связь {x['id']}: хребет '{x['spine']}' не выведен из типа")
        if x["status"] not in nveco.STATUSES:
            errs.append(f"связь {x['id']}: status '{x['status']}'")
        for field, lo, hi in (("strength", 0, 100), ("lockInDepth", 0, 100),
                              ("substitutability", 0, 100), ("confidence", 0, 1)):
            v = x.get(field)
            if v is None:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errs.append(f"связь {x['id']}: {field} не число ({v!r})")
            elif not lo <= v <= hi:
                errs.append(f"связь {x['id']}: {field}={v} вне {lo}..{hi}")
        if x.get("techNode") and x["techNode"] not in tech_ids:
            errs.append(f"связь {x['id']}: неизвестный techNode '{x['techNode']}'")
        if not x.get("evidence"):
            errs.append(f"связь {x['id']} без evidence — нет цитаты, нет связи")
        for ev in x.get("evidence", []):
            if not ev.get("quote") or not ev.get("url"):
                errs.append(f"связь {x['id']}: источник без цитаты или ссылки")
            elif nveco.word_count(ev["quote"]) > nveco.MAX_QUOTE_WORDS:
                errs.append(f"связь {x['id']}: цитата {nveco.word_count(ev['quote'])} "
                            f"слов при пределе {nveco.MAX_QUOTE_WORDS}")
            if ev.get("tier") not in (1, 2, 3, 4, 5, 6):
                errs.append(f"связь {x['id']}: тир источника '{ev.get('tier')}'")

    n = payload.get("network") or {}
    for k in ("totalNodes", "totalEdges", "pivotalNodes", "secondaryNodes", "density",
              "averageDegree", "clusteringCoefficient", "singlePointsOfFailure",
              "subgraphs"):
        if k not in n:
            errs.append(f"network: нет поля {k}")
    if n.get("totalNodes") != len(payload["entities"]):
        errs.append("network.totalNodes не равен числу сущностей")
    if n.get("totalEdges") != len(payload["edges"]):
        errs.append("network.totalEdges не равен числу связей")
    if (n.get("pivotalNodes") or 0) + (n.get("secondaryNodes") or 0) != len(payload["entities"]):
        errs.append("network: pivotal + secondary не сходится с общим числом")
    for sg in n.get("subgraphs", []):
        for i in sg.get("nodeIds", []):
            if i not in idset:
                errs.append(f"подграф {sg['id']}: узла '{i}' нет на карте")
        for i in sg.get("edgeIds", []):
            if i not in seen:
                errs.append(f"подграф {sg['id']}: связи '{i}' нет на карте")
    for s in n.get("singlePointsOfFailure", []):
        if s["id"] not in idset:
            errs.append(f"точка отказа '{s['id']}' отсутствует среди сущностей")
        if not s.get("reason"):
            errs.append(f"точка отказа '{s['id']}' без обоснования")
    return errs


# ── чейнджлог по 10 категориям блюпринта ─────────────────────────────────────
def _changelog(prev, cur, net):
    cl = {k: [] for k in nvnet.CHANGE_CATEGORIES}
    cl["month"] = cur["asOf"]
    cl["version"] = cur["version"]
    if not prev:
        # Первый выпуск — не diff против пустоты. Фиксируется, что вошло в сеть и
        # откуда: 106+243 из семени и всё, что добавила достройка.
        cl["baseline"] = {
            "seedEntities": len(net["seed"]["entities"]),
            "seedEdges": len(net["seed"]["edges"]),
            "addedEntities": net["newEntities"],
            "addedEdges": net["newEdges"],
            "note": "первый выпуск сети: семя пилота NVIDIA плюс достройка связей "
                    "пивот↔пивот; категории изменений заполнятся со следующего выпуска",
        }
        cl["newNodes"] = [{"id": e["id"], "why": e.get("oneLiner")}
                          for e in cur["entities"] if e.get("firstSeen") == cur["asOf"]
                          and e["id"] not in {x["id"] for x in net["seed"]["entities"]}]
        cl["relationshipsAdded"] = [
            {"id": x["id"], "why": x.get("note") or x["type"]}
            for x in cur["edges"] if x["id"] not in {y["id"] for y in net["seed"]["edges"]}]
        cl["newSources"] = [{"id": x["id"], "count": len(x["evidence"])}
                            for x in cur["edges"]
                            if x["id"] not in {y["id"] for y in net["seed"]["edges"]}]
        return cl

    pe = {x["id"]: x for x in prev.get("entities", [])}
    ce = {x["id"]: x for x in cur["entities"]}
    pg = {x["id"]: x for x in prev.get("edges", [])}
    cg = {x["id"]: x for x in cur["edges"]}
    cl["newNodes"] = [{"id": i, "why": ce[i].get("oneLiner")} for i in sorted(set(ce) - set(pe))]
    cl["removedNodes"] = [{"id": i, "why": "больше не подтверждается"}
                          for i in sorted(set(pe) - set(ce))]
    cl["relationshipsAdded"] = [{"id": i, "why": cg[i].get("note")}
                                for i in sorted(set(cg) - set(pg))]
    cl["relationshipsRemoved"] = [{"id": i, "why": "связь больше не заявлена"}
                                  for i in sorted(set(pg) - set(cg))]
    for i in sorted(set(cg) & set(pg)):
        for f in ("strength", "status", "confirmedSources"):
            if pg[i].get(f) != cg[i].get(f):
                cl["relationshipsUpdated"].append(
                    {"id": i, "field": f, "from": pg[i].get(f), "to": cg[i].get(f)})
        if (pg[i].get("risk") or {}).get("level") != (cg[i].get("risk") or {}).get("level"):
            cl["riskEscalations"].append(
                {"id": i, "from": (pg[i].get("risk") or {}).get("level"),
                 "to": (cg[i].get("risk") or {}).get("level")})
        if len(pg[i].get("evidence", [])) != len(cg[i].get("evidence", [])):
            cl["newSources"].append({"id": i, "count": len(cg[i].get("evidence", []))})
    for i in sorted(set(ce) & set(pe)):
        a, b = pe[i].get("criticality"), ce[i].get("criticality")
        if a is not None and b is not None and abs(b - a) > 5:
            cl["criticalityShifts"].append({"id": i, "from": a, "to": b})
        if pe[i].get("phase") != ce[i].get("phase"):
            cl["phaseChanges"].append({"id": i, "from": pe[i].get("phase"),
                                       "to": ce[i].get("phase")})
        if pe[i].get("primaryLayer") != ce[i].get("primaryLayer"):
            cl["layerChanges"].append({"id": i, "from": pe[i].get("primaryLayer"),
                                       "to": ce[i].get("primaryLayer")})
    return cl


def _changelog_md(cur, cl, net) -> str:
    n = cur["network"]
    L = [f"# СЕТЬ ИИ-ИНФРАСТРУКТУРЫ — {cur['version']}", "",
         f"{n['totalNodes']} сущностей ({n['pivotalNodes']} пивотов, "
         f"{n['secondaryNodes']} вторичных), {n['totalEdges']} связей. "
         f"Схема `{cur['schema']}`, сгенерировано {cur['generated']}.", "",
         "## Топология",
         f"- Плотность: **{n['density']}** · средняя степень: **{n['averageDegree']}** · "
         f"кластеризация: **{n['clusteringCoefficient']}**.",
         f"- Точек отказа найдено: **{len(n['singlePointsOfFailure'])}**.",
         f"- Подграфов: **{len(n['subgraphs'])}** "
         f"({sum(1 for s in n['subgraphs'] if s.get('degenerate'))} вырожденных).", ""]

    if cl.get("baseline"):
        b = cl["baseline"]
        L += ["## Первый выпуск",
              f"- Из семени пилота NVIDIA: **{b['seedEntities']}** сущностей, "
              f"**{b['seedEdges']}** связей — перенесены без переисследования.",
              f"- Добавлено достройкой: **{b['addedEntities']}** сущность, "
              f"**{b['addedEdges']}** связей пивот↔пивот.",
              f"- {b['note']}.", ""]

    L += ["## Центральность — верх списка", "",
          "| сущность | degree | betweenness | пивот |", "|---|---|---|---|"]
    top = sorted(cur["entities"], key=lambda e: -e["centrality"]["betweenness"])[:10]
    L += [f"| {e['name']} | {e['centrality']['degree']} | "
          f"{e['centrality']['betweenness']} | {'да' if e['pivotal'] else '—'} |"
          for e in top]
    L += [""]

    if n["singlePointsOfFailure"]:
        L += ["## Точки отказа", ""]
        L += [f"- **{s['name']}** ({s['layer']}, betweenness {s['betweenness']}) — {s['reason']}"
              for s in n["singlePointsOfFailure"]]
        L += [""]

    L += ["## Подграфы", ""]
    for s in n["subgraphs"]:
        mark = " — **ВЫРОЖДЕН**" if s.get("degenerate") else ""
        L += [f"- **{s['label']}**{mark}: {len(s['nodeIds'])} узлов, "
              f"{len(s['edgeIds'])} внутренних связей. {s['description']}."]
    for note in n.get("subgraphNotes", []):
        L += [f"  - {note}"]
    L += [""]

    L += ["## Изменения по десяти категориям блюпринта", "",
          "| категория | записей |", "|---|---|"]
    RU = {"newNodes": "новые узлы", "removedNodes": "удалённые узлы",
          "relationshipsAdded": "связи +", "relationshipsRemoved": "связи −",
          "relationshipsUpdated": "связи ~", "criticalityShifts": "сдвиг критичности >5",
          "phaseChanges": "смена фазы", "riskEscalations": "эскалация риска",
          "newSources": "новые источники", "layerChanges": "смена слоя"}
    L += [f"| {RU[k]} | {len(cl.get(k) or [])} |" for k in nvnet.CHANGE_CATEGORIES]
    L += [""]

    added = cl.get("relationshipsAdded") or []
    if added:
        L += [f"## Добавленные связи ({len(added)})", ""]
        L += [f"- `{r['id']}` — {r.get('why') or ''}" for r in added[:25]]
        L += [""]
    return "\n".join(L)


def run(month: str, net: dict) -> dict:
    prev = None
    if OUT_JSON.exists():
        try:
            prev = json.loads(OUT_JSON.read_text())
        except json.JSONDecodeError:
            prev = None
    payload = build(month, net)
    errors = validate(payload)
    if errors:
        return {"ok": False, "errors": errors, "path": str(OUT_JSON)}
    cl = _changelog(prev, payload, net)
    payload["changelog"] = cl
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    OUT_MD.write_text(_changelog_md(payload, cl, net))
    return {"ok": True, "errors": [], "path": str(OUT_JSON),
            "entities": payload["totals"]["entities"],
            "edges": payload["totals"]["edges"],
            "version": payload["version"], "network": payload["network"]}


if __name__ == "__main__":
    from . import nvnet_ingest
    m = sys.argv[1] if len(sys.argv) > 1 else nveco.current_month()
    print(run(m, nvnet_ingest.build(m)))
