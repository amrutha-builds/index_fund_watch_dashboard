#!/usr/bin/env bash
# Refresh the Fire-Sale Watch dashboard from your current config.yaml.
# Used by the cron job, and runnable by hand anytime:  ./update.sh
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
# shellcheck disable=SC1091
source "$DIR/.venv/bin/activate"
exec python "$DIR/fetch_data.py"
