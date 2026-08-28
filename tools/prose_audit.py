"""Проверка прозы карты экосистемы против правил из хендоффа 2026-08-28.

Зачем инструмент, а не глазами. Правок нужно около полутора тысяч на двух
языках. Без счётчика «сделано» превращается в ощущение, а регресс в следующем
месяце никто не заметит. Здесь каждое правило считается, и его можно поставить
воротами в конвейер.

    python tools/prose_audit.py            # отчёт по поставляемому файлу
    python tools/prose_audit.py --strict   # код 1, если хоть одно правило нарушено

Что НЕ проверяется машиной: «заканчивается на то, почему связь важна» (п.6
хендоффа) — это суждение, и притворяться, что регулярное выражение его ловит,
хуже, чем честно оставить человеку.
"""

import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAYLOAD = ROOT / "handoff" / "ai_ecosystem_network.json"

# ── правило 2: запрещённая лексика ───────────────────────────────────────────
# «якорь» — карта больше не якорная, у неё 27 равноправных пивотов, поэтому
# слово и жаргон, и фактически неверно. Остальные три — категория вместо факта.
BANNED_RU = {
    "якорь": r"якор[ьяюеё]\w*",
    "ров":   r"\bров\b|\bрва\b|\bрву\b|\bровом\b",
    "узкое место": r"узк\w+\s+мест\w+",
    "движок": r"движ[ко]\w*",
}
BANNED_EN = {
    "anchor": r"\banchors?\b|\banchor's\b",
    "moat": r"\bmoats?\b",
    "bottleneck": r"\bbottlenecks?\b",
    "engine": r"\bengines?\b",
}

# ── правило 3: голый порядковый номер без названного ориентира ───────────────
ORDINAL_RU = r"\b(перв\w+|втор\w+|трет\w+|четвёрт\w+|пят\w+)\b"
ORDINAL_EN = r"\b(first|second|third|fourth|fifth)\b"

NUM = r"\d"


def _txt(v, lang):
    """Поле прозы: пара {ru,en} либо голая строка (контракт допускает обе)."""
    if isinstance(v, dict):
        return v.get(lang) or ""
    return v or "" if lang == "ru" else ""


def load(path=PAYLOAD):
    return json.loads(Path(path).read_text())


def prose_fields(d):
    """(путь, значение) по КАЖДОМУ пользовательскому полю прозы.

    Цитаты источников сюда не входят намеренно: они на языке своего документа
    и правилам стиля карты не подчиняются.
    """
    out = []
    for e in d["entities"]:
        i = e["id"]
        for f in ("oneLiner", "whyIrreplaceable", "whatBreaksIt"):
            if e.get(f) is not None:
                out.append((f"entities[{i}].{f}", e[f]))
        for k, v in (e.get("criticalityWhy") or {}).items():
            if v is not None:
                out.append((f"entities[{i}].criticalityWhy.{k}", v))
        if (e.get("risk") or {}).get("note"):
            out.append((f"entities[{i}].risk.note", e["risk"]["note"]))
    for x in d["edges"]:
        i = x["id"]
        for f in ("note", "detail"):
            if x.get(f) is not None:
                out.append((f"edges[{i}].{f}", x[f]))
        if (x.get("risk") or {}).get("mitigation"):
            out.append((f"edges[{i}].risk.mitigation", x["risk"]["mitigation"]))
    return out


def third_party_subjects(d):
    """Заметки, где НИ ОДИН конец связи не назван, но названа чужая компания.

    Приближение, и намеренно консервативное: настоящий разбор подлежащего
    требует синтаксиса. Правило хендоффа — «подлежащее это один из двух концов».
    Если ни один конец в тексте не упомянут, а третья сторона упомянута, заметка
    почти наверняка про кого-то другого. Обратное не ловится, и это честнее
    считать недоучётом, чем выдумывать точность.
    """
    names = {}
    for e in d["entities"]:
        n = e["name"]
        n = n.get("ru") if isinstance(n, dict) else n
        names[e["id"]] = n
    hits = []
    for x in d["edges"]:
        note = _txt(x.get("note"), "ru")
        if not note:
            continue
        low = note.lower()
        ends = [names.get(x["source"], ""), names.get(x["target"], "")]
        if any(nm and nm.lower() in low for nm in ends):
            continue                      # хотя бы один конец назван — ок
        others = [nm for eid, nm in names.items()
                  if eid not in (x["source"], x["target"])
                  and nm and len(nm) > 3 and nm.lower() in low]
        if others:
            hits.append((x["id"], note, others[:3]))
    return hits


def audit(d):
    fields = prose_fields(d)
    r = {"banned": [], "ordinals": [], "fields": len(fields)}

    for path, val in fields:
        ru, en = _txt(val, "ru"), _txt(val, "en")
        for word, pat in BANNED_RU.items():
            if re.search(pat, ru, re.I):
                r["banned"].append((path, "ru", word))
        for word, pat in BANNED_EN.items():
            if re.search(pat, en, re.I):
                r["banned"].append((path, "en", word))
        # Порядковый допустим, только если рядом названа сущность (заглавная
        # буква или латиница) — «второй после NVIDIA» проходит, голый — нет.
        for txt, pat, lang in ((ru, ORDINAL_RU, "ru"), (en, ORDINAL_EN, "en")):
            if re.search(pat, txt, re.I) and not re.search(r"[A-Z][A-Za-z]{2,}", txt):
                r["ordinals"].append((path, lang))

    notes = [x for x in d["edges"] if x.get("note")]
    r["notes"] = len(notes)
    r["notes_with_number"] = sum(1 for x in notes if re.search(NUM, _txt(x["note"], "ru")))
    lens = [len(_txt(x["note"], "ru")) for x in notes]
    r["median_len"] = statistics.median(lens) if lens else 0
    r["third_party"] = third_party_subjects(d)
    r["detail"] = sum(1 for x in d["edges"] if x.get("detail"))
    r["edges"] = len(d["edges"])
    return r


def report(r) -> bool:
    print(f"полей прозы проверено: {r['fields']}\n")
    print("ПРАВИЛО 1 — подлежащее заметки это один из концов связи")
    print(f"  заметок про третью сторону: {len(r['third_party'])}  (цель 0)")
    for eid, note, others in r["third_party"][:8]:
        print(f"    {eid:44} упомянуты: {', '.join(others)}")
    if len(r["third_party"]) > 8:
        print(f"    …и ещё {len(r['third_party']) - 8}")

    print("\nПРАВИЛО 2 — запрещённая лексика")
    by_word = {}
    for path, lang, word in r["banned"]:
        by_word.setdefault(word, []).append((path, lang))
    if not by_word:
        print("  чисто")
    for w, hits in sorted(by_word.items(), key=lambda i: -len(i[1])):
        print(f"  «{w}»: {len(hits)}")
        for p, l in hits[:3]:
            print(f"      {l}  {p}")

    print("\nПРАВИЛО 3 — голый порядковый без названного ориентира")
    print(f"  случаев: {len(r['ordinals'])}  (цель 0)")
    for p, l in r["ordinals"][:6]:
        print(f"      {l}  {p}")

    print("\nПРАВИЛО 4 — число в заметке")
    print(f"  {r['notes_with_number']} из {r['notes']} "
          f"({100 * r['notes_with_number'] // max(1, r['notes'])}%)")

    print("\nПРАВИЛО 5 — медиана длины заметки")
    print(f"  {r['median_len']:.0f} знаков (ориентир ~85, это НЕ пас на удлинение)")

    print("\nПРАВИЛО 7 — detail на сильных связях")
    print(f"  {r['detail']} из {r['edges']}")

    ok = not r["third_party"] and not r["banned"] and not r["ordinals"]
    print("\nИТОГ:", "все машинные правила выполнены" if ok else "есть нарушения")
    return ok


if __name__ == "__main__":
    path = PAYLOAD
    for a in sys.argv[1:]:
        if not a.startswith("--"):
            path = Path(a)
    ok = report(audit(load(path)))
    sys.exit(0 if ok or "--strict" not in sys.argv else 1)
