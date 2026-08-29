"""Разложить `dossier.json` в файлы, которые читает конвейер.

Досье — один объект на сущность: описание, факторы, связи, источники и кандидаты
лежат вместе, потому что исследуются вместе. Конвейер читает четыре CSV, потому что
валидирует их построчно и умеет отвергать одну строку, не теряя остальные. Этот
скрипт — мост между двумя формами, и он намеренно тупой: раскладывает, проверяет
форму, называет ошибку по имени и НИЧЕГО не додумывает.

Что куда:

    runs/<месяц>/nveco-dossier-NN/dossier.json
      ├─ factors.csv      четыре фактора с обоснованиями  ─┐
      ├─ edges.csv        новые связи                      ├─ nveco_ingest
      ├─ sources.csv      источники профиля и связей       │  (run_nvidia.py)
      ├─ translations.csv английская сторона всей прозы   ─┘
      └─ ../nvnet-dossier/descriptions.csv   описание {ru,en}  ─ nvnet_ingest
                          candidates.csv → ../_queue/candidates.csv

Почему `entities.csv` не пишется. Досье этого прогона правит ПРОФИЛЬ узла, а не его
паспорт: слой, роль, тикер и география уже стоят и не оспариваются. Строка entities.csv
обязана нести весь паспорт целиком, и переписывать её ради одного поля значило бы
перекладывать владение строкой на досье без причины. Когда досье действительно
расходится с паспортом — оно пишет `profile`, и тогда строка появляется.

Usage: python tools/dossier_split.py <YYYY-MM> [--dir nveco-dossier-01] [--check]
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db, nveco, nveco_feedback  # noqa: E402

FACTORS = list(nveco.FACTORS)
WHY = {"irreplaceability": "why_irreplaceability", "lock_in_depth": "why_lock_in",
       "time_to_replace": "why_time", "concentration": "why_concentration"}
I18N_FACTOR_FIELD = dict(WHY)

SOURCE_COLS = ["owner_kind", "owner_key", "tier", "type", "title", "url",
               "published", "quote", "confidence", "counter"]
FACTOR_COLS = ["entity_id"] + FACTORS + [WHY[f] for f in FACTORS]
EDGE_COLS = ["source", "target", "type", "direction", "strength", "lock_in_depth",
             "substitutability", "is_reversible", "risk_level", "risk_type",
             "risk_timeline", "risk_mitigation", "tech_node", "formed",
             "strengthened", "note"]
ENTITY_COLS = ["id", "name", "aliases", "type", "role", "sector", "primary_layer",
               "domain", "layers", "phase", "ticker", "public_private", "geo",
               "founded", "revenue_usd_b", "one_liner", "why_irreplaceable",
               "what_breaks_it", "geo_risk", "geo_risk_note", "export_regime",
               "concentration"]


def _bi(v, where, errs, field):
    """Пара {ru, en}. Пустая сторона — это брак, а не пропуск."""
    if v is None:
        return None, None
    if not isinstance(v, dict) or not (v.get("ru") or "").strip() \
            or not (v.get("en") or "").strip():
        errs.append(f"{where}: {field} должно быть парой {{ru, en}} с непустыми "
                    f"сторонами")
        return None, None
    return v["ru"].strip(), v["en"].strip()


def _source_row(src, kind, key, where, errs):
    for f in ("url", "quote", "type"):
        if not (src.get(f) or "").strip():
            errs.append(f"{where}: у источника нет {f}")
            return None
    if nveco.word_count(src["quote"]) > nveco.MAX_QUOTE_WORDS:
        errs.append(f"{where}: цитата {nveco.word_count(src['quote'])} слов при "
                    f"пределе {nveco.MAX_QUOTE_WORDS}: «{src['quote'][:60]}…»")
        return None
    return {"owner_kind": kind, "owner_key": key,
            # ТИР ПУСТ НАМЕРЕННО: его ставит движок по реестру издателей относительно
            # предмета. Досье, пишущее тир, тем самым назначало бы себе привилегию.
            "tier": "", "type": src["type"].strip(),
            "title": (src.get("title") or "").strip(),
            "url": src["url"].strip(), "published": (src.get("published") or "").strip(),
            "quote": src["quote"].strip(), "confidence": "",
            "counter": "true" if src.get("counter") else "false"}


def split_one(path: Path, month: str) -> dict:
    """Один dossier.json -> строки для CSV. Ничего не пишет."""
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise SystemExit(f"{path}: dossier.json — массив объектов, по одному на сущность")
    out = {"entities": [], "factors": [], "edges": [], "sources": [],
           "descriptions": [], "i18n": [], "candidates": [], "errors": [],
           "covered": [], "counters": 0, "confirms": 0}

    for d in data:
        eid = (d.get("id") or "").strip()
        where = f"{path.parent.name}/{eid or '?'}"
        if not eid:
            out["errors"].append(f"{path.name}: объект без id")
            continue

        # --- описание
        ru, en = _bi(d.get("description"), where, out["errors"], "description")
        if ru:
            out["descriptions"].append({"entity_id": eid, "description_ru": ru,
                                        "description_en": en})

        # --- факторы
        fs = d.get("factors") or {}
        missing = [f for f in FACTORS if f not in fs]
        if missing:
            out["errors"].append(f"{where}: нет факторов {', '.join(missing)} — "
                                 f"досье даёт все четыре")
        row = {"entity_id": eid}
        for f in FACTORS:
            item = fs.get(f) or {}
            v = item.get("value")
            wru, wen = _bi(item.get("why"), where, out["errors"], f"factors.{f}.why")
            if v is None or wru is None:
                continue
            row[f] = v
            row[WHY[f]] = wru
            out["i18n"].append({"kind": "entity", "id": eid,
                                "field": I18N_FACTOR_FIELD[f], "lang": "en",
                                "text": wen})
        out["factors"].append(row)

        # --- источники профиля
        psrc = d.get("profile_sources") or []
        rows = [r for r in (_source_row(s, "entity", eid, where, out["errors"])
                            for s in psrc) if r]
        out["sources"] += rows
        if len(rows) < 3:
            out["errors"].append(f"{where}: {len(rows)} источников профиля, нужно ≥3")
        if nveco.has_own_publisher(eid) and not any(
                nveco.is_self_source(r["url"], eid) for r in rows):
            out["errors"].append(
                f"{where}: ни один источник профиля не издан самой сущностью — "
                f"это упоминание, а не досье (домены: "
                f"{', '.join(nveco.entity_domains(eid)) or '—'})")

        # --- профиль, если досье расходится с паспортом
        prof = d.get("profile")
        if prof:
            erow = {c: "" for c in ENTITY_COLS}
            erow.update({k: v for k, v in prof.items() if k in ENTITY_COLS
                         and not isinstance(v, dict)})
            erow["id"] = eid
            for field in ("one_liner", "why_irreplaceable", "what_breaks_it",
                          "geo_risk_note"):
                if field in prof:
                    r_, e_ = _bi(prof[field], where, out["errors"], f"profile.{field}")
                    if r_:
                        erow[field] = r_
                        out["i18n"].append({"kind": "entity", "id": eid, "field": field,
                                            "lang": "en", "text": e_})
            out["entities"].append(erow)

        # --- связи
        for x in d.get("edges") or []:
            stance = (x.get("stance") or "confirms").strip()
            if stance not in ("confirms", "counters"):
                out["errors"].append(f"{where}: stance '{stance}' — только confirms "
                                     f"или counters")
                continue
            key = (x.get("id") or "").strip()
            if not key:
                for f in ("source", "target", "type"):
                    if not (x.get(f) or "").strip():
                        out["errors"].append(f"{where}: у новой связи нет {f}")
                        break
                else:
                    key = nveco.edge_id(x["source"].strip(), x["target"].strip(),
                                        x["type"].strip())
                    erow = {c: "" for c in EDGE_COLS}
                    for c in EDGE_COLS:
                        if c in x and not isinstance(x[c], dict):
                            erow[c] = x[c]
                    erow["source"], erow["target"] = x["source"], x["target"]
                    # `risk_mitigation` — тоже проза выдачи, и валидатор контракта
                    # роняет выпуск при пустой английской стороне. Пара {ru, en}
                    # обязательна ровно так же, как у `note`.
                    if x.get("risk_mitigation") is not None:
                        mru, men = _bi(x.get("risk_mitigation"), where, out["errors"],
                                       f"edges[{key}].risk_mitigation")
                        if mru:
                            erow["risk_mitigation"] = mru
                            out["i18n"].append({"kind": "edge", "id": key,
                                                "field": "risk_mitigation", "lang": "en",
                                                "text": men})
                    nru, nen = _bi(x.get("note"), where, out["errors"],
                                   f"edges[{key}].note")
                    if nru:
                        erow["note"] = nru
                        out["i18n"].append({"kind": "edge", "id": key, "field": "note",
                                            "lang": "en", "text": nen})
                    out["edges"].append(erow)
            if not key:
                continue
            srcs = x.get("sources") or []
            if not srcs:
                out["errors"].append(f"{where}: связь {key} без источника — "
                                     f"нет цитаты, нет связи")
            for s in srcs:
                r = _source_row({**s, "counter": stance == "counters"},
                                "edge", key, where, out["errors"])
                if r:
                    out["sources"].append(r)
            out["counters" if stance == "counters" else "confirms"] += 1

        # --- отметка о покрытии. Пишется здесь, а не при загрузке, потому что
        # «досье отработано» — это факт о работе агента, а не о том, сколько строк
        # из неё пережило валидацию. Узел, чьё досье не нашло ничего, покрыт: его
        # смотрели, и это ровно то, что нужно знать членству, чтобы отличить
        # «нечего предъявить» от «до него не дошла очередь».
        my_srcs = [r for r in rows if r["owner_key"] == eid]
        out["covered"].append({
            "entity_id": eid, "batch": path.parent.name,
            "sources": len(my_srcs),
            "self_srcs": sum(1 for r in my_srcs
                             if nveco.is_self_source(r["url"], eid)),
            "edges": len(d.get("edges") or [])})

        # --- кандидаты
        for c in d.get("candidates") or []:
            out["candidates"].append({
                "named_by": eid, "name": (c.get("name") or "").strip(),
                "why": (c.get("why") or "").strip(),
                "url": (c.get("url") or "").strip(),
                "quote": (c.get("quote") or "").strip(),
                "month": month, "batch": path.parent.name})
    return out


def _write(path: Path, cols: list, rows: list):
    if not rows:
        return 0
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    return len(rows)


def run(month: str, only: str = None, check: bool = False) -> dict:
    base = db.RUNS_DIR / month
    dirs = sorted(p for p in base.iterdir()
                  if p.is_dir() and p.name.startswith("nveco-dossier")
                  and (only is None or p.name == only)) if base.is_dir() else []
    stats, all_candidates, errors, covered = [], [], [], []
    for d in dirs:
        f = d / "dossier.json"
        if not f.exists():
            continue
        o = split_one(f, month)
        errors += o["errors"]
        if not check:
            _write(d / "factors.csv", FACTOR_COLS, o["factors"])
            _write(d / "edges.csv", EDGE_COLS, o["edges"])
            _write(d / "sources.csv", SOURCE_COLS, o["sources"])
            _write(d / "translations.csv", ["kind", "id", "field", "lang", "text"],
                   o["i18n"])
            if o["entities"]:
                _write(d / "entities.csv", ENTITY_COLS, o["entities"])
            nd = base / "nvnet-dossier"
            nd.mkdir(parents=True, exist_ok=True)
            prev = []
            dp = nd / "descriptions.csv"
            if dp.exists():
                with dp.open(newline="", encoding="utf-8") as fh:
                    prev = [r for r in csv.DictReader(fh)
                            if r["entity_id"] not in {x["entity_id"]
                                                      for x in o["descriptions"]}]
            _write(dp, ["entity_id", "description_ru", "description_en"],
                   prev + o["descriptions"])
        all_candidates += o["candidates"]
        covered += o["covered"]
        stats.append({"dir": d.name, "factors": len(o["factors"]),
                      "edges": len(o["edges"]), "sources": len(o["sources"]),
                      "descriptions": len(o["descriptions"]),
                      "confirms": o["confirms"], "counters": o["counters"],
                      "candidates": len(o["candidates"]),
                      "errors": len(o["errors"])})
    queued = {}
    if all_candidates and not check:
        q = base / "_queue"
        q.mkdir(parents=True, exist_ok=True)
        _write(q / "candidates.csv",
               ["named_by", "name", "why", "url", "quote", "month", "batch"],
               all_candidates)
        # CSV перезаписывается каждым прогоном, поэтому нерешённый кандидат исчезал
        # бы вместе с месяцем, который его назвал. Очередь живёт в базе; CSV остаётся
        # человеку. Разбор очереди — tools/queue_review.py.
        con = nveco.connect()
        queued = nveco_feedback.record_candidates(con, month, all_candidates)
        queued["on_map"] = nveco_feedback.mark_on_map(con, month)
        con.commit()
        con.close()
    if covered and not check:
        con = nveco.connect()
        tiers = {r["entity_id"]: r["rota_tier"] for r in
                 con.execute("SELECT entity_id, rota_tier FROM nvnet_integration")} \
            if con.execute("SELECT name FROM sqlite_master WHERE type='table' AND "
                           "name='nvnet_integration'").fetchone() else {}
        for c in covered:
            con.execute("""INSERT INTO nveco_dossier_run
                             (entity_id, month, batch, tier, sources, self_srcs, edges)
                           VALUES (?,?,?,?,?,?,?)
                           ON CONFLICT(entity_id, month) DO UPDATE SET
                             batch=excluded.batch, tier=excluded.tier,
                             sources=excluded.sources, self_srcs=excluded.self_srcs,
                             edges=excluded.edges""",
                        (c["entity_id"], month, c["batch"], tiers.get(c["entity_id"]),
                         c["sources"], c["self_srcs"], c["edges"]))
        con.commit()
        con.close()
    return {"batches": stats, "errors": errors, "candidates": len(all_candidates),
            "queue": queued, "covered": len(covered)}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    month = args[0] if args else nveco.current_month()
    only = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--dir=")), None)
    out = run(month, only, check="--check" in sys.argv)
    for s in out["batches"]:
        print(f"{s['dir']}: {s['factors']} факторов, {s['edges']} новых связей, "
              f"{s['sources']} источников, {s['descriptions']} описаний, "
              f"подтверждений {s['confirms']}, опровержений {s['counters']}, "
              f"кандидатов {s['candidates']}"
              + (f"  ОШИБОК {s['errors']}" if s["errors"] else ""))
    for e in out["errors"]:
        print("  ОШИБКА", e)
    print(f"кандидатов всего: {out['candidates']}; досье отработано у "
          f"{out.get('covered', 0)} узлов")
    q = out.get("queue") or {}
    if q:
        print(f"очередь в базе: новых {q.get('new', 0)}, повторно названо "
              f"{q.get('repeated', 0)}, уже на карте {len(q.get('on_map') or [])}")
        for name, eid in (q.get("on_map") or []):
            print(f"  уже на карте: {name} -> {eid}")
    sys.exit(1 if out["errors"] else 0)
