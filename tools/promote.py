"""Apply the weekly promotion decisions from the Monday review.

The dashboard shows the payload's `promotion_queue` as a pop-up (yes/no per
discovered candidate). The user's picks come back here — the engine NEVER
auto-promotes. Accepted names are appended to config/promoted.yaml (tracked from
the next run) and marked in universe_candidates so they leave the queue.

Usage:
  python tools/promote.py --promote "Lightspeed:vc" "General Catalyst:vc:key"
  python tools/promote.py --dismiss "Some Name" "Another Name"
  python tools/promote.py --from decisions.json     # {"promote":[{name,class,tier}], "dismiss":[name]}

`class` is one of corporate|vc|individual|alt_manager|sovereign; tier defaults to
watch. A name with no class is left for you to fill in config/promoted.yaml.
"""

import json
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import db  # noqa: E402

PROMOTED = db.CONFIG_DIR / "promoted.yaml"


def _load():
    d = yaml.safe_load(PROMOTED.read_text()) if PROMOTED.exists() else None
    return (d or {}).get("promoted") or []


def _save(rows):
    PROMOTED.write_text(
        "# Promoted allocators — accepted in the weekly Monday review "
        "(tools/promote.py).\n# Loaded by db.sync_allocators. Never auto-promoted.\n"
        + yaml.safe_dump({"promoted": rows}, sort_keys=False, allow_unicode=True))


def _mark(con, name, status):
    con.execute("UPDATE universe_candidates SET status=?, decided_at=? WHERE name=?",
                (status, date.today().isoformat(), name))


def promote(items):
    """items: list of (name, class|None, tier)."""
    rows = _load()
    have = {r["name"] for r in rows}
    con = db.connect()
    added = []
    for name, cls, tier in items:
        if name not in have:
            rows.append({"name": name, "class": cls, "tier": tier or "watch",
                         "promoted_on": date.today().isoformat()})
            added.append(name)
        _mark(con, name, "promoted")
    con.commit()
    con.close()
    _save(rows)
    print(f"promoted {len(added)}: {', '.join(added) or '—'} "
          f"(edit config/promoted.yaml to set class where missing)")


def dismiss(names):
    con = db.connect()
    for n in names:
        _mark(con, n, "dismissed")
    con.commit()
    con.close()
    print(f"dismissed {len(names)}: {', '.join(names) or '—'}")


def _parse(spec):
    # "Name" | "Name:class" | "Name:class:tier"
    parts = spec.split(":")
    name = parts[0].strip()
    cls = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
    tier = parts[2].strip() if len(parts) > 2 else "watch"
    return name, cls, tier


def main(argv):
    if not argv:
        print(__doc__)
        return
    flag, rest = argv[0], argv[1:]
    if flag == "--promote":
        promote([_parse(s) for s in rest])
    elif flag == "--dismiss":
        dismiss([s.strip() for s in rest])
    elif flag == "--from":
        d = json.loads(Path(rest[0]).read_text())
        promote([(p["name"], p.get("class"), p.get("tier", "watch"))
                 for p in d.get("promote", [])])
        dismiss([n if isinstance(n, str) else n["name"] for n in d.get("dismiss", [])])
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
