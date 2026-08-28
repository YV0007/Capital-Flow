"""Двуязычная проза: {"ru": …, "en": …} на каждом текстовом поле выдачи.

## Зачем это здесь, а не на стороне дашборда

Дашборд умел переводить сам — файлом-спутником capitalMapRu.json, набранным
руками и привязанным к стабильным id. Он работал ровно до следующей поставки: на
2026-08-24 непереведённых строк было 79, а тренды не переведены вовсе. Причина
структурная, а не организационная. Перевод, живущий отдельно от генерации,
устаревает при каждом выпуске, потому что источник правды и его перевод меняются
в разное время и разными руками.

Движок пишет предложение, имея весь контекст: он знает тип связи, статус
источника, кто кого поставляет и почему. Второй язык дешевле всего написать
ровно в этот момент. Поэтому обе версии рождаются вместе и путешествуют вместе.

## Что такое «параллельная версия»

НЕ машинный перевод и не подстрочник. Русский должен читаться как русская
финансовая проза, английский — как английская. Одна мысль, два естественных
изложения. Имена собственные (компании, фонды, продукты, тикеры) не переводятся
ни в ту, ни в другую сторону. Числа и даты — по правилам своего языка
($1.37B против $1,37 млрд).

## Что НЕ оборачивается

Идентификаторы, слаги, значения перечислений, URL и ЦИТАТЫ ИЗ ИСТОЧНИКОВ. Цитата
остаётся на языке документа, из которого взята: перевод цитаты — это уже не
цитата, и подпись «источник» под ней была бы ложью.
"""

import csv

from . import db

LANGS = ("ru", "en")

# Разделитель хранения: одна строка на (объект, поле, язык). Ни одна прикладная
# таблица не получает колонок *_en — иначе каждое новое поле прозы означало бы
# миграцию схемы, а третий язык — ещё одну.
SCHEMA = """
CREATE TABLE IF NOT EXISTS i18n_text (
  scope   TEXT NOT NULL,          -- 'nveco' | 'capital' — какая карта
  kind    TEXT NOT NULL,          -- 'entity' | 'edge' | 'cycle' | 'layer' | …
  obj_id  TEXT NOT NULL,          -- id сущности/связи/слоя
  field   TEXT NOT NULL,          -- 'one_liner' | 'note' | 'why_lock_in' | …
  lang    TEXT NOT NULL,          -- 'ru' | 'en'
  text    TEXT NOT NULL,
  source  TEXT,                   -- 'csv' | 'config' | 'generated' | 'backfill'
  PRIMARY KEY (scope, kind, obj_id, field, lang)
);
CREATE INDEX IF NOT EXISTS ix_i18n_lookup ON i18n_text(scope, kind, obj_id);
"""


class MissingTranslation(RuntimeError):
    """Поднимается валидатором выдачи, а не на записи: собрать все пропуски и
    показать их списком полезнее, чем упасть на первом."""


def ensure(con):
    con.executescript(SCHEMA)
    con.commit()


# ── запись ───────────────────────────────────────────────────────────────────

def put(con, scope, kind, obj_id, field, lang, text, source="csv"):
    if lang not in LANGS:
        raise ValueError(f"неизвестный язык '{lang}'")
    if not (text or "").strip():
        return 0
    con.execute(
        """INSERT INTO i18n_text (scope,kind,obj_id,field,lang,text,source)
           VALUES (?,?,?,?,?,?,?)
           ON CONFLICT(scope,kind,obj_id,field,lang) DO UPDATE SET
             text=excluded.text, source=excluded.source""",
        (scope, kind, obj_id, field, lang, text.strip(), source))
    return 1


def reset_csv_scope(con, scope, source="csv") -> int:
    """Убрать из склада всё, что пришло из файлов, ПЕРЕД их перезагрузкой.

    Файлы перевода — полный манифест, а не приращение: строка, которую из них
    убрали, должна исчезнуть и из выдачи. Без этого склад копит осиротевший
    текст и продолжает его отдавать. Ровно это и случилось: 1569 строк в складе
    против 999 в файле, и дашборд получал английские заметки, которых уже нет
    ни в одном источнике — со словом «anchor», вычищенным двумя проходами ранее.

    Сгенерированное (`source='generated'` — подписи контуров, причины точек
    отказа) НЕ трогается: оно рождается в коде, а не в файлах, и файлов, из
    которых его можно перечитать, не существует.
    """
    n = con.execute("DELETE FROM i18n_text WHERE scope=? AND source=?",
                    (scope, source)).rowcount
    con.commit()
    return n


def load_csv(con, path, scope, source="csv") -> dict:
    """Файл перевода: kind,id,field,lang,text.

    Формат намеренно узкий и длинный, а не «колонка на язык»: третий язык тогда
    не меняет ни схему, ни парсер, а пропуск видно как отсутствие строки, а не
    как пустую ячейку, которую легко не заметить глазом.
    """
    stats = {"rows": 0, "written": 0, "bad": []}
    with open(path, newline="", encoding="utf-8") as fh:
        for i, row in enumerate(csv.DictReader(fh), start=2):
            stats["rows"] += 1
            kind = (row.get("kind") or "").strip()
            oid = (row.get("id") or "").strip()
            field = (row.get("field") or "").strip()
            lang = (row.get("lang") or "").strip().lower()
            text = (row.get("text") or "").strip()
            if not all((kind, oid, field, lang)) or lang not in LANGS:
                stats["bad"].append(f"{path.name}:{i} kind/id/field/lang неполны")
                continue
            if not text:
                stats["bad"].append(f"{path.name}:{i} пустой текст — "
                                    f"пропуск записывается отсутствием строки, "
                                    f"а не пустой ячейкой")
                continue
            stats["written"] += put(con, scope, kind, oid, field, lang, text, source)
    con.commit()
    return stats


# ── чтение ───────────────────────────────────────────────────────────────────

def index(con, scope) -> dict:
    """{(kind, obj_id, field): {lang: text}} — один запрос на сборку выдачи."""
    out = {}
    for r in con.execute(
            "SELECT kind,obj_id,field,lang,text FROM i18n_text WHERE scope=?",
            (scope,)):
        out.setdefault((r[0], r[1], r[2]), {})[r[3]] = r[4]
    return out


def bi(ru=None, en=None):
    """Пара как она уезжает в файл. Пустая сторона НЕ подменяется другой:
    подмена сделала бы дыру невидимой, а валидатор именно её и ищет."""
    return {"ru": (ru or "").strip() or None, "en": (en or "").strip() or None}


def wrap(idx, kind, obj_id, field, fallback_ru=None, fallback_en=None):
    """Достать пару из индекса, добрав недостающую сторону из исходной колонки.

    `fallback_ru` — то, что лежит в прикладной таблице сегодня. Для карты
    экосистемы это русский, для карты потоков — английский; поэтому обе стороны
    передаются явно, и модуль не угадывает, на каком языке исходник.
    """
    got = idx.get((kind, obj_id, field), {})
    return bi(got.get("ru") or fallback_ru, got.get("en") or fallback_en)


# ── проверка ─────────────────────────────────────────────────────────────────

def is_pair(v) -> bool:
    return isinstance(v, dict) and set(v) == {"ru", "en"}


def check(payload, paths) -> list:
    """Пройти по выдаче и вернуть КАЖДОЕ поле с пустой стороной.

    `paths` — список (json-путь, значение). Собирает вызывающий: он знает форму
    своей выдачи, а универсальный обход по всему дереву поймал бы и цитаты,
    которые оборачивать нельзя.
    """
    errs = []
    for path, val in paths:
        if val is None:
            continue
        if not is_pair(val):
            errs.append(f"{path}: не пара {{ru,en}} — {type(val).__name__}")
            continue
        for lang in LANGS:
            if not (val.get(lang) or "").strip():
                errs.append(f"{path}: пустая сторона '{lang}'")
    return errs


def coverage(con, scope) -> dict:
    """Сколько полей имеют обе стороны. Для отчёта прогона, не для валидатора."""
    rows = list(con.execute(
        """SELECT kind, field,
                  SUM(lang='ru') ru, SUM(lang='en') en
             FROM i18n_text WHERE scope=? GROUP BY kind, field""", (scope,)))
    out = {"fields": [], "ru": 0, "en": 0}
    for kind, field, ru, en in rows:
        out["fields"].append({"kind": kind, "field": field, "ru": ru, "en": en,
                              "gap": abs((ru or 0) - (en or 0))})
        out["ru"] += ru or 0
        out["en"] += en or 0
    out["fields"].sort(key=lambda x: -x["gap"])
    return out
