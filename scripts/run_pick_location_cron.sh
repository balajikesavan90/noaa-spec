#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PATH="/usr/local/bin:/usr/bin:/bin:${HOME}/.local/bin:${PATH:-}"
VENV_PYTHON="${REPO_ROOT}/.venv/bin/python"

cd "${REPO_ROOT}"

if [[ ! -x "${VENV_PYTHON}" ]]; then
    echo "Missing ${VENV_PYTHON}. Run 'poetry install' to create the project-local virtualenv." >&2
    exit 1
fi

exec "${VENV_PYTHON}" -m noaa_spec.cli pick-location \
    --start-year "${NOAA_PICK_START_YEAR:-1975}" \
    --end-year "${NOAA_PICK_END_YEAR:-2025}" \
    --sleep-seconds "${NOAA_PICK_SLEEP_SECONDS:-0.5}" \
    --output-dir "${NOAA_PICK_OUTPUT_DIR:-/media/balaji-kesavan/LaCie/NOAA_Data}"
