"""Обратная связь конвейера: отказы и очередь кандидатов, которые нельзя не прочитать.

Этот модуль заведён Фазой 2 после того, как Фаза 0 нашла улику. Агент `nveco-silicon`
называл `Carl Zeiss SMT` начиная с 2026-08. Правило двух шагов выбрасывало его каждым
прогоном, писало причину в `runs/2026-08/_rejected/nveco-silicon.csv`, файл лежал в
репозитории закоммиченным — и не был прочитан ни разу. Строка «отказы возвращаются
агенту следующим прогоном» стояла в брифах и в докстроке `nveco_ingest`. Механика
писала исправно; не работала ДОСТАВКА.

Разбор, почему именно (полностью — в журнале Фазы 2, §«Мёртвая петля»):

1. **Отказ жил один прогон.** `nveco_ingest` чистит `_rejected/` перед записью нового
   набора. Между двумя ingest'ами одного месяца прошлый список исчезал.
2. **Путь в брифе не совпадал с путём записи.** `agents/nveco-CONTEXT.md` §10 посылает
   агента в `runs/<ПРОШЛЫЙ месяц>/_rejected/`, ingest пишет в `runs/<ТЕКУЩИЙ>/`.
3. **У слоевых агентов вообще нет пакетчика.** `make_dossier_batches.py` собирает
   контекст досье, `make_research_batches.py` — недельному конвейеру. Восьми
   `nveco-*` не собирает никто, и «вернётся агенту» означало «агент сам сходит и
   откроет файл».
4. **Отказ ПО СУЩНОСТИ доставить было нечем.** Пакет собирается обходом сущностей
   базы; отклонённой сущности в базе по определению нет, поэтому её отказ не мог
   попасть ни в один пакет — ни тогда, ни сейчас, ни в будущем.
5. **Никто не проверял, что отказ прочитан.** Ни одной проверки на «строка лежит N
   прогонов и не решена» не существовало.

Против каждой причины здесь стоит своё:

1. Отказ живёт в БД (`nveco_rejection`), пока не снят исправлением или не решён явно.
2. Путь один: база. CSV остаётся человеку, машина читает таблицу.
3. Отказы по сущностям автоматически становятся строками очереди кандидатов
   (`origin: rejection`) — то есть попадают в тот канал, у которого потребитель есть.
4. `subject_id`/`subject_name` — отдельные колонки, и пакетчик отдаёт отказы, чей
   предмет на карту не попал, ОТДЕЛЬНЫМ списком, а не внутри пакета узла.
5. `tools/feedback_check.py` роняет прогон, когда строка висит дольше порога.

Правило, которое из этого следует и которое стоит держать в голове при чтении:
**молчание об отказе — это не решение.** Строка либо перестала приходить (исправлена),
либо получила `decision` с причиной. Третьего состояния нет.
"""

import hashlib
import re

# Сколько прогонов отказ вправе провисеть открытым, прежде чем это станет ошибкой
# конвейера, а не свойством данных. Единица — «его увидели и не решили»; двойка —
# «его увидели дважды и не решили», и вот это уже та самая мёртвая петля.
MAX_OPEN_TIMES = 2

_KV = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=")


def parse_row(blob: str) -> dict:
    """Строка отказа `k=v; k=v` обратно в словарь.

    Значения содержат и точки с запятой, и знаки равенства (цитаты, URL), поэтому
    режем по ПОЗИЦИЯМ ключей, а не split(';'). Ключ — то, что стоит слева от '='
    сразу после начала строки или после '; '.
    """
    out, pos = {}, []
    for m in _KV.finditer(blob or ""):
        s = m.start()
        if s == 0 or blob[max(0, s - 2):s] == "; ":
            pos.append((m.group(1), m.end()))
    for i, (k, v_at) in enumerate(pos):
        end = len(blob) if i + 1 == len(pos) else pos[i + 1][1] - len(pos[i + 1][0]) - 3
        out[k] = blob[v_at:end].strip()
    return out


def subject_of(fname: str, blob: str) -> tuple:
    """(вид предмета, id, имя) отклонённой строки.

    Имя нужно ровно затем, ради чего заведён модуль: у отклонённой СУЩНОСТИ id на
    карте нет и не будет, пока её не впустят, — и найти её потом можно только по
    имени, которым её назвал агент.
    """
    r = parse_row(blob)
    if fname == "entities.csv":
        return "entity", r.get("id") or None, r.get("name") or None
    if fname == "edges.csv":
        eid = r.get("edge")
        if not eid and r.get("source") and r.get("target") and r.get("type"):
            eid = f"{r['source']}__{r['target']}__{r['type']}"
        return "edge", eid or None, None
    if fname == "sources.csv":
        return "source", r.get("owner_key") or None, (r.get("title") or None)
    return "?", None, None


def _key(agent: str, fname: str, subject: str, reason: str) -> str:
    """Ключ отказа БЕЗ номера строки: строка, переехавшая на две позиции вниз, —
    тот же самый отказ, и считать его новым значило бы обнулять счётчик повторов
    каждой правкой соседней строки."""
    h = hashlib.sha1(f"{agent}|{fname}|{subject}|{reason}".encode()).hexdigest()[:16]
    return h


def record_rejections(con, month: str, rejected: dict) -> dict:
    """Записать отказы прогона в реестр и снять те, что перестали приходить.

    `rejected` — {agent: [{file, line, reason, row}, …]} прямо из nveco_ingest.
    Возвращает сводку: сколько новых, сколько повторились, сколько снялось.
    """
    seen = set()
    fresh = repeat = 0
    for agent, rows in (rejected or {}).items():
        for r in rows:
            fname = r.get("file") or "?"
            blob = r.get("row") or ""
            kind, sid, sname = subject_of(fname, blob)
            k = _key(agent, fname, sid or sname or blob[:80], r.get("reason") or "")
            seen.add(k)
            prev = con.execute("SELECT times, status FROM nveco_rejection WHERE key=?",
                               (k,)).fetchone()
            if prev:
                # Отказ, который уже решали, но пришёл снова, — это НЕ повтор решения:
                # агент прислал ту же строку, ничего не исправив. Строка снова
                # открывается, и счётчик повторов растёт.
                #
                # Единственное исключение — `dismissed`. Оно означает не «починим
                # потом», а «эта строка обязана отвергаться всегда»: так помечена
                # заглушка `googl-placeholder`, которая стоит в выдаче агента с пилота
                # и каждым прогоном доказывает, что путь отказа жив. Переоткрывать
                # такую строку значило бы требовать чинить работающую проверку.
                # Повторы считаются и у неё — решение видно, а не спрятано.
                if prev["status"] == "dismissed":
                    con.execute("""UPDATE nveco_rejection SET last_seen=?, times=times+1,
                                     row=?, agent=?, file=? WHERE key=?""",
                                (month, blob, agent, fname, k))
                else:
                    con.execute("""UPDATE nveco_rejection SET last_seen=?, times=times+1,
                                     status='open', row=?, agent=?, file=?
                                   WHERE key=?""",
                                (month, blob, agent, fname, k))
                repeat += 1
            else:
                con.execute("""INSERT INTO nveco_rejection
                                 (key, agent, file, reason, row, subject_kind,
                                  subject_id, subject_name, first_seen, last_seen)
                               VALUES (?,?,?,?,?,?,?,?,?,?)""",
                            (k, agent, fname, r.get("reason") or "", blob,
                             kind, sid, sname, month, month))
                fresh += 1
    # Строка, которой в этом прогоне не было, — исправлена или отозвана. Это
    # единственный способ закрыть отказ БЕЗ решения, и он честный: причина отказа
    # исчезла вместе со строкой.
    closed = 0
    for row in con.execute("SELECT key FROM nveco_rejection WHERE status='open'").fetchall():
        if row["key"] not in seen:
            con.execute("""UPDATE nveco_rejection SET status='resolved', decision=?,
                             decided_month=? WHERE key=?""",
                        ("строка больше не приходит от агента — исправлена или отозвана",
                         month, row["key"]))
            closed += 1
    return {"new": fresh, "repeated": repeat, "resolved": closed,
            "open": con.execute("SELECT COUNT(*) c FROM nveco_rejection "
                                "WHERE status='open'").fetchone()["c"]}


def _cand_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")


def record_candidates(con, month: str, rows) -> dict:
    """Строки очереди кандидатов — в базу. Идемпотентно по нормализованному имени."""
    fresh = repeat = 0
    for c in rows or []:
        k = _cand_key(c.get("name"))
        if not k:
            continue
        prev = con.execute("SELECT status FROM nveco_candidate WHERE key=?", (k,)).fetchone()
        if prev:
            con.execute("""UPDATE nveco_candidate SET last_seen=?, times=times+1
                           WHERE key=?""", (month, k))
            repeat += 1
        else:
            con.execute("""INSERT INTO nveco_candidate
                             (key, name, named_by, why, url, quote, first_seen,
                              last_seen, origin)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                        (k, c.get("name"), c.get("named_by") or "?", c.get("why"),
                         c.get("url"), c.get("quote"), month, month,
                         c.get("origin") or "dossier"))
            fresh += 1
    return {"new": fresh, "repeated": repeat}


def enqueue_rejected_entities(con, month: str) -> list:
    """Отклонённая СУЩНОСТЬ становится кандидатом.

    Это и есть недостающее звено. Отказ по сущности нельзя доставить пакетом узла —
    узла нет; но кандидат у очереди есть, и очередь обязана быть разобрана целиком.
    Так `Carl Zeiss SMT` попал бы под рассмотрение в тот же месяц, в который его
    впервые выбросили, а не через год и не по чужой находке.
    """
    added = []
    for r in con.execute("""SELECT * FROM nveco_rejection
                            WHERE status='open' AND subject_kind='entity'"""):
        name = r["subject_name"] or r["subject_id"]
        if not name:
            continue
        k = _cand_key(name)
        if con.execute("SELECT 1 FROM nveco_candidate WHERE key=?", (k,)).fetchone():
            continue
        con.execute("""INSERT INTO nveco_candidate
                         (key, name, named_by, why, url, quote, first_seen, last_seen,
                          origin)
                       VALUES (?,?,?,?,?,?,?,?, 'rejection')""",
                    (k, name, f"_rejected/{r['agent']}",
                     f"отклонена загрузкой: {r['reason']}", "", "", month, month))
        con.execute("UPDATE nveco_rejection SET status='queued', decision=?, "
                    "decided_month=? WHERE key=?",
                    ("предмет отказа поставлен в очередь кандидатов", month, r["key"]))
        added.append(name)
    return added


def mark_on_map(con, month: str) -> list:
    """Кандидат, который уже на карте, — не находка очереди, а её нормальная работа.

    Досье называет всё, чего не видит в своём пакете; сверку со списком карты делает
    очередь. Строка получает решение `on_map` с id — то есть РЕШЕНИЕ, а не молчание.
    """
    ents = {r["id"]: r["name"] for r in con.execute("SELECT id, name FROM nveco_entity")}
    by_name = {_cand_key(v): k for k, v in ents.items()}
    by_id = {_cand_key(k): k for k in ents}
    hit = []
    for r in con.execute("SELECT key, name FROM nveco_candidate WHERE status='open'"):
        eid = by_name.get(r["key"]) or by_id.get(r["key"])
        if eid:
            con.execute("""UPDATE nveco_candidate SET status='on_map', decision=?,
                             decided_month=?, entity_id=? WHERE key=?""",
                        (f"уже на карте как '{eid}'", month, eid, r["key"]))
            hit.append((r["name"], eid))
    return hit


def decide_candidate(con, name: str, status: str, reason: str, month: str,
                     entity_id: str = None) -> bool:
    k = _cand_key(name)
    cur = con.execute("SELECT 1 FROM nveco_candidate WHERE key=?", (k,)).fetchone()
    if not cur:
        return False
    con.execute("""UPDATE nveco_candidate SET status=?, decision=?, decided_month=?,
                     entity_id=? WHERE key=?""", (status, reason, month, entity_id, k))
    return True


def decide_rejection(con, key: str, status: str, reason: str, month: str) -> bool:
    cur = con.execute("SELECT 1 FROM nveco_rejection WHERE key=?", (key,)).fetchone()
    if not cur:
        return False
    con.execute("""UPDATE nveco_rejection SET status=?, decision=?, decided_month=?
                   WHERE key=?""", (status, reason, month, key))
    return True


def audit(con) -> dict:
    """Что не потреблено. Пустой ответ — единственный приемлемый.

    Разделяет два состояния, которые легко спутать: «строка новая, её ещё не видели»
    и «строка висит второй прогон подряд». Первое — нормальная работа, второе — та
    самая мёртвая петля, ради которой модуль написан.
    """
    stale_rej = [dict(r) for r in con.execute(
        f"""SELECT key, agent, file, reason, subject_kind, subject_id, subject_name,
                   first_seen, last_seen, times
            FROM nveco_rejection
            WHERE status='open' AND times > {MAX_OPEN_TIMES}
            ORDER BY times DESC, first_seen""")]
    open_rej = [dict(r) for r in con.execute(
        """SELECT key, agent, file, reason, subject_kind, subject_id, subject_name,
                  first_seen, times
           FROM nveco_rejection WHERE status='open' ORDER BY first_seen""")]
    open_cand = [dict(r) for r in con.execute(
        """SELECT key, name, named_by, first_seen, times, origin
           FROM nveco_candidate WHERE status='open' ORDER BY first_seen, name""")]
    return {"open_rejections": open_rej, "stale_rejections": stale_rej,
            "open_candidates": open_cand,
            "ok": not stale_rej and not open_cand}


def rejections_for(con, ids) -> dict:
    """Отказы, привязанные к сущностям пакета: {entity_id: [строки]}."""
    want = set(ids)
    out = {}
    for r in con.execute("""SELECT * FROM nveco_rejection WHERE status IN ('open','queued')"""):
        for cand in (r["subject_id"], ):
            if not cand:
                continue
            # Отказ по РЕБРУ касается обоих его концов: id ребра — source__target__type.
            parts = cand.split("__") if r["subject_kind"] == "edge" else [cand]
            for p in parts:
                if p in want:
                    out.setdefault(p, []).append(
                        {"agent": r["agent"], "file": r["file"],
                         "reason": r["reason"], "row": r["row"][:200],
                         "times": r["times"], "first_seen": r["first_seen"]})
    return out


def offmap_rejections(con) -> list:
    """Отказы, чей предмет на карту НЕ попал.

    Ровно тот класс, который прежняя механика доставить не могла: пакет собирается
    обходом сущностей базы, а этих сущностей в базе нет. Отдаются пакетчиком отдельным
    списком — вне пакета, но в том же файле, который агент открывает.
    """
    ids = {r["id"] for r in con.execute("SELECT id FROM nveco_entity")}
    out = []
    for r in con.execute("""SELECT * FROM nveco_rejection
                            WHERE status IN ('open','queued') ORDER BY first_seen"""):
        sid = r["subject_id"]
        if r["subject_kind"] == "edge" and sid:
            if all(p in ids for p in sid.split("__")[:2]):
                continue
        elif sid in ids:
            continue
        out.append({"key": r["key"], "agent": r["agent"], "file": r["file"],
                    "reason": r["reason"], "kind": r["subject_kind"],
                    "id": sid, "name": r["subject_name"],
                    "first_seen": r["first_seen"], "times": r["times"],
                    "row": r["row"][:200]})
    return out
