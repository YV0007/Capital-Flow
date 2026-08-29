"""Намеренная порча файла передачи — проверка, что валидатор её ловит.

Не декоративный тест. Валидатор `nveco_handoff.validate` — единственное, что стоит между
битыми данными и дашбордом, и его отказ обязан быть доказан, а не заявлен. Каждый случай
ниже — нарушение конкретного железного правила контракта.

  python tools/nveco_corrupt_test.py
"""

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import nveco, nveco_handoff, nveco_ingest   # noqa: E402


def _first_edge_with_evidence(d):
    return next(e for e in d["edges"] if e.get("evidence"))


CASES = []


def case(name, rule):
    def deco(fn):
        CASES.append((name, rule, fn))
        return fn
    return deco


@case("висячий target", "правило 2")
def _(d):
    _first_edge_with_evidence(d)["target"] = "no-such-entity"


@case("ребро без evidence", "правило 3")
def _(d):
    _first_edge_with_evidence(d)["evidence"] = []


@case("цитата в 30 слов", "правило 3")
def _(d):
    _first_edge_with_evidence(d)["evidence"][0]["quote"] = " ".join(["слово"] * 30)


@case("сущность вне слоёв охвата", "правило 4")
def _(d):
    # Охват сужают, сущность не трогают: так проверяется именно граница карты, а не
    # опечатка в id слоя. Сузился предмет — узел перестал быть про него.
    out = d["entities"][-1]["layers"][0]["layer"]
    d["scope"]["layers"] = [l for l in d["scope"]["layers"] if l != out]


@case("вернувшееся поле hops", "правило 4")
def _(d):
    d["entities"][-1]["hops"] = 3


@case("вернувшийся фактор strategicControl", "правило 5")
def _(d):
    d["entities"][0]["criticalityFactors"]["strategicControl"] = 40


@case("вернувшийся корневой anchor", "/4")
def _(d):
    d["anchor"] = "nvidia"


@case("цифра concentration, взявшаяся ниоткуда", "правило 5")
def _(d):
    # Четвёртый фактор входит в рубрику с весом 0.15. Цифра, приписанная в файл мимо
    # арифметики, немедленно разводит criticality с её собственной формулой — и это
    # то самое место, где выдуманная доля рынка обязана умереть.
    d["entities"][0]["criticalityFactors"]["concentration"] = 90


@case("статус bilateral с одной подтвердившей стороной", "стороны")
def _(d):
    e = _first_edge_with_evidence(d)
    e["status"] = "bilateral"
    e["sidedness"] = "bilateral"
    e["claimedBy"] = [e["source"]]


@case("claimedBy называет сторону вне связи", "стороны")
def _(d):
    e = _first_edge_with_evidence(d)
    e["claimedBy"] = ["постороннийузел"]


@case("статус disputed без контрцитаты", "стороны")
def _(d):
    e = _first_edge_with_evidence(d)
    e["status"] = "disputed"
    e["sidedness"] = "disputed"
    e["counterEvidence"] = []


@case("контрцитата есть, а статус не disputed", "стороны")
def _(d):
    e = _first_edge_with_evidence(d)
    e["counterEvidence"] = [dict(e["evidence"][0])]


@case("выдуманный sidedness", "стороны")
def _(d):
    _first_edge_with_evidence(d)["sidedness"] = "оба-как-то-так"


@case("сущность без блока sourcing", "прозрачность")
def _(d):
    d["entities"][0].pop("sourcing", None)


@case("карта без предмета", "охват")
def _(d):
    d.pop("scope", None)


@case("criticality не сходится с рубрикой", "правило 5")
def _(d):
    d["entities"][0]["criticality"] = 7


@case("у слоя нет plane", "правило 6")
def _(d):
    d["layers"][0].pop("plane", None)


@case("поле dcNode у сущности", "правило 7")
def _(d):
    d["entities"][0]["dcNode"] = "litho"


@case("strength строкой", "правило 9")
def _(d):
    _first_edge_with_evidence(d)["strength"] = "95"


@case("strength вне диапазона", "правило 9")
def _(d):
    _first_edge_with_evidence(d)["strength"] = 500


@case("хребет не выведен из типа", "spine")
def _(d):
    _first_edge_with_evidence(d)["spine"] = "capital" \
        if _first_edge_with_evidence(d)["spine"] != "capital" else "moat"


@case("id связи не равен source__target__type", "правило 1")
def _(d):
    _first_edge_with_evidence(d)["id"] = "какой-то-другой-id"


@case("дублирующийся id сущности", "правило 1")
def _(d):
    d["entities"].append(copy.deepcopy(d["entities"][0]))
    d["totals"]["entities"] += 1


@case("нет блока criticalityBasis", "основание оценки")
def _(d):
    d["entities"][0].pop("criticalityBasis", None)


@case("criticalityBasis обещает четыре фактора при трёх", "основание оценки")
def _(d):
    e = next(x for x in d["entities"]
             if x["criticalityFactors"].get("concentration") is None)
    e["criticalityBasis"] = {"factorsUsed": 4, "factors": [], "renormalized": False}


@case("контур ссылается на несуществующую связь", "cycles")
def _(d):
    if d["cycles"]:
        d["cycles"][0]["edges"] = ["нет__такой__связи"]
    else:
        raise SystemExit("в файле нет контуров — тест неприменим")


# ── ПРОВЕРКИ ЧЛЕНСТВА ────────────────────────────────────────────────────────
# Отдельная секция, а не ещё десять случаев порчи файла, потому что членство —
# правило ЗАГРУЗКИ, а не формы выдачи: узел, у которого нечего предъявить от себя,
# не должен доехать до файла вообще. Проверяется сама функция правила, на игрушечных
# входах: так тест ловит ошибку в правиле, а не в том, что случайно попало в выдачу
# этого месяца.
#
# В Фазе 0 правило посчитано, но выключено (membership.enforce: false), и тест
# проверяет именно СЧЁТ. Включение — Фаза 3, и эти же случаи станут её приёмкой без
# единой правки.

NVIDIA_10K = ("https://www.sec.gov/Archives/edgar/data/1045810/"
              "000104581026000021/nvda-20260125.htm")
ASML_10K = ("https://www.sec.gov/Archives/edgar/data/937966/"
            "000162828026011378/asml-20251231.htm")


def _ent(eid, layers=("L1",)):
    return {eid: {"name": eid, "layers": list(layers)}}


def _src(owner, url):
    return {"owner_kind": "entity", "owner_key": owner, "url": url,
            "tier": 1, "quote": "x"}


def _edge(eid, a, b):
    return {"id": eid, "source": a, "target": b}


MEMBERSHIP_CASES = []


def mcase(name, expect_fail):
    def deco(fn):
        MEMBERSHIP_CASES.append((name, expect_fail, fn))
        return fn
    return deco


@mcase("профиль, описанный только чужой отчётностью", "min_self_sources")
def _():
    # Три источника — норма пройдена. Но все три изданы другой компанией, и
    # собственного слова у узла нет ни одного.
    return (_ent("asml"),
            {"a": _edge("a", "asml", "nvidia"), "b": _edge("b", "asml", "tsmc")},
            [_src("asml", NVIDIA_10K + "#1"), _src("asml", NVIDIA_10K + "#2"),
             _src("asml", NVIDIA_10K + "#3")])


@mcase("тот же профиль с одной собственной цитатой", None)
def _():
    return (_ent("asml"),
            {"a": _edge("a", "asml", "nvidia"), "b": _edge("b", "asml", "tsmc")},
            [_src("asml", NVIDIA_10K + "#1"), _src("asml", NVIDIA_10K + "#2"),
             _src("asml", ASML_10K)])


@mcase("сущность с одной подтверждённой связью", "min_confirmed_edges")
def _():
    return (_ent("asml"), {"a": _edge("a", "asml", "nvidia")},
            [_src("asml", NVIDIA_10K + "#1"), _src("asml", NVIDIA_10K + "#2"),
             _src("asml", ASML_10K)])


@mcase("сущность с одним источником", "min_sources")
def _():
    return (_ent("asml"),
            {"a": _edge("a", "asml", "nvidia"), "b": _edge("b", "asml", "tsmc")},
            [_src("asml", ASML_10K)])


@mcase("сущность вне слоёв охвата", "in_scope")
def _():
    return (_ent("asml", layers=("L99",)),
            {"a": _edge("a", "asml", "nvidia"), "b": _edge("b", "asml", "tsmc")},
            [_src("asml", ASML_10K + "#1"), _src("asml", ASML_10K + "#2"),
             _src("asml", ASML_10K + "#3")])


@mcase("у закона нет пресс-службы: правило SELF снимается фактом", None)
def _():
    # chips-act не имеет собственного издателя (config/entity_domains.yaml), и
    # min_self_sources для него снимается ровно этим, а не исключением в коде.
    return (_ent("chips-act"),
            {"a": _edge("a", "chips-act", "nvidia"),
             "b": _edge("b", "chips-act", "tsmc")},
            [_src("chips-act", NVIDIA_10K + "#1"), _src("chips-act", NVIDIA_10K + "#2"),
             _src("chips-act", NVIDIA_10K + "#3")])


# ── СВЕРКА ДВУХ СТОРОН ───────────────────────────────────────────────────────
# Стадия `nveco_reconcile` отвечает на один вопрос: сколько КОНЦОВ стоит за связью.
# Проверяется само правило, а не то, что вышло в этом месяце: правило обязано
# держаться на входах, которых в данных пока нет (спор, например, не встречается ни
# разу — и именно поэтому его нельзя оставить непроверенным).

RECONCILE_CASES = []


def rcase(name, tiers, claimed, disputed, expect_status, expect_side):
    RECONCILE_CASES.append((name, tiers, claimed, disputed, expect_status, expect_side))


rcase("обе стороны цитируют себя сами", [1, 1], {"a", "b"}, False, "bilateral", "bilateral")
rcase("один издатель, названный дважды", [1, 1], {"a"}, False, "confirmed", "single")
rcase("второй конец молчит", [1], set(), False, "high_confidence", "single")
rcase("контрцитата при двух подтверждениях", [1, 1], {"a", "b"}, True, "disputed", "disputed")
rcase("контрцитата при одном источнике", [2], {"a"}, True, "disputed", "disputed")
rcase("ни одной цитаты сторон", [5, 5], set(), False, "signal", "single")


def run_reconcile() -> int:
    from engine.nveco_score import _status_and_confidence
    failures = 0
    for name, tiers, claimed, disputed, exp_st, exp_side in RECONCILE_CASES:
        status, _ = _status_and_confidence(tiers, claimed, disputed)
        side = ("disputed" if disputed else
                "bilateral" if len(claimed) >= 2 else "single")
        ok = status == exp_st and side == exp_side
        print(f"  {'ok  ' if ok else 'FAIL'} [сверка] {name}: {status}/{side}"
              + ("" if ok else f" — ожидалось {exp_st}/{exp_side}"))
        failures += 0 if ok else 1
    return failures


def run_membership() -> int:
    failures = 0
    for name, expect, build in MEMBERSHIP_CASES:
        ents, edges, srcs = build()
        # statuses=None: в игрушечном входе статусов ещё нет, и правило считает по
        # связям вообще — ровно так же, как на первом прогоне месяца.
        rep = nveco_ingest.membership_report(ents, edges, srcs, None)
        row = rep["rows"][0]
        failed = [k for k in ("in_scope", "min_sources", "min_self_sources",
                              "min_confirmed_edges") if row[k] == 0]
        if expect is None:
            ok = not failed
            what = "проходит" if ok else f"НЕ проходит: {', '.join(failed)}"
        else:
            ok = failed == [expect]
            what = (f"не проходит {expect}" if ok
                    else f"ожидался отказ по {expect}, получено {failed or 'проходит'}")
        print(f"  {'ok  ' if ok else 'FAIL'} [членство] {name}: {what}")
        failures += 0 if ok else 1
    return failures


def main():
    path = ROOT / nveco.scope_cfg()["handoff"]
    if not path.exists():
        print(f"FAIL: нет файла {path} — сначала прогоните run_nvidia.py")
        return 1
    clean = json.loads(path.read_text())

    base = nveco_handoff.validate(clean)
    if base:
        print("FAIL: ЧИСТЫЙ файл не проходит валидатор:")
        for e in base[:10]:
            print("   ", e)
        return 1
    print(f"чистый файл: PASS (0 ошибок, {clean['totals']['entities']} сущностей, "
          f"{clean['totals']['edges']} связей)")

    failures = 0
    for name, rule, corrupt in CASES:
        d = copy.deepcopy(clean)
        corrupt(d)
        errs = nveco_handoff.validate(d)
        if errs:
            print(f"  ok   [{rule}] {name}: отвергнуто — {errs[0][:88]}")
        else:
            print(f"  FAIL [{rule}] {name}: ПРОПУЩЕНО валидатором")
            failures += 1

    print()
    failures += run_reconcile()
    print()
    failures += run_membership()

    total = len(CASES) + len(MEMBERSHIP_CASES) + len(RECONCILE_CASES)
    print(f"\n{'PASS' if not failures else 'FAIL'}: {total - failures}/{total} "
          f"проверок пройдено ({len(CASES)} видов порчи, "
          f"{len(RECONCILE_CASES)} случаев сверки, "
          f"{len(MEMBERSHIP_CASES)} случаев членства)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
