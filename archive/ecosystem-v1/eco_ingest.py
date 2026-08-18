"""Ecosystem ingest: agent CSVs -> validate -> resolve -> dedupe -> SQLite.

Reads runs/<YYYY-MM>/eco-*/{nodes,edges,source_log}.csv, validates every row against the
frozen contract, resolves company names to permanent slugs through the SAME alias table
the weekly pipeline uses, and upserts into the eco_* tables.

Two things this module refuses to do, ever:
  * write an edge with no verbatim quote + resolved URL (the iron rule);
  * write a second node for a company that already exists in another layer.

Rejected rows are not printed and forgotten — they are written to
runs/<month>/rejects.csv with the reason, which is what the next run hands back to the
agents (same feedback loop as the weekly pipeline's ingest_problems).

Idempotent: re-running the same month updates in place (slug is the key) and never
duplicates a node, an edge or an evidence row.
"""

import csv
import json
import sys
from datetime import date

from . import db, eco
from .ingest import is_search_url

NODE_COLUMNS = ["name", "layers", "sector", "role", "tier", "ticker", "public_private",
                "geo", "f_share", "f_alternatives", "f_switch_time", "f_barrier",
                "share_note", "one_liner", "what_breaks_it", "dc_node"]
EDGE_COLUMNS = ["source", "target", "edge_type", "spine", "strength", "tech_node",
                "started", "evidence_quote", "source_url", "source_tier",
                "published_date", "note"]

FACTORS = ["f_share", "f_alternatives", "f_switch_time", "f_barrier"]


def _s(row, key):
    return (row.get(key) or "").strip()


def _int(value, lo, hi):
    """Parse a bounded integer. Returns (value|None, error|None)."""
    v = (value or "").strip()
    if v == "":
        return None, "empty"
    try:
        n = int(float(v))
    except ValueError:
        return None, f"not a number: '{v}'"
    if not lo <= n <= hi:
        return None, f"{n} out of range {lo}..{hi}"
    return n, None


def _parse_layers(spec: str):
    """'L3:primary|L10|L12' -> ([('L3',1),('L10',0),('L12',0)], errors).

    Exactly one primary. A single-layer node without the marker gets it implicitly —
    that is the common case and making agents type ':primary' on it buys nothing.
    """
    errors = []
    parts = [p.strip() for p in (spec or "").split("|") if p.strip()]
    if not parts:
        return [], ["missing layers"]
    out, primaries = [], 0
    for p in parts:
        bits = [b.strip() for b in p.split(":")]
        layer = bits[0].upper()
        is_primary = len(bits) > 1 and bits[1].lower() in ("primary", "1", "true")
        if layer not in eco.LAYER_INDEX:
            errors.append(f"bad layer '{layer}'")
            continue
        if any(l == layer for l, _ in out):
            errors.append(f"layer '{layer}' listed twice")
            continue
        primaries += is_primary
        out.append((layer, 1 if is_primary else 0))
    if not out:
        return [], errors or ["no valid layer"]
    if primaries == 0:
        if len(out) == 1:
            out[0] = (out[0][0], 1)
        else:
            errors.append("several layers but none marked :primary")
    elif primaries > 1:
        errors.append("more than one layer marked :primary")
    return out, errors


# ── node rows ────────────────────────────────────────────────────────────────
def _validate_node(row, sectors):
    """Returns (clean|None, errors, warnings)."""
    errors, warnings = [], []
    name = _s(row, "name")
    if not name:
        return None, ["missing name"], []

    layers, lerr = _parse_layers(_s(row, "layers"))
    errors += lerr

    role = _s(row, "role").lower()
    if role not in eco.ROLES:
        errors.append(f"bad role '{role}' (producer|owner|capital|demand|platform)")
    tier = _s(row, "tier").lower() or "core"
    if tier not in eco.NODE_TIERS:
        errors.append(f"bad tier '{tier}' (anchor|core|emerging)")

    factors = {}
    for f in FACTORS:
        v, err = _int(row.get(f), 0, 5)
        if err:
            errors.append(f"{f}: {err} (rubric needs all four 0..5)")
        factors[f] = v

    pp = _s(row, "public_private")
    if pp and pp not in ("Pub", "Pvt"):
        errors.append(f"bad public_private '{pp}' (Pub|Pvt)")

    sector = _s(row, "sector") or None
    dc_node = _s(row, "dc_node") or None
    if sector:
        meta = sectors.get(sector)
        if not meta:
            warnings.append(f"sector '{sector}' not in the frozen taxonomy")
        else:
            if layers and meta["layer"] not in [l for l, _ in layers]:
                warnings.append(
                    f"sector '{sector}' belongs to {meta['layer']}, which is not among "
                    f"this node's layers")
            dc_node = dc_node or meta["dc_node"]

    if not _s(row, "share_note") and not errors:
        warnings.append("no share_note — f_share is unsourced")

    if errors:
        return None, errors, warnings
    return {
        "name": name, "layers": layers, "sector": sector, "role": role, "tier": tier,
        "ticker": _s(row, "ticker") or None, "public_private": pp or None,
        "geo": _s(row, "geo") or None, "share_note": _s(row, "share_note") or None,
        "one_liner": _s(row, "one_liner") or None,
        "what_breaks_it": _s(row, "what_breaks_it") or None,
        "dc_node": dc_node, **factors,
    }, [], warnings


# ── edge rows ────────────────────────────────────────────────────────────────
def _validate_edge(row, min_quote, tech_slugs):
    errors, warnings = [], []
    source, target = _s(row, "source"), _s(row, "target")
    if not source:
        errors.append("missing source")
    if not target:
        errors.append("missing target")

    etype = _s(row, "edge_type").lower()
    if etype in eco.EXCLUDED_EDGE_TYPES:
        errors.append(f"edge_type '{etype}' is not collected in v1")
    elif etype not in eco.EDGE_TYPES:
        errors.append(f"bad edge_type '{etype}'")

    strength, err = _int(row.get("strength"), 0, 100)
    if err:
        errors.append(f"strength: {err}")

    quote = (row.get("evidence_quote") or "").strip()
    if not quote:
        errors.append("no evidence_quote — the iron rule: no verbatim quote, no edge")
    elif len(quote) < min_quote:
        errors.append(f"evidence_quote too short ({len(quote)} < {min_quote} chars) "
                      "— quote the sentence, not a fragment")

    url = _s(row, "source_url")
    if not url:
        errors.append("no source_url")
    elif not url.lower().startswith("http"):
        errors.append(f"source_url is not a URL: '{url[:60]}'")
    elif is_search_url(url):
        errors.append("source_url is a search query, not a resolved document")

    stier = _s(row, "source_tier").lower()
    if stier not in eco.TIER_RANK:
        errors.append(f"bad source_tier '{stier}' ({'|'.join(eco.SOURCE_TIERS)})")

    tech = _s(row, "tech_node").lower() or None
    if tech and tech not in tech_slugs:
        warnings.append(f"unknown tech_node '{tech}' — dropped")
        tech = None

    # The agent's `spine` column is advisory: the type decides. Silently correcting it
    # would hide a misunderstanding, so warn.
    spine_given = _s(row, "spine").lower()
    spine = eco.SPINE_BY_TYPE.get(etype)
    if spine_given and spine and spine_given != spine:
        warnings.append(f"spine '{spine_given}' contradicts edge_type '{etype}' "
                        f"— corrected to '{spine}'")

    if errors:
        return None, errors, warnings
    return {
        "source": source, "target": target, "edge_type": etype, "spine": spine,
        "strength": strength, "tech_node": tech, "started": _s(row, "started") or None,
        "quote": quote, "source_url": url, "source_tier": stier,
        "published_date": _s(row, "published_date") or None,
        "note": _s(row, "note") or None,
    }, [], warnings


# ── merge across agents ──────────────────────────────────────────────────────
def _merge_node(acc, clean, slug, agent, problems):
    """Two agents may legitimately meet the same company (NVIDIA is silicon AND infra).
    Merge into ONE declaration: union the layers, keep the first non-empty scalar, and
    say so when they disagree — a silent overwrite would hide a real dispute."""
    cur = acc.get(slug)
    if cur is None:
        acc[slug] = {**clean, "_agents": [agent]}
        return
    cur["_agents"].append(agent)
    have = {l for l, _ in cur["layers"]}
    for layer, prim in clean["layers"]:
        if layer not in have:
            cur["layers"].append((layer, 0))     # primary stays with the first declarer
            have.add(layer)
    for k, v in clean.items():
        if k == "layers":
            continue
        if cur.get(k) in (None, "") and v not in (None, ""):
            cur[k] = v
        elif v not in (None, "") and cur.get(k) != v and k in FACTORS + ["role", "tier"]:
            problems.append(f"{agent}: node '{clean['name']}' {k}={v} conflicts with "
                            f"{cur[k]} from {cur['_agents'][0]} — kept "
                            f"{cur['_agents'][0]}'s")


def _merge_edge(acc, clean, slug, agent, problems):
    """A second source for the same edge is a SECOND EVIDENCE ROW, not a second edge —
    that is what turns a dashed line solid."""
    ev = {"source_url": clean["source_url"], "source_tier": clean["source_tier"],
          "quote": clean["quote"], "published_date": clean["published_date"]}
    cur = acc.get(slug)
    if cur is None:
        acc[slug] = {**{k: v for k, v in clean.items()
                        if k not in ("quote", "source_url", "source_tier", "published_date")},
                     "evidence": [ev], "_agents": [agent]}
        return
    cur["evidence"].append(ev)
    if agent not in cur["_agents"]:
        cur["_agents"].append(agent)
    if clean["strength"] != cur["strength"]:
        problems.append(f"{agent}: edge {slug} strength {clean['strength']} differs from "
                        f"{cur['strength']} — kept the higher")
        cur["strength"] = max(cur["strength"], clean["strength"])
    for k in ("tech_node", "started", "note"):
        if not cur.get(k) and clean.get(k):
            cur[k] = clean[k]


# ── writers ──────────────────────────────────────────────────────────────────
def _upsert_node(con, slug, n, month):
    """first_seen is written once and never overwritten — it is the node's birthday and
    the changelog reads it."""
    row = con.execute("SELECT id, first_seen FROM eco_nodes WHERE slug = ?",
                      (slug,)).fetchone()
    payload = (n["name"], n["role"], n["sector"], n["tier"], n["ticker"],
               n["public_private"], n["geo"], n["one_liner"], n["what_breaks_it"],
               n["dc_node"], n["f_share"], n["f_alternatives"], n["f_switch_time"],
               n["f_barrier"], n["share_note"])
    if row:
        con.execute(
            """UPDATE eco_nodes SET name=?, role=?, sector=?, tier=?, ticker=?,
                 public_private=?, geo=?, one_liner=?, what_breaks_it=?, dc_node=?,
                 f_share=?, f_alternatives=?, f_switch_time=?, f_barrier=?, share_note=?
               WHERE id=?""", payload + (row["id"],))
        node_id, created = row["id"], False
    else:
        cur = con.execute(
            """INSERT INTO eco_nodes (slug, name, role, sector, tier, ticker,
                 public_private, geo, one_liner, what_breaks_it, dc_node, f_share,
                 f_alternatives, f_switch_time, f_barrier, share_note, first_seen)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (slug,) + payload + (month,))
        node_id, created = cur.lastrowid, True
    # Layers are declared fresh every month a node appears; a layer that stopped being
    # declared has stopped being true.
    con.execute("DELETE FROM eco_node_layers WHERE node_id = ?", (node_id,))
    for layer, prim in n["layers"]:
        con.execute(
            """INSERT INTO eco_node_layers (node_id, layer, is_primary) VALUES (?,?,?)""",
            (node_id, layer, prim))
    return node_id, created


def _upsert_edge(con, slug, e, src_id, tgt_id, tech_id, month):
    row = con.execute("SELECT id FROM eco_edges WHERE slug = ?", (slug,)).fetchone()
    if row:
        con.execute(
            """UPDATE eco_edges SET source_id=?, target_id=?, edge_type=?, spine=?,
                 strength=?, tech_node_id=?, started=COALESCE(started,?), note=?,
                 last_confirmed=? WHERE id=?""",
            (src_id, tgt_id, e["edge_type"], e["spine"], e["strength"], tech_id,
             e["started"], e["note"], month, row["id"]))
        edge_id, created = row["id"], False
    else:
        cur = con.execute(
            """INSERT INTO eco_edges (slug, source_id, target_id, edge_type, spine,
                 strength, tech_node_id, started, note, last_confirmed)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (slug, src_id, tgt_id, e["edge_type"], e["spine"], e["strength"], tech_id,
             e["started"], e["note"], month))
        edge_id, created = cur.lastrowid, True
    today = date.today().isoformat()
    for ev in e["evidence"]:
        con.execute(
            """INSERT OR IGNORE INTO eco_evidence
                 (edge_id, source_url, source_tier, quote, published_date, fetched_date)
               VALUES (?,?,?,?,?,?)""",
            (edge_id, ev["source_url"], ev["source_tier"], ev["quote"],
             ev["published_date"], today))
    return edge_id, created


def _sync_tech_nodes(con):
    """config/eco_layers.yaml is the source of truth for tech nodes; the owner link is
    resolved only if that company is already on the map."""
    for t in eco.load_layers().get("tech_nodes", []):
        owner = con.execute("SELECT id FROM eco_nodes WHERE slug = ?",
                            (t["owner"],)).fetchone()
        con.execute(
            """INSERT INTO eco_tech_nodes (slug, label, owner_node_id, note)
               VALUES (?,?,?,?)
               ON CONFLICT(slug) DO UPDATE SET
                 label=excluded.label, note=excluded.note,
                 owner_node_id=COALESCE(excluded.owner_node_id, eco_tech_nodes.owner_node_id)""",
            (t["slug"], t["label"], owner["id"] if owner else None, t.get("note")))


def _read(path):
    with path.open(newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            yield i, row


def ingest_month(month: str) -> dict:
    """Load every eco-* agent directory for a month. Returns a summary dict."""
    if not eco.month_ok(month):
        raise ValueError(f"month must be YYYY-MM, got '{month}'")
    con = eco.connect()
    rules = eco.load_rules()
    min_quote = int((rules.get("evidence") or {}).get("min_quote_chars", 25))
    sectors = eco.sector_index()
    tech_slugs = eco.tech_node_slugs()

    month_dir = db.RUNS_DIR / month
    if not month_dir.is_dir():
        raise FileNotFoundError(f"no run directory: {month_dir}")

    rejects, problems = [], []
    per_agent = {}
    node_acc, edge_acc = {}, {}
    agent_dirs = sorted(p for p in month_dir.iterdir()
                        if p.is_dir() and p.name.startswith("eco-"))

    # Pass 1 — nodes from every agent, merged into one declaration per company.
    for adir in agent_dirs:
        agent = adir.name
        per_agent.setdefault(agent, {"rows_in": 0, "rows_rejected": 0})
        fpath = adir / "nodes.csv"
        if not fpath.exists():
            continue
        for line, row in _read(fpath):
            per_agent[agent]["rows_in"] += 1
            clean, errs, warns = _validate_node(row, sectors)
            for w in warns:
                problems.append(f"{agent}/nodes.csv:{line} WARN {w}")
            if errs:
                per_agent[agent]["rows_rejected"] += 1
                rejects.append({"agent": agent, "file": "nodes.csv", "line": line,
                                "reason": "; ".join(errs),
                                "row": json.dumps(row, ensure_ascii=False)})
                continue
            _merge_node(node_acc, clean, eco.node_slug(con, clean["name"]), agent,
                        problems)

    node_ids = {}
    created_nodes = []
    for slug, n in node_acc.items():
        nid, created = _upsert_node(con, slug, n, month)
        node_ids[slug] = nid
        if created:
            created_nodes.append(slug)
    con.commit()
    _sync_tech_nodes(con)

    # Pass 2 — edges. Endpoints must be declared nodes: the contract forbids dangling
    # references, so an edge to an undeclared company is rejected, not invented.
    for adir in agent_dirs:
        agent = adir.name
        per_agent.setdefault(agent, {"rows_in": 0, "rows_rejected": 0})
        fpath = adir / "edges.csv"
        if not fpath.exists():
            continue
        for line, row in _read(fpath):
            per_agent[agent]["rows_in"] += 1
            clean, errs, warns = _validate_edge(row, min_quote, tech_slugs)
            for w in warns:
                problems.append(f"{agent}/edges.csv:{line} WARN {w}")
            if not errs:
                s_slug = eco.node_slug(con, clean["source"])
                t_slug = eco.node_slug(con, clean["target"])
                if s_slug == t_slug:
                    errs.append(f"self-loop on '{s_slug}'")
                for role, sl, nm in (("source", s_slug, clean["source"]),
                                     ("target", t_slug, clean["target"])):
                    if sl not in node_ids and not con.execute(
                            "SELECT 1 FROM eco_nodes WHERE slug=?", (sl,)).fetchone():
                        errs.append(f"{role} '{nm}' -> '{sl}' is not a declared node "
                                    "(add it to nodes.csv)")
            if errs:
                per_agent[agent]["rows_rejected"] += 1
                rejects.append({"agent": agent, "file": "edges.csv", "line": line,
                                "reason": "; ".join(errs),
                                "row": json.dumps(row, ensure_ascii=False)})
                continue
            _merge_edge(edge_acc, clean, eco.edge_slug(s_slug, t_slug, clean["edge_type"]),
                        agent, problems)

    created_edges, evidence_rows = [], 0
    for slug, e in edge_acc.items():
        s_slug, t_slug, _ = slug.split("__")
        src = con.execute("SELECT id FROM eco_nodes WHERE slug=?", (s_slug,)).fetchone()
        tgt = con.execute("SELECT id FROM eco_nodes WHERE slug=?", (t_slug,)).fetchone()
        tech = None
        if e.get("tech_node"):
            r = con.execute("SELECT id FROM eco_tech_nodes WHERE slug=?",
                            (e["tech_node"],)).fetchone()
            tech = r["id"] if r else None
        _, created = _upsert_edge(con, slug, e, src["id"], tgt["id"], tech, month)
        evidence_rows += len(e["evidence"])
        if created:
            created_edges.append(slug)

    # source_log — same table and contract as the weekly pipeline.
    for adir in agent_dirs:
        slog = adir / "source_log.csv"
        if not slog.exists():
            continue
        for _, row in _read(slog):
            con.execute(
                """INSERT INTO source_log (run_week, agent, source_url, source_tier, yielded)
                   VALUES (?,?,?,?,?)""",
                (month, adir.name, (row.get("source_url") or "").strip(), None,
                 1 if (row.get("yielded") or "").strip() in ("1", "true", "yes") else 0))

    for agent, s in per_agent.items():
        con.execute(
            """INSERT INTO eco_runs (month, agent, rows_in, rows_rejected, notes)
               VALUES (?,?,?,?,?)
               ON CONFLICT(month, agent) DO UPDATE SET
                 rows_in=excluded.rows_in, rows_rejected=excluded.rows_rejected,
                 notes=excluded.notes""",
            (month, agent, s["rows_in"], s["rows_rejected"], None))
    con.commit()

    # Hand the rejects back — this file is the next run's reading assignment.
    rpath = month_dir / "rejects.csv"
    if rejects:
        with rpath.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["agent", "file", "line", "reason", "row"])
            w.writeheader()
            w.writerows(rejects)
    elif rpath.exists():
        rpath.unlink()

    stats = {
        "agents": len(agent_dirs), "nodes": len(node_acc), "nodes_new": len(created_nodes),
        "edges": len(edge_acc), "edges_new": len(created_edges), "evidence": evidence_rows,
        "rejected": len(rejects), "problems": problems,
        "rejects_path": str(rpath) if rejects else None,
    }
    con.close()
    return stats


if __name__ == "__main__":
    s = ingest_month(sys.argv[1] if len(sys.argv) > 1 else eco.current_month())
    print(f"eco_ingest: {s['nodes']} nodes ({s['nodes_new']} new), {s['edges']} edges "
          f"({s['edges_new']} new), {s['evidence']} evidence rows, "
          f"{s['rejected']} rejected")
    for p in s["problems"]:
        print("  ", p)
