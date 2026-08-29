"""Загрузка выдач агентов: четыре CSV -> валидация -> резолвинг -> дедуп -> SQLite.

Читает runs/<YYYY-MM>/nveco-*/{entities,factors,edges,sources}.csv, проверяет каждую
строку против ЗАМОРОЖЕННЫХ конфигов (слой существует? тип связи существует? фактор в
0..100? цитата не длиннее 15 слов?), разрешает имена в постоянные id через общий
config/aliases.yaml и грузит в nveco_*.

Три вещи, которые модуль отказывается делать:
  * записать ребро без источника с дословной цитатой;
  * записать сущность, не работающую ни в одном слое охвата (config/nveco_scope.yaml);
  * записать вычисляемое поле со слов агента — spine, criticality, status, gravity,
    sidedness и тир источника считает движок, и попытка агента их прислать
    игнорируется.

Правило «не дальше двух шагов от центра» отсюда ВЫРЕЗАНО в v4 вместе с полем `hops`:
центра у карты больше нет, а границу задают три проверки — см. блок «членство» ниже.

Отвергнутые строки не молчат: пишутся в runs/<month>/_rejected/<agent>.csv с причиной
и считаются в nveco_run. Это то, что следующий месяц вернёт агентам.

Идемпотентно: ключ — постоянный id, повторный прогон обновляет на месте.

И АВТОРИТЕТНО за свой месяц: строка, исчезнувшая из CSV, снимается с карты вместе с
источниками, переводом и участием в контурах. Снимается только за теми агентами, кто в
этом месяце реально сдал файл, — молчание остальных ничего не отзывает. Правило целиком
и его четыре случая — над `_retiring_agents`.
"""

import csv
import sys

from . import db, nveco
from .ingest import is_search_url

ENTITY_COLUMNS = ["id", "name", "aliases", "type", "role", "sector", "primary_layer",
                  "domain",
                  "layers", "phase", "ticker", "public_private", "geo", "founded",
                  "revenue_usd_b", "one_liner", "why_irreplaceable", "what_breaks_it",
                  "geo_risk", "geo_risk_note", "export_regime", "concentration"]
FACTOR_COLUMNS = ["entity_id", "irreplaceability", "lock_in_depth", "time_to_replace",
                  "concentration", "why_irreplaceability", "why_lock_in",
                  "why_time", "why_concentration"]
EDGE_COLUMNS = ["source", "target", "type", "direction", "strength", "lock_in_depth",
                "substitutability", "is_reversible", "risk_level", "risk_type",
                "risk_timeline", "risk_mitigation", "tech_node", "formed",
                "strengthened", "note"]
SOURCE_COLUMNS = ["owner_kind", "owner_key", "tier", "type", "title", "url",
                  "published", "quote", "confidence"]

WHY_COLUMNS = {"irreplaceability": "why_irreplaceability", "lock_in_depth": "why_lock_in",
               "time_to_replace": "why_time", "concentration": "why_concentration"}


def _s(row, key):
    return (row.get(key) or "").strip()


def _bool(v, default=True):
    s = (v or "").strip().lower()
    if s in ("true", "1", "yes", "да"):
        return True
    if s in ("false", "0", "no", "нет"):
        return False
    return default


def _int(value, lo, hi):
    v = (value or "").strip()
    if v == "":
        return None, "пусто"
    try:
        n = int(float(v))
    except ValueError:
        return None, f"не число: '{v}'"
    if not lo <= n <= hi:
        return None, f"{n} вне диапазона {lo}..{hi}"
    return n, None


def _limit(errors, field, text, limit):
    if text and len(text) > limit:
        errors.append(f"{field}: {len(text)} знаков при пределе {limit}")


# ── строки ───────────────────────────────────────────────────────────────────
def _validate_entity(row, layer_ids, sector_idx):
    errors, warnings = [], []
    name = _s(row, "name")
    if not name:
        return None, ["нет name"], []
    eid = _s(row, "id") or nveco.entity_id(name)

    etype = _s(row, "type").lower()
    if etype not in nveco.ENTITY_TYPES:
        errors.append(f"type '{etype}' не из перечисления")
    role = _s(row, "role").lower()
    if role not in nveco.ROLES:
        errors.append(f"role '{role}' не из перечисления")
    phase = _s(row, "phase").lower() or "mature"
    if phase not in nveco.PHASES:
        errors.append(f"phase '{phase}' не из перечисления")

    primary = _s(row, "primary_layer").upper()
    layers = [l.strip().upper() for l in _s(row, "layers").split("|") if l.strip()]
    if not layers and primary:
        layers = [primary]
    if not primary and layers:
        primary = layers[0]
    if primary not in layer_ids:
        errors.append(f"primary_layer '{primary}' нет в config/nveco_layers.yaml")
    for l in layers:
        if l not in layer_ids:
            errors.append(f"слой '{l}' нет в config/nveco_layers.yaml")
    if primary and layers and primary not in layers:
        layers.insert(0, primary)   # primary обязан входить в layers

    sector = _s(row, "sector") or None
    if sector:
        meta = sector_idx.get(sector)
        if not meta:
            warnings.append(f"сектор '{sector}' не из таксономии — записан как есть")
        elif meta["layer"] not in layers:
            warnings.append(f"сектор '{sector}' принадлежит {meta['layer']}, "
                            f"которого нет среди слоёв сущности")

    pp = _s(row, "public_private").lower() or None
    if pp and pp not in nveco.PUBLIC_PRIVATE:
        errors.append(f"public_private '{pp}' не из перечисления")

    geo_risk = _s(row, "geo_risk").lower() or "low"
    if geo_risk not in nveco.RISK_LEVELS:
        errors.append(f"geo_risk '{geo_risk}' не из перечисления")
    conc, err = _int(row.get("concentration"), 0, 100)
    if err and _s(row, "concentration"):
        errors.append(f"concentration: {err}")

    rev = None
    if _s(row, "revenue_usd_b"):
        try:
            rev = float(_s(row, "revenue_usd_b").replace(",", ""))
        except ValueError:
            warnings.append(f"revenue_usd_b '{_s(row, 'revenue_usd_b')}' — не число, отброшено")

    for field, limit in (("one_liner", nveco.TEXT_LIMITS["one_liner"]),
                         ("why_irreplaceable", nveco.TEXT_LIMITS["why_irreplaceable"]),
                         ("what_breaks_it", nveco.TEXT_LIMITS["what_breaks_it"]),
                         ("geo_risk_note", nveco.TEXT_LIMITS["geo_risk_note"])):
        _limit(errors, field, _s(row, field), limit)

    if errors:
        return None, errors, warnings
    return {
        "id": eid, "name": name,
        "aliases": _s(row, "aliases") or None, "type": etype, "role": role,
        "sector": sector, "primary_layer": primary, "layers": layers, "phase": phase,
        # Домен принимается как есть и только проверенный: движок не достраивает
        # его из имени — oracle.ai прошло бы такую проверку, не будучи Oracle.
        "domain": (_s(row, "domain") or "").lower().removeprefix("www.") or None,
        "ticker": _s(row, "ticker") or None, "public_private": pp,
        "geo": _s(row, "geo") or None, "founded": _s(row, "founded") or None,
        "revenue_usd_b": rev, "one_liner": _s(row, "one_liner") or None,
        "why_irreplaceable": _s(row, "why_irreplaceable") or None,
        "what_breaks_it": _s(row, "what_breaks_it") or None,
        "geo_risk": geo_risk, "geo_risk_note": _s(row, "geo_risk_note") or None,
        "export_regime": _s(row, "export_regime") or None, "concentration": conc,
    }, [], warnings


def _validate_factors(row):
    """Три обязательных фактора и один необязательный.

    `concentration` необязателен НЕ ради послабления, а потому что его источник —
    досье узла, которого у большинства сущностей ещё нет. Пустая клетка честно
    значит «доля функции не измерена»; выдуманный ноль значил бы «функции у узла
    нет», и с весом 0.15 эта выдумка попала бы в каждую оценку карты.

    Строгость там, где она нужна: если цифра ЕСТЬ, обоснование обязательно, а
    обоснование обязано опираться на цитату — это проверяет валидатор выдачи.
    Пустая пара «нет цифры и нет обоснования» проходит; «цифра без обоснования» и
    «обоснование без цифры» — нет.
    """
    errors, warnings = [], []
    eid = _s(row, "entity_id")
    if not eid:
        return None, ["нет entity_id"], []
    if _s(row, "strategic_control"):
        warnings.append("колонка strategic_control из контракта v3 игнорируется: "
                        "фактор снят вместе с центром карты, на его месте "
                        "concentration — доля СВОЕЙ функции, не рычаг чужой компании")
    out = {"entity_id": eid, "factors": {}}
    for f in nveco.FACTORS:
        required = f in nveco.REQUIRED_FACTORS
        raw = (row.get(f) or "").strip()
        why = _s(row, WHY_COLUMNS[f])
        if not raw and not required:
            if why:
                errors.append(f"{WHY_COLUMNS[f]}: обоснование есть, а цифры нет")
            continue
        v, err = _int(raw, 0, 100)
        if err:
            errors.append(f"{f}: {err}"
                          + (" (обязательный фактор, 0..100)" if required else ""))
        _limit(errors, WHY_COLUMNS[f], why, nveco.TEXT_LIMITS["why"])
        if not why:
            errors.append(f"{WHY_COLUMNS[f]}: пусто — оценка без обоснования не принимается")
        out["factors"][f] = (v, why)
    return (None, errors, warnings) if errors else (out, [], warnings)


def _validate_edge(row, types):
    errors, warnings = [], []
    src, tgt = _s(row, "source"), _s(row, "target")
    if not src:
        errors.append("нет source")
    if not tgt:
        errors.append("нет target")

    etype = _s(row, "type").lower()
    if etype not in types:
        errors.append(f"тип связи '{etype}' нет в config/nveco_edges.yaml")

    direction = _s(row, "direction").lower() or nveco.default_direction(etype) or "downstream"
    if direction not in nveco.DIRECTIONS:
        errors.append(f"direction '{direction}' не из перечисления")

    strength, err = _int(row.get("strength"), 0, 100)
    if err:
        errors.append(f"strength: {err}")
    lock, lerr = _int(row.get("lock_in_depth"), 0, 100)
    subst, serr = _int(row.get("substitutability"), 0, 100)
    if lerr and _s(row, "lock_in_depth"):
        warnings.append(f"lock_in_depth: {lerr} — отброшено")
    if serr and _s(row, "substitutability"):
        warnings.append(f"substitutability: {serr} — отброшено")

    risk_level = _s(row, "risk_level").lower() or None
    if risk_level and risk_level not in nveco.RISK_LEVELS:
        errors.append(f"risk_level '{risk_level}' не из перечисления")
    risk_type = _s(row, "risk_type").lower() or None
    if risk_type and risk_type not in nveco.RISK_TYPES:
        errors.append(f"risk_type '{risk_type}' не из перечисления")
    risk_timeline = _s(row, "risk_timeline").lower() or None
    if risk_timeline and risk_timeline not in nveco.RISK_TIMELINES:
        errors.append(f"risk_timeline '{risk_timeline}' не из перечисления")

    _limit(errors, "note", _s(row, "note"), nveco.TEXT_LIMITS["note"])
    _limit(errors, "risk_mitigation", _s(row, "risk_mitigation"),
           nveco.TEXT_LIMITS["risk_mitigation"])

    if errors:
        return None, errors, warnings
    return {
        "source": src, "target": tgt, "type": etype,
        "spine": nveco.spine_of(etype), "direction": direction, "strength": strength,
        "lock_in_depth": lock, "substitutability": subst,
        "is_reversible": _bool(row.get("is_reversible"), True),
        "risk_level": risk_level, "risk_type": risk_type, "risk_timeline": risk_timeline,
        "risk_mitigation": _s(row, "risk_mitigation") or None,
        "tech_node": _s(row, "tech_node") or None,
        "formed": _s(row, "formed") or None,
        "strengthened": _s(row, "strengthened") or None,
        "note": _s(row, "note") or None,
    }, [], warnings


def _validate_source(row):
    errors, warnings = [], []
    kind = _s(row, "owner_kind").lower()
    if kind not in ("entity", "edge"):
        errors.append(f"owner_kind '{kind}' должен быть entity или edge")
    key = _s(row, "owner_key")
    if not key:
        errors.append("нет owner_key")

    tier, err = _int(row.get("tier"), 1, 6)
    if err:
        errors.append(f"tier: {err}")
    stype = _s(row, "type").lower()
    if stype not in nveco.SOURCE_TYPES:
        errors.append(f"type '{stype}' не из перечисления источников")

    url = _s(row, "url")
    if not url:
        errors.append("нет url")
    elif not url.lower().startswith("http"):
        errors.append(f"url не ссылка: '{url[:50]}'")
    elif is_search_url(url):
        errors.append("url — поисковый запрос, а не резолвленный документ")

    quote = (row.get("quote") or "").strip()
    if not quote:
        errors.append("нет цитаты — железное правило: нет цитаты, нет связи")
    elif nveco.word_count(quote) > nveco.MAX_QUOTE_WORDS:
        errors.append(f"цитата {nveco.word_count(quote)} слов при пределе "
                      f"{nveco.MAX_QUOTE_WORDS} — возьмите фразу, где отношение названо")

    # Тир — свойство источника ОТНОСИТЕЛЬНО ПРЕДМЕТА, а не мнение агента. Здесь
    # известен только владелец строки, поэтому предметом считается он: для источника
    # сущности это она сама, для источника связи — её первый конец. Второй конец
    # подставит nveco_score, когда связь уже собрана, и там тир пересчитывается
    # начисто. Здесь только предупреждение — расхождение не повод терять цитату.
    if url and tier:
        subject = key if kind == "entity" else (key.split("__")[0] if key else None)
        expect, _ = nveco.source_tier(url, subject)
        if expect and expect != tier:
            warnings.append(f"тир {tier} заявлен там, где по реестру издателей "
                            f"относительно '{subject}' тир {expect}")

    conf = None
    if _s(row, "confidence"):
        try:
            conf = float(_s(row, "confidence"))
            if not 0 <= conf <= 1:
                warnings.append("confidence вне 0..1 — пересчитан из тира")
                conf = None
        except ValueError:
            conf = None
    if conf is None and tier:
        conf = nveco.tier_confidence(tier)

    if errors:
        return None, errors, warnings
    return {"owner_kind": kind, "owner_key": key, "tier": tier, "type": stype,
            "title": _s(row, "title") or None, "url": url,
            "published": _s(row, "published") or None, "quote": quote,
            "confidence": conf}, [], warnings


# ── проход по файлам ─────────────────────────────────────────────────────────
def _read(path):
    with path.open(newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            yield i, row


# ── членство ─────────────────────────────────────────────────────────────────
# Правило «не дальше двух шагов от центра» вырезано целиком. На его месте три проверки из
# config/nveco_scope.yaml, и ни одна из них не называет ни одной компании:
#
#   1  in_scope            — сущность работает хотя бы в одном слое охвата
#   2  min_sources         — у неё СВОЁ досье: >= N источников,
#      min_self_sources      из них >= M изданы ею самой
#   3  min_confirmed_edges — >= K подтверждённых связей с сущностями на карте
#
# Почему прежнее правило пришлось выбросить, а не подкрутить. Оно отвечало на вопрос
# «далеко ли отсюда до центра», а вопрос членства звучит иначе: «занимается ли эта
# сущность нашим предметом и знаем ли мы о ней хоть что-то из первых рук». Второй
# вопрос центра не требует. Практическое следствие: Carl Zeiss SMT — три шага от
# NVIDIA и потому вне старой карты, при том что у него есть и подтверждённые связи с
# ASML, и собственные публикации. Новое правило впускает его, не двигая ни одного
# порога.
#
# В ФАЗЕ 0 ПРОВЕРКИ СЧИТАЮТСЯ, НО НЕ ОТКЛОНЯЮТ (membership.enforce: false). Причина
# в журнале сборки: сорока сущностям карты нечего предъявить от себя, и включение
# правила сегодня снесло бы две пятых карты раньше, чем приедут досье. Отчёт пишется
# всегда — молча не проходит ничего.


def membership_report(ents, edges, srcs, statuses=None) -> dict:
    """Кто прошёл бы три проверки, а кто нет. Ничего не отклоняет.

    statuses — {edge_id: status} с прошлого прогона, если он есть: подтверждённость
    связи считает nveco_score ПОСЛЕ загрузки, и на первом прогоне её ещё нет. Когда
    статусов нет, третья проверка считается по числу связей вообще, и это записано
    в самом отчёте, чтобы цифру нельзя было принять за подтверждённые.
    """
    cfg = nveco.membership_cfg()
    scope_layers = set(nveco.scope_layers())
    min_src = int(cfg.get("min_sources", 0))
    min_self = int(cfg.get("min_self_sources", 0))
    min_edges = int(cfg.get("min_confirmed_edges", 0))
    strong = ("bilateral", "confirmed")

    by_ent = {}
    for s in srcs:
        if s["owner_kind"] == "entity":
            by_ent.setdefault(s["owner_key"], []).append(s)
    deg = {}
    for e in edges.values():
        ok = True if statuses is None else statuses.get(e.get("id") or "") in strong
        if not ok:
            continue
        for side in (e["source"], e["target"]):
            deg[side] = deg.get(side, 0) + 1

    rows, fails = [], {"in_scope": [], "min_sources": [], "min_self_sources": [],
                       "min_confirmed_edges": []}
    for eid, e in sorted(ents.items()):
        mine = by_ent.get(eid, [])
        layers = set(e.get("layers") or [])
        self_n = sum(1 for s in mine if nveco.is_self_source(s["url"], eid))
        # У сущности без собственного издателя проверка на self-источник СНИМАЕТСЯ
        # самим этим фактом: у закона нет пресс-службы. Исключения в коде нет —
        # есть пустой список доменов в реестре, и он читается как факт о мире.
        needs_self = nveco.has_own_publisher(eid)
        checks = {
            "in_scope": bool(layers & scope_layers),
            "min_sources": len(mine) >= min_src,
            "min_self_sources": (self_n >= min_self) if needs_self else True,
            "min_confirmed_edges": deg.get(eid, 0) >= min_edges,
        }
        for k, ok in checks.items():
            if not ok:
                fails[k].append(eid)
        rows.append({"id": eid, "name": e["name"], "sources": len(mine),
                     "self_sources": self_n, "own_publisher": int(needs_self),
                     "edges": deg.get(eid, 0),
                     **{k: int(v) for k, v in checks.items()},
                     "passes": int(all(checks.values()))})
    return {"rows": rows, "fails": fails,
            "passed": sum(r["passes"] for r in rows),
            "failed": sum(1 for r in rows if not r["passes"]),
            "edge_basis": "confirmed" if statuses is not None else "all_edges",
            "enforced": bool(cfg.get("enforce", False))}


def write_membership_report(month: str, report: dict) -> str:
    out = db.RUNS_DIR / month / "_membership"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "report.csv"
    cols = ["id", "name", "sources", "self_sources", "own_publisher", "edges",
            "in_scope", "min_sources", "min_self_sources", "min_confirmed_edges",
            "passes"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(sorted(report["rows"], key=lambda r: (r["passes"], r["id"])))
    return str(path)


# ── снятие с карты ───────────────────────────────────────────────────────────
# Загрузка обязана быть АВТОРИТЕТНОЙ за тот месяц, который грузит: строка, исчезнувшая
# из CSV, обязана исчезнуть из базы. Иначе исправление невозможно опубликовать — id
# ребра выводится из его концов (`source__target__type`), и разворот ориентации не
# правит строку, а ПЕРЕИМЕНОВЫВАЕТ её: 2026-08-23 семь развёрнутых рёбер дали 250 строк
# вместо 243, старая и новая версии одновременно и противореча друг другу.
#
# Но авторитет не абсолютный, а ПОАГЕНТНЫЙ. Месяц, где выдачу дали два агента из
# восьми, — легальный прогон (см. check_agent_outputs в run_nvidia.py), и молчание
# шести остальных не отзывает их строки. Отсюда четыре случая:
#
#   файла нет                      -> агент не работал: не трогаем ничего;
#   файл есть, строк нет           -> агент заявил «у меня пусто»: снимаем всё его;
#   файл есть, часть строк выжила  -> снимаем всё остальное, что числится за ним;
#   файл есть, не выжила ни одна   -> это авария выдачи, а не отзыв: НЕ снимаем.
#
# Последний случай — единственная поблажка, и она не произвольная: агент, у которого
# сдвинулась колонка и отвергнуты все строки, неотличим по результату от агента,
# который не запускался. Стирать по такому сигналу нельзя, но и молчать нельзя —
# случай уходит в warnings прогона.
def _retiring_agents(per_file, fname, survivors):
    """(кто вправе снимать свои строки, у кого выдача пустая при непустом файле)."""
    allowed, broken = [], []
    for (agent, f), rows_in in sorted(per_file.items()):
        if f != fname:
            continue
        (broken if rows_in and not survivors.get(agent) else allowed).append(agent)
    return allowed, broken


def _owned_by(con, table, agents, keep):
    """id строк таблицы, что числятся за этими агентами и не пришли в этом месяце.

    owner_agent IS NULL не снимается никогда: это строка, записанная до появления
    колонки, и приписать её агенту сейчас — значит угадать. Пусть лучше висит видимо,
    чем исчезнет по догадке.
    """
    return [r["id"] for r in con.execute(
        f"SELECT id, owner_agent FROM {table} WHERE owner_agent IS NOT NULL")
        if r["owner_agent"] in agents and r["id"] not in keep]


def _drop_i18n(con, kind, ids):
    """Перевод снятой строки — сирота: показывать его не на чем, а склад он засоряет."""
    if not ids or not con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='i18n_text'").fetchone():
        return
    for oid in ids:
        con.execute("DELETE FROM i18n_text WHERE scope='nveco' AND kind=? AND obj_id=?",
                    (kind, oid))


def _retire_edges(con, agents, keep):
    """Снять рёбра вместе с их источниками и участием в контурах.

    Зависимые строки удаляются ЯВНО, хотя nveco_cycle_edge и связан внешним ключом с
    ON DELETE CASCADE: `PRAGMA foreign_keys` — состояние соединения, а не свойство
    схемы, и молчаливая опора на него означала бы, что один забытый PRAGMA оставляет
    базу с висячими источниками. nveco_source внешнего ключа не имеет вовсе —
    owner_id там свободный текст на две таблицы сразу.
    """
    stale = _owned_by(con, "nveco_edge", agents, keep)
    for eid in stale:
        con.execute("DELETE FROM nveco_cycle_edge WHERE edge_id=?", (eid,))
        con.execute("DELETE FROM nveco_source WHERE owner_kind='edge' AND owner_id=?", (eid,))
        con.execute("DELETE FROM nveco_edge WHERE id=?", (eid,))
    _drop_i18n(con, "edge", stale)
    return stale


def _retire_entities(con, agents, keep):
    """Снять сущности вместе со слоями, факторами, риском и источниками.

    Сущность, на которую ещё ссылается ЧЬЁ-ТО ребро, остаётся: source_id и target_id
    объявлены с ON DELETE CASCADE, и снос такой сущности утащил бы за собой ребро
    агента, который в этом месяце просто не работал, — вместе с его доказательствами.
    Возвращается вторым списком, чтобы это было видно в прогоне, а не только в базе.
    """
    stale, held = [], []
    for eid in _owned_by(con, "nveco_entity", agents, keep):
        used = con.execute("SELECT COUNT(*) c FROM nveco_edge WHERE source_id=? OR target_id=?",
                           (eid, eid)).fetchone()["c"]
        (held if used else stale).append(eid)
    for eid in stale:
        con.execute("UPDATE nveco_tech_node SET owner_id=NULL WHERE owner_id=?", (eid,))
        con.execute("DELETE FROM nveco_source WHERE owner_kind='entity' AND owner_id=?", (eid,))
        con.execute("DELETE FROM nveco_entity_factor WHERE entity_id=?", (eid,))
        con.execute("DELETE FROM nveco_entity_layer WHERE entity_id=?", (eid,))
        con.execute("DELETE FROM nveco_entity_risk WHERE entity_id=?", (eid,))
        con.execute("DELETE FROM nveco_entity WHERE id=?", (eid,))
    _drop_i18n(con, "entity", stale)
    return stale, held


def ingest_month(month: str, scope_id: str = None) -> dict:
    if not nveco.month_ok(month):
        raise ValueError(f"месяц должен быть YYYY-MM, получено '{month}'")
    scope_id = scope_id or nveco.SCOPE_ID
    # Охват обязан быть подмножеством таксономии слоёв. Разойдясь молча, он сузил бы
    # карту на слой, о котором никто не спрашивал.
    unknown_scope = [l for l in nveco.scope_layers() if l not in set(nveco.layer_ids())]
    if unknown_scope:
        raise ValueError(f"config/nveco_scope.yaml называет слои, которых нет в "
                         f"config/nveco_layers.yaml: {', '.join(unknown_scope)}")

    con = nveco.connect()
    # Статусы связей снимаются ДО записи: nveco_score считает их следующей стадией,
    # и после INSERT в базе лежат свежие строки со статусом по умолчанию. Прочитать
    # их там значило бы утверждать, что подтверждённых связей ноль, — на чистой базе
    # это неправда с первого же прогона.
    prev_status = {r["id"]: r["status"] for r in
                   con.execute("SELECT id, status FROM nveco_edge")} or None
    layer_ids = set(nveco.layer_ids())
    sector_idx = nveco.sector_index()
    types = nveco.edge_types()

    month_dir = db.RUNS_DIR / month
    if not month_dir.is_dir():
        raise FileNotFoundError(f"нет директории прогона: {month_dir}")
    agent_dirs = sorted(p for p in month_dir.iterdir()
                        if p.is_dir() and p.name.startswith("nveco-"))

    rejected = {}          # agent -> [ {file,line,reason,row} ]
    per_agent = {}
    # (агент, файл) -> сколько строк в файле БЫЛО. Пустой файл и отсутствующий файл
    # здесь перестают быть одним и тем же: первый — заявление «у меня ничего», второй —
    # молчание. От этого различия зависит, кому позволено снимать строки с карты.
    per_file = {}
    warnings = []
    ents, facts, edges, srcs = {}, {}, {}, []

    def reject(agent, fname, line, reason, row):
        rejected.setdefault(agent, []).append(
            {"file": fname, "line": line, "reason": reason,
             "row": "; ".join(f"{k}={v}" for k, v in row.items() if v)[:400]})
        per_agent[agent]["rejected"] += 1

    # --- сущности
    for adir in agent_dirs:
        agent = adir.name
        per_agent.setdefault(agent, {"rows_in": 0, "rows_kept": 0, "rejected": 0})
        f = adir / "entities.csv"
        if not f.exists():
            continue
        per_file[(agent, "entities.csv")] = 0
        for line, row in _read(f):
            per_agent[agent]["rows_in"] += 1
            per_file[(agent, "entities.csv")] += 1
            clean, errs, warns = _validate_entity(row, layer_ids, sector_idx)
            warnings += [f"{agent}/entities.csv:{line} {w}" for w in warns]
            if errs:
                reject(agent, "entities.csv", line, "; ".join(errs), row)
                continue
            if clean["id"] in ents:
                warnings.append(f"{agent}/entities.csv:{line} сущность '{clean['id']}' "
                                f"уже заявлена другим агентом — объединена")
                for k, v in clean.items():
                    if k == "layers":
                        for l in v:
                            if l not in ents[clean["id"]]["layers"]:
                                ents[clean["id"]]["layers"].append(l)
                    elif not ents[clean["id"]].get(k) and v:
                        ents[clean["id"]][k] = v
            else:
                ents[clean["id"]] = clean
            per_agent[agent]["rows_kept"] += 1
            ents[clean["id"]]["_agent"] = agent

    # --- факторы
    for adir in agent_dirs:
        agent = adir.name
        f = adir / "factors.csv"
        if not f.exists():
            continue
        for line, row in _read(f):
            per_agent[agent]["rows_in"] += 1
            clean, errs, _ = _validate_factors(row)
            if errs:
                reject(agent, "factors.csv", line, "; ".join(errs), row)
                continue
            if clean["entity_id"] not in ents:
                reject(agent, "factors.csv", line,
                       f"факторы для незаявленной сущности '{clean['entity_id']}'", row)
                continue
            facts[clean["entity_id"]] = clean["factors"]
            per_agent[agent]["rows_kept"] += 1

    # --- рёбра
    for adir in agent_dirs:
        agent = adir.name
        per_agent.setdefault(agent, {"rows_in": 0, "rows_kept": 0, "rejected": 0})
        f = adir / "edges.csv"
        if not f.exists():
            continue
        per_file[(agent, "edges.csv")] = 0
        for line, row in _read(f):
            per_agent[agent]["rows_in"] += 1
            per_file[(agent, "edges.csv")] += 1
            clean, errs, warns = _validate_edge(row, types)
            warnings += [f"{agent}/edges.csv:{line} {w}" for w in warns]
            if not errs:
                s, t = clean["source"], clean["target"]
                if s == t:
                    errs.append(f"петля на '{s}'")
                for role, x in (("source", s), ("target", t)):
                    if x not in ents:
                        errs.append(f"{role} '{x}' не заявлен ни в одном entities.csv")
            if errs:
                reject(agent, "edges.csv", line, "; ".join(errs), row)
                continue
            key = nveco.edge_id(clean["source"], clean["target"], clean["type"])
            if key in edges:
                warnings.append(f"{agent}/edges.csv:{line} ребро {key} дублируется "
                                f"— оставлено первое")
            else:
                edges[key] = {**clean, "id": key, "_agent": agent}
            per_agent[agent]["rows_kept"] += 1

    # --- источники
    for adir in agent_dirs:
        agent = adir.name
        f = adir / "sources.csv"
        if not f.exists():
            continue
        for line, row in _read(f):
            per_agent[agent]["rows_in"] += 1
            clean, errs, warns = _validate_source(row)
            warnings += [f"{agent}/sources.csv:{line} {w}" for w in warns]
            if not errs:
                if clean["owner_kind"] == "entity" and clean["owner_key"] not in ents:
                    errs.append(f"источник для незаявленной сущности '{clean['owner_key']}'")
                if clean["owner_kind"] == "edge" and clean["owner_key"] not in edges:
                    errs.append(f"источник для незаявленной связи '{clean['owner_key']}'")
            if errs:
                reject(agent, "sources.csv", line, "; ".join(errs), row)
                continue
            srcs.append(clean)
            per_agent[agent]["rows_kept"] += 1

    # --- железное правило: нет цитаты — нет связи
    with_src = {s["owner_key"] for s in srcs if s["owner_kind"] == "edge"}
    for key in list(edges):
        if key not in with_src:
            e = edges.pop(key)
            reject(e["_agent"], "edges.csv", 0,
                   "нет ни одного источника с дословной цитатой — ребро не пишется",
                   {"edge": key})

    # --- членство. Проверка 1 (охват) действует ВСЕГДА: сущность, не работающая ни
    # в одном слое предмета, — это не про эту карту, и держать её значило бы стереть
    # границу. Проверки 2 и 3 считаются и отчитываются, но отклоняют только когда
    # membership.enforce включён (Фаза 3).
    scope_layers = set(nveco.scope_layers())
    for eid in list(ents):
        e = ents[eid]
        if not (set(e.get("layers") or []) & scope_layers):
            ents.pop(eid)
            reject(e.get("_agent", "?"), "entities.csv", 0,
                   f"не работает ни в одном слое охвата "
                   f"({', '.join(sorted(scope_layers))}) — вне предмета карты",
                   {"id": eid, "name": e["name"]})
            facts.pop(eid, None)
    for key in list(edges):
        e = edges[key]
        if e["source"] not in ents or e["target"] not in ents:
            edges.pop(key)
    srcs = [s for s in srcs
            if (s["owner_kind"] == "entity" and s["owner_key"] in ents)
            or (s["owner_kind"] == "edge" and s["owner_key"] in edges)]

    # --- запись
    for eid, e in ents.items():
        prev = con.execute("SELECT first_seen FROM nveco_entity WHERE id=?", (eid,)).fetchone()
        first_seen = prev["first_seen"] if prev and prev["first_seen"] else month
        con.execute(
            """INSERT INTO nveco_entity (id,name,aliases,type,role,sector,primary_layer,
                 phase,ticker,public_private,geo,founded,revenue_usd_b,one_liner,
                 why_irreplaceable,what_breaks_it,first_seen,last_confirmed,
                 owner_agent,domain)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, aliases=excluded.aliases, type=excluded.type,
                 role=excluded.role, sector=excluded.sector,
                 primary_layer=excluded.primary_layer, phase=excluded.phase,
                 ticker=excluded.ticker, public_private=excluded.public_private,
                 geo=excluded.geo, founded=excluded.founded,
                 revenue_usd_b=excluded.revenue_usd_b, one_liner=excluded.one_liner,
                 why_irreplaceable=excluded.why_irreplaceable,
                 what_breaks_it=excluded.what_breaks_it,
                 last_confirmed=excluded.last_confirmed,
                 owner_agent=excluded.owner_agent,
                 domain=COALESCE(excluded.domain, nveco_entity.domain)""",
            (eid, e["name"], e["aliases"], e["type"], e["role"], e["sector"],
             e["primary_layer"], e["phase"], e["ticker"], e["public_private"], e["geo"],
             e["founded"], e["revenue_usd_b"], e["one_liner"], e["why_irreplaceable"],
             e["what_breaks_it"], first_seen, month, e.get("_agent"),
             (e.get("domain") or "").strip().lower() or None))
        con.execute("DELETE FROM nveco_entity_layer WHERE entity_id=?", (eid,))
        for l in e["layers"]:
            con.execute(
                "INSERT INTO nveco_entity_layer (entity_id,layer_id,is_primary) VALUES (?,?,?)",
                (eid, l, 1 if l == e["primary_layer"] else 0))
        con.execute(
            """INSERT INTO nveco_entity_risk (entity_id,geopolitical,note,export_regime,
                 concentration) VALUES (?,?,?,?,?)
               ON CONFLICT(entity_id) DO UPDATE SET geopolitical=excluded.geopolitical,
                 note=excluded.note, export_regime=excluded.export_regime,
                 concentration=excluded.concentration""",
            (eid, e["geo_risk"], e["geo_risk_note"], e["export_regime"], e["concentration"]))

    for eid, fs in facts.items():
        for factor, (value, why) in fs.items():
            con.execute(
                """INSERT INTO nveco_entity_factor (entity_id,factor,value,why)
                   VALUES (?,?,?,?)
                   ON CONFLICT(entity_id,factor) DO UPDATE SET
                     value=excluded.value, why=excluded.why""",
                (eid, factor, value, why))

    for key, e in edges.items():
        con.execute(
            """INSERT INTO nveco_edge (id,source_id,target_id,type,spine,direction,
                 strength,lock_in_depth,substitutability,is_reversible,risk_level,
                 risk_type,risk_timeline,risk_mitigation,tech_node,formed,strengthened,
                 last_confirmed,note,owner_agent)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 type=excluded.type, spine=excluded.spine, direction=excluded.direction,
                 strength=excluded.strength, lock_in_depth=excluded.lock_in_depth,
                 substitutability=excluded.substitutability,
                 is_reversible=excluded.is_reversible, risk_level=excluded.risk_level,
                 risk_type=excluded.risk_type, risk_timeline=excluded.risk_timeline,
                 risk_mitigation=excluded.risk_mitigation, tech_node=excluded.tech_node,
                 formed=COALESCE(nveco_edge.formed, excluded.formed),
                 strengthened=excluded.strengthened,
                 last_confirmed=excluded.last_confirmed, note=excluded.note,
                 owner_agent=excluded.owner_agent""",
            (key, e["source"], e["target"], e["type"], e["spine"], e["direction"],
             e["strength"], e["lock_in_depth"], e["substitutability"],
             1 if e["is_reversible"] else 0, e["risk_level"], e["risk_type"],
             e["risk_timeline"], e["risk_mitigation"], e["tech_node"], e["formed"],
             e["strengthened"], month, e["note"], e.get("_agent")))

    # `self_of` — id того конца, который издал ссылку. Считается ЗДЕСЬ, а не в
    # score, чтобы правило min_self_sources и статус `bilateral` читали одну и ту же
    # разметку, а не две разные её реконструкции.
    for s in srcs:
        if s["owner_kind"] == "entity":
            ends = [s["owner_key"]]
        else:
            ends = s["owner_key"].split("__")[:2]
        self_of = next((x for x in ends if nveco.is_self_source(s["url"], x)), None)
        con.execute(
            """INSERT OR IGNORE INTO nveco_source (owner_kind,owner_id,tier,type,title,
                 url,published,quote,confidence,self_of) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (s["owner_kind"], s["owner_key"], s["tier"], s["type"], s["title"],
             s["url"], s["published"], s["quote"], s["confidence"], self_of))
        con.execute("UPDATE nveco_source SET self_of=? WHERE owner_kind=? AND "
                    "owner_id=? AND url=? AND quote=?",
                    (self_of, s["owner_kind"], s["owner_key"], s["url"], s["quote"]))

    # Тех-узлы — из конфига, а не из выдачи агента: это словарь, а не находка.
    for t in nveco.load_layers().get("tech_nodes", []) or []:
        owner = t.get("owner") if t.get("owner") in ents else None
        con.execute(
            """INSERT INTO nveco_tech_node (id,label,owner_id,note,importance)
               VALUES (?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET label=excluded.label,
                 owner_id=excluded.owner_id, note=excluded.note,
                 importance=excluded.importance""",
            (t["id"], t["label"], owner, t.get("note"), t.get("importance")))

    # --- снятие с карты: то, что агент этого месяца больше не заявляет
    # Считается по ВЫЖИВШИМ строкам, а не по прошедшим валидацию: ребро, потерявшее
    # цитату, и сущность, выпавшая за два шага, до базы не дошли, и агент, у которого
    # так отпало всё, ничего в этом месяце не подтвердил.
    ent_alive, edge_alive = {}, {}
    for e in ents.values():
        ent_alive[e.get("_agent")] = ent_alive.get(e.get("_agent"), 0) + 1
    for e in edges.values():
        edge_alive[e.get("_agent")] = edge_alive.get(e.get("_agent"), 0) + 1

    may_edges, broken_edges = _retiring_agents(per_file, "edges.csv", edge_alive)
    retired_edges = _retire_edges(con, set(may_edges), set(edges))
    may_ents, broken_ents = _retiring_agents(per_file, "entities.csv", ent_alive)
    retired_ents, held_ents = _retire_entities(con, set(may_ents), set(ents))

    for agent in broken_edges + broken_ents:
        warnings.append(f"{agent}: файл сдан, но не выжила ни одна строка — "
                        f"строки этого агента НЕ сняты с карты (авария выдачи "
                        f"неотличима от отзыва, и стирать по ней нельзя)")
    for eid in held_ents:
        warnings.append(f"сущность '{eid}' больше не заявлена, но на неё ссылается "
                        f"связь другого агента — оставлена на карте")

    for agent, st in per_agent.items():
        con.execute(
            """INSERT INTO nveco_run (month,scope_id,agent,rows_in,rows_kept,rejected)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(month,scope_id,agent) DO UPDATE SET
                 rows_in=excluded.rows_in, rows_kept=excluded.rows_kept,
                 rejected=excluded.rejected""",
            (month, scope_id, agent, st["rows_in"], st["rows_kept"], st["rejected"]))
    # --- членство: считается по ВЫЖИВШИМ строкам и отчитывается всегда
    for key in edges:
        edges[key].setdefault("id", key)
    memb = membership_report(ents, edges, srcs, prev_status)
    memb["path"] = write_membership_report(month, memb)

    con.commit()
    con.close()

    # --- отказы возвращаются агентам
    rej_dir = month_dir / "_rejected"
    # Чистим каталог целиком: файл отказов прошлого прогона, оставшийся лежать рядом с
    # новым, — это ложное задание агенту на строки, которые он уже исправил.
    if rej_dir.is_dir():
        for old_file in rej_dir.glob("nveco-*.csv"):
            old_file.unlink()
    if rejected:
        rej_dir.mkdir(exist_ok=True)
        for agent, rows in rejected.items():
            with (rej_dir / f"{agent}.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["file", "line", "reason", "row"])
                w.writeheader()
                w.writerows(rows)

    return {"agents": len(agent_dirs), "entities": len(ents), "edges": len(edges),
            "sources": len(srcs), "factors": len(facts),
            "rejected": sum(len(v) for v in rejected.values()),
            "rejected_by_agent": {a: len(v) for a, v in rejected.items()},
            "retired_entities": retired_ents, "retired_edges": retired_edges,
            "held_entities": held_ents,
            "broken_agents": sorted(set(broken_edges + broken_ents)),
            "membership": memb,
            "warnings": warnings,
            "rejects_dir": str(rej_dir) if rejected else None}


if __name__ == "__main__":
    s = ingest_month(sys.argv[1] if len(sys.argv) > 1 else nveco.current_month())
    print(f"nveco_ingest: {s['entities']} сущностей, {s['edges']} связей, "
          f"{s['sources']} источников, {s['rejected']} отклонено, "
          f"снято {len(s['retired_entities'])}/{len(s['retired_edges'])}")
    for w in s["warnings"][:30]:
        print("  ", w)
