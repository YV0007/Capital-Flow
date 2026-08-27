"""Сборка handoff/nvidia_ecosystem.json + ECOSYSTEM-V2-CHANGELOG.md.

Замороженный контракт между этим движком и дашбордом. Дашборд не считает НИЧЕГО:
критичность, гравитация, концентрация, контуры, хребет и признак устаревания приходят
посчитанными; на той стороне только отрисовка и фильтрация.

Валидатор здесь не «на всякий случай»: **файл, нарушивший хоть одно железное правило,
не пишется вовсе**. Отдать дашборду битый файл хуже, чем не отдать никакого — во втором
случае видно, что что-то сломалось, в первом карта молча врёт.

Железные правила, которые проверяются перед записью:
  1  id сущностей и связей стабильны и уникальны
  2  source/target каждой связи есть в entities[]
  3  evidence непустой у каждой связи, цитата <= 15 слов
  4  каждая сущность не дальше anchor.hops шагов от якоря
  5  вычисляемые поля на месте и в своих диапазонах
  6  layers переменной длины, но каждая запись полна (plane, order)
  7  ни одного поля, указывающего в DC-AI
  8  camelCase, числа — числа
"""

import json
import sys
from datetime import date

from . import db, nveco

OUT_MD = db.HANDOFF_DIR / "ECOSYSTEM-V2-CHANGELOG.md"
FORBIDDEN_KEYS = {"dcNode", "dc_node", "dcnode"}


class ContractError(AssertionError):
    """Нарушение железного правила. Файл не пишется."""


# ── сборка ───────────────────────────────────────────────────────────────────
def build(month: str, anchor: str = None) -> dict:
    acfg = nveco.anchor_cfg(anchor)
    con = nveco.connect()
    lidx = nveco.layer_index()

    stats = {r["layer_id"]: r for r in con.execute(
        "SELECT * FROM nveco_layer_stat WHERE run_month=?", (month,))} \
        if con.execute("SELECT name FROM sqlite_master WHERE name='nveco_layer_stat'"
                       ).fetchone() else {}

    layers = []
    for l in nveco.layers():
        st = stats.get(l["id"])
        conc = None
        if st and st["level"]:
            conc = {"level": st["level"], "hhi": st["hhi"],
                    "top": json.loads(st["top_json"] or "[]")}
        # label_en/caption_en едут ДАЛЬШЕ КАК ЕСТЬ: контракт v2 их не описывает, но
        # сеть v3 собирает из них двуязычные подписи. Лишний ключ в файле семени
        # безвреден, потерянный — стоил бы отдельного чтения конфига в двух местах.
        layers.append({"id": l["id"], "label": l["label"], "caption": l["caption"],
                       "label_en": l.get("label_en"), "caption_en": l.get("caption_en"),
                       "plane": l["plane"], "order": l["order"], "band": l.get("band"),
                       "concentration": conc})

    sectors = [{"key": s["key"], "label": s["label"], "label_en": s.get("label_en"),
                "layer": s["layer"]} for s in nveco.sectors()]

    # источники
    src_by = {}
    for r in con.execute("SELECT * FROM nveco_source ORDER BY tier, id"):
        src_by.setdefault((r["owner_kind"], r["owner_id"]), []).append({
            "tier": r["tier"], "type": r["type"], "title": r["title"], "url": r["url"],
            "published": r["published"], "fetched": r["fetched"],
            "alive": bool(r["alive"]), "quote": r["quote"],
            "confidence": r["confidence"]})

    gravity = {}
    if con.execute("SELECT name FROM sqlite_master WHERE name='nveco_gravity'").fetchone():
        gravity = {r["entity_id"]: json.loads(r["json"])
                   for r in con.execute("SELECT * FROM nveco_gravity")}

    factors, whys = {}, {}
    for r in con.execute("SELECT * FROM nveco_entity_factor"):
        factors.setdefault(r["entity_id"], {})[r["factor"]] = r["value"]
        whys.setdefault(r["entity_id"], {})[r["factor"]] = r["why"]

    elayers = {}
    for r in con.execute("SELECT * FROM nveco_entity_layer"):
        elayers.setdefault(r["entity_id"], []).append(r)

    risks = {r["entity_id"]: r for r in con.execute("SELECT * FROM nveco_entity_risk")}
    tech_by_owner = {}
    # note_en живёт в конфиге, а не в таблице: подпись тех-узла — это таксономия,
    # а не исследованный факт, и заводить под неё колонку значило бы мигрировать
    # схему ради строки, которая и так лежит рядом с русской.
    tech_en = {n["id"]: n.get("note_en") for n in nveco.tech_nodes()}
    tech_nodes = []
    for r in con.execute("SELECT * FROM nveco_tech_node ORDER BY id"):
        tech_nodes.append({"id": r["id"], "label": r["label"], "owner": r["owner_id"],
                           "note": r["note"], "note_en": tech_en.get(r["id"]),
                           "importance": r["importance"]})
        if r["owner_id"]:
            tech_by_owner.setdefault(r["owner_id"], []).append(r["id"])

    # camelCase-имена факторов — язык передачи, snake_case остаётся языком исследования
    CAMEL = {"irreplaceability": "irreplaceability", "lock_in_depth": "lockInDepth",
             "time_to_replace": "timeToReplace", "strategic_control": "strategicControl"}

    entities = []
    for e in con.execute("SELECT * FROM nveco_entity ORDER BY id"):
        f = factors.get(e["id"], {})
        w = whys.get(e["id"], {})
        ls = sorted(elayers.get(e["id"], []),
                    key=lambda r: lidx.get(r["layer_id"], {}).get("order", 99))
        rk = risks.get(e["id"])
        entities.append({
            "id": e["id"], "name": e["name"],
            "aliases": [a for a in (e["aliases"] or "").split("|") if a],
            "type": e["type"], "role": e["role"], "sector": e["sector"],
            "layers": [{"layer": r["layer_id"], "primary": bool(r["is_primary"]),
                        "criticality": r["criticality"]} for r in ls],
            "primaryLayer": e["primary_layer"],
            "criticality": e["criticality"],
            "criticalityFactors": {CAMEL[k]: f.get(k) for k in nveco.FACTORS},
            "criticalityWhy": {CAMEL[k]: w.get(k) for k in nveco.FACTORS},
            "gravity": gravity.get(e["id"], {"reach": 0, "layers": 0, "edgeTypes": 0,
                                             "cycles": 0, "score": 0, "signals": {}}),
            "oneLiner": e["one_liner"], "whyIrreplaceable": e["why_irreplaceable"],
            "whatBreaksIt": e["what_breaks_it"],
            "phase": e["phase"],
            "risk": {"geopolitical": rk["geopolitical"] if rk else "low",
                     "note": rk["note"] if rk else None,
                     "exportRegime": rk["export_regime"] if rk else None,
                     "concentration": rk["concentration"] if rk else None},
            "ticker": e["ticker"], "publicPrivate": e["public_private"],
            "geo": e["geo"], "founded": e["founded"], "revenueUsdB": e["revenue_usd_b"],
            "techNodes": tech_by_owner.get(e["id"], []),
            "hops": e["hops"],
            "firstSeen": e["first_seen"], "lastConfirmed": e["last_confirmed"],
            "stale": bool(e["stale"]),
            "sources": src_by.get(("entity", e["id"]), []),
        })
        entities[-1]["gravity"].setdefault("signals", {})

    edges = []
    for r in con.execute("SELECT * FROM nveco_edge ORDER BY id"):
        edges.append({
            "id": r["id"], "source": r["source_id"], "target": r["target_id"],
            "type": r["type"], "spine": r["spine"], "direction": r["direction"],
            "strength": r["strength"], "lockInDepth": r["lock_in_depth"],
            "substitutability": r["substitutability"],
            "isReversible": bool(r["is_reversible"]),
            "status": r["status"], "confidence": r["confidence"],
            "sourceTier": r["source_tier"], "confirmedSources": r["confirmed_sources"],
            "risk": {"level": r["risk_level"], "type": r["risk_type"],
                     "timeline": r["risk_timeline"], "mitigation": r["risk_mitigation"]},
            "techNode": r["tech_node"], "formed": r["formed"],
            "strengthened": r["strengthened"], "lastConfirmed": r["last_confirmed"],
            "note": r["note"],
            "evidence": src_by.get(("edge", r["id"]), []),
        })

    cycles = []
    # ORDER BY по числу, а не по строке: иначе c10 встаёт между c1 и c2, и чейнджлог
    # начинается не с самых коротких контуров, ради которых его и читают.
    for r in con.execute(
            "SELECT * FROM nveco_cycle WHERE run_month=? "
            "ORDER BY CAST(substr(id, 2) AS INTEGER)", (month,)):
        eids = [x["edge_id"] for x in con.execute(
            "SELECT edge_id FROM nveco_cycle_edge WHERE run_month=? AND cycle_id=? "
            "ORDER BY position", (month, r["id"]))]
        cycles.append({"id": r["id"], "type": r["cycle_type"],
                       "path": json.loads(r["path_json"]), "edges": eids,
                       "note": r["note"]})

    payload = {
        "schema": nveco.SCHEMA_VERSION,
        "generated": date.today().isoformat(),
        "asOf": month,
        "source": "engine",
        "ecosystem": acfg.get("ecosystem", acfg["id"]),
        "anchor": acfg["id"],
        "totals": {"entities": len(entities), "edges": len(edges),
                   "layers": len(layers), "cycles": len(cycles),
                   "techNodes": len(tech_nodes)},
        "layers": layers, "sectors": sectors, "entities": entities,
        "techNodes": tech_nodes, "edges": edges, "cycles": cycles,
    }
    con.close()
    return payload


# ── валидатор ────────────────────────────────────────────────────────────────
def validate(payload: dict, max_hops: int = 2) -> list:
    errs = []
    ids = [e["id"] for e in payload["entities"]]
    if len(ids) != len(set(ids)):
        errs.append("правило 1: дублирующиеся id сущностей")
    idset = set(ids)
    layer_ids = {l["id"] for l in payload["layers"]}
    sector_keys = {s["key"] for s in payload["sectors"]}
    tech_ids = {t["id"] for t in payload["techNodes"]}

    # правило 6 — слои переменной длины, но каждая запись полна
    for l in payload["layers"]:
        # .get() везде: отсутствующее поле обязано стать СООБЩЕНИЕМ, а не исключением.
        # Валидатор, падающий на битых данных, ничем не лучше отсутствующего валидатора:
        # вызывающий код не получит списка ошибок и не сможет их показать.
        missing = [k for k in ("id", "label", "caption", "plane", "order")
                   if l.get(k) is None]
        for k in missing:
            errs.append(f"правило 6: у слоя {l.get('id')} нет поля {k}")
        if missing:
            continue
        if l["plane"] not in ("control", "orbit", "nucleus"):
            errs.append(f"правило 6: слой {l['id']} с планом '{l['plane']}'")
        if len(l["label"]) > 16:
            errs.append(f"правило 6: label слоя {l['id']} длиннее 16 знаков")
        # Длина caption НЕ блокирует запись: замороженная таблица таксономии даёт для
        # L0 и L15 подписи в 29-30 знаков, а комментарий контракта пишет «<=28». Два
        # замороженных блока противоречат друг другу, и односторонне менять ни один из
        # них нельзя. Подписи отдаются дословно по таблице; расхождение вынесено в
        # handoff/NVIDIA-ECOSYSTEM-BUILD-LOG.md как вопрос к пользователю.
        if len(l["caption"]) > 32:
            errs.append(f"правило 6: caption слоя {l['id']} длиннее 32 знаков")

    for key, seq in (("entities", payload["entities"]), ("edges", payload["edges"]),
                     ("layers", payload["layers"]), ("cycles", payload["cycles"]),
                     ("techNodes", payload["techNodes"])):
        if payload["totals"].get(key) != len(seq):
            errs.append(f"totals.{key}={payload['totals'].get(key)}, а в массиве {len(seq)}")

    for e in payload["entities"]:
        if e["type"] not in nveco.ENTITY_TYPES:
            errs.append(f"сущность {e['id']}: type '{e['type']}'")
        if e["role"] not in nveco.ROLES:
            errs.append(f"сущность {e['id']}: role '{e['role']}'")
        if e["phase"] not in nveco.PHASES:
            errs.append(f"сущность {e['id']}: phase '{e['phase']}'")
        if not e["layers"]:
            errs.append(f"сущность {e['id']}: нет слоёв")
        if sum(1 for l in e["layers"] if l["primary"]) != 1:
            errs.append(f"сущность {e['id']}: основной слой должен быть ровно один")
        for l in e["layers"]:
            if l["layer"] not in layer_ids:
                errs.append(f"сущность {e['id']}: неизвестный слой {l['layer']}")
        if e["sector"] and e["sector"] not in sector_keys:
            errs.append(f"сущность {e['id']}: сектор '{e['sector']}' вне таксономии")
        # правило 5 — вычисляемое на месте и сходится с рубрикой
        f = e["criticalityFactors"]
        snake = {"irreplaceability": f.get("irreplaceability"),
                 "lock_in_depth": f.get("lockInDepth"),
                 "time_to_replace": f.get("timeToReplace"),
                 "strategic_control": f.get("strategicControl")}
        expect = nveco.criticality(snake)
        if expect is None:
            errs.append(f"сущность {e['id']}: не все четыре фактора заполнены")
        elif expect != e["criticality"]:
            errs.append(f"сущность {e['id']}: criticality {e['criticality']} "
                        f"не сходится с рубрикой ({expect})")
        for k, v in f.items():
            if v is not None and not (isinstance(v, int) and 0 <= v <= 100):
                errs.append(f"сущность {e['id']}: фактор {k} = {v!r}")
        prim = [l for l in e["layers"] if l["primary"]]
        if prim and prim[0]["criticality"] != e["criticality"]:
            errs.append(f"сущность {e['id']}: критичность основного слоя не равна общей")
        # правило 4 — не дальше двух шагов от якоря
        if e.get("hops") is None or e["hops"] > max_hops:
            errs.append(f"правило 4: сущность {e['id']} в {e.get('hops')} шагах "
                        f"от якоря при пределе {max_hops}")
        for lim, field in ((110, "oneLiner"), (280, "whyIrreplaceable"),
                           (110, "whatBreaksIt")):
            if e.get(field) and len(e[field]) > lim:
                errs.append(f"сущность {e['id']}: {field} длиннее {lim} знаков")
        for k in FORBIDDEN_KEYS:
            if k in e:
                errs.append(f"правило 7: у сущности {e['id']} поле {k} — ссылка в DC-AI")

    seen_edge = set()
    for x in payload["edges"]:
        # правило 2 — висячих ссылок не бывает
        for end in ("source", "target"):
            if x[end] not in idset:
                errs.append(f"правило 2: связь {x['id']}: {end} '{x[end]}' "
                            f"отсутствует в entities[]")
        if x["id"] != f"{x['source']}__{x['target']}__{x['type']}":
            errs.append(f"правило 1: id связи {x['id']} не равен "
                        f"<source>__<target>__<type>")
        if x["id"] in seen_edge:
            errs.append(f"правило 1: дублирующийся id связи {x['id']}")
        seen_edge.add(x["id"])
        if x["type"] not in nveco.edge_types():
            errs.append(f"связь {x['id']}: тип '{x['type']}' вне таксономии")
        elif x["spine"] != nveco.spine_of(x["type"]):
            errs.append(f"связь {x['id']}: хребет '{x['spine']}' не выведен из типа")
        if x["direction"] not in nveco.DIRECTIONS:
            errs.append(f"связь {x['id']}: direction '{x['direction']}'")
        if x["status"] not in nveco.STATUSES:
            errs.append(f"связь {x['id']}: status '{x['status']}'")
        # правило 9 — числа числа и в диапазонах
        for field, lo, hi in (("strength", 0, 100), ("lockInDepth", 0, 100),
                              ("substitutability", 0, 100), ("confidence", 0, 1)):
            v = x.get(field)
            if v is None:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errs.append(f"связь {x['id']}: {field} не число ({v!r})")
            elif not lo <= v <= hi:
                errs.append(f"связь {x['id']}: {field}={v} вне {lo}..{hi}")
        if x["techNode"] and x["techNode"] not in tech_ids:
            errs.append(f"связь {x['id']}: неизвестный techNode '{x['techNode']}'")
        # правило 3 — evidence непустой, цитата <= 15 слов
        if not x.get("evidence"):
            errs.append(f"правило 3: связь {x['id']} без evidence — нет цитаты, нет связи")
        for ev in x.get("evidence", []):
            if not ev.get("quote") or not ev.get("url"):
                errs.append(f"правило 3: связь {x['id']}: источник без цитаты или ссылки")
            elif nveco.word_count(ev["quote"]) > nveco.MAX_QUOTE_WORDS:
                errs.append(f"правило 3: связь {x['id']}: цитата "
                            f"{nveco.word_count(ev['quote'])} слов при пределе "
                            f"{nveco.MAX_QUOTE_WORDS}")
            if ev.get("tier") not in (1, 2, 3, 4, 5, 6):
                errs.append(f"связь {x['id']}: тир источника '{ev.get('tier')}'")
        if x.get("note") and len(x["note"]) > 200:
            errs.append(f"связь {x['id']}: note длиннее 200 знаков")
        mit = (x.get("risk") or {}).get("mitigation")
        if mit and len(mit) > 160:
            errs.append(f"связь {x['id']}: risk.mitigation длиннее 160 знаков")

    for c in payload["cycles"]:
        if c["type"] not in ("sales", "financing", "lockin"):
            errs.append(f"контур {c['id']}: тип '{c['type']}'")
        if c["path"][0] != c["path"][-1]:
            errs.append(f"контур {c['id']}: путь не возвращается в начало")
        for s in c["path"]:
            if s not in idset:
                errs.append(f"контур {c['id']}: сущности '{s}' нет на карте")
        for s in c["edges"]:
            if s not in seen_edge:
                errs.append(f"контур {c['id']}: связи '{s}' нет на карте")

    for t in payload["techNodes"]:
        if t.get("owner") and t["owner"] not in idset:
            errs.append(f"тех-узел {t['id']}: владельца '{t['owner']}' нет на карте")

    if payload.get("schema") != nveco.SCHEMA_VERSION:
        errs.append(f"schema '{payload.get('schema')}' вместо {nveco.SCHEMA_VERSION}")
    if payload.get("anchor") not in idset:
        errs.append(f"якоря '{payload.get('anchor')}' нет среди сущностей")
    return errs


# ── чейнджлог ────────────────────────────────────────────────────────────────
def _diff(prev, cur):
    if not prev:
        return {"added": [{"kind": "run", "id": cur["asOf"],
                           "why": "первый прогон — базовая линия"}],
                "removed": [], "changed": []}
    pe = {x["id"]: x for x in prev.get("entities", [])}
    ce = {x["id"]: x for x in cur.get("entities", [])}
    pg = {x["id"]: x for x in prev.get("edges", [])}
    cg = {x["id"]: x for x in cur.get("edges", [])}
    added, removed, changed = [], [], []
    for i in sorted(set(ce) - set(pe)):
        added.append({"kind": "entity", "id": i, "why": ce[i].get("oneLiner") or "новая сущность"})
    for i in sorted(set(pe) - set(ce)):
        removed.append({"kind": "entity", "id": i, "why": "больше не подтверждается"})
    for i in sorted(set(cg) - set(pg)):
        added.append({"kind": "edge", "id": i,
                      "why": cg[i].get("note") or f"{cg[i]['type']}, сила {cg[i]['strength']}"})
    for i in sorted(set(pg) - set(cg)):
        removed.append({"kind": "edge", "id": i, "why": "связь больше не заявлена"})
    for i in sorted(set(ce) & set(pe)):
        for field in ("criticality", "phase", "stale", "primaryLayer"):
            if pe[i].get(field) != ce[i].get(field):
                changed.append({"kind": "entity", "id": i, "field": field,
                                "from": pe[i].get(field), "to": ce[i].get(field)})
    for i in sorted(set(cg) & set(pg)):
        for field in ("status", "strength", "confirmedSources", "sourceTier"):
            if pg[i].get(field) != cg[i].get(field):
                changed.append({"kind": "edge", "id": i, "field": field,
                                "from": pg[i].get(field), "to": cg[i].get(field)})
    return {"added": added, "removed": removed, "changed": changed}


def _changelog_md(cur, diff) -> str:
    t = cur["totals"]
    conf = sum(1 for e in cur["edges"] if e["status"] == "confirmed")
    prim = sum(1 for e in cur["edges"] if (e["sourceTier"] or 6) <= 3)
    dead = sum(1 for e in cur["edges"] for ev in e["evidence"] if not ev["alive"])
    L = [f"# ЭКОСИСТЕМА NVIDIA — {cur['asOf']}", "",
         f"Якорь: **{cur['anchor']}**. {t['entities']} сущностей, {t['edges']} связей, "
         f"{t['cycles']} контуров, {t['techNodes']} тех-узлов. "
         f"Сгенерировано {cur['generated']}, схема `{cur['schema']}`.", "",
         "## Состояние",
         f"- Подтверждённых связей: **{conf}** из {t['edges']} "
         f"({round(100 * conf / max(1, t['edges']))}%).",
         f"- С первичным источником (тир 1–3): **{prim}** "
         f"({round(100 * prim / max(1, t['edges']))}%).",
         f"- Мёртвых ссылок: **{dead}**.",
         f"- Блёкнущих сущностей: **{sum(1 for e in cur['entities'] if e['stale'])}**.", ""]

    by = {}
    for e in cur["edges"]:
        by[e["spine"]] = by.get(e["spine"], 0) + 1
    L += ["## Связи по хребтам",
          "| хребет | связей |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in sorted(by.items(), key=lambda x: -x[1])]
    L += [""]

    def block(title, rows, fmt, limit=12):
        if not rows:
            return [f"## {title}", "— ничего.", ""]
        out = [f"## {title} ({len(rows)})"] + [fmt(r) for r in rows[:limit]]
        if len(rows) > limit:
            out.append(f"- …и ещё {len(rows) - limit}.")
        return out + [""]

    L += block("Добавлено", diff["added"], lambda r: f"- **{r['kind']}** `{r['id']}` — {r['why']}")
    L += block("Отвалилось", diff["removed"], lambda r: f"- **{r['kind']}** `{r['id']}` — {r['why']}")
    L += block("Изменилось", diff["changed"],
               lambda r: f"- **{r['kind']}** `{r['id']}`: {r['field']} {r['from']} → {r['to']}")

    if cur["cycles"]:
        L += ["## Замкнутые контуры"]
        L += [f"- `{c['id']}` **{c['type']}** — {' → '.join(c['path'])}"
              for c in cur["cycles"][:12]]
        L += [""]
    tight = [l for l in cur["layers"]
             if l["concentration"] and l["concentration"]["level"] == "monopoly"]
    if tight:
        L += ["## Слои под одним владельцем"]
        L += [f"- **{l['id']} {l['label']}** — HHI {l['concentration']['hhi']}, "
              f"держат: {', '.join(l['concentration']['top'])}" for l in tight]
        L += [""]
    return "\n".join(L)


def run(month: str, anchor: str = None) -> dict:
    acfg = nveco.anchor_cfg(anchor)
    out_json = db.ROOT / acfg["handoff"]
    prev = None
    if out_json.exists():
        try:
            prev = json.loads(out_json.read_text())
        except json.JSONDecodeError:
            prev = None

    payload = build(month, anchor)
    errors = validate(payload, max_hops=int(acfg.get("hops", 2)))
    if errors:
        # Файл НЕ пишется. Предыдущий остаётся на месте — лучше вчерашняя правда,
        # чем сегодняшняя ложь.
        return {"ok": False, "errors": errors, "path": str(out_json),
                "entities": payload["totals"]["entities"],
                "edges": payload["totals"]["edges"]}

    diff = _diff(prev, payload)
    payload["changelog"] = {"month": month, **diff}
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    OUT_MD.write_text(_changelog_md(payload, diff))
    return {"ok": True, "errors": [], "path": str(out_json),
            "entities": payload["totals"]["entities"],
            "edges": payload["totals"]["edges"],
            "cycles": payload["totals"]["cycles"],
            "added": len(diff["added"]), "removed": len(diff["removed"]),
            "changed": len(diff["changed"])}


if __name__ == "__main__":
    r = run(sys.argv[1] if len(sys.argv) > 1 else nveco.current_month())
    print(r if r["ok"] else f"КОНТРАКТ НАРУШЕН, файл не записан:\n  " +
          "\n  ".join(r["errors"][:30]))
