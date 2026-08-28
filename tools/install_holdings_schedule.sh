#!/usr/bin/env bash
# Install the MONTHLY fund-portfolio run as a real launchd job.
#
#   bash tools/install_holdings_schedule.sh          # install
#   bash tools/install_holdings_schedule.sh --show   # print the plist, install nothing
#   bash tools/install_holdings_schedule.sh --remove # uninstall
#
# Why launchd and not cron: on macOS a cron entry does not fire if the machine was
# asleep at the appointed minute, and this job runs once a month — a missed fire is
# a missed month. launchd runs a StartCalendarInterval job as soon as the machine
# wakes, which is the behaviour a monthly job needs.
#
# Why the 22nd: 13F filings land ~45 days after quarter end (Q2 2026 was filed
# 2026-08-12), so a late-month run catches the new quarter's filings in the same
# pass instead of a month later. Any day from the 20th works.
#
# The run needs an agent launcher on PATH (see engine/holdings_agents.py) and an
# SEC contact header. Both are read from the environment written into the plist
# below — edit them before installing.

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$PWD"
LABEL="com.capitalflow.holdings"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PY="$(command -v python3)"
# XML-escape it: a User-Agent conventionally contains <angle brackets>, which
# would produce a plist launchd silently refuses to load.
SEC_UA_RAW="${FUND_SEC_USER_AGENT:-Capital Flow research <you@example.com>}"
SEC_UA="$(printf '%s' "$SEC_UA_RAW" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g')"

read -r -d '' BODY <<XML || true
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>$ROOT/run_holdings.py</string>
    <string>--push</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>FUND_SEC_USER_AGENT</key><string>$SEC_UA</string>
    <key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
  </dict>
  <!-- 22nd of each month, 09:07. Off the hour on purpose. -->
  <key>StartCalendarInterval</key>
  <dict>
    <key>Day</key><integer>22</integer>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>7</integer>
  </dict>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>$ROOT/runs/holdings-schedule.log</string>
  <key>StandardErrorPath</key><string>$ROOT/runs/holdings-schedule.log</string>
</dict>
</plist>
XML

case "${1:-}" in
  --show)   printf '%s\n' "$BODY"; exit 0 ;;
  --remove) launchctl unload "$PLIST" 2>/dev/null || true
            rm -f "$PLIST"; echo "removed $LABEL"; exit 0 ;;
esac

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/runs"
printf '%s\n' "$BODY" > "$PLIST"
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "installed $LABEL — runs run_holdings.py --push on the 22nd of each month at 09:07"
echo "log: $ROOT/runs/holdings-schedule.log"
echo
echo "Check it is registered:   launchctl list | grep capitalflow"
echo "Fire it once by hand:     launchctl start $LABEL"
