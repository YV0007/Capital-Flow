"""Реестр фактов: величина, её расписка и правило «чем подкреплено число».

## Зачем перевёрнут порядок

До этой правки проза писалась ВОКРУГ цитат. Агент брал то, что нашлось в
`evidence`, и строил вокруг найденного предложения — поэтому текст выходил ровно
такой глубины, какой оказались цитаты. Измерено на карте перед правкой: **101 связь
из 262** с развёрнутым разбором стоит на ОДНОМ документе, и почти всегда это дежурный
абзац про риски. Отсюда и обезличивание: если в цитате написано «one customer», то и
в тексте появляется «one customer», хотя вся карта существует ради того, чтобы
называть.

Новый порядок: исследование → реестр величин → свободный текст. Цитата не сидит
внутри предложения, она лежит слоем ниже, как расписка. Читатель её не видит, пока
не откроет источники, а движок сверяет по ней каждое число.

## Что здесь проверяется, а что нет

| слой | кто делает | ловит | НЕ доказывает |
|---|---|---|---|
| текст ↔ реестр | `nvnet_handoff`, офлайн | выдуманное число | что число верно |
| величина ↔ фрагмент | этот модуль, офлайн | число, приписанное наугад | что страница не изменилась |
| ссылка жива | `nveco_verify` | мёртвую ссылку | что число на странице |
| число НА странице | `nveco_verify`, best-effort | расхождение со страницей | ничего при PDF, JS, пейволле |

Второй слой — самый дешёвый и самый недооценённый: если величина `12.2` не
встречается в собственном `verbatim` факта, то расписка выписана не на ту сумму, и
это видно без единого обращения к сети.

## Правило подкрепления — ПО ОБЪЕКТУ, а не по карте

Есть у объекта `facts[]` — числа его прозы проверяются ПО РЕЕСТРУ, и откат к цитатам
ему запрещён. Нет — работает прежняя проверка по `evidence`/`sources`, а сам объект
считается долгом и попадает в счётчик прогона поимённо.

Иначе правило было бы невключаемым: на момент правки числа в прозе есть у 150
объектов карты, и требовать реестр со всех сразу значило бы не выпускать карту, пока
не переписан последний абзац. Долг видно в каждом прогоне — этого достаточно, чтобы
он не забылся.
"""

import re

from . import nveco

FACT_COLS = ["owner_kind", "owner_key", "label_ru", "label_en", "value", "unit",
             "as_of", "about", "url", "source_type", "retrieved", "verbatim"]

# Единицы — закрытый список НЕ из педантизма: «$12.2 млрд» и «12.2%» это разные
# утверждения об одной цифре, и потребитель обязан их различать, не разбирая текст.
UNITS = {"usd_b", "usd_m", "usd_k", "usd", "pct", "pp", "mw", "gw", "kwh",
         "wafers", "units", "people", "years", "months", "days", "nm",
         "gbps", "tb_s", "sqft", "acres", "count", "ratio", "date", "none"}

AS_OF_RE = re.compile(r"^\d{4}(-(0[1-9]|1[0-2])(-\d{2})?|-Q[1-4]|-H[12]|-FY)?$")
_DIGIT = re.compile(r"\d")
_CYRILLIC = re.compile(r"[А-Яа-яЁё]")


def has_number(value: str) -> bool:
    return bool(_DIGIT.search(value or ""))


def numbers(text: str) -> set:
    """Числовые токены в нормализованном виде — та же нормализация, что у прозы."""
    from .nvnet_handoff import _numbers
    return _numbers(text or "")


def fact_pool(facts) -> set:
    """Числа, которые реестр объекта вправе подтвердить.

    Берутся И значения, И фрагменты: величина может стоять в тексте округлённой
    («около $12 млрд» при value 12.2), а в цитате — как есть.
    """
    out = set()
    for f in facts or []:
        out |= numbers(str(f.get("value") or ""))
        out |= numbers(f.get("verbatim") or "")
        out |= numbers(str(f.get("asOf") or f.get("as_of") or ""))
    return out


def backing(obj: dict, kind: str):
    """(множество чисел, чем подкреплено) для одного объекта выдачи.

    `kind` — 'edge' или 'entity'. Возвращает 'facts', если у объекта есть реестр, и
    'evidence' в противном случае. Второе — долг, а не режим работы.
    """
    facts = obj.get("facts") or []
    if facts:
        return fact_pool(facts), "facts"
    rows = (obj.get("evidence") if kind == "edge" else obj.get("sources")) or []
    return numbers(" ".join(r.get("quote", "") for r in rows)), "evidence"


def validate_fact(row: dict, ids: set = None, where: str = "") -> list:
    """Ошибки одной записи реестра. Пустой список — запись годна.

    Проверяется форма и ОДНА содержательная вещь, которую можно проверить офлайн:
    что величина действительно стоит в приведённом фрагменте. Всё остальное —
    верна ли величина, свежая ли дата, первоисточник ли это — отвечает исследователь
    работой, а не форма файла.
    """
    errs = []
    kind = (row.get("owner_kind") or "").strip()
    if kind not in ("entity", "edge"):
        errs.append(f"{where}owner_kind '{kind}' должен быть entity или edge")
    if not (row.get("owner_key") or "").strip():
        errs.append(f"{where}нет owner_key")

    for side in ("label_ru", "label_en"):
        if not (row.get(side) or "").strip():
            errs.append(f"{where}нет {side} — подпись величины двуязычна, "
                        f"как и вся проза выдачи")

    value = (row.get("value") or "").strip()
    if not value:
        errs.append(f"{where}нет value — факт без величины это не факт, а мнение")
    if len(value) > 40:
        errs.append(f"{where}value длиной {len(value)} — это уже предложение, "
                    f"а не величина")
    # ВЕЛИЧИНА — НЕ ПРОЗА. Двуязычная сторона факта это `label`; в `value` стоит
    # число, дата или имя из источника, и переводить его не нужно и нельзя.
    # Русский текст здесь означает, что подпись перепутали с величиной, — и он
    # немедленно всплывает в аудите перевода на стороне дашборда как строка,
    # которую английский читатель видит по-русски. Поймано ровно так.
    if _CYRILLIC.search(value):
        errs.append(f"{where}value «{value}» по-русски — величина не переводится, "
                    f"а двуязычная подпись живёт в label")

    unit = (row.get("unit") or "").strip().lower()
    if unit and unit not in UNITS:
        errs.append(f"{where}unit '{unit}' не из списка: "
                    f"{', '.join(sorted(UNITS))}")

    as_of = (row.get("as_of") or "").strip()
    if as_of and not AS_OF_RE.match(as_of):
        errs.append(f"{where}as_of '{as_of}' — нужен YYYY, YYYY-MM, YYYY-MM-DD, "
                    f"YYYY-Qn, YYYY-Hn или YYYY-FY")

    about = (row.get("about") or "").strip()
    if about and ids is not None and about not in ids:
        errs.append(f"{where}about '{about}' — такой сущности на карте нет")

    url = (row.get("url") or "").strip()
    if not url:
        errs.append(f"{where}нет url")
    elif not url.lower().startswith("http"):
        errs.append(f"{where}url не ссылка: '{url[:40]}'")
    else:
        from .ingest import is_search_url
        if is_search_url(url):
            errs.append(f"{where}url — поисковый запрос, а не документ")

    stype = (row.get("source_type") or "").strip().lower()
    if stype and stype not in nveco.SOURCE_TYPES:
        errs.append(f"{where}source_type '{stype}' не из перечисления источников")

    verbatim = (row.get("verbatim") or "").strip()
    if has_number(value):
        if not verbatim:
            errs.append(f"{where}величина '{value}' без verbatim — числовой факт "
                        f"обязан приводить фрагмент, где эта величина стоит")
        elif not (numbers(value) & numbers(verbatim)):
            errs.append(f"{where}величина '{value}' не встречается в собственном "
                        f"фрагменте «{verbatim[:60]}…» — расписка выписана не на ту сумму")
    if verbatim and nveco.word_count(verbatim) > nveco.MAX_QUOTE_WORDS:
        errs.append(f"{where}verbatim {nveco.word_count(verbatim)} слов при пределе "
                    f"{nveco.MAX_QUOTE_WORDS}")
    return errs


def to_payload(row: dict, tier: int = None) -> dict:
    """Строка CSV -> объект выдачи. Подпись двуязычна, тир ставит движок."""
    return {
        "label": {"ru": (row.get("label_ru") or "").strip(),
                  "en": (row.get("label_en") or "").strip()},
        "value": (row.get("value") or "").strip(),
        "unit": (row.get("unit") or "").strip().lower() or None,
        "asOf": (row.get("as_of") or "").strip() or None,
        "about": (row.get("about") or "").strip() or None,
        "url": (row.get("url") or "").strip(),
        "sourceType": (row.get("source_type") or "").strip().lower() or None,
        "tier": tier,
        "retrieved": (row.get("retrieved") or "").strip() or None,
        "verbatim": (row.get("verbatim") or "").strip() or None,
    }


def one_document(facts) -> bool:
    """Все расписки объекта выписаны одним документом.

    Не ошибка: у экспортного акта один документ и есть вся правда. Но для связи с
    несколькими величинами это признак того, что исследование не выходило за пределы
    первой найденной страницы, — поэтому предупреждение, а не отказ.
    """
    urls = {f.get("url") for f in facts or [] if f.get("url")}
    return len(urls) == 1 and len(facts or []) > 1
