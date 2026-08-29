"""Разбор охоты за пропущенными связями: каждое задание получает ответ.

Третий канал обратной связи рядом с отказами (`tools/queue_review.py --rejections`)
и очередью кандидатов. Те двое отвечают на «что мы отвергли» и «какого УЗЛА у нас
нет». Этот — на вопрос, которого до Фазы 4 не задавал никто: **какого РЕБРА у нас
нет между узлами, которые оба уже на карте.**

Повод берётся из корпуса, а не из головы: узел сам раскрыл контрагента, не назвав
его, либо таксономия обещает ребро, которого у него нет ни с кем. Разбор — здесь.

    found      связь найдена и заведена. Обычно закрывается САМА: как только ребро
               появилось, повод исчезает, и следующий прогон снимает задание.
    not_found  искали и не нашли. Причина обязательна и уезжает в `nvnet_not_found`,
               чтобы ту же пару не переспрашивали каждый месяц. Отрицательный
               ответ — это ответ.
    dismissed  повод неверен: правило выпустило задание, которого не должно было.
               Это находка о ПРАВИЛЕ, и причина должна говорить, что в нём чинить.

Молчание четвёртым способом не является: `tools/feedback_check.py` роняет прогон,
пока задание висит открытым дольше порога.

Usage:
  python tools/gap_review.py                       # состояние охоты
  python tools/gap_review.py --open                # только нерешённые
  python tools/gap_review.py --decide <ключ> --status not_found --why "…"
  python tools/gap_review.py --from decisions.csv  # пакетно: key,status,why
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import nveco, nveco_gaps  # noqa: E402

STATUSES = ("found", "not_found", "dismissed")
MARK = {"open": "  ?", "found": "  +", "not_found": "  −", "dismissed": "  ×"}


def _not_found(con, row, reason: str, month: str):
    """Отрицательный ответ переезжает в nvnet_not_found — таблицу, которая для него
    и заведена. До Фазы 4 её писал только агент вручную; список пар, которые СТОИТ
    проверить, не составлял никто, поэтому в ней лежало пять строк за всю историю."""
    pid = f"gap:{row['key']}"
    con.execute("""INSERT OR REPLACE INTO nvnet_not_found
                     (pair_id, entity_a, entity_b, expected, reason)
                   VALUES (?,?,?,?,?)""",
                (pid, row["subject_id"],
                 row["counterparty"] or f"[{row['cp_class']}]",
                 row["expected"], reason))


def show(con, only_open: bool) -> int:
    q = "SELECT * FROM nveco_gap" + (" WHERE status='open'" if only_open else "")
    rows = [dict(r) for r in con.execute(q + " ORDER BY status, kind, subject_id")]
    if not rows:
        print("охота пуста")
        return 0
    for r in rows:
        print(f"{MARK.get(r['status'], '  ?')} {r['subject_id']:<20} "
              f"{r['expected']:<14} [{r['cp_class'] or r['counterparty']}]  "
              f"{r['status']:<10} x{r['times']}  {r['key']}")
        print(f"      повод:   {r['why']}")
        if r["quote"]:
            print(f"      цитата:  «{r['quote'][:88]}»")
        if r["decision"]:
            print(f"      решение: {r['decision']}")
    n = sum(1 for r in rows if r["status"] == "open")
    print(f"\nвсего {len(rows)}, без решения {n}")
    return n


def main() -> int:
    argv = sys.argv[1:]
    con = nveco.connect()
    month = nveco.current_month()

    def opt(name, default=None):
        for i, a in enumerate(argv):
            if a == name and i + 1 < len(argv):
                return argv[i + 1]
            if a.startswith(name + "="):
                return a.split("=", 1)[1]
        return default

    def apply(key, st, why):
        row = con.execute("SELECT * FROM nveco_gap WHERE key=?", (key,)).fetchone()
        if not row:
            print(f"нет такого задания: {key}")
            return False
        if st == "not_found":
            _not_found(con, row, why, month)
        return nveco_gaps.decide(con, key, st, why, month)

    src = opt("--from")
    if src:
        n = 0
        with open(src, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                st, why = (row.get("status") or "").strip(), (row.get("why") or "").strip()
                if st not in STATUSES or not why:
                    print(f"пропущено {row.get('key')}: нужен status из "
                          f"{'|'.join(STATUSES)} и непустая причина")
                    continue
                n += bool(apply(row["key"].strip(), st, why))
        con.commit()
        print(f"решено {n}")
        con.close()
        return 0

    key = opt("--decide")
    if key:
        st, why = opt("--status"), opt("--why")
        if st not in STATUSES or not why:
            print(f"нужны --status ({'|'.join(STATUSES)}) и --why «причина»")
            con.close()
            return 2
        ok = apply(key, st, why)
        con.commit()
        print(f"{key}: {st}" if ok else "не решено")
        con.close()
        return 0 if ok else 1

    n = show(con, "--open" in argv)
    con.close()
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
