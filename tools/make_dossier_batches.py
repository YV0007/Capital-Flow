"""Пакеты для поузлового исследования: кого брать в этом месяце и что о нём уже известно.

Замыкает ту же петлю обратной связи, что `tools/make_research_batches.py` делает для
недельного конвейера, но единица здесь другая. Там единица — класс аллокаторов и его
watchlist; здесь — ОДИН УЗЕЛ, сделанный как следует. Соответственно и контекстный пакет
собирается на узел, а не на класс.

Что кладётся в пакет каждому узлу:

  1. **ЧТО УЖЕ ЗНАЕМ** — существующий профиль, все его связи с обоих концов, все его
     источники с тирами и с пометкой «чьё это слово». Отсюда исследователь видит
     главное: где профиль стоит на чужой отчётности и какие связи заявлены только
     одним концом.
  2. **ЧТО СВЕРЯТЬ** — связи со статусом `single`, где ВТОРОЙ конец молчит. Это самая
     дешёвая работа пакета: подтверждение с другой стороны поднимает связь до
     `bilateral`, и искать для этого новую связь не нужно.
  3. **ЧТО ОТКЛОНИЛИ В ПРОШЛЫЙ РАЗ** — строки РЕЕСТРА отказов (`nveco_rejection`) про
     этот узел, с причиной и с числом прогонов, сколько отказ уже повторялся. Плюс,
     ОТДЕЛЬНЫМ списком в каждом пакете, — отказы, чей предмет на карту не попал
     вовсе. Второй список Фаза 2 завела потому, что первого не хватало: пакет
     собирается обходом сущностей базы, а отклонённой сущности в базе нет по
     определению, и её отказ не мог попасть ни в один пакет. Ровно в этой щели
     просидел `Carl Zeiss SMT`.
  4. **ЧТО ИСКАТЬ** — задания охоты за пропущенными связями (`nveco_gap`): узел сам
     раскрыл контрагента, не назвав его, либо таксономия обещает ребро, которого у
     него нет ни с кем. Это единственный раздел пакета, который говорит агенту о
     том, чего в карте НЕТ, — остальные описывают то, что есть.
  5. **ЧЕГО НЕ ХВАТАЕТ ПО ЧЛЕНСТВУ** — какие из трёх проверок узел сегодня не проходит
     (`runs/<месяц>/_membership/report.csv`). Это прямое задание: «нужен ещё один
     собственный источник» лучше, чем «исследуй получше».

Ярус берётся из `nvnet_integration` — таблицы, которую пишет `nvnet_handoff` каждым
прогоном. Ядро (топ-30) исследуется ежемесячно, средний ярус — ежеквартально, хвост —
по триггеру. Ротацию включает Фаза 2; здесь ярус только читается, чтобы пакетчик уже
сегодня собирал то, что ротация закажет завтра.

Usage:
  python tools/make_dossier_batches.py <YYYY-MM> [--tier core|mid|tail|all|due]
                                       [--size 8] [--ids a,b,c] [--start 1]

`--tier=due` — то, что заказывает РОТАЦИЯ на этот месяц: ядро ежемесячно, средний
ярус ежеквартально, хвост по триггеру или устарелости, с причиной на каждого узла.
Что не влезло в месячный бюджет, печатается отдельной строкой: тихая обрезка читается
как «покрыли всё» там, где покрыто сорок из ста.
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db, nveco, nveco_feedback, nveco_gaps  # noqa: E402

BATCH_SIZE = 8
DOSSIER_DIR = "nveco-dossier-{:02d}"


def _months_between(a: str, b: str) -> int:
    """Сколько месяцев прошло от a до b. Оба — 'YYYY-MM'."""
    ay, am = int(a[:4]), int(a[5:7])
    by, bm = int(b[:4]), int(b[5:7])
    return (by - ay) * 12 + (bm - am)


def _due(con, month: str, tiers: dict) -> list:
    """Кого ротация заказывает в ЭТОМ месяце, с причиной на каждого.

    Три правила яруса, и ни одно не про «дошли руки»:

      ядро          — каждый месяц;
      средний ярус  — раз в квартал;
      хвост         — по триггеру (новая связь коснулась узла после его последнего
                      досье) либо по устарелости (полгода без подтверждения).

    Узел, которого не исследовали ни разу, просрочен по определению: у него нет
    даты, от которой каденцию можно отсчитать. Именно эти узлы и составляют долг
    кампании, поэтому они идут первыми — внутри яруса по рангу ротации.
    """
    rot = nveco.rotation_cfg()
    cadence = {"core": rot["core_cadence_months"], "mid": rot["mid_cadence_months"]}
    last = {}
    for r in con.execute("SELECT entity_id, MAX(month) m FROM nveco_dossier_run "
                         "GROUP BY entity_id"):
        last[r["entity_id"]] = r["m"]
    # Триггер хвоста: связь, ПОДТВЕРЖДЁННАЯ позже последнего досье узла. У ребра нет
    # колонки «когда завелось» — есть `last_confirmed`, месяц последнего прогона, в
    # котором его заявили. Для триггера этого достаточно и даже честнее: вопрос
    # хвоста — «изменилось ли что-то вокруг узла с тех пор, как мы его смотрели», а
    # не «завелась ли строка ровно тогда-то».
    touched = {}
    for r in con.execute("SELECT source_id, target_id, last_confirmed FROM nveco_edge"):
        when = r["last_confirmed"]
        if not when:
            continue
        when = when[:7]
        for side in (r["source_id"], r["target_id"]):
            if side not in touched or when > touched[side]:
                touched[side] = when

    out = []
    for eid, t in tiers.items():
        tier, rank = t["tier"], t["rota_rank"] or t["rank"] or 999
        seen = last.get(eid)
        if not seen:
            out.append((rank, eid, tier, "досье не отрабатывалось ни разу"))
            continue
        age = _months_between(seen, month)
        if tier in cadence:
            if age >= cadence[tier]:
                out.append((rank, eid, tier,
                            f"каденция яруса {cadence[tier]} мес., прошло {age}"))
            continue
        if age >= rot["tail_stale_months"]:
            out.append((rank, eid, tier,
                        f"хвост: {age} мес. без подтверждения при пороге "
                        f"{rot['tail_stale_months']}"))
        elif touched.get(eid) and touched[eid] > seen:
            out.append((rank, eid, tier,
                        f"хвост по триггеру: связь заведена в {touched[eid]}, "
                        f"досье от {seen}"))
    out.sort()
    return out


def _tiers(con) -> dict:
    """{id: (ярус, ранг, integration)} из последнего прогона сети."""
    has = con.execute("SELECT name FROM sqlite_master WHERE type='table' "
                      "AND name='nvnet_integration'").fetchone()
    if not has:
        return {}
    return {r["entity_id"]: {"tier": r["rota_tier"], "rank": r["rank"],
                             "rota_rank": r["rota_rank"], "crit_rank": r["crit_rank"],
                             "rota_basis": r["rota_basis"],
                             "integration": r["score"], "core": bool(r["core"])}
            for r in con.execute("SELECT * FROM nvnet_integration")}


def _membership(month: str) -> dict:
    path = db.RUNS_DIR / month / "_membership" / "report.csv"
    if not path.exists():
        return {}
    out = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["id"]] = {k: row[k] for k in
                              ("sources", "self_sources", "own_publisher", "edges",
                               "in_scope", "min_sources", "min_self_sources",
                               "min_confirmed_edges", "passes")}
    return out


def _rejected(con, ids) -> dict:
    """Отказы, привязанные к узлам пакета, — из РЕЕСТРА, а не из CSV месяца.

    Прежняя версия читала `runs/<месяц>/_rejected/*.csv` и раскладывала строки по
    пробельным токенам. Она не работала по двум причинам сразу: файл живёт один
    прогон (ingest чистит каталог перед записью), а разложение по токенам всё равно
    ничего не давало отклонённой СУЩНОСТИ — её нет в базе, значит нет и пакета, в
    который строку можно положить. Реестр помнит отказ, пока он не решён, и держит
    предмет отказа отдельной колонкой.
    """
    return nveco_feedback.rejections_for(con, ids)


def _entity_pack(con, eid: str, memb: dict, rejects: dict, tier: dict) -> dict:
    e = con.execute("SELECT * FROM nveco_entity WHERE id=?", (eid,)).fetchone()
    if not e:
        return None
    layers = [r["layer_id"] for r in con.execute(
        "SELECT layer_id FROM nveco_entity_layer WHERE entity_id=? "
        "ORDER BY is_primary DESC", (eid,))]
    factors = {r["factor"]: {"value": r["value"], "why": r["why"]} for r in con.execute(
        "SELECT factor, value, why FROM nveco_entity_factor WHERE entity_id=?", (eid,))}
    sources = [{"tier": r["tier"], "url": r["url"], "quote": r["quote"],
                "published": r["published"], "self": r["self_of"],
                "alive": bool(r["alive"])}
               for r in con.execute("SELECT * FROM nveco_source WHERE owner_kind='entity' "
                                    "AND owner_id=? ORDER BY tier", (eid,))]
    edges, to_reconcile = [], []
    for r in con.execute("SELECT * FROM nveco_edge WHERE source_id=? OR target_id=? "
                         "ORDER BY id", (eid, eid)):
        other = r["target_id"] if r["source_id"] == eid else r["source_id"]
        ev = [{"tier": s["tier"], "url": s["url"], "quote": s["quote"],
               "self": s["self_of"], "counter": bool(s["counter"])}
              for s in con.execute("SELECT * FROM nveco_source WHERE owner_kind='edge' "
                                   "AND owner_id=? ORDER BY tier", (r["id"],))]
        item = {"id": r["id"], "source": r["source_id"], "target": r["target_id"],
                "type": r["type"], "direction": r["direction"],
                "role": "вверх по стеку" if r["target_id"] == eid else "вниз по стеку",
                "counterparty": other, "status": r["status"],
                "sidedness": r["sidedness"],
                "claimed_by": [x for x in (r["claimed_by"] or "").split("|") if x],
                "note": r["note"], "evidence": ev}
        edges.append(item)
        # Связь, которую заявил только один конец, — самая дешёвая работа пакета:
        # цитата со второй стороны поднимает её до `bilateral` без новых находок.
        if r["sidedness"] != "bilateral" and eid not in item["claimed_by"]:
            to_reconcile.append({"edge": r["id"], "counterparty": other,
                                 "type": r["type"],
                                 "нужна цитата": f"документ {eid}, где названа связь "
                                                 f"с {other}"})
    m = memb.get(eid, {})
    gaps = [k for k in ("in_scope", "min_sources", "min_self_sources",
                        "min_confirmed_edges") if m.get(k) == "0"]
    return {
        "id": eid, "name": e["name"], "type": e["type"], "role": e["role"],
        "layers": layers, "primary_layer": e["primary_layer"],
        "domains": nveco.entity_domains(eid), "cik": nveco.entity_cik(eid),
        "own_publisher": nveco.has_own_publisher(eid),
        "integration": tier.get("integration"), "rank": tier.get("rank"),
        "rotation_tier": tier.get("tier"), "core": tier.get("core"),
        "rota_rank": tier.get("rota_rank"), "crit_rank": tier.get("crit_rank"),
        "rota_basis": tier.get("rota_basis"),
        "profile_now": {"one_liner": e["one_liner"],
                        "why_irreplaceable": e["why_irreplaceable"],
                        "what_breaks_it": e["what_breaks_it"],
                        "phase": e["phase"], "ticker": e["ticker"],
                        "geo": e["geo"], "revenue_usd_b": e["revenue_usd_b"]},
        "factors_now": factors,
        "sources_now": sources,
        "membership": {"counts": {k: m.get(k) for k in ("sources", "self_sources",
                                                        "edges")},
                       "fails": gaps},
        "edges_now": edges,
        "to_reconcile": to_reconcile,
        "rejected_last_time": rejects.get(eid, [])[:5],
    }


def run(month: str, tier: str = "core", size: int = BATCH_SIZE, ids=None,
        start: int = 1) -> dict:
    con = nveco.connect()
    tiers = _tiers(con)
    memb = _membership(month)

    due = []
    if ids:
        chosen = [i for i in ids if con.execute(
            "SELECT 1 FROM nveco_entity WHERE id=?", (i,)).fetchone()]
        missing = [i for i in ids if i not in chosen]
    elif tier == "due":
        due = _due(con, month, tiers)
        budget = nveco.rotation_cfg()["monthly_budget"]
        # Бюджет режет ХВОСТ очереди, и это записывается вслух: тихая обрезка
        # читается как «покрыли всё», когда покрыто сорок из ста.
        chosen = [eid for _, eid, _, _ in due][:budget]
        missing = []
    else:
        rows = [(v["rota_rank"] or v["rank"], k) for k, v in tiers.items()
                if tier == "all" or v["tier"] == tier]
        chosen = [k for _, k in sorted(rows)]
        missing = []
    if not chosen:
        con.close()
        raise SystemExit(f"нечего исследовать: ярус '{tier}' пуст. Прогоните "
                         f"run_network.py — ярус пишется его стадией handoff.")

    rejects = _rejected(con, set(chosen))
    hunts = nveco_gaps.for_entities(con, set(chosen))
    packs = []
    for eid in chosen:
        p = _entity_pack(con, eid, memb, rejects, tiers.get(eid, {}))
        if p:
            p["to_hunt"] = hunts.get(eid, [])
            packs.append(p)
    # Отказы, чей предмет на карту не попал, кладутся В КАЖДЫЙ пакет отдельным
    # списком. Это единственный класс отказов, который прежняя механика доставить не
    # могла в принципе, и именно в нём сидел Carl Zeiss SMT.
    offmap = nveco_feedback.offmap_rejections(con)
    con.close()

    written = []
    for n in range(0, len(packs), size):
        batch = packs[n:n + size]
        d = db.RUNS_DIR / month / DOSSIER_DIR.format(n // size + start)
        d.mkdir(parents=True, exist_ok=True)
        (d / "batch.json").write_text(json.dumps({
            "month": month, "batch": n // size + start,
            "tier": tier, "size": len(batch),
            "как читать": (
                "1) ЧТО УЖЕ ЗНАЕМ — sources_now показывает, ЧЬИМ словом стоит профиль: "
                "self=null значит, что о сущности говорит кто-то другой. Такой профиль "
                "исследуется с нуля, а не дополняется. "
                "2) ЧТО СВЕРЯТЬ — to_reconcile: связи, которые второй конец не "
                "подтверждал. Цитата из документов ЭТОГО узла поднимает их до "
                "bilateral, и это самая дешёвая работа пакета. "
                "3) ЧЕГО НЕ ХВАТАЕТ — membership.fails: какие проверки узел сегодня "
                "не проходит. "
                "4) ЧТО ИСКАТЬ — to_hunt: связи, которых на карте НЕТ, хотя повод "
                "считать, что они есть, уже лежит в корпусе. Либо узел сам раскрыл "
                "контрагента, не назвав его, либо таксономия обещает ребро, которого "
                "у него нет ни с кем. Для ЭТОЙ работы годится любой тир: названный "
                "контрагент из пресс-релиза лучше безымянного из отчётности. "
                "Не нашли — так и скажите: `not_found` с причиной. "
                "5) ОТКАЗЫ — rejected_last_time: движок отверг эти строки с причиной, "
                "не присылайте их такими же. "
                "Тир источника, integration, core и sidedness вы НЕ пишете."),
            "выход": "dossier.json рядом с этим файлом; формат — agents/eco-dossier.md",
            "отклонено_и_на_карту_не_попало": offmap,
            "entities": batch,
        }, ensure_ascii=False, indent=2) + "\n")
        written.append({"dir": str(d), "n": len(batch),
                        "ids": [b["id"] for b in batch]})
    return {"batches": written, "entities": len(packs), "missing": missing,
            "tier": tier, "offmap_rejections": len(offmap),
            "due": [{"id": e, "tier": t, "why": w} for _, e, t, w in due],
            "over_budget": [{"id": e, "tier": t, "why": w}
                            for _, e, t, w in due[len(chosen):]]}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    month = args[0] if args else nveco.current_month()
    tier, size, ids, start = "core", BATCH_SIZE, None, 1
    for a in sys.argv[1:]:
        if a.startswith("--tier="):
            tier = a.split("=", 1)[1]
        elif a.startswith("--size="):
            size = int(a.split("=", 1)[1])
        elif a.startswith("--ids="):
            ids = [x.strip() for x in a.split("=", 1)[1].split(",") if x.strip()]
        elif a.startswith("--start="):
            # Догоняющий проход внутри уже начатого месяца: пакеты 01–05 отработаны,
            # новые обязаны лечь рядом, а не поверх.
            start = int(a.split("=", 1)[1])
    out = run(month, tier, size, ids, start)
    print(f"ярус {out['tier']}: {out['entities']} узлов, {len(out['batches'])} пакетов")
    for b in out["batches"]:
        print(f"  {b['dir']}  {b['n']}: {', '.join(b['ids'])}")
    if out["missing"]:
        print(f"  нет на карте: {', '.join(out['missing'])}")
    if out.get("over_budget"):
        print(f"  СВЕРХ БЮДЖЕТА и в этот месяц НЕ ПОПАЛИ: "
              f"{len(out['over_budget'])} узлов — "
              f"{', '.join(x['id'] for x in out['over_budget'][:12])}"
              + (" …" if len(out["over_budget"]) > 12 else ""))
    if out["offmap_rejections"]:
        print(f"  нерешённых отказов, чей предмет вне карты: "
              f"{out['offmap_rejections']} — лежат в каждом пакете")
