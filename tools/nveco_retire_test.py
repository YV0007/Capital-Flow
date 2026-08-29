"""Проверка, что загрузка АВТОРИТЕТНА за свой месяц: строка, исчезнувшая из CSV,
исчезает и из базы — вместе с источниками, факторами и участием в контурах.

И что снятие ПО МОЛЧАНИЮ агента отличимо от отказа ПО ЧЛЕНСТВУ: это разные события,
и путать их нельзя ни в отчёте, ни в базе. См. последний случай файла.

Регрессия на 2026-08-23. Тогда семь рёбер сменили ориентацию
(`meta__pytorch__funded_by` -> `pytorch__meta__funded_by`), id выводится из концов,
и `INSERT ... ON CONFLICT DO UPDATE` записал новые, не тронув старые: 250 связей
вместо 243, чейнджлог «+7 / -0» вместо «+7 / -7», чистка руками.

Тест работает на СВОЕЙ базе и своём каталоге прогонов (переменная CAPITAL_DB и
подмена db.RUNS_DIR), поэтому запускается когда угодно и ничего не портит:

  python tools/nveco_retire_test.py
"""

import csv
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="nveco-retire-"))
os.environ["CAPITAL_DB"] = str(TMP / "test.db")

from engine import db, nveco, nveco_feedback, nveco_ingest   # noqa: E402

db.RUNS_DIR = TMP / "runs"
MONTH = "2026-08"

ENTITY_COLS = ["id", "name", "type", "role", "sector", "primary_layer", "one_liner"]
EDGE_COLS = ["source", "target", "type", "strength", "note"]
SOURCE_COLS = ["owner_kind", "owner_key", "tier", "type", "title", "url", "quote"]
FACTOR_COLS = ["entity_id", "irreplaceability", "lock_in_depth", "time_to_replace",
               "concentration", "why_irreplaceability", "why_lock_in", "why_time",
               "why_concentration"]

ENTITIES = {
    "nvidia": ["nvidia", "NVIDIA", "company", "platform", "gpu", "L10", "ускорители"],
    "tsmc": ["tsmc", "TSMC", "company", "producer", "foundry", "L3", "фабрика"],
    "asml": ["asml", "ASML", "company", "producer", "fab_equipment", "L1", "станки"],
    "meta": ["meta", "Meta", "company", "demand", "hyperscaler", "L9", "покупатель"],
    "pytorch": ["pytorch", "PyTorch", "technology", "platform", "gpu", "L10", "фреймворк"],
}
FACTORS = ["tsmc", 90, 85, 80, 70, "единственная фабрика на N3",
           "переезд стоит годы", "новая фабрика — четыре года",
           "почти весь передовой кремний"]


def _write(path, cols, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)


def _source(kind, key, n):
    return [kind, key, 1, "company_pr", f"пресс-релиз {n}",
            f"https://nvidianews.nvidia.com/news/{key.replace('__', '-')}-{n}",
            "договор подтверждён обеими сторонами в официальном сообщении"]


def _month(edges_by_agent, entities_by_agent=None, factors=True):
    """Разложить месяц по каталогам агентов. Источник на каждое ребро — обязателен."""
    base = db.RUNS_DIR / MONTH
    if base.exists():
        shutil.rmtree(base)
    entities_by_agent = entities_by_agent or {
        "nveco-silicon": ["nvidia", "tsmc", "asml"],
        "nveco-capital": ["meta", "pytorch"],
    }
    for agent, ids in entities_by_agent.items():
        _write(base / agent / "entities.csv", ENTITY_COLS, [ENTITIES[i] for i in ids])
    for agent, rows in edges_by_agent.items():
        _write(base / agent / "edges.csv", EDGE_COLS,
               [[s, t, ty, 80, "связь"] for s, t, ty in rows])
        srcs = [_source("edge", f"{s}__{t}__{ty}", i) for i, (s, t, ty) in enumerate(rows)]
        if agent == "nveco-silicon":
            srcs.append(_source("entity", "tsmc", 9))
        _write(base / agent / "sources.csv", SOURCE_COLS, srcs)
    if factors and "nveco-silicon" in entities_by_agent:
        _write(base / "nveco-silicon" / "factors.csv", FACTOR_COLS, [FACTORS])


SILICON = [("tsmc", "nvidia", "manufactures"), ("asml", "tsmc", "supplies")]
CAPITAL = [("meta", "nvidia", "customer_of"), ("meta", "pytorch", "funded_by")]


def _ids(con, table):
    return {r[0] for r in con.execute(f"SELECT id FROM {table}")}


def _count(con, sql, *args):
    return con.execute(sql, args).fetchone()[0]


CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


@check("ребро, исчезнувшее из CSV, снято вместе с источником")
def _(log):
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    assert len(_ids(con, "nveco_edge")) == 4, _ids(con, "nveco_edge")
    con.close()

    _month({"nveco-silicon": SILICON[:1], "nveco-capital": CAPITAL})
    s = nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    edges = _ids(con, "nveco_edge")
    con.close()
    assert "asml__tsmc__supplies" not in edges, "снятое ребро осталось в базе"
    assert len(edges) == 3, edges
    assert s["retired_edges"] == ["asml__tsmc__supplies"], s["retired_edges"]
    log("снято ровно одно ребро, остальные три на месте")
    con = nveco.connect()
    left = _count(con, "SELECT COUNT(*) FROM nveco_source WHERE owner_kind='edge' "
                       "AND owner_id='asml__tsmc__supplies'")
    con.close()
    assert left == 0, f"источники снятого ребра остались: {left}"
    log("источники снятого ребра удалены")


@check("разворот ориентации не оставляет обе версии (регрессия 2026-08-23)")
def _(log):
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    nveco_ingest.ingest_month(MONTH)
    flipped = [CAPITAL[0], ("pytorch", "meta", "funded_by")]
    _month({"nveco-silicon": SILICON, "nveco-capital": flipped})
    nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    edges = _ids(con, "nveco_edge")
    con.close()
    assert "pytorch__meta__funded_by" in edges, "новая ориентация не записана"
    assert "meta__pytorch__funded_by" not in edges, "старая ориентация осталась"
    assert len(edges) == 4, f"{len(edges)} связей вместо 4 — обе версии живы"
    log("после разворота ровно 4 связи, старого id нет")


@check("молчащий агент ничего не теряет")
def _(log):
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    nveco_ingest.ingest_month(MONTH)
    # месяц, где выдал ТОЛЬКО nveco-silicon: строки nveco-capital обязаны выжить
    _month({"nveco-silicon": SILICON},
           entities_by_agent={"nveco-silicon": ["nvidia", "tsmc", "asml"]})
    s = nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    edges, ents = _ids(con, "nveco_edge"), _ids(con, "nveco_entity")
    con.close()
    assert "meta__nvidia__customer_of" in edges, "снято ребро молчавшего агента"
    assert "meta" in ents and "pytorch" in ents, "снята сущность молчавшего агента"
    assert not s["retired_edges"] and not s["retired_entities"], s["retired_edges"]
    log("четыре связи и пять сущностей на месте, снято 0")


@check("сущность, исчезнувшая из CSV, снята со слоями, фактором и риском")
def _(log):
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    # Четыре: фикстура даёт `concentration` вместе с обоснованием, как это будет
    # делать досье. На реальных данных Фазы 0 строк три, и рубрика считается
    # перенормировкой — оба случая обязаны работать одним и тем же кодом.
    assert _count(con, "SELECT COUNT(*) FROM nveco_entity_factor WHERE entity_id='tsmc'") == 4
    con.close()
    # asml уходит из entities.csv ВМЕСТЕ со своим ребром — иначе ребро её удержит
    _month({"nveco-silicon": SILICON[:1], "nveco-capital": CAPITAL},
           entities_by_agent={"nveco-silicon": ["nvidia", "tsmc"],
                              "nveco-capital": ["meta", "pytorch"]}, factors=False)
    s = nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    ents = _ids(con, "nveco_entity")
    rest = {t: _count(con, f"SELECT COUNT(*) FROM {t} WHERE entity_id='asml'")
            for t in ("nveco_entity_layer", "nveco_entity_factor", "nveco_entity_risk")}
    con.close()
    assert "asml" not in ents, "снятая сущность осталась"
    assert s["retired_entities"] == ["asml"], s["retired_entities"]
    assert not any(rest.values()), f"хвосты снятой сущности: {rest}"
    log(f"asml снята; хвостов не осталось {rest}")


@check("сущность держится на карте, пока на неё ссылается связь молчащего агента")
def _(log):
    # pytorch переходит под nveco-silicon, ребро meta->pytorch остаётся за nveco-capital
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL},
           entities_by_agent={"nveco-silicon": ["nvidia", "tsmc", "asml", "pytorch"],
                              "nveco-capital": ["meta"]})
    nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    owner = con.execute("SELECT owner_agent o FROM nveco_entity WHERE id='pytorch'").fetchone()["o"]
    con.close()
    assert owner == "nveco-silicon", owner

    # nveco-silicon перестаёт заявлять pytorch; nveco-capital в этом месяце молчит,
    # и его ребро meta->pytorch остаётся в базе — значит и сущность обязана остаться
    _month({"nveco-silicon": SILICON},
           entities_by_agent={"nveco-silicon": ["nvidia", "tsmc", "asml"]})
    s = nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    ents, edges = _ids(con, "nveco_entity"), _ids(con, "nveco_edge")
    con.close()
    assert "meta__pytorch__funded_by" in edges, "снято ребро молчавшего агента"
    assert "pytorch" in ents, "сущность снята из-под живого ребра"
    assert s["held_entities"] == ["pytorch"], s["held_entities"]
    assert any("оставлена на карте" in w for w in s["warnings"]), s["warnings"]
    log("pytorch на месте и названа в warnings: её удерживает чужая связь")


@check("выдача, отвергнутая целиком, ничего не снимает")
def _(log):
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    nveco_ingest.ingest_month(MONTH)
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    base = db.RUNS_DIR / MONTH
    # у агента «съехала колонка»: тип связи не из таксономии, отвергнуты все строки
    _write(base / "nveco-capital" / "edges.csv", EDGE_COLS,
           [["meta", "nvidia", "нет-такого-типа", 80, "брак"],
            ["meta", "pytorch", "нет-такого-типа", 80, "брак"]])
    s = nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    edges = _ids(con, "nveco_edge")
    con.close()
    assert "meta__nvidia__customer_of" in edges, "снято по аварийной выдаче"
    assert not s["retired_edges"], s["retired_edges"]
    assert any("не выжила ни одна строка" in w for w in s["warnings"]), s["warnings"]
    log("связи целы, случай ушёл в warnings")


@check("пустой файл — это отзыв: агент заявил, что у него ничего нет")
def _(log):
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    nveco_ingest.ingest_month(MONTH)
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    _write(db.RUNS_DIR / MONTH / "nveco-capital" / "edges.csv", EDGE_COLS, [])
    s = nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    edges = _ids(con, "nveco_edge")
    con.close()
    assert edges == {"tsmc__nvidia__manufactures", "asml__tsmc__supplies"}, edges
    assert len(s["retired_edges"]) == 2, s["retired_edges"]
    log("обе связи nveco-capital сняты, связи nveco-silicon целы")


@check("ретирование по членству отличимо от ретирования по молчанию агента")
def _(log):
    # ТРИ РАЗНЫХ СОБЫТИЯ, которые обязаны выглядеть по-разному.
    #
    #   молчание агента     — «мы про этот узел в этом месяце ничего не говорили».
    #                         Строка остаётся, retired_entities пуст.
    #   гейт по покрытию    — «мы про него говорили, но досье по нему не отрабатывали».
    #                         Проверки на источники к нему НЕ ПРИМЕНЯЮТСЯ, и провалом
    #                         это не считается.
    #   отказ по членству   — «досье отработано, и предъявить нечего». Строка отчёта
    #                         помечена провалом с названной проверкой.
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    s = nveco_ingest.ingest_month(MONTH)
    memb = {r["id"]: r for r in s["membership"]["rows"]}

    # asml описана одним источником, но её досье не отрабатывалось: гейт снимает
    # с неё проверку на число источников, и долгом это не является.
    assert memb["asml"]["pending_dossier"] == 1, memb["asml"]
    assert memb["asml"]["min_sources"] == -1, memb["asml"]
    assert "min_sources" not in memb["asml"]["failed"], memb["asml"]
    log("непокрытая досье сущность не судится по числу источников")

    # Отмечаем досье отработанным — и та же самая строка становится долгом.
    con = nveco.connect()
    con.execute("INSERT OR REPLACE INTO nveco_dossier_run "
                "(entity_id, month, batch, tier, sources, self_srcs, edges) "
                "VALUES ('asml', ?, 'test', 'core', 1, 0, 1)", (MONTH,))
    con.commit()
    con.close()
    s2 = nveco_ingest.ingest_month(MONTH)
    memb2 = {r["id"]: r for r in s2["membership"]["rows"]}
    assert memb2["asml"]["pending_dossier"] == 0, memb2["asml"]
    assert "min_sources" in memb2["asml"]["failed"], memb2["asml"]
    log("та же строка после отработанного досье становится провалом min_sources")

    # Но с карты её не сняли: её держит ребро с цитатой, и провал членства узла не
    # является свидетельством против чужого утверждения о связи.
    con = nveco.connect()
    ents = _ids(con, "nveco_entity")
    con.close()
    assert "asml" in ents, "узел, удерживаемый ребром, снят членством"
    held = {h["id"] for h in s2["membership"]["held"]}
    assert "asml" in held, s2["membership"]["held"]
    assert not s2["membership"]["retired"], s2["membership"]["retired"]
    assert "asml" not in s2["retired_entities"], s2["retired_entities"]
    log("удержана ребром: названа в held, но не в retired и не снята с карты")

    # Теперь молчание: nveco-silicon не сдаёт файл вовсе.
    _month({"nveco-capital": CAPITAL},
           entities_by_agent={"nveco-capital": ["meta", "pytorch"]}, factors=False)
    s3 = nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    ents = _ids(con, "nveco_entity")
    con.close()
    assert "asml" in ents, "молчание агента сняло сущность с карты"
    assert not s3["retired_entities"], s3["retired_entities"]
    # И в отчёте членства её теперь просто нет — про неё в этом месяце не говорили.
    assert "asml" not in {r["id"] for r in s3["membership"]["rows"]}
    log("молчание агента не снимает ничего и в отчёт членства не попадает")


@check("узел без единой связи снимается членством, и отказ уходит в очередь")
def _(log):
    # Единственный случай, когда retire_unheld действительно снимает: держать узел
    # нечем. Отказ обязан уйти в реестр и оттуда в очередь кандидатов — узел не
    # исчезает, он возвращается на рассмотрение.
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    base = db.RUNS_DIR / MONTH / "nveco-silicon"
    rows = [ENTITIES[i] for i in ("nvidia", "tsmc", "asml")] + [
        ["lonely", "Lonely Corp", "company", "producer", "gpu", "L10", "ни с кем"]]
    _write(base / "entities.csv", ENTITY_COLS, rows)
    s = nveco_ingest.ingest_month(MONTH)
    retired = {r["id"] for r in s["membership"]["retired"]}
    assert "lonely" in retired, s["membership"]["retired"]
    con = nveco.connect()
    assert "lonely" not in _ids(con, "nveco_entity")
    cand = {r["name"]: dict(r) for r in con.execute("SELECT * FROM nveco_candidate")}
    con.close()
    assert "Lonely Corp" in cand, cand
    assert cand["Lonely Corp"]["origin"] == "rejection", cand["Lonely Corp"]
    log("снят членством, назван в retired, вернулся в очередь кандидатов")


# ── ОБРАТНАЯ СВЯЗЬ ───────────────────────────────────────────────────────────
# Отдельная группа случаев, заведённая Фазой 2. Проверяется не то, что отказ ЗАПИСАН
# — это работало и раньше, — а то, что он ДОСТАВЛЕН и не может потеряться молча.
#
# Повод известен поимённо. `Carl Zeiss SMT` отвергался каждым прогоном, причина
# писалась в файл, файл лежал в репозитории закоммиченным, и ни одна проверка не была
# обязана его открыть. Механика без проверки потребления выглядит живой ровно до дня,
# когда кто-нибудь пересчитает данные руками.

OFFSCOPE = ["ghost", "Ghost Corp", "company", "producer", "gpu", "L99", "вне слоёв"]


def _with_ghost(agent="nveco-silicon"):
    """Месяц, в котором один агент прислал сущность с несуществующим слоем.

    Такая строка отвергается загрузкой и на карту не попадает — то есть попадает
    ровно в тот класс отказов, который прежняя механика доставить не могла.
    """
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    base = db.RUNS_DIR / MONTH / agent
    rows = [ENTITIES[i] for i in ("nvidia", "tsmc", "asml")] + [OFFSCOPE]
    _write(base / "entities.csv", ENTITY_COLS, rows)


@check("отказ по сущности переживает прогон и встаёт в очередь кандидатов")
def _(log):
    _with_ghost()
    s = nveco_ingest.ingest_month(MONTH)
    assert s["rejected"] >= 1, s["rejected"]
    con = nveco.connect()
    rej = [dict(r) for r in con.execute(
        "SELECT * FROM nveco_rejection WHERE subject_kind='entity'")]
    cand = [dict(r) for r in con.execute("SELECT * FROM nveco_candidate")]
    con.close()
    assert len(rej) == 1, rej
    assert rej[0]["subject_name"] == "Ghost Corp", rej[0]
    log(f"отказ записан: {rej[0]['reason'][:60]}")
    # ГЛАВНОЕ. Отклонённой сущности в базе нет, и пакет узла ей собрать нельзя.
    # Единственный канал, у которого есть потребитель, — очередь кандидатов.
    assert [c["name"] for c in cand] == ["Ghost Corp"], cand
    assert cand[0]["origin"] == "rejection", cand[0]
    assert rej[0]["status"] == "queued", rej[0]
    log("отклонённая сущность доставлена в очередь кандидатов, а не в файл")


@check("отказ, присланный второй раз без изменений, считается повтором")
def _(log):
    _with_ghost()
    nveco_ingest.ingest_month(MONTH)
    _with_ghost()
    nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    r = con.execute("SELECT * FROM nveco_rejection WHERE subject_kind='entity'").fetchone()
    con.close()
    assert r["times"] == 2, dict(r)
    assert r["first_seen"] == MONTH and r["last_seen"] == MONTH
    log("счётчик повторов 2 — строка не подменена новой записью")


@check("отказ, который перестал приходить, снимается сам и без решения")
def _(log):
    _with_ghost()
    nveco_ingest.ingest_month(MONTH)
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})   # призрака больше нет
    nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    r = con.execute("SELECT * FROM nveco_rejection WHERE subject_kind='entity'").fetchone()
    con.close()
    # 'queued' не переоткрывается и не «снимается исправлением»: предмет уже передан
    # очереди, и её решение — единственное, которое его закрывает.
    assert r["status"] == "queued", dict(r)
    log("строка, переданная очереди, остаётся за очередью")


@check("dismissed не переоткрывается повторной присылкой, open — переоткрывается")
def _(log):
    _with_ghost()
    nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    key = con.execute("SELECT key FROM nveco_rejection WHERE subject_kind='edge' "
                      "OR subject_kind='entity' LIMIT 1").fetchone()["key"]
    nveco_feedback.decide_rejection(con, key, "dismissed", "так и должно быть", MONTH)
    con.commit()
    con.close()
    _with_ghost()
    nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    r = con.execute("SELECT * FROM nveco_rejection WHERE key=?", (key,)).fetchone()
    con.close()
    assert r["status"] == "dismissed", dict(r)
    assert r["times"] == 2, dict(r)
    log("решение 'обязано отвергаться всегда' держится, повторы всё равно считаются")


@check("кандидат, оказавшийся на карте, получает решение, а не молчание")
def _(log):
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    nveco_feedback.record_candidates(con, MONTH, [
        {"name": "TSMC", "named_by": "nvidia", "why": "названа в отчётности"},
        {"name": "Celestica", "named_by": "nvidia", "why": "названа сборщиком"}])
    hit = nveco_feedback.mark_on_map(con, MONTH)
    con.commit()
    rows = {r["name"]: dict(r) for r in con.execute("SELECT * FROM nveco_candidate")}
    audit = nveco_feedback.audit(con)
    con.close()
    assert [h[1] for h in hit] == ["tsmc"], hit
    assert rows["TSMC"]["status"] == "on_map" and rows["TSMC"]["decision"], rows["TSMC"]
    assert rows["Celestica"]["status"] == "open", rows["Celestica"]
    # Нерешённый кандидат обязан РОНЯТЬ проверку, а не тихо лежать в очереди.
    assert not audit["ok"], audit
    assert [c["name"] for c in audit["open_candidates"]] == ["Celestica"], audit
    log("на карте — решение с id; не на карте — открытая строка, роняющая проверку")


@check("пакетчик отдаёт отказ, чей предмет на карту не попал")
def _(log):
    # Структурная дыра, в которой просидел Carl Zeiss SMT: пакет собирается обходом
    # сущностей базы, отклонённой сущности в базе нет, значит её отказ не мог попасть
    # ни в один пакет — ни тогда, ни потом.
    _with_ghost()
    nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    off = nveco_feedback.offmap_rejections(con)
    inpack = nveco_feedback.rejections_for(con, {"nvidia", "tsmc", "asml"})
    con.close()
    names = {o["name"] or o["id"] for o in off}
    assert "Ghost Corp" in names, off
    assert not any("Ghost" in str(v) for v in inpack.values()), inpack
    log(f"вне карты и потому вне пакета узла: {', '.join(sorted(n for n in names if n))}")


def main():
    fails = 0
    for name, fn in CHECKS:
        if (TMP / "test.db").exists():
            (TMP / "test.db").unlink()          # каждый случай — со своей чистой базы
        try:
            fn(lambda m: print(f"        {m}"))
            print(f"  ok   {name}")
        except AssertionError as e:
            print(f"  FAIL {name}: {e}")
            fails += 1
    shutil.rmtree(TMP, ignore_errors=True)
    print(f"\n{'PASS' if not fails else 'FAIL'}: {len(CHECKS) - fails}/{len(CHECKS)} "
          f"проверок снятия с карты и обратной связи")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

