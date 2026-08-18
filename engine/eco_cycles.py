"""Ecosystem cycle detection — the one lens with no judgement in it.

A cycle is a property of the graph: if NVIDIA holds a stake in OpenAI, OpenAI buys compute
from CoreWeave, and CoreWeave buys GPUs from NVIDIA, the loop exists whether or not anyone
finds it flattering. §4.3 of the plan calls this the cheapest and probably strongest lens
on the screen, and it is the thing the ecosystem map can show that the flow map cannot.

Two motors, told apart by what closes the loop:
  `sales`     — mostly physical edges: a stake in a customer comes back as a purchase.
  `financing` — mostly capital edges: build the asset, sign the contract, the contract
                makes the asset financeable, raise capital against it.

Deduped by the SET of participants, so one loop is reported once regardless of which
member you happen to start from.
"""

import json
import sys

from . import eco

# Read in the MONEY direction (payer → payee), which is how the cycle is traversed.
TYPE_RU = {
    "supply": "платит за поставку", "offtake": "платит за мощность",
    "platform": "платит за платформу", "partner": "платит партнёру",
    "owns": "владеет", "stake": "держит долю в", "finances": "финансирует",
    "develops": "создаёт актив", "operates": "платит за эксплуатацию",
}


def _graph(con):
    """Adjacency over ACTIVE edges only — an unverified or expired edge must not close a
    loop, or the map would claim a circle it can no longer prove.

    IMPORTANT — the graph is built in the MONEY direction, which is not the direction the
    edges are stored in. Edges are stored supplier → consumer (goods), because that is the
    rule the taxonomy states and the one that makes `asml__tsmc__supply` read correctly.
    Money runs the other way down a physical edge (the consumer pays the supplier) and the
    same way along a capital edge (the investor funds the investee).

    Reversing the physical spine here is what makes the loop in §4.3 of the plan appear at
    all: NVIDIA funds OpenAI, OpenAI pays CoreWeave, CoreWeave pays NVIDIA. In goods
    direction those three edges form a plain chain and nothing closes. A "circular deal"
    is a statement about money, so the money graph is the one to search.
    """
    adj, meta, names = {}, {}, {}
    for r in con.execute(
            """SELECT e.slug, e.edge_type, e.strength, s.slug AS s, t.slug AS t,
                      s.name AS sname, t.name AS tname
               FROM eco_edges e
               JOIN eco_nodes s ON s.id = e.source_id
               JOIN eco_nodes t ON t.id = e.target_id
               WHERE e.status = 'active'"""):
        payer, payee = ((r["s"], r["t"]) if r["edge_type"] in eco.CAPITAL_TYPES
                        else (r["t"], r["s"]))
        cand = {"slug": r["slug"], "type": r["edge_type"], "strength": r["strength"]}
        cur = meta.get((payer, payee))
        # Two nodes can be joined by several edges in the same money direction
        # (Microsoft holds a stake in OpenAI AND licenses its models). One of them has
        # to represent the pair in the cycle; pick deterministically — strongest, then
        # alphabetical — so the same data always yields the same cycles.
        if cur is None:
            adj.setdefault(payer, []).append(payee)
            meta[(payer, payee)] = cand
        elif (-cand["strength"], cand["slug"]) < (-cur["strength"], cur["slug"]):
            meta[(payer, payee)] = cand
        names[r["s"]], names[r["t"]] = r["sname"], r["tname"]
    return adj, meta, names


def find_cycles(adj, min_len=3, max_len=5, cap=20000):
    """Enumerate simple directed cycles of length min_len..max_len.

    Each cycle is only emitted from its lexicographically smallest member, and the DFS
    never steps onto a node smaller than that start — the standard trick that keeps one
    cycle from being found once per rotation. `cap` is a runaway guard, not a design
    limit: at map scale (hundreds of edges) it is never reached.
    """
    found, steps = {}, 0
    for start in sorted(adj):
        stack = [(start, [start])]
        while stack:
            node, path = stack.pop()
            steps += 1
            if steps > cap:
                return list(found.values())
            for nxt in adj.get(node, []):
                if nxt == start and len(path) >= min_len:
                    key = frozenset(path)
                    if key not in found:
                        found[key] = list(path)
                    continue
                if len(path) >= max_len or nxt <= start or nxt in path:
                    continue
                stack.append((nxt, path + [nxt]))
    return list(found.values())


def classify(types) -> str:
    """Majority of capital-spine edge types -> financing, else sales. A tie goes to
    `financing`: an ownership link inside a loop is the more consequential reading."""
    cap = sum(1 for t in types if t in eco.CAPITAL_TYPES)
    return "financing" if cap * 2 >= len(types) else "sales"


def _note(path, meta, names, kind):
    parts = []
    for a, b in zip(path, path[1:] + [path[0]]):
        m = meta[(a, b)]
        parts.append(f"{names.get(a, a)} —{TYPE_RU.get(m['type'], m['type'])}→ "
                     f"{names.get(b, b)}")
    head = "Контур сбыта" if kind == "sales" else "Контур финансирования"
    return f"{head}: " + "; ".join(parts)


def run(month: str) -> dict:
    con = eco.connect()
    rules = (eco.load_rules().get("cycles") or {})
    min_len = int(rules.get("min_length", 3))
    max_len = int(rules.get("max_length", 5))

    adj, meta, names = _graph(con)
    cycles = find_cycles(adj, min_len, max_len)
    # Deterministic order: shortest first, then strongest, then alphabetical — so the
    # ids c1, c2 … are stable across reruns of the same data.
    def _strength(path):
        return sum(meta[(a, b)]["strength"]
                   for a, b in zip(path, path[1:] + [path[0]]))
    cycles.sort(key=lambda p: (len(p), -_strength(p), p))

    con.execute("DELETE FROM eco_cycles WHERE run_id=?", (month,))
    out = []
    for i, path in enumerate(cycles, start=1):
        pairs = list(zip(path, path[1:] + [path[0]]))
        types = [meta[p]["type"] for p in pairs]
        kind = classify(types)
        edge_slugs = [meta[p]["slug"] for p in pairs]
        rec = {"slug": f"c{i}", "type": kind, "path": path + [path[0]],
               "edges": edge_slugs, "note": _note(path, meta, names, kind)}
        con.execute(
            """INSERT OR IGNORE INTO eco_cycles
                 (run_id, slug, cycle_type, path_json, edges_json, members, note)
               VALUES (?,?,?,?,?,?,?)""",
            (month, rec["slug"], kind, json.dumps(rec["path"]),
             json.dumps(edge_slugs), "|".join(sorted(path)), rec["note"]))
        out.append(rec)
    con.commit()
    con.close()
    return {"cycles": len(out),
            "sales": sum(1 for c in out if c["type"] == "sales"),
            "financing": sum(1 for c in out if c["type"] == "financing"),
            "detail": out}


if __name__ == "__main__":
    r = run(sys.argv[1] if len(sys.argv) > 1 else eco.current_month())
    print(f"{r['cycles']} cycles ({r['sales']} sales, {r['financing']} financing)")
    for c in r["detail"]:
        print(" ", c["slug"], c["type"], " -> ".join(c["path"]))
