#!/usr/bin/env bash
# Capital Flow — one-command deterministic run + deploy.
#
#   bash run.sh            # current ISO week
#   bash run.sh 2026-W32   # a specific week
#
# This runs the DETERMINISTIC half only (ingest -> signals -> beneficiaries ->
# report -> handoff -> deploy to the dashboard and push to Vercel). The agent
# RESEARCH stage (the six agents writing CSVs into runs/<week>/) is separate — it
# needs a Claude Code session or the weekly cloud routine. This script deploys
# whatever CSVs already exist for the week.
#
# It build-gates the deploy: if the dashboard build fails, it does NOT push.

set -euo pipefail

# --- activate the workspace: resolve to this script's folder no matter where you run it ---
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

AB="${AB_INVESTMENT_PATH:-/Users/macbook/Desktop/BASE/Code/ab-investment}"
WEEK="${1:-$(python3 -c 'import datetime;y,w,_=datetime.date.today().isocalendar();print(f"{y}-W{w:02d}")')}"

echo "== Capital Flow: $WEEK =="

# 1) pipeline + copy the handoff into the dashboard (no push yet)
python3 run_week.py "$WEEK" --deliver

# 2) build-gate: only deploy if the dashboard compiles
echo "== build check ($AB) =="
( cd "$AB" && npm run build >/dev/null ) && echo "build OK" || { echo "BUILD FAILED — not deploying"; exit 1; }

# 3) deploy: commit capitalMap.json to main + push (Vercel auto-deploys)
echo "== deploy =="
AB_INVESTMENT_PATH="$AB" python3 -c "from engine import deliver; print(deliver.run('$WEEK', push=True))"

echo "== done: $WEEK deployed =="
