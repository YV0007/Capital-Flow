"""Контекстный пакет для прозы: внутри чего пишется текст.

Свобода письма без контекста вырождается в две вещи сразу — в общие слова и в
противоречия соседним текстам. Поэтому исследователь получает пакет ДО того, как
садится писать, и пишет ВНУТРИ него.

Что кладётся на каждый объект:

  оба конца целиком      описание, сектор, слои, критичность с обоснованиями,
                         источники и уже имеющиеся факты
  окрестность            все ПРОЧИЕ связи каждого конца одной строкой — чтобы не
                         написать про tsmc→broadcom то, что уже сказано в tsmc→nvidia
  что уже сказано        нынешние note, detail, description этого объекта и соседей
  чем подкреплено        evidence объекта: на чём стоит нынешний текст и почему он
                         вышел таким
  словарь карты          как ЭТА карта называет типы связей, хребты, слои, секторы
  предмет карты          из config/nveco_scope.yaml

Очередь по умолчанию — не «всё подряд», а то, где текст заведомо плох:

  1. связи ядро↔ядро, где ВСЕ источники это один документ (текст писался вокруг
     одного дежурного абзаца);
  2. остальные связи ядро↔ядро с разбором;
  3. дальше вниз по критичности концов.

Usage:
  python tools/make_prose_batches.py <YYYY-MM> [--size 8] [--limit 40]
                                     [--queue one-doc|core|all] [--ids a__b__c,...]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db, nveco, nvnet  # noqa: E402

BATCH_SIZE = 8
DIR = "nvnet-prose-{:02d}"
PAYLOAD = Path("handoff/ai_ecosystem_network.json")


def _payload() -> dict:
    p = db.ROOT / PAYLOAD
    if not p.exists():
        raise SystemExit(f"нет {p} — сначала прогоните run_network.py")
    return json.loads(p.read_text())


def _one_line(x: str) -> str:
    return " ".join((x or "").split())


def _edge_line(x, ents) -> str:
    """Соседняя связь одной строкой: тип, второй конец, суть."""
    note = x.get("note")
    note = note.get("ru") if isinstance(note, dict) else note
    return (f"{x['id']} [{x['type']}, {x['status']}/{x.get('sidedness')}] "
            f"{_one_line(note)[:150]}")


def _entity_pack(e: dict, edges_by_ent: dict, ents: dict) -> dict:
    desc = e.get("description")
    return {
        "id": e["id"], "name": e["name"] if isinstance(e["name"], str)
        else e["name"].get("ru"),
        "type": e["type"], "role": e["role"], "sector": e.get("sector"),
        "layers": [l["layer"] for l in e.get("layers") or []],
        "criticality": e.get("criticality"),
        "criticalityFactors": e.get("criticalityFactors"),
        "criticalityWhy": {k: (v or {}).get("ru") if isinstance(v, dict) else v
                           for k, v in (e.get("criticalityWhy") or {}).items()},
        "oneLiner": (e.get("oneLiner") or {}).get("ru")
        if isinstance(e.get("oneLiner"), dict) else e.get("oneLiner"),
        "description_now": desc.get("ru") if isinstance(desc, dict) else desc,
        "revenueUsdB": e.get("revenueUsdB"), "geo": e.get("geo"),
        "ticker": e.get("ticker"), "founded": e.get("founded"),
        "sourcing": e.get("sourcing"),
        "sources": [{"tier": s["tier"], "url": s["url"], "quote": s["quote"],
                     "self": s.get("self")} for s in (e.get("sources") or [])],
        "facts_now": e.get("facts") or [],
        "neighbourhood": [_edge_line(x, ents) for x in edges_by_ent.get(e["id"], [])],
    }


def _edge_task(x: dict, ents: dict, edges_by_ent: dict) -> dict:
    a, b = ents[x["source"]], ents[x["target"]]
    note, detail = x.get("note"), x.get("detail")
    return {
        "kind": "edge", "id": x["id"], "type": x["type"], "spine": x["spine"],
        "direction": x["direction"], "status": x["status"],
        "sidedness": x.get("sidedness"), "claimedBy": x.get("claimedBy"),
        "strength": x.get("strength"), "risk": x.get("risk"),
        "techNode": x.get("techNode"), "formed": x.get("formed"),
        "note_now": note.get("ru") if isinstance(note, dict) else note,
        "detail_now": detail.get("ru") if isinstance(detail, dict) else detail,
        "evidence": [{"tier": s["tier"], "url": s["url"], "quote": s["quote"],
                      "self": s.get("self")} for s in (x.get("evidence") or [])],
        "counterEvidence": x.get("counterEvidence") or [],
        "facts_now": x.get("facts") or [],
        "one_document": len({s["url"] for s in (x.get("evidence") or [])}) == 1,
        "ends": {x["source"]: _entity_pack(a, edges_by_ent, ents),
                 x["target"]: _entity_pack(b, edges_by_ent, ents)},
        "что обязан ответить текст": nvnet.edge_types().get(x["type"], {}).get("label"),
    }


def _queue(payload: dict, mode: str) -> list:
    ents = {e["id"]: e for e in payload["entities"]}
    core = {e["id"] for e in payload["entities"] if e.get("core")}
    edges = payload["edges"]
    core_edges = [x for x in edges if x["source"] in core and x["target"] in core]

    def one_doc(x):
        return len({s["url"] for s in (x.get("evidence") or [])}) == 1

    def crit(x):
        return -((ents[x["source"]].get("criticality") or 0)
                 + (ents[x["target"]].get("criticality") or 0))

    if mode == "one-doc":
        rows = [x for x in core_edges if x.get("detail") and one_doc(x)]
    elif mode == "core":
        rows = [x for x in core_edges if x.get("detail")]
    else:
        rows = [x for x in edges if x.get("detail")]
    # Внутри очереди — по сумме критичности концов: дороже всего плохой текст там,
    # куда читатель смотрит в первую очередь.
    return sorted(rows, key=lambda x: (crit(x), x["id"]))


def run(month: str, size=BATCH_SIZE, limit=None, mode="one-doc", ids=None) -> dict:
    payload = _payload()
    ents = {e["id"]: e for e in payload["entities"]}
    edges_by_ent = {}
    for x in payload["edges"]:
        for end in (x["source"], x["target"]):
            edges_by_ent.setdefault(end, []).append(x)

    if ids:
        chosen = [x for x in payload["edges"] if x["id"] in set(ids)]
        missing = sorted(set(ids) - {x["id"] for x in chosen})
    else:
        chosen, missing = _queue(payload, mode), []
    if limit:
        chosen = chosen[:limit]
    if not chosen:
        raise SystemExit(f"очередь '{mode}' пуста — нечего переписывать")

    tasks = [_edge_task(x, ents, edges_by_ent) for x in chosen]
    vocab = {
        "предмет карты": payload["meta"]["scope"],
        "типы связей": {k: v.get("label") for k, v in nvnet.edge_types().items()},
        "хребты": {k: v.get("label") for k, v in
                   (payload.get("edgeSpines") or {}).items()} or None,
        "слои": {l["id"]: l.get("label") for l in payload.get("layers") or []},
    }
    written = []
    for n in range(0, len(tasks), size):
        batch = tasks[n:n + size]
        d = db.RUNS_DIR / month / DIR.format(n // size + 1)
        d.mkdir(parents=True, exist_ok=True)
        (d / "context.json").write_text(json.dumps({
            "month": month, "batch": n // size + 1, "queue": mode,
            "как читать": (
                "1) ПИШЕТЕ ВНУТРИ ПАКЕТА: всё, что утверждаете, лежит либо в вашем "
                "реестре фактов, либо здесь. Ничего из общей эрудиции. "
                "2) `one_document: true` значит, что нынешний текст написан вокруг "
                "ОДНОГО документа — это и есть причина, по которой связь в очереди. "
                "3) `neighbourhood` показывает, что уже сказано у соседей: не "
                "повторяйте и не противоречьте. "
                "4) `facts.csv` пишется ДО текста. Число, которого нет в реестре, "
                "движок из текста не пропустит. "
                "5) Тир, статус и стороны вы не пишете — их ставит движок."),
            "выход": "facts.csv, details.csv, notes.csv в этом каталоге; "
                     "правила и формат — agents/eco-prose.md",
            "словарь карты": vocab,
            "объекты": batch,
        }, ensure_ascii=False, indent=2) + "\n")
        written.append({"dir": str(d), "n": len(batch),
                        "ids": [t["id"] for t in batch]})
    return {"batches": written, "tasks": len(tasks), "missing": missing, "queue": mode}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    month = args[0] if args else nveco.current_month()
    size, limit, mode, ids = BATCH_SIZE, None, "one-doc", None
    for a in sys.argv[1:]:
        if a.startswith("--size="):
            size = int(a.split("=", 1)[1])
        elif a.startswith("--limit="):
            limit = int(a.split("=", 1)[1])
        elif a.startswith("--queue="):
            mode = a.split("=", 1)[1]
        elif a.startswith("--ids="):
            ids = [x.strip() for x in a.split("=", 1)[1].split(",") if x.strip()]
    out = run(month, size, limit, mode, ids)
    print(f"очередь {out['queue']}: {out['tasks']} объектов, "
          f"{len(out['batches'])} пакетов")
    for b in out["batches"]:
        print(f"  {b['dir']}  {b['n']}: {', '.join(b['ids'][:4])}"
              + (" …" if b["n"] > 4 else ""))
    if out["missing"]:
        print("  нет на карте:", ", ".join(out["missing"]))
