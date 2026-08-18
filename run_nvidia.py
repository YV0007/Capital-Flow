"""Оркестратор карты «Экосистема NVIDIA» (v2).

Usage:
  python run_nvidia.py [YYYY-MM] [--anchor nvidia] [--skip-agents] [--deliver]
                       [--offline] [--verify-limit N]

Конвейер — тот же порядок, что у первого месячного, содержание другое:

    8 агентов (Claude Code, пишут CSV в runs/<YYYY-MM>/nveco-*/)
      -> nveco_ingest   валидация против конфигов, резолвинг, правило двух шагов
      -> nveco_verify   переобход КАЖДОЙ ссылки, alive/fetched
      -> nveco_score    рубрика, хребет, статус, гравитация, концентрация, обрезки
      -> nveco_cycles   контуры 3–5, sales / financing / lockin
      -> nveco_handoff  handoff/nvidia_ecosystem.json + чейнджлог, с валидатором на выходе

Агенты — единственный недетерминированный слой, и они отрабатывают ДО этого скрипта
(см. RUNBOOK.md). Всё, что делает скрипт, — Python и SQL над тем, что агенты написали:
одни и те же CSV всегда дают одну и ту же карту.

Порядок score -> cycles -> score не случаен: гравитация учитывает число контуров, на
которых стоит сущность, поэтому оценка прогоняется дважды. Второй проход дешёвый.
"""

import shutil
import sys
from pathlib import Path

from engine import nveco, nveco_cycles, nveco_handoff, nveco_ingest, nveco_score, nveco_verify

AGENTS = ["nveco-geo", "nveco-silicon", "nveco-systems", "nveco-power",
          "nveco-software", "nveco-models", "nveco-capital", "nveco-strategic"]


def check_agent_outputs(month: str) -> list:
    """Каких агентов не было в этом месяце. НЕ фатально: месяц, где обновили два слоя
    из шестнадцати, — легальный прогон."""
    base = Path("runs") / month
    return [a for a in AGENTS
            if not (base / a).is_dir() or not (base / a / "edges.csv").exists()]


def main(month: str, anchor: str = None, do_deliver: bool = False,
         offline: bool = False, verify_limit: int = None) -> int:
    acfg = nveco.anchor_cfg(anchor)
    print(f"== Экосистема {acfg['name']} ({acfg['id']}): {month} ==")

    missing = check_agent_outputs(month)
    if missing:
        print(f"[agents]  нет выдачи: {', '.join(missing)}")

    s = nveco_ingest.ingest_month(month, anchor)
    print(f"[ingest]  {s['entities']} сущностей, {s['edges']} связей, "
          f"{s['sources']} источников, {s['factors']} наборов факторов, "
          f"{s['rejected']} отклонено")
    for a, n in sorted(s["rejected_by_agent"].items(), key=lambda x: -x[1]):
        print(f"          отклонено у {a}: {n}")
    for w in s["warnings"][:20]:
        print("          ", w)
    if s["rejects_dir"]:
        print(f"          отказы -> {s['rejects_dir']} (вернутся агентам в следующем месяце)")

    v = nveco_verify.run(month, offline=offline, limit=verify_limit)
    if offline:
        print(f"[verify]  ПРОПУЩЕНО (offline) — {v['skipped']} ссылок не проверено")
    else:
        print(f"[verify]  {v['checked']} ссылок: {v['alive']} живых, {v['dead']} мёртвых, "
              f"{v['blocked']} заблокировано/пейволл")
    for u in v["dead_urls"][:10]:
        print("          МЁРТВАЯ", u)

    sc = nveco_score.run(month, anchor)
    print(f"[score]   {sc['entities']} сущностей; статусы связей {sc['status_mix']}; "
          f"обрезано {sc['clamped']}; блёкнет {sc['stale']}")
    print("          топ критичности: " +
          ", ".join(f"{k}={c}" for k, c in sc["top"]))
    for line in sc["log"][:12]:
        print("          ", line)

    cy = nveco_cycles.run(month, anchor)
    print(f"[cycles]  {cy['cycles']} контуров {cy['by_type']}, "
          f"через якорь проходит {cy['anchored']}")
    for c in cy["detail"][:6]:
        print(f"           {c['id']} {c['type']}: {' -> '.join(c['path'])}")

    # второй проход оценки: теперь известны контуры, и гравитация их учитывает
    nveco_score.run(month, anchor)

    h = nveco_handoff.run(month, anchor)
    if not h["ok"]:
        print(f"[handoff] КОНТРАКТ НАРУШЕН — файл НЕ записан ({len(h['errors'])} ошибок):")
        for e in h["errors"][:25]:
            print("           ", e)
        if len(h["errors"]) > 25:
            print(f"            …и ещё {len(h['errors']) - 25}")
        return 1
    print(f"[handoff] {h['entities']} сущностей, {h['edges']} связей, {h['cycles']} "
          f"контуров -> {h['path']}")
    print(f"          чейнджлог: +{h['added']} / -{h['removed']} / ~{h['changed']}")

    if do_deliver:
        dest = Path(acfg["deliver_to"]).expanduser()
        if not dest.parent.is_dir():
            print(f"[deliver] ПРОПУЩЕНО — нет директории {dest.parent}")
        else:
            shutil.copy(h["path"], dest)
            print(f"[deliver] -> {dest}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    month = args[0] if args else nveco.current_month()
    anchor, limit = None, None
    for i, a in enumerate(sys.argv[1:]):
        if a == "--anchor" and i + 2 <= len(sys.argv[1:]):
            anchor = sys.argv[i + 2]
        elif a.startswith("--anchor="):
            anchor = a.split("=", 1)[1]
        elif a.startswith("--month="):
            month = a.split("=", 1)[1]
        elif a.startswith("--verify-limit="):
            limit = int(a.split("=", 1)[1])
        elif a == "--verify-limit" and i + 2 <= len(sys.argv[1:]):
            limit = int(sys.argv[i + 2])
    if anchor in args:
        args.remove(anchor)
        month = args[0] if args else nveco.current_month()
    # --skip-agents принимается ради симметрии с run_month.py: агентский слой и так
    # отрабатывает вне этого скрипта, флаг документирует намерение.
    sys.exit(main(month, anchor, do_deliver="--deliver" in sys.argv,
                  offline="--offline" in sys.argv, verify_limit=limit))
