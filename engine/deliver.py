"""Deliver: push the handoff into the ab-investment dashboard repo.

Auto-push model (decided): the scheduled/weekly run copies handoff/capital_map.json
into the dashboard repo at src/data/capitalMap.json, commits it, and pushes to
main. Vercel auto-deploys on push. There is no review gate — whatever the agents
verified goes live — so agent accuracy discipline is what protects production.

LOGO REFRESH. Every cycle brings entities the dashboard has never seen, and a
node with no logo falls back to a monogram tile. So after copying the map we run
the dashboard's scripts/fetch_logos.py in incremental mode: it walks the NEW map,
resolves a domain for anything without one, verifies the page really belongs to
that entity, and downloads the sharpest icon it can find. Anything unverifiable
stays a monogram — a wrong logo is worse than none. Pass refresh_logos=False to
skip (offline runs, or when you want a data-only commit).

Safety properties:
- Commits only the delivery paths (map, logo manifest, logo files, entity
  reference) — never sweeps up unrelated dashboard work in progress.
- Gated: nothing here runs unless explicitly invoked (run_week.py --deliver/--push).
  `push=False` copies the file but does not commit/push.
- The logo step is best-effort: a network failure there never blocks delivery of
  the data itself.

Config: the dashboard repo path comes from env AB_INVESTMENT_PATH, defaulting to the
known local checkout.
"""

import os
import shutil
import subprocess
from pathlib import Path

from . import db

AB_PATH = Path(os.environ.get(
    "AB_INVESTMENT_PATH", "/Users/macbook/Desktop/BASE/Code/ab-investment"))
DEST_REL = "src/data/capitalMap.json"
LOGO_SCRIPT = "scripts/fetch_logos.py"
# Everything a delivery is allowed to touch in the dashboard repo.
COMMIT_PATHS = [DEST_REL, "src/data/logoManifest.json",
                "src/data/entityReference.json", "public/logos"]
LOGO_TIMEOUT = 900          # 15 min ceiling; the script is incremental so it's usually seconds


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True, text=True)


def refresh_logos() -> dict:
    """Fetch logos for entities the dashboard doesn't have one for yet."""
    script = AB_PATH / LOGO_SCRIPT
    if not script.exists():
        return {"ran": False, "note": f"{LOGO_SCRIPT} not found"}
    try:
        p = subprocess.run(["python3", str(script)], cwd=AB_PATH,
                           capture_output=True, text=True, timeout=LOGO_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"ran": False, "note": "timed out"}
    tail = (p.stdout or "").strip().splitlines()
    return {"ran": p.returncode == 0, "summary": tail[-1] if tail else "",
            "note": (p.stderr or "").strip()[:200] or None}


def run(week: str, push: bool = False, refresh_logos_first: bool = True) -> dict:
    src = db.HANDOFF_DIR / "capital_map.json"
    if not src.exists():
        raise FileNotFoundError(f"no handoff to deliver: {src} (run the pipeline first)")
    if not (AB_PATH / ".git").is_dir():
        raise FileNotFoundError(f"dashboard repo not found at {AB_PATH} "
                                f"(set AB_INVESTMENT_PATH)")

    dest = AB_PATH / DEST_REL
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)

    # Logos come AFTER the copy so the script sees this cycle's new entities.
    logos = refresh_logos() if refresh_logos_first else {"ran": False, "note": "skipped"}

    if not push:
        return {"copied_to": str(dest), "pushed": False, "logos": logos}

    _git(["add", "--", *COMMIT_PATHS], AB_PATH)
    # Commit only if something in the delivery set actually changed.
    status = _git(["status", "--porcelain", "--", *COMMIT_PATHS], AB_PATH).stdout.strip()
    if not status:
        return {"copied_to": str(dest), "pushed": False, "note": "no change", "logos": logos}
    _git(["commit", "-m", f"Capital Flow data update: {week}", "--", *COMMIT_PATHS], AB_PATH)
    _git(["push", "origin", "HEAD:main"], AB_PATH)
    return {"copied_to": str(dest), "pushed": True, "week": week, "logos": logos}


if __name__ == "__main__":
    import sys
    wk = sys.argv[1]
    do_push = "--push" in sys.argv
    print(run(wk, push=do_push, refresh_logos_first="--no-logos" not in sys.argv))
