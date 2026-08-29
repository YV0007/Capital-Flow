"""Оркестратор карты экосистемы ИИ-инфраструктуры (контракт nvidia-ecosystem/4).

Usage:
  python run_nvidia.py [YYYY-MM] [--skip-agents] [--deliver]
                       [--offline] [--verify-limit N]

Имя скрипта и префикс `nveco_` историчны: пилот был картой одной орбиты. Карта с v4
центра не имеет, а переименование 13 модулей и 18 таблиц посреди миграции контракта —
чистый риск без выигрыша. См. handoff/AI-ECOSYSTEM-V4-BUILD-LOG.md.

Конвейер — тот же порядок, что у первого месячного, содержание другое:

    8 агентов (Claude Code, пишут CSV в runs/<YYYY-MM>/nveco-*/)
      -> nveco_ingest   валидация против конфигов, резолвинг, охват и членство
      -> nveco_verify   переобход КАЖДОЙ ссылки, alive/fetched
      -> nveco_reconcile сверка двух сторон: чей документ, сколько концов, споры
      -> nveco_score    рубрика, хребет, статус, гравитация
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

from engine import (nveco, nveco_cycles, nveco_handoff, nveco_ingest, nveco_reconcile,
                    nveco_score, nveco_verify)

AGENTS = ["nveco-geo", "nveco-silicon", "nveco-systems", "nveco-power",
          "nveco-software", "nveco-models", "nveco-capital", "nveco-strategic"]


def check_agent_outputs(month: str) -> list:
    """Каких агентов не было в этом месяце. НЕ фатально: месяц, где обновили два слоя
    из шестнадцати, — легальный прогон."""
    base = Path("runs") / month
    return [a for a in AGENTS
            if not (base / a).is_dir() or not (base / a / "edges.csv").exists()]


def main(month: str, do_deliver: bool = False,
         offline: bool = False, verify_limit: int = None) -> int:
    print(f"== Экосистема ИИ-инфраструктуры ({nveco.SCOPE_ID}): {month} ==")

    missing = check_agent_outputs(month)
    if missing:
        print(f"[agents]  нет выдачи: {', '.join(missing)}")

    s = nveco_ingest.ingest_month(month)
    print(f"[ingest]  {s['entities']} сущностей, {s['edges']} связей, "
          f"{s['sources']} источников, {s['factors']} наборов факторов, "
          f"{s['rejected']} отклонено")
    for a, n in sorted(s["rejected_by_agent"].items(), key=lambda x: -x[1]):
        print(f"          отклонено у {a}: {n}")
    if s["retired_entities"] or s["retired_edges"]:
        print(f"          снято с карты: {len(s['retired_entities'])} сущностей, "
              f"{len(s['retired_edges'])} связей "
              f"(больше не заявлены агентом, который в этом месяце выдал файл)")
        for i in (s["retired_entities"] + s["retired_edges"])[:10]:
            print("           снято", i)
    # Печатается ОТДЕЛЬНО от warnings: список предупреждений режется двадцатью
    # строками, а «агент сдал файл, из которого не выжило ничего» — то, ради чего
    # прогон стоит перезапустить, и потеряться в обрезке оно не должно.
    for a in s["broken_agents"]:
        print(f"          {a}: файл сдан, но не выжила ни одна строка — строки этого "
              f"агента НЕ сняты с карты; посмотрите его файл в _rejected/")
    for i in s["held_entities"]:
        print(f"          сущность '{i}' больше не заявлена, но на неё ссылается связь "
              f"молчавшего агента — оставлена на карте")
    for w in s["warnings"][:20]:
        print("          ", w)
    if s["rejects_dir"]:
        print(f"          отказы -> {s['rejects_dir']} (копия для человека)")
    fb = s.get("feedback") or {}
    if fb:
        print(f"[отказы]  реестр: новых {fb.get('new', 0)}, повторно прислано "
              f"{fb.get('repeated', 0)}, снято исправлением {fb.get('resolved', 0)}, "
              f"открыто {fb.get('open', 0)}")
        for name in fb.get("queued") or []:
            print(f"          отклонённая сущность '{name}' поставлена в очередь "
                  f"кандидатов — отказ по сущности иначе не доставить")
        for name, eid in fb.get("on_map") or []:
            print(f"          кандидат '{name}' уже на карте как '{eid}'")
        print("          разбор: tools/queue_review.py · проверка: "
              "tools/feedback_check.py")
    m = s["membership"]
    print(f"[членство] проходят применимые проверки {m['passed']} из "
          f"{m['passed'] + m['failed']}; проверки "
          f"{'ВКЛЮЧЕНЫ (' + m['on_fail'] + ')' if m['enforced'] else 'выключены'}")
    print(f"          досье отработано у {m['covered']}; ещё не покрыто "
          f"{len(m['pending'])} — к ним {', '.join(m['coverage_gated'])} не применяются")
    for k, v in m["fails"].items():
        if v:
            print(f"          не проходят {k}: {len(v)}")
    if m.get("retired"):
        print(f"          СНЯТО ЧЛЕНСТВОМ: {len(m['retired'])}")
        for r in m["retired"][:20]:
            print(f"           снят {r['id']} — {r['failed']}")
    if m.get("held"):
        print(f"          удержаны ребром (не сняты, помечены): {len(m['held'])}")
        for r in m["held"][:8]:
            print(f"           {r['id']} — {r['failed']}, держит {r['held_by'].split('|')[0]}")
        if len(m["held"]) > 8:
            print(f"           …и ещё {len(m['held']) - 8}")
    print(f"          отчёт -> {m['path']}")
    if m.get("retired_path"):
        print(f"          ретирование -> {m['retired_path']}")

    v = nveco_verify.run(month, offline=offline, limit=verify_limit)
    if offline:
        print(f"[verify]  ПРОПУЩЕНО (offline) — {v['skipped']} ссылок не проверено")
    else:
        print(f"[verify]  {v['checked']} ссылок: {v['alive']} живых, {v['dead']} мёртвых, "
              f"{v['blocked']} заблокировано/пейволл")
    for u in v["dead_urls"][:10]:
        print("          МЁРТВАЯ", u)

    rc = nveco_reconcile.run(month)
    print(f"[сверка]  тир пересчитан относительно предмета: {rc['retiered']} "
          f"источников; стороны {rc['sidedness_mix']}")
    print(f"          профилей с собственной цитатой: {rc['self_sourced_profiles']} "
          f"из {rc['profiles']}")
    for d in rc["disputes"]:
        print(f"          СПОР {d['edge']}: утверждают {', '.join(d['claimed_by']) or '—'}, "
              f"опровергают {', '.join(d['counter_by']) or '—'}")

    sc = nveco_score.run(month)
    print(f"[score]   {sc['entities']} сущностей; статусы связей {sc['status_mix']}; "
          f"обрезано {sc['clamped']}; блёкнет {sc['stale']}")
    print("          топ критичности: " +
          ", ".join(f"{k}={c}" for k, c in sc["top"]))
    for line in sc["log"][:12]:
        print("          ", line)

    cy = nveco_cycles.run(month)
    print(f"[cycles]  {cy['cycles']} контуров {cy['by_type']}")
    for c in cy["detail"][:6]:
        print(f"           {c['id']} {c['type']}: {' -> '.join(c['path'])}")

    # второй проход оценки: теперь известны контуры, и гравитация их учитывает
    nveco_score.run(month)

    h = nveco_handoff.run(month)
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
        dest = Path(nveco.scope_cfg()["deliver_to"]).expanduser()
        if not dest.parent.is_dir():
            print(f"[deliver] ПРОПУЩЕНО — нет директории {dest.parent}")
        else:
            shutil.copy(h["path"], dest)
            print(f"[deliver] -> {dest}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    month = args[0] if args else nveco.current_month()
    limit = None
    for i, a in enumerate(sys.argv[1:]):
        if a.startswith("--month="):
            month = a.split("=", 1)[1]
        elif a.startswith("--verify-limit="):
            limit = int(a.split("=", 1)[1])
        elif a == "--verify-limit" and i + 2 <= len(sys.argv[1:]):
            limit = int(sys.argv[i + 2])
    # --skip-agents принимается ради симметрии с run_month.py: агентский слой и так
    # отрабатывает вне этого скрипта, флаг документирует намерение.
    sys.exit(main(month, do_deliver="--deliver" in sys.argv,
                  offline="--offline" in sys.argv, verify_limit=limit))
