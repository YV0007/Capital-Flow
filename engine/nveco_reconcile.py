"""Сверка двух сторон: чей это документ и сколько концов стоит за связью.

Стадия между `nveco_ingest` и `nveco_score`. Отвечает на ОДИН вопрос — **чьим словом
подтверждена связь** — и ни на один другой. Статус, обрезки, гравитация и рубрика
остаются в `nveco_score`: там арифметика над доказательствами, здесь — разметка самих
доказательств.

Почему это отдельная стадия, а не десять строк внутри оценки. До v4 «сила
доказательства» была одномерной: тир источника плюс их число. С приходом досье по узлу
у каждой связи появляются ДВА независимых рассказчика, и вопрос «сколько сторон это
утверждает» перестал быть свойством источника — он стал свойством пары. Считать его в
том же цикле, где считается критичность и обрезаются риски, значит смешивать разбор
свидетельств с их взвешиванием: первый обязан быть виден отдельно, потому что именно он
приносит `disputed`.

Что делает стадия:

  1. **Пересчитывает тир КАЖДОГО источника относительно предмета.** Число, записанное
     агентом, — это его мнение по шкале, которой больше нет. Для источника связи
     предмет — первый конец, контрагент — второй; для источника профиля предмет — сама
     сущность.
  2. **Проставляет `self_of`** — id того конца, который издал ссылку. Это вход и для
     правила `min_self_sources`, и для статуса `bilateral`: обе проверки обязаны читать
     ОДНУ разметку, а не две её реконструкции.
  3. **Ставит `sidedness`:**

         A заявил, B подтвердил своими документами  ->  bilateral
         A заявил, B молчит                          ->  single
         A заявил, B противоречит                    ->  disputed

Три правила, которые стадия не нарушает никогда:

* **Спор не решается.** `disputed` — не ошибка данных и не слабое доказательство.
  Расхождение двух компаний в описании собственных отношений — находка, и схлопывать
  её в `confirmed` нельзя, сколько бы цитат ни лежало с одной стороны.
* **Сторона не удаляется.** Контрцитата едет в `counterEvidence` рядом с прямой,
  обе видны потребителю.
* **`bilateral` требует двух РАЗНЫХ издателей**, и притом именно тех двух, кого связь
  касается. Две цитаты с одного домена дают множество из одного элемента и `bilateral`
  не дают — это следствие устройства, а не отдельная проверка.
"""

import sys

from . import nveco


def _sources_of_edges(con) -> dict:
    out = {}
    for r in con.execute("SELECT id, owner_id, url, tier, alive, self_of, counter "
                         "FROM nveco_source WHERE owner_kind='edge'"):
        out.setdefault(r["owner_id"], []).append(dict(r))
    return out


def run(month: str = None) -> dict:
    con = nveco.connect()
    retiered = 0
    disputes = []
    srcs = _sources_of_edges(con)

    for e in con.execute("SELECT id, source_id, target_id FROM nveco_edge").fetchall():
        rows = srcs.get(e["id"], [])
        for r in rows:
            # Предмет связи — её первый конец, контрагент — второй. Это и есть та
            # точка отсчёта, из-за которой 10-K NVIDIA перестал быть тиром 1 везде.
            t, _ = nveco.source_tier(r["url"], e["source_id"], e["target_id"])
            t = t or 6
            self_of = next((x for x in (e["source_id"], e["target_id"])
                            if nveco.is_self_source(r["url"], x)), None)
            if t != r["tier"] or self_of != r["self_of"]:
                retiered += 1 if t != r["tier"] else 0
                con.execute("UPDATE nveco_source SET tier=?, confidence=?, self_of=? "
                            "WHERE id=?",
                            (t, nveco.tier_confidence(t), self_of, r["id"]))
            r["tier"], r["self_of"] = t, self_of

        live = [r for r in rows if r["alive"]]      # мёртвая ссылка не подтверждает
        claimed = sorted({r["self_of"] for r in live if r["self_of"] and not r["counter"]})
        counters = [r for r in live if r["counter"]]
        sidedness = ("disputed" if counters else
                     "bilateral" if len(claimed) >= 2 else "single")
        if counters:
            disputes.append({
                "edge": e["id"],
                "claimed_by": claimed,
                "counter_by": sorted({r["self_of"] for r in counters if r["self_of"]}),
                "counter_urls": [r["url"] for r in counters],
            })
        con.execute("UPDATE nveco_edge SET sidedness=?, claimed_by=? WHERE id=?",
                    (sidedness, "|".join(claimed) or None, e["id"]))

    # Источники профиля: предмет — сама сущность, второго конца нет.
    for r in con.execute("SELECT id, owner_id, url, tier, self_of FROM nveco_source "
                         "WHERE owner_kind='entity'").fetchall():
        t, _ = nveco.source_tier(r["url"], r["owner_id"])
        t = t or 6
        self_of = r["owner_id"] if nveco.is_self_source(r["url"], r["owner_id"]) else None
        if t != r["tier"]:
            retiered += 1
        if t != r["tier"] or self_of != r["self_of"]:
            con.execute("UPDATE nveco_source SET tier=?, confidence=?, self_of=? "
                        "WHERE id=?", (t, nveco.tier_confidence(t), self_of, r["id"]))
    con.commit()

    mix = {s: con.execute("SELECT COUNT(*) c FROM nveco_edge WHERE sidedness=?",
                          (s,)).fetchone()["c"] for s in nveco.SIDEDNESS}
    # Профили: сколько сущностей имеют хоть одну СВОЮ цитату. Это то самое число,
    # ради которого затевалась кампания, и считать его надо там, где оно рождается.
    self_profiles = con.execute(
        "SELECT COUNT(DISTINCT owner_id) c FROM nveco_source "
        "WHERE owner_kind='entity' AND self_of IS NOT NULL").fetchone()["c"]
    total_profiles = con.execute(
        "SELECT COUNT(DISTINCT owner_id) c FROM nveco_source "
        "WHERE owner_kind='entity'").fetchone()["c"]
    con.close()
    return {"retiered": retiered, "sidedness_mix": mix, "disputes": disputes,
            "self_sourced_profiles": self_profiles, "profiles": total_profiles}


if __name__ == "__main__":
    print(run(sys.argv[1] if len(sys.argv) > 1 else nveco.current_month()))
