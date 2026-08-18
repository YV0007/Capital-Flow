"""Ecosystem handoff: SQLite -> handoff/ecosystem_map.json (+ ECOSYSTEM-CHANGELOG.md).

The frozen contract between this engine and the dashboard. The dashboard computes
NOTHING: criticality, gravity, concentration and cycles arrive already calculated; it only
draws. That is why this module is allowed to be boring — every interesting decision was
made upstream.

Two hard invariants, asserted before anything is written:
  * every edge endpoint resolves to a node in `nodes[]` (no dangling references);
  * every edge carries at least one evidence row (no quote, no edge).

Also written here: `engineConfirmed`, the free cross-check against the WEEKLY pipeline.
An `owns` / `stake` / `finances` edge that matches a dated event already in `events` is
flagged — the same fact arrived twice by two independent routes, which is the strongest
signal this repository can produce about itself.
"""

import json
import sys
from datetime import date

from . import db, eco

ECOSYSTEM = "ai-datacenters"
OUT_JSON = db.HANDOFF_DIR / "ecosystem_map.json"
OUT_MD = db.HANDOFF_DIR / "ECOSYSTEM-CHANGELOG.md"

ENGINE_CONFIRM_TYPES = {"owns", "stake", "finances"}
# Weekly event types that mean the same thing as an ecosystem capital edge.
_EVENT_MATCH = {
    "owns": {"acquisition", "corporate_investment", "sovereign_investment"},
    "stake": {"minority_stake", "equity", "funding_round", "follow_on",
              "corporate_investment", "sovereign_investment"},
    "finances": {"project_finance", "spv", "grant", "corporate_investment"},
}


def _norm(s):
    return " ".join((s or "").lower().split())


def _engine_confirmed(con, src_name, tgt_name, edge_type) -> bool:
    """Does the weekly pipeline already carry this ownership/financing fact as a dated
    event? Matched on canonical allocator name + a contained target name, which is as
    tight as the two vocabularies allow."""
    if edge_type not in ENGINE_CONFIRM_TYPES:
        return False
    allocator = db.resolve_name(src_name)
    types = _EVENT_MATCH[edge_type]
    rows = con.execute(
        """SELECT e.target, e.event_type FROM events e
           JOIN allocators a ON a.id = e.allocator_id
           WHERE lower(a.name) = ?""", (_norm(allocator),)).fetchall()
    tgt = _norm(db.resolve_name(tgt_name))
    for r in rows:
        if r["event_type"] not in types:
            continue
        t = _norm(r["target"])
        if t == tgt or tgt in t or t in tgt:
            return True
    return False


def _effective_tier(evidence):
    """The strongest tier among the LIVE evidence rows — that is what the line style
    reflects."""
    live = [e for e in evidence if e["alive"]] or evidence
    return min((e["tier"] for e in live), key=lambda t: eco.TIER_RANK.get(t, 9))


def build(month: str) -> dict:
    con = eco.connect()
    bands = eco.layer_bands()
    layer_cfg = eco.load_layers().get("layers", [])

    # ── layers (always 12, even when empty) ──────────────────────────────────
    stats = {r["layer"]: r for r in con.execute(
        "SELECT * FROM eco_layer_stats WHERE run_id=?", (month,))}
    layers = []
    for L in layer_cfg:
        st = stats.get(L["id"])
        conc = None
        if st and st["level"]:
            conc = {"level": st["level"], "hhi": st["hhi"],
                    "top": json.loads(st["top_json"] or "[]")}
        layers.append({"id": L["id"], "label": L["label"], "caption": L["caption"],
                       "band": bands[L["id"]], "concentration": conc})

    sectors = []
    for L in layer_cfg:
        for s in L.get("sectors", []):
            sectors.append({"key": s["key"], "label": s.get("label"), "layer": L["id"],
                            "dcNode": s.get("dc_node")})

    # ── nodes ────────────────────────────────────────────────────────────────
    tech_by_owner = {}
    tech_nodes = []
    for r in con.execute(
            """SELECT t.slug, t.label, t.note, n.slug AS owner
               FROM eco_tech_nodes t LEFT JOIN eco_nodes n ON n.id = t.owner_node_id
               ORDER BY t.slug"""):
        tech_nodes.append({"id": r["slug"], "label": r["label"], "owner": r["owner"],
                           "note": r["note"]})
        if r["owner"]:
            tech_by_owner.setdefault(r["owner"], []).append(r["slug"])

    scores = {r["node_id"]: r for r in con.execute(
        "SELECT * FROM eco_scores WHERE run_id=?", (month,))}
    node_layers = {}
    for r in con.execute(
            """SELECT node_id, layer, is_primary, criticality_in_layer
               FROM eco_node_layers"""):
        node_layers.setdefault(r["node_id"], []).append(r)

    nodes, node_slugs = [], set()
    for n in con.execute("SELECT * FROM eco_nodes ORDER BY slug"):
        sc = scores.get(n["id"])
        ls = sorted(node_layers.get(n["id"], []),
                    key=lambda r: eco.LAYER_INDEX[r["layer"]])
        nodes.append({
            "id": n["slug"], "name": n["name"], "role": n["role"], "sector": n["sector"],
            "layers": [{"layer": r["layer"], "primary": bool(r["is_primary"]),
                        "criticality": r["criticality_in_layer"]} for r in ls],
            "criticality": n["criticality"],
            "criticalityFactors": {"share": n["f_share"],
                                   "alternatives": n["f_alternatives"],
                                   "switchTime": n["f_switch_time"],
                                   "barrier": n["f_barrier"]},
            "gravity": {"nodes": sc["gravity_nodes"] if sc else 0,
                        "layers": sc["gravity_layers"] if sc else 0,
                        "edgeTypes": sc["gravity_edge_types"] if sc else 0,
                        "score": sc["gravity_score"] if sc else 0},
            "oneLiner": n["one_liner"], "whatBreaksIt": n["what_breaks_it"],
            "shareNote": n["share_note"],
            "ticker": n["ticker"], "publicPrivate": n["public_private"], "geo": n["geo"],
            "tier": n["tier"], "techNodes": tech_by_owner.get(n["slug"], []),
            "dcNode": n["dc_node"], "firstSeen": n["first_seen"],
            "lastConfirmed": n["last_confirmed"], "stale": bool(n["stale"]),
        })
        node_slugs.add(n["slug"])

    # ── edges ────────────────────────────────────────────────────────────────
    ev_by_edge = {}
    for r in con.execute("SELECT * FROM eco_evidence ORDER BY id"):
        ev_by_edge.setdefault(r["edge_id"], []).append(
            {"quote": r["quote"], "url": r["source_url"], "tier": r["source_tier"],
             "published": r["published_date"], "fetched": r["fetched_date"],
             "alive": bool(r["alive"])})

    edges = []
    for e in con.execute(
            """SELECT e.*, s.slug AS s_slug, s.name AS s_name, t.slug AS t_slug,
                      t.name AS t_name, tn.slug AS tech
               FROM eco_edges e
               JOIN eco_nodes s ON s.id = e.source_id
               JOIN eco_nodes t ON t.id = e.target_id
               LEFT JOIN eco_tech_nodes tn ON tn.id = e.tech_node_id
               ORDER BY e.slug"""):
        evidence = ev_by_edge.get(e["id"], [])
        if not evidence:
            raise AssertionError(
                f"contract violation: edge {e['slug']} has no evidence — the iron rule is "
                "enforced at ingest, so this means the DB was edited by hand")
        confirmed = sum(1 for x in evidence if x["alive"])
        edges.append({
            "id": e["slug"], "source": e["s_slug"], "target": e["t_slug"],
            "type": e["edge_type"], "spine": e["spine"], "strength": e["strength"],
            "techNode": e["tech"], "status": e["status"],
            "tier": _effective_tier(evidence),
            "confirmedSources": confirmed or len(evidence),
            "engineConfirmed": _engine_confirmed(con, e["s_name"], e["t_name"],
                                                 e["edge_type"]),
            "started": e["started"], "lastConfirmed": e["last_confirmed"],
            "note": e["note"], "evidence": evidence,
        })
        for end in ("source", "target"):
            if edges[-1][end] not in node_slugs:
                raise AssertionError(
                    f"contract violation: edge {e['slug']} {end} "
                    f"'{edges[-1][end]}' is not in nodes[]")

    # persist engineConfirmed so it is queryable, not just emitted
    for x in edges:
        con.execute("UPDATE eco_edges SET engine_confirmed=? WHERE slug=?",
                    (1 if x["engineConfirmed"] else 0, x["id"]))
    con.commit()

    cycles = [{"id": r["slug"], "type": r["cycle_type"],
               "path": json.loads(r["path_json"]), "edges": json.loads(r["edges_json"]),
               "note": r["note"]}
              for r in con.execute(
                  "SELECT * FROM eco_cycles WHERE run_id=? ORDER BY slug", (month,))]

    payload = {
        "generated": date.today().isoformat(),
        "asOf": month,
        "source": "engine",
        "ecosystem": ECOSYSTEM,
        "totals": {"nodes": len(nodes), "edges": len(edges), "layers": len(layers),
                   "cycles": len(cycles)},
        "layers": layers,
        "sectors": sectors,
        "nodes": nodes,
        "techNodes": tech_nodes,
        "edges": edges,
        "cycles": cycles,
    }
    con.close()
    return payload


# ── changelog ────────────────────────────────────────────────────────────────
def _diff(prev, cur):
    """A 10–20 line diff is the ONLY thing the user is expected to read each month, so
    this reports facts that change the picture, not every field that moved."""
    added, removed, changed = [], [], []
    if not prev:
        return {"added": [{"kind": "run", "id": cur["asOf"],
                           "why": "первый прогон — базовая линия"}],
                "removed": [], "changed": []}

    pn = {n["id"]: n for n in prev.get("nodes", [])}
    cn = {n["id"]: n for n in cur.get("nodes", [])}
    pe = {e["id"]: e for e in prev.get("edges", [])}
    ce = {e["id"]: e for e in cur.get("edges", [])}

    for i in sorted(set(cn) - set(pn)):
        added.append({"kind": "node", "id": i,
                      "why": cn[i].get("oneLiner") or "новый узел"})
    for i in sorted(set(pn) - set(cn)):
        removed.append({"kind": "node", "id": i, "why": "узел больше не подтверждается"})
    for i in sorted(set(ce) - set(pe)):
        e = ce[i]
        added.append({"kind": "edge", "id": i,
                      "why": e.get("note") or f"{e['type']}, strength {e['strength']}"})
    for i in sorted(set(pe) - set(ce)):
        removed.append({"kind": "edge", "id": i, "why": "ребро больше не заявлено"})

    for i in sorted(set(cn) & set(pn)):
        for field in ("criticality", "role", "tier", "stale"):
            a, b = pn[i].get(field), cn[i].get(field)
            if a != b:
                changed.append({"kind": "node", "id": i, "field": field,
                                "from": a, "to": b})
    for i in sorted(set(ce) & set(pe)):
        for field in ("status", "strength", "confirmedSources", "engineConfirmed"):
            a, b = pe[i].get(field), ce[i].get(field)
            if a != b:
                changed.append({"kind": "edge", "id": i, "field": field,
                                "from": a, "to": b})
    return {"added": added, "removed": removed, "changed": changed}


def _changelog_md(cur, diff) -> str:
    t = cur["totals"]
    L = [f"# ECOSYSTEM — {cur['asOf']}", "",
         f"Карта: **{t['nodes']} узлов**, **{t['edges']} рёбер**, "
         f"**{t['cycles']} замкнутых контуров**. Сгенерировано {cur['generated']}.", ""]

    dashed = sum(1 for e in cur["edges"] if e["confirmedSources"] < 2)
    unver = sum(1 for e in cur["edges"] if e["status"] == "unverified")
    econf = sum(1 for e in cur["edges"] if e["engineConfirmed"])
    L += ["## Состояние",
          f"- Сплошных линий (≥2 источника): **{t['edges'] - dashed}**, пунктиром: {dashed}.",
          f"- Погасших рёбер (источник мёртв): **{unver}**.",
          f"- Подтверждено недельным движком: **{econf}**.",
          f"- Блёкнущих узлов (>6 мес. без подтверждения): "
          f"**{sum(1 for n in cur['nodes'] if n['stale'])}**.", ""]

    def _block(title, rows, fmt, limit=12):
        if not rows:
            return [f"## {title}", "— ничего.", ""]
        out = [f"## {title} ({len(rows)})"]
        out += [fmt(r) for r in rows[:limit]]
        if len(rows) > limit:
            out.append(f"- …и ещё {len(rows) - limit}.")
        return out + [""]

    L += _block("Добавлено", diff["added"],
                lambda r: f"- **{r['kind']}** `{r['id']}` — {r['why']}")
    L += _block("Отвалилось", diff["removed"],
                lambda r: f"- **{r['kind']}** `{r['id']}` — {r['why']}")
    L += _block("Изменилось", diff["changed"],
                lambda r: f"- **{r['kind']}** `{r['id']}`: {r['field']} "
                          f"{r['from']} → {r['to']}")

    if cur["cycles"]:
        L += ["## Замкнутые контуры"]
        L += [f"- `{c['id']}` **{c['type']}** — {' → '.join(c['path'])}"
              for c in cur["cycles"][:10]]
        L += [""]

    tight = sorted((l for l in cur["layers"]
                    if l["concentration"] and l["concentration"]["level"] == "monopoly"),
                   key=lambda l: -(l["concentration"]["hhi"] or 0))
    if tight:
        L += ["## Слои под одним владельцем"]
        L += [f"- **{l['id']} {l['label']}** — HHI {l['concentration']['hhi']}, "
              f"держат: {', '.join(l['concentration']['top'])}" for l in tight]
        L += [""]
    return "\n".join(L)


def run(month: str) -> dict:
    prev = None
    if OUT_JSON.exists():
        try:
            prev = json.loads(OUT_JSON.read_text())
        except json.JSONDecodeError:
            prev = None
    payload = build(month)
    # Diffing against whatever was shipped last is right in both cases: a new month shows
    # the month's delta, and a re-run of the same month shows only what actually moved
    # (which is how idempotency becomes visible instead of merely claimed).
    diff = _diff(prev, payload)
    payload["changelog"] = {"month": month, **diff}

    db.HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    OUT_MD.write_text(_changelog_md(payload, diff))
    return {"nodes": payload["totals"]["nodes"], "edges": payload["totals"]["edges"],
            "cycles": payload["totals"]["cycles"],
            "added": len(diff["added"]), "removed": len(diff["removed"]),
            "changed": len(diff["changed"]), "path": str(OUT_JSON)}


if __name__ == "__main__":
    print(run(sys.argv[1] if len(sys.argv) > 1 else eco.current_month()))
