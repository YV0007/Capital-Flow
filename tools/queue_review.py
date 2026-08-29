"""Разбор очереди кандидатов: каждая строка получает решение с причиной.

Очередь — это то, что карта услышала от самой себя. Досье узла называет всех, кого
видит своими поставщиками, клиентами и конкурентами; те из них, кого на карте нет,
становятся строкой очереди. Правило Фазы 2 простое и не имеет исключений:

    **очередь разбирается ЦЕЛИКОМ. Каждая строка либо принята, либо отклонена
    С ПРИЧИНОЙ. Молчание решением не является.**

Правило пишется так резко потому, что противоположное уже случилось. Отказ по
`Carl Zeiss SMT` лежал в репозитории закоммиченным год и был прочитан только тогда,
когда кампания пересчитала данные руками. Строка без решения выглядит одинаково с
любой стороны — и когда её рассматривают, и когда о ней забыли.

Приём кандидата — это НЕ заведение сущности. Сущности заводят агенты своими
`entities.csv`; очередь лишь говорит, кого исследовать следующим циклом. Поэтому
`accepted` означает «взят в работу», а не «уже на карте».

Реестр отказов — вторая половина той же петли, и решается он здесь же: у отказа тоже
не бывает состояния «посмотрели и промолчали».

Usage:
  python tools/queue_review.py                       # состояние очереди
  python tools/queue_review.py --decide "Micron" --status on_map --why "…" [--id micron]
  python tools/queue_review.py --from decisions.csv  # пакетно: name,status,why,id
  python tools/queue_review.py --export <YYYY-MM>    # runs/<месяц>/_queue/decisions.csv
  python tools/queue_review.py --rejections          # открытые отказы с ключами
  python tools/queue_review.py --rejection <ключ> --status dismissed --why "…"
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db, nveco, nveco_feedback  # noqa: E402

STATUSES = ("accepted", "rejected", "on_map")
# `dismissed` — «эта строка обязана отвергаться всегда» (заглушка, проверяющая, что
# путь отказа жив). `admitted` — «предмет отказа впущен на карту другим правилом».
REJ_STATUSES = ("dismissed", "admitted", "resolved")


def show(con) -> int:
    rows = [dict(r) for r in con.execute(
        "SELECT * FROM nveco_candidate ORDER BY status, first_seen, name")]
    if not rows:
        print("очередь пуста")
        return 0
    for r in rows:
        mark = {"open": "  ?", "accepted": "  +", "rejected": "  -",
                "on_map": "  ="}.get(r["status"], "  ?")
        print(f"{mark} {r['name']:<34} {r['status']:<9} назвал {r['named_by']:<18} "
              f"с {r['first_seen']} ({r['origin']})")
        if r["decision"]:
            print(f"      решение: {r['decision']}")
        elif r["why"]:
            print(f"      повод:   {r['why']}")
    open_n = sum(1 for r in rows if r["status"] == "open")
    print(f"\nвсего {len(rows)}, без решения {open_n}")
    return open_n


def export(con, month: str) -> str:
    out = db.RUNS_DIR / month / "_queue"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "decisions.csv"
    cols = ["name", "status", "decision", "entity_id", "named_by", "why", "url",
            "quote", "first_seen", "decided_month", "origin"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in con.execute("SELECT * FROM nveco_candidate ORDER BY name"):
            w.writerow({c: r[c] for c in cols})
    return str(path)


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

    if "--export" in argv:
        m = opt("--export") or month
        print(export(con, m))
        con.close()
        return 0

    src = opt("--from")
    if src:
        n = 0
        with open(src, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                st = (row.get("status") or "").strip()
                if st not in STATUSES:
                    print(f"пропущено '{row.get('name')}': status '{st}' — "
                          f"только {', '.join(STATUSES)}")
                    continue
                why = (row.get("decision") or row.get("why") or "").strip()
                if not why:
                    print(f"пропущено '{row.get('name')}': решение без причины")
                    continue
                if nveco_feedback.decide_candidate(
                        con, row["name"], st, why, month,
                        (row.get("entity_id") or "").strip() or None):
                    n += 1
                else:
                    print(f"нет в очереди: {row.get('name')}")
        con.commit()
        print(f"решено {n}")
        con.close()
        return 0

    name = opt("--decide")
    if name:
        st = opt("--status")
        why = opt("--why")
        if st not in STATUSES or not why:
            print(f"нужны --status ({'|'.join(STATUSES)}) и --why «причина»")
            con.close()
            return 2
        ok = nveco_feedback.decide_candidate(con, name, st, why, month, opt("--id"))
        con.commit()
        print(f"{name}: {st}" if ok else f"нет в очереди: {name}")
        con.close()
        return 0 if ok else 1

    key = opt("--rejection")
    if key:
        st = opt("--status")
        why = opt("--why")
        if st not in REJ_STATUSES or not why:
            print(f"нужны --status ({'|'.join(REJ_STATUSES)}) и --why «причина»")
            con.close()
            return 2
        ok = nveco_feedback.decide_rejection(con, key, st, why, month)
        con.commit()
        print(f"{key}: {st}" if ok else f"нет такого отказа: {key}")
        con.close()
        return 0 if ok else 1

    if "--rejections" in argv:
        n = 0
        for r in con.execute("SELECT * FROM nveco_rejection ORDER BY status, first_seen"):
            n += r["status"] == "open"
            print(f"  [{r['status']:<9}] {r['key']}  {r['agent']}/{r['file']}  "
                  f"{r['subject_kind']} {r['subject_id'] or r['subject_name'] or '?'}  "
                  f"x{r['times']} с {r['first_seen']}")
            print(f"      причина: {r['reason']}")
            if r["decision"]:
                print(f"      решение: {r['decision']}")
        print(f"\nоткрытых отказов: {n}")
        con.close()
        return 1 if n else 0

    open_n = show(con)
    con.close()
    return 1 if open_n else 0


if __name__ == "__main__":
    sys.exit(main())
