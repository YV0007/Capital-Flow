"""Охота за пропущенными связями: карта ищет то, чего у неё нет, а не ждёт находки.

Заведён Фазой 4 после того, как у TSMC — крупнейшей фабрики мира — на карте
оказалось шесть заказчиков, и все шесть нашлись только потому, что заказчик сам
назвал TSMC в собственной отчётности. Со стороны TSMC не нашёлся ни один.

РАЗБОР, ПОЧЕМУ ТАК ВЫШЛО. Три причины, и ни одна не про качество исследования.

1. **Открытие связи было побочным эффектом чтения узла.** Ребро A-B появлялось,
   только если досье по A или по B натыкалось на имя второго конца в документах
   первого. Никакого списка «пар, которые вероятно существуют» не было; никакой
   записи «эту пару искали и не нашли» тоже.

2. **У целого класса отношений имени нет НИ НА ОДНОЙ стороне.** Это измерено,
   а не предположено:
     TSMC   — «Our largest customer in 2023, 2024 and 2025 accounted for», без имени;
     Marvell — «third-party foundries located in Taiwan», без имени;
     Amazon — в 10-K слов TSMC, foundry, Trainium, Graviton НОЛЬ вхождений.
   Обе стороны описывают отношение, ни одна не называет контрагента. Для досье,
   которому велено опираться на собственные документы узла, такая связь невидима
   навсегда — сколько досье ни отрабатывай.

3. **Очередь кандидатов ловит только отсутствующие УЗЛЫ.** Amazon и Marvell оба
   на карте; отсутствующее ребро между двумя стоящими узлами кандидатом быть не
   может по определению. Механизма для него не существовало.

ЧТО ЗДЕСЬ ПРОТИВ ЭТОГО. Два генератора заданий, оба опираются на то, что уже
лежит в корпусе, и оба называют КЛАССЫ, а не ответы:

  `disclosed_unnamed` — узел собственной цитатой раскрыл контрагента и не назвал
      его. Таких цитат в корпусе шестьдесят на сорока девяти объектах, и до этой
      фазы их не читал никто: карта шестьдесят раз сказала о себе, что неполна.
      Задание уровня УЗЛА («найди, кто эти заказчики»), потому что имя как раз и
      неизвестно.

  `expected_edge` — таксономия говорит, что узел такого рода не работает без
      контрагента такого рода, а на карте у него такого нет ни с кем. Задание
      уровня КЛАССА («у этого проектировщика нет ни одной фабрики»), а не пары:
      кто именно фабрика — выясняет исследование, а не правило.

Правила — `config/nveco_gaps.yaml`, чтобы спорить с ними можно было не читая
Python. Задание закрывается ровно двумя способами, и оба ответ: `found` (связь
заведена с цитатой) или `not_found` (искали, не нашли, причина записана и уходит
в `nvnet_not_found`). Молчание третьим способом не является.
"""

import hashlib
import re

from . import db, nveco

_CFG = None


def cfg() -> dict:
    global _CFG
    if _CFG is None:
        _CFG = nveco.load_gaps()
    return _CFG


def limits() -> dict:
    base = {"per_entity": 6, "max_open_times": 2, "recheck_not_found_months": 6}
    return {**base, **(cfg().get("limits") or {})}


def _key(kind, subject, counterparty, expected) -> str:
    return hashlib.sha1(
        f"{kind}|{subject}|{counterparty or ''}|{expected}".encode()).hexdigest()[:16]


_WORD = re.compile(r"[A-Z][A-Za-z&.\-]+")


def _names_someone(quote: str, stop: set) -> bool:
    """Есть ли в цитате имя собственное, кроме первого слова.

    Раскрытие «две компании дали 19% и 15%» повода стоит, а «Arm China дала 16%» —
    нет: контрагент назван. Отличить их можно по форме, не заводя словаря компаний:
    заглавное слово в середине фразы — это имя, если оно не месяц, не страна и не
    аббревиатура отчётности. Стоп-список — в config/nveco_gaps.yaml.
    """
    body = quote.strip()
    for m in _WORD.finditer(body):
        if m.start() == 0:
            continue                       # первое слово фразы — не улика
        w = m.group(0).strip(".").lower()
        if w in stop or len(w) < 2:
            continue
        return True
    return False


def _months_between(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


# ── повод 1: узел раскрыл контрагента и не назвал его ────────────────────────
def disclosed_unnamed(con) -> list:
    """Собственные цитаты узлов, раскрывающие отношение без имени второй стороны.

    Ключ — ИЗДАТЕЛЬ цитаты (`self_of`), а не владелец строки. Фраза «our largest
    customer» на ребре `amd__tsmc__manufactures` издана TSMC и говорит о ЕЁ
    заказчиках, а не о паре, к которой ребро привязано. Считать по владельцу
    значило бы приписать утверждение не тому, кто его сделал.
    """
    conf = cfg()
    named_ok = [p.lower() for p in (conf.get("named_after_all") or [])]
    out, seen = [], set()
    stop = set(w.lower() for w in (conf.get("not_a_name") or []))
    for kind, spec in (conf.get("disclosed_unnamed") or {}).items():
        rx = re.compile("|".join(spec["patterns"]), re.I)
        veto = re.compile("|".join(spec["veto"]), re.I) if spec.get("veto") else None
        for r in con.execute("SELECT owner_kind, owner_id, self_of, url, quote "
                             "FROM nveco_source WHERE self_of IS NOT NULL"):
            q = r["quote"] or ""
            if not rx.search(q) or (veto and veto.search(q)):
                continue
            # Фраза, которая всё-таки называет партнёра, поводом не является.
            # Первая версия сверялась со списком фраз и пропускала «our largest
            # customer individually, Arm China, accounted for» — раскрытие, где имя
            # СТОИТ. Поэтому имя ищется по форме: заглавное слово не в начале цитаты
            # и не из стоп-списка. Дешевле ложного задания агенту.
            if any(n in q.lower() for n in named_ok) or _names_someone(q, stop):
                continue
            subj = r["self_of"]
            k = (subj, kind)
            if k in seen:
                continue
            seen.add(k)
            out.append({
                "kind": "disclosed_unnamed", "subject_id": subj,
                "counterparty": None, "cp_class": kind,
                "expected": spec["expect"], "rule_id": f"disclosed:{kind}",
                "why": spec["why"]["ru"], "quote": q, "quote_url": r["url"]})
    return out


# ── повод 2: таксономия обещает ребро, которого нет ──────────────────────────
def _select(ents, sel: dict) -> set:
    """id сущностей, подходящих под селектор {layers, roles, sectors, not_sectors}."""
    out = set()
    for eid, e in ents.items():
        if sel.get("layers") and not (set(e["layers"]) & set(sel["layers"])):
            continue
        if sel.get("roles") and e["role"] not in sel["roles"]:
            continue
        if sel.get("sectors") and e["sector"] not in sel["sectors"]:
            continue
        if sel.get("not_sectors") and e["sector"] in sel["not_sectors"]:
            continue
        out.add(eid)
    return out


def expected_edges(con) -> list:
    ents = {}
    for r in con.execute("SELECT id, name, role, sector FROM nveco_entity"):
        ents[r["id"]] = {"name": r["name"], "role": r["role"], "sector": r["sector"],
                         "layers": []}
    for r in con.execute("SELECT entity_id, layer_id FROM nveco_entity_layer"):
        if r["entity_id"] in ents:
            ents[r["entity_id"]]["layers"].append(r["layer_id"])

    # ОБЕ ПОЛОВИНЫ КАРТЫ. Семя (`nveco_edge`) и достройка сети (`nvnet_edge`)
    # хранятся раздельно, и охота, читающая только семя, заказала бы поиск связи,
    # которая уже найдена достройкой. Первый же прогон поймал это на паре
    # tsmc-google: ребро пришло из достройки, а правило требовало искать фабрику.
    edges = [(r["source_id"], r["target_id"], r["type"])
             for r in con.execute("SELECT source_id, target_id, type FROM nveco_edge")]
    if con.execute("SELECT name FROM sqlite_master WHERE type='table' AND "
                   "name='nvnet_edge'").fetchone():
        edges += [(r["source_id"], r["target_id"], r["type"])
                  for r in con.execute("SELECT source_id, target_id, type FROM nvnet_edge")]
    out = []
    for rule in cfg().get("expected_edges") or []:
        subjects = _select(ents, rule.get("when") or {})
        exp = rule["expect"]
        cps = _select(ents, exp.get("counterparty") or {})
        etype, direction = exp["type"], exp.get("direction", "from")
        for s in sorted(subjects):
            # `from` — контрагент ИСТОЧНИК ребра (фабрика производит для узла).
            partners = {a if direction == "from" else b
                        for a, b, t in edges
                        if t == etype and (b if direction == "from" else a) == s}
            if partners & (cps - {s}):
                continue          # такой контрагент уже есть — повода нет
            out.append({
                "kind": "expected_edge", "subject_id": s, "counterparty": None,
                "cp_class": ", ".join(sorted((exp.get("counterparty") or {}).get("sectors")
                                             or (exp.get("counterparty") or {}).get("layers")
                                             or ["?"])),
                "expected": etype, "rule_id": rule["id"],
                "why": rule["why"]["ru"], "quote": None, "quote_url": None})
    return out


# ── реестр ───────────────────────────────────────────────────────────────────
def record(con, month: str, tasks) -> dict:
    """Задания в реестр. Идемпотентно; повтор растит счётчик, а не плодит строки."""
    fresh = repeat = 0
    seen = set()
    for t in tasks:
        k = _key(t["kind"], t["subject_id"], t["counterparty"], t["expected"])
        seen.add(k)
        prev = con.execute("SELECT status FROM nveco_gap WHERE key=?", (k,)).fetchone()
        if prev:
            con.execute("UPDATE nveco_gap SET last_seen=?, times=times+1, why=?, "
                        "quote=?, quote_url=? WHERE key=?",
                        (month, t["why"], t["quote"], t["quote_url"], k))
            repeat += 1
        else:
            con.execute("""INSERT INTO nveco_gap
                             (key, kind, subject_id, counterparty, cp_class, expected,
                              rule_id, why, quote, quote_url, first_seen, last_seen)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (k, t["kind"], t["subject_id"], t["counterparty"], t["cp_class"],
                         t["expected"], t["rule_id"], t["why"], t["quote"],
                         t["quote_url"], month, month))
            fresh += 1
    # Задание, повода для которого больше нет, закрывается САМО и без решения:
    # либо связь завелась, либо узел перестал раскрывать безымянного контрагента.
    # Это единственный способ закрыть охоту молча, и он честный — повод исчез.
    closed = 0
    for r in con.execute("SELECT key FROM nveco_gap WHERE status='open'").fetchall():
        if r["key"] not in seen:
            con.execute("UPDATE nveco_gap SET status='found', decision=?, "
                        "decided_month=? WHERE key=?",
                        ("повода больше нет: связь заведена либо раскрытие исчезло",
                         month, r["key"]))
            closed += 1
    return {"new": fresh, "repeated": repeat, "closed": closed,
            "open": con.execute("SELECT COUNT(*) c FROM nveco_gap "
                                "WHERE status='open'").fetchone()["c"]}


def run(con, month: str) -> dict:
    """Полный проход охоты: собрать поводы, записать в реестр."""
    tasks = disclosed_unnamed(con) + expected_edges(con)
    stats = record(con, month, tasks)
    stats["tasks"] = len(tasks)
    return stats


def for_entities(con, ids) -> dict:
    """{entity_id: [задания]} для пакета досье, не больше limits.per_entity на узел."""
    cap = limits()["per_entity"]
    want, out = set(ids), {}
    for r in con.execute("SELECT * FROM nveco_gap WHERE status='open' "
                         "ORDER BY kind, subject_id"):
        s = r["subject_id"]
        if s not in want or len(out.get(s, [])) >= cap:
            continue
        out.setdefault(s, []).append({
            "key": r["key"], "повод": r["why"], "искать связь": r["expected"],
            "контрагент": r["counterparty"] or f"класс: {r['cp_class']}",
            "своя цитата": r["quote"], "источник": r["quote_url"],
            "правило": r["rule_id"], "висит прогонов": r["times"]})
    return out


def decide(con, key: str, status: str, reason: str, month: str) -> bool:
    if not con.execute("SELECT 1 FROM nveco_gap WHERE key=?", (key,)).fetchone():
        return False
    con.execute("UPDATE nveco_gap SET status=?, decision=?, decided_month=? WHERE key=?",
                (status, reason, month, key))
    return True


def audit(con) -> dict:
    """Задания, которые видели и не решили. Пустой ответ — единственный приемлемый."""
    mx = limits()["max_open_times"]
    stale = [dict(r) for r in con.execute(
        f"""SELECT key, kind, subject_id, cp_class, expected, why, first_seen, times
            FROM nveco_gap WHERE status='open' AND times > {mx}
            ORDER BY times DESC, subject_id""")]
    return {"stale_gaps": stale,
            "open": con.execute("SELECT COUNT(*) c FROM nveco_gap "
                                "WHERE status='open'").fetchone()["c"]}
