"""Rebuild db/capital.db from the full runs/ history.

Usage: python tools/rebuild_db.py

The SQLite DB is gitignored; runs/ is the committed source of truth. A FRESH
CLONE MUST RUN THIS before running a new week, otherwise the handoff will
contain only the new week's events and the delivery will try to replace the
cumulative map with a tiny one (deliver.py now blocks that, but the fix is
this rebuild). Replays every runs/<week>/ in order: events + profiles +
references + beneficiaries, then recomputes themes for the latest week.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import beneficiaries, db, ingest, profiles, references, themes  # noqa: E402


def main() -> None:
    weeks = sorted(p.name for p in db.RUNS_DIR.iterdir()
                   if p.is_dir() and not p.name.startswith("."))
    if not weeks:
        print("no runs/ history to rebuild from")
        return
    print(f"rebuilding {db.DB_PATH} from {len(weeks)} weeks: {', '.join(weeks)}")
    for w in weeks:
        s = ingest.ingest_week(w)
        b = beneficiaries.run(w)
        p = profiles.ingest_week(w)
        r = references.ingest_week(w)
        print(f"  {w}: +{s['inserted']} events ({s['skipped']} skipped), "
              f"{b['linked']} beneficiaries, {p['profiles']} profiles, "
              f"{r['references']} references")
    t = themes.run(weeks[-1])
    print(f"  themes recomputed for {weeks[-1]}: {len(t['fired'])} fired")
    print("done — run `python run_week.py <week>` for the current cycle next")


if __name__ == "__main__":
    main()
