"""Shared vocabulary + helpers for the MONTHLY ecosystem pipeline.

The weekly pipeline's shared layer is engine/db.py; this module is its ecosystem
counterpart and deliberately builds ON it rather than beside it — `connect()` is
db.connect() (same file, same schema application), and node names resolve through the
same config/aliases.yaml, so NVIDIA is one NVIDIA on both maps.

Nothing here makes a judgement. Vocabularies are frozen in config/eco_*.yaml.
"""

import re
import unicodedata
from datetime import date

import yaml

from . import db

LAYERS = [f"L{i}" for i in range(1, 13)]
LAYER_INDEX = {l: i for i, l in enumerate(LAYERS)}

# The ten edge types and which spine each belongs to. The pairing is not the agent's
# choice — ingest overrides a mismatched `spine` column rather than trusting it.
SPINE_BY_TYPE = {
    "supply": "physical", "offtake": "physical", "platform": "physical",
    "partner": "physical", "compete": "physical",
    "owns": "capital", "stake": "capital", "finances": "capital",
    "develops": "capital", "operates": "capital",
}
EDGE_TYPES = set(SPINE_BY_TYPE)
CAPITAL_TYPES = {t for t, s in SPINE_BY_TYPE.items() if s == "capital"}
PHYSICAL_TYPES = {t for t, s in SPINE_BY_TYPE.items() if s == "physical"}
# Not collected in v1 (§10 of the plan): a judgement, not a fact from a release.
EXCLUDED_EDGE_TYPES = {"compete"}

SOURCE_TIERS = ["filing", "company_pr", "transcript", "press", "estimate"]
# Lower is stronger — used to pick an edge's effective tier from its evidence rows.
TIER_RANK = {t: i for i, t in enumerate(SOURCE_TIERS)}

ROLES = {"producer", "owner", "capital", "demand", "platform"}
NODE_TIERS = {"anchor", "core", "emerging"}

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

_CFG = {}


def _load(name: str) -> dict:
    if name not in _CFG:
        p = db.CONFIG_DIR / name
        _CFG[name] = yaml.safe_load(p.read_text()) if p.exists() else {}
    return _CFG[name] or {}


def load_layers() -> dict:
    return _load("eco_layers.yaml")


def load_watchlist() -> dict:
    return _load("eco_watchlist.yaml")


def load_rules() -> dict:
    return _load("eco_rules.yaml")


def connect():
    """Same DB, same connect path as the weekly pipeline (db.connect applies both
    schemas). Kept as a named alias so eco modules never reach for a second file."""
    return db.connect()


# ── Taxonomy lookups ─────────────────────────────────────────────────────────
def sector_index() -> dict:
    """{sector_key: {'layer': 'L2', 'label': …, 'dc_node': 'litho'}} — the frozen
    taxonomy, flattened. Ingest uses it to check a node's sector actually belongs to
    one of its layers, and to fill dc_node when the agent left it blank."""
    out = {}
    for L in load_layers().get("layers", []):
        for s in L.get("sectors", []):
            out[s["key"]] = {"layer": L["id"], "label": s.get("label"),
                             "dc_node": s.get("dc_node")}
    return out


def layer_bands() -> dict:
    return {L["id"]: L["band"] for L in load_layers().get("layers", [])}


def tech_node_slugs() -> set:
    return {t["slug"] for t in load_layers().get("tech_nodes", [])}


# ── Identity ─────────────────────────────────────────────────────────────────
_SLUG_OVERRIDES = None


def slug_overrides() -> dict:
    """{normalized name: slug} from config/eco_watchlist.yaml. Watchlist slugs win over
    the generated form, because they are the ones already written into the contract
    (`ontario-teachers`, not `ontario-teachers-pension-plan`)."""
    global _SLUG_OVERRIDES
    if _SLUG_OVERRIDES is not None:
        return _SLUG_OVERRIDES
    out = {}
    w = load_watchlist()
    for key in ("anchors", "emerging", "capital_spine"):
        for r in (w.get(key) or []):
            out[_norm(r["name"])] = r["slug"]
            out[_norm(r["slug"])] = r["slug"]
    _SLUG_OVERRIDES = out
    return out


def _norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def slugify(name: str) -> str:
    """Stable, ASCII, lowercase slug. Node and edge ids are permanent — a renamed slug
    is a lost history, so this function must stay deterministic forever."""
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s)


def node_slug(con, name: str) -> str:
    """Resolve a company name to its permanent map id.

    Order matters: aliases first (so 'Google' and 'Alphabet' land on one node), then the
    watchlist's declared slug, then an existing DB row matched by name, then a generated
    slug. Steps 2 and 3 are what stop a node's id drifting between runs.
    """
    canonical = db.resolve_name(name)
    ov = slug_overrides()
    for cand in (canonical, name):
        if _norm(cand) in ov:
            return ov[_norm(cand)]
    if con is not None:
        row = con.execute(
            "SELECT slug FROM eco_nodes WHERE lower(name) = ?", (_norm(canonical),)
        ).fetchone()
        if row:
            return row["slug"]
    return slugify(canonical)


def edge_slug(source_slug: str, target_slug: str, edge_type: str) -> str:
    """'<source>__<target>__<type>' — frozen by the handoff contract."""
    return f"{source_slug}__{target_slug}__{edge_type}"


# ── Dates ────────────────────────────────────────────────────────────────────
def current_month() -> str:
    t = date.today()
    return f"{t.year}-{t.month:02d}"


def month_ok(m: str) -> bool:
    return bool(MONTH_RE.match(m or ""))


def to_month(value: str):
    """Any ISO-ish date -> 'YYYY-MM'. None for unparseable input."""
    v = (value or "").strip()
    if MONTH_RE.match(v):
        return v
    m = re.match(r"^(\d{4})-(\d{2})", v)
    return f"{m.group(1)}-{m.group(2)}" if m else None


def months_between(a: str, b: str) -> int:
    """Whole months from a to b ('2026-02' -> '2026-08' = 6). 0 if either is unusable."""
    if not (month_ok(a) and month_ok(b)):
        return 0
    ya, ma = int(a[:4]), int(a[5:7])
    yb, mb = int(b[:4]), int(b[5:7])
    return (yb - ya) * 12 + (mb - ma)
