#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PATH="/usr/local/bin:/usr/bin:/bin:${HOME}/.local/bin:${PATH:-}"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

cd "${REPO_ROOT}"

if ! command -v poetry >/dev/null 2>&1; then
    echo "Missing 'poetry' on PATH. Install Poetry with the documented official installer, then run 'poetry install'." >&2
    exit 1
fi

exec poetry run python3 -m noaa_spec.cli pick-location \
    --start-year "${NOAA_PICK_START_YEAR:-1975}" \
    --end-year "${NOAA_PICK_END_YEAR:-2025}" \
    --sleep-seconds "${NOAA_PICK_SLEEP_SECONDS:-0.5}" \
    --output-dir "${NOAA_PICK_OUTPUT_DIR:-/media/balaji-kesavan/LaCie/NOAA_Data}"
