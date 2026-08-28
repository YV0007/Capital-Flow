"""Сборка сети: семя v2 + достройка v3.

Семя — handoff/nvidia_ecosystem.json — переносится ЦЕЛИКОМ и без изменений: 106
сущностей и 243 связи это первый полный прогон, и переисследовать его нельзя. Правки
ровно три, все механические:

  * `pivotal: true/false` каждой сущности по config/nvnet_pivots.yaml;
  * `hops` пересчитывается от БЛИЖАЙШЕГО пивота, а не от единственного якоря;
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
from .nveco_ingest import (_validate_entity, _validate_factors, _validate_source,
                           WHY_COLUMNS)

CAMEL = {"irreplaceability": "irreplaceability", "lock_in_depth": "lockInDepth",
         "time_to_replace": "timeToReplace", "strategic_control": "strategicControl"}


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


def _status_and_confidence(tiers):
    from .nveco_score import _status_and_confidence as f
    return f(tiers)


def build(month: str) -> dict:
    seed = nvnet.load_seed()
    pivots = [p for p in nvnet.pivot_ids()]
    types = nvnet.edge_types()
    today = date.today().isoformat()

    entities = {e["id"]: dict(e) for e in seed["entities"]}
    edges = {e["id"]: dict(e) for e in seed["edges"]}
    problems, rejects = [], []

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
        for line, row in (_read(f) if f else ()):
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
                "hops": None, "firstSeen": month, "lastConfirmed": month,
                "stale": False, "sources": [],
            }
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
            for line, row in _read(f):
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
            entities[key]["sources"] = rows

    # ── критичность новых сущностей по той же рубрике ─────────────────────────
    for eid, fs in factors_by_ent.items():
        if eid not in entities:
            continue
        vals = {k: v[0] for k, v in fs.items()}
        c = nveco.criticality(vals)
        entities[eid]["criticality"] = c
        entities[eid]["criticalityFactors"] = {CAMEL[k]: vals[k] for k in nveco.FACTORS}
        entities[eid]["criticalityWhy"] = {CAMEL[k]: fs[k][1] for k in nveco.FACTORS}
        for l in entities[eid]["layers"]:
            l["criticality"] = c if l["primary"] else round((c or 0) * 0.5)

    # ── pivotal + правило «≤2 шагов от ЛЮБОГО пивота» ─────────────────────────
    pivot_set = {p for p in pivots if p in entities}
    missing_pivots = [p for p in pivots if p not in entities]
    dist = nvnet.hops_from_pivots(pivot_set, edges.values())
    limit = nvnet.hops_limit()
    dropped = []
    for eid in list(entities):
        h = dist.get(eid)
        entities[eid]["pivotal"] = eid in pivot_set
        entities[eid]["hops"] = h
        if h is None or h > limit:
            dropped.append(eid)
            entities.pop(eid)
    for k in [k for k, v in edges.items()
              if v["source"] not in entities or v["target"] not in entities]:
        edges.pop(k)

    return {"entities": entities, "edges": edges, "seed": seed,
            "newEntities": new_ent, "newEdges": new_edge, "newSources": new_src,
            "details": detail_rows,
            "problems": problems, "rejects": rejects, "dropped": dropped,
            "missingPivots": missing_pivots, "pivots": sorted(pivot_set)}


def persist(month: str, net: dict) -> None:
    """Сохраняет ТОЛЬКО достройку: семя живёт в nveco_* и не дублируется."""
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
                 geo_risk_note,export_regime,concentration)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (eid, e["name"], "|".join(e["aliases"]), e["type"], e["role"], e["sector"],
             e["primaryLayer"], "|".join(l["layer"] for l in e["layers"]), e["phase"],
             e["ticker"], e["publicPrivate"], e["geo"], e["founded"], e["revenueUsdB"],
             e["oneLiner"], e["whyIrreplaceable"], e["whatBreaksIt"],
             e["risk"]["geopolitical"], e["risk"]["note"], e["risk"]["exportRegime"],
             e["risk"]["concentration"]))
    for eid, x in net["edges"].items():
        if eid in seed_edges:
            continue
        con.execute(
            """INSERT OR REPLACE INTO nvnet_edge (id,source_id,target_id,type,spine,
                 direction,strength,lock_in_depth,substitutability,is_reversible,status,
                 confidence,source_tier,confirmed_sources,risk_level,risk_type,
                 risk_timeline,risk_mitigation,tech_node,formed,strengthened,
                 last_confirmed,note,clamped,origin)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (eid, x["source"], x["target"], x["type"], x["spine"], x["direction"],
             x["strength"], x.get("lockInDepth"), x.get("substitutability"),
             1 if x.get("isReversible") else 0, x["status"], x["confidence"],
             x["sourceTier"], x["confirmedSources"], (x["risk"] or {}).get("level"),
             (x["risk"] or {}).get("type"), (x["risk"] or {}).get("timeline"),
             (x["risk"] or {}).get("mitigation"), x.get("techNode"), x.get("formed"),
             x.get("strengthened"), x.get("lastConfirmed"), x.get("note"),
             x.get("clamped"), x.get("origin")))
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
    con.commit()
    con.close()


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else nveco.current_month()
    n = build(m)
    print(f"сеть: {len(n['entities'])} сущностей, {len(n['edges'])} связей; "
          f"новых {n['newEntities']}/{n['newEdges']}; отклонено {len(n['rejects'])}")
