"""Проверка, что обратная связь ПОТРЕБЛЯЕТСЯ, а не копится.

Заведена Фазой 2. Повод — `Carl Zeiss SMT`: агент называл его, загрузка отклоняла,
причина писалась в файл, файл лежал закоммиченным, и никто не был обязан его открыть.
Дефект был не в механике записи, а в отсутствии проверки на чтение. Механику, у
которой нет проверки потребления, нельзя считать работающей: она выглядит живой ровно
до того дня, когда кто-нибудь пересчитает данные руками.

Что проверяется:

  1. **Отказ не висит открытым дольше порога.** `nveco_feedback.MAX_OPEN_TIMES`
     прогонов подряд — это уже не «его ещё не успели рассмотреть», а «его смотрят и
     не решают». Такая строка роняет проверку.
  2. **Очередь кандидатов разобрана.** Каждая строка либо принята, либо отклонена
     с причиной, либо помечена «уже на карте». Открытая строка — незакрытая работа.
  3. **Охота за пропущенными связями разобрана.** Задание, которое видели дважды и
     не решили, — та же мёртвая петля, только про рёбра, а не про отказы.
  4. **Реестр вообще заполняется.** Прогон, в котором ingest отверг строки, а в
     реестре не прибавилось ничего, означает, что запись отвалилась, — и это
     страшнее любого отдельного отказа.

Usage:
  python tools/feedback_check.py [--json] [--quiet]

Код возврата 1, когда есть что чинить, — чтобы прогон и CI могли на это опереться.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import nveco, nveco_feedback, nveco_gaps  # noqa: E402


def run() -> dict:
    con = nveco.connect()
    a = nveco_feedback.audit(con)
    g = nveco_gaps.audit(con)
    a["stale_gaps"] = g["stale_gaps"]
    a["open_gaps"] = g["open"]
    a["ok"] = a["ok"] and not g["stale_gaps"]
    totals = {
        "rejections": con.execute("SELECT COUNT(*) c FROM nveco_rejection").fetchone()["c"],
        "candidates": con.execute("SELECT COUNT(*) c FROM nveco_candidate").fetchone()["c"],
    }
    by_status = {}
    for tbl in ("nveco_rejection", "nveco_candidate"):
        by_status[tbl] = {r["status"]: r["c"] for r in con.execute(
            f"SELECT status, COUNT(*) c FROM {tbl} GROUP BY status")}
    # Реестр, оставшийся пустым при непустых прогонах, — отдельная поломка: она
    # выглядит как «отказов нет», а означает «запись отвалилась».
    ran = con.execute("SELECT COALESCE(SUM(rejected),0) c FROM nveco_run").fetchone()["c"]
    con.close()
    silent = ran > 0 and totals["rejections"] == 0
    a.update({"totals": totals, "by_status": by_status,
              "rejected_rows_in_runs": ran, "ledger_silent": silent})
    a["ok"] = a["ok"] and not silent
    return a


def main() -> int:
    out = run()
    if "--json" in sys.argv:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["ok"] else 1
    q = "--quiet" in sys.argv
    if out["ledger_silent"]:
        print("ОШИБКА: прогоны отвергли строки, а реестр отказов пуст — запись "
              "обратной связи не работает")
    for r in out["stale_rejections"]:
        print(f"ОТКАЗ ВИСИТ {r['times']} прогона: {r['agent']}/{r['file']} "
              f"[{r['subject_kind']} {r['subject_id'] or r['subject_name'] or '?'}] "
              f"с {r['first_seen']} — {r['reason']}")
    for r in out["stale_gaps"]:
        print(f"ОХОТА ВИСИТ {r['times']} прогона: {r['subject_id']} — "
              f"{r['why']}, ждём {r['expected']} от [{r['cp_class']}] (с {r['first_seen']})")
    for c in out["open_candidates"]:
        print(f"КАНДИДАТ БЕЗ РЕШЕНИЯ: {c['name']} (назвал {c['named_by']}, "
              f"с {c['first_seen']}, {c['origin']})")
    if not q:
        print(f"реестр отказов: {out['by_status']['nveco_rejection']}")
        print(f"очередь кандидатов: {out['by_status']['nveco_candidate']}")
        print(f"открытых отказов {len(out['open_rejections'])}, из них просроченных "
              f"{len(out['stale_rejections'])}; кандидатов без решения "
              f"{len(out['open_candidates'])}; заданий охоты открыто "
              f"{out['open_gaps']}, из них просроченных {len(out['stale_gaps'])}")
    print("обратная связь потребляется" if out["ok"] else
          "ОБРАТНАЯ СВЯЗЬ НЕ ПОТРЕБЛЯЕТСЯ")
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
