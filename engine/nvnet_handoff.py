"""Сборка handoff/ai_ecosystem_network.json + валидатор + чейнджлог по 10 категориям.

Контракт /4 ЛОМАЕТ форму: снят `hops`, снят `strategicControl`, снят корневой
`ecosystem`. 16 слоёв, 5 хребтов, рубрика, тиры и форма Source по-прежнему приходят из
семени без изменений. Новое здесь — `integration` и выведенное из неё `core` на
сущности, блок `meta` с предметом карты и состоянием членства, `centrality`, блок
`network` и версия выпуска.

Файл, не прошедший валидатор, НЕ ПИШЕТСЯ. Предыдущий остаётся: отдать дашборду битую
сеть хуже, чем не отдать новую.
"""

import csv
import json
import re
import sys
from datetime import date

from . import db, i18n, nveco, nvnet, nvnet_centrality, nvnet_spof, nvnet_subgraphs

OUT_JSON = db.HANDOFF_DIR / "ai_ecosystem_network.json"
OUT_MD = db.HANDOFF_DIR / "AI-ECOSYSTEM-NETWORK-CHANGELOG.md"


class ContractError(AssertionError):
    pass


# Проверки, применимые только к узлу с отработанным досье. Держатся здесь списком,
# потому что валидатор обязан уметь поймать нарушение гейта, не читая конфиг заново.
GATED_CHECKS = {"min_sources", "min_self_sources"}


def _membership_meta(month: str, entities) -> dict:
    """Сколько узлов карта впустила, сняла, удержала и держит в очереди.

    Читает отчёты, которые написал nveco_ingest: считать проверки второй раз здесь
    значило бы завести вторую их реализацию, а расхождение двух копий одного правила
    страшнее, чем чтение файла.

    Фаза 3 включила правило, и поля перестали быть нулями по построению:
      admitted — проходят ВСЕ применимые к ним проверки;
      retired  — сняты членством с причиной (файл _membership/retired.csv);
      held     — не проходят, но удержаны ребром с цитатой: остались и помечены;
      queued   — стоят на карте и своего досье пока не предъявили.

    Разница между `retired` и `held` — это и есть решение Фазы 3 о том, чем карта
    дорожит больше: провал членства узла не является свидетельством против ребра,
    у которого своя цитата и свой владелец. См. config/nveco_scope.yaml, on_fail.
    """
    base = db.RUNS_DIR / month / "_membership"
    path = base / "report.csv"
    cfg = nveco.membership_cfg()
    enforced = bool(cfg.get("enforce", False))
    if not path.exists():
        return {"admitted": 0, "retired": 0, "held": 0, "queued": 0,
                "enforced": enforced, "note": "отчёт членства за этот месяц не найден"}
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    on_map = {e["id"] for e in entities}
    rows = [r for r in rows if r["id"] in on_map]
    passing = [r for r in rows if r["passes"] == "1"]
    retired, held = [], []
    rp = base / "retired.csv"
    if rp.exists():
        for r in csv.DictReader(rp.open(encoding="utf-8")):
            (retired if r["outcome"] == "retired" else held).append(
                {"id": r["id"], "failed": r["failed"], "heldBy": r.get("held_by") or None})
    # Отчёт пишет nveco_ingest; сущность, заведённая ДОСТРОЙКОЙ, в него не попадает.
    # Разрыв не заглаживается молча — он выносится числом.
    uncovered = sorted(on_map - {r["id"] for r in rows})
    return {
        "admitted": len(passing),
        "retired": len(retired),
        "retiredNodes": retired,
        "held": len(held),
        "heldNodes": held,
        "queued": len(rows) - len(passing),
        "enforced": enforced,
        "onFail": cfg.get("on_fail", "retire_unheld"),
        "coverageGated": sorted(cfg.get("coverage_gated")
                                or ("min_sources", "min_self_sources")),
        "pendingDossier": sum(1 for r in rows if r.get("pending_dossier") == "1"),
        "covered": len(rows),
        "uncovered": uncovered,
        "checks": {k: sum(1 for r in rows if r[k] == "0")
                   for k in ("in_scope", "min_sources", "min_self_sources",
                             "min_confirmed_edges")},
    }


def build(month: str, net: dict) -> dict:
    seed = net["seed"]
    entities = [net["entities"][k] for k in sorted(net["entities"])]
    edges = [net["edges"][k] for k in sorted(net["edges"])]

    metrics = nvnet_centrality.run([e["id"] for e in entities], edges,
                                  nvnet.pagerank_dependence())
    for e in entities:
        e["centrality"] = metrics["centrality"][e["id"]]

    # ── интеграция и ядро ────────────────────────────────────────────────────
    # Ядро — ВЫХОД, а не вход: верхние N по вычисленной мере, пересчёт каждый прогон.
    # Списка руками нет нигде, и это единственное место, где карта решает, кто в ядре.
    layers_of = {e["id"]: [l["layer"] for l in e.get("layers") or []] for e in entities}
    struct = nvnet_centrality.structural([e["id"] for e in entities], edges,
                                         layers_of, seed.get("cycles") or [])
    integ = nvnet_centrality.integration(metrics["centrality"], struct,
                                         nvnet.integration_weights())
    core = set(nvnet_centrality.core_ids(integ, nveco.core_n()))
    for e in entities:
        e["integration"] = integ[e["id"]]
        e["core"] = e["id"] in core
        # `pivotal` — ЗЕРКАЛО `core` ровно на выпуск v4.0. Дашборд читает это поле
        # сегодня, и гасить его до его собственного прохода нельзя. Помечено
        # deprecated, удаляется в /5; чтобы оно не разошлось с `core`, оно и не
        # вычисляется отдельно, а присваивается здесь одной строкой.
        e["pivotal"] = e["core"]

    sub = nvnet_subgraphs.run(entities, edges)
    spof = nvnet_spof.run(entities, metrics["adjacency"], metrics["centrality"])

    pivotal = len(core)
    payload = {
        "schema": nvnet.SCHEMA_VERSION,
        "version": nvnet.release_version(month),
        "generated": date.today().isoformat(),
        "asOf": month,
        "source": "engine",
        # Корневой `ecosystem` снят контрактом /4: он называл карту именем компании.
        # Идентификатор сети живёт в network.id и в meta.
        #
        # `pivots` остаётся ровно на этот выпуск и содержит СОСТАВ ЯДРА, а не список
        # из конфига: дашборд читает это поле сегодня, и подменить его смысл тише,
        # чем погасить, — здесь единственный способ не сломать его до его прохода.
        "pivots": sorted(core),
        "meta": {
            "scope": {"ru": seed["scope"]["ru"], "en": seed["scope"]["en"]},
            "scopeId": seed["scope"]["id"],
            "coreRule": f"top-{nveco.core_n()} by integration",
            "coreCount": len(core),
            "membership": _membership_meta(month, entities),
            "deprecated": {
                "pivotal": "зеркало core; удаляется в ai-ecosystem-network/5",
            },
        },
        "totals": {"entities": len(entities), "edges": len(edges),
                   "layers": len(seed["layers"]), "cycles": len(seed.get("cycles", [])),
                   "techNodes": len(seed.get("techNodes", []))},
        # ТАКСОНОМИЯ ЕДЕТ В ФАЙЛЕ, а не копируется потребителем.
        #
        # Дашборд держал свою копию таблицы типов, она отстала на два типа v3
        # (is_alternative_to, enables_interop), и его фолбэк молча нарисовал их
        # как «поставляет»: карта утверждала, что AMD ПОСТАВЛЯЕТ CUDA, хотя AMD
        # ей альтернатива, и красила ребро по хребту «физика» вместо
        # «соперничества». Тихий фолбэк, меняющий смысл связи, хуже отсутствующего.
        #
        # Пока таблица живёт двумя копиями, она будет расходиться — поэтому
        # источник правды переезжает в саму поставку.
        "spines": {k: {"label": i18n.bi(v.get("label"), v.get("label_en"))}
                   for k, v in nveco.load_edge_types().get("spines", {}).items()},
        "edgeTypes": {k: {"spine": v.get("spine"),
                          "verb": i18n.bi(v.get("verb"), v.get("verb_en")),
                          "label": i18n.bi(v.get("label"), v.get("label_en"))}
                      for k, v in nvnet.edge_types().items()},
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
    return bilingualise(payload, nveco.connect())


# ── двуязычие ────────────────────────────────────────────────────────────────
# ОДИН проход в конце сборки, а не обёртка в двадцати местах. Причина простая:
# список полей прозы — это контракт, и он должен читаться одним списком, а не
# собираться по коду. Что здесь не перечислено, то и не оборачивается: цитаты
# источников, id, слаги и URL остаются простыми строками.
#
# Русская сторона берётся из значения, которое уже лежит в выдаче (карта
# экосистемы собиралась по-русски), английская — из склада переводов i18n_text
# либо из ключа *_en рядом в конфиге. Пустая сторона НЕ подменяется другой:
# валидатор ниже ищет именно её.
BILINGUAL_FIELDS = {
    "entity": ("oneLiner", "whyIrreplaceable", "whatBreaksIt"),
    "entity_factor": ("irreplaceability", "lockInDepth", "timeToReplace",
                      "concentration"),
    "edge": ("note", "detail"),
}

# Поля, английская сторона которых приезжает ТЕМ ЖЕ CSV, что и русская, а не из
# склада переводов: их пишет исследователь сразу на двух языках. Склад всё равно
# побеждает, если перевод в нём заведён, — правило для всей прозы одно.
CSV_BILINGUAL = {"entity": ("description",), "edge": ("detail",)}

# поле выдачи -> поле в складе переводов
_I18N_KEY = {
    "oneLiner": "one_liner", "whyIrreplaceable": "why_irreplaceable",
    "description": "description",
    "whatBreaksIt": "what_breaks_it", "note": "note", "detail": "detail",
    "irreplaceability": "why_irreplaceability", "lockInDepth": "why_lock_in",
    "timeToReplace": "why_time", "concentration": "why_concentration",
    "riskNote": "risk_note", "mitigation": "risk_mitigation",
}


def bilingualise(payload: dict, con) -> dict:
    """Обернуть каждое поле прозы в {"ru": …, "en": …}. Меняет payload на месте."""
    idx = i18n.index(con, "nveco")

    def w(kind, oid, out_field, ru):
        return i18n.wrap(idx, kind, oid, _I18N_KEY[out_field], fallback_ru=ru)

    for e in payload["entities"]:
        eid = e["id"]
        # ИМЯ оборачивается ТОЛЬКО когда перевод заведён. NVIDIA — это NVIDIA на
        # обоих языках, и пара {ru: "NVIDIA", en: "NVIDIA"} была бы шумом; а вот
        # «Китай» английскому читателю нечитаем. Контракт допускает обе формы,
        # поэтому бренды остаются простой строкой.
        nm = idx.get(("entity", eid, "name"))
        if nm and nm.get("ru") and nm.get("en"):
            e["name"] = i18n.bi(nm["ru"], nm["en"])
        for f in BILINGUAL_FIELDS["entity"]:
            if e.get(f) is not None:
                # Переписанная агентом сторона выигрывает у склада переводов:
                # склад хранит перевод СТАРОГО текста, и подставить его к новому
                # значило бы показать двум читателям разные утверждения.
                fresh_en = e.pop("_one_liner_en", None) if f == "oneLiner" else None
                e[f] = (i18n.bi(e[f], fresh_en) if fresh_en
                        else w("entity", eid, f, e[f]))
        # description — как detail у связи: обе стороны пришли одной строкой CSV.
        if e.get("description") is not None:
            e["description"] = i18n.wrap(idx, "entity", eid, "description",
                                         fallback_ru=e["description"],
                                         fallback_en=e.pop("_description_en", None))
        else:
            e.pop("_description_en", None)
        cw = e.get("criticalityWhy") or {}
        for f in BILINGUAL_FIELDS["entity_factor"]:
            if cw.get(f) is not None:
                cw[f] = w("entity", eid, f, cw[f])
        if (e.get("risk") or {}).get("note") is not None:
            e["risk"]["note"] = w("entity", eid, "riskNote", e["risk"]["note"])

    for x in payload["edges"]:
        xid = x["id"]
        if x.get("note") is not None:
            fresh_en = x.pop("_note_en", None)
            x["note"] = (i18n.bi(x["note"], fresh_en) if fresh_en
                         else w("edge", xid, "note", x["note"]))
        if x.get("detail") is not None:
            # Английская сторона пришла тем же CSV и лежит рядом: склад переводов для
            # неё не нужен, но если он есть — он побеждает, как и у прочей прозы.
            x["detail"] = i18n.wrap(idx, "edge", xid, "detail",
                                    fallback_ru=x["detail"],
                                    fallback_en=x.pop("_detail_en", None))
        else:
            x.pop("_detail_en", None)
        if (x.get("risk") or {}).get("mitigation") is not None:
            x["risk"]["mitigation"] = w("edge", xid, "mitigation", x["risk"]["mitigation"])

    for c in payload.get("cycles", []):
        c["note"] = i18n.wrap(idx, "cycle", c["id"], "note",
                              fallback_ru=c.get("note"), fallback_en=c.pop("noteEn", None))

    # Конфигурные подписи: английское уже лежит рядом ключом *_en, склад не нужен.
    for l in payload.get("layers", []):
        l["label"] = i18n.bi(l.get("label"), l.pop("label_en", None))
        l["caption"] = i18n.bi(l.get("caption"), l.pop("caption_en", None))
    for s in payload.get("sectors", []):
        s["label"] = i18n.bi(s.get("label"), s.pop("label_en", None))
    for n_ in payload.get("techNodes", []):
        n_["note"] = i18n.bi(n_.get("note"), n_.pop("note_en", None))
        # То же правило для подписи: «3 нм» переводится, «NVLink» — нет.
        lab_en = n_.pop("label_en", None)
        if lab_en:
            n_["label"] = i18n.bi(n_.get("label"), lab_en)
    for sg in payload["network"]["subgraphs"]:
        sg["label"] = i18n.bi(sg.get("label"), sg.pop("label_en", None))
        sg["description"] = i18n.bi(sg.get("description"), sg.pop("description_en", None))
    for s in payload["network"]["singlePointsOfFailure"]:
        s["reason"] = i18n.bi(s.get("reason"), s.pop("reasonEn", None))
    return payload


def bilingual_paths(payload: dict) -> list:
    """(json-путь, значение) по КАЖДОМУ обёрнутому полю — вход валидатора."""
    out = []
    for i, e in enumerate(payload["entities"]):
        for f in BILINGUAL_FIELDS["entity"] + CSV_BILINGUAL["entity"]:
            if f in e:
                out.append((f"entities[{e['id']}].{f}", e[f]))
        for f, v in (e.get("criticalityWhy") or {}).items():
            out.append((f"entities[{e['id']}].criticalityWhy.{f}", v))
        if (e.get("risk") or {}).get("note") is not None:
            out.append((f"entities[{e['id']}].risk.note", e["risk"]["note"]))
    for x in payload["edges"]:
        if x.get("note") is not None:
            out.append((f"edges[{x['id']}].note", x["note"]))
        if x.get("detail") is not None:
            out.append((f"edges[{x['id']}].detail", x["detail"]))
        if (x.get("risk") or {}).get("mitigation") is not None:
            out.append((f"edges[{x['id']}].risk.mitigation", x["risk"]["mitigation"]))
    for c in payload.get("cycles", []):
        out.append((f"cycles[{c['id']}].note", c.get("note")))
    for l in payload.get("layers", []):
        out += [(f"layers[{l['id']}].label", l["label"]),
                (f"layers[{l['id']}].caption", l["caption"])]
    for s in payload.get("sectors", []):
        out.append((f"sectors[{s['key']}].label", s["label"]))
    for n_ in payload.get("techNodes", []):
        out.append((f"techNodes[{n_['id']}].note", n_["note"]))
    for sg in payload["network"]["subgraphs"]:
        out += [(f"subgraphs[{sg['id']}].label", sg["label"]),
                (f"subgraphs[{sg['id']}].description", sg["description"])]
    for s in payload["network"]["singlePointsOfFailure"]:
        out.append((f"spof[{s['id']}].reason", s["reason"]))
    return out



# ── detail: развёрнутый разбор связи ────────────────────────────────────────
DETAIL_MIN_CHARS = 90          # короче — это второй `note`, а не разбор
DETAIL_MAX_CHARS = 900         # длиннее — это уже не 2-5 предложений
# Разделитель НЕ может стоять перед пробелом: иначе «May 31, 2031» слипается в одно
# число 312031 и проверка начинает ругаться на несуществующую выдумку.
_NUM = re.compile(r"\d+(?:[.,]\d+)*")
_THOUSANDS = re.compile(r"\d{1,3}(?:[\u00a0 ]\d{3})+(?:[.,]\d+)?")


_IN_NAME = re.compile(r"(?<=[A-Za-zА-Яа-я])[-–]?\d+(?:\.\d+)?")


def _readings(token: str) -> set:
    """Все допустимые прочтения одного числового токена.

    «2,788» по-русски это 2.788, по-английски — 2788, и по самому токену это не
    различить. Поэтому токен раскрывается в набор прочтений, а подтверждённым
    считается число, у которого цитата подтверждает ХОТЯ БЫ ОДНО. Требовать
    совпадения всех прочтений нельзя — это отвергало бы верное число; принимать
    любое похожее тоже нельзя — тогда проверка перестаёт что-либо значить.
    """
    t = token.replace("\u00a0", "").replace(" ", "")
    frac = t.split(",")[1] if t.count(",") == 1 and "." not in t else ""
    if frac and len(frac) <= 2:
        cands = [t.replace(",", ".")]                    # десятичная запятая
    elif frac and len(frac) == 3:
        cands = [t.replace(",", "."), t.replace(",", "")]  # 2,788 -> 2.788 или 2788
    else:
        cands = [t.replace(",", "")]                     # разделитель тысяч
    out = set()
    for c in cands:
        c = c.rstrip(".")
        if "." in c:
            c = c.rstrip("0").rstrip(".")
        if c:
            out.add(c)
    return out


def _unbacked(text: str, quoted: set) -> list:
    """Числа текста, ни одно прочтение которых не встречается в цитатах.

    Имена с цифрами («H100», «x86») вычищаются тем же правилом, что и в
    `_numbers`: это названия, а не количества, и источник для них не нужен."""
    text = _IN_NAME.sub(" ", text or "")
    text = _THOUSANDS.sub(lambda m: m.group(0).replace("\u00a0", "").replace(" ", ""),
                          text or "")
    bad = []
    for raw in _NUM.findall(text):
        r = _readings(raw)
        if r and not (r & quoted):
            bad.append(raw)
    return sorted(set(bad))


def _numbers(text: str) -> set:
    """Числовые токены в нормализованном виде.

    Нормализация нужна, потому что одно и то же число в двух языках пишется
    по-разному: «$6.5 billion» и «6,5 млрд». Приводим к общему виду — убираем
    разделители тысяч, запятую-десятичную превращаем в точку, отбрасываем хвостовые
    нули, — и сравниваем уже это.
    """
    # Русская типографика отделяет тысячи пробелом: «7 796,7 млрд». Склеиваем такие
    # группы заранее, иначе число распадётся на «7» и «796,7» и не совпадёт с
    # английским «7,796.7» из цитаты.
    # ЦИФРЫ ВНУТРИ ИМЁН — не количества. «x86», «H100», «GPT-4», «Spectrum-X»:
    # это названия, и требовать для них источник бессмысленно. Отличие в том, что
    # перед цифрой стоит буква без пробела. Без этой чистки «x86» превращался в
    # число 86 и валил выпуск на ровном месте.
    text = _IN_NAME.sub(" ", text or "")
    text = _THOUSANDS.sub(lambda m: m.group(0).replace("\u00a0", "").replace(" ", ""),
                          text)
    out = set()
    for raw in _NUM.findall(text):
        out |= _readings(raw)
    return out


def _check_detail(payload: dict) -> list:
    """Правила поля `detail`. Главное из них — прослеживаемость цифр.

    Число, которого нет ни в одной цитате этой связи, — выдумка, даже если оно верно.
    Проверка механическая: все числовые токены обеих языковых версий обязаны
    встретиться в evidence[].quote. Это единственный способ удержать обещание «цифры
    только там, где они подтверждены»: обещание, которое никто не проверяет, живёт
    ровно до первого напряжённого прогона.
    """
    errs = []
    for x in payload["edges"]:
        d = x.get("detail")
        if d is None:
            continue
        if not isinstance(d, dict):
            errs.append(f"связь {x['id']}: detail не пара {{ru, en}}")
            continue
        ru, en = (d.get("ru") or "").strip(), (d.get("en") or "").strip()
        for lang, text in (("ru", ru), ("en", en)):
            if not text:
                errs.append(f"связь {x['id']}: detail.{lang} пуст — "
                            f"поле либо заполнено на обоих языках, либо отсутствует")
            elif not DETAIL_MIN_CHARS <= len(text) <= DETAIL_MAX_CHARS:
                errs.append(f"связь {x['id']}: detail.{lang} {len(text)} знаков, "
                            f"допустимо {DETAIL_MIN_CHARS}..{DETAIL_MAX_CHARS}")
        note = x.get("note") or {}
        if isinstance(note, dict):
            for lang in ("ru", "en"):
                a = (d.get(lang) or "").strip()
                b = (note.get(lang) or "").strip()
                if a and b and a == b:
                    errs.append(f"связь {x['id']}: detail.{lang} дословно повторяет "
                                f"note — такое поле не пишется, а опускается")
        quoted = _numbers(" ".join(ev.get("quote", "") for ev in x.get("evidence", [])))
        for lang in ("ru", "en"):
            unbacked = _unbacked(d.get(lang) or "", quoted)
            if unbacked:
                errs.append(f"связь {x['id']}: числа в detail.{lang} не встречаются "
                            f"ни в одной цитате: {', '.join(unbacked[:6])}")
    return errs


# ── description: развёрнутое описание узла ───────────────────────────────────
# Панель сущности задаёт пять вопросов подряд: что продаёт, откуда деньги, где стоит
# в стеке, какого размера, что изменилось. Проверить машиной можно не «отвечает ли
# текст», а форму и добросовестность: длину, обе стороны, прослеживаемость цифр и
# отсутствие оборотов, которые остаются правдой под любой компанией.
DESCRIPTION_MIN_SENTENCES = 4
DESCRIPTION_MAX_SENTENCES = 7
DESCRIPTION_MIN_CHARS = 260     # короче — это второй oneLiner, а не описание
DESCRIPTION_MAX_CHARS = 1400    # длиннее — это уже не 4–7 предложений

# Границей считается точка (или ? !) С ПРОБЕЛОМ после неё. Отсюда прямое требование
# к тексту: внутри предложения такой пары быть не должно. «$3.4 млрд» и «85%»
# безопасны — там за точкой идёт цифра; а «U.S. government» и «т. е.» сломали бы
# счёт, поэтому в описании они не пишутся. Это не обход проблемы, а то же правило
# «без жаргона и сокращений», только проверяемое.
_SENT_SPLIT = re.compile(r'(?<=[.!?…])["»)]?\s+')

# Обороты, которые остаются правдой под другой компанией. Список короткий и
# намеренно бесспорный: каждый из них — оценка без факта, и ни один не бывает
# единственным способом сказать то, что нужно.
_SUBSTITUTABLE = (
    "лидер рынка", "рыночный лидер", "лидер отрасли", "ключевой игрок",
    "сильные позиции", "прочные позиции", "одна из ведущих", "один из ведущих",
    "одним из ведущих", "широко признан", "хорошо известн", "успешно развива",
    "market leader", "industry leader", "key player", "strong position",
    "strong market position", "one of the leading", "widely recognized",
    "well known for", "successfully develop",
)


def _sentences(text: str) -> list:
    return [s for s in (p.strip() for p in _SENT_SPLIT.split((text or "").strip())) if s]


def _check_description(payload: dict) -> list:
    """Правила поля `description`. Те же, что у `detail`, плюс счёт предложений.

    Прослеживаемость цифр — главное и здесь. Панель читают как данные, поэтому
    число, которого нет ни в одной цитате ЭТОЙ сущности, не отгружается, даже если
    оно верно: проверить его читателю неоткуда, а подпись «источник» под ним была бы
    ложью. Правило заставляет исследователя приносить цитату вместе с цифрой —
    ровно так же, как «нет цитаты — нет связи» заставляет приносить её вместе с ребром.
    """
    errs = []
    for e in payload["entities"]:
        d = e.get("description")
        if d is None:
            continue
        if not isinstance(d, dict):
            errs.append(f"сущность {e['id']}: description не пара {{ru, en}}")
            continue
        for lang in ("ru", "en"):
            text = (d.get(lang) or "").strip()
            if not text:
                errs.append(f"сущность {e['id']}: description.{lang} пуст — поле либо "
                            f"заполнено на обоих языках, либо отсутствует")
                continue
            if not DESCRIPTION_MIN_CHARS <= len(text) <= DESCRIPTION_MAX_CHARS:
                errs.append(f"сущность {e['id']}: description.{lang} {len(text)} знаков, "
                            f"допустимо {DESCRIPTION_MIN_CHARS}..{DESCRIPTION_MAX_CHARS}")
            sents = _sentences(text)
            if not DESCRIPTION_MIN_SENTENCES <= len(sents) <= DESCRIPTION_MAX_SENTENCES:
                errs.append(f"сущность {e['id']}: description.{lang} — {len(sents)} "
                            f"предложений, нужно {DESCRIPTION_MIN_SENTENCES}–"
                            f"{DESCRIPTION_MAX_SENTENCES}")
            if sents and sents[-1][-1] not in ".!?…":
                errs.append(f"сущность {e['id']}: description.{lang} обрывается без "
                            f"знака конца предложения")
            low = text.lower()
            for phrase in _SUBSTITUTABLE:
                if phrase in low:
                    errs.append(f"сущность {e['id']}: description.{lang} содержит "
                                f"'{phrase}' — оборот остался бы правдой под другой "
                                f"компанией, тест на подстановку не пройден")
            # Пересказ соседнего поля — не описание: те поля отрисованы рядом и
            # отвечают на другие вопросы.
            for other in ("oneLiner", "whyIrreplaceable", "whatBreaksIt"):
                v = e.get(other)
                s = (v.get(lang) if isinstance(v, dict) else None) or ""
                if s.strip() and s.strip() in text:
                    errs.append(f"сущность {e['id']}: description.{lang} дословно "
                                f"повторяет {other} — описание добавляет, а не пересказывает")
        quoted = _numbers(" ".join(s.get("quote", "") for s in e.get("sources", [])))
        for lang in ("ru", "en"):
            unbacked = _unbacked(d.get(lang) or "", quoted)
            if unbacked:
                errs.append(f"сущность {e['id']}: числа в description.{lang} не "
                            f"встречаются ни в одной цитате этой сущности: "
                            f"{', '.join(unbacked[:6])}")
    return errs


def description_coverage(payload: dict) -> dict:
    """Сколько узлов уже описано. Для отчёта прогона, не для валидатора: описание —
    поле необязательное, и месяц, где его получили 27 узлов из 107, обязан
    отгрузиться, а не упасть."""
    ents = payload["entities"]
    piv = set(payload.get("pivots") or [])
    have = {e["id"] for e in ents if e.get("description")}
    return {"total": len(ents), "have": len(have),
            "pivots": len(piv), "pivots_have": len(piv & have),
            "pivots_missing": sorted(piv - have)}


# ── стиль прозы: то, что можно проверить машиной ─────────────────────────────
# Правила из хендоффа 2026-08-28. Проверяются здесь, а не только отчётом, потому
# что отчёт можно не посмотреть, а выпуск, который не пишется, — нельзя.
BANNED_PROSE = {
    # Слово, называвшее карту орбитой одной компании. Запрещено В ПРОЗЕ ВЫДАЧИ, и
    # именно поэтому названо здесь буквально: правило, которое нельзя записать, нельзя
    # и применить. С v4 у карты нет центра ни в механике, ни в словах.
    "якорь": r"якор[ьяюеё]\w*",
    "ров": r"\bров\b|\bрва\b|\bрву\b|\bровом\b",
    "узкое место": r"узк\w+\s+мест\w+",
    "движок": r"движ[ко]\w*",
    "anchor": r"\banchors?\b|\banchor's\b",
    "moat": r"\bmoats?\b",
    "bottleneck": r"\bbottlenecks?\b",
    "engine": r"\bengines?\b",
}


def _prose_style_errors(payload: dict) -> list:
    """Запрещённая лексика в любом пользовательском поле прозы.

    Цитаты источников НЕ проверяются: они на языке своего документа и стилю
    карты не подчиняются. Перефразировать цитату — значит перестать её цитировать.
    """
    import re
    errs = []
    # ТАКСОНОМИЯ ИСКЛЮЧЕНА. Запрет касается прозы, которая должна называть
    # вещи; подпись слоя, сектора или типа связи — это и есть имя категории, и
    # «Движки инференса» там правильный термин, а не отговорка.
    TAXONOMY = ("layers[", "sectors[", "techNodes[", "subgraphs[")
    for path, val in bilingual_paths(payload):
        if not isinstance(val, dict) or path.startswith(TAXONOMY):
            continue
        for lang in ("ru", "en"):
            s = val.get(lang) or ""
            for word, pat in BANNED_PROSE.items():
                if re.search(pat, s, re.I):
                    errs.append(f"{path}.{lang}: запрещённое слово «{word}» — "
                                f"назови сущность или механизм, а не категорию")
    return errs


def _unsourced_numbers(payload: dict) -> list:
    """Число в note или oneLiner, которого нет ни в одной цитате этого объекта.

    То же правило, что уже действует для detail. Эти поля читаются как данные и
    цитируются как данные, поэтому цифра без источника здесь дороже, чем
    отсутствие цифры.
    """
    errs = []
    for x in payload["edges"]:
        note = x.get("note")
        if not isinstance(note, dict):
            continue
        quoted = _numbers(" ".join(ev.get("quote", "") for ev in x.get("evidence", [])))
        for lang in ("ru", "en"):
            bad = sorted(_numbers(note.get(lang) or "") - quoted)
            if bad:
                errs.append(f"связь {x['id']}: числа в note.{lang} не встречаются "
                            f"ни в одной цитате: {', '.join(bad[:6])}")
    for e in payload["entities"]:
        quoted = _numbers(" ".join(s.get("quote", "") for s in e.get("sources", [])))
        ol = e.get("oneLiner")
        if isinstance(ol, dict):
            for lang in ("ru", "en"):
                bad = sorted(_numbers(ol.get(lang) or "") - quoted)
                if bad:
                    errs.append(f"сущность {e['id']}: числа в oneLiner.{lang} не "
                                f"встречаются ни в одной цитате: {', '.join(bad[:6])}")
        # ОБОСНОВАНИЯ ФАКТОРОВ — тоже проза, и цифра в них тоже обязана быть из
        # цитаты. Правило распространено сюда Фазой 1 ради `concentration`: доля
        # функции без источника — ровно та выдумка, которую четвёртый фактор мог бы
        # протащить в каждую оценку карты с весом 0.15. Раз уж проверка есть, она
        # применяется ко всем четырём обоснованиям, а не к одному избранному.
        for f, v in (e.get("criticalityWhy") or {}).items():
            if not isinstance(v, dict):
                continue
            for lang in ("ru", "en"):
                bad = _unbacked(v.get(lang) or "", quoted)
                if bad:
                    errs.append(f"сущность {e['id']}: числа в criticalityWhy.{f}.{lang} "
                                f"не встречаются ни в одной цитате этой сущности: "
                                f"{', '.join(bad[:6])}")
    return errs


# ── валидатор ────────────────────────────────────────────────────────────────
def validate(payload: dict) -> list:
    errs = []
    errs += _prose_style_errors(payload)
    errs += _unsourced_numbers(payload)
    m = payload.get("meta", {}).get("membership") or {}
    for k in ("admitted", "retired", "held", "queued", "enforced"):
        if k not in m:
            errs.append(f"meta.membership: нет поля {k}")
    if m.get("held") != len(m.get("heldNodes") or []):
        errs.append("meta.membership: held не сходится с heldNodes")
    if m.get("retired") != len(m.get("retiredNodes") or []):
        errs.append("meta.membership: retired не сходится с retiredNodes")
    # Снятый узел не может остаться в entities[]: «снят» и «на карте» — это
    # взаимоисключающие утверждения, и выпуск, который делает оба, неверен.
    on_map = {e["id"] for e in payload["entities"]}
    ghosts = [r["id"] for r in (m.get("retiredNodes") or []) if r["id"] in on_map]
    if ghosts:
        errs.append(f"meta.membership: снятые членством остались в entities[]: "
                    f"{', '.join(ghosts[:6])}")
    # Половина перевода — это ровно тот отказ, который мы убираем. Поэтому
    # пустая сторона роняет выпуск, а не уезжает в дашборд «на потом».
    errs += i18n.check(payload, bilingual_paths(payload))
    if payload.get("schema") != nvnet.SCHEMA_VERSION:
        errs.append(f"schema '{payload.get('schema')}' вместо {nvnet.SCHEMA_VERSION}")
    for k in ("anchor", "ecosystem"):
        if k in payload:
            errs.append(f"/4: поле '{k}' снято — у карты нет центра")
    if not payload.get("pivots"):
        errs.append("пустой список pivots (в /4 это состав ядра)")
    m = payload.get("meta") or {}
    if not ((m.get("scope") or {}).get("ru") and (m.get("scope") or {}).get("en")):
        errs.append("meta.scope: карта обязана называть свой предмет на обоих языках")
    if not m.get("coreRule"):
        errs.append("meta: нет coreRule")

    ids = [e["id"] for e in payload["entities"]]
    if len(ids) != len(set(ids)):
        errs.append("дублирующиеся id сущностей")
    idset = set(ids)
    layer_ids = {l["id"] for l in payload["layers"]}
    tech_ids = {t["id"] for t in payload["techNodes"]}
    types = nvnet.edge_types()

    for p in payload["pivots"]:
        if p not in idset:
            errs.append(f"узел ядра '{p}' отсутствует среди сущностей")

    core_ids = {e["id"] for e in payload["entities"] if e.get("core")}
    if core_ids != set(payload["pivots"]):
        errs.append("pivots не совпадает с составом core — поле обязано быть зеркалом")
    if len(core_ids) != nveco.core_n():
        errs.append(f"в ядре {len(core_ids)} узлов при правиле top-{nveco.core_n()}")
    for e in payload["entities"]:
        if "pivotal" not in e or not isinstance(e["pivotal"], bool):
            errs.append(f"сущность {e['id']}: нет булева pivotal")
        if "core" not in e or not isinstance(e["core"], bool):
            errs.append(f"сущность {e['id']}: нет булева core")
        if e.get("pivotal") != e.get("core"):
            errs.append(f"сущность {e['id']}: pivotal разошёлся с core, "
                        f"а обязан быть его зеркалом весь выпуск /4")
        if "hops" in e:
            errs.append(f"сущность {e['id']}: поле hops снято контрактом /4")
        basis = e.get("criticalityBasis")
        if not isinstance(basis, dict) or "factorsUsed" not in basis:
            errs.append(f"сущность {e['id']}: нет блока criticalityBasis — "
                        f"потребитель не может отличить оценку по четырём факторам "
                        f"от оценки по трём")
        else:
            used = [k for k, v in (e.get("criticalityFactors") or {}).items()
                    if v is not None]
            if basis.get("factorsUsed") != len(used):
                errs.append(f"сущность {e['id']}: criticalityBasis.factorsUsed "
                            f"{basis.get('factorsUsed')} при {len(used)} факторах")
        ig = e.get("integration") or {}
        if not isinstance(ig.get("score"), int) or not 0 <= ig["score"] <= 100:
            errs.append(f"сущность {e['id']}: integration.score вне 0..100")
        for k in ("degree", "betweenness", "pagerank", "layersSpanned",
                  "edgeTypes", "cycles"):
            if k not in ig:
                errs.append(f"сущность {e['id']}: в integration нет {k}")
        sg = e.get("sourcing") or {}
        if sg.get("total") != len(e.get("sources") or []):
            errs.append(f"сущность {e['id']}: sourcing.total не сходится с sources[]")
        if sg.get("selfSourced") is None:
            errs.append(f"сущность {e['id']}: нет sourcing.selfSourced")
        if "domains" not in e or not isinstance(e["domains"], list):
            errs.append(f"сущность {e['id']}: нет списка domains")
        # ЧЛЕНСТВО ВИДНО НА УЗЛЕ, А НЕ ТОЛЬКО В meta. Иначе «узел не проходит
        # проверку, но оставлен» превращается в невидимое исключение: на карте он
        # выглядит как все остальные.
        if not isinstance(e.get("pendingDossier"), bool):
            errs.append(f"сущность {e['id']}: нет булева pendingDossier")
        mf = e.get("membershipFailing")
        if not isinstance(mf, list):
            errs.append(f"сущность {e['id']}: membershipFailing должен быть списком")
        elif e.get("pendingDossier") and (set(mf) & GATED_CHECKS):
            errs.append(f"сущность {e['id']}: непокрытая досье сущность помечена "
                        f"провалом гейтированной проверки — гейт по покрытию нарушен")
        c = e.get("centrality") or {}
        if not isinstance(c.get("degree"), int) or c["degree"] < 0:
            errs.append(f"сущность {e['id']}: centrality.degree не целое")
        b = c.get("betweenness")
        if not isinstance(b, (int, float)) or isinstance(b, bool) or not 0 <= b <= 1:
            errs.append(f"сущность {e['id']}: centrality.betweenness вне 0..1")
        pr = c.get("pagerank")
        if not isinstance(pr, (int, float)) or isinstance(pr, bool) or not 0 <= pr <= 1:
            errs.append(f"сущность {e['id']}: centrality.pagerank вне 0..1")
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
                                    "concentration": f.get("concentration")})
        if "strategicControl" in f:
            errs.append(f"сущность {e['id']}: фактор strategicControl снят контрактом /4")
        if expect is None:
            errs.append(f"сущность {e['id']}: нет одного из трёх обязательных факторов")
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
        # ── лестница доказательства /4 ───────────────────────────────────────
        # Те же четыре правила, что в валидаторе семени. Дублируются НЕ копией
        # текста, а копией смысла: обе половины карты уезжают одному потребителю,
        # и статус, проверенный в одной и не проверенный в другой, — это дыра
        # ровно там, где данные и смешиваются.
        if x.get("status") not in nveco.STATUSES:
            errs.append(f"связь {x['id']}: status '{x.get('status')}'")
        if x.get("sidedness") not in nveco.SIDEDNESS:
            errs.append(f"связь {x['id']}: sidedness '{x.get('sidedness')}'")
        claimed = set(x.get("claimedBy") or [])
        if x.get("status") == "bilateral" and len(claimed) < 2:
            errs.append(f"связь {x['id']}: статус bilateral при {len(claimed)} "
                        f"подтвердивших стороне(ах) — нужны обе")
        if claimed - {x["source"], x["target"]}:
            errs.append(f"связь {x['id']}: claimedBy называет сторону вне связи")
        if x.get("status") == "disputed" and not x.get("counterEvidence"):
            errs.append(f"связь {x['id']}: статус disputed без контрцитаты")
        if x.get("counterEvidence") and x.get("status") != "disputed":
            errs.append(f"связь {x['id']}: есть контрцитата, а статус не disputed")
        if x["type"] not in types:
            errs.append(f"связь {x['id']}: тип '{x['type']}' вне таксономии v2+v3")
        # Хребет — производная типа, а не независимое поле. Расхождение означало
        # бы, что ребро покрашено не тем цветом и прочитано не тем механизмом.
        elif x.get("spine") != types[x["type"]].get("spine"):
            errs.append(f"связь {x['id']}: хребет '{x.get('spine')}' не совпадает "
                        f"с хребтом типа '{x['type']}' "
                        f"({types[x['type']].get('spine')})")
        # И тип обязан быть в таблице, которую МЫ ЖЕ отдаём в этом файле:
        # потребитель читает её отсюда, поэтому дыра в ней — это дыра у него.
        if x["type"] not in (payload.get("edgeTypes") or {}):
            errs.append(f"связь {x['id']}: тип '{x['type']}' отсутствует в "
                        f"edgeTypes самой выдачи — потребитель не сможет его отрисовать")
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

    errs += _check_detail(payload)
    errs += _check_description(payload)

    # PageRank — доля важности, и сумма долей обязана равняться единице. Расхождение
    # означает, что мера посчитана на другом множестве узлов или обрезана после
    # нормировки; и то и другое делает числа несравнимыми между прогонами.
    prs = [(e.get("centrality") or {}).get("pagerank") for e in payload["entities"]]
    prs = [x for x in prs if isinstance(x, (int, float)) and not isinstance(x, bool)]
    if prs and abs(sum(prs) - 1.0) > 1e-3:
        errs.append(f"сумма centrality.pagerank = {round(sum(prs), 6)}, а должна быть ≈1")

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
# Причины в чейнджлоге — ЭТО ПРОЗА ВЫДАЧИ, и правило двуязычия на неё
# распространяется наравне со всем остальным. Голая русская строка здесь уезжает
# английскому читателю по-русски, и аудит перевода на стороне дашборда роняет сборку —
# правильно роняет. Поэтому ни одной голой строки: только пары.
_WHY = {
    "node_gone": {"ru": "больше не подтверждается",
                  "en": "no longer confirmed"},
    "edge_gone": {"ru": "связь больше не заявлена",
                  "en": "the link is no longer claimed"},
    "core_in": {"ru": "поднялся в верхние по интеграции",
                "en": "rose into the top by integration"},
    "core_out": {"ru": "опустился ниже порога ядра",
                 "en": "fell below the core threshold"},
    "core_off_map": {"ru": "ушёл с карты",
                     "en": "left the map"},
    "core_first": {"ru": "первый выпуск, где ядро вычислено, а не назначено",
                   "en": "first release where the core is computed, not assigned"},
    "baseline": {"ru": "первый выпуск сети: семя пилота плюс достройка связей; "
                       "категории изменений заполнятся со следующего выпуска",
                 "en": "first network release: the pilot seed plus the added links; "
                       "the change categories fill in from the next release on"},
}


def _cl_has_changes(cl: dict) -> bool:
    """Несёт ли чейнджлог хоть одну содержательную строку.

    `baseline` считается изменением: первый выпуск — тоже событие. Служебные ключи
    (`month`, `version`, `rerun`) не считаются.
    """
    if cl.get("baseline"):
        return True
    return any(cl.get(k) for k in nvnet.CHANGE_CATEGORIES)


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
            "note": _WHY["baseline"],
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
        cl["coreChanges"] = [{"id": e["id"], "move": "in",
                              "integration": e["integration"]["score"],
                              "why": _WHY["core_first"]}
                             for e in cur["entities"] if e["core"]]
        return cl

    pe = {x["id"]: x for x in prev.get("entities", [])}
    ce = {x["id"]: x for x in cur["entities"]}
    pg = {x["id"]: x for x in prev.get("edges", [])}
    cg = {x["id"]: x for x in cur["edges"]}
    cl["newNodes"] = [{"id": i, "why": ce[i].get("oneLiner")} for i in sorted(set(ce) - set(pe))]
    cl["removedNodes"] = [{"id": i, "why": _WHY["node_gone"]}
                          for i in sorted(set(pe) - set(ce))]
    cl["relationshipsAdded"] = [{"id": i, "why": cg[i].get("note")}
                                for i in sorted(set(cg) - set(pg))]
    cl["relationshipsRemoved"] = [{"id": i, "why": _WHY["edge_gone"]}
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
    # ВХОД И ВЫХОД ИЗ ЯДРА. Сравнивается с тем, что прошлый выпуск НАЗЫВАЛ ядром,
    # каким бы способом он к этому ни пришёл: в /3 это был список из конфига, в /4 —
    # верхние 30 по integration. Именно поэтому сравнение идёт по признаку в файле, а
    # не по правилу: переход от назначенного ядра к вычисленному сам по себе есть
    # изменение состава, и спрятать его за «правило поменялось» нельзя.
    def _core_of(payload):
        got = {x["id"] for x in payload.get("entities", []) if x.get("core")}
        return got or set(payload.get("pivots") or [])

    pc, cc = _core_of(prev), _core_of(cur)
    cl["coreChanges"] = (
        [{"id": i, "move": "in", "integration": ce[i]["integration"]["score"],
          "why": _WHY["core_in"]} for i in sorted(cc - pc)]
        + [{"id": i, "move": "out",
            "integration": (ce[i]["integration"]["score"] if i in ce else None),
            "why": _WHY["core_out"] if i in ce else _WHY["core_off_map"]}
           for i in sorted(pc - cc)])

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


def _ru(v):
    """Русская сторона двуязычного поля для человекочитаемого чейнджлога.

    Проза выдачи с v4 везде пара {ru, en}, а чейнджлог читает человек и по-русски.
    Без этой развёртки в файл попадал сам словарь: `{'ru': …, 'en': …}` посреди
    предложения. Ошибкой контракта это не было — файл-спутник валидатор не проверяет,
    — но читать его стало нельзя, и это заметно только глазами.
    """
    if isinstance(v, dict):
        return v.get("ru") or v.get("en") or ""
    return v if v is not None else ""


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

    L += ["## Центральность — три меры, три разных вопроса", "",
          "`degree` — со сколькими связан · `betweenness` — через кого идут пути · "
          "`pagerank` — на кого опираются те, на кого опираются сами.", ""]
    for key, title in (("betweenness", "По betweenness — кто держит пути"),
                       ("pagerank", "По pagerank — на кого опирается сеть")):
        L += [f"### {title}", "",
              "| сущность | degree | betweenness | pagerank | пивот |",
              "|---|---|---|---|---|"]
        top = sorted(cur["entities"], key=lambda e: -e["centrality"][key])[:10]
        L += [f"| {_ru(e['name'])} | {e['centrality']['degree']} | "
              f"{e['centrality']['betweenness']} | {e['centrality']['pagerank']} | "
              f"{'да' if e['pivotal'] else '—'} |" for e in top]
        L += [""]

    if n["singlePointsOfFailure"]:
        L += ["## Точки отказа", ""]
        L += [f"- **{_ru(s['name'])}** ({s['layer']}, betweenness {s['betweenness']}) "
              f"— {_ru(s['reason'])}" for s in n["singlePointsOfFailure"]]
        L += [""]

    L += ["## Подграфы", ""]
    for s in n["subgraphs"]:
        mark = " — **ВЫРОЖДЕН**" if s.get("degenerate") else ""
        L += [f"- **{_ru(s['label'])}**{mark}: {len(s['nodeIds'])} узлов, "
              f"{len(s['edgeIds'])} внутренних связей. {_ru(s['description'])}."]
    for note in n.get("subgraphNotes", []):
        L += [f"  - {note}"]
    L += [""]

    L += [f"## Изменения по {len(nvnet.CHANGE_CATEGORIES)} категориям", "",
          "| категория | записей |", "|---|---|"]
    RU = {"newNodes": "новые узлы", "removedNodes": "удалённые узлы",
          "relationshipsAdded": "связи +", "relationshipsRemoved": "связи −",
          "relationshipsUpdated": "связи ~", "criticalityShifts": "сдвиг критичности >5",
          "phaseChanges": "смена фазы", "riskEscalations": "эскалация риска",
          "newSources": "новые источники", "layerChanges": "смена слоя",
          "coreChanges": "вход/выход из ядра"}
    L += [f"| {RU[k]} | {len(cl.get(k) or [])} |" for k in nvnet.CHANGE_CATEGORIES]
    L += [""]

    core = cl.get("coreChanges") or []
    if core:
        ins = [c for c in core if c["move"] == "in"]
        outs = [c for c in core if c["move"] == "out"]
        L += [f"## Вход и выход из ядра ({len(ins)} / {len(outs)})", "",
              f"Ядро вычисляется, а не назначается: {cur['meta']['coreRule']}. "
              f"Движение состава — такая же находка карты, как новая связь.", ""]
        if ins:
            L += ["**Вошли.**", ""] + [
                f"- `{c['id']}` — интеграция {c['integration']}" for c in ins[:40]] + [""]
        if outs:
            L += ["**Вышли.**", ""] + [
                f"- `{c['id']}` — интеграция {c['integration']}, {_ru(c['why'])}"
                for c in outs[:40]] + [""]

    added = cl.get("relationshipsAdded") or []
    if added:
        L += [f"## Добавленные связи ({len(added)})", ""]
        L += [f"- `{r['id']}` — {_ru(r.get('why'))}" for r in added[:25]]
        L += [""]
    return "\n".join(L)


# ЯРУС РОТАЦИИ — по ЛУЧШЕМУ из двух рангов, а не по одной интеграции.
#
# Фаза 0 задала этот вопрос и не стала решать его сама: «возможно, ярус должен
# считаться по максимуму из двух осей». Фаза 2 решила — да, и вот почему.
#
# По интеграции ASML 52-я, Carl Zeiss SMT 108-й из 108. По критичности они же 7-я и
# 9-й. Ярус от одной интеграции отправил бы обоих в квартальный и триггерный циклы,
# то есть исследовал бы РЕЖЕ ВСЕГО те узлы, про которые карта знает МЕНЬШЕ ВСЕГО.
# Низкая интеграция такого узла — в большой мере мера нашего незнания о нём: у ASML
# на карте три связи не потому, что их три, а потому, что их никто не искал. Ротация,
# считающая ярус по интеграции, закрепляла бы это незнание навсегда.
#
# `core` в payload при этом остаётся ЧИСТО интеграционным: контракт определяет его
# как топ-30 по integration, дашборд ранжирует по нему. Ярус ротации и состав ядра —
# два разных вопроса, и слить их в одно понятие значило бы повторить ошибку якоря,
# который делал три работы сразу. Поэтому rota_tier='core' и core=1 расходятся, и
# расхождение записано колонкой `rota_basis`: по какой оси узел попал в свой ярус.
#
# Пороги — config/nveco_scope.yaml, блок `rotation`.


def rotation_tier(rank: int, total: int, core_n: int, mid_share: float = None) -> str:
    if mid_share is None:
        mid_share = nveco.rotation_cfg()["mid_share"]
    if rank < core_n:
        return "core"
    return "mid" if rank < core_n + round((total - core_n) * mid_share) else "tail"


def persist_integration(month: str, payload: dict) -> int:
    """Сложить `integration` и ярус в базу.

    Мера считается при сборке выдачи, а нужна ДО неё — пакетчику досье, чтобы знать,
    кого исследовать в этом месяце. Файл для этого читать нельзя: он выпускается в
    конце прогона, и пакетчик, читающий его, работал бы по позапрошлой карте.
    """
    con = nveco.connect()
    con.execute("""CREATE TABLE IF NOT EXISTS nvnet_integration (
                     entity_id TEXT PRIMARY KEY, run_month TEXT, score INTEGER,
                     degree INTEGER, betweenness REAL, pagerank REAL,
                     layers_spanned INTEGER, edge_types INTEGER, cycles INTEGER,
                     rank INTEGER, core INTEGER, rota_tier TEXT)""")
    for col, decl in (("crit_rank", "INTEGER"), ("rota_rank", "INTEGER"),
                      ("rota_basis", "TEXT")):
        if col not in {r[1] for r in con.execute("PRAGMA table_info(nvnet_integration)")}:
            con.execute(f"ALTER TABLE nvnet_integration ADD COLUMN {col} {decl}")
    ents = sorted(payload["entities"], key=lambda e: (-e["integration"]["score"],
                                                      -e["integration"]["degree"], e["id"]))
    rot = nveco.rotation_cfg()
    core_n = nveco.core_n()
    int_rank = {e["id"]: i for i, e in enumerate(ents)}
    # Второй ранг — по критичности. Ничьи разрешаются так же, как у интеграции
    # (по степени, затем по id), иначе ярус прыгал бы между прогонами на одних
    # и тех же данных.
    by_crit = sorted(payload["entities"],
                     key=lambda e: (-(e.get("criticality") or 0),
                                    -e["integration"]["degree"], e["id"]))
    crit_rank = {e["id"]: i for i, e in enumerate(by_crit)}
    basis = rot["basis"]
    con.execute("DELETE FROM nvnet_integration")
    rows = []
    for e in ents:
        ir, cr = int_rank[e["id"]], crit_rank[e["id"]]
        if basis == "integration":
            rr, why = ir, "integration"
        elif basis == "criticality":
            rr, why = cr, "criticality"
        else:
            rr = min(ir, cr)
            why = "integration" if ir <= cr else "criticality"
        rows.append((e, ir, cr, rr, why))
    # Ранг ротации пересортировывается заново: min() двух рангов даёт дубли, а ярус
    # обязан быть сплошным порядком, иначе «верхние 30» окажутся не тридцатью.
    rows.sort(key=lambda x: (x[3], x[1], x[0]["id"]))
    for pos, (e, ir, cr, rr, why) in enumerate(rows):
        ig = e["integration"]
        con.execute("""INSERT INTO nvnet_integration (entity_id, run_month, score, degree,
                         betweenness, pagerank, layers_spanned, edge_types, cycles,
                         rank, core, rota_tier, crit_rank, rota_rank, rota_basis)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (e["id"], month, ig["score"], ig["degree"], ig["betweenness"],
                     ig["pagerank"], ig["layersSpanned"], ig["edgeTypes"], ig["cycles"],
                     ir + 1, 1 if e.get("core") else 0,
                     rotation_tier(pos, len(rows), rot["core_n"], rot["mid_share"]),
                     cr + 1, pos + 1, why))
    con.commit()
    con.close()
    return len(ents)


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
    persist_integration(month, payload)
    cl = _changelog(prev, payload, net)
    # ПОВТОРНЫЙ ПРОГОН — НЕ НОВЫЙ ВЫПУСК. Базой чейнджлога служит ранее записанный
    # payload, поэтому прогон, ничего не изменивший, честно даёт пустой diff — и этим
    # СТИРАЕТ запись о том, что несёт выпуск. Один прогон «чтобы пересобрать после
    # правки скрипта» — и файл сообщает «изменений нет» там, где на деле уехали
    # четыре связи. Пустой diff при той же версии оставляет прежний чейнджлог.
    if prev and prev.get("version") == payload["version"] and not _cl_has_changes(cl) \
            and _cl_has_changes(prev.get("changelog") or {}):
        cl = prev["changelog"]
        cl["rerun"] = ("прогон не изменил ни одной строки; чейнджлог выпуска "
                       "сохранён от предыдущего прогона того же месяца")
    payload["changelog"] = cl
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    OUT_MD.write_text(_changelog_md(payload, cl, net))
    core_top = sorted((e for e in payload["entities"] if e["core"]),
                      key=lambda e: -e["integration"]["score"])[:8]
    return {"ok": True, "errors": [], "path": str(OUT_JSON),
            "entities": payload["totals"]["entities"],
            "edges": payload["totals"]["edges"],
            "version": payload["version"], "network": payload["network"],
            "coreRule": payload["meta"]["coreRule"],
            "coreTop": core_top,
            "membership": payload["meta"]["membership"],
            "descriptions": description_coverage(payload)}


if __name__ == "__main__":
    from . import nvnet_ingest
    m = sys.argv[1] if len(sys.argv) > 1 else nveco.current_month()
    print(run(m, nvnet_ingest.build(m)))
