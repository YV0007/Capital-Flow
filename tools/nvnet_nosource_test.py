"""Проверка, что связь БЕЗ источника в сеть не попадает.

Правило контракта v2 «нет цитаты — нет ребра» действует и в v3. Заявить это в тексте
дёшево; здесь оно проверяется на настоящем конвейере: в выдачу подкладывается ребро без
единой строки в sources.csv, конвейер прогоняется, и ребро обязано быть отклонено с
причиной, а не молча принято.

Заодно проверяется валидатор файла: собранный вручную payload с пустым evidence,
несуществующим пивотом и заглушкой вместо центральности не должен пройти.

  python tools/nvnet_nosource_test.py [YYYY-MM]
"""

import copy
import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import nveco, nvnet_handoff, nvnet_ingest      # noqa: E402

BAD = {"source": "openai", "target": "asml", "type": "customer_of",
       "direction": "upstream", "strength": "90", "lock_in_depth": "70",
       "substitutability": "20", "is_reversible": "true", "risk_level": "medium",
       "risk_type": "market", "risk_timeline": "1-2y", "risk_mitigation": "",
       "tech_node": "", "formed": "2025", "strengthened": "",
       "note": "Выдуманная связь без единого источника — обязана быть отклонена.",
       "origin": "TEST"}


def main(month):
    edges = ROOT / "runs" / month / "nvnet-network" / "edges.csv"
    if not edges.exists():
        print(f"FAIL: нет {edges}")
        return 1
    backup = edges.with_suffix(".csv.bak")
    shutil.copy(edges, backup)
    try:
        rows = list(csv.DictReader(backup.open(encoding="utf-8")))
        hdr = list(rows[0].keys())
        with edges.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=hdr)
            w.writeheader()
            w.writerows(rows + [{k: BAD.get(k, "") for k in hdr}])

        net = nvnet_ingest.build(month)
        bad_id = f"{BAD['source']}__{BAD['target']}__{BAD['type']}"
        if bad_id in net["edges"]:
            print(f"FAIL: связь без источника {bad_id} ПРИНЯТА конвейером")
            return 1
        reason = next((r["reason"] for r in net["rejects"] if bad_id in r["row"]), None)
        print(f"ok  связь без источника отклонена: {reason}")

        payload = nvnet_handoff.build(month, net)
        base = nvnet_handoff.validate(payload)
        if base:
            print("FAIL: чистый payload не проходит валидатор:", base[:5])
            return 1
        print(f"ok  чистый payload проходит валидатор "
              f"({payload['totals']['entities']} сущностей, {payload['totals']['edges']} связей)")

        cases = []

        def case(name):
            def deco(fn):
                cases.append((name, fn))
                return fn
            return deco

        @case("ребро с пустым evidence")
        def _(d):
            d["edges"][0]["evidence"] = []

        @case("пивот, которого нет среди сущностей")
        def _(d):
            d["pivots"] = list(d["pivots"]) + ["no-such-pivot"]

        @case("betweenness-заглушка вне 0..1")
        def _(d):
            d["entities"][0]["centrality"]["betweenness"] = 42

        @case("сущность без pivotal")
        def _(d):
            d["entities"][0].pop("pivotal", None)

        @case("остался anchor от v2")
        def _(d):
            d["anchor"] = "nvidia"

        @case("подграф ссылается на несуществующий узел")
        def _(d):
            d["network"]["subgraphs"][0]["nodeIds"] = ["no-such-entity"]

        @case("точка отказа без обоснования")
        def _(d):
            if d["network"]["singlePointsOfFailure"]:
                d["network"]["singlePointsOfFailure"][0]["reason"] = ""
            else:
                d["network"]["singlePointsOfFailure"] = [{"id": "nvidia", "reason": ""}]

        @case("totalNodes не сходится")
        def _(d):
            d["network"]["totalNodes"] = 999

        @case("цитата в 40 слов")
        def _(d):
            d["edges"][0]["evidence"][0]["quote"] = " ".join(["слово"] * 40)

        failures = 0
        for name, corrupt in cases:
            d = copy.deepcopy(payload)
            corrupt(d)
            errs = nvnet_handoff.validate(d)
            if errs:
                print(f"  ok   {name}: отвергнуто — {errs[0][:90]}")
            else:
                print(f"  FAIL {name}: ПРОПУЩЕНО валидатором")
                failures += 1
        print(f"\n{'PASS' if not failures else 'FAIL'}: "
              f"{len(cases) - failures}/{len(cases)} видов порчи пойманы")
        return 1 if failures else 0
    finally:
        shutil.move(backup, edges)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else nveco.current_month()))
