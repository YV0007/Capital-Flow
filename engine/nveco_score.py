"""Вычисляемый слой: рубрика, хребет, статус, гравитация, концентрация, обрезки.

Ни одного суждения. Всё здесь — арифметика над тем, что агенты уже записали, и
применение замороженных правил. Ровно поэтому агент не имеет права писать эти поля
сам: карта, где цифры не сходятся с собственной рубрикой, хуже карты без цифр.

Что считается:
  criticality  — 0.30·irreplaceability + 0.30·lockInDepth + 0.25·timeToReplace
                 + 0.15·strategicControl (веса заморожены контрактом)
  spine        — из типа связи, по config/nveco_edges.yaml
  status       — по правилу подтверждения из тиров ЖИВЫХ источников
  confidence   — из тира лучшего живого источника
  gravity      — структурно по графу: охват, слои, типы связей, контуры
  concentration— HHI по критичности внутри слоя
  stale        — старше шести месяцев без подтверждения
  обрезки      — связь без источника тира 1–3 не может нести critical и strength > 80
"""

import json
import sys

from . import nveco

# Гравитация. Веса подобраны так, чтобы охват доминировал, но не затирал остальное:
# сущность, дотягивающаяся до многих, важна структурно — но сущность, дотягивающаяся
# до многих ЧЕРЕЗ РАЗНЫЕ МЕХАНИКИ, важнее.
GRAVITY_WEIGHTS = {"reach": 0.45, "layers": 0.25, "edge_types": 0.20, "cycles": 0.10}
REACH_FULL_SCALE = 25          # охват, начиная с которого компонент насыщается
CYCLES_FULL_SCALE = 5

# Порог концентрации слоя (HHI по критичности).
HHI_MONOPOLY, HHI_OLIGOPOLY = 0.50, 0.25

# Обрезки для связей без первичного источника.
PRIMARY_TIERS = (1, 2, 3)
CLAMP_MAX_STRENGTH = 80
STALE_MONTHS = 6


def _status_and_confidence(tiers):
    """Правило подтверждения. Не смягчается.

    confirmed       — два и более источника тира 1–2, ЛИБО один тира 1 плюс один тира 3
    high_confidence — один тира 1, ЛИБО два тира 2–3
    signal          — всё остальное
    """
    t12 = sum(1 for t in tiers if t in (1, 2))
    t1 = sum(1 for t in tiers if t == 1)
    t3 = sum(1 for t in tiers if t == 3)
    t23 = sum(1 for t in tiers if t in (2, 3))
    if t12 >= 2 or (t1 >= 1 and t3 >= 1):
        status = "confirmed"
    elif t1 >= 1 or t23 >= 2:
        status = "high_confidence"
    else:
        status = "signal"
    best = min(tiers) if tiers else 6
    conf = nveco.tier_confidence(best)
    # Подтверждение несколькими источниками добавляет уверенности, но не выше потолка
    # своего тира: два вторичных источника не делают слух первичным фактом.
    if status == "confirmed":
        conf = min(0.99, conf + 0.03)
    elif status == "signal":
        conf = max(0.40, conf - 0.05)
    return status, round(conf, 3)


def run(month: str, anchor: str = None) -> dict:
    acfg = nveco.anchor_cfg(anchor)
    con = nveco.connect()
    log = []

    # ── критичность сущностей ────────────────────────────────────────────────
    factors = {}
    for r in con.execute("SELECT entity_id, factor, value FROM nveco_entity_factor"):
        factors.setdefault(r["entity_id"], {})[r["factor"]] = r["value"]

    entities = [dict(r) for r in con.execute("SELECT * FROM nveco_entity")]
    no_factors = []
    for e in entities:
        c = nveco.criticality(factors.get(e["id"], {}))
        if c is None:
            no_factors.append(e["id"])
        e["criticality"] = c
        con.execute("UPDATE nveco_entity SET criticality=? WHERE id=?", (c, e["id"]))
    if no_factors:
        log.append(f"без полного набора факторов, критичность не посчитана: "
                   f"{', '.join(sorted(no_factors)[:8])}"
                   f"{' …' if len(no_factors) > 8 else ''}")

    # ── хребет из типа + статус из тиров + обрезки ───────────────────────────
    srcs = {}
    for r in con.execute("SELECT owner_id, tier, alive FROM nveco_source "
                         "WHERE owner_kind='edge'"):
        srcs.setdefault(r["owner_id"], []).append((r["tier"], r["alive"]))

    clamped = 0
    for e in con.execute("SELECT * FROM nveco_edge").fetchall():
        spine = nveco.spine_of(e["type"])
        rows = srcs.get(e["id"], [])
        live = [t for t, alive in rows if alive]
        tiers = live or []                      # мёртвый источник не подтверждает
        status, conf = _status_and_confidence(tiers)
        best_tier = min(tiers) if tiers else (min(t for t, _ in rows) if rows else 6)

        strength, risk_level, why = e["strength"], e["risk_level"], None
        if not any(t in PRIMARY_TIERS for t in tiers):
            if strength > CLAMP_MAX_STRENGTH:
                why = (f"strength {strength} -> {CLAMP_MAX_STRENGTH}: "
                       f"нет источника тира 1–3")
                strength = CLAMP_MAX_STRENGTH
            if risk_level == "critical":
                why = ((why + "; ") if why else "") + "risk critical -> high: нет источника тира 1–3"
                risk_level = "high"
        if why:
            clamped += 1
            log.append(f"обрезано {e['id']}: {why}")

        con.execute(
            """UPDATE nveco_edge SET spine=?, status=?, confidence=?, source_tier=?,
                 confirmed_sources=?, strength=?, risk_level=?, clamped=? WHERE id=?""",
            (spine, status, conf, best_tier, len(tiers), strength, risk_level, why,
             e["id"]))
    con.commit()

    # ── гравитация ───────────────────────────────────────────────────────────
    layers_of = {}
    for r in con.execute("SELECT entity_id, layer_id, is_primary FROM nveco_entity_layer"):
        layers_of.setdefault(r["entity_id"], []).append((r["layer_id"], r["is_primary"]))

    edges = [dict(r) for r in con.execute(
        "SELECT id, source_id, target_id, type, spine, strength FROM nveco_edge")]
    cycle_members = {}
    for r in con.execute("SELECT members FROM nveco_cycle WHERE run_month=?", (month,)):
        for m in r["members"].split("|"):
            cycle_members[m] = cycle_members.get(m, 0) + 1

    touch = {e["id"]: {"reach": set(), "layers": set(), "types": set()} for e in entities}
    per_layer_edges = {e["id"]: {} for e in entities}
    lidx = {l: i for i, l in enumerate(nveco.layer_ids())}
    for ed in edges:
        for me, other in ((ed["source_id"], ed["target_id"]), (ed["target_id"], ed["source_id"])):
            if me not in touch:
                continue
            touch[me]["reach"].add(other)
            touch[me]["types"].add(ed["type"])
            for l, _ in layers_of.get(other, []):
                touch[me]["layers"].add(l)
            # Ребро относится к тому слою сущности, который ближе всего к основному
            # слою контрагента — так капсула утолщается там, где связь реально идёт.
            opl = next((l for l, p in layers_of.get(other, []) if p), None)
            mine = [l for l, _ in layers_of.get(me, [])]
            if opl in lidx and mine:
                best = min(mine, key=lambda l: abs(lidx.get(l, 0) - lidx[opl]))
                per_layer_edges[me][best] = per_layer_edges[me].get(best, 0) + 1

    for e in entities:
        t = touch[e["id"]]
        cyc = cycle_members.get(e["id"], 0)
        score = round(100 * (
            GRAVITY_WEIGHTS["reach"] * min(1.0, len(t["reach"]) / REACH_FULL_SCALE)
            + GRAVITY_WEIGHTS["layers"] * len(t["layers"]) / max(1, len(lidx))
            + GRAVITY_WEIGHTS["edge_types"] * len(t["types"]) / len(nveco.edge_types())
            + GRAVITY_WEIGHTS["cycles"] * min(1.0, cyc / CYCLES_FULL_SCALE)))
        e["_gravity"] = {"reach": len(t["reach"]), "layers": len(t["layers"]),
                         "edgeTypes": len(t["types"]), "cycles": cyc, "score": score}

        # критичность по слоям: основной — полная, прочие — по доле активности
        primary = next((l for l, p in layers_of.get(e["id"], []) if p), e["primary_layer"])
        base = per_layer_edges[e["id"]].get(primary, 0)
        for layer, is_primary in layers_of.get(e["id"], []):
            if is_primary or e["criticality"] is None:
                cl = e["criticality"]
            else:
                ratio = (per_layer_edges[e["id"]].get(layer, 0) / base) if base else 0.5
                cl = round(e["criticality"] * max(0.30, min(1.0, ratio)))
            con.execute("UPDATE nveco_entity_layer SET criticality=? "
                        "WHERE entity_id=? AND layer_id=?", (cl, e["id"], layer))

    # гравитация хранится вычисленной — дашборд ничего не считает
    con.execute("CREATE TABLE IF NOT EXISTS nveco_gravity ("
                "entity_id TEXT PRIMARY KEY, run_month TEXT, json TEXT)")
    for e in entities:
        con.execute("INSERT INTO nveco_gravity (entity_id, run_month, json) VALUES (?,?,?) "
                    "ON CONFLICT(entity_id) DO UPDATE SET run_month=excluded.run_month, "
                    "json=excluded.json",
                    (e["id"], month, json.dumps(e["_gravity"])))

    # ── концентрация слоя ────────────────────────────────────────────────────
    con.execute("CREATE TABLE IF NOT EXISTS nveco_layer_stat ("
                "run_month TEXT, layer_id TEXT, hhi REAL, level TEXT, top_json TEXT,"
                " UNIQUE(run_month, layer_id))")
    con.execute("DELETE FROM nveco_layer_stat WHERE run_month=?", (month,))
    for layer in nveco.layer_ids():
        rows = con.execute(
            """SELECT e.id AS id, COALESCE(el.criticality, 0) AS c
               FROM nveco_entity_layer el JOIN nveco_entity e ON e.id = el.entity_id
               WHERE el.layer_id=? ORDER BY c DESC, e.id""", (layer,)).fetchall()
        total = sum(r["c"] for r in rows)
        if total <= 0:
            hhi, level, top = None, None, []
        else:
            hhi = round(sum((r["c"] / total) ** 2 for r in rows), 4)
            level = ("monopoly" if hhi >= HHI_MONOPOLY else
                     "oligopoly" if hhi >= HHI_OLIGOPOLY else "competitive")
            top = [r["id"] for r in rows[:3] if r["c"] > 0]
        con.execute("INSERT INTO nveco_layer_stat (run_month,layer_id,hhi,level,top_json) "
                    "VALUES (?,?,?,?,?)", (month, layer, hhi, level, json.dumps(top)))

    # ── устаревание ──────────────────────────────────────────────────────────
    stale = 0
    for e in entities:
        lc = e["last_confirmed"]
        s = 1 if (not lc or nveco.months_between(lc, month) > STALE_MONTHS) else 0
        stale += s
        con.execute("UPDATE nveco_entity SET stale=? WHERE id=?", (s, e["id"]))
    con.commit()

    out = {
        "entities": len(entities), "clamped": clamped, "stale": stale,
        "anchor": acfg["id"],
        "status_mix": {s: con.execute("SELECT COUNT(*) c FROM nveco_edge WHERE status=?",
                                      (s,)).fetchone()["c"] for s in nveco.STATUSES},
        "top": [(r["id"], r["criticality"]) for r in con.execute(
            "SELECT id, criticality FROM nveco_entity "
            "WHERE criticality IS NOT NULL ORDER BY criticality DESC, id LIMIT 5")],
        "log": log,
    }
    con.close()
    return out


if __name__ == "__main__":
    print(run(sys.argv[1] if len(sys.argv) > 1 else nveco.current_month()))
