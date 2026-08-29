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

from engine import db, nveco, nveco_ingest              # noqa: E402

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
    # ДВА РАЗНЫХ СОБЫТИЯ, которые обязаны выглядеть по-разному в отчёте.
    #
    #   молчание агента — «мы про этот узел в этом месяце ничего не говорили».
    #                     Строка остаётся, retired_entities пуст.
    #   отказ по членству — «мы про него говорили, и предъявить ему нечего».
    #                     Строка отчёта членства помечена passes=0 с названным
    #                     провалившимся правилом.
    #
    # Пока правило выключено (Фаза 0), второе не снимает никого — но СЧИТАЕТСЯ уже
    # сейчас, и различить два случая по выдаче ingest'а должно быть можно. Иначе
    # Фаза 3, включая правило, не сможет доказать, что снесла именно должников.
    _month({"nveco-silicon": SILICON, "nveco-capital": CAPITAL})
    s = nveco_ingest.ingest_month(MONTH)
    memb = {r["id"]: r for r in s["membership"]["rows"]}

    # asml описана одним источником и держит одну связь: по членству она должница.
    assert memb["asml"]["passes"] == 0, memb["asml"]
    assert memb["asml"]["min_sources"] == 0, "долг по числу источников не замечен"
    # но с карты её никто не снял: правило выключено, а молчания агента не было
    assert "asml" not in s["retired_entities"], s["retired_entities"]

    # Теперь молчание: nveco-silicon не сдаёт файл вовсе.
    _month({"nveco-capital": CAPITAL},
           entities_by_agent={"nveco-capital": ["meta", "pytorch"]}, factors=False)
    s2 = nveco_ingest.ingest_month(MONTH)
    con = nveco.connect()
    ents = _ids(con, "nveco_entity")
    con.close()
    assert "asml" in ents, "молчание агента сняло сущность с карты"
    assert not s2["retired_entities"], s2["retired_entities"]
    # И в отчёте членства её теперь просто нет — про неё в этом месяце не говорили.
    assert "asml" not in {r["id"] for r in s2["membership"]["rows"]}
    log("должник по членству помечен и оставлен; молчание агента не снимает ничего")


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
          f"проверок снятия с карты")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

