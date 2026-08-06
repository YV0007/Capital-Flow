"""Deliver: push the handoff into the ab-investment dashboard repo.

Auto-push model (decided): the scheduled/weekly run copies handoff/capital_map.json
into the dashboard repo at src/data/capitalMap.json, commits ONLY that file, and
pushes to main. Vercel auto-deploys on push. There is no review gate — whatever the
agents verified goes live — so agent accuracy discipline is what protects production.

Safety properties:
- Commits only the single capitalMap.json path (never sweeps up unrelated changes in
  the dashboard working tree).
- Gated: nothing here runs unless explicitly invoked (run_week.py --deliver/--push).
  `push=False` copies the file but does not commit/push.

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


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True, text=True)


def run(week: str, push: bool = False) -> dict:
    src = db.HANDOFF_DIR / "capital_map.json"
    if not src.exists():
        raise FileNotFoundError(f"no handoff to deliver: {src} (run the pipeline first)")
    if not (AB_PATH / ".git").is_dir():
        raise FileNotFoundError(f"dashboard repo not found at {AB_PATH} "
                                f"(set AB_INVESTMENT_PATH)")

    dest = AB_PATH / DEST_REL
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)

    if not push:
        return {"copied_to": str(dest), "pushed": False}

    _git(["add", DEST_REL], AB_PATH)
    # Commit only if the data file actually changed.
    status = _git(["status", "--porcelain", DEST_REL], AB_PATH).stdout.strip()
    if not status:
        return {"copied_to": str(dest), "pushed": False, "note": "no change"}
    _git(["commit", "-m", f"Capital Flow data update: {week}", "--", DEST_REL], AB_PATH)
    _git(["push", "origin", "HEAD:main"], AB_PATH)
    return {"copied_to": str(dest), "pushed": True, "week": week}


if __name__ == "__main__":
    import sys
    wk = sys.argv[1]
    do_push = "--push" in sys.argv
    print(run(wk, push=do_push))
