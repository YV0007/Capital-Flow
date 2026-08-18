"""Переобход ссылок: жива ли каждая цитата.

Раз в месяц движок ходит по КАЖДОМУ источнику — и сущностей, и связей, одним проходом
(ради этого источники лежат в одной таблице). Проверяется HTTP-статус; результат
пишется в `alive` и `fetched`.

Мёртвая ссылка НЕ удаляет ребро. Она снимает с него один подтверждённый источник, что
может уронить статус с `confirmed` до `high_confidence` и дальше. Это правильное
поведение: связь, доказательство которой исчезло, должна выглядеть слабее, а не
пропадать молча.

Различаются три исхода, и это не педантизм:
  200                -> alive = 1
  404 / 410 / DNS    -> alive = 0, «источник исчез»
  403 / 429 / таймаут-> alive НЕ трогается, пишется причина

Третий случай существует потому, что пейволлы и антибот-стены отдают 403 на ровно тех
источниках, которые карта цитирует чаще всего. Считать «нас не пустили» за «это
неправда» значит гасить карту по причине, не имеющей отношения к истине.
"""

import sys
from datetime import date

from . import nveco

try:
    import requests
except ImportError:
    requests = None

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
# SEC требует User-Agent с контактом и отвергает браузерную строку
# (https://www.sec.gov/about/developer-resources). Отчётность — тир 1, то есть самые
# ценные источники карты; неправильный заголовок означал бы 403 именно на них.
SEC_UA = "capital-flow research contact@example.com"
SEC_HOSTS = ("sec.gov", "data.sec.gov")
TIMEOUT = 20
DEAD_CODES = {400, 404, 410, 451}
BLOCKED_CODES = {401, 402, 403, 405, 406, 408, 429, 500, 502, 503, 504}


def _ua_for(url: str) -> str:
    host = (url or "").split("//", 1)[-1].split("/", 1)[0].lower()
    return SEC_UA if any(host == h or host.endswith("." + h) for h in SEC_HOSTS) else UA


def _fetch(url: str):
    """('ok'|'dead'|'blocked', пояснение)."""
    if requests is None:
        return "blocked", "requests не установлен"
    try:
        r = requests.get(url, headers={"User-Agent": _ua_for(url), "Accept": "*/*"},
                         timeout=TIMEOUT, allow_redirects=True)
    except Exception as exc:                     # сеть никогда не роняет прогон
        return "blocked", f"{type(exc).__name__}: {str(exc)[:100]}"
    if r.status_code in DEAD_CODES:
        return "dead", f"HTTP {r.status_code}"
    if r.status_code in BLOCKED_CODES or r.status_code >= 400:
        return "blocked", f"HTTP {r.status_code}"
    return "ok", f"HTTP {r.status_code}"


def run(month: str, offline: bool = False, limit: int = None) -> dict:
    con = nveco.connect()
    today = date.today().isoformat()
    rows = con.execute("SELECT id, url, alive FROM nveco_source ORDER BY id").fetchall()
    if limit:
        rows = rows[:limit]

    stats = {"checked": 0, "alive": 0, "dead": 0, "blocked": 0, "skipped": 0}
    seen = {}
    if offline:
        stats["skipped"] = len(rows)
    else:
        for r in rows:
            url = r["url"]
            if url not in seen:
                seen[url] = _fetch(url)
            verdict, note = seen[url]
            stats["checked"] += 1
            if verdict == "ok":
                con.execute("UPDATE nveco_source SET alive=1, fetched=?, http_note=? WHERE id=?",
                            (today, note, r["id"]))
                stats["alive"] += 1
            elif verdict == "dead":
                con.execute("UPDATE nveco_source SET alive=0, fetched=?, http_note=? WHERE id=?",
                            (today, f"источник исчез: {note}", r["id"]))
                stats["dead"] += 1
            else:
                con.execute("UPDATE nveco_source SET fetched=?, http_note=? WHERE id=?",
                            (today, f"не проверено: {note}", r["id"]))
                stats["blocked"] += 1
        con.commit()

    stats["dead_urls"] = [r["url"] for r in con.execute(
        "SELECT DISTINCT url FROM nveco_source WHERE alive=0")]
    con.close()
    return stats


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    print(run(args[0] if args else nveco.current_month(), offline="--offline" in sys.argv))
