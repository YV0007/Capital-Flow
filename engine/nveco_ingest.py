"""Загрузка выдач агентов: четыре CSV -> валидация -> резолвинг -> дедуп -> SQLite.

Читает runs/<YYYY-MM>/nveco-*/{entities,factors,edges,sources}.csv, проверяет каждую
строку против ЗАМОРОЖЕННЫХ конфигов (слой существует? тип связи существует? фактор в
0..100? цитата не длиннее 15 слов?), разрешает имена в постоянные id через общий
config/aliases.yaml и грузит в nveco_*.

Три вещи, которые модуль отказывается делать:
  * записать ребро без источника с дословной цитатой;
  * записать сущность дальше двух шагов от якоря (последний проход);
  * записать вычисляемое поле со слов агента — spine, criticality, status, gravity
    считает nveco_score, и попытка агента их прислать игнорируется.

Отвергнутые строки не молчат: пишутся в runs/<month>/_rejected/<agent>.csv с причиной
и считаются в nveco_run. Это то, что следующий месяц вернёт агентам.

Идемпотентно: ключ — постоянный id, повторный прогон обновляет на месте.
"""

import csv
import sys
from collections import deque

from . import db, nveco
from .ingest import is_search_url

ENTITY_COLUMNS = ["id", "name", "aliases", "type", "role", "sector", "primary_layer",
                  "layers", "phase", "ticker", "public_private", "geo", "founded",
                  "revenue_usd_b", "one_liner", "why_irreplaceable", "what_breaks_it",
                  "geo_risk", "geo_risk_note", "export_regime", "concentration"]
FACTOR_COLUMNS = ["entity_id", "irreplaceability", "lock_in_depth", "time_to_replace",
                  "strategic_control", "why_irreplaceability", "why_lock_in",
                  "why_time", "why_control"]
EDGE_COLUMNS = ["source", "target", "type", "direction", "strength", "lock_in_depth",
                "substitutability", "is_reversible", "risk_level", "risk_type",
                "risk_timeline", "risk_mitigation", "tech_node", "formed",
                "strengthened", "note"]
SOURCE_COLUMNS = ["owner_kind", "owner_key", "tier", "type", "title", "url",
                  "published", "quote", "confidence"]

WHY_COLUMNS = {"irreplaceability": "why_irreplaceability", "lock_in_depth": "why_lock_in",
               "time_to_replace": "why_time", "strategic_control": "why_control"}


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
        "ticker": _s(row, "ticker") or None, "public_private": pp,
        "geo": _s(row, "geo") or None, "founded": _s(row, "founded") or None,
        "revenue_usd_b": rev, "one_liner": _s(row, "one_liner") or None,
        "why_irreplaceable": _s(row, "why_irreplaceable") or None,
        "what_breaks_it": _s(row, "what_breaks_it") or None,
        "geo_risk": geo_risk, "geo_risk_note": _s(row, "geo_risk_note") or None,
        "export_regime": _s(row, "export_regime") or None, "concentration": conc,
    }, [], warnings


def _validate_factors(row):
    errors = []
    eid = _s(row, "entity_id")
    if not eid:
        return None, ["нет entity_id"], []
    out = {"entity_id": eid, "factors": {}}
    for f in nveco.FACTORS:
        v, err = _int(row.get(f), 0, 100)
        if err:
            errors.append(f"{f}: {err} (нужны все четыре фактора 0..100)")
        why = _s(row, WHY_COLUMNS[f])
        _limit(errors, WHY_COLUMNS[f], why, nveco.TEXT_LIMITS["why"])
        if not why:
            errors.append(f"{WHY_COLUMNS[f]}: пусто — оценка без обоснования не принимается")
        out["factors"][f] = (v, why)
    return (None, errors, []) if errors else (out, [], [])


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

    # Тир — свойство источника, а не мнение агента.
    if url and tier:
        expect, _ = nveco.domain_tier(url)
        if expect and expect != tier:
            warnings.append(f"тир {tier} заявлен для домена, у которого по "
                            f"config/sources.yaml тир {expect}")

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


def _hops_from_anchor(anchor_id, edges):
    """Кратчайшее расстояние до якоря по НЕОРИЕНТИРОВАННОМУ графу связей.

    Ненаправленно намеренно: «поставляет NVIDIA» и «покупает у NVIDIA» одинаково
    делают сущность частью орбиты. Направление важно для смысла ребра, но не для
    вопроса «входит ли эта компания в экосистему».
    """
    adj = {}
    for e in edges:
        adj.setdefault(e["source"], set()).add(e["target"])
        adj.setdefault(e["target"], set()).add(e["source"])
    dist = {anchor_id: 0}
    q = deque([anchor_id])
    while q:
        cur = q.popleft()
        for nxt in adj.get(cur, ()):
            if nxt not in dist:
                dist[nxt] = dist[cur] + 1
                q.append(nxt)
    return dist


def ingest_month(month: str, anchor: str = None) -> dict:
    if not nveco.month_ok(month):
        raise ValueError(f"месяц должен быть YYYY-MM, получено '{month}'")
    acfg = nveco.anchor_cfg(anchor)
    anchor_id, max_hops = acfg["id"], int(acfg.get("hops", 2))

    con = nveco.connect()
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
        for line, row in _read(f):
            per_agent[agent]["rows_in"] += 1
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
        for line, row in _read(f):
            per_agent[agent]["rows_in"] += 1
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

    # --- правило двух шагов: всё, до чего от якоря дальше, в карту не входит
    dist = _hops_from_anchor(anchor_id, edges.values())
    for eid in list(ents):
        h = dist.get(eid)
        if h is None or h > max_hops:
            e = ents.pop(eid)
            reject(e.get("_agent", "?"), "entities.csv", 0,
                   f"до якоря '{anchor_id}' {'нет пути' if h is None else str(h) + ' шага'} "
                   f"при пределе {max_hops} — вне орбиты",
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
                 why_irreplaceable,what_breaks_it,hops,first_seen,last_confirmed)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, aliases=excluded.aliases, type=excluded.type,
                 role=excluded.role, sector=excluded.sector,
                 primary_layer=excluded.primary_layer, phase=excluded.phase,
                 ticker=excluded.ticker, public_private=excluded.public_private,
                 geo=excluded.geo, founded=excluded.founded,
                 revenue_usd_b=excluded.revenue_usd_b, one_liner=excluded.one_liner,
                 why_irreplaceable=excluded.why_irreplaceable,
                 what_breaks_it=excluded.what_breaks_it, hops=excluded.hops,
                 last_confirmed=excluded.last_confirmed""",
            (eid, e["name"], e["aliases"], e["type"], e["role"], e["sector"],
             e["primary_layer"], e["phase"], e["ticker"], e["public_private"], e["geo"],
             e["founded"], e["revenue_usd_b"], e["one_liner"], e["why_irreplaceable"],
             e["what_breaks_it"], dist.get(eid), first_seen, month))
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
                 last_confirmed,note)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                 type=excluded.type, spine=excluded.spine, direction=excluded.direction,
                 strength=excluded.strength, lock_in_depth=excluded.lock_in_depth,
                 substitutability=excluded.substitutability,
                 is_reversible=excluded.is_reversible, risk_level=excluded.risk_level,
                 risk_type=excluded.risk_type, risk_timeline=excluded.risk_timeline,
                 risk_mitigation=excluded.risk_mitigation, tech_node=excluded.tech_node,
                 formed=COALESCE(nveco_edge.formed, excluded.formed),
                 strengthened=excluded.strengthened,
                 last_confirmed=excluded.last_confirmed, note=excluded.note""",
            (key, e["source"], e["target"], e["type"], e["spine"], e["direction"],
             e["strength"], e["lock_in_depth"], e["substitutability"],
             1 if e["is_reversible"] else 0, e["risk_level"], e["risk_type"],
             e["risk_timeline"], e["risk_mitigation"], e["tech_node"], e["formed"],
             e["strengthened"], month, e["note"]))

    for s in srcs:
        con.execute(
            """INSERT OR IGNORE INTO nveco_source (owner_kind,owner_id,tier,type,title,
                 url,published,quote,confidence) VALUES (?,?,?,?,?,?,?,?,?)""",
            (s["owner_kind"], s["owner_key"], s["tier"], s["type"], s["title"],
             s["url"], s["published"], s["quote"], s["confidence"]))

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

    for agent, st in per_agent.items():
        con.execute(
            """INSERT INTO nveco_run (month,anchor,agent,rows_in,rows_kept,rejected)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(month,anchor,agent) DO UPDATE SET
                 rows_in=excluded.rows_in, rows_kept=excluded.rows_kept,
                 rejected=excluded.rejected""",
            (month, anchor_id, agent, st["rows_in"], st["rows_kept"], st["rejected"]))
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
            "warnings": warnings,
            "rejects_dir": str(rej_dir) if rejected else None}


if __name__ == "__main__":
    s = ingest_month(sys.argv[1] if len(sys.argv) > 1 else nveco.current_month())
    print(f"nveco_ingest: {s['entities']} сущностей, {s['edges']} связей, "
          f"{s['sources']} источников, {s['rejected']} отклонено")
    for w in s["warnings"][:30]:
        print("  ", w)
