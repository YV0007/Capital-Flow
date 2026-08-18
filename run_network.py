"""Оркестратор сети ИИ-инфраструктуры (v3).

Usage: python run_network.py [YYYY-MM] [--deliver] [--offline]

Однократная ДОСТРОЙКА поверх готового пилота, а не месячный цикл — поэтому здесь нет
обязательного месячного параметра и нет стадии агентов. Месячный цикл начнётся со
следующего реального обновления семени.

    handoff/nvidia_ecosystem.json (семя: 106 сущностей, 243 связи)
      + runs/<месяц>/nvnet-*/       (достройка: новая сущность и связи пивот↔пивот)
      -> nvnet_ingest      pivotal, hops от ближайшего пивота, проверка новых строк
      -> nvnet_centrality  degree и betweenness (Брандес, чистый Python)
      -> nvnet_subgraphs   три подграфа ПРАВИЛОМ, вырожденность не скрывается
      -> nvnet_spof        точки отказа: удалить узел и посчитать разрыв
      -> nvnet_handoff     handoff/ai_ecosystem_network.json + чейнджлог, с валидатором
"""

import shutil
import sys
from pathlib import Path

from engine import nveco, nvnet, nvnet_handoff, nvnet_ingest

DELIVER_TO = Path.home() / "Desktop/BASE/Code/ab-investment/src/data/aiEcosystemNetwork.json"


def main(month: str, do_deliver: bool = False, offline: bool = False) -> int:
    print(f"== Сеть ИИ-инфраструктуры: {month} ==")

    net = nvnet_ingest.build(month)
    print(f"[ingest]  {len(net['entities'])} сущностей, {len(net['edges'])} связей "
          f"(семя {len(net['seed']['entities'])}/{len(net['seed']['edges'])}, "
          f"достройка +{net['newEntities']}/+{net['newEdges']})")
    print(f"          пивотов на карте: {len(net['pivots'])}"
          + (f"; НЕТ В ДАННЫХ: {', '.join(net['missingPivots'])}"
             if net["missingPivots"] else ""))
    for p in net["problems"][:15]:
        print("          ", p)
    if net["rejects"]:
        print(f"          отклонено строк: {len(net['rejects'])}")
        for r in net["rejects"][:10]:
            print(f"           {r['file']}:{r['line']} {r['reason'][:110]}")
    if net["dropped"]:
        print(f"          вне сети (дальше {nvnet.hops_limit()} шагов от любого пивота): "
              f"{', '.join(net['dropped'][:8])}")

    if not offline:
        nvnet_ingest.persist(month, net)
        print("[persist] достройка записана в nvnet_* (семя не дублируется)")

    h = nvnet_handoff.run(month, net)
    if not h["ok"]:
        print(f"[handoff] КОНТРАКТ НАРУШЕН — файл НЕ записан ({len(h['errors'])} ошибок):")
        for e in h["errors"][:25]:
            print("           ", e)
        return 1
    n = h["network"]
    print(f"[metrics] плотность {n['density']}, средняя степень {n['averageDegree']}, "
          f"кластеризация {n['clusteringCoefficient']}")
    print(f"[spof]    {len(n['singlePointsOfFailure'])} точек отказа: " +
          ", ".join(f"{s['id']}({s['betweenness']})"
                    for s in n["singlePointsOfFailure"][:6]))
    for s in n["subgraphs"]:
        mark = " ВЫРОЖДЕН" if s.get("degenerate") else ""
        print(f"[subgraph] {s['id']}: {len(s['nodeIds'])} узлов, "
              f"{len(s['edgeIds'])} связей{mark}")
    for note in n.get("subgraphNotes", []):
        print("           ", note)
    print(f"[handoff] {h['entities']} сущностей, {h['edges']} связей, версия "
          f"{h['version']} -> {h['path']}")

    if do_deliver:
        if not DELIVER_TO.parent.is_dir():
            print(f"[deliver] ПРОПУЩЕНО — нет директории {DELIVER_TO.parent}")
        else:
            shutil.copy(h["path"], DELIVER_TO)
            print(f"[deliver] -> {DELIVER_TO}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    month = args[0] if args else nveco.current_month()
    sys.exit(main(month, do_deliver="--deliver" in sys.argv,
                  offline="--offline" in sys.argv))
