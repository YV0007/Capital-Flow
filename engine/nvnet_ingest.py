"""Сборка сети: семя v2 + достройка v3.

Семя — handoff/nvidia_ecosystem.json — переносится ЦЕЛИКОМ и без изменений: 106
сущностей и 243 связи это первый полный прогон, и переисследовать его нельзя. Правки
ровно три, все механические:

  * `core` и его зеркало `pivotal` — ВЫЧИСЛЯЮТСЯ по integration в nvnet_handoff;
  * членство держат три проверки охвата, а не расстояние до назначенного центра;
  * добавляются новые сущности и связи из runs/<month>/nvnet-*/ .

Новые строки проходят те же проверки, что в v2 (тип связи существует, цитата ≤15 слов,
источник — резолвленный документ), плюс два новых типа из config/nvnet_edges.yaml.
Отклонённые строки пишутся в runs/<month>/_rejected/, как и раньше.
"""

import csv
import json
import sys
from datetime import date

from . import db, nveco, nvnet
from .ingest import is_search_url
from .nveco_ingest import (_owned_by, _retiring_agents, _validate_entity,
                           _validate_factors, _validate_source, WHY_COLUMNS)

CAMEL = {"concentration": "concentration",
         "irreplaceability": "irreplaceability", "lock_in_depth": "lockInDepth",
         "time_to_replace": "timeToReplace"}


def _read(path):
    with path.open(newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            yield i, row


def _validate_edge(row, types):
    """Тот же контроль, что в v2, но по расширенному списку типов."""
    errors, warnings = [], []
    src = (row.get("source") or "").strip()
    tgt = (row.get("target") or "").strip()
    if not src:
        errors.append("нет source")
    if not tgt:
        errors.append("нет target")
    etype = (row.get("type") or "").strip().lower()
    if etype not in types:
        errors.append(f"тип связи '{etype}' нет ни в v2, ни в расширении v3")
    direction = ((row.get("direction") or "").strip().lower()
                 or nvnet.default_direction(etype) or "downstream")
    if direction not in nveco.DIRECTIONS:
        errors.append(f"direction '{direction}' не из перечисления")

    def _int(v, lo, hi, name, hard=True):
        s = (v or "").strip()
        if s == "":
            return None
        try:
            n = int(float(s))
        except ValueError:
            (errors if hard else warnings).append(f"{name}: не число '{s}'")
            return None
        if not lo <= n <= hi:
            (errors if hard else warnings).append(f"{name}: {n} вне {lo}..{hi}")
            return None
        return n

    strength = _int(row.get("strength"), 0, 100, "strength")
    if strength is None and not errors:
        errors.append("нет strength")
    lock = _int(row.get("lock_in_depth"), 0, 100, "lock_in_depth", hard=False)
    subst = _int(row.get("substitutability"), 0, 100, "substitutability", hard=False)

    for name, allowed in (("risk_level", nveco.RISK_LEVELS),
                          ("risk_type", nveco.RISK_TYPES),
                          ("risk_timeline", nveco.RISK_TIMELINES)):
        v = (row.get(name) or "").strip().lower() or None
        if v and v not in allowed:
            errors.append(f"{name} '{v}' не из перечисления")
    note = (row.get("note") or "").strip()
    if note and len(note) > nveco.TEXT_LIMITS["note"]:
        errors.append(f"note: {len(note)} знаков при пределе {nveco.TEXT_LIMITS['note']}")
    mit = (row.get("risk_mitigation") or "").strip()
    if mit and len(mit) > nveco.TEXT_LIMITS["risk_mitigation"]:
        errors.append(f"risk_mitigation: {len(mit)} знаков при пределе 160")
    if errors:
        return None, errors, warnings
    return {
        "source": src, "target": tgt, "type": etype, "spine": nvnet.spine_of(etype),
        "direction": direction, "strength": strength, "lockInDepth": lock,
        "substitutability": subst,
        "isReversible": (row.get("is_reversible") or "true").strip().lower()
                        not in ("false", "0", "no", "нет"),
        "risk": {"level": (row.get("risk_level") or "").strip().lower() or None,
                 "type": (row.get("risk_type") or "").strip().lower() or None,
                 "timeline": (row.get("risk_timeline") or "").strip().lower() or None,
                 "mitigation": mit or None},
        "techNode": (row.get("tech_node") or "").strip() or None,
        "formed": (row.get("formed") or "").strip() or None,
        "strengthened": (row.get("strengthened") or "").strip() or None,
        "note": note or None,
        "origin": (row.get("origin") or "").strip() or None,
    }, [], warnings


def _status_and_confidence(tiers, claimed=(), disputed=False):
    """Одно правило подтверждения на обе половины карты — импортом, не копией."""
    from .nveco_score import _status_and_confidence as f
    return f(tiers, claimed, disputed)


def build(month: str) -> dict:
    seed = nvnet.load_seed()
    types = nvnet.edge_types()
    today = date.today().isoformat()

    entities = {e["id"]: dict(e) for e in seed["entities"]}
    edges = {e["id"]: dict(e) for e in seed["edges"]}
    problems, rejects = [], []
    # Владельцы строк достройки и размеры их файлов — рядом с данными, а не внутри
    # них: сущность и связь уезжают в файл передачи как есть, и лишнее поле там
    # уронил бы валидатор контракта. Оба словаря нужны persist'у, чтобы снять с
    # карты то, что из CSV исчезло, и только за теми каталогами, кто в этом месяце
    # действительно сдал файл.
    owners = {"entity": {}, "edge": {}}
    per_file = {}                       # (каталог, файл) -> сколько строк БЫЛО

    # ── достройка из runs/<month>/nvnet-*/ ────────────────────────────────────
    month_dir = db.RUNS_DIR / month
    new_ent, new_edge, new_src = 0, 0, 0
    factors_by_ent = {}
    src_by_owner = {}
    sector_idx = nveco.sector_index()
    layer_ids = set(nveco.layer_ids())

    agent_dirs = sorted(p for p in month_dir.iterdir()
                        if p.is_dir() and p.name.startswith("nvnet-")) \
        if month_dir.is_dir() else []

    for adir in agent_dirs:
        # Каждый файл читается НЕЗАВИСИМО от соседей. Раньше здесь стоял `continue` по
        # отсутствию entities.csv, и каталог без сущностей выпадал целиком вместе со
        # своими sources.csv — так каталог достройки `nvnet-detail`, где сущностей нет
        # по замыслу, молча терял все источники, а цифры в detail оставались
        # неподтверждёнными. Отсутствие одного файла — не повод не читать остальные.
        f = adir / "entities.csv"
        if not f.exists():
            f = None
        else:
            per_file[(adir.name, "entities.csv")] = 0
        for line, row in (_read(f) if f else ()):
            per_file[(adir.name, "entities.csv")] += 1
            clean, errs, warns = _validate_entity(row, layer_ids, sector_idx)
            problems += [f"{adir.name}/entities.csv:{line} {w}" for w in warns]
            if errs:
                rejects.append({"file": f"{adir.name}/entities.csv", "line": line,
                                "reason": "; ".join(errs), "row": str(row)[:300]})
                continue
            if clean["id"] in entities:
                problems.append(f"{adir.name}/entities.csv:{line} сущность "
                                f"'{clean['id']}' уже есть в семени — пропущена")
                continue
            entities[clean["id"]] = {
                "id": clean["id"], "name": clean["name"],
                "aliases": [a for a in (clean["aliases"] or "").split("|") if a],
                "type": clean["type"], "role": clean["role"], "sector": clean["sector"],
                "layers": [{"layer": l, "primary": l == clean["primary_layer"],
                            "criticality": None} for l in clean["layers"]],
                "primaryLayer": clean["primary_layer"],
                "criticality": None, "criticalityFactors": {}, "criticalityWhy": {},
                "gravity": {"reach": 0, "layers": 0, "edgeTypes": 0, "cycles": 0,
                            "score": 0, "signals": {}},
                "oneLiner": clean["one_liner"],
                "whyIrreplaceable": clean["why_irreplaceable"],
                "whatBreaksIt": clean["what_breaks_it"], "phase": clean["phase"],
                "risk": {"geopolitical": clean["geo_risk"], "note": clean["geo_risk_note"],
                         "exportRegime": clean["export_regime"],
                         "concentration": clean["concentration"]},
                "ticker": clean["ticker"], "publicPrivate": clean["public_private"],
                "geo": clean["geo"], "founded": clean["founded"],
                "revenueUsdB": clean["revenue_usd_b"], "techNodes": [],
                "firstSeen": month, "lastConfirmed": month,
                "stale": False, "sources": [],
                "domains": nveco.entity_domains(clean["id"]),
                "cik": nveco.entity_cik(clean["id"]),
                "sourcing": {"total": 0, "selfSourced": 0, "byTier": {}},
            }
            owners["entity"][clean["id"]] = adir.name
            new_ent += 1

        f = adir / "factors.csv"
        if f.exists():
            for line, row in _read(f):
                clean, errs, _ = _validate_factors(row)
                if errs:
                    rejects.append({"file": f"{adir.name}/factors.csv", "line": line,
                                    "reason": "; ".join(errs), "row": str(row)[:300]})
                    continue
                factors_by_ent[clean["entity_id"]] = clean["factors"]

        f = adir / "edges.csv"
        if f.exists():
            per_file[(adir.name, "edges.csv")] = 0
            for line, row in _read(f):
                per_file[(adir.name, "edges.csv")] += 1
                clean, errs, warns = _validate_edge(row, types)
                problems += [f"{adir.name}/edges.csv:{line} {w}" for w in warns]
                if not errs:
                    for role, x in (("source", clean["source"]), ("target", clean["target"])):
                        if x not in entities:
                            errs.append(f"{role} '{x}' не заявлен ни в семени, ни в новых")
                    if clean["source"] == clean["target"]:
                        errs.append("петля")
                if errs:
                    rejects.append({"file": f"{adir.name}/edges.csv", "line": line,
                                    "reason": "; ".join(errs), "row": str(row)[:300]})
                    continue
                eid = f"{clean['source']}__{clean['target']}__{clean['type']}"
                if eid in edges:
                    problems.append(f"{adir.name}/edges.csv:{line} связь {eid} уже есть "
                                    f"в семени — пропущена")
                    continue
                edges[eid] = {"id": eid, **clean, "status": "signal", "confidence": None,
                              "sourceTier": None, "confirmedSources": 0,
                              "lastConfirmed": month, "evidence": []}
                owners["edge"][eid] = adir.name
                new_edge += 1

    # Источники — ВТОРЫМ проходом, когда связи всех каталогов уже загружены. Иначе
    # порядок каталогов начинает решать: `nvnet-detail` сортируется раньше
    # `nvnet-network`, и его источники к ещё не прочитанным связям отвергались как
    # «связь неизвестна». Ссылка не должна зависеть от алфавита.
    for adir in agent_dirs:
        f = adir / "sources.csv"
        if f.exists():
            for line, row in _read(f):
                clean, errs, warns = _validate_source(row)
                problems += [f"{adir.name}/sources.csv:{line} {w}" for w in warns]
                if not errs:
                    k = clean["owner_key"]
                    if clean["owner_kind"] == "entity" and k not in entities:
                        errs.append(f"источник для неизвестной сущности '{k}'")
                    if clean["owner_kind"] == "edge" and k not in edges:
                        errs.append(f"источник для неизвестной связи '{k}'")
                if errs:
                    rejects.append({"file": f"{adir.name}/sources.csv", "line": line,
                                    "reason": "; ".join(errs), "row": str(row)[:300]})
                    continue
                src_by_owner.setdefault((clean["owner_kind"], clean["owner_key"]), []).append({
                    "tier": clean["tier"], "type": clean["type"], "title": clean["title"],
                    "url": clean["url"], "published": clean["published"],
                    "fetched": today, "alive": True, "quote": clean["quote"],
                    "confidence": clean["confidence"]})
                new_src += 1

    # ── detail: развёрнутый разбор связи, отдельным файлом ────────────────────
    # Отдельный вход, а не колонка в edges.csv, по двум причинам. Во-первых, 243 из
    # 262 связей приходят из семени, и колонки в их CSV уже нет — дописывать поле
    # пришлось бы в конвейер v2, который заморожен. Во-вторых, detail пишется
    # выборочно и обновляется чаще самой связи: держать его рядом дешевле, чем
    # перегенерировать семя ради одного абзаца.
    detail_rows = 0
    for adir in agent_dirs:
        f = adir / "details.csv"
        if not f.exists():
            continue
        for line, row in _read(f):
            eid = (row.get("edge_id") or "").strip()
            ru = (row.get("detail_ru") or "").strip()
            en = (row.get("detail_en") or "").strip()
            if eid not in edges:
                rejects.append({"file": f"{adir.name}/details.csv", "line": line,
                                "reason": f"detail для неизвестной связи '{eid}'",
                                "row": str(row)[:200]})
                continue
            if not ru or not en:
                rejects.append({"file": f"{adir.name}/details.csv", "line": line,
                                "reason": "detail должен быть на обоих языках; "
                                          "пустая сторона — это не пропуск, а брак",
                                "row": str(row)[:200]})
                continue
            edges[eid]["detail"] = ru
            edges[eid]["_detail_en"] = en
            detail_rows += 1

    # ── description: развёрнутое описание узла, отдельным файлом ──────────────
    # Отдельный вход по тем же двум причинам, что и details.csv у связи: 106 из 107
    # сущностей приходят из семени, где такой колонки нет и не будет (конвейер v2
    # заморожен), а описание обновляется чаще самого профиля. Файл — единственный дом
    # текста: в nvnet_entity он не кладётся, потому что там живёт только достройка, а
    # описание пишется в первую очередь СЕМЕННЫМ сущностям.
    desc_rows = 0
    for adir in agent_dirs:
        f = adir / "descriptions.csv"
        if not f.exists():
            continue
        per_file[(adir.name, "descriptions.csv")] = 0
        for line, row in _read(f):
            per_file[(adir.name, "descriptions.csv")] += 1
            eid = (row.get("entity_id") or "").strip()
            ru = (row.get("description_ru") or "").strip()
            en = (row.get("description_en") or "").strip()
            if eid not in entities:
                rejects.append({"file": f"{adir.name}/descriptions.csv", "line": line,
                                "reason": f"описание для неизвестной сущности '{eid}'",
                                "row": str(row)[:200]})
                continue
            if not ru or not en:
                rejects.append({"file": f"{adir.name}/descriptions.csv", "line": line,
                                "reason": "описание должно быть на обоих языках; "
                                          "пустая сторона — это не пропуск, а брак",
                                "row": str(row)[:200]})
                continue
            if entities[eid].get("description"):
                problems.append(f"{adir.name}/descriptions.csv:{line} у '{eid}' уже "
                                f"есть описание от другого каталога — перезаписано")
            entities[eid]["description"] = ru
            entities[eid]["_description_en"] = en
            desc_rows += 1
    # ── ПЕРЕПИСАННАЯ ПРОЗА: notes.csv и oneliners.csv ─────────────────────────
    # Тот же путь, что у detail, и по той же причине: 262 связи и 107 сущностей
    # приходят из замороженного семени v2, а проза переписывается чаще, чем
    # меняется сама связь. Держать правку рядом дешевле, чем трогать семя.
    #
    # Перезапись ТОЛЬКО того, что прислано. Пустая ячейка — это «не трогай», а
    # не «сотри»: иначе частичный проход по сильным связям обнулил бы остальные.
    note_rows = liner_rows = 0
    for adir in agent_dirs:
        f = adir / "notes.csv"
        if f.exists():
            for line, row in _read(f):
                eid = (row.get("edge_id") or "").strip()
                ru = (row.get("note_ru") or "").strip()
                en = (row.get("note_en") or "").strip()
                if eid not in edges:
                    rejects.append({"file": f"{adir.name}/notes.csv", "line": line,
                                    "reason": f"note для неизвестной связи '{eid}'",
                                    "row": str(row)[:200]})
                    continue
                if bool(ru) != bool(en):
                    rejects.append({"file": f"{adir.name}/notes.csv", "line": line,
                                    "reason": "note должен быть на обоих языках; "
                                              "пустая сторона — это брак, а не пропуск",
                                    "row": str(row)[:200]})
                    continue
                if not ru:
                    continue
                edges[eid]["note"] = ru
                edges[eid]["_note_en"] = en
                note_rows += 1
        f = adir / "oneliners.csv"
        if f.exists():
            for line, row in _read(f):
                nid = (row.get("entity_id") or "").strip()
                ru = (row.get("one_liner_ru") or "").strip()
                en = (row.get("one_liner_en") or "").strip()
                if nid not in entities:
                    rejects.append({"file": f"{adir.name}/oneliners.csv", "line": line,
                                    "reason": f"one_liner для неизвестной сущности '{nid}'",
                                    "row": str(row)[:200]})
                    continue
                if bool(ru) != bool(en):
                    rejects.append({"file": f"{adir.name}/oneliners.csv", "line": line,
                                    "reason": "one_liner должен быть на обоих языках",
                                    "row": str(row)[:200]})
                    continue
                if not ru:
                    continue
                entities[nid]["oneLiner"] = ru
                entities[nid]["_one_liner_en"] = en
                liner_rows += 1

    # ── ЖЕЛЕЗНОЕ ПРАВИЛО: новая связь без источника не пишется ────────────────
    for eid in [k for k, v in edges.items() if not v.get("evidence")]:
        if src_by_owner.get(("edge", eid)):
            continue
        e = edges.pop(eid)
        rejects.append({"file": "edges.csv", "line": 0,
                        "reason": "нет ни одного источника с дословной цитатой — "
                                  "связь не пишется (правило контракта v2)",
                        "row": f"{eid} origin={e.get('origin')}"})
        new_edge -= 1

    # ── прикрепление источников и статусов к новым строкам ────────────────────
    for (kind, key), rows in src_by_owner.items():
        if kind == "edge" and key in edges:
            # СЛИЯНИЕ, а не перезапись. Источник, добавленный к семенной связи ради
            # цифр в `detail`, не должен стирать доказательства, на которых эта связь
            # вообще стоит. Дедуп по (url, цитата): один и тот же абзац, поданный
            # дважды, не должен считаться вторым подтверждением.
            have = {(e["url"], e["quote"]) for e in edges[key].get("evidence") or []}
            merged = list(edges[key].get("evidence") or [])
            merged += [r for r in rows if (r["url"], r["quote"]) not in have]
            edges[key]["evidence"] = merged
            rows = merged
            tiers = [r["tier"] for r in rows]
            status, conf = _status_and_confidence(tiers)
            edges[key].update({"status": status, "confidence": conf,
                               "sourceTier": min(tiers), "confirmedSources": len(tiers)})
            # обрезка v2: без источника тира 1–3 нельзя нести critical и strength > 80
            if not any(t in (1, 2, 3) for t in tiers):
                why = []
                if edges[key]["strength"] > 80:
                    why.append(f"strength {edges[key]['strength']} -> 80")
                    edges[key]["strength"] = 80
                if (edges[key]["risk"] or {}).get("level") == "critical":
                    why.append("risk critical -> high")
                    edges[key]["risk"]["level"] = "high"
                if why:
                    edges[key]["clamped"] = "; ".join(why) + ": нет источника тира 1–3"
        elif kind == "entity" and key in entities:
            # СЛИЯНИЕ, а не перезапись — по той же причине, что у связи выше.
            # Источник, добавленный ради цифры в `description`, не должен стирать
            # документ, на котором стоит сам профиль: у семенных сущностей это
            # единственная строка доказательств, и перезапись молча уносила бы её.
            have = {(s["url"], s["quote"]) for s in entities[key].get("sources") or []}
            entities[key]["sources"] = (list(entities[key].get("sources") or [])
                                        + [r for r in rows
                                           if (r["url"], r["quote"]) not in have])

    # ── критичность новых сущностей по той же рубрике ─────────────────────────
    for eid, fs in factors_by_ent.items():
        if eid not in entities:
            continue
        vals = {k: v[0] for k, v in fs.items()}
        c = nveco.criticality(vals)
        entities[eid]["criticality"] = c
        # Отсутствующий фактор едет ЯВНЫМ null, а не пропущенным ключом: «не
        # измерено» и «поля нет» — разные утверждения, и потребитель обязан их
        # различать. Ключ `concentration` присутствует у всех, значение — у тех,
        # у кого есть досье.
        entities[eid]["criticalityFactors"] = {CAMEL[k]: vals.get(k)
                                               for k in nveco.FACTORS}
        entities[eid]["criticalityWhy"] = {CAMEL[k]: (fs[k][1] if k in fs else None)
                                           for k in nveco.FACTORS}
        for l in entities[eid]["layers"]:
            l["criticality"] = c if l["primary"] else round((c or 0) * 0.5)

    # ── ЕДИНЫЙ ПЕРЕСЧЁТ ТИРОВ ПО ВСЕЙ СЕТИ ───────────────────────────────────
    # Половины карты собираются по-разному: сущности и связи семени приезжают уже
    # оценёнными из nveco_score, а достройка приносит источники со СЛОВ АГЕНТА и
    # доклеивает их к семенным строкам. До v4 разница была незаметна, потому что
    # шкала была одна на всех. Теперь тир зависит от того, ЧЕЙ это документ
    # относительно предмета, и оставить в файле два способа его получить значило бы
    # выдать карту, где одна и та же ссылка стоит тиром 1 у одной строки и тиром 2 у
    # соседней. Поэтому здесь тир считается заново для КАЖДОГО источника карты — и
    # для семени, и для достройки, — а статус связи выводится из результата.
    for eid, e in entities.items():
        for src in e.get("sources") or []:
            t, _ = nveco.source_tier(src.get("url"), eid)
            src["tier"] = t or 6
            src["confidence"] = nveco.tier_confidence(src["tier"])
            src["self"] = eid if nveco.is_self_source(src.get("url"), eid) else None
    for key, x in edges.items():
        live, claimed = [], set()
        for src in x.get("evidence") or []:
            t, _ = nveco.source_tier(src.get("url"), x["source"], x["target"])
            src["tier"] = t or 6
            src["confidence"] = nveco.tier_confidence(src["tier"])
            owner = next((end for end in (x["source"], x["target"])
                          if nveco.is_self_source(src.get("url"), end)), None)
            src["self"] = owner
            live.append(src["tier"])
            if owner:
                claimed.add(owner)
        counter = x.get("counterEvidence") or []
        for src in counter:
            t, _ = nveco.source_tier(src.get("url"), x["source"], x["target"])
            src["tier"] = t or 6
            src["self"] = next((end for end in (x["source"], x["target"])
                                if nveco.is_self_source(src.get("url"), end)), None)
        status, conf = _status_and_confidence(live, claimed, bool(counter))
        x["status"] = status
        x["confidence"] = conf
        x["sourceTier"] = min(live) if live else 6
        x["confirmedSources"] = len(live)
        x["sidedness"] = ("disputed" if counter else
                          "bilateral" if len(claimed) >= 2 else "single")
        x["claimedBy"] = sorted(claimed)
        x.setdefault("counterEvidence", [])

    # ── прозрачность профиля у ВСЕХ, включая достройку ───────────────────────
    # Семя привозит `sourcing` посчитанным, но у сущности, заведённой достройкой,
    # источники приезжают отдельным файлом, и блок пришлось бы собирать дважды.
    # Считается он здесь по итоговому списку — одному на обе половины карты.
    for eid, e in entities.items():
        srcs = e.get("sources") or []
        by_tier = {}
        for x in srcs:
            by_tier[str(x.get("tier"))] = by_tier.get(str(x.get("tier")), 0) + 1
        e["domains"] = nveco.entity_domains(eid)
        e["cik"] = nveco.entity_cik(eid)
        e["sourcing"] = {
            "total": len(srcs),
            "selfSourced": sum(1 for x in srcs
                               if nveco.is_self_source(x.get("url"), eid)),
            "byTier": {k: by_tier[k] for k in sorted(by_tier)}}

    # ── членство держат три проверки охвата, а не расстояние до центра ────────
    # Раньше здесь стоял обход графа от 27 назначенных пивотов, и всё, до чего от них
    # дальше двух шагов, выбрасывалось молча-с-причиной. Правило вырезано целиком:
    # сеть — это уже собранная карта, границу которой держит nveco_ingest, и вторая
    # граница поверх первой только резала бы её вслепую. Связь без обоих концов
    # по-прежнему не едет: это правило целостности, а не членства.
    dropped = []
    for k in [k for k, v in edges.items()
              if v["source"] not in entities or v["target"] not in entities]:
        edges.pop(k)

    return {"entities": entities, "edges": edges, "seed": seed,
            "owners": owners, "perFile": per_file,
            "newEntities": new_ent, "newEdges": new_edge, "newSources": new_src,
            "details": detail_rows, "descriptions": desc_rows,
            "notes": note_rows, "oneLiners": liner_rows,
            "problems": problems, "rejects": rejects, "dropped": dropped}


def _drop_i18n(con, kind, ids):
    """Перевод снятой строки — сирота. Удаляется ТОЛЬКО если id не живёт в v2:
    склад переводов один на обе карты (scope='nveco'), и id, который ещё есть в
    nveco_*, принадлежит не нам."""
    if not ids or not con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='i18n_text'").fetchone():
        return
    v2 = "nveco_entity" if kind == "entity" else "nveco_edge"
    for oid in ids:
        if con.execute(f"SELECT 1 FROM {v2} WHERE id=?", (oid,)).fetchone():
            continue
        con.execute("DELETE FROM i18n_text WHERE scope='nveco' AND kind=? AND obj_id=?",
                    (kind, oid))


def _retire(con, month, net) -> dict:
    """Снять с карты строки достройки, которых больше нет в CSV этого месяца.

    Правило и его четыре случая — общие с v2, см. `_retiring_agents` в
    nveco_ingest: снимает только каталог, который в этом месяце реально сдал файл
    и сдал не пустой мусор. Семя не трогается вовсе — оно живёт в nveco_* и в
    nvnet_* его нет.
    """
    alive = {"entity": {}, "edge": {}}
    for kind, key in (("entity", "entities"), ("edge", "edges")):
        for oid, agent in net["owners"][kind].items():
            if oid in net[key]:
                alive[kind][agent] = alive[kind].get(agent, 0) + 1

    may_edges, broken = _retiring_agents(net["perFile"], "edges.csv", alive["edge"])
    stale_edges = _owned_by(con, "nvnet_edge", set(may_edges), set(net["edges"]))
    for eid in stale_edges:
        con.execute("DELETE FROM nvnet_source WHERE owner_kind='edge' AND owner_id=?", (eid,))
        con.execute("DELETE FROM nvnet_edge WHERE id=?", (eid,))
    _drop_i18n(con, "edge", stale_edges)

    may_ents, broken_e = _retiring_agents(net["perFile"], "entities.csv", alive["entity"])
    stale_ents, held = [], []
    for eid in _owned_by(con, "nvnet_entity", set(may_ents), set(net["entities"])):
        # nvnet_edge ссылается на сущности БЕЗ внешнего ключа: source_id там свободный
        # текст, потому что половина концов лежит в семени. Каскада нет — значит и
        # висячей ссылки быть не должно, проверяем руками.
        used = con.execute("SELECT COUNT(*) c FROM nvnet_edge WHERE source_id=? OR target_id=?",
                           (eid, eid)).fetchone()["c"]
        (held if used else stale_ents).append(eid)
    for eid in stale_ents:
        con.execute("DELETE FROM nvnet_source WHERE owner_kind='entity' AND owner_id=?", (eid,))
        con.execute("DELETE FROM nvnet_entity_factor WHERE entity_id=?", (eid,))
        con.execute("DELETE FROM nvnet_entity WHERE id=?", (eid,))
    _drop_i18n(con, "entity", stale_ents)

    # Пары БЕЗ связи — тот же вопрос: файл существует, значит он и есть полный список
    # проверенных пар этого месяца. Файла нет — прошлый список остаётся как был.
    stale_pairs = []
    gaps = db.RUNS_DIR / month / "nvnet-gaps" / "not_found.csv"
    if gaps.exists():
        keep = {(row.get("pair_id") or "").strip() for _, row in _read(gaps)}
        stale_pairs = [r["pair_id"] for r in con.execute("SELECT pair_id FROM nvnet_not_found")
                       if r["pair_id"] not in keep]
        for pid in stale_pairs:
            con.execute("DELETE FROM nvnet_not_found WHERE pair_id=?", (pid,))

    return {"entities": stale_ents, "edges": stale_edges, "pairs": stale_pairs,
            "held": held, "broken": sorted(set(broken + broken_e))}


def persist(month: str, net: dict) -> dict:
    """Сохраняет ТОЛЬКО достройку: семя живёт в nveco_* и не дублируется.

    Авторитетно за свой месяц: строка, исчезнувшая из CSV каталога, который в этом
    месяце выдал файл, снимается вместе с источниками и переводом. Возвращает, что
    было снято."""
    con = db.connect()
    con.executescript((db.ROOT / "db" / "schema_nvnet.sql").read_text())
    seed_ids = {e["id"] for e in net["seed"]["entities"]}
    seed_edges = {e["id"] for e in net["seed"]["edges"]}
    for eid, e in net["entities"].items():
        if eid in seed_ids:
            continue
        con.execute(
            """INSERT OR REPLACE INTO nvnet_entity (id,name,aliases,type,role,sector,
                 primary_layer,layers,phase,ticker,public_private,geo,founded,
                 revenue_usd_b,one_liner,why_irreplaceable,what_breaks_it,geo_risk,
                 geo_risk_note,export_regime,concentration,owner_agent)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (eid, e["name"], "|".join(e["aliases"]), e["type"], e["role"], e["sector"],
             e["primaryLayer"], "|".join(l["layer"] for l in e["layers"]), e["phase"],
             e["ticker"], e["publicPrivate"], e["geo"], e["founded"], e["revenueUsdB"],
             e["oneLiner"], e["whyIrreplaceable"], e["whatBreaksIt"],
             e["risk"]["geopolitical"], e["risk"]["note"], e["risk"]["exportRegime"],
             e["risk"]["concentration"], net["owners"]["entity"].get(eid)))
    for eid, x in net["edges"].items():
        if eid in seed_edges:
            continue
        con.execute(
            """INSERT OR REPLACE INTO nvnet_edge (id,source_id,target_id,type,spine,
                 direction,strength,lock_in_depth,substitutability,is_reversible,status,
                 confidence,source_tier,confirmed_sources,risk_level,risk_type,
                 risk_timeline,risk_mitigation,tech_node,formed,strengthened,
                 last_confirmed,note,clamped,origin,owner_agent)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (eid, x["source"], x["target"], x["type"], x["spine"], x["direction"],
             x["strength"], x.get("lockInDepth"), x.get("substitutability"),
             1 if x.get("isReversible") else 0, x["status"], x["confidence"],
             x["sourceTier"], x["confirmedSources"], (x["risk"] or {}).get("level"),
             (x["risk"] or {}).get("type"), (x["risk"] or {}).get("timeline"),
             (x["risk"] or {}).get("mitigation"), x.get("techNode"), x.get("formed"),
             x.get("strengthened"), x.get("lastConfirmed"), x.get("note"),
             x.get("clamped"), x.get("origin"), net["owners"]["edge"].get(eid)))
        for ev in x["evidence"]:
            con.execute(
                """INSERT OR IGNORE INTO nvnet_source (owner_kind,owner_id,tier,type,
                     title,url,published,fetched,alive,quote,confidence)
                   VALUES ('edge',?,?,?,?,?,?,?,1,?,?)""",
                (eid, ev["tier"], ev["type"], ev["title"], ev["url"], ev["published"],
                 ev["fetched"], ev["quote"], ev["confidence"]))
    # пары без связи
    gaps = db.RUNS_DIR / month / "nvnet-gaps" / "not_found.csv"
    if gaps.exists():
        for _, row in _read(gaps):
            con.execute(
                """INSERT OR REPLACE INTO nvnet_not_found
                     (pair_id,entity_a,entity_b,expected,reason) VALUES (?,?,?,?,?)""",
                (row["pair_id"], row["entity_a"], row["entity_b"],
                 row.get("expected"), row["reason"]))
    retired = _retire(con, month, net)
    con.commit()
    con.close()
    return retired


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else nveco.current_month()
    n = build(m)
    print(f"сеть: {len(n['entities'])} сущностей, {len(n['edges'])} связей; "
          f"новых {n['newEntities']}/{n['newEdges']}; отклонено {len(n['rejects'])}")
