#!/usr/bin/env bash
# Install (or refresh) the daily cron job that updates the dashboard.
# Safe to run multiple times — it replaces only its own line.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TAG="# fire-sale-watch"
# Weekdays at 18:30 local time — after US market close, once fund NAVs settle.
LINE="30 18 * * 1-5 $DIR/update.sh >> $DIR/cron.log 2>&1 $TAG"

current="$(crontab -l 2>/dev/null || true)"
cleaned="$(printf '%s\n' "$current" | grep -v -F "$TAG" || true)"
{ printf '%s\n' "$cleaned" | sed '/^$/d'; printf '%s\n' "$LINE"; } | crontab -

echo "Installed cron job:"
crontab -l | grep -F "$TAG"
