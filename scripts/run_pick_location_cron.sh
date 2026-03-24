#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

if ! command -v poetry >/dev/null 2>&1; then
    echo "Missing 'poetry' on PATH. Install Poetry, then rerun 'poetry install'." >&2
    exit 1
fi

exec poetry run noaa-spec pick-location \
    --start-year "${NOAA_PICK_START_YEAR:-1975}" \
    --end-year "${NOAA_PICK_END_YEAR:-2025}" \
    --sleep-seconds "${NOAA_PICK_SLEEP_SECONDS:-0.5}" \
    --output-dir "${NOAA_PICK_OUTPUT_DIR:-output}"
