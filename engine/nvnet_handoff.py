"""Сборка handoff/ai_ecosystem_network.json + валидатор + чейнджлог по 10 категориям.

Контракт v3 РАСШИРЯЕТ v2, а не заменяет: 16 слоёв, 5 хребтов, рубрика, тиры и форма
Source приходят из семени без изменений. Новое здесь — `pivots` вместо `anchor`,
`pivotal` на сущности, `centrality`, блок `network` и версия выпуска.

Как и в v2, файл, не прошедший валидатор, НЕ ПИШЕТСЯ. Предыдущий остаётся: отдать
дашборду битую сеть хуже, чем не отдать новую.
"""

import json
import re
import sys
from datetime import date

from . import db, i18n, nveco, nvnet, nvnet_centrality, nvnet_spof, nvnet_subgraphs

OUT_JSON = db.HANDOFF_DIR / "ai_ecosystem_network.json"
OUT_MD = db.HANDOFF_DIR / "AI-ECOSYSTEM-NETWORK-CHANGELOG.md"


class ContractError(AssertionError):
    pass


def build(month: str, net: dict) -> dict:
    seed = net["seed"]
    entities = [net["entities"][k] for k in sorted(net["entities"])]
    edges = [net["edges"][k] for k in sorted(net["edges"])]

    metrics = nvnet_centrality.run([e["id"] for e in entities], edges,
                                  nvnet.pagerank_dependence())
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
                      "strategicControl"),
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
    "timeToReplace": "why_time", "strategicControl": "why_control",
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
                e[f] = w("entity", eid, f, e[f])
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
            x["note"] = w("edge", xid, "note", x["note"])
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
    """Числа текста, ни одно прочтение которых не встречается в цитатах."""
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
    text = _THOUSANDS.sub(lambda m: m.group(0).replace("\u00a0", "").replace(" ", ""),
                          text or "")
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


# ── валидатор ────────────────────────────────────────────────────────────────
def validate(payload: dict) -> list:
    errs = []
    # Половина перевода — это ровно тот отказ, который мы убираем. Поэтому
    # пустая сторона роняет выпуск, а не уезжает в дашборд «на потом».
    errs += i18n.check(payload, bilingual_paths(payload))
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
        pr = c.get("pagerank")
        if not isinstance(pr, (int, float)) or isinstance(pr, bool) or not 0 <= pr <= 1:
            errs.append(f"сущность {e['id']}: centrality.pagerank вне 0..1")
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

    L += ["## Центральность — три меры, три разных вопроса", "",
          "`degree` — со сколькими связан · `betweenness` — через кого идут пути · "
          "`pagerank` — на кого опираются те, на кого опираются сами.", ""]
    for key, title in (("betweenness", "По betweenness — кто держит пути"),
                       ("pagerank", "По pagerank — на кого опирается сеть")):
        L += [f"### {title}", "",
              "| сущность | degree | betweenness | pagerank | пивот |",
              "|---|---|---|---|---|"]
        top = sorted(cur["entities"], key=lambda e: -e["centrality"][key])[:10]
        L += [f"| {e['name']} | {e['centrality']['degree']} | "
              f"{e['centrality']['betweenness']} | {e['centrality']['pagerank']} | "
              f"{'да' if e['pivotal'] else '—'} |" for e in top]
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
            "version": payload["version"], "network": payload["network"],
            "descriptions": description_coverage(payload)}


if __name__ == "__main__":
    from . import nvnet_ingest
    m = sys.argv[1] if len(sys.argv) > 1 else nveco.current_month()
    print(run(m, nvnet_ingest.build(m)))
