#!/usr/bin/env bash
# Open the dashboard in Google Chrome (Windows) from WSL.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WINPATH="$(wslpath -w "$DIR/dashboard.html")"
CHROME="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"

if [ -x "$CHROME" ]; then
  # explorer.exe/chrome return quirky exit codes even on success, so don't gate on them.
  "$CHROME" "$WINPATH" >/dev/null 2>&1
else
  # Chrome not where we expect — fall back to the Windows default browser.
  explorer.exe "$WINPATH" >/dev/null 2>&1 || \
    echo "Open this file in your browser: $DIR/dashboard.html"
fi
