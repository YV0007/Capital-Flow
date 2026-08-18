"""Validate handoff/ecosystem_map.json against the FROZEN handoff contract.

Run after every monthly pipeline. The contract is the only point where this engine and
the dashboard touch, so a violation here is worse than a crash — it ships a map that
renders wrong. Exit code 1 on any error.

  python tools/eco_validate.py [path]
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine.eco_score import criticality           # noqa: E402

EDGE_TYPES = {"supply", "offtake", "platform", "partner", "compete", "owns", "stake",
              "finances", "develops", "operates"}
TIERS = {"filing", "company_pr", "transcript", "press", "estimate"}
ROLES = {"producer", "owner", "capital", "demand", "platform"}
LEVELS = {"monopoly", "oligopoly", "competitive"}
BAND = {"L1": 1, "L2": 1, "L3": 2, "L4": 2, "L5": 3, "L6": 3, "L7": 3,
        "L8": 4, "L9": 4, "L10": 4, "L11": 5, "L12": 5}


def validate(path: Path):
    d = json.loads(path.read_text())
    errs, warns = [], []

    for k in ("generated", "asOf", "source", "ecosystem", "totals", "layers", "sectors",
              "nodes", "techNodes", "edges", "cycles", "changelog"):
        if k not in d:
            errs.append(f"missing top-level key '{k}'")
    if errs:
        return errs, warns

    # 4. layers: always 12
    if len(d["layers"]) != 12:
        errs.append(f"layers must be 12 entries, got {len(d['layers'])}")
    for L in d["layers"]:
        if BAND.get(L["id"]) != L.get("band"):
            errs.append(f"layer {L['id']}: band {L.get('band')} != {BAND.get(L['id'])}")
        c = L.get("concentration")
        if c and c.get("level") not in LEVELS:
            errs.append(f"layer {L['id']}: bad concentration level {c.get('level')}")

    t = d["totals"]
    for key, seq in (("nodes", d["nodes"]), ("edges", d["edges"]),
                     ("layers", d["layers"]), ("cycles", d["cycles"])):
        if t.get(key) != len(seq):
            errs.append(f"totals.{key}={t.get(key)} but {key} has {len(seq)}")

    # 1. stable ids + uniqueness
    ids = [n["id"] for n in d["nodes"]]
    if len(ids) != len(set(ids)):
        errs.append("duplicate node ids")
    node_ids = set(ids)
    layer_ids = {L["id"] for L in d["layers"]}
    sector_keys = {s["key"] for s in d["sectors"]}

    for n in d["nodes"]:
        if n["role"] not in ROLES:
            errs.append(f"node {n['id']}: bad role {n['role']}")
        if not n.get("layers"):
            errs.append(f"node {n['id']}: no layers")
        if sum(1 for l in n["layers"] if l.get("primary")) != 1:
            errs.append(f"node {n['id']}: must have exactly one primary layer")
        for l in n["layers"]:
            if l["layer"] not in layer_ids:
                errs.append(f"node {n['id']}: unknown layer {l['layer']}")
        # 5. criticality must reconcile with the rubric
        f = n["criticalityFactors"]
        expect = criticality(f["share"], f["alternatives"], f["switchTime"], f["barrier"])
        if expect != n["criticality"]:
            errs.append(f"node {n['id']}: criticality {n['criticality']} != rubric "
                        f"{expect} from {f}")
        prim = [l for l in n["layers"] if l.get("primary")]
        if prim and prim[0]["criticality"] != n["criticality"]:
            errs.append(f"node {n['id']}: primary-layer criticality "
                        f"{prim[0]['criticality']} != node criticality {n['criticality']}")
        if n.get("sector") and n["sector"] not in sector_keys:
            warns.append(f"node {n['id']}: sector '{n['sector']}' not in sectors[]")

    tech_ids = {x["id"] for x in d["techNodes"]}
    for x in d["techNodes"]:
        if x.get("owner") and x["owner"] not in node_ids:
            warns.append(f"techNode {x['id']}: owner '{x['owner']}' not on the map")

    edge_ids = set()
    for e in d["edges"]:
        # 2. no dangling references
        for end in ("source", "target"):
            if e[end] not in node_ids:
                errs.append(f"edge {e['id']}: {end} '{e[end]}' not in nodes[]")
        if e["id"] != f"{e['source']}__{e['target']}__{e['type']}":
            errs.append(f"edge {e['id']}: id does not match "
                        f"<source>__<target>__<type>")
        if e["id"] in edge_ids:
            errs.append(f"duplicate edge id {e['id']}")
        edge_ids.add(e["id"])
        if e["type"] not in EDGE_TYPES:
            errs.append(f"edge {e['id']}: bad type {e['type']}")
        if e["type"] == "compete":
            errs.append(f"edge {e['id']}: `compete` is not collected in v1")
        if e["spine"] not in ("physical", "capital"):
            errs.append(f"edge {e['id']}: bad spine {e['spine']}")
        if not 0 <= e["strength"] <= 100:
            errs.append(f"edge {e['id']}: strength out of range")
        if e["tier"] not in TIERS:
            errs.append(f"edge {e['id']}: bad tier {e['tier']}")
        if e.get("techNode") and e["techNode"] not in tech_ids:
            errs.append(f"edge {e['id']}: unknown techNode {e['techNode']}")
        # 3. evidence is non-empty for EVERY edge
        if not e.get("evidence"):
            errs.append(f"edge {e['id']}: empty evidence — no quote, no edge")
        for ev in e.get("evidence", []):
            if not ev.get("quote") or not ev.get("url"):
                errs.append(f"edge {e['id']}: evidence row missing quote or url")
            if ev.get("tier") not in TIERS:
                errs.append(f"edge {e['id']}: evidence tier {ev.get('tier')}")
        live = sum(1 for ev in e.get("evidence", []) if ev.get("alive"))
        if e["confirmedSources"] not in (live, len(e.get("evidence", []))):
            warns.append(f"edge {e['id']}: confirmedSources={e['confirmedSources']} "
                         f"vs {live} live / {len(e['evidence'])} total")

    for c in d["cycles"]:
        if c["type"] not in ("sales", "financing"):
            errs.append(f"cycle {c['id']}: bad type {c['type']}")
        if c["path"][0] != c["path"][-1]:
            errs.append(f"cycle {c['id']}: path must return to its first node")
        for s in c["path"]:
            if s not in node_ids:
                errs.append(f"cycle {c['id']}: node '{s}' not on the map")
        for s in c["edges"]:
            if s not in edge_ids:
                errs.append(f"cycle {c['id']}: edge '{s}' not on the map")
    return errs, warns


if __name__ == "__main__":
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "handoff/ecosystem_map.json"
    if not p.exists():
        print(f"FAIL: {p} does not exist")
        sys.exit(1)
    errors, warnings = validate(p)
    for w in warnings:
        print("WARN", w)
    for e in errors:
        print("ERR ", e)
    print(f"{'FAIL' if errors else 'PASS'}: {len(errors)} errors, "
          f"{len(warnings)} warnings — {p}")
    sys.exit(1 if errors else 0)
