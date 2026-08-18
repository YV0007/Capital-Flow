"""Ecosystem scoring: criticality, gravity, layer concentration.

Pure arithmetic over what the agents already stored. No judgement is made here and none
may be added — every input is a 0..5 factor an agent wrote down with a sourced note, and
the whole point of the rubric is that the node panel can show WHY a score is 98 instead
of asserting it.

  criticality = round(100 * (0.30*share + 0.30*alternatives + 0.25*switch_time
                             + 0.15*barrier) / 5)
  ASML 5/5/5/5 -> 100.  A commodity ODM 2/1/1/1 -> 26.

Gravity is deliberately a DIFFERENT number: how much of the map a node touches. Microsoft
scores high on gravity and moderately on criticality; ASML the reverse. They are reported
side by side and never blended.
"""

import json
import sys

from . import eco

# Per-layer criticality for a NON-primary layer. The rubric factors describe the company
# as a whole, so a secondary layer is scaled by how much of the node's edge activity
# actually happens there (see ECOSYSTEM-BUILD-LOG.md — this is the one derived number on
# the map, and it only affects capsule thickness, never the headline score).
SECONDARY_MIN, SECONDARY_MAX = 0.30, 1.00
SECONDARY_DEFAULT = 0.50


def criticality(f_share, f_alternatives, f_switch_time, f_barrier, weights=None) -> int:
    w = weights or {"share": 0.30, "alternatives": 0.30, "switch_time": 0.25,
                    "barrier": 0.15}
    vals = {"share": f_share, "alternatives": f_alternatives,
            "switch_time": f_switch_time, "barrier": f_barrier}
    if any(v is None for v in vals.values()):
        return 0
    return round(100 * sum(w[k] * vals[k] for k in w) / 5)


def _edges_of(con):
    """All edges with both endpoints resolved to slugs. Expired edges still count for
    gravity — a relationship that ended still shaped the map this month; only
    `unverified` (we can no longer prove it) is dropped."""
    return con.execute(
        """SELECT e.id, e.edge_type, e.strength, e.status,
                  s.id AS sid, s.slug AS s_slug, t.id AS tid, t.slug AS t_slug
           FROM eco_edges e
           JOIN eco_nodes s ON s.id = e.source_id
           JOIN eco_nodes t ON t.id = e.target_id
           WHERE e.status != 'unverified'""").fetchall()


def _primary_layer(layers):
    for l, p in layers:
        if p:
            return l
    return layers[0][0] if layers else None


def run(month: str) -> dict:
    con = eco.connect()
    rules = eco.load_rules()
    weights = (rules.get("criticality") or {}).get("weights")
    g = rules.get("gravity") or {}
    gw = g.get("weights") or {"nodes": 0.5, "layers": 0.3, "edge_types": 0.2}
    full_scale = float(g.get("nodes_full_scale", 25))
    conc = rules.get("concentration") or {}
    mono, oligo = float(conc.get("monopoly_hhi", 0.5)), float(conc.get("oligopoly_hhi", 0.25))

    nodes = {r["id"]: dict(r) for r in con.execute("SELECT * FROM eco_nodes")}
    layers_of = {}
    for r in con.execute("SELECT node_id, layer, is_primary FROM eco_node_layers"):
        layers_of.setdefault(r["node_id"], []).append((r["layer"], r["is_primary"]))
    for nid in nodes:
        layers_of.setdefault(nid, [])

    edges = _edges_of(con)

    # ── criticality ──────────────────────────────────────────────────────────
    for nid, n in nodes.items():
        n["criticality"] = criticality(n["f_share"], n["f_alternatives"],
                                       n["f_switch_time"], n["f_barrier"], weights)
        con.execute("UPDATE eco_nodes SET criticality=? WHERE id=?",
                    (n["criticality"], nid))

    # ── gravity + per-layer edge attribution ─────────────────────────────────
    touch = {nid: {"nodes": set(), "layers": set(), "types": set()} for nid in nodes}
    per_layer_edges = {nid: {} for nid in nodes}
    for e in edges:
        for me, other in ((e["sid"], e["tid"]), (e["tid"], e["sid"])):
            if me not in touch:
                continue
            touch[me]["nodes"].add(other)
            touch[me]["types"].add(e["edge_type"])
            for l, _ in layers_of.get(other, []):
                touch[me]["layers"].add(l)
            # Attribute the edge to whichever of MY layers sits closest to the
            # counterparty's primary layer — that is the layer the relationship
            # physically runs through.
            opl = _primary_layer(layers_of.get(other, []))
            mine = [l for l, _ in layers_of.get(me, [])]
            if opl and mine:
                best = min(mine, key=lambda l: abs(eco.LAYER_INDEX[l] - eco.LAYER_INDEX[opl]))
                per_layer_edges[me][best] = per_layer_edges[me].get(best, 0) + 1

    for nid, n in nodes.items():
        t = touch[nid]
        nodes_norm = min(1.0, len(t["nodes"]) / full_scale) if full_scale else 0.0
        score = round(100 * (gw["nodes"] * nodes_norm
                             + gw["layers"] * len(t["layers"]) / 12
                             + gw["edge_types"] * len(t["types"]) / 10))
        con.execute(
            """INSERT INTO eco_scores (node_id, run_id, criticality, gravity_nodes,
                 gravity_layers, gravity_edge_types, gravity_score)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(node_id, run_id) DO UPDATE SET
                 criticality=excluded.criticality, gravity_nodes=excluded.gravity_nodes,
                 gravity_layers=excluded.gravity_layers,
                 gravity_edge_types=excluded.gravity_edge_types,
                 gravity_score=excluded.gravity_score""",
            (nid, month, n["criticality"], len(t["nodes"]), len(t["layers"]),
             len(t["types"]), score))

        # per-layer criticality (capsule thickness)
        primary = _primary_layer(layers_of[nid])
        base = per_layer_edges[nid].get(primary, 0)
        for layer, is_primary in layers_of[nid]:
            if is_primary:
                cl = n["criticality"]
            else:
                if base:
                    ratio = per_layer_edges[nid].get(layer, 0) / base
                else:
                    ratio = SECONDARY_DEFAULT
                ratio = max(SECONDARY_MIN, min(SECONDARY_MAX, ratio))
                cl = round(n["criticality"] * ratio)
            con.execute(
                "UPDATE eco_node_layers SET criticality_in_layer=? WHERE node_id=? AND layer=?",
                (cl, nid, layer))

    # ── layer concentration (HHI over criticality_in_layer shares) ───────────
    con.execute("DELETE FROM eco_layer_stats WHERE run_id=?", (month,))
    for layer in eco.LAYERS:
        rows = con.execute(
            """SELECT n.slug AS slug, COALESCE(nl.criticality_in_layer, 0) AS c
               FROM eco_node_layers nl JOIN eco_nodes n ON n.id = nl.node_id
               WHERE nl.layer = ? ORDER BY c DESC, n.slug""", (layer,)).fetchall()
        total = sum(r["c"] for r in rows)
        if total <= 0:
            hhi, level, top = None, None, []
        else:
            hhi = round(sum((r["c"] / total) ** 2 for r in rows), 4)
            level = "monopoly" if hhi >= mono else ("oligopoly" if hhi >= oligo
                                                    else "competitive")
            top = [r["slug"] for r in rows[:3] if r["c"] > 0]
        con.execute(
            """INSERT INTO eco_layer_stats (run_id, layer, hhi, level, top_json)
               VALUES (?,?,?,?,?)""",
            (month, layer, hhi, level, json.dumps(top)))

    # ── staleness (§7.4): nothing confirming it for N months -> it fades ──────
    months = int((rules.get("staleness") or {}).get("months", 6))
    for nid in nodes:
        newest = con.execute(
            """SELECT MAX(e.last_confirmed) AS m FROM eco_edges e
               WHERE (e.source_id=? OR e.target_id=?) AND e.status='active'""",
            (nid, nid)).fetchone()["m"]
        stale = 1 if (not newest or eco.months_between(newest, month) > months) else 0
        con.execute("UPDATE eco_nodes SET last_confirmed=?, stale=? WHERE id=?",
                    (newest, stale, nid))

    con.commit()
    out = {
        "nodes": len(nodes),
        "top": [(r["slug"], r["criticality"]) for r in con.execute(
            "SELECT slug, criticality FROM eco_nodes ORDER BY criticality DESC LIMIT 5")],
        "layers_scored": con.execute(
            "SELECT COUNT(*) c FROM eco_layer_stats WHERE run_id=? AND hhi IS NOT NULL",
            (month,)).fetchone()["c"],
        "stale": con.execute("SELECT COUNT(*) c FROM eco_nodes WHERE stale=1").fetchone()["c"],
    }
    con.close()
    return out


if __name__ == "__main__":
    print(run(sys.argv[1] if len(sys.argv) > 1 else eco.current_month()))
