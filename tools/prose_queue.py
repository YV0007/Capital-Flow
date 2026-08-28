"""Очередь на переписывание прозы: что брать в следующий транш.

Проза карты переписывается НЕ одним проходом. 262 связи и 107 сущностей с
источником под каждой цифрой — это не один вызов, а повторяемая работа, и она
должна выглядеть как конвейерная стадия, а не как разовая правка.

Очередь отвечает на один вопрос: **что делать дальше и почему именно это.**
Сортирует по важности, показывает уже сделанное, и умеет отдать транш в том
виде, в каком его ждёт агент `nvnet-prose`.

    python tools/prose_queue.py                 # состояние очереди
    python tools/prose_queue.py --next 20       # следующий транш
    python tools/prose_queue.py --next 20 --csv # заготовки CSV под транш

Приоритет — не по алфавиту и не по номеру. Связь тем важнее, чем чаще на неё
наведут курсор: сначала сила связи, потом центральность её концов. Сущность —
по тем же двум мерам своего узла.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAYLOAD = ROOT / "handoff" / "ai_ecosystem_network.json"
OUT_DIR = ROOT / "runs"

# Проза считается ПЕРЕПИСАННОЙ, если проходит тест из трёх вопросов настолько,
# насколько его вообще можно проверить машиной: названы вещи (есть имя
# собственное) и есть проверяемое (число или дата). Третий вопрос — подмена —
# машиной не проверяется и остаётся на агенте.
NAMED = re.compile(r"[A-Z][A-Za-z0-9.\-]{2,}|[А-ЯЁ][а-яё]{3,}")
CHECKABLE = re.compile(r"\d")


def _t(v, lang="ru"):
    return (v.get(lang) if isinstance(v, dict) else v) or ""


def _done(text: str) -> bool:
    return bool(NAMED.search(text)) and bool(CHECKABLE.search(text))


def load():
    return json.loads(PAYLOAD.read_text())


def rank(d):
    """Связи и сущности в порядке «что важнее переписать»."""
    cen = {e["id"]: (e.get("centrality") or {}) for e in d["entities"]}

    def node_weight(i):
        c = cen.get(i, {})
        return (c.get("degree") or 0) + 400 * (c.get("pagerank") or 0)

    edges = []
    for x in d["edges"]:
        note = _t(x.get("note"))
        edges.append({
            "kind": "edge", "id": x["id"], "type": x["type"],
            "score": x.get("strength", 0) + node_weight(x["source"]) + node_weight(x["target"]),
            "note": note,
            "note_done": _done(note),
            "detail": bool(x.get("detail")),
            "quotes": len(x.get("evidence") or []),
        })
    ents = []
    for e in d["entities"]:
        ol = _t(e.get("oneLiner"))
        ents.append({
            "kind": "entity", "id": e["id"],
            "score": (e.get("criticality") or 0) + node_weight(e["id"]),
            "note": ol, "note_done": _done(ol),
            "detail": None, "quotes": len(e.get("sources") or []),
        })
    edges.sort(key=lambda r: -r["score"])
    ents.sort(key=lambda r: -r["score"])
    return edges, ents


def status(edges, ents):
    ed = sum(1 for r in edges if r["note_done"])
    en = sum(1 for r in ents if r["note_done"])
    det = sum(1 for r in edges if r["detail"])
    print("ОЧЕРЕДЬ ПЕРЕПИСЫВАНИЯ ПРОЗЫ\n")
    print(f"  заметки связей   {ed:>4} / {len(edges)}   переписано "
          f"({100 * ed // max(1, len(edges))}%)")
    print(f"  описания узлов   {en:>4} / {len(ents)}   переписано "
          f"({100 * en // max(1, len(ents))}%)")
    print(f"  detail на связях {det:>4} / {len(edges)}")
    print("\n«переписано» = названо имя собственное И есть проверяемое число или дата.")
    print("Тест на подмену (правило 3) машиной не проверяется — он на агенте.\n")
    todo = [r for r in edges if not r["note_done"]][:10]
    print("Следующие по важности связи:")
    for r in todo:
        flag = "" if r["quotes"] else "  ⚠ НЕТ ЦИТАТ — сначала источник"
        print(f"  {r['score']:>6.0f}  {r['id']:<46} {r['type']}{flag}")


def tranche(edges, ents, n):
    """Транш: связи и сущности вперемешку, по общей важности."""
    pending = [r for r in edges + ents if not r["note_done"]]
    pending.sort(key=lambda r: -r["score"])
    return pending[:n]


def write_csv(rows, month):
    d = OUT_DIR / month / "nvnet-prose"
    d.mkdir(parents=True, exist_ok=True)
    ed = [r for r in rows if r["kind"] == "edge"]
    en = [r for r in rows if r["kind"] == "entity"]
    # Заготовки идут с ПУСТЫМИ полями намеренно: пустая ячейка означает «не
    # трогай», поэтому забытая строка ничего не портит, а не затирает текст.
    with (d / "notes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["edge_id", "note_ru", "note_en"])
        for r in ed: w.writerow([r["id"], "", ""])
    with (d / "oneliners.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["entity_id", "one_liner_ru", "one_liner_en"])
        for r in en: w.writerow([r["id"], "", ""])
    with (d / "details.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["edge_id", "detail_ru", "detail_en"])
        for r in ed: w.writerow([r["id"], "", ""])
    src = d / "sources.csv"
    if not src.exists():
        with src.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["owner_kind", "owner_key", "tier", "type",
                                    "title", "url", "published", "quote", "confidence"])
    print(f"заготовки на {len(ed)} связей и {len(en)} сущностей -> {d}")
    print("Заполняйте только то, что действительно нашли: пустая ячейка = «не трогай».")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--next", type=int, metavar="N", help="показать следующий транш")
    ap.add_argument("--csv", action="store_true", help="записать заготовки CSV")
    ap.add_argument("--month", default=None)
    a = ap.parse_args()

    d = load()
    edges, ents = rank(d)
    if not a.next:
        status(edges, ents)
        return 0
    rows = tranche(edges, ents, a.next)
    month = a.month or d.get("asOf") or "2026-08"
    if a.csv:
        write_csv(rows, month)
        return 0
    print(f"ТРАНШ — {len(rows)} объектов по важности\n")
    for r in rows:
        q = f"{r['quotes']} цитат" if r["quotes"] else "⚠ НЕТ ЦИТАТ"
        print(f"  {r['score']:>6.0f}  {r['kind']:<6} {r['id']:<46} {q}")
        print(f"          сейчас: {r['note'][:96]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
