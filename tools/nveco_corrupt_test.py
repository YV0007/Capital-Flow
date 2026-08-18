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
from engine import nveco, nveco_handoff            # noqa: E402


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


@case("сущность в 3 шагах от якоря", "правило 4")
def _(d):
    d["entities"][-1]["hops"] = 3


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


@case("контур ссылается на несуществующую связь", "cycles")
def _(d):
    if d["cycles"]:
        d["cycles"][0]["edges"] = ["нет__такой__связи"]
    else:
        raise SystemExit("в файле нет контуров — тест неприменим")


def main():
    acfg = nveco.anchor_cfg()
    path = ROOT / acfg["handoff"]
    if not path.exists():
        print(f"FAIL: нет файла {path} — сначала прогоните run_nvidia.py")
        return 1
    clean = json.loads(path.read_text())

    base = nveco_handoff.validate(clean, max_hops=int(acfg.get("hops", 2)))
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
        errs = nveco_handoff.validate(d, max_hops=int(acfg.get("hops", 2)))
        if errs:
            print(f"  ok   [{rule}] {name}: отвергнуто — {errs[0][:88]}")
        else:
            print(f"  FAIL [{rule}] {name}: ПРОПУЩЕНО валидатором")
            failures += 1

    print(f"\n{'PASS' if not failures else 'FAIL'}: {len(CASES) - failures}/{len(CASES)} "
          f"видов порчи пойманы")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
